# Backlog

Items marked _details below_ link to their `##` section; items marked _backlog only_ have none, and every `##` section appears in this list.

- Add json schema validation for config file — backlog only
- Set min and max recurrence days — backlog only
- Align the tests with the multi-context contract — [details below](#align-the-tests-with-the-multi-context-contract)
- Add one extra task when at least one and fewer than the work-in-progress limit are due — [details below](#add-one-extra-task-when-at-least-one-and-fewer-than-the-work-in-progress-limit-are-due)
- Coins from Glicko rating — [details below](#coins-from-glicko-rating)
- Describe every response in the OpenAPI document — [details below](#describe-every-response-in-the-openapi-document)
- Move the relative date labels from the client into compute_* and the API — backlog only
      Test: The done, overdue, and upcoming labels come from API fields, and the frontend performs no date arithmetic.
- Add blockers: a task is blocked while its blocker's row exists; removal needs DELETE /api/task/{id} — backlog only
- Add sub-tasks: completing any child completes its parent upward, never downward; skip a parent completed in the last two days — backlog only

## Align the tests with the multi-context contract

The specs now describe tasks with several contexts and contexts with several scopes.
The tests still use the single-valued context column and the deleted context and scope routes.
Every skipped criterion names the test that must replace it.

### Fixtures and helpers

- Rename `context` to `contexts` in every task fixture under `tests/data/` and store a JSON array such as `["casa"]`.
- Add `tests/data/contexts.csv` with `id`, `display_name`, `description`, and a JSON `scopes` array; cover overlapping scopes, an unused context, a scope named only by an unused context, and a scope named `all`.
- Add `tests/data/contexts_without_all.csv`; it serves the absent-alias criterion and the `contexts_csv` path-selection criterion.
- Add task fixtures with a task in several contexts for the full-membership, WIP, and shared-context Glicko criteria.
- Add task fixtures for the one-extra-task criteria: zero due, one due under the limit, at the limit, no long-recurrence candidate, and a multiple-context request.
- Add a task fixture with at least 40 tasks for the search pagination criteria.
- Add an empty task fixture for the first-ID creation criterion, or create one inside the test.
- Add both context data resources and every new task fixture to `tests/data/datapackage.json`, and replace every task resource's `context` enum with a `contexts` string field. `make check_data` must pass.
- Rename the `CONTEXTS_CSV` constant to `CONTEXT_TASKS_CSV` and add `CONTEXT_DATA_CSV = "tests/data/contexts.csv"`.
- Add `contexts_csv` to every test helper URL that reads contexts or validates task contexts.
- Update `_copy_fixture` to copy the task and context fixtures into the temporary directory.
- Replace `_read_context_task_ids` with helpers for the task collection filter and the single-context dated due read.
- Point `_read_due_contexts` at `GET /api/context/due/{date}` and add the scope filters.
- Add helpers for `GET /api/context/{context_id}/`, `GET /api/scope/`, and `PATCH /api/task/{id}/contexts`.
- Remove `_read_task_ids_on` with the orphaned date-query test.

### Acceptance tests

- Create `tests/test_acceptance_context_views.py` for the nine criteria in `specs/context_views.spec.toml`.
- Create `tests/test_acceptance_scope_views.py` for the fourteen criteria in `specs/scope_views.spec.toml`.
- Create `tests/test_acceptance_one_extra_task.py` for the six criteria in `specs/one_extra_task.spec.toml`.
- Create `tests/test_acceptance_task_creation.py` for the nineteen criteria in `specs/task_creation.spec.toml`.
- Create `tests/test_acceptance_search.py` for the seventeen criteria in `specs/search.spec.toml`.
- Create `tests/test_acceptance_contract.py` for the four criteria in `specs/contract.spec.toml`.
- Update `tests/test_acceptance_tasks_views.py`: delete `test_date_query_parameter_is_ignored`; add the fifteen skipped criteria for the context filter, WIP selection, multi-context read-only, due-read errors, and the two older route tests.
- Update `tests/test_acceptance_task_detail.py` with its three skipped criteria.
- Update `tests/test_acceptance_task_edits.py` with its eleven skipped criteria.
- Update `tests/test_acceptance_glicko.py` with its three shared-context criteria and repoint the existing context reads at the dated due route.
- Remove `skip = "Not implemented"` from each criterion as its test lands.

### Unit tests

- `tests/test_api.py`: change the task-detail assertions from `context` to `contexts`, update the expected context lists for multi-context tasks, point the context helpers at the task collection and dated due routes, and cover the context filter, context detail, scope list, `contexts_csv` path, `PATCH contexts`, and the single-context WIP mode.
- `tests/test_compute.py`: update every task context expectation to `contexts`; add a multi-context task and assert full membership in the context filters, WIP selection, deferral, completion counts, and the Glicko opponent set.
- `tests/test_io.py`: parse and write the JSON `contexts` cell, add a task with several contexts, read the context data CSV, and assert the writer quotes the JSON cell.
- `tests/test_entrypoint.py`: update the generated-module fixture to the context data file and assert the new default context path; the old `context` enum fixture no longer matches the contract.

## Add one extra task when at least one and fewer than the work-in-progress limit are due

`filter_one_extra_task` exists in `compute.py` as a stub returning `[]`. Implement the acceptance criteria in `specs/one_extra_task.spec.toml` and call the selector from the dated due read, `GET /api/task/due/{date}?context={context_id}`, after the WIP selection. Keep it complementary to `filter_n_tasks_by_context`.

## Coins from Glicko rating

Coins are computed from the Glicko rating instead of recurrence_days/starred.
Prerequisite: Glicko rating system is fully implemented (rating exists on every Task).

### Constants in `models.py`

| Constant | Value | Notes |
|---|---|---|
| `RATING_MIN` | 1000 | Minimum rating anchor |
| `RATING_MAX` | 2000 | Maximum rating anchor |
| `RATING_MID` | 1500 | Midpoint rating anchor |
| `COINS_MIN` | 20 | Minimum coin value |
| `COINS_MAX` | 200 | Maximum coin value |
| `COINS_MID` | 50 | Midpoint coin value |
| `STEP` | `RATING_MID - RATING_MIN` | Computed at module level (500) |
| `GROWTH` | `(COINS_MAX - COINS_MIN) / (COINS_MID - COINS_MIN) - 1` | Computed at module level (5) |
| `COEFFICIENT` | `(COINS_MID - COINS_MIN) / (GROWTH - 1)` | Computed at module level (7.5) |
| `OFFSET` | `COINS_MIN - COEFFICIENT` | Computed at module level (12.5) |

### Signature change in `compute.py`

Old:
```python
def compute_coins(recurrence_days: int, is_starred: bool) -> int:
```

New:
```python
def compute_coins(rating: int) -> int:
    """Compute coins from Glicko rating via exponential model, clamped to [COINS_MIN, COINS_MAX]."""
    return min(
        max(COINS_MIN, round(COEFFICIENT * pow(GROWTH, (rating - RATING_MIN) / STEP) + OFFSET)),
        COINS_MAX,
    )
```

### Call-site change in `io.py`

`_row_to_task` changes from:
```python
coins=compute_coins(dates.recurrence_days, starred),
```
to:
```python
coins=compute_coins(rating),
```

`rating` is the integer already read in `_row_to_task`; do not pass the CSV string.

### Documentation

- DOCS.md: replace coins description with `coins: integer, computed from Glicko rating via an exponential model clamped to [20, 200]`.

### Red phase

Rewrite `test_compute_coins` to test the new signature and formula. Boundary-value assertions:
- `compute_coins(1000) == 20` (rating at minimum → COINS_MIN)
- `compute_coins(2000) == 200` (rating at maximum → COINS_MAX)
- `compute_coins(1500) == 50` (midpoint, verify exponential model)
- `compute_coins(500) == 20` (below minimum clamped)
- `compute_coins(2500) == 200` (above maximum clamped)

### No changes

- CSV schema — coins is not stored.
- Task model — `starred` stays; `coins` stays as a runtime attribute.
- API response shape — field name and position unchanged.
- Frontend — no code changes; the value displayed changes naturally.

## Describe every response in the OpenAPI document

Every endpoint returns a bare `dict`, so the 200 response of every path in
`/api/openapi.json` has an empty schema. Declare a `response_model` per endpoint
and return the model, so `_task_to_dict` disappears and there is one definition.

The four criteria already exist in `specs/contract.spec.toml` and are skipped.
They require every 200 response to declare a schema, and the task and context
detail schemas to declare their properties and collection item types.

Definition of done: `tests/test_acceptance_contract.py` exists and every criterion
stops being skipped. Symmetric work in the frontend belongs to `recurrator.web`.
