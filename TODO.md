# Project Roadmap

## Gold (TDD Target)

### CLI command `list-all`
**Description**: A Typer command that loads tasks from the default CSV file and displays them in a readable format showing: `id`, `description`, `context`, `skip_count`, `starred`, `latest_date`, `recurrence_days`, and `due_date` for each task.

**Current Status**: 🚧 In Progress
- ✅ Loads tasks from CSV
- ✅ Prints task IDs
- ⏳ Remaining: Display all required fields in readable format

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

### CLI Commands (cli.py)
- 🚧 `list-all` — List all tasks with computed fields

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
