# Developer Guidelines & Project Standards

**Public Interface:** In this project, the **Public Interface** is the HTTP API defined in `api.py`, the single authoritative interface to task data. The static frontend mount in `api.py` is browser delivery, not part of the task-data Public Interface.
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
- CLI tabular output MUST be valid CSV (header + data rows). Non-tabular output uses JSON; informational and version messages may use plain text as an exception.

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
- Tests that modify shared mutable state (CSV files) follow a checksum-based restore pattern:
  1. Capture `original_checksum = _get_file_checksum(csv_path)` at the start.
  2. Make changes, run assertions.
  3. Undo each mutation to its original value using the corresponding `update_*` function.
  4. Assert `_assert_file_unchanged(csv_path, original_checksum)` at the end.
  The undo steps may be inline, as in `_verify_task_as_done` in `conftest.py`, or wrapped in `try/finally`, as in `test_task_done_idempotency`; the checksum assertion after them verifies the file was fully restored.

**Commit emoji prefixes:** 🛑🧪 (Red), ✅🧪 (Green), ♻️ (refactor), 📝 (docs), 👾 (mutmut config), 🏹👾 (mutant hunting), 👷 (CI).

Run one test with `pytest tests/test_api.py::test_get_due_contexts`, or one ShellSpec example with `shellspec spec/create_config_spec.sh`. `make tests` runs pytest then ShellSpec; qed acceptance criteria live in `specs/`. `tests/test_frontend.py` checks static markers; `test_frontend_is_served_from_the_api_app` checks the served index and JavaScript. CLI tests call the real CLI at `API_BASE_URL` (`http://api:8000`), so they need the compose `api` service.

## Data Modeling & CSV Mapping

- `Task` is a plain class with `Dates` dataclass for computed date fields.
- Computed attributes (`latest_date`, `recurrence_days`, `due_date`, `coins`) are NOT stored in CSV. They are computed at read time in `io._row_to_task()` and stored as instance attributes.
- `latest_done_date` is a stored attribute (read from `date_4` in CSV) but lives in the `Dates` dataclass alongside computed fields. It is the first field in `Dates`.
- Pattern for adding a new computed field: (1) pure function in `compute.py`, (2) orchestrate computation in `_row_to_task` via `io._compute_dates()` or equivalent, (3) add parameter to `Task.__init__` in `models.py`.
- CSV conversion: `starred`: `0`→`False`, `1`→`True`. Date fields: `"NA"`→`None`, else `date.fromisoformat()`. `id`/`skip_count`: `int()`.
- `recurrator/_contexts.py` is generated from the Frictionless `datapackage.json`, and `recurrator/_config.py` from `config.json` (built-in defaults when absent), by `make install` and by `src/entrypoint.sh` at container start. Both are gitignored. Without production files `create_contexts.sh` falls back to `tests/data/datapackage.json`.

## Container Startup and Deployment

- `src/entrypoint.sh` regenerates both modules from `/root/.config/recurrator` before the command; api and cli each do this.
- `Dockerfile.dev` adds qed and Lean to the app image for the `develop` service, behind the `develop` profile. Nothing is pinned; `lake build` follows qed's `lean-toolchain`. `.pipelines/verify.sh` runs `make verify` and CI calls it; it assumes the app image exists.
- The published image runs without a code checkout in [`devarops/recurrator_setup`](https://github.com/devarops/recurrator_setup), which provisions the server; keep it self-contained and do not add a bind-mount dependency.
- FastAPI serves `public/` at `/` after the API routes. The frontend and API share an origin, use root-relative API paths, and have no API-address setting; CORS is not enabled. Keep the local address `http://localhost/` for local work.
- Production serves the app at `http://recurrator/` over the tailnet: [`recurrator_setup`](https://github.com/devarops/recurrator_setup) maps host port 80 to the container's 8000, and the nightly probe in [`provisioner`](https://github.com/IslasGECI/provisioner) `src/Cronfile` requests that address. Local compose binds host 80 too. A port change touches all three, so ship them together.
- `PUBLIC_DIR` walks up from `api.py` to the directory containing `public/index.html`, so app import and tests work from any working directory and under mutmut.
- The app is reached over plain HTTP on Tailscale, where `crypto.subtle` is unavailable (plain HTTP is not a secure context); the frontend skips monster avatars instead of failing the page.

## Mutation Testing

Configured in `setup.cfg` under `[mutmut]`. Run `make mutants` inside container. Check survivors with `mutmut results`.

## TODO.md

`TODO.md` keeps one checklist above detail sections. Every `##` section appears as a checklist item linking to it with `details below`; items without one end with `backlog only`. Keep both in sync.

---

## Development Environment

```shell
docker build --tag evaristor/recurrator:latest .
docker compose run --interactive --name recurrator_dev --rm --tty cli bash
# Inside container:
make init && make tests
# Or directly:
docker compose exec cli make init
docker compose exec cli make tests
```

**TZ=America/Los_Angeles** in Dockerfile. `POST /task/{id}/done` uses `date.today()` reflecting this timezone. Do not change without updating all date-dependent assertions.

**Useful make targets:** `tests` (pytest, then ShellSpec), `check` (lint + typecheck + test data validation), `coverage`, `mutants` (mutation testing via mutmut), `check_data` (Frictionless Data validation), `format` (black formatter), `setup` (`clean` + `install`), `verify` (qed spec, inside the develop image).

`pyproject.toml` declares only `typer`; `fastapi`, `uvicorn`, `requests`, and the lint/test tools come from the `Dockerfile`, so a native install needs them added. The Dockerfile also installs ShellSpec, which `make tests` needs.

`make tests` is the suite, `make check` the gate, and `make verify` runs the qed spec inside the develop image. `make init` prepends `check_production_data`, which reads `/root/.config/recurrator`, so use `make setup` where production data is absent, as CI does.

A one-off `docker compose run --rm cli make tests` fails with `ModuleNotFoundError` because a fresh container lacks the editable install. Start a long-lived container and use `exec`, as CI does: `docker compose run --name recurrator_dev --rm --detach cli sleep infinity`.
