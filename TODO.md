# Gold (TDD Target)

## Current: CLI command `list-all`
- **Description**: A Typer command that loads tasks from the default CSV file and displays them in a readable format showing id, description, context, skip_count, starred, latest_date, recurrence_days, and due_date for each task.
- **Status**: Not Started

---

## Implementation Status

### Functions Implemented
- `compute_intervals(dates: list[date | None]) -> list[int]` (in `compute.py`): Compute intervals in days between consecutive non-None dates
- `compute_latest_date(date_4, skipped_date) -> date` (in `compute.py`): Returns max of two dates, handling None for skipped_date only
- `compute_recurrence_days(intervals) -> int` (in `compute.py`): Compute recurrence days as median of intervals, defaulting to 14 days
- `compute_due_date(latest_date, recurrence_days) -> date` (in `compute.py`): Return next due date by adding recurrence_days to latest_date
- `_parse_date(date_str) -> date | None` (in `io.py`): Helper to parse ISO 8601 strings, returns None for "NA"
- `_row_to_task(row: dict) -> Task` (in `io.py`): Helper to convert CSV row to Task object
- `_compute_dates(row: dict) -> ComputedDates` (in `io.py`): Compute latest_date, recurrence_days, and due_date from CSV row
- `import_tasks_from_csv(path) -> list[Task]` (in `io.py`): Import tasks from CSV file

### Classes Defined
- `ComputedDates` (in `io.py`): Dataclass grouping computed date attributes (latest_date, recurrence_days, due_date)

### Refactorings Applied
- Extract Function (`_parse_date`, `_row_to_task`, `_compute_dates`)
- Add Parameter (`Task.__init__` — added `recurrence_days`, `computed_dates`)
- Replace Loop with Pipeline (list comprehensions)
- Replace Magic Number with Symbolic Constant (`DEFAULT_RECURRENCE_DAYS = 14`)
- Standardize None Handling (made `compute_intervals` handle None internally like `compute_latest_date`)
- Introduce Parameter Object (grouped computed dates into `ComputedDates` dataclass)
- Rejected refactorings that sacrificed readability for fewer lines

---

## Completed

### CLI command `import_tasks_from_csv(path)`
- Status: ✅ Complete

---

## Chores

- [x] Verify `compute_latest_date(date_4, skipped_date)` returns `date_4` if `skipped_date` is `None`
