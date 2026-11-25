from datetime import date

from fastapi import APIRouter, FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, StrictBool

from . import compute, io
from ._config import DEFAULT_CONTEXTS_CSV_PATH, DEFAULT_TASKS_CSV_PATH, WIP_LIMIT

app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

api = APIRouter(prefix="/api")


def _resolve_tasks_csv_path(csv: str | None) -> str:
    """Resolve the task CSV path from the query parameter or default."""
    return csv or DEFAULT_TASKS_CSV_PATH


def _resolve_contexts_csv_path(contexts_csv: str | None) -> str:
    """Resolve the context CSV path from the query parameter or default."""
    return contexts_csv or DEFAULT_CONTEXTS_CSV_PATH


def _task_ids(tasks: list[io.Task]) -> list[int]:
    """Return every task's id, preserving the given order."""
    return [task.id for task in tasks]


def _context_ids(contexts: list[io.Context]) -> list[str]:
    """Return every context's id, sorted."""
    return sorted(context.id for context in contexts)


def _distinct_contexts(context: list[str] | None) -> list[str]:
    """Return the requested context ids without repeats, preserving order."""
    return list(dict.fromkeys(context or []))


def _refuse_empty_contexts(context: list[str] | None) -> None:
    """Reject a requested context value that is empty."""
    if any(not context_value for context_value in context or []):
        raise RequestValidationError(
            [{"loc": ("query", "context"), "msg": "Context must not be empty"}]
        )


def _has_unknown_context(context: list[str], contexts_csv_path: str) -> bool:
    """Return whether any requested context is absent from the context data."""
    stored_ids = {stored.id for stored in io.import_contexts_from_csv(contexts_csv_path)}
    return any(context_id not in stored_ids for context_id in context)


def _task_to_dict(task: io.Task, reference_date: date) -> dict:
    """Return the task detail fields, projecting the Glicko deviation to the date."""
    projected_deviation = round(compute.compute_live_participant_deviation(task, reference_date))
    return TaskDetail(
        id=task.id,
        description=task.description,
        contexts=task.contexts,
        skip_count=task.skip_count,
        starred=task.starred,
        latest_date=task.latest_date.isoformat(),
        latest_done_date=task.latest_done_date.isoformat(),
        recurrence_days=task.recurrence_days,
        due_date=task.due_date.isoformat(),
        coins=task.coins,
        rating=task.rating,
        rating_deviation=projected_deviation,
    ).model_dump()


def _context_to_dict(context: io.Context) -> dict:
    """Return the context detail fields."""
    return ContextDetail(
        id=context.id,
        display_name=context.display_name,
        description=context.description,
        scopes=context.scopes,
    ).model_dump()


def _success_response_schema(schema: dict) -> dict:
    """Return the OpenAPI extra that documents the 200 response with this schema."""
    return {
        "responses": {
            str(status.HTTP_200_OK): {"content": {"application/json": {"schema": schema}}}
        }
    }


def _error_response(message: str, status_code: int) -> JSONResponse:
    """Return the error envelope shared by every failed request."""
    return JSONResponse(content={"error": message}, status_code=status_code)


def _task_not_found_response() -> JSONResponse:
    """Return the 404 envelope for an id that names no task."""
    return _error_response("Task not found", status.HTTP_404_NOT_FOUND)


def _context_not_found_response() -> JSONResponse:
    """Return the 404 envelope for an id that names no context."""
    return _error_response("Context not found", status.HTTP_404_NOT_FOUND)


@app.exception_handler(RequestValidationError)
async def _invalid_request_response(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    """Return the shared error envelope for a request that fails validation."""
    return _error_response("Invalid request", status.HTTP_422_UNPROCESSABLE_CONTENT)


def _find_task(task_id: int, csv_path: str) -> io.Task | None:
    """Return the stored task, or None when no task has the id."""
    try:
        return io.get_task_by_id(task_id, csv_path)
    except ValueError:
        return None


def _find_context(context_id: str, contexts_csv_path: str) -> io.Context | None:
    """Return the stored context, or None when no context has the id."""
    try:
        return io.get_context_by_id(context_id, contexts_csv_path)
    except ValueError:
        return None


def _existing_task_csv_path(task_id: int, csv: str | None) -> str | None:
    """Return the task file path, or None when no task has the id."""
    csv_path = _resolve_tasks_csv_path(csv)
    return csv_path if _find_task(task_id, csv_path) is not None else None


def _select_wip_tasks_and_skip_deferred(
    tasks: list[io.Task], context: str, reference_date: date, csv_path: str
) -> list[io.Task]:
    """Return one context's work-in-progress tasks and skip the deferred surplus."""
    tasks_in_context = compute.filter_tasks_by_context(tasks, context)
    completed_count = compute.count_completed_on(tasks_in_context, reference_date)
    available_slots = compute.compute_available_wip_slots(WIP_LIMIT, completed_count)
    selected, deferred = compute.filter_n_tasks_by_context(
        tasks, context, reference_date, available_slots
    )
    for task in deferred:
        io.update_task_as_skipped(task.id, reference_date, csv_path)
    return selected


def _select_due_tasks(
    tasks: list[io.Task], requested_contexts: list[str], reference_date: date, csv_path: str
) -> list[io.Task]:
    """Return the tasks due at the reference date for the requested contexts."""
    if not requested_contexts:
        return compute.filter_due_tasks(tasks, reference_date)
    if len(requested_contexts) == 1:
        return _select_wip_tasks_and_skip_deferred(
            tasks, requested_contexts[0], reference_date, csv_path
        )
    return compute.filter_due_tasks_by_any_context(tasks, set(requested_contexts), reference_date)


def _completion_response(task: io.Task) -> dict:
    """Return the confirmation fields for a completed task."""
    return CompletionConfirmation(
        id=task.id,
        skip_count=task.skip_count,
        due_date=task.due_date.isoformat(),
        latest_done_date=task.latest_done_date.isoformat(),
        rating=task.rating,
        rating_deviation=task.rating_deviation,
    ).model_dump()


def _apply_rating_updates(
    updates: dict[int, tuple[int, int]], csv_path: str, reference_date: date
) -> None:
    """Store each task's new rating, deviation, and anchor."""
    for updated_id, (rating, rating_deviation) in updates.items():
        io.update_task_rating_fields(updated_id, rating, rating_deviation, reference_date, csv_path)


class TaskDetail(BaseModel):
    """The task detail response returned by GET /task/{task_id}."""

    id: int
    description: str
    contexts: list[str]
    skip_count: int
    starred: bool
    latest_date: str
    latest_done_date: str
    recurrence_days: int
    due_date: str
    coins: int
    rating: int
    rating_deviation: int


class ContextDetail(BaseModel):
    """The context detail response returned by GET /context/{context_id}/."""

    id: str
    display_name: str
    description: str
    scopes: list[str]


class Confirmation(BaseModel):
    """The base of the confirmations action routes return: the id and the changed fields."""

    id: int


class DescriptionConfirmation(Confirmation):
    """The confirmation returned by PATCH /task/{task_id}/description."""

    description: str


class StarredConfirmation(Confirmation):
    """The confirmation returned by PATCH /task/{task_id}/starred."""

    starred: bool


class CompletionConfirmation(Confirmation):
    """The confirmation returned by POST /task/{task_id}/done."""

    skip_count: int
    due_date: str
    latest_done_date: str
    rating: int
    rating_deviation: int


class DescriptionUpdate(BaseModel):
    description: str


class StarredUpdate(BaseModel):
    starred: StrictBool


@api.get(
    "/task/",
    response_model=None,
    openapi_extra=_success_response_schema({"type": "array", "items": {"type": "integer"}}),
)
def get_all_tasks(
    csv: str = Query(None),
    context: list[str] = Query(None),
    contexts_csv: str = Query(None),
) -> list[int] | JSONResponse:
    csv_path = _resolve_tasks_csv_path(csv)
    _refuse_empty_contexts(context)
    tasks = io.import_tasks_from_csv(csv_path)
    if context:
        contexts_csv_path = _resolve_contexts_csv_path(contexts_csv)
        if _has_unknown_context(context, contexts_csv_path):
            return _context_not_found_response()
        tasks = compute.filter_tasks_by_any_context(tasks, set(context))
    return _task_ids(tasks)


@api.get("/context/")
def get_all_contexts(csv: str = Query(None), contexts_csv: str = Query(None)) -> list[str]:
    contexts_csv_path = _resolve_contexts_csv_path(contexts_csv)
    contexts = io.import_contexts_from_csv(contexts_csv_path)
    return _context_ids(contexts)


@api.get("/task/due/{reference_date}")
def get_due_task_ids(
    reference_date: date,
    csv: str = Query(None),
    context: list[str] = Query(None),
) -> list[int]:
    csv_path = _resolve_tasks_csv_path(csv)
    _refuse_empty_contexts(context)
    tasks = io.import_tasks_from_csv(csv_path)
    requested_contexts = _distinct_contexts(context)
    selected_tasks = _select_due_tasks(tasks, requested_contexts, reference_date, csv_path)
    return _task_ids(selected_tasks)


@api.get("/task/due/")
def get_due_tasks_today(csv: str = Query(None)) -> list[int]:
    """Return the ids of the tasks due today."""
    return get_due_task_ids(date.today(), csv=csv, context=[])


@api.get(
    "/task/due",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
def redirect_due_tasks(csv: str = Query(None)):
    """Redirect the slashless due read to the due collection."""
    return RedirectResponse(url="/api/task/due/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@api.get(
    "/task/{task_id}",
    response_model=None,
    openapi_extra=_success_response_schema(TaskDetail.model_json_schema()),
)
def get_task_by_id(
    task_id: int,
    csv: str = Query(None),
    reference_date_str: str = Query(None, alias="date"),
) -> dict | JSONResponse:
    csv_path = _resolve_tasks_csv_path(csv)
    task = _find_task(task_id, csv_path)
    if task is None:
        return _task_not_found_response()
    reference_date = date.fromisoformat(reference_date_str) if reference_date_str else date.today()
    return _task_to_dict(task, reference_date)


@api.get("/context/due/{reference_date}")
def get_due_contexts(reference_date: date, csv: str = Query(None)) -> list[str]:
    """Return the context ids with at least one task due on or before the date."""
    csv_path = _resolve_tasks_csv_path(csv)
    tasks = io.import_tasks_from_csv(csv_path)
    return compute.filter_due_contexts(tasks, reference_date)


@api.get("/context/due/")
def get_due_contexts_today(csv: str = Query(None)) -> list[str]:
    """Return the context ids with at least one task due today."""
    return get_due_contexts(date.today(), csv)


@api.get(
    "/context/{context_id}/",
    openapi_extra=_success_response_schema(ContextDetail.model_json_schema()),
)
def get_context_by_id(context_id: str, csv: str = Query(None), contexts_csv: str = Query(None)):
    """Return one stored context."""
    contexts_csv_path = _resolve_contexts_csv_path(contexts_csv)
    context = _find_context(context_id, contexts_csv_path)
    if context is None:
        return _context_not_found_response()
    return _context_to_dict(context)


@api.patch(
    "/task/{task_id}/description",
    openapi_extra=_success_response_schema(DescriptionConfirmation.model_json_schema()),
)
def patch_task_description(task_id: int, body: DescriptionUpdate, csv: str = Query(None)):
    """Replace a task's description with the given text."""
    csv_path = _existing_task_csv_path(task_id, csv)
    if csv_path is None:
        return _task_not_found_response()
    if not body.description.strip():
        return _error_response("Description must not be empty", status.HTTP_400_BAD_REQUEST)
    io.update_task_description(task_id, body.description, csv_path)
    return DescriptionConfirmation(id=task_id, description=body.description).model_dump()


@api.patch(
    "/task/{task_id}/starred",
    openapi_extra=_success_response_schema(StarredConfirmation.model_json_schema()),
)
def patch_task_starred(task_id: int, body: StarredUpdate, csv: str = Query(None)):
    """Replace a task's starred flag with the given value."""
    csv_path = _existing_task_csv_path(task_id, csv)
    if csv_path is None:
        return _task_not_found_response()
    io.update_task_starred(task_id, body.starred, csv_path)
    return StarredConfirmation(id=task_id, starred=body.starred).model_dump()


@api.post(
    "/task/{task_id}/done",
    openapi_extra=_success_response_schema(CompletionConfirmation.model_json_schema()),
)
def post_task_done(task_id: int, csv: str = Query(None)):
    csv_path = _resolve_tasks_csv_path(csv)
    today = date.today()

    current_task = io.get_task_by_id(task_id, csv_path)
    if not compute.is_done_allowed(current_task.latest_done_date, today):
        return _error_response("Task was already completed too recently", status.HTTP_409_CONFLICT)

    io.update_task_as_done(task_id, today, csv_path)

    tasks = io.import_tasks_from_csv(csv_path)
    opponents = compute.select_opponents(tasks, current_task, today)
    updates = compute.compute_match_updates(current_task, opponents, today)
    _apply_rating_updates(updates, csv_path, today)

    updated_task = io.get_task_by_id(task_id, csv_path)
    return _completion_response(updated_task)


app.include_router(api)
