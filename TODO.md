# Backlog

Items marked _details below_ link to their `##` section; items marked _backlog only_ have none, and every `##` section appears in this list.

- Add json schema validation for config file — backlog only
- Set min and max recurrence days — backlog only
- Add one extra task when we have fewer than 6 tasks — [details below](#add-one-extra-task-when-we-have-fewer-than-6-tasks)
- Glicko rating system — [details below](#glicko-rating-system)
- Coins from Glicko rating — [details below](#coins-from-glicko-rating)
- Test frontend with Playwright or FastAPI TestClient — backlog only
- Restore monster avatars on the deployed app — backlog only
- Add search page to frontend — backlog only
- Add page to create new tasks — backlog only

## Add one extra task when we have fewer than 6 tasks

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

We use `glicko2` 2.1.0 instead of writing the formulas. It is pure Python, MIT licensed, and has no dependencies. `glicko2.Player(rating, rd)` accepts the 1500-scale values and converts internally; `update_player(rating_list, RD_list, outcome_list)` applies one rating period. Pin the version in `pyproject.toml` and add it to the `Dockerfile`; never vendor it.

Each task gets an integer rating and rating deviation; contexts are isolated pools. We do not store volatility: every player loads with the library default 0.06, and we discard the volatility the library computes. Volatility therefore stays fixed, which makes this Glicko-2 with a constant sigma.

### Match mechanics

On `POST /task/{id}/done`, with `date` equal to the completion date:

- The pool is what the context page would show at that moment: `filter_n_tasks_by_context` with `available_slots = WIP_LIMIT - completed today`, plus the completed task if the selection omits it.
- Every participant plays every other participant once, so `n` tasks play `n(n−1)/2` matches.
- The completed task loses every match (outcome 0.0); every other pair draws (0.5 for both).
- All new ratings are computed from the ratings before the event; no participant reads another participant's new value.
- When the completed task is alone, the event is one match against a synthetic opponent whose rating and RD are the medians of all tasks in the context; the synthetic opponent is never written.

### Constants (add to `models.py`)

| Constant | Value | Notes |
|---|---|---|
| `GLICKO_RATING_DEFAULT` | 1500 | Default initial rating |
| `GLICKO_RD_DEFAULT` | 350 | Default initial RD |

`GLICKO_SCALE`, `GLICKO_Q`, `GLICKO_VOL_DEFAULT`, `RD_MIN`, `RD_MAX`, and `C_SQUARED` are gone. The library owns the scale, the `g` and `E` terms, and RD growth. Its one-year `RD_MIN` to `RD_MAX` condition does not survive the change: growth is per period, and we create one period per completion.

### CSV columns (after `starred`)

`rating` (integer), `rating_deviation` (integer), `rating_date` (date, never NA).

Ratings and RD round to the nearest integer when written; the library returns floats. `rating_date` records the last update and feeds nothing. There is no volatility column.

### Data seeding

All existing tasks (production and test CSVs) get `rating=1500`, `rating_deviation=350`, and `rating_date=date_4`.

The production change is a one-time migration of `devarops/recurrator.config`: add the three columns, seed every row, and update that repository's `datapackage.json`. Run it before deploying the image that reads the columns. Update the test CSVs and `tests/data/datapackage.json` here in the same change.

### Model changes

- `Task.__init__` adds `rating: int` and `rating_deviation: int`.
- `Dates` dataclass adds `rating_date: date`; read it in `_row_to_task`, not `_compute_dates`.

### Compute (add to `compute.py`)

Only the match graph is ours; the rating math stays in the library.

```python
def build_glicko_matches(
    tasks: list[Task], context: Context, reference_date: date, completed_task_id: int
) -> dict[int, list[tuple[int | None, float]]]:
    """Map each participant id to (opponent id, outcome) pairs."""

def compute_context_medians(tasks: list[Task], context: Context) -> tuple[int, int]:
    """Return the median rating and median RD of every task in the context."""
```

`None` stands for the synthetic opponent. `build_glicko_matches` returns `{completed_task_id: [(None, 0.0)]}` when the pool has one participant, and an empty dict when the completed task does not exist. An even-sized context uses the mean of the two middle values, then rounds.

### I/O (add to `io.py`)

- `_row_to_task` reads `rating` and `rating_deviation` with `int()`, and `rating_date` with the date convention.
- `record_glicko_match(task_id, completion_date, csv_path)` loads the tasks once, calls `build_glicko_matches`, and builds one `glicko2.Player(rating, rd)` per participant from the loaded values.
- It calls `update_player` once per participant with the pre-event opponent lists, then rounds each result to an integer.
- It writes every participant in one pass with `update_task_ratings(updates, csv_path)`, which rewrites the CSV once and sets `rating_date` to the completion date.
- `post_task_done` calls `record_glicko_match` before `update_task_as_done`, so the completion dates do not change the pool.

### Tests

- `build_glicko_matches` covers: no such task; one participant; two; four due plus an early completer; six selected from eight due tasks; and the draw among non-completers.
- `compute_context_medians` covers odd and even counts and a single task.
- `record_glicko_match` asserts exact integers recorded from one library run, then restores the CSV and checks the checksum.
- Do not call the library to compute the test expectation.
- There are no tests for the formulas; the library owns them, and mutation testing does not mutate site-packages.

### API (`api.py`)

- `post_task_done` flow: `is_done_allowed` → `record_glicko_match` → `update_task_as_done`.
- `_task_to_dict` includes `rating` and `rating_deviation` as integers.
- Done response returns `id`, `skip_count`, `due_date`, `rating`, `rating_deviation`.
- Update `DOCS.md` and `CHANGELOG.md` in the same commit as the API change.

### Dependencies

- `pyproject.toml`: add `glicko2==2.1.0` to `requires`.
- `Dockerfile`: add `glicko2==2.1.0` to the pip install list.
- `AGENTS.md`: update the line that says `pyproject.toml` declares only `typer`.

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
