from datetime import date

from fastapi import APIRouter, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import compute, io
from ._config import DEFAULT_TASKS_CSV_PATH, WIP_LIMIT

app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

api = APIRouter(prefix="/api")


def _resolve_csv_path(csv: str | None = None) -> str:
    """Resolve CSV path from query parameter or default."""
    return csv or DEFAULT_TASKS_CSV_PATH


def _load_tasks(csv_path: str) -> list[io.Task]:
    """Import every stored task from the given task file."""
    return io.import_tasks_from_csv(csv_path)


def _task_ids(tasks: list[io.Task]) -> list[int]:
    """Return every task's id, preserving the given order."""
    return [task.id for task in tasks]


def _anchored_rating_fields(task: io.Task) -> dict:
    """Return the Glicko fields with the stored deviation."""
    return {
        "rating": task.rating,
        "rating_deviation": task.rating_deviation,
    }


def _projected_rating_fields(task: io.Task, reference_date: date) -> dict:
    """Return the Glicko fields with the deviation projected to reference_date."""
    return {
        "rating": task.rating,
        "rating_deviation": round(
            compute.compute_live_rating_deviation(
                task.rating_deviation, task.rating_date, reference_date
            )
        ),
    }


def _task_to_dict(task: io.Task, reference_date: date) -> dict:
    """Convert Task object to API response dictionary."""
    return {
        "id": task.id,
        "description": task.description,
        "contexts": task.contexts,
        "skip_count": task.skip_count,
        "starred": task.starred,
        "latest_date": task.latest_date.isoformat(),
        "latest_done_date": task.latest_done_date.isoformat(),
        "recurrence_days": task.recurrence_days,
        "due_date": task.due_date.isoformat(),
        "coins": task.coins,
        **_projected_rating_fields(task, reference_date),
    }


def _error_response(message: str, status_code: int) -> JSONResponse:
    """Return the error envelope shared by every failed request."""
    return JSONResponse(content={"error": message}, status_code=status_code)


def _task_not_found_response() -> JSONResponse:
    """Return the 404 envelope for an id that names no task."""
    return _error_response("Task not found", 404)


@app.exception_handler(RequestValidationError)
async def _invalid_request_response(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    """Return the shared error envelope for a request that fails validation."""
    return _error_response("Invalid request", 422)


def _find_task(task_id: int, csv_path: str) -> io.Task | None:
    """Return the stored task, or None when no task has the id."""
    try:
        return io.get_task_by_id(task_id, csv_path)
    except ValueError:
        return None


@api.get("/task/")
def get_all_tasks(csv: str = Query(None)):
    return _task_ids(_load_tasks(_resolve_csv_path(csv)))


def _apply_wip_selection(
    tasks: list[io.Task], context: str, reference_date: date, csv_path: str
) -> list[int]:
    """Apply work-in-progress selection to one context, deferring the surplus."""
    tasks_in_context = compute.filter_all_tasks_by_context(tasks, context)
    completed_today = compute.count_completed_today(tasks_in_context, reference_date)
    available_slots = compute.compute_available_wip_slots(WIP_LIMIT, completed_today)
    selected, deferred = compute.filter_n_tasks_by_context(
        tasks, context, reference_date, available_slots
    )
    for task in deferred:
        io.update_task_as_skipped(task.id, reference_date, csv_path)
    return _task_ids(selected)


@api.get("/task/due/{reference_date}")
def get_due_task_ids(
    reference_date: date,
    csv: str = Query(None),
    context: list[str] = Query(None),
):
    csv_path = _resolve_csv_path(csv)
    tasks = _load_tasks(csv_path)
    requested_contexts = list(dict.fromkeys(context or []))
    if len(requested_contexts) == 1:
        return _apply_wip_selection(tasks, requested_contexts[0], reference_date, csv_path)
    due_tasks = compute.filter_due_tasks(tasks, reference_date)
    if requested_contexts:
        return _task_ids(compute.filter_tasks_by_any_context(due_tasks, set(requested_contexts)))
    return _task_ids(due_tasks)


@api.get("/task/{task_id}")
def get_task_by_id(
    task_id: int,
    csv: str = Query(None),
    reference_date_str: str = Query(None, alias="date"),
):
    csv_path = _resolve_csv_path(csv)
    task = _find_task(task_id, csv_path)
    if task is None:
        return _task_not_found_response()
    reference_date = date.fromisoformat(reference_date_str) if reference_date_str else date.today()
    return _task_to_dict(task, reference_date)


@api.get("/context/due/{reference_date}")
def get_due_contexts(reference_date: date, csv: str = Query(None)):
    """Return the context ids with at least one task due on or before the date."""
    return compute.filter_due_contexts(_load_tasks(_resolve_csv_path(csv)), reference_date)


class DescriptionUpdate(BaseModel):
    description: str


@api.patch("/task/{task_id}/description")
def patch_task_description(task_id: int, body: DescriptionUpdate, csv: str = Query(None)):
    """Replace a task's description with the given text."""
    csv_path = _resolve_csv_path(csv)
    if _find_task(task_id, csv_path) is None:
        return _task_not_found_response()
    if not body.description.strip():
        return _error_response("Description must not be empty", 400)
    io.update_task_description(task_id, body.description, csv_path)
    return {"id": task_id, "description": body.description}


@api.post("/task/{task_id}/done")
def post_task_done(task_id: int, csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    today = date.today()

    current_task = io.get_task_by_id(task_id, csv_path)
    if not compute.is_done_allowed(current_task.latest_done_date, today):
        return _error_response("Task was already completed too recently", 409)

    io.update_task_as_done(task_id, today, csv_path)

    tasks = _load_tasks(csv_path)
    opponents = compute.select_opponents(tasks, current_task, today)
    updates = compute.compute_match_updates(current_task, opponents, today)
    for updated_id, (rating, rating_deviation) in updates.items():
        io.update_task_rating(updated_id, rating, csv_path)
        io.update_task_rating_deviation(updated_id, rating_deviation, csv_path)
        io.update_task_rating_date(updated_id, today, csv_path)

    updated_task = io.get_task_by_id(task_id, csv_path)
    return {
        "id": updated_task.id,
        "skip_count": updated_task.skip_count,
        "due_date": updated_task.due_date.isoformat(),
        "latest_done_date": updated_task.latest_done_date.isoformat(),
        **_anchored_rating_fields(updated_task),
    }


app.include_router(api)
