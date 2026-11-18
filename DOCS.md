# API Reference

Recurrator exposes one public interface: the task-data HTTP API in `recurrator/api.py`, served under `/api`.
Every item listed below is an entry point of that API, and nothing outside the API is listed.
The frontend and the TUI are clients of this API and live in other repositories; neither is an API entry point.
The same contract is published live at `GET /api/openapi.json`, `GET /api/docs`, and `GET /api/redoc`.

Every entry point accepts the same optional query parameter:

- `csv` (string) — path to the task data file; defaults to the configured file

A task is due when its `due_date` is on or before the reference date. Reference dates are ISO 8601 (`YYYY-MM-DD`).

Every non-200 response carries an `error` field: `{"error": "<message>"}`, including the 422 responses returned for a malformed body.

## Endpoints

### GET /api/task/

Returns the IDs of all tasks.

- **Returns**: `[<integer>, ...]` — every task ID in the task data file, in file order
- **Notes**: The task data file must contain `id`, `context`, `description`, `date_1` through `date_4`, `skip_count`, `skip_date`, and `starred`. Dates are ISO 8601 or `NA`; `starred` is `0` or `1`. `rating_date` is optional; without it the last completion date anchors the deviation.
- **Notes**: A `date` query parameter has no effect; due filtering is expressed in the path.

### GET /api/task/due/{date}

Returns the IDs of the tasks due on or before a date.

- **Path parameters**:
  - `date` (ISO 8601 date) — reference date
- **Returns**: `[<integer>, ...]` — task IDs whose due date is on or before `date`, in file order
- **Notes**: Read-only.

### GET /api/task/due/

Returns the IDs of the tasks due on or before today.

- **Returns**: `[<integer>, ...]` — the same IDs as `GET /api/task/due/{date}` for today's date in `America/Los_Angeles`
- **Notes**: Read-only.

### GET /api/task/{id}

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
- **Notes**: `latest_date` is the later of the last completion date and the skip date. `latest_done_date` is the last completion date itself, unaffected by the skip date. `recurrence_days` is the median interval between completions, defaulting to 14. `due_date` is `latest_date` plus `recurrence_days`. `coins` equals `recurrence_days`, doubled when the task is starred. `rating_deviation` is projected to `date` when provided; otherwise it is projected to today. `description` is markdown text that may contain real line breaks, returned as newlines.

### GET /api/search/

Returns one page of tasks, or the tasks whose description matches a query.

- **Query parameters**:
  - `query` (string, optional) — text to match against each description
  - `limit` (integer, optional) — page size when `query` is absent; defaults to 20
  - `page` (integer, optional) — 1-based page number when `query` is absent; defaults to 1
- **Returns**: `[{...}, ...]` — full task objects, with the same fields as `GET /api/task/{id}`
- **Errors**: 400 when `query` is present but empty, or shorter than three characters after trimming, with the body `{"error": "<message>"}`; 422 when `limit` or `page` is not an integer or is less than 1
- **Notes**: Without `query`, the response is one page of the task list in file order: up to `limit` tasks starting after `(page - 1) * limit`, and a page past the end is empty. A page holding fewer than `limit` tasks is the last one. With `query`, `limit` and `page` have no effect and every match is returned, sorted by similarity descending with ties in file order. A description matches when its similarity to the query is at least 80, measured with RapidFuzz's WRatio after folding case and accents and collapsing each run of whitespace to one space. Only `description` is matched; context names are not. The query is trimmed and its whitespace collapsed before the length check and before matching. Read-only.

### GET /api/context/

Returns the contexts named in the task data file.

- **Returns**: `["<context>", ...]` — every context that at least one task names, sorted alphabetically
- **Notes**: A context with no due task is listed. A `date` query parameter has no effect; due filtering is expressed in the path.

### GET /api/context/due/{date}

Returns the contexts with at least one task due on or before a date.

- **Path parameters**:
  - `date` (ISO 8601 date) — reference date
- **Returns**: `["<context>", ...]` — context names sorted alphabetically
- **Notes**: Read-only.

### GET /api/context/due/

Returns the contexts with at least one task due on or before today.

- **Returns**: `["<context>", ...]` — the same contexts as `GET /api/context/due/{date}` for today's date in `America/Los_Angeles`
- **Notes**: Read-only.

### GET /api/context/{context_id}

Returns every task ID in one context.

- **Path parameters**:
  - `context_id` (string) — a context named by at least one task in the task data file
- **Returns**: `[<integer>, ...]` — every task ID in that context, in file order
- **Errors**: 404 when no task names the given context
- **Notes**: Read-only; it does not change `skip_count` or `skip_date`.

### GET /api/context/{context_id}/due/{date}

Returns prioritized task IDs for one context, limited by available work-in-progress capacity.

- **Path parameters**:
  - `context_id` (string) — a context named by at least one task in the task data file
  - `date` (ISO 8601 date) — reference date
- **Returns**: `[<integer>, ...]` — selected task IDs in priority order
- **Errors**: 404 when no task names the given context
- **Notes**: Tasks completed on `date` reduce the available capacity. Surplus non-starred tasks are deferred: their `skip_count` is incremented and `skip_date` is set to `date`, so this read endpoint also writes to the task data file. Deferred tasks are not returned.

### GET /api/scope/

Returns the stored scopes.

- **Returns**: `["<scope>", ...]` — scope names sorted alphabetically
- **Notes**: Scopes come from the context data; the current data stores `both`, `personal`, and `work`. The `all` alias is not a stored scope and is not listed.

### GET /api/scope/{scope_id}/

Returns the contexts in a scope.

- **Path parameters**:
  - `scope_id` (string) — a stored scope, or `all`
- **Returns**: `["<context>", ...]` — the contexts that belong to the scope and are named by at least one task, sorted alphabetically
- **Errors**: 404 when `scope_id` is neither a stored scope nor `all`
- **Notes**: `all` returns every context, identical to `GET /api/context/`.

### GET /api/scope/{scope_id}/due/{date}

Returns the contexts in a scope with at least one task due on or before a date.

- **Path parameters**:
  - `scope_id` (string) — a stored scope, or `all`
  - `date` (ISO 8601 date) — reference date
- **Returns**: `["<context>", ...]` — context names sorted alphabetically
- **Errors**: 404 when `scope_id` is neither a stored scope nor `all`
- **Notes**: `all` returns every context with a due task, identical to `GET /api/context/due/{date}`.

### GET /api/scope/{scope_id}/due/

Returns the contexts in a scope with at least one task due on or before today.

- **Path parameters**:
  - `scope_id` (string) — a stored scope, or `all`
- **Returns**: `["<context>", ...]` — the same contexts as `GET /api/scope/{scope_id}/due/{date}` for today's date in `America/Los_Angeles`
- **Errors**: 404 when `scope_id` is neither a stored scope nor `all`

### POST /api/task/

Creates a task.

- **Body**:
  - `context` (string, required) — a stored context value
  - `description` (string, required) — the task text, stored verbatim
- **Returns**: 201 with the full task object, with the same fields as `GET /api/task/{id}`
- **Errors**: 422 when `description` is missing or not a string, or `context` is missing or not a stored context; 400 when the description is empty or only whitespace; 409 when the description duplicates the newest task's, with the body `{"error": "<message>", "id": <integer>}` naming that task
- **Notes**: The new task takes `max(id) + 1`, or 1 when the task data file holds no rows. Its stored dates are `NA, NA, today - 28, today - 14`, using the `America/Los_Angeles` calendar date, so it is due today with a recurrence of 14 days. `skip_count` is 0, `starred` is false, `rating` is 1500, `rating_deviation` is 350, and `rating_date` is the last seeded date. The body carries neither dates nor flags, so a caller cannot create a task with a history. The duplicate check compares the description against the task that currently holds `max(id)` and never against the rest of the file; the comparison strips leading and trailing whitespace, drops the whitespace inside the text, folds case and folds accents, while the stored text stays exactly as sent. The body is validated before the file is read: a malformed body returns 422, an empty description returns 400, and a duplicate returns 409, in that order. Creation is not idempotent: repeating a request whose description still matches the newest task returns 409 rather than writing a second row.

### PATCH /api/task/{id}/starred

Sets whether a task is starred.

- **Path parameters**:
  - `id` (integer) — task ID
- **Body**:
  - `starred` (boolean, required)
- **Returns**: An object with these fields:
  - `id` (integer)
  - `starred` (boolean)
- **Errors**: 404 when no task has the given ID; 422 with an `error` message when `starred` is missing or not a boolean
- **Notes**: The write is idempotent: setting the value the task already has returns 200.

### PATCH /api/task/{id}/description

Replaces a task's description.

- **Path parameters**:
  - `id` (integer) — task ID
- **Body**:
  - `description` (string, required)
- **Returns**: An object with these fields:
  - `id` (integer)
  - `description` (string)
- **Errors**: 422 with an `error` message when `description` is missing or not a string; 404 when no task has the given ID; 400 when the description is empty or only whitespace
- **Notes**: The body is validated before the task is looked up, and the task before the text: a malformed body returns 422, an unknown ID returns 404 even when the description is empty, and only an existing task with an empty description returns 400. The text is stored verbatim, including markdown and real line breaks; it is not trimmed. A read returns the same text unchanged, and the characters backslash and n are ordinary text.

### POST /api/task/{id}/done

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

- `GET /api/task/due` redirects with 307 to `GET /api/task/due/`
- `GET /api/context/due` redirects with 307 to `GET /api/context/due/`
- `GET /api/search` redirects with 307 to `GET /api/search/`
