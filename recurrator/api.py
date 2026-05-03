from fastapi import FastAPI

app = FastAPI()


def _build_task_ids():
    """Build list of task ID objects."""
    return [{"id": 8}]


def _build_task_8():
    """Build task 8 object."""
    return {"id": 8, "description": "TypeLit.io", "context": "laptop", "skip_count": 1, "starred": False, "latest_date": "2025-08-19", "recurrence_days": 14, "due_date": "2025-09-02"}


@app.get("/tasks/")
def get_tasks():
    return _build_task_ids()


@app.get("/tasks/8")
def get_task_8():
    return _build_task_8()
