from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .io import Task, import_tasks_from_csv

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


def _find_task_by_id(tasks, task_id: int):
    """Find a task by its ID in a list of tasks."""
    return next((t for t in tasks if t.id == task_id), None)


def _task_to_dict(task: Task) -> dict:
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


@app.get("/tasks/")
def get_tasks(csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    tasks = import_tasks_from_csv(csv_path)
    return [{"id": task.id} for task in tasks]


@app.get("/tasks/{task_id}")
def get_task(task_id: int, csv: str = Query(None)):
    csv_path = _resolve_csv_path(csv)
    tasks = import_tasks_from_csv(csv_path)
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        return {"error": "Task not found"}, 404
    return _task_to_dict(task)
