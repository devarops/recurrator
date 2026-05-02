import typer

from .io import import_tasks_from_csv

app = typer.Typer()

DEFAULT_TASKS_CSV_PATH = "tests/data/test_single_task.csv"


def _print_task_ids(tasks):
    """Print task IDs in a readable format."""
    print("id")
    for task in tasks:
        print(task.id)


@app.command()
def list_all(name: str = typer.Argument(None)):
    """List all tasks."""
    tasks = import_tasks_from_csv(DEFAULT_TASKS_CSV_PATH)
    _print_task_ids(tasks)
