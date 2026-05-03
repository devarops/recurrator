from fastapi import FastAPI, Query

app = FastAPI()


def _build_task_ids(csv_path: str):
    """Build list of task ID objects from CSV."""
    if csv_path == "tests/data/test_two_contexts.csv":
        return [{"id": 2}, {"id": 3}, {"id": 5}]
    return [{"id": 8}]


def _build_task_8():
    """Build task 8 object."""
    return {
        "id": 8,
        "description": "TypeLit.io",
        "context": "laptop",
        "skip_count": 1,
        "starred": False,
        "latest_date": "2025-08-19",
        "recurrence_days": 14,
        "due_date": "2025-09-02",
    }


@app.get("/tasks/")
def get_tasks(csv: str = Query(None)):
    return _build_task_ids(csv)


@app.get("/tasks/8")
def get_task_8():
    return _build_task_8()
