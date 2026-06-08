from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import date

from . import compute, io
from ._config import DEFAULT_TASKS_CSV_PATH, WIP_LIMIT
from .models import Context

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve_csv_path(csv: str | None = None) -> str:
    """Resolve CSV path from query parameter or default."""
    return csv or DEFAULT_TASKS_CSV_PATH


def _task_to_dict(task: io.Task) -> dict:
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
    }


def _load_tasks_and_date(csv: str | None, reference_date: str) -> tuple:
    """Import tasks from CSV and parse the reference date."""
    csv_path = _resolve_csv_path(csv)
    tasks = io.import_tasks_from_csv(csv_path)
    parsed_reference_date = date.fromisoformat(reference_date)
    return tasks, parsed_reference_date


@app.get("/task/")
def get_all_tasks(csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    tasks = io.import_tasks_from_csv(csv_path)
    return [task.id for task in tasks]


@app.get("/task/{task_id}")
def get_task_by_id(task_id: int, csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    try:
        task = io.get_task_by_id(task_id, csv_path)
    except ValueError:
        return {"error": "Task not found"}, 404
    return _task_to_dict(task)


@app.get("/context/{context_id}")
def get_tasks_by_context(
    context_id: str,
    csv: str = Query(None),
    reference_date: str = Query(None, alias="date"),
):
    """Return prioritized task IDs for the given context."""
    tasks, parsed_reference_date = _load_tasks_and_date(csv, reference_date)
    context = Context(context_id)
    tasks_in_context = compute.filter_all_tasks_by_context(tasks, context)
    completed_today = compute.count_completed_today(tasks_in_context, parsed_reference_date)
    available_slots = compute.compute_available_wip_slots(WIP_LIMIT, completed_today)
    selected, deferred = compute.filter_n_tasks_by_context(
        tasks, context, parsed_reference_date, available_slots
    )
    csv_path = _resolve_csv_path(csv)
    for task in deferred:
        io.update_task_as_skipped(task.id, parsed_reference_date, csv_path)
    return [task.id for task in selected]


@app.get("/context/")
def get_due_contexts(csv: str = Query(None), reference_date: str = Query(None, alias="date")):
    """Return unique contexts from tasks due on or before the given date."""
    tasks, parsed_reference_date = _load_tasks_and_date(csv, reference_date)
    due_contexts = compute.filter_due_contexts(tasks, parsed_reference_date)
    return [context.value for context in due_contexts]


@app.post("/task/{task_id}/done")
def post_task_done(task_id: int, csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    today = date.today()

    last_completion_date = io.get_task_by_id(task_id, csv_path).latest_done_date
    if not compute.is_done_allowed(last_completion_date, today):
        return JSONResponse(
            content={"error": "Task was already completed too recently"},
            status_code=409,
        )

    io.update_task_as_done(task_id, today, csv_path)

    updated_task = io.get_task_by_id(task_id, csv_path)
    return {
        "id": updated_task.id,
        "skip_count": updated_task.skip_count,
        "due_date": updated_task.due_date.isoformat(),
    }
