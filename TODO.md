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
- Add blockers: a task is blocked while its blocker's row exists; removal needs DELETE /task/{id} — backlog only
- Add sub-tasks: completing any child completes its parent upward, never downward; skip a parent completed in the last two days — backlog only

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

We use `glicko2` 2.1.0 instead of writing the rating formulas. It is pure Python, MIT licensed, and has no dependencies. `glicko2.Player(rating, rd)` accepts the 1500-scale values and converts internally; `update_player(rating_list, RD_list, outcome_list)` applies one rating period. Pin the version in `pyproject.toml` and add it to the `Dockerfile`; never vendor it.

Each task gets an integer rating, an integer rating deviation (RD), and the date the pair was last anchored (`rating_date`). Matches happen only inside a context, so ratings stay mostly context-local; the one cross-context signal is the universe median used when a task plays alone. We do not store volatility: every player loads with the fixed `GLICKO_VOLATILITY_DEFAULT` of 0.06, and we discard the volatility the library computes. Constant sigma is also the rate that drives RD growth.

RD follows Lichess's time-based model: outcomes shrink it, and time since `rating_date` grows it. The CSV stores the RD **anchored** to `rating_date`, as Lichess stores the RD at the end of the last rating period; reads project it to the requested date, and a completion projects it to the completion date before the match. `rating_date` is therefore live metadata, not an audit field.

Acceptance criteria live in `specs/glicko.spec.toml`; each one is skipped until its test in `tests/test_acceptance_glicko.py` exists.

### Lichess parity

We copy these Lichess practices:

- step 6 growth from elapsed time, with fractional rating periods (`RATING_PERIODS_PER_DAY`);
- RD clamped to `[GLICKO_RD_MIN, GLICKO_RD_MAX]`, which is Lichess's `[45, 500]`;
- the stored RD is anchored to the last update and projected on read; the next update stores a new anchor;
- one completion is one rating period, but inactivity contributes fractional periods before it;
- `GLICKO_RD_PROVISIONAL = 110`, the threshold where Lichess displays `?`; the frontend can use it, but the API has no provisional field yet.

We do not copy Lichess's rating floor and ceiling, its maximum rating delta, its color advantage, or its stored volatility. Lichess currently starts new ratings at RD 500 with σ = 0.09, but documents `0.21436` periods per day as RD 60 → 110 in one year; that target matches σ = 0.06, the sigma this plan fixes. Copying the newer defaults would require recalibrating the rate.

### Match mechanics

On `POST /task/{id}/done`, with `date` equal to the completion date:

- The pool is what the context page would show at that moment: `filter_n_tasks_by_context` with `available_slots = WIP_LIMIT - completed today`, plus the completed task if the selection omits it.
- Every participant plays every other participant once, so `n` tasks play `n(n−1)/2` matches.
- The completed task loses every match (outcome 0.0); every other pair draws (0.5 for both).
- Before the event, every participant's RD is projected from its `rating_date` to the completion date; opponent lists use those projected values.
- All new ratings are computed from the ratings before the event; no participant reads another participant's new value.
- When the completed task is alone, the event is one match against a synthetic opponent whose rating and RD are the live medians of every task in the CSV file, regardless of context; the synthetic opponent is never written.

### Constants (add to `models.py`)

| Constant | Value | Notes |
|---|---|---|
| `GLICKO_RATING_DEFAULT` | 1500 | Default initial rating |
| `GLICKO_RD_DEFAULT` | 350 | Default initial RD; below the 500 cap |
| `GLICKO_RD_MIN` | 45 | Lichess's minimum deviation |
| `GLICKO_RD_MAX` | 500 | Lichess's maximum deviation |
| `GLICKO_RD_PROVISIONAL` | 110 | Lichess's provisional threshold; frontend only |
| `GLICKO_VOLATILITY_DEFAULT` | 0.06 | Fixed sigma; also the growth rate |
| `GLICKO_SCALE` | 173.7178 | The library's Glicko-2 scale, used only for step 6 |
| `RATING_PERIODS_PER_DAY` | 0.21436 | Lichess's rate: RD 60 → 110 in one year at σ = 0.06 |

`GLICKO_Q` and `C_SQUARED` are gone; the library owns the game update. `GLICKO_SCALE` returns only for the step-6 growth formula. The old one-year `RD_MIN` → `RD_MAX` condition returns as `RATING_PERIODS_PER_DAY` plus clamps, not as a per-completion rule.

### CSV columns (after `starred`)

`rating` (integer), `rating_deviation` (integer), `rating_date` (date, never NA).

`rating_deviation` is the anchor at `rating_date`, not the value the API shows; the API projects it to the request date. Ratings and RD round to the nearest integer when written; the library returns floats. There is no volatility column.

### Data seeding

All existing tasks (production and test CSVs) get `rating=1500`, `rating_deviation=350`, and `rating_date=date_4`.

Seeding `rating_date=date_4` intentionally projects existing uncertainty forward: a task last completed a year ago reads about 362, and a task idle for years approaches 500. This is the Lichess behavior, not a migration glitch.

The production change is a one-time migration of `devarops/recurrator.config`: add the three columns, seed every row, and update that repository's `datapackage.json`. Run it before deploying the image that reads the columns. Update the test CSVs and `tests/data/datapackage.json` here in the same change.

### Model changes

- `Task.__init__` adds `rating: int` and `rating_deviation: int`; the latter is the anchor.
- `Dates` dataclass adds `rating_date: date`; read it in `_row_to_task`, not `_compute_dates`.

### Compute (add to `compute.py`)

The match graph and the step-6 projection are ours; the game update stays in the library.

```python
def compute_elapsed_rating_periods(rating_date: date, reference_date: date) -> float:
    """Fractional rating periods elapsed, never negative."""

def compute_live_rating_deviation(
    rating_deviation: int, rating_date: date, reference_date: date
) -> int:
    """Project an anchored RD to reference_date, clamped to [RD_MIN, RD_MAX]."""

def build_glicko_matches(
    tasks: list[Task], context: Context, reference_date: date, completed_task_id: int
) -> dict[int, list[tuple[int | None, float]]]:
    """Map each participant id to (opponent id, outcome) pairs."""

def compute_universe_medians(
    tasks: list[Task], reference_date: date
) -> tuple[int, int]:
    """Return the median rating and median live RD of every task in the file."""
```

Step 6 is the one formula we own:

```text
elapsed_periods = max((reference_date - rating_date).days, 0) * RATING_PERIODS_PER_DAY
RD = sqrt(RD_anchor^2 + elapsed_periods * (GLICKO_SCALE * GLICKO_VOLATILITY_DEFAULT)^2)
RD = min(max(round(RD), GLICKO_RD_MIN), GLICKO_RD_MAX)
```

`glicko2` has no preview API and applies step 6 only as a side effect of `update_player`, so implementing this once in `compute.py` is clearer than reading private state. The game update itself stays in the library.

`None` stands for the synthetic opponent. `build_glicko_matches` returns `{completed_task_id: [(None, 0.0)]}` when the pool has one participant, and an empty dict when the completed task does not exist. An even-sized file uses the mean of the two middle values, then rounds. The synthetic opponent uses the live medians at the completion date.

### I/O (add to `io.py`)

- `_row_to_task` reads `rating` and `rating_deviation` with `int()`, and `rating_date` with the date convention. `Task.rating_deviation` is the anchor.
- `record_glicko_match(task_id, completion_date, csv_path)` loads the tasks once, calls `build_glicko_matches`, and projects every participant's RD to `completion_date` with `compute_live_rating_deviation` before building players.
- It builds one `_GlickoPlayer(task.rating, live_rd)` per participant from the pre-event values, calls `update_player` once with the pre-event opponent ratings and live RDs, then rounds and clamps each result.
- It writes every participant in one pass with `update_task_ratings(updates, completion_date, csv_path)`, which rewrites the CSV once and sets `rating_date` to the completion date. Only post-match RD is written, so no reverse adjustment is needed.
- `post_task_done` calls `record_glicko_match` before `update_task_as_done`, so the completion dates do not change the pool.

`glicko2.Player.update_player` always applies step 6 once. Lichess passes `skipDeviationIncrease = true` because the elapsed-time projection already ran; `glicko2` has no such flag, so use a small adapter:

```python
class _GlickoPlayer(glicko2.Player):
    def _preRatingRD(self):
        """Step 6 is applied from rating_date in compute.py."""
```

This is an adapter, not a vendored copy; pinning 2.1.0 keeps the hook stable.

### Tests

- `compute_elapsed_rating_periods` covers 0 days, less than one period, a year, and a future `rating_date` (clamped to zero).
- `compute_live_rating_deviation` covers no elapsed time, a year from RD 60 to about 110, the 45 and 500 clamps, and fractional days.
- `build_glicko_matches` covers: no such task; one participant; two; four due plus an early completer; six selected from eight due tasks; and the draw among non-completers.
- `compute_universe_medians` covers odd and even counts, a single row, rows from several contexts, and time-projected RDs.
- `record_glicko_match` asserts exact integers recorded from one library run with an old `rating_date`, then restores the CSV and checks the checksum.
- Do not call the library to compute the test expectation. Step 6 is ours, so test it directly; the library's game-update formulas are not tested, and mutation testing does not mutate site-packages.
- Add a fixture with two tasks that have the same stored RD and `rating_date`s one year apart, for the inactivity acceptance test.

### API (`api.py`)

- `GET /task/{id}` accepts an optional `date` query, defaulting to today, and projects `rating_deviation` to it.
- `_task_to_dict(task, reference_date)` returns `rating` and live `rating_deviation` as integers.
- `post_task_done` flow: `is_done_allowed` → `record_glicko_match` → `update_task_as_done`.
- Done response returns `id`, `skip_count`, `due_date`, `rating`, `rating_deviation`; after the update `rating_date` is today, so the live value equals the stored one.
- Update `DOCS.md` and `CHANGELOG.md` in the same commit as the API change.

### Dependencies

- `pyproject.toml`: add `glicko2==2.1.0` to `requires`.
- `Dockerfile`: add `glicko2==2.1.0` to the pip install list.
- `AGENTS.md`: update the line that says `pyproject.toml` declares only `typer`.

### Frontend

Deferred to a later cycle. When it arrives, show the provisional marker when `rating_deviation >= GLICKO_RD_PROVISIONAL`.

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
