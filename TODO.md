# Backlog

Items marked _details below_ link to their `##` section; items marked _backlog only_ have none, and every `##` section appears in this list.

- Add json schema validation for config file — backlog only
- Set min and max recurrence days — backlog only
- Add one extra task when we have fewer than 6 tasks — [details below](#add-one-extra-task-when-we-have-fewer-than-6-tasks)
- Glicko rating system — [details below](#glicko-rating-system)
- Coins from Glicko rating — [details below](#coins-from-glicko-rating)
- Restore monster avatars on the deployed app — backlog only
- Add search page to frontend — backlog only
- Add page to create new tasks — backlog only
- Move the relative date labels from the frontend into compute_* and the API — backlog only
      Test: The done, overdue, and upcoming labels come from API fields, and public/ui.js performs no date arithmetic.
- Add blockers: a task is blocked while its blocker's row exists; removal needs DELETE /task/{id} — backlog only
- Add sub-tasks: completing any child completes its parent upward, never downward; skip a parent completed in the last two days — backlog only

## Add one extra task when we have fewer than 6 tasks

`filter_one_extra_task` exists in `compute.py` as a stub returning `[]`. Implement the acceptance criteria in `specs/one_extra_task.spec.toml` and call the selector from `GET /context/{context_id}` after the WIP selection. Keep it complementary to `filter_n_tasks_by_context`.

## Glicko rating system

Implement the acceptance criteria in `specs/glicko.spec.toml`. The implementation still uses a linear deviation projection, an all-context opponent selection, and the stored-anchor API default.

### Deviation growth

Replace the linear projection in `compute_live_rating_deviation` with the Lichess step-6 formula. The `glicko2` package already applies one rating period in `Player._preRatingRD` with its 0.06 volatility and 173.7178 scale; the missing part is the fractional periods between `rating_date` and the reference date.

```text
elapsed_periods = max((reference_date - rating_date).days, 0) * RATING_PERIODS_PER_DAY
RD = sqrt(RD_anchor^2 + elapsed_periods * (GLICKO_SCALE * GLICKO_VOLATILITY_DEFAULT)^2)
RD = min(max(round(RD), GLICKO_RD_MIN), GLICKO_RD_MAX)
```

Add `GLICKO_VOLATILITY_DEFAULT = 0.06`, `GLICKO_SCALE = 173.7178`, and `RATING_PERIODS_PER_DAY = 0.21436`, plus `compute_elapsed_rating_periods`. The `_GlickoPlayer` adapter keeps the library from applying step 6 a second time.

### Participation

The event includes every due or overdue task in the completed task's context, plus the completed task even when it was not due. Other not-due tasks stay out. Remove the different-rating condition from `filter_opponents_with_different_rating`; the identity and context conditions remain. The context page's WIP limit is a display rule only and does not restrict the rating event.

### Match update

The current star is the target: the completed task plays every participant and loses; each opponent plays only the completed and wins; opponents do not play each other. Keep `compute_match_updates`. When the completed task is alone, add one internal synthetic opponent whose rating and deviation are the live medians of every task in the CSV; `compute_universe_medians` supplies them. Never write the synthetic.

### Rating-date anchor

After a completion, set `rating_date` to the completion date for the completed task and every real opponent whose rating or deviation changed. Add `update_task_rating_date(task_id, rating_date, csv_path)` in `io.py`, mirroring `update_task_rating` and `update_task_rating_deviation`, and call it from `post_task_done` for each updated id. Keep the per-field writes; do not add the one-pass record function.

### API

`GET /task/{id}` without `date` should project `rating_deviation` to today. This is the selected change from the current stored-anchor default. When the code lands, update `DOCS.md` and `CHANGELOG.md` with the new default and the anchor behaviour. The POST response reads the stored post-match values after the anchor update.

### Tests

Update the unit tests for the step-6 projection, the due/overdue selection without the rating filter, the synthetic medians, and the rating-date anchor.

### Data migration

The test CSVs and `tests/data/datapackage.json` already have the three rating columns. The production migration of `devarops/recurrator.config` remains; run it before deploying the image that reads the columns.

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
