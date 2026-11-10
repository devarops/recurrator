# API Reference

Recurrator exposes one public interface: the task-data HTTP API in `recurrator/api.py`.
Every item listed below is an entry point of that API, and nothing outside the API is listed.
The frontend served at `/` and the `recurrator` CLI are clients of this API; the frontend is not an API entry point.

Every entry point accepts the same optional query parameter:

- `csv` (string) — path to the task data file; defaults to the configured file

A task is due when its `due_date` is on or before the reference date. Reference dates are ISO 8601 (`YYYY-MM-DD`).

## Endpoints

### GET /task/

Returns the IDs of all tasks.

- **Returns**: `[<integer>, ...]` — every task ID in the task data file, in file order
- **Notes**: The task data file must contain `id`, `context`, `description`, `date_1` through `date_4`, `skip_count`, `skip_date`, and `starred`. Dates are ISO 8601 or `NA`; `starred` is `0` or `1`. `rating_date` is optional; without it the last completion date anchors the deviation.
- **Notes**: A `date` query parameter has no effect; due filtering is expressed in the path.

### GET /task/due/{date}

Returns the IDs of the tasks due on or before a date.

- **Path parameters**:
  - `date` (ISO 8601 date) — reference date
- **Returns**: `[<integer>, ...]` — task IDs whose due date is on or before `date`, in file order
- **Notes**: Read-only.

### GET /task/due/

Returns the IDs of the tasks due on or before today.

- **Returns**: `[<integer>, ...]` — the same IDs as `GET /task/due/{date}` for today's date in `America/Los_Angeles`
- **Notes**: Read-only.

### GET /task/{id}

Returns one task with its computed schedule.

- **Path parameters**:
  - `id` (integer) — task ID
- **Query parameters**:
  - `date` (ISO 8601 date, optional) — reference date for projecting `rating_deviation`; without it the deviation is projected to today
- **Returns**: An object with these fields:
  - `id` (integer)
  - `description` (string)
  - `context` (string)
  - `skip_count` (integer)
  - `starred` (boolean)
  - `latest_date` (ISO 8601 date string)
  - `latest_done_date` (ISO 8601 date string)
  - `recurrence_days` (integer)
  - `due_date` (ISO 8601 date string)
  - `coins` (integer)
  - `rating` (integer)
  - `rating_deviation` (integer)
- **Errors**: 404 when no task has the given ID
- **Notes**: `latest_date` is the later of the last completion date and the skip date. `latest_done_date` is the last completion date itself, unaffected by the skip date. `recurrence_days` is the median interval between completions, defaulting to 14. `due_date` is `latest_date` plus `recurrence_days`. `coins` equals `recurrence_days`, doubled when the task is starred. `rating_deviation` is projected to `date` when provided; otherwise it is projected to today.

### GET /search/

Returns the tasks whose description matches a query.

- **Query parameters**:
  - `query` (string, optional) — text to match against each description; without it, every task is returned
- **Returns**: `[{...}, ...]` — full task objects, with the same fields as `GET /task/{id}`, in an order the API does not define
- **Errors**: 400 when `query` is present but empty, or shorter than three characters after trimming; the body contains an `error` message
- **Notes**: A description matches when its similarity to the query is at least 80, measured with RapidFuzz's WRatio after folding case and accents. Only `description` is matched; context names are not. The query is trimmed before the length check and before matching. Read-only.

### GET /context/

Returns the contexts named in the task data file.

- **Returns**: `["<context>", ...]` — every context that at least one task names, sorted alphabetically
- **Notes**: A context with no due task is listed. A `date` query parameter has no effect; due filtering is expressed in the path.

### GET /context/due/{date}

Returns the contexts with at least one task due on or before a date.

- **Path parameters**:
  - `date` (ISO 8601 date) — reference date
- **Returns**: `["<context>", ...]` — context names sorted alphabetically
- **Notes**: Read-only.

### GET /context/due/

Returns the contexts with at least one task due on or before today.

- **Returns**: `["<context>", ...]` — the same contexts as `GET /context/due/{date}` for today's date in `America/Los_Angeles`
- **Notes**: Read-only.

### GET /context/{context_id}

Returns every task ID in one context.

- **Path parameters**:
  - `context_id` (string) — a context named by at least one task in the task data file
- **Returns**: `[<integer>, ...]` — every task ID in that context, in file order
- **Errors**: 404 when no task names the given context
- **Notes**: Read-only; it does not change `skip_count` or `skip_date`.

### GET /context/{context_id}/due/{date}

Returns prioritized task IDs for one context, limited by available work-in-progress capacity.

- **Path parameters**:
  - `context_id` (string) — a context named by at least one task in the task data file
  - `date` (ISO 8601 date) — reference date
- **Returns**: `[<integer>, ...]` — selected task IDs in priority order
- **Errors**: 404 when no task names the given context
- **Notes**: Tasks completed on `date` reduce the available capacity. Surplus non-starred tasks are deferred: their `skip_count` is incremented and `skip_date` is set to `date`, so this read endpoint also writes to the task data file. Deferred tasks are not returned.

### GET /scope/

Returns the stored scopes.

- **Returns**: `["<scope>", ...]` — scope names sorted alphabetically
- **Notes**: Scopes come from the context data; the current data stores `both`, `personal`, and `work`. The `all` alias is not a stored scope and is not listed.

### GET /scope/{scope_id}/

Returns the contexts in a scope.

- **Path parameters**:
  - `scope_id` (string) — a stored scope, or `all`
- **Returns**: `["<context>", ...]` — the contexts that belong to the scope and are named by at least one task, sorted alphabetically
- **Errors**: 404 when `scope_id` is neither a stored scope nor `all`
- **Notes**: `all` returns every context, identical to `GET /context/`.

### GET /scope/{scope_id}/due/{date}

Returns the contexts in a scope with at least one task due on or before a date.

- **Path parameters**:
  - `scope_id` (string) — a stored scope, or `all`
  - `date` (ISO 8601 date) — reference date
- **Returns**: `["<context>", ...]` — context names sorted alphabetically
- **Errors**: 404 when `scope_id` is neither a stored scope nor `all`
- **Notes**: `all` returns every context with a due task, identical to `GET /context/due/{date}`.

### GET /scope/{scope_id}/due/

Returns the contexts in a scope with at least one task due on or before today.

- **Path parameters**:
  - `scope_id` (string) — a stored scope, or `all`
- **Returns**: `["<context>", ...]` — the same contexts as `GET /scope/{scope_id}/due/{date}` for today's date in `America/Los_Angeles`
- **Errors**: 404 when `scope_id` is neither a stored scope nor `all`

### PATCH /task/{id}/starred

Sets whether a task is starred.

- **Path parameters**:
  - `id` (integer) — task ID
- **Body**:
  - `starred` (boolean, required)
- **Returns**: An object with these fields:
  - `id` (integer)
  - `starred` (boolean)
- **Errors**: 404 when no task has the given ID; 422 when `starred` is missing or not a boolean
- **Notes**: The write is idempotent: setting the value the task already has returns 200. `coins` doubles when a task is starred, visible on the next read.

### PATCH /task/{id}/description

Replaces a task's description.

- **Path parameters**:
  - `id` (integer) — task ID
- **Body**:
  - `description` (string, required)
- **Returns**: An object with these fields:
  - `id` (integer)
  - `description` (string)
- **Errors**: 404 when no task has the given ID; 400 when the description is empty or only whitespace; 422 when `description` is missing or not a string
- **Notes**: The text is stored verbatim, including markdown and line breaks; it is not trimmed.

### POST /task/{id}/done

Marks a task as completed on the server's current date.

- **Path parameters**:
  - `id` (integer) — task ID
- **Returns**: An object with these fields:
  - `id` (integer)
  - `skip_count` (integer) — always 0 after completion
  - `due_date` (ISO 8601 date string) — recomputed next due date
  - `latest_done_date` (ISO 8601 date string) — the completion date
  - `rating` (integer)
  - `rating_deviation` (integer)
- **Errors**: 409 when the task was completed on the current date or the previous day; the body contains an `error` message
- **Notes**: The four stored completion dates shift forward, the new date becomes the latest, and the skip count resets. Completion uses the `America/Los_Angeles` calendar date, also updates the rating and deviation of the other tasks in the same context, and anchors the updated deviations to the completion date.

## Redirects

- `GET /task/due` redirects with 307 to `GET /task/due/`
- `GET /context/due` redirects with 307 to `GET /context/due/`
- `GET /search` redirects with 307 to `GET /search/`
