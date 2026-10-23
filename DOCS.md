# API Reference

Recurrator exposes one public interface: the task-data HTTP API in `recurrator/api.py`.
Every item listed below is an entry point of that API, and nothing outside the API is listed.
The frontend served at `/` and the `recurrator` CLI are clients of this API; the frontend is not an API entry point.

## Endpoints

### GET /task/

Returns the IDs of all tasks.

- **Query parameters**:
  - `csv` (string, optional) — path to the task data file; defaults to the configured file
- **Returns**: `[<integer>, ...]` — task IDs from the task data file
- **Notes**: The task data file must contain `id`, `context`, `description`, `date_1` through `date_4`, `skip_count`, `skip_date`, and `starred`. Dates are ISO 8601 or `NA`; `starred` is `0` or `1`.

### GET /task/{id}

Returns one task with its computed schedule.

- **Path parameters**:
  - `id` (integer) — task ID
- **Query parameters**:
  - `csv` (string, optional) — path to the task data file; defaults to the configured file
- **Returns**: An object with these fields:
  - `id` (integer)
  - `description` (string)
  - `context` (string)
  - `skip_count` (integer)
  - `starred` (boolean)
  - `latest_date` (ISO 8601 date string)
  - `recurrence_days` (integer)
  - `due_date` (ISO 8601 date string)
  - `coins` (integer)
- **Errors**: 404 when no task has the given ID
- **Notes**: `latest_date` is the later of the last completion date and the skip date. `recurrence_days` is the median interval between completions, defaulting to 14. `due_date` is `latest_date` plus `recurrence_days`. `coins` equals `recurrence_days`, doubled when the task is starred.

### GET /context/

Returns the contexts that have at least one due or overdue task.

- **Query parameters**:
  - `csv` (string, optional) — path to the task data file; defaults to the configured file
  - `date` (ISO 8601 date string, required) — reference date for due status
- **Returns**: `["<context>", ...]` — context names sorted alphabetically
- **Notes**: A task is due when its `due_date` is on or before `date`.

### GET /context/{context_id}

Returns prioritized task IDs for one context, limited by available work-in-progress capacity.

- **Path parameters**:
  - `context_id` (string) — a configured context value
- **Query parameters**:
  - `csv` (string, optional) — path to the task data file; defaults to the configured file
  - `date` (ISO 8601 date string, required) — reference date for due status
- **Returns**: `[<integer>, ...]` — selected task IDs
- **Notes**: Tasks completed on `date` reduce the available capacity. Surplus non-starred tasks are deferred: their `skip_count` is incremented and `skip_date` is set to `date`, so this read endpoint also writes to the task data file.

### POST /task/{id}/done

Marks a task as completed on the server's current date.

- **Path parameters**:
  - `id` (integer) — task ID
- **Query parameters**:
  - `csv` (string, optional) — path to the task data file; defaults to the configured file
- **Returns**: An object with these fields:
  - `id` (integer)
  - `skip_count` (integer) — always 0 after completion
  - `due_date` (ISO 8601 date string) — recomputed next due date
- **Errors**: 409 when the task was completed on the current date or the previous day; the body contains an `error` message
- **Notes**: The four stored completion dates shift forward, the new date becomes the latest, and the skip count resets. Completion uses the `America/Los_Angeles` calendar date.
