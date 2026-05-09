from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date

from . import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_TASKS_CSV_PATH = "/root/.config/recurrator/tasks.csv"


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
    }


@app.get("/task/")
def get_all_tasks(csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    tasks = io.import_tasks_from_csv(csv_path)
    return [{"id": task.id} for task in tasks]


@app.get("/task/{task_id}")
def get_task_by_id(task_id: int, csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    try:
        task = io.get_task_by_id(task_id, csv_path)
    except ValueError:
        return {"error": "Task not found"}, 404
    return _task_to_dict(task)


@app.post("/task/{task_id}/done")
def post_task_done(task_id: int, csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    io.update_task_as_done(task_id, date.today(), csv_path)

    updated_task = io.get_task_by_id(task_id, csv_path)
    return {
        "id": updated_task.id,
        "skip_count": updated_task.skip_count,
        "due_date": updated_task.due_date.isoformat(),
    }
