import typer
import requests  # type: ignore[import-untyped]

app = typer.Typer(no_args_is_help=True)

API_BASE_URL = "http://api:8000"


def _print_task_ids(tasks):
    """Print task IDs in a readable format."""
    print("id")
    for task in tasks:
        print(task["id"])


@app.command()
def version():
    """Show the version of recurrator."""
    typer.echo("recurrator v0.1.0")


@app.command(name="list-all-tasks")
def list_all_tasks(csv: str = typer.Option(..., "--csv", help="Path to CSV file")):
    """List all tasks."""
    try:
        response = requests.get(f"{API_BASE_URL}/task/", params={"csv": csv})
        response.raise_for_status()
        tasks = response.json()
        _print_task_ids(tasks)
    except requests.exceptions.RequestException as e:
        typer.echo(f"Error: Cannot connect to API at {API_BASE_URL} - {e}", err=True)
        raise typer.Exit(1)
