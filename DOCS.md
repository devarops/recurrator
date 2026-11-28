# API Reference

Recurrator exposes one public interface: the task and context HTTP API in `recurrator/api.py`, served under `/api`.
Every item listed below is a current entry point of that API, and nothing outside the API is listed.
Only current elements are listed; planned behavior lives in `specs/*.spec.toml` and `DESIGN.md`.
The frontend and the TUI are clients of this API and live in other repositories; neither is an API entry point.
The same contract is published live at `GET /api/openapi.json`, `GET /api/docs`, and `GET /api/redoc`.

Paths are resource-scoped: every entry point under `/api/task/` returns tasks and every entry point under `/api/context/` returns contexts.

Every entry point accepts the optional `csv` query parameter:

- `csv` (string) — path to the task data file; defaults to the configured file

The task collection, the context collection, and the context detail also accept `contexts_csv`:

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
- **Notes**: Without `context`, every due task is returned in file order and the read is read-only. With exactly one distinct context, the read applies work-in-progress capacity: tasks completed on `date` in that context reduce the available slots, surplus non-starred tasks are deferred by incrementing `skip_count` and setting `skip_date` to `date`, and deferred tasks are not returned. A starred task is never deferred, and a task with more skips is chosen before one with fewer. With more than one distinct context, the read returns the OR-union of due tasks, deduplicated and in file order, and no work-in-progress limit is applied. Repeating a context value does not change the response.

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

### GET /api/context/

Returns the context IDs in the context data.

- **Returns**: `["<context>", ...]` — context IDs sorted alphabetically, including contexts with no tasks
- **Notes**: The response carries IDs only; use `GET /api/context/{context_id}/` for attributes. Read-only.

### GET /api/context/due/{date}

Returns the contexts with at least one task due on or before a date.

- **Path parameters**:
  - `date` (ISO 8601 date) — reference date
- **Returns**: `["<context>", ...]` — context IDs sorted alphabetically
- **Notes**: A context with no due task is excluded. Read-only.

### GET /api/context/due/

Returns the contexts with at least one task due on or before today.

- **Returns**: `["<context>", ...]` — the same contexts as `GET /api/context/due/{date}` for today's date in `America/Los_Angeles`
- **Notes**: The same rules as `GET /api/context/due/{date}` apply.

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
- **Notes**: The four stored completion dates shift forward, the new date becomes the latest, and the skip count resets. Completion uses the `America/Los_Angeles` calendar date. The completed task and every due task whose `contexts` array shares at least one context with it form one Glicko event; a task that shares two contexts participates once, and a task that shares no context keeps its rating. The update also anchors the updated deviations to the completion date.

## Redirects

- `GET /api/task/due` redirects with 307 to `GET /api/task/due/`
- `GET /api/context/due` redirects with 307 to `GET /api/context/due/`
- `GET /api/context/{context_id}` redirects with 307 to `GET /api/context/{context_id}/`
