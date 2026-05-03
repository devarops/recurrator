# Plan: Add --csv Required Option to list-all CLI Command

## Context
- CLI currently calls `GET /tasks/` without CSV parameter
- API uses default CSV path `/root/.config/recurrator/tasks.csv`
- User changed the default CSV, so test data no longer matches
- We need to make CSV path explicit and required

## Implementation

### 1. Modify `recurrator/cli.py`

**Current (lines 16-26):**
```python
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
```

**New:**
```python
@app.command()
def list_all(csv: str = typer.Option(...)):
    """List all tasks."""
    try:
        response = requests.get(f"{API_BASE_URL}/tasks/?csv={csv}")
        response.raise_for_status()
        tasks = response.json()
        _print_task_ids(tasks)
    except requests.exceptions.RequestException as e:
        typer.echo(f"Error: Cannot connect to API at {API_BASE_URL} - {e}", err=True)
        raise typer.Exit(1)
```

**Changes:**
- Replace `name: str = typer.Argument(None)` with `csv: str = typer.Option(...)`
- Change API URL from `/tasks/` to `/tasks/?csv={csv}`

### 2. Update `tests/test_cli.py`

**Current (line 22):**
```python
result = runner.invoke(app, ["list-all"])
```

**New:**
```python
result = runner.invoke(app, ["list-all", "--csv", "tests/data/test_single_task.csv"])
```

## Files to Modify
1. `recurrator/cli.py` - Add required --csv option
2. `tests/test_cli.py` - Pass CSV path to test

## Testing
Run `docker exec recurrator_ci make tests` to verify all tests pass.