# Backlog

Items marked _details below_ link to their `##` section; items marked _backlog only_ have none, and every `##` section appears in this list.

- Add json schema validation for config file — backlog only
- Set min and max recurrence days — backlog only
- Align the tests with the multi-context contract — [details below](#align-the-tests-with-the-multi-context-contract)
- Add one extra task when at least one and fewer than the work-in-progress limit are due — [details below](#add-one-extra-task-when-at-least-one-and-fewer-than-the-work-in-progress-limit-are-due)
- Coins from Glicko rating — [details below](#coins-from-glicko-rating)
- Describe every response in the OpenAPI document — [details below](#describe-every-response-in-the-openapi-document)
- Delete tasks through the API — [details below](#delete-tasks-through-the-api)
- Move the relative date labels from the client into compute_* and the API — backlog only
      Test: The done, overdue, and upcoming labels come from API fields, and the frontend performs no date arithmetic.
- Add blockers: a task is blocked while its blocker's row exists; removal needs DELETE /api/task/{id} — backlog only
- Add sub-tasks: completing any child completes its parent upward, never downward; skip a parent completed in the last two days — backlog only

## Align the tests with the multi-context contract

The specs describe tasks with several contexts and contexts with several scopes.
The suite still names the single-valued context column and the deleted context and scope routes.
The migration runs in three phases, and this section covers the first.

### Phase 1: align the existing tests

Rewrite only the assertions the new design falsifies, plus the scaffolding they need.
No assertion is added, no spec changes, and no production code moves.

- Delete `test_date_query_parameter_is_ignored`, `test_import_tasks_from_csv_two_contexts`,
  `test_get_tasks_by_context`, and `test_get_tasks_by_context_defers_remaining_tasks`, with
  `_read_task_ids_on`, `_restore_skip_fields`, and the `deferred_context_read` fixture.
- Rename `context` to `contexts` in every task fixture and store a JSON array such as `["casa"]`.
- Add `tests/data/contexts.csv` with `casa`, `chores`, and `laptop`; their scopes span
  `["personal"]`, `["work"]`, and `["work","personal"]`.
- Rename the `CONTEXTS_CSV` constant to `CONTEXT_TASKS_CSV`; `CONTEXTS_CSV` names the new file.
- Rewrite the task-detail expectations to `contexts` arrays, and point `_read_due_contexts` and
  `_read_context_task_ids` at the dated due reads.
- Replace `Context` members with context IDs in `test_compute.py` and `test_io.py`, and drop the
  generated-context assertion from `test_entrypoint.py`.
- Update `tests/data/datapackage.json`: rename the field in every task resource, drop the enum,
  constrain the JSON cells by shape, and register the contexts resource.

The expected state is red: `pytest tests` and `mypy tests` fail against the interface that does
not exist yet, while `black` and `flake8` stay clean.
The same commit rewrites this section and lists every test as rewritten, deleted, or untouched.

### Phase 2: production

Rewrite `models`, `compute`, `io`, and `api`; retire `create_contexts.sh`, `_contexts.py`, and
their Makefile and entrypoint wiring; add `default_contexts_csv_path` to the generated config.
Migrate the data repository first: `context.csv` becomes `contexts.csv` with `id`,
`display_name`, `description`, and `scopes`, where `both` becomes `["work","personal"]`;
`is_not` stays as an unread column.

### Phase 3: the missing tests

Create the acceptance files the specs name, add the fixture data each criterion needs, and
remove one `skip = "Not implemented"` per test through the normal Red-Green-Refactor cycle.

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

## Delete tasks through the API

`DELETE /api/task/{id}` is described in `DOCS.md`, and its eleven criteria are
skipped in `specs/task_deletion.spec.toml`. None of the work below changes the
public interface.

- Add `delete_task(task_id, csv_path)` to `io.py`: read the rows and the field
  names, drop the one matching row, and pass the rest to `_write_csv_rows`,
  which already replaces the file through a temporary file. Raise `ValueError`
  when no row matches, as `_read_task_row` does.
- Add a `DeletionConfirmation` model holding only `id` and return it from the
  route, using `_existing_task_csv_path` so the 404 envelope matches every other
  ID endpoint. The route takes `task_id: int` and `csv: str = Query(None)`.
- Add unit tests in `tests/test_io.py` for the matching row, its neighbours, the
  last row, and a missing ID. Only the missing-ID case fits
  `_assert_file_unchanged`.
- Create `tests/test_acceptance_task_deletion.py` and the fixture data each
  criterion needs, then remove one `skip` per test through the
  Red-Green-Refactor cycle. A deletion cannot be undone through the API, so each
  test works on its own copy of the task data or restores the row it removed.
- One criterion pairs deletion with creation, so it stays skipped until
  `specs/task_creation.spec.toml` is implemented.

Deleting the row in the live file is enough because the data repository's sync
script commits `tasks.csv` on every run, so a removed row stays in that history.
No archive file is needed.
