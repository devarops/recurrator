# Backlog

Items marked _details below_ link to their `##` section; items marked _backlog only_ have none, and every `##` section appears in this list.

- Add json schema validation for config file — backlog only
- Set min and max recurrence days — backlog only
- Add one extra task when we have fewer than 6 tasks — [details below](#add-one-extra-task-when-we-have-fewer-than-6-tasks)
- Coins from Glicko rating — [details below](#coins-from-glicko-rating)
- Describe every response in the OpenAPI document — [details below](#describe-every-response-in-the-openapi-document)
- Move the relative date labels from the client into compute_* and the API — backlog only
      Test: The done, overdue, and upcoming labels come from API fields, and the frontend performs no date arithmetic.
- Implement or remove the documented endpoints that do not exist — backlog only
- Reconcile the browser reference date with the server timezone — backlog only
- Add blockers: a task is blocked while its blocker's row exists; removal needs DELETE /api/task/{id} — backlog only
- Add sub-tasks: completing any child completes its parent upward, never downward; skip a parent completed in the last two days — backlog only

## Add one extra task when we have fewer than 6 tasks

`filter_one_extra_task` exists in `compute.py` as a stub returning `[]`. Implement the acceptance criteria in `specs/one_extra_task.spec.toml` and call the selector from `GET /api/context/{context_id}` after the WIP selection. Keep it complementary to `filter_n_tasks_by_context`.

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

The criterion already exists in `specs/contract.spec.toml` and is skipped:

> When the OpenAPI document is read, the 200 response of every task endpoint
> declares at least one property.

Definition of done: its test in `tests/test_acceptance_contract.py` exists and the
criterion stops being skipped. Symmetric work in the frontend belongs to
`recurrator.web`.
