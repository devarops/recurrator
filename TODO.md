# Project Roadmap

## Gold (Final Target System)

### API + CLI Architecture
**Primary Interface**: FastAPI REST API (single source of truth)
**Secondary Interface**: CLI thin wrapper (optional, calls API)
**Storage**: CSV at `~/.config/recurrator/tasks.csv` (mounted via Docker volume)
**Deployment**: Docker Compose

**Features**:
- ✅ API: `GET /tasks/` — List task IDs only
- ⏳ API: `GET /tasks/:id` — Get single task with all fields
- ⏳ API: `POST /tasks/:id/done` — Mark task as done (resets skip_count, rotates dates)
- ⏳ CLI: `list-all`, `show-task`, `mark-done` (thin wrappers calling API)

**Current Vertical Slice**: API Layer - List Tasks
- Status: 🚧 In Progress
- Next: Implement `GET /tasks/` endpoint returning list of task IDs

---

## Implementation Status

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

### API Functions (api.py) — Planned
- ⏳ `GET /tasks/` endpoint
- ⏳ `GET /tasks/:id` endpoint
- ⏳ `POST /tasks/:id/done` endpoint

### Write Operations (services.py) — Planned
- ⏳ `mark_task_done(task_id)` — Update task on completion

### CLI Commands (cli.py) — Refactoring Pending
- 🚧 `list-all` — Currently prints task IDs; needs refactoring to call API
- ⏳ `show-task` — Thin wrapper around `GET /tasks/:id`
- ⏳ `mark-done` — Thin wrapper around `POST /tasks/:id/done`

---

## Refactorings Applied

### I/O Module (io.py)
- Extract Function: `_parse_date()`, `_row_to_task()`, `_compute_dates()`
- Introduce Parameter Object: `ComputedDates` dataclass
- Standardize None Handling: Made `compute_intervals()` handle None internally
- Replace Magic Number with Symbolic Constant: `DEFAULT_RECURRENCE_DAYS = 14`

### CLI Module (cli.py) — Latest
- Move import to module level (PEP 8 standard)
- Extract magic string constant: `DEFAULT_TASKS_CSV_PATH`
- Extract function: `_print_task_ids()` for output logic

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
