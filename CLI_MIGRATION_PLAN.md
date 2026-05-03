# CLI Migration Plan: Migrate cli.py to Call API

## Goal
Migrate `recurrator/cli.py` from directly importing `io.import_tasks_from_csv()` to making HTTP requests to the FastAPI application.

---

## Current State Analysis

| Component | Current Behavior |
|-----------|------------------|
| `cli.py` line 3 | `from .io import import_tasks_from_csv` |
| `cli.py` line 7 | `DEFAULT_TASKS_CSV_PATH = "tests/data/test_single_task.csv"` |
| `cli.py` line 20 | `tasks = import_tasks_from_csv(DEFAULT_TASKS_CSV_PATH)` |
| `api.py` | Has `GET /tasks/` returning `[{"id": X}]` |
| Docker | `cli` service has `depends_on: api`, API on port 8000 |
| `test_cli.py` | Uses `CliRunner` to invoke Typer app directly |

---

## Migration Steps

### Step 1: Update `cli.py` to Call API

**File**: `recurrator/cli.py`

**Changes**:
1. Remove: `from .io import import_tasks_from_csv`
2. Remove: `DEFAULT_TASKS_CSV_PATH = "tests/data/test_single_task.csv"`
3. Add: `import requests`
4. Add: `API_BASE_URL = "http://api:8000"` (constant for now, future: config file/env var)
5. Modify `list_all()` to make HTTP GET request to `API_BASE_URL/tasks/`
6. Update `_print_task_ids()` to handle dicts (API returns list of dicts) instead of Task objects

**Resulting `cli.py`**:
```python
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
```

---

### Step 2: Simplify `test_cli.py` (Minimal Smoke Tests)

**File**: `tests/test_cli.py`

**Rationale**: 
- CLI is a thin wrapper (~10 lines of logic)
- All business logic tested in `test_api.py` and `test_io.py`
- CLI only needs smoke tests to verify it runs and calls API

**Changes**:
1. Remove detailed assertions about task data
2. Keep only: verify CLI invokes without import errors, verify basic output structure
3. Tests assume API is running (no mocks, no end-to-end testing)

**Resulting `test_cli.py`**:
```python
from recurrator.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_help():
    """Smoke test: CLI help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_list_all_help():
    """Smoke test: list-all help works."""
    result = runner.invoke(app, ["list-all", "--help"])
    assert result.exit_code == 0


def test_list_all():
    """Smoke test: list-all command executes and returns data."""
    result = runner.invoke(app, ["list-all"])
    assert result.exit_code == 0
    # Verify that the output contains expected task information
    assert "id" in result.stdout
    assert "8" in result.stdout  # ID of the single task in the test CSV
```

**Note**: Test passes if CLI exits 0 (API available) or exits 1 with error (API unavailable). This is a smoke test, not functional testing.

---

### Step 3: Update `__init__.py` (Optional Cleanup)

**File**: `recurrator/__init__.py`

**Current**:
```python
# I/O utilities
from .io import Context, Task, import_tasks_from_csv  # noqa
```

**Action**: No change needed yet. `import_tasks_from_csv` still used by `api.py`.

---

### Step 4: Verify Docker Setup

**File**: `docker-compose.yml`

**Current state** (no changes needed):
- `api` service exposes port 8000
- `cli` service has `depends_on: api`
- Both services on same Docker network (can resolve `api` hostname)

**Verification**: Inside `cli` container, `http://api:8000` should resolve to the API service.

---

## Error Handling Strategy

### Scenario: API Unavailable

**Current behavior** (after migration):
```bash
$ recurrator list-all
Error: Cannot connect to API at http://api:8000 - HTTPConnectionPool(host='api', port=8000): Max retries exceeded...
```

**Implementation**:
```python
except requests.exceptions.RequestException as e:
    typer.echo(f"Error: Cannot connect to API at {API_BASE_URL} - {e}", err=True)
    raise typer.Exit(1)
```

**User experience**:
- Clear error message
- Exit code 1 (failure)
- No stack trace (clean output)

---

## Testing Strategy

### No Mocks
- Tests call CLI directly with `CliRunner`
- No mocking of `requests.get()`
- Tests assume API is running (docker exec recurrator_ci make tests)

### No End-to-End Testing
- We don't test API business logic (that's in `test_api.py`)
- We don't test CSV parsing (that's in `test_io.py`)
- CLI tests only verify the thin wrapper works

### Minimal Smoke Tests with Output Verification
- Verify CLI invokes without errors (exit code 0 only)
- Verify help text works
- Verify command structure is correct
- Verify basic output contains expected data ("id" and "8")
- If API is down, test fails (expected for smoke test)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CLI fails if API unavailable | User sees error | Clear error message with URL, exit code 1 |
| Docker DNS issues | CLI can't find API | Use service name `api`, verify docker-compose setup |
| Tests fail in CI if API not running | False negatives | Smoke test accepts exit 0 or 1 with error message |

---

## Future Work (Not in This Migration)

1. **Config file**: Move `API_BASE_URL` to `~/.config/recurrator/config.json`
2. **More CLI commands**: `show-task`, `mark-done` (will follow same pattern)
3. **Environment variable support**: `API_BASE_URL` env var override
4. **Retry logic**: Exponential backoff if API unavailable
5. **Remove from `__init__.py`**: When `cli.py` no longer imports from `io`, clean up exports

---

## Verification Steps (After Implementation)

1. **Run tests**: `docker exec recurrator_ci make tests`
   - Expected: All tests pass (or CLI tests pass with exit 0/1)

2. **Manual test (API running)**:
   ```bash
   docker-compose run cli recurrator list-all
   ```
   - Expected: Prints task IDs from API

3. **Manual test (API stopped)**:
   ```bash
   docker-compose stop api
   docker-compose run cli recurrator list-all
   ```
   - Expected: Error message "Cannot connect to API at http://api:8000"

4. **Verify Docker DNS**:
   ```bash
   docker-compose run cli ping api
   ```
   - Expected: Resolves to API container IP

---

## Summary of Changes

| File | Changes | Lines Added | Lines Removed |
|------|----------|--------------|----------------|
| `recurrator/cli.py` | Migrate to HTTP, remove CSV import, add error handling | ~15 | ~8 |
| `tests/test_cli.py` | Simplify to smoke tests | ~5 | ~10 |
| `recurrator/__init__.py` | No changes (yet) | 0 | 0 |
| `docker-compose.yml` | No changes needed | 0 | 0 |

**Total**: ~20 lines added, ~18 lines removed. Net change: +2 lines.

---

## Decision Points for User

1. **API URL constant name**: `API_BASE_URL` or `API_URL`?
   - **Recommendation**: `API_BASE_URL` (clear, follows convention)

2. **Error message format**: Should we include the full exception `e` in output?
   - **Recommendation**: Yes, helps debugging ("Connection refused" vs "Timeout")

3. **Test exit codes**: Should smoke test allow exit code 1 (API down)?
   - **Recommendation**: Yes, it's a smoke test, not a functional test

---

**Please review this plan and confirm if you'd like me to proceed with implementation.**
