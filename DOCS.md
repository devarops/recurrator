# API Reference

Recurrator exposes one public interface: the task, context, and scope HTTP API in `recurrator/api.py`, served under `/api`.
Every item listed below is an entry point of that API, and nothing outside the API is listed.
The frontend and the TUI are clients of this API and live in other repositories; neither is an API entry point.
The same contract is published live at `GET /api/openapi.json`, `GET /api/docs`, and `GET /api/redoc`.

Paths are resource-scoped: every entry point under `/api/task/` returns tasks, every entry point under `/api/context/` returns contexts, and every entry point under `/api/scope/` returns scopes.

Every entry point accepts the same optional query parameters:

- `csv` (string) — path to the task data file; defaults to the configured file
- `contexts_csv` (string) — path to the context data file; defaults to the configured file

A task is due when its `due_date` is on or before the reference date. Reference dates are ISO 8601 (`YYYY-MM-DD`).

Every error response carries an `error` field: `{"error": "<message>"}`, including the 422 responses returned for a malformed body or query value.

## Data files

The task data file is a CSV file that holds one row per task.
It must contain `id`, `contexts`, `description`, `date_1` through `date_4`, `skip_count`, `skip_date`, and `starred`.
`contexts` is a JSON array of context IDs, for example `["actividad","casa"]`; it holds at least one ID, does not repeat one, and every value must be an ID from the context data.
Dates are ISO 8601 or `NA`; `starred` is `0` or `1`.
`rating`, `rating_deviation`, and `rating_date` are optional; without `rating_date` the last completion date anchors the deviation.

The context data file is a CSV file that holds one row per context.
It must contain `id`, `display_name`, `description`, and `scopes`.
`id` is the context's unique identifier and the value tasks use in `contexts`.
`display_name` and `description` are non-empty strings.
`scopes` is a JSON array of scope names, for example `["personal","monday"]`; it holds at least one name and does not repeat one.
A context exists with or without tasks, and a scope exists when at least one context names it.
The context data is authoritative for valid contexts and scopes.
Every context ID must be usable as one URL path segment; `due` is reserved for the due collection.

A task belongs to every context in its `contexts` array. It consumes a work-in-progress slot in each of those contexts, can appear in each context's view, and shares one `skip_count` and `skip_date` across all of them, so deferring it in one context defers it in every context it names.

## Endpoints

### GET /api/task/

Returns the IDs of all tasks.

- **Query parameters**:
  - `context` (string, optional, repeatable) — a context ID
- **Returns**: `[<integer>, ...]` — task IDs in file order
- **Errors**: 422 when a `context` value is empty; 404 when a `context` value names no stored context
- **Notes**: Without `context`, every task is returned. With one or more values, a task is returned when its `contexts` array contains at least one requested context, so the values combine with OR. A task that contains several requested contexts is returned once. Repeating a value does not change the response. Read-only.

### GET /api/task/due/{date}

Returns task IDs selected for a reference date.

- **Path parameters**:
  - `date` (ISO 8601 date) — reference date
- **Query parameters**:
  - `context` (string, optional, repeatable) — a context ID
- **Returns**: `[<integer>, ...]` — selected task IDs
- **Errors**: 422 when a `context` value is empty; 404 when a `context` value names no stored context
- **Notes**: Without `context`, every due task is returned in file order and the read is read-only. With exactly one distinct context, the read applies work-in-progress capacity: tasks completed on `date` in that context reduce the available slots, surplus non-starred tasks are deferred by incrementing `skip_count` and setting `skip_date` to `date`, and deferred tasks are not returned. A starred task is never deferred, and a task with more skips is chosen before one with fewer. When at least one and fewer than the WIP limit are due, the response includes at most one extra upcoming task: the upcoming task belonging to that context, above the long-recurrence threshold, with the earliest due date and larger recurrence days breaking a tie. The extra task is not due and is not deferred. Response order is not promised; read `GET /api/task/{id}` and check `due_date` to identify the extra task. With more than one distinct context, the read returns the OR-union of due tasks, deduplicated and in file order, and no work-in-progress limit or extra task is applied. Repeating a context value does not change the response.

### GET /api/task/due/

Returns the task IDs selected for today.

- **Query parameters**:
  - `context` (string, optional, repeatable) — a context ID
- **Returns**: `[<integer>, ...]` — the same IDs as `GET /api/task/due/{date}` for today's date in `America/Los_Angeles`
- **Errors**: 422 when a `context` value is empty; 404 when a `context` value names no stored context
- **Notes**: The same single-context, multiple-context, and no-context rules as `GET /api/task/due/{date}` apply.

### GET /api/task/{id}

Returns one task with its computed schedule.

- **Path parameters**:
  - `id` (integer) — task ID
- **Query parameters**:
  - `date` (ISO 8601 date, optional) — reference date for projecting `rating_deviation`; without it the deviation is projected to today
- **Returns**: An object with these fields:
  - `id` (integer)
  - `description` (string)
  - `contexts` (array of strings) — the task's context IDs, sorted alphabetically and deduplicated
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
- **Notes**: `latest_date` is the later of the last completion date and the skip date. `latest_done_date` is the last completion date itself, unaffected by the skip date. `recurrence_days` is the median interval between completions, defaulting to 14. `due_date` is `latest_date` plus `recurrence_days`. `rating_deviation` is projected to `date` when provided; otherwise it is projected to today. `description` is markdown text that may contain real line breaks, returned as newlines.

### GET /api/search/

Returns one page of tasks, or the tasks whose description matches a query.

- **Query parameters**:
  - `query` (string, optional) — text to match against each description
  - `limit` (integer, optional) — page size when `query` is absent; defaults to 20
  - `page` (integer, optional) — 1-based page number when `query` is absent; defaults to 1
- **Returns**: `[{...}, ...]` — full task objects, with the same fields as `GET /api/task/{id}`
- **Errors**: 400 when `query` is present but empty, or shorter than three characters after trimming, with the body `{"error": "<message>"}`; 422 when `limit` or `page` is not an integer or is less than 1
- **Notes**: Without `query`, the response is one page of the task list in file order: up to `limit` tasks starting after `(page - 1) * limit`, and a page past the end is empty. A page holding fewer than `limit` tasks is the last one. With `query`, `limit` and `page` have no effect and every match is returned, sorted by similarity descending with ties in file order. A description matches when its similarity to the query is at least 80, measured with RapidFuzz's WRatio after folding case and accents and collapsing each run of whitespace to one space. Only `description` is matched; context IDs, display names, and scopes are not. The query is trimmed and its whitespace collapsed before the length check and before matching. Read-only.

### GET /api/context/

Returns the context IDs in the context data.

- **Query parameters**:
  - `scope` (string, optional, repeatable) — a scope name
- **Returns**: `["<context>", ...]` — context IDs sorted alphabetically, including contexts with no tasks
- **Errors**: 422 when a `scope` value is empty; 404 when a `scope` value names no stored scope
- **Notes**: With one or more values, a context is returned when its `scopes` array contains every requested scope, so the values combine with AND. Repeating a value does not change the response. There is no `all` alias; `all` is an ordinary scope name and is unknown unless the context data names it. The response carries IDs only; use `GET /api/context/{context_id}/` for attributes.

### GET /api/context/due/{date}

Returns the contexts with at least one task due on or before a date.

- **Path parameters**:
  - `date` (ISO 8601 date) — reference date
- **Query parameters**:
  - `scope` (string, optional, repeatable) — a scope name
- **Returns**: `["<context>", ...]` — context IDs sorted alphabetically
- **Errors**: 422 when a `scope` value is empty; 404 when a `scope` value names no stored scope
- **Notes**: The scope values combine with AND, as in `GET /api/context/`. A context with no due task is excluded even when it matches every requested scope. Read-only.

### GET /api/context/due/

Returns the contexts with at least one task due on or before today.

- **Query parameters**:
  - `scope` (string, optional, repeatable) — a scope name
- **Returns**: `["<context>", ...]` — the same contexts as `GET /api/context/due/{date}` for today's date in `America/Los_Angeles`
- **Errors**: 422 when a `scope` value is empty; 404 when a `scope` value names no stored scope
- **Notes**: The same scope rules as `GET /api/context/due/{date}` apply.

### GET /api/context/{context_id}/

Returns one context.

- **Path parameters**:
  - `context_id` (string) — a context ID from the context data
- **Returns**: An object with these fields:
  - `id` (string) — the context ID
  - `display_name` (string)
  - `description` (string)
  - `scopes` (array of strings) — scope names sorted alphabetically and deduplicated
- **Errors**: 404 when no context has the given ID
- **Notes**: A context with no tasks is returned. The context data must provide every field; a missing or empty field or an empty `scopes` array is a server-side data error, not a client error. `GET /api/context/{context_id}` redirects with 307 to the trailing-slash form.

### GET /api/scope/

Returns every scope named by the context data.

- **Returns**: `["<scope>", ...]` — scope names sorted alphabetically
- **Notes**: A scope named by a context with no tasks is listed. A scope that no context names does not exist and is not listed. The `all` alias is not special; a scope named `all` is listed like any other. Read-only.

### POST /api/task/

Creates a task.

- **Body**:
  - `contexts` (array of strings, required) — one or more stored context IDs, without duplicates
  - `description` (string, required) — the task text, stored verbatim
- **Returns**: 201 with the full task object, with the same fields as `GET /api/task/{id}`
- **Errors**: 422 when `contexts` is missing, is not an array, is empty, contains a non-string, names no stored context, or repeats a context; or when `description` is missing or not a string. 400 when the description is empty or only whitespace. 409 when the description duplicates the newest task's, with the body `{"error": "<message>", "id": <integer>}` naming that task.
- **Notes**: The new task takes `max(id) + 1`, or 1 when the task data file holds no rows. Its stored dates are `NA, NA, today - 28, today - 14`, using the `America/Los_Angeles` calendar date, so it is due today with a recurrence of 14 days. `skip_count` is 0, `starred` is false, `rating` is 1500, `rating_deviation` is 350, and `rating_date` is the last seeded date. The body carries neither dates nor flags, so a caller cannot create a task with a history. The duplicate check compares the description against the task that currently holds `max(id)` and never against the rest of the file; the comparison strips leading and trailing whitespace, drops the whitespace inside the text, folds case and folds accents, while the stored text stays exactly as sent. The body is validated before the task file is read: a malformed body or an invalid `contexts` list returns 422, an empty description returns 400, and a duplicate returns 409, in that order. Creation is not idempotent: repeating a request whose description still matches the newest task returns 409 rather than writing a second row.

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

### PATCH /api/task/{id}/contexts

Replaces a task's contexts.

- **Path parameters**:
  - `id` (integer) — task ID
- **Body**:
  - `contexts` (array of strings, required) — one or more stored context IDs, without duplicates
- **Returns**: An object with these fields:
  - `id` (integer)
  - `contexts` (array of strings) — the new context IDs, sorted alphabetically and deduplicated
- **Errors**: 422 with an `error` message when `contexts` is missing, is not an array, contains a non-string, is empty, repeats a context, or names no stored context; 404 when no task has the given ID
- **Notes**: The body is validated before the task is looked up: a malformed body returns 422, an unknown ID returns 404 even when the list is empty, and only an existing task with an invalid list returns 422. The write is idempotent: setting the contexts the task already has returns 200.

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
- **Notes**: The four stored completion dates shift forward, the new date becomes the latest, and the skip count resets. Completion uses the `America/Los_Angeles` calendar date. The completed task and every due task whose `contexts` array shares at least one context with it form one Glicko event; a task that shares two contexts participates once, and a task that shares no context keeps its rating. The update also anchors the updated deviations to the completion date.

### DELETE /api/task/{id}

Deletes a task.

- **Path parameters**:
  - `id` (integer) — task ID
- **Returns**: An object with these fields:
  - `id` (integer)
- **Errors**: 404 when no task has the given ID
- **Notes**: The task's row leaves the task data file, and every other row keeps its contents, its order, and its stored fields, including its dates, rating, and rating deviation. The file keeps its header when the last row is removed, and the collection read then returns an empty list. Deletion is unconditional: a starred task, a deferred task, and a task completed on the current date are removed like any other, because the star protects only against deferral. IDs are not reserved, so a task created after the deletion takes `max(id) + 1`, and deleting the newest task lets the next created task take its ID. Repeating the request returns 404, because no task has the ID, and the task data file does not change. The API offers no restore.

## Redirects

- `GET /api/task/due` redirects with 307 to `GET /api/task/due/`
- `GET /api/context/due` redirects with 307 to `GET /api/context/due/`
- `GET /api/context/{context_id}` redirects with 307 to `GET /api/context/{context_id}/`
- `GET /api/search` redirects with 307 to `GET /api/search/`
