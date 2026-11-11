from datetime import date

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import compute, io
from ._config import DEFAULT_TASKS_CSV_PATH, WIP_LIMIT
from .models import Context

app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

api = APIRouter(prefix="/api")


def _resolve_csv_path(csv: str | None = None) -> str:
    """Resolve CSV path from query parameter or default."""
    return csv or DEFAULT_TASKS_CSV_PATH


def _rating_fields(task: io.Task, reference_date: date | None = None) -> dict:
    """Return the Glicko fields shared by task responses."""
    if reference_date is None:
        rating_deviation = task.rating_deviation
    else:
        rating_deviation = round(
            compute.compute_live_rating_deviation(
                task.rating_deviation, task.rating_date, reference_date
            )
        )
    return {
        "rating": task.rating,
        "rating_deviation": rating_deviation,
    }


def _task_to_dict(task: io.Task, reference_date: date | None = None) -> dict:
    """Convert Task object to API response dictionary."""
    return {
        "id": task.id,
        "description": task.description,
        "context": task.context.value,
        "skip_count": task.skip_count,
        "starred": task.starred,
        "latest_date": task.latest_date.isoformat(),
        "recurrence_days": task.recurrence_days,
        "due_date": task.due_date.isoformat(),
        "coins": task.coins,
        **_rating_fields(task, reference_date),
    }


def _load_tasks_and_date(csv_path: str, reference_date: str) -> tuple:
    """Import tasks from CSV and parse the reference date."""
    tasks = io.import_tasks_from_csv(csv_path)
    parsed_reference_date = date.fromisoformat(reference_date)
    return tasks, parsed_reference_date


@api.get("/task/")
def get_all_tasks(csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    tasks = io.import_tasks_from_csv(csv_path)
    return [task.id for task in tasks]


@api.get("/task/{task_id}")
def get_task_by_id(
    task_id: int,
    csv: str = Query(None),
    reference_date: str = Query(None, alias="date"),
):
    csv_path = _resolve_csv_path(csv)
    try:
        task = io.get_task_by_id(task_id, csv_path)
    except ValueError:
        return JSONResponse(content={"error": "Task not found"}, status_code=404)
    parsed_reference_date = date.fromisoformat(reference_date) if reference_date else date.today()
    return _task_to_dict(task, parsed_reference_date)


@api.get("/context/{context_id}")
def get_tasks_by_context(
    context_id: str,
    csv: str = Query(None),
    reference_date: str = Query(None, alias="date"),
):
    """Return prioritized task IDs for the given context."""
    csv_path = _resolve_csv_path(csv)
    tasks, parsed_reference_date = _load_tasks_and_date(csv_path, reference_date)
    context = Context(context_id)
    tasks_in_context = compute.filter_all_tasks_by_context(tasks, context)
    completed_today = compute.count_completed_today(tasks_in_context, parsed_reference_date)
    available_slots = compute.compute_available_wip_slots(WIP_LIMIT, completed_today)
    selected, deferred = compute.filter_n_tasks_by_context(
        tasks, context, parsed_reference_date, available_slots
    )
    for task in deferred:
        io.update_task_as_skipped(task.id, parsed_reference_date, csv_path)
    return [task.id for task in selected]


@api.get("/context/")
def get_due_contexts(csv: str = Query(None), reference_date: str = Query(None, alias="date")):
    """Return unique contexts from tasks due on or before the given date."""
    csv_path = _resolve_csv_path(csv)
    tasks, parsed_reference_date = _load_tasks_and_date(csv_path, reference_date)
    due_contexts = compute.filter_due_contexts(tasks, parsed_reference_date)
    return [context.value for context in due_contexts]


class DescriptionUpdate(BaseModel):
    description: str


@api.patch("/task/{task_id}/description")
def patch_task_description(task_id: int, body: DescriptionUpdate, csv: str = Query(None)):
    """Replace a task's description with the given text."""
    csv_path = _resolve_csv_path(csv)
    if not body.description.strip():
        return JSONResponse(content={"error": "Description must not be empty"}, status_code=400)
    try:
        io.get_task_by_id(task_id, csv_path)
    except ValueError:
        return JSONResponse(content={"error": "Task not found"}, status_code=404)
    io.update_task_description(task_id, body.description, csv_path)
    return {"id": task_id, "description": body.description}


@api.post("/task/{task_id}/done")
def post_task_done(task_id: int, csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    today = date.today()

    current_task = io.get_task_by_id(task_id, csv_path)
    if not compute.is_done_allowed(current_task.latest_done_date, today):
        return JSONResponse(
            content={"error": "Task was already completed too recently"},
            status_code=409,
        )

    io.update_task_as_done(task_id, today, csv_path)

    tasks = io.import_tasks_from_csv(csv_path)
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
        **_rating_fields(updated_task),
    }


app.include_router(api)
