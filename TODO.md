# Project Roadmap

## Gold (Final Target System)

### API + CLI Architecture
**Primary Interface**: FastAPI REST API (single source of truth)
**Secondary Interface**: CLI thin wrapper (optional, calls API)
**Storage**: CSV at `~/.config/recurrator/tasks.csv` (mounted via Docker volume)
**Deployment**: Docker Compose (two services: `api` + `cli`)

**Features**:
- ✅ API: `GET /tasks/` — List task IDs only
- ✅ API: `GET /tasks/:id` — Get single task with all fields
- ⏳ API: `POST /tasks/:id/done` — Mark task as done (resets skip_count, rotates dates)
- ✅ CLI: `list-all` — List all tasks (thin wrapper calling API)
- ⏳ CLI: `show-task` — Show single task (thin wrapper calling API)
- ⏳ CLI: `mark-done` — Mark task as done (thin wrapper calling API)

**Current Vertical Slice**: API Layer - Complete (Reads)
- Status: ✅ Complete
- Next: Implement write operations (POST /tasks/:id/done)

---

## Implementation Status

### Architecture Status
- ✅ FastAPI app created in `recurrator/api.py`
- ✅ Two-service Docker Compose (`api` + `cli`) with `depends_on: api`
- ✅ CLI migrated to HTTP calls (Plan A - thin wrapper calling API)
- ✅ All 13 tests passing (no mocks, integration-style)

### Static Frontend (public/index.html)
- ✅ Created decoupled HTML task viewer (42 lines)
- ✅ Pico.css styling (10KB CDN) for clean presentation
- ✅ Minimal JavaScript (~15 lines) for fetch and render
- ✅ HTML table layout for task details
- ✅ CSV parameter support (`?csv=tests/data/test_two_contexts.csv`)
- ✅ CORS middleware added to API for file:// protocol support
- ✅ Error handling for API unavailability

### Core Functions (compute.py)
- ✅ `compute_intervals(dates)` — Compute intervals in days between consecutive non-None dates
- ✅ `compute_latest_date(date_4, skipped_date)` — Return max of two dates, handling None for skipped_date
- ✅ `compute_recurrence_days(intervals)` — Compute median interval, default 14 days
- ✅ `compute_due_date(latest_date, recurrence_days)` — Return next due date

### I/O Functions (io.py)
- ✅ `_parse_date(date_str)` — Parse ISO 8601 strings, return None for "NA"
- ✅ `_row_to_task(row)` — Convert CSV row to Task object
- ✅ `_compute_dates(row)` — Compute latest_date, recurrence_days, due_date from CSV
- ✅ `import_tasks_from_csv(path)` — Load tasks from CSV file

### Data Classes (io.py)
- ✅ `ComputedDates` — Dataclass grouping computed date attributes

### API Functions (api.py) — Implemented
- ✅ `GET /tasks/` endpoint — Returns list of task IDs
- ✅ `GET /tasks/:id` endpoint — Returns full task object
- ⏳ `POST /tasks/:id/done` endpoint — Mark task as done (pending)

### Write Operations (services.py) — Planned
- ⏳ `mark_task_done(task_id)` — Update task on completion

### CLI Commands (cli.py) — Partially Implemented
- ✅ `list-all` — Calls `GET /tasks/` via API (implemented)
- ⏳ `show-task` — Calls `GET /tasks/:id` via API (pending)
- ⏳ `mark-done` — Calls `POST /tasks/:id/done` via API (pending)

---

## Refactorings Applied

### I/O Module (io.py)
- Extract Function: `_parse_date()`, `_row_to_task()`, `_compute_dates()`
- Introduce Parameter Object: `ComputedDates` dataclass
- Standardize None Handling: Made `compute_intervals()` handle None internally
- Replace Magic Number with Symbolic Constant: `DEFAULT_RECURRENCE_DAYS = 14`

### API Module (api.py) — Latest
- Extract Function: `_resolve_csv_path()` for CSV path resolution
- Extract Function: `_find_task_by_id()` for task lookup
- Extract Function: `_task_to_dict()` for Task to dict conversion
- Add Type Hints: `_task_to_dict(task: Task) -> dict`
- Rename Constant: `DEFAULT_TASKS_CSV_PATH` (clearer naming)

### CLI Module (cli.py) — Migrated to Plan A
- Remove CSV Import: Removed `from .io import import_tasks_from_csv`
- Remove Local Constant: Removed `DEFAULT_TASKS_CSV_PATH` (now in API)
- Add HTTP Client: Added `import requests` and `API_BASE_URL = "http://api:8000"`
- Refactor `list_all()`: Now calls `GET /tasks/` via HTTP
- Update `_print_task_ids()`: Handles dicts from API JSON response
- Add Error Handling: Clear message when API unavailable, exit code 1

---

## Mark-Done Specification

When `POST /tasks/:id/done` is called:

1. **Skip Count**: Reset to 0
2. **Completion Dates Rotation** (CSV columns):
   - Drop previous `date_1` (oldest completion)
   - Shift: `date_2` → `date_1`
   - Shift: `date_3` → `date_2`
   - Shift: `date_4` → `date_3`
   - Set: `date_4` ← today's date (ISO 8601)
3. **Skipped Date**: Leave unchanged (handled by `compute_latest_date()`)
4. **Recurrence & Due Date**: 
   - **NOT recalculated on completion** (will be handled by separate batch process at midnight)
   - Remain as-is until next scheduled recalculation
5. **Response**: `{"status": "success", "id": <id>}`

**Implementation**: New function `mark_task_done(task_id: int) -> bool` in `io.py` or `services.py`

---

## Pending Refactorings

### Centralize Configuration in JSON
**Status**: Planned  
**Motivation**: Constants `DEFAULT_RECURRENCE_DAYS` and `DEFAULT_TASKS_CSV_PATH` are scattered across modules. Centralize for easier maintenance.

**Design**:
- Config file: `~/.config/recurrator/config.json` (XDG Base Directory standard)
- Production CSV path: `~/.config/recurrator/tasks.csv`
- Test CSV files: Remain in `tests/data/` (testing only)

**Implementation**:
1. Create `recurrator/config_loader.py` with `load_config()` function
2. Create `~/.config/recurrator/config.json`:
   ```json
   {
     "default_recurrence_days": 14,
     "default_tasks_csv_path": "~/.config/recurrator/tasks.csv"
   }
   ```
3. Update `compute.py` to load `default_recurrence_days` from config
4. Update `cli.py` to load `default_tasks_csv_path` from config
5. Verify all tests pass (tests still use `tests/data/` artifacts)

**Files Affected**: `compute.py`, `cli.py`, `config_loader.py` (new), `config.json` (new)

---

## Design Principles

- **Readability over brevity**: Clear variable names and extracted functions express intent
- **Explicit imports**: All dependencies visible at module level (PEP 8)
- **Single responsibility**: Helper functions (`_parse_date`, `_print_task_ids`, etc.) do one thing well
- **Test-driven**: Only implement what tests require; generalize safely

---

## Future Features

### Gamification System
**Status**: Planned  
**Motivation**: Add point accumulation for completed tasks. Points accumulate daily and can be expended.

**Design**:
- Task completion awards configurable points
- Points stored in task metadata or separate ledger
- Daily point accumulation
- Point expenditure mechanism (TBD)

**Implementation**: Deferred until after write operations (mark-done) are complete

**User Story**: "A small gamification layer awards points for each completed task, and these points accumulate daily until you choose to expend them."
