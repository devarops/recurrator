from fastapi import FastAPI

app = FastAPI()


def _build_task_ids():
    """Build list of task ID objects."""
    return [{"id": 8}]


@app.get("/tasks/")
def get_tasks():
    return _build_task_ids()
