import typer
import requests

app = typer.Typer()

API_BASE_URL = "http://api:8000"


def _print_task_ids(tasks):
    """Print task IDs in a readable format."""
    print("id")
    for task in tasks:
        print(task["id"])


@app.command()
def list_all(name: str = typer.Argument(None)):
    """List all tasks."""
    try:
        response = requests.get(f"{API_BASE_URL}/tasks/")
        response.raise_for_status()
        tasks = response.json()
        _print_task_ids(tasks)
    except requests.exceptions.RequestException as e:
        typer.echo(f"Error: Cannot connect to API at {API_BASE_URL} - {e}", err=True)
        raise typer.Exit(1)
