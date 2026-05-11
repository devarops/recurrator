# Project State Analysis

This document describes the observable state of the project's public interfaces.

## API Endpoints

### GET /task/

Returns a JSON array of task ID objects.

- **Query parameters**: `csv` (string, path to CSV file)
- **Status code**: 200
- **Response**: `[<integer>, ...]`
- **Ordering**: Ascending by task ID

### GET /task/{id}

Returns a single task's full details as JSON.

- **Path parameters**: `id` (integer)
- **Query parameters**: `csv` (string, path to CSV file)
- **Status code**: 200
- **Response fields**:
  - `id` (integer)
  - `description` (string)
  - `context` (string, one of "casa", "laptop", "limpiar")
  - `skip_count` (integer)
  - `starred` (boolean)
  - `latest_date` (ISO 8601 date string)
  - `recurrence_days` (integer)
  - `due_date` (ISO 8601 date string)

### GET /context/

Returns unique context names from due/overdue tasks.

- **Query parameters**:
  - `csv` (string, path to CSV file)
  - `date` (ISO 8601 date string, reference date for determining due status)
- **Status code**: 200
- **Response**: `["casa", "laptop", "limpiar"]` — array of context name strings, sorted alphabetically

### GET /context/{context_id}

Returns task IDs that are due or overdue in the given context.

- **Path parameters**: `context_id` (string, one of "casa", "laptop", "limpiar")
- **Query parameters**:
  - `csv` (string, path to CSV file)
  - `date` (ISO 8601 date string, reference date for determining due status)
- **Status code**: 200
- **Response**: `[<integer>, ...]` — array of task IDs with due dates on or before the reference date

### POST /task/{id}/done

Marks a task as completed on today's date.

- **Path parameters**: `id` (integer)
- **Query parameters**: `csv` (string, path to CSV file)
- **Status code**: 200
- **Response fields**:
  - `id` (integer)
  - `skip_count` (integer, always 0 after completion)
  - `due_date` (ISO 8601 date string, differs from the previous due date)
- **Behavior**:
  - Rotates completion dates (date_1 ← date_2 ← date_3 ← date_4 ← completion_date)
  - Resets `skip_count` to 0
  - Recomputes `due_date` based on updated dates

## CLI Commands

### help

- Invoked without arguments
- Prints "Usage" text to stdout
- Exit code: 0

### list-all-tasks

Lists task IDs by querying the API.

- **Options**: `--csv` (string, required, path to CSV file)
- **Output**: Contains "id" and task ID numbers to stdout
- **Exit code**: 0 on success
- **Errors**: Prints error message to stderr and exits with code 1 on connection failure

## CSV Data Model

### Columns

Tasks are stored with at least these columns:
- `id` (integer)
- `context` (string enum)
- `description` (string)
- `date_1`, `date_2`, `date_3`, `date_4` (ISO 8601 dates or "NA")
- `skip_count` (integer)
- `skipped_date` (ISO 8601 date or "NA")
- `starred` (integer, 0 or 1)

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

## Context Enum Values

- `Context.CASA` = "casa"
- `Context.LAPTOP` = "laptop"
- `Context.LIMPIAR` = "limpiar"

## Core Functions

### `compute_intervals(dates: list[date | None]) -> list[int]`

Computes day intervals between consecutive non-None dates.

- **Parameters**: `dates` — A list of 4 date values (some may be None)
- **Returns**: List of integer day differences between consecutive non-None dates
- **Notes**: None values are filtered out before computing intervals

### `compute_latest_date(last_completion_date: date, skipped_date: date | None) -> date`

Returns the later of the last completion date and the skipped date.

- **Parameters**:
  - `last_completion_date` — The most recent completion date (never None)
  - `skipped_date` — The date the task was last skipped (may be None)
- **Returns**: The later of the two dates. Returns `last_completion_date` if `skipped_date` is None

### `compute_recurrence_days(intervals: Sequence[int | None]) -> int`

Computes recurrence days as the median of the given intervals.

- **Parameters**: `intervals` — A list of intervals (some may be None)
- **Returns**: The rounded median of non-None intervals. Returns 14 if all intervals are None
- **Notes**: None values are filtered out before computing the median

### `compute_due_date(latest_date: date, recurrence_days: int) -> date`

Adds recurrence days to the latest date to determine the next due date.

- **Parameters**:
  - `latest_date` — The reference date to add to
  - `recurrence_days` — Number of days to add
- **Returns**: `latest_date + recurrence_days`

### `filter_four_dates(dates: list[date | None], new_date: date) -> list[date | None]`

Keeps the 4 most recent dates from a combined list of existing dates and a new date.

- **Parameters**:
  - `dates` — A list of up to 4 dates (some may be None)
  - `new_date` — The date to incorporate
- **Returns**: A list of exactly 4 dates, sorted ascending, with the most recent 4 values. Pads with None on the left if fewer than 4 dates exist

### `filter_all_tasks_by_context(tasks: list[Task], context: Context) -> list[Task]`

Filters a list of tasks to return only those matching the given context.

- **Parameters**:
  - `tasks` — A list of Task objects
  - `context` — A Context enum value to filter by
- **Returns**: List of tasks whose context matches the given value

### `filter_due_tasks_by_context(tasks: list[Task], context: Context, reference_date: date) -> list[Task]`

Filters a list of tasks by both context and due/overdue status.

- **Parameters**:
  - `tasks` — A list of Task objects
  - `context` — A Context enum value to filter by
  - `reference_date` — The cutoff date for determining due status
- **Returns**: List of tasks whose context matches AND whose due_date is on or before reference_date

### `filter_due_tasks(tasks: list[Task], reference_date: date) -> list[Task]`

Filters a list of tasks by due/overdue status alone.

- **Parameters**:
  - `tasks` — A list of Task objects
  - `reference_date` — The cutoff date for determining due status
- **Returns**: List of tasks whose due_date is on or before reference_date, regardless of context

### `filter_due_contexts(tasks: list[Task], reference_date: date) -> list[Context]`

Returns the unique contexts of tasks that are due or overdue on or before the reference date, sorted alphabetically by context value.

- **Parameters**:
  - `tasks` — A list of Task objects
  - `reference_date` — The cutoff date for determining due status
- **Returns**: List of Context enum values, one per context that has at least one task with `due_date <= reference_date`. Sorted alphabetically by context value

### `import_tasks_from_csv(path: str) -> list[Task]`

Reads a CSV file and returns a list of Task objects with computed attributes.

- **Parameters**: `path` — Path to the CSV file
- **Returns**: List of Task objects, one per CSV row
- **Errors**: Raises ValueError if a task ID is not found

### `import_dates_from_csv(task_id: int, path: str) -> list[date | None]`

Returns the raw date values for a given task.

- **Parameters**:
  - `task_id` — The task ID to look up
  - `path` — Path to the CSV file
- **Returns**: A list of exactly 4 date values (None for "NA" entries)
- **Errors**: Raises ValueError if task_id is not found

### `update_task_dates(task_id: int, dates: list[date | None], path: str) -> None`

Updates the date_1 through date_4 fields for a task in the CSV file.

- **Parameters**:
  - `task_id` — The task ID to update
  - `dates` — A 4-element list of date values (elements may be None)
  - `path` — Path to the CSV file
- **Returns**: None
- **Notes**: Only modifies date columns; other fields are left unchanged

### `update_task_skip_count(task_id: int, skip_count: int, csv_path: str) -> None`

Updates the skip_count field for a task in the CSV file.

- **Parameters**:
  - `task_id` — The task ID to update
  - `skip_count` — The new skip count value
  - `csv_path` — Path to the CSV file
- **Returns**: None
- **Notes**: Only modifies the skip_count column; other fields are left unchanged

### `update_task_as_done(task_id: int, completion_date: date, csv_path: str) -> None`

Marks a task as completed by rotating dates and resetting the skip count.

- **Parameters**:
  - `task_id` — The task ID to mark as done
  - `completion_date` — The date the task was completed
  - `csv_path` — Path to the CSV file
- **Returns**: None
- **Behavior**:
  - Rotates completion dates using `filter_four_dates`
  - Resets skip_count to 0
  - Persists all changes to CSV file

### `get_task_by_id(task_id: int, csv_path: str) -> Task`

Retrieves a single Task object by its ID from a CSV file.

- **Parameters**:
  - `task_id` — The task ID to find
  - `csv_path` — Path to the CSV file
- **Returns**: A Task object with the matching ID
- **Errors**: Raises ValueError if task_id is not found
