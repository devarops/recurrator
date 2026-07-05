# Backlog

- Add json schema validation for config file.
- Set min and max recurrence days.
- Test frontend with Playwright or FastAPI TestClient.
- Add one extra task when we have fewer than 6 tasks.
- Glicko rating system.
- Coins from Glicko rating.

## One extra task algorithm

**Purpose:** When a context has fewer than 6 due tasks, pick one upcoming (not yet due) task to pad the list. Complementary to `filter_n_tasks_by_context`.

**Scope:** Within a single context (matching `filter_n_tasks_by_context`).

**Side effects:** None. Skip tracking is handled elsewhere (API layer of prioritization algorithm).

new function in `compute.py`:

```python
def filter_one_extra_task(
    tasks: list[Task], context: Context, reference_date: date
) -> list[Task]:
```

**Contract:**
1. Start with `all_tasks_in_context = filter_all_tasks_by_context(tasks, context)`.
2. Exclude tasks where `due_date <= reference_date` (already due/overdue — handled by other algorithms).
3. Filter for `recurrence_days > 30` (strict; same as `>= 31`).
4. Sort by `due_date` ASC, then `recurrence_days` DESC (closest due date first; larger recurrence breaks ties).
5. Take the first element (nearest upcoming), return it as `[task]`, or `[]` if none qualify.

## Glicko rating system

Each task gets its own Glicko rating (r) and rating deviation (RD). Contexts are isolated pools —
only tasks in the same context compete.

Not in the plan below: rating and rating_deviation are stored as integers in CSV but treated as floats
in compute functions — conversion happens in `_row_to_task`. rating_date lives in the `Dates` dataclass
but is read from CSV directly, not computed; wire it in `_row_to_task`, not `_compute_dates`.
`record_glicko_match` writes back via `_update_task_in_csv`; you may extract an
`update_task_ratings` helper. There is no explicit `update_task_ratings` step in the plan — the
implementer must add one. GLICKO_Q is `ln(10) / 400` computed once in models.py. Test tasks get
`rating_date = date_4` in every row because date_4 is never NA.

### Match mechanics

On `POST /task/{id}/done`:

- The **completed task** loses one match against every due/overdue task in the same context
  (outcome 0.0 each).
- Each **due/overdue opponent** wins against the completed task (outcome 1.0) and draws
  against every other opponent (outcome 0.5).
- All participants play the same number of matches.

### Constants (add to `models.py`)

| Constant | Value | Notes |
|---|---|---|
| `GLICKO_SCALE` | 400 | Standard Glicko scale |
| `GLICKO_Q` | `ln(10) / 400` (~0.005756) | |
| `RD_MIN` | 50 | Minimum uncertainty |
| `RD_MAX` | 350 | Maximum uncertainty |
| `C_SQUARED` | 328 | RD goes from min to max in ~365 days |
| `GLICKO_RATING_DEFAULT` | 1500 | Default initial rating |
| `GLICKO_RD_DEFAULT` | 350 | Default initial RD |

### CSV columns (after `starred`)

`rating` (int), `rating_deviation` (int), `rating_date` (date, never NA).

### Data seeding

All existing tasks (production and test CSVs) get defaults:
`rating=1500`, `rating_deviation=350`, `rating_date=date_4`.

### Model changes

- `Task.__init__` adds `rating: int` and `rating_deviation: int` as direct constructor params.
- `Dates` dataclass adds `rating_date: date`.

### Pure functions (add to `compute.py`)

```python
def compute_rd_grown(rd, days_since_update) -> float:
    """RD' = min(sqrt(RD² + c² * days), RD_MAX)"""

def compute_g(rd) -> float:
    """g(RD) = 1 / sqrt(1 + 3 * q² * RD² / pi²)"""

def compute_expected_score(rating, opp_rating, opp_g) -> float:
    """E = 1 / (1 + 10^(-g * (r - r_j) / 400))"""

def compute_glicko_update(rating, rd, opponents) -> tuple[float, float]:
    """Full multi-opponent Glicko update.
    opponents: list of (opp_rating, opp_g, outcome)
    Returns (new_rating, new_rd).
    """
```

### I/O (add to `io.py`)

- `_row_to_task` reads `rating`, `rating_deviation`, `rating_date` from CSV.
- `record_glicko_match(task_id, completion_date, csv_path)` — self-contained Level 2 function.
  Loads all tasks, identifies participants, applies RD growth, calls Glicko compute,
  writes updated `rating`, `rating_deviation`, `rating_date` for each participant.

### API (`api.py`)

- `post_task_done` flow: `is_done_allowed` → `record_glicko_match` → `update_task_as_done`.
- `_task_to_dict` includes `rating` and `rating_deviation`.
- Done response returns `id`, `skip_count`, `due_date`, `rating`, `rating_deviation`.

### Frontend

Deferred to a later cycle.

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
coins=compute_coins(row["rating"]),
```

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
