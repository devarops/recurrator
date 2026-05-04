# Project State Analysis Based on Test Suite

This document describes the observable state of the project as revealed by the test suite (18 passing tests).

## API Endpoints

### GET /tasks/
- Returns a JSON array of task ID objects
- Each object contains an `id` field (integer)
- Query parameter: `csv` (path to CSV file)
- Returns list ordered by task ID when multiple tasks present
- Status code: 200

### GET /tasks/{id}
- Returns full task object as JSON
- Query parameter: `csv` (path to CSV file)
- Status code: 200
- Response format includes:
  - `id` (integer)
  - `description` (string)
  - `context` (string, enum: "laptop", "limpiar")
  - `skip_count` (integer)
  - `starred` (boolean)
  - `latest_date` (ISO 8601 date string)
  - `recurrence_days` (integer)
  - `due_date` (ISO 8601 date string)

## CLI Commands

### help
- Works without arguments
- Displays "Usage" text

### list-all
- Accepts `--csv` parameter (path to CSV file)
- Outputs task ID data to stdout
- Output contains "id" and task ID numbers

## CSV Data Model

### Columns
Tasks are stored with at least these columns (verified by tests):
- `id` (integer)
- `context` (string enum)
- `description` (string)
- `date_1`, `date_2`, `date_3`, `date_4` (ISO 8601 dates or "NA")
- `skip_count` (integer)
- `skipped_date` (ISO 8601 date or "NA")
- `starred` (binary: 0 or 1)

### Data Examples
- Single task CSV: Contains task with id=8, description="TypeLit.io", context="laptop"
- Multi-task CSV: Contains tasks with ids 2, 3, 5 with contexts "casa" and "limpiar"

## Task Object Model

A Task has the following attributes:
- `id`: integer identifier
- `description`: string
- `context`: Context enum (CASA, LAPTOP, LIMPIAR)
- `skip_count`: integer
- `starred`: boolean
- `latest_date`: computed date (the later of date_4 or skipped_date)
- `recurrence_days`: computed integer (median of intervals between dates, defaults to 14)
- `due_date`: computed date (latest_date + recurrence_days)

## Core Functions

### compute_intervals(dates: list[date | None]) -> list[int]
- Accepts a list of dates (some may be None)
- Returns list of day intervals between consecutive non-None dates
- Filters out None values before computing intervals
- Example: [None, None, 2024-01-02, 2024-01-04] → [2]

### compute_latest_date(date_4: date, skipped_date: date | None) -> date
- Takes the maximum of date_4 and skipped_date
- If skipped_date is None, returns date_4
- Always returns a date (not None)

### compute_recurrence_days(intervals: list) -> int
- Accepts list of intervals
- Returns median of intervals
- Returns 14 (default) if all intervals are None

### compute_due_date(latest_date: date, recurrence_days: int) -> date
- Adds recurrence_days to latest_date
- Returns the computed due date

### filter_four_dates(dates: list[date | None], new_date: date) -> list[date | None]
- Takes a list of (up to) 4 dates with possible None values and a new date
- Combines dates, filters out None values, sorts them, and keeps the 4 most recent
- Pads with None values at the start if fewer than 4 dates exist
- Returns exactly 4 dates
- Example: [None, None, 2024-01-02, 2024-01-04] + 2024-01-06 → [None, 2024-01-02, 2024-01-04, 2024-01-06]

### import_tasks_from_csv(path: str) -> list[Task]
- Reads CSV file and returns list of Task objects
- Each row in CSV becomes a Task with computed attributes
- Raises ValueError if task not found (implicit from signature change)

### import_dates_from_csv(task_id: int, path: str) -> list[date | None]
- Returns list of exactly 4 dates for a given task
- Raises ValueError if task_id not found in CSV
- Returns None for "NA" values in date columns

### update_task_dates(task_id: int, dates: list[date | None], path: str) -> None
- Updates date_1, date_2, date_3, date_4 for a task in CSV
- Accepts a 4-element list of dates (elements may be None)
- Persists changes to CSV file
- Does not modify other fields or restore file state on error

### update_task_skip_count(task_id: int, skip_count: int, csv_path: str) -> None
- Updates skip_count field for a task in CSV
- Persists changes to CSV file
- Does not modify other fields

### update_task_as_done(task_id: int, completion_date: date, csv_path: str) -> None
- Marks a task as completed on a specific date
- Rotates completion dates: date_1 ← date_2 ← date_3 ← date_4 ← completion_date
- Uses filter_four_dates to perform date rotation
- Resets skip_count to 0
- Persists all changes to CSV file

## Test Data

### test_single_task.csv
- Contains one task: id=8, description="TypeLit.io", context="laptop", skip_count=1

### test_two_contexts.csv
- Contains three tasks: ids 2, 3, 5
- Task 2: context="casa", description="Vaciar cajón", skip_count=10
- Task 3: context="limpiar", description="Lavar trapos", skip_count=0
- Task 5: context="limpiar", description="Limpiar ventanas", skip_count=1

## Context Enum Values

From test imports and usage:
- CASA = "casa"
- LAPTOP = "laptop"
- LIMPIAR = "limpiar"

## Guarantees from Tests

- All 18 tests pass with 100% success rate
- CSV file state is preserved after test operations (verified via MD5 checksums in destructive tests)
- Task import correctly parses CSV data and computes derived attributes
- Date operations maintain chronological ordering
- None values in date fields are properly handled
- skip_count can be set to any integer value
- Multiple tasks can coexist in a single CSV file with different contexts
