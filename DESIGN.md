# Design: recurrator

`DESIGN.md` is the system's workflow for programmers. It is the target before implementation and the description of what was built after. It owns the mechanism and ordering; `DOCS.md` owns the current caller's view, and `specs/*.spec.toml` owns the observable criteria.

## Status

| Block | Status | Evidence |
| --- | --- | --- |
| Data model and task detail | built | `specs/task_detail.spec.toml` |
| Context data and context views | built | `specs/context_views.spec.toml` |
| Task description and starred | built | `tests/test_acceptance_task_edits.py::test_description_is_written_verbatim`, `tests/test_acceptance_task_edits.py::test_starring_is_idempotent` |
| Completion and Glicko | built | `specs/glicko.spec.toml` |
| API shape and OpenAPI contract | built | `specs/contract.spec.toml`, `tests/test_api.py::test_malformed_description_body_returns_error_field` |
| Task collection and due selection | planned | `specs/tasks_views.spec.toml` |
| Task contexts edit | planned | `specs/task_edits.spec.toml` |
| One extra task | planned | `specs/one_extra_task.spec.toml` |
| Search | planned | `specs/search.spec.toml` |
| Scope views | planned | `specs/scope_views.spec.toml` |
| Task creation | planned | `specs/task_creation.spec.toml` |
| Task deletion | planned | `specs/task_deletion.spec.toml` |
| Coins from Glicko rating | planned | no artifact yet |

## Data model and task detail

The task data file is the source of truth for task history. Each row becomes a `Task`; the `contexts` cell is a JSON array, dates are ISO 8601 or `NA`, and `starred` is `0` or `1`. `id` and `skip_count` are integers. The rating columns are optional; an older file without them defaults to 1500, 350, and the last completion date.

Computed fields exist only at read time. `_row_to_dates` derives `latest_done_date`, `latest_date`, `recurrence_days`, and `due_date`; `_row_to_task` adds `contexts`, `coins`, and the Glicko fields. `latest_done_date` is the last completion date, while `latest_date` is the later of that date and the skip date. `recurrence_days` is the median interval between completions, defaulting to 14. `due_date` is `latest_date` plus `recurrence_days`.

Why: the CSV stores history, not projections. A stored `due_date` or `recurrence_days` would be a second source of truth and would drift whenever a date or skip changed. Detail reads project `rating_deviation` to the requested reference date; a read without one projects to today.

## Context data and context views

The context data file is authoritative for contexts and scopes. Each row has `id`, `display_name`, `description`, and a `scopes` JSON array. A context exists with or without tasks, and a scope exists when at least one context names it. The detail read returns the context's fields with its scopes sorted and deduplicated.

Why: contexts and scopes are configuration, not task history. Deriving them from task rows would lose an empty context and would let a missing task data file erase the vocabulary. The context file is also the only place a scope is declared.

## Task description and starred

`PATCH /api/task/{id}/description` stores the text verbatim, including markdown and real line breaks; it does not trim. `PATCH /api/task/{id}/starred` sets the flag. Both validate the body before looking up the task and return a confirmation subset with the changed fields.

Why: a write returns what changed, not the whole resource, so a caller does not have to reconcile a full object it did not ask for. Description is free text, so it is never normalized. Starred is idempotent; setting the value the task already has succeeds.

## Completion and Glicko

`POST /api/task/{id}/done` uses the server's current date in `America/Los_Angeles`. It shifts the four stored completion dates forward, makes the new date the latest, and resets `skip_count`. The completed task and every due task whose `contexts` array shares at least one context form one Glicko event; a task that shares two contexts participates once, and a task that shares none keeps its rating. The update writes the new ratings, deviations, and `rating_date` anchor.

Why: completion is the only event that changes a task's skill estimate. Grouping by shared context models a session of related work as one match, and deduplicating by task prevents a task with two shared contexts from counting twice. The rating date anchors the deviation projection so a task does not get more certain merely because time passed without a completion.

## API shape and OpenAPI contract

The API is resource-scoped under `/api`. List endpoints return identities; detail endpoints return attributes. Action responses return a confirmation subset with `id` and the changed fields, not the full resource. Every error response carries `{"error": "<message>"}`, and a non-200 response uses `JSONResponse`; returning a `(dict, int)` would serialize as a JSON array.

Every successful response declares a schema. Collection endpoints declare their item type, and detail endpoints declare their properties. The route uses `openapi_extra` with the response model's JSON schema, so the published `/api/openapi.json` carries the shape rather than an empty object.

Why: the OpenAPI document is the published contract, not a debug view. A bare `dict` would make every response schema empty and force clients to guess. A confirmation subset keeps a write response small and unambiguous.

## Task collection and due selection

`GET /api/task/` returns task IDs in file order. One or more `context` values combine with OR; a task in several requested contexts is returned once. The due read without a context returns every due task in file order and changes nothing.

With exactly one distinct context, the due read applies work-in-progress capacity. Tasks completed on the reference date in that context reduce the available slots. Surplus non-starred tasks are deferred by incrementing `skip_count` and setting `skip_date` to the reference date; deferred tasks are not returned. A starred task is never deferred, and a task with more skips is chosen before one with fewer. With more than one distinct context, the read returns the OR-union of due tasks, deduplicated in file order, and applies no work-in-progress limit.

Why: one context is a focus session, where the point is to leave with a small number of tasks; several contexts are an overview, where hiding work would make the view lie. The skip is shared across a task's contexts, so deferring it in one context defers it everywhere.

The two acceptance criteria for prioritization and deferral are still skipped in `specs/tasks_views.spec.toml`; that is why this block is planned while the mechanism exists.

## Task contexts edit

`PATCH /api/task/{id}/contexts` replaces the array. The body must hold one or more stored context IDs without repeats. The body is validated before the task is looked up, and the write is idempotent. The confirmation returns the new IDs, sorted and deduplicated.

Why: a task belongs to every context it names, so changing the array changes which work-in-progress views and Glicko events include it. The context data is authoritative; an unknown ID is a client error, not a new context.

## One extra task

When a dated due read is narrowed to one context and has at least one and fewer than the work-in-progress limit of due tasks, the response adds exactly one upcoming task from that context. The extra task is above the long-recurrence threshold, has the earliest due date, and larger recurrence days break a tie. It is not due, not deferred, and its skip fields do not change. There is no extra task with zero due tasks, at the limit, without a qualifying long-recurrence task, or with more than one context.

Why: a nearly empty focus session should offer one meaningful piece of future work without pretending it is due. The long-recurrence threshold keeps the offer to work that will not return immediately; the cap keeps the focus list bounded.

## Search

`GET /api/search/` pages the task list without a query: `limit` defaults to 20, `page` is 1-based, and a page past the end is empty. With a query, `limit` and `page` have no effect and every match is returned. A description matches when RapidFuzz's WRatio is at least 80 after folding case and accents and collapsing whitespace. The query is trimmed and its whitespace collapsed before the length check and before matching. A query shorter than three characters is a 400. Only `description` is matched.

Why: the task text is the only free-form field a person remembers. Folding case and accents and collapsing whitespace makes the search tolerant of typing, while the 80 threshold keeps a short query from matching everything.

## Scope views

`GET /api/scope/` lists every scope named by the context data, sorted, including a scope named by a context with no tasks. A scope no context names does not exist. There is no special `all` alias; `all` is an ordinary scope name.

Why: scopes are a view over the context data, not a separate store. An empty context still declares its scopes, and a name is not special merely because a client might want a wildcard.

## Task creation

`POST /api/task/` takes `contexts` and `description`. The new task takes `max(id) + 1`, or 1 when the file is empty. Its stored dates are `NA, NA, today - 28, today - 14` in `America/Los_Angeles`, so it is due today with a recurrence of 14 days. `skip_count` is 0, `starred` is false, `rating` is 1500, `rating_deviation` is 350, and `rating_date` is the last seeded date. The duplicate check compares against the task holding `max(id)`, after stripping and collapsing whitespace and folding case and accents; the stored text is unchanged. The body is validated before the file is read, and creation is not idempotent.

Why: a new task needs enough history to be due immediately without inventing a long completion record. The duplicate check catches the common double-submit without scanning the whole file.

## Task deletion

`DELETE /api/task/{id}` removes the matching row and keeps every other row's contents, order, and stored fields. The header stays when the last row leaves. Deletion is unconditional: a starred, deferred, or just-completed task is removed like any other. IDs are not reserved, so a later creation can take the freed ID. Repeating the request returns 404. The API offers no restore.

Why: the star protects against deferral, not against an explicit delete. The data repository's sync script commits the task file, so the row remains in that history; a separate archive would be a second source of truth.

## Coins from Glicko rating

Coins are computed from the Glicko rating, not from recurrence and starring. The constants are `RATING_MIN = 1000`, `RATING_MAX = 2000`, `RATING_MID = 1500`, `COINS_MIN = 20`, `COINS_MAX = 200`, `COINS_MID = 50`, `STEP = 500`, `GROWTH = 5`, `COEFFICIENT = 7.5`, and `OFFSET = 12.5`. The model is:

```text
coins = clamp(round(COEFFICIENT * GROWTH ** ((rating - RATING_MIN) / STEP) + OFFSET), COINS_MIN, COINS_MAX)
```

`compute_coins` takes the rating. `_row_to_task` passes the integer rating it already read. Today the call site still passes recurrence and starred; the change is planned. The boundary values are `compute_coins(1000) == 20`, `compute_coins(1500) == 50`, and `compute_coins(2000) == 200`; ratings below 1000 and above 2000 clamp to the ends.

Why: coins should reward skill, not frequency. A task done often and a task done well are different achievements, and the rating already carries the difference.

## Decisions and rejected alternatives

- **Tasks have several contexts.** A task is one row and one work-in-progress member per context, with one shared skip. Rejected: a single context column, which cannot express a task that belongs to home and work.
- **One Glicko event per completion, grouped by shared context.** Rejected: pairwise matches, which depend on iteration order and let a task with two shared contexts count twice.
- **Computed fields at read time.** Rejected: storing `due_date`, `recurrence_days`, or `coins`, which would create derived state that drifts from the dates.
- **Context data is authoritative.** Rejected: deriving contexts and scopes from task rows, which loses empty contexts and undeclared scopes.
- **The API is the single source of truth.** The browser frontend and the TUI are separate repositories and speak only HTTP. Rejected: clients reading the CSV, which would couple them to storage and bypass validation.
- **Deletion leaves no archive in the API.** The data repository's sync script commits the task file. Rejected: a second archive file, which would be another source of truth.
- **Coins come from the rating.** Rejected: recurrence-based coins, which reward frequency rather than skill.
- **The OpenAPI document carries response schemas.** Rejected: bare `dict` returns, which publish empty schemas.
- **The test migration is a build sequence, not design.** It stays in `TODO.md`; the target behavior stays in the specs.
