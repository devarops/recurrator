# Developer Guidelines & Project Standards

## Architecture

**Layered Module Structure (strict one-way dependencies):**
- `models.py` — domain data structures. Zero external dependencies.
- `compute.py` — pure business logic. Depends only on `models`.
- `io.py` — persistence. Depends on `compute` and `models`.
- `api.py` / `cli.py` — interfaces. Depend on `io`.

**Lower layers NEVER import from higher layers.**

**API conventions:**
- API is single source of truth; CLI is a thin HTTP client with zero business logic.
- Single-responsibility endpoints: list endpoints return identities, detail endpoints return attributes.
- Action responses return confirmation subsets (`id` + changed fields), not full resources.
- Error envelope: `{"error": "<message>"}` with appropriate HTTP status code.
- CLI tabular output MUST be valid CSV (header + data rows). Non-tabular output uses JSON.

**No Derived Values in Presentation Layer:** The frontend may transform data for display (type coercion, renaming, filtering, column selection) but must never introduce new atomic values through computation (no arithmetic, statistics, joins, or aggregations). Derived values belong in `compute_*` on the backend.

## TDD Cycle

```
Red → Fail (commit failing test) → Green (make it pass, commit) → Refactor
```

- **Fail sub-phase**: Write the test, run suite, confirm exactly one test fails for the right reason, commit.
- If multiple tests fail for the same behavioral gap, defer extra tests to keep exactly one failing test per Red phase. Add them back after Green.
- Failing test convention: use `pass` body only when the target function doesn't exist yet (fails at import). Otherwise write real assertions.
- After-Gold test pattern: subsequent strengthening assertions use 🥇🧪 prefix.

**Commit emoji prefixes:** 🛑🧪 (Red), ✅ (Green), ♻️ (refactor), 📝 (docs), 🥇🧪 (after-gold), 👾 (mutmut config), 🏹👾 (mutant hunting), 👷 (CI).

## Data Modeling & CSV Mapping

- `Task` is a plain class with `Dates` dataclass for computed date fields.
- Computed attributes (`latest_date`, `recurrence_days`, `due_date`, `coins`) are NOT stored in CSV. They are computed at read time in `io._row_to_task()` and stored as instance attributes.
- Pattern for adding a new computed field: (1) pure function in `compute.py`, (2) orchestrate computation in `_row_to_task` via `io._compute_dates()` or equivalent, (3) add parameter to `Task.__init__` in `models.py`.
- CSV conversion: `starred`: `0`→`False`, `1`→`True`. Date fields: `"NA"`→`None`, else `date.fromisoformat()`. `id`/`skip_count`: `int()`.
- `Context` enum is generated at build time from `tests/data/datapackage.json` via `src/create_contexts.sh`.

## Development Environment

```shell
docker build --tag evaristor/recurrator:latest .
docker compose run --interactive --name recurrator_ci --rm --tty cli bash
# Inside container:
make init && make tests
# Or directly:
docker compose exec cli make init
docker compose exec cli make tests
```

**TZ=America/Los_Angeles** in Dockerfile. `POST /task/{id}/done` uses `date.today()` reflecting this timezone. Do not change without updating all date-dependent assertions.

**Useful make targets:** `tests` (pytest), `check` (lint + typecheck + test data validation), `coverage`, `mutants` (mutation testing via mutmut), `check_data` (Frictionless Data validation).

## Mutation Testing

Configured in `setup.cfg` under `[mutmut]`. Run `make mutants` inside container. Check survivors with `mutmut results`.
