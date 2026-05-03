from fastapi import FastAPI, Query

from .io import import_tasks_from_csv

app = FastAPI()

DEFAULT_CSV_PATH = "tests/data/test_single_task.csv"


def _task_to_dict(task) -> dict:
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
    csv_path = csv or DEFAULT_CSV_PATH
    tasks = import_tasks_from_csv(csv_path)
    return [{"id": task.id} for task in tasks]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    tasks = import_tasks_from_csv(DEFAULT_CSV_PATH)
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        return {"error": "Task not found"}, 404
    return _task_to_dict(task)
