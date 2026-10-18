# Developer Guidelines & Project Standards

**Public Interface:** In this project, the **Public Interface** is the HTTP API defined in `api.py`, the single authoritative interface to task data.
The browser pages in `public/` are the **frontend**, and `cli.py` is the **CLI**; both are optional clients of the API and never access the CSV directly.

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
- Error envelope: `{"error": "<message>"}` with appropriate HTTP status code. Non-200 responses must use `JSONResponse(content={...}, status_code=N)` from `fastapi.responses`; the `return dict, int` tuple pattern serializes as a JSON array `[{...}, 409]` instead of unpacking.
- CLI tabular output MUST be valid CSV (header + data rows). Non-tabular output uses JSON.

**Documentation:** `DOCS.md` lists the HTTP API only. The browser pages in `public/` and the `recurrator` CLI are clients, so describe them in `README.md`, not in the endpoint reference. `CHANGELOG.md` records only changes that touch an endpoint listed in `DOCS.md`; documentation-only edits do not belong.

**No Derived Values in Presentation Layer:** The frontend may transform data for display (type coercion, renaming, filtering, column selection) but must never introduce new atomic values through computation (no arithmetic, statistics, joins, or aggregations). Derived values belong in `compute_*` on the backend.

**Naming conventions in `compute.py`:** Pure functions use `reference_date` (not `today`) for the cut-off/current date parameter, and `is_*` prefix for boolean-returning functions.

## TDD Cycle

```
Red → Fail (commit failing test) → Green (make it pass, commit) → Refactor
```

- **Fail sub-phase**: Write the test, run suite, confirm exactly one test fails for the right reason, commit.
- If multiple tests fail for the same behavioral gap, defer extra tests to keep exactly one failing test per Red phase. Add them back after Green.
- Failing test convention: use `pass` body only when the target function doesn't exist yet (fails at import). Otherwise write real assertions.
- After-Gold test pattern: subsequent strengthening assertions use 🥇🧪 prefix.
- Tests that modify shared mutable state (CSV files) follow a checksum-based restore pattern:
  1. Capture `original_checksum = _get_file_checksum(csv_path)` at the start.
  2. Make changes, run assertions.
  3. Undo each mutation to its original value using the corresponding `update_*` function.
  4. Assert `_assert_file_unchanged(csv_path, original_checksum)` at the end.
  The undo steps are inline (not wrapped in `try/finally`); the checksum assertion at the end verifies the file was fully restored. See `_verify_task_as_done` in `conftest.py` for a reusable example.

**Commit emoji prefixes:** 🛑🧪 (Red), ✅🧪 (Green), ♻️ (refactor), 📝 (docs), 🥇🧪 (after-gold), 👾 (mutmut config), 🏹👾 (mutant hunting), 👷 (CI).

Run one test with `pytest tests/test_api.py::test_get_due_contexts`. API and CLI tests use FastAPI `TestClient` and Typer `CliRunner`; `tests/test_frontend.py` only checks static HTML markers.

## Data Modeling & CSV Mapping

- `Task` is a plain class with `Dates` dataclass for computed date fields.
- Computed attributes (`latest_date`, `recurrence_days`, `due_date`, `coins`) are NOT stored in CSV. They are computed at read time in `io._row_to_task()` and stored as instance attributes.
- `latest_done_date` is a stored attribute (read from `date_4` in CSV) but lives in the `Dates` dataclass alongside computed fields. It is the first field in `Dates`.
- Pattern for adding a new computed field: (1) pure function in `compute.py`, (2) orchestrate computation in `_row_to_task` via `io._compute_dates()` or equivalent, (3) add parameter to `Task.__init__` in `models.py`.
- CSV conversion: `starred`: `0`→`False`, `1`→`True`. Date fields: `"NA"`→`None`, else `date.fromisoformat()`. `id`/`skip_count`: `int()`.
- `recurrator/_contexts.py` is generated from the Frictionless `datapackage.json`, and `recurrator/_config.py` from `config.json` (built-in defaults when absent), by `make install`. Both are gitignored.

## Mutation Testing

Configured in `setup.cfg` under `[mutmut]`. Run `make mutants` inside container. Check survivors with `mutmut results`.

---

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

**Useful make targets:** `tests` (pytest), `check` (lint + typecheck + test data validation), `coverage`, `mutants` (mutation testing via mutmut), `check_data` (Frictionless Data validation), `format` (black formatter).
