import typer

app = typer.Typer()


@app.command()
def list_all(name: str = typer.Argument(None)):
    """List all tasks."""
    from .io import import_tasks_from_csv
    tasks = import_tasks_from_csv("tests/data/test_single_task.csv")
    print("id")
