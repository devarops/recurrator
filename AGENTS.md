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
- Error envelope: `{"error": "<message>"}`. Non-200 responses must use `JSONResponse(content={...}, status_code=N)` from `fastapi.responses`; a returned `dict, int` tuple serializes as a JSON array `[{...}, 409]` instead.
- CLI tabular output MUST be valid CSV (header + data rows). Non-tabular output uses JSON; informational and version messages may use plain text as an exception.

**Documentation:** `DOCS.md` lists the HTTP API only; describe the frontend and CLI in `README.md`. `CHANGELOG.md` records only endpoint changes.

**No Derived Values in Presentation Layer:** The frontend may transform data for display but must never compute new atomic values (no arithmetic, statistics, joins, or aggregations); derived values belong in `compute_*`.

**Naming conventions in `compute.py`:** Pure functions use `reference_date` (not `today`) for the cut-off/current date parameter, and `is_*` prefix for boolean-returning functions.

## TDD Cycle

```
Red → Fail (commit failing test) → Green (make it pass, commit) → Refactor
```

- **Fail sub-phase**: Write the test, run suite, confirm exactly one test fails for the right reason, commit.
- If multiple tests fail for the same behavioral gap, defer extra tests to keep exactly one failing test per Red phase. Add them back after Green.
- Failing test convention: use `pass` body only when the target function doesn't exist yet (fails at import). Otherwise write real assertions.
- Tests that modify the CSV use a checksum restore: capture `_get_file_checksum`, mutate, undo with the matching `update_*` function, then assert `_assert_file_unchanged`. Do it inline as in `_verify_task_as_done` in `conftest.py`, or in `try/finally` as in `test_task_done_idempotency`.

**Commit emoji prefixes:** 🛑🧪 (Red), ✅🧪 (Green), ♻️ (refactor), 📝 (docs), 👾 (mutmut config), 🏹👾 (mutant hunting), 👷 (CI).

Run one test with `pytest tests/test_api.py::test_get_due_contexts`, or one ShellSpec example with `shellspec spec/create_config_spec.sh`. `make tests` runs the pytest unit tests; `make verify` runs the qed criteria and ShellSpec. `tests/test_frontend.py` checks static markers, and `tests/test_api.py::test_frontend_is_served_from_the_api_app` checks the served index and JavaScript. CLI tests need the compose `api` service.

## Data Modeling & CSV Mapping

- `Task` is a plain class with `Dates` dataclass for computed date fields.
- Computed attributes (`latest_date`, `recurrence_days`, `due_date`, `coins`) are NOT stored in CSV. They are computed at read time in `io._row_to_task()` and stored as instance attributes.
- `latest_done_date` is a stored attribute (read from `date_4` in CSV) but lives in the `Dates` dataclass alongside computed fields. It is the first field in `Dates`.
- Pattern for adding a new computed field: (1) pure function in `compute.py`, (2) orchestrate computation in `_row_to_task` via `io._compute_dates()` or equivalent, (3) add parameter to `Task.__init__` in `models.py`.
- CSV conversion: `starred`: `0`→`False`, `1`→`True`. Date fields: `"NA"`→`None`, else `date.fromisoformat()`. `id`/`skip_count`: `int()`.
- `recurrator/_contexts.py` is generated from the Frictionless `datapackage.json`, and `recurrator/_config.py` from `config.json` (built-in defaults when absent), by `make install` and by `src/entrypoint.sh` at container start. Both are gitignored. Without production files `create_contexts.sh` falls back to `tests/data/datapackage.json`.

## Container Startup and Deployment

- `src/entrypoint.sh` regenerates both modules from `/root/.config/recurrator` before the command.
- `Dockerfile.dev` adds every test and verification tool to the app image, for the `develop` service: `black`, `flake8`, `frictionless`, `httpx`, `mutmut`, `mypy`, `pylint`, `pytest`, `pytest-cov`, ShellSpec, qed and Lean. It builds `FROM evaristor/recurrator:latest`, so build the prod image first or the dev layer takes a stale base. `Dockerfile` carries only what the app needs to run. Nothing in the dev layer is pinned; `lake build` follows qed's `lean-toolchain`.
- The published image runs without a code checkout in `recurrator_setup`; keep it self-contained and never add a bind mount. Deployment runs no initialization step: the editable install is baked in at build time and `src/entrypoint.sh` generates the modules at container start. The image has no default command, so every runner supplies uvicorn.
- `.github/workflows/actions.yml` builds `evaristor/recurrator:latest`, builds `evaristor/recurrator:develop` on top, and runs `check`, `tests`, `coverage`, `mutants` and `verify` in the dev image. It pushes only if they pass, so a red run leaves the previous `latest` in production. Before pushing, it boots the prod image alone, with no volumes, and requires `/openapi.json` and `/` to respond; that is the only check for a dependency that exists only in dev. Tags are `latest` plus `%y%V`; `:develop` is never published.
- FastAPI serves `public/` at `/` after the API routes. The frontend and API share an origin, use root-relative API paths, and have no API-address setting; CORS is not enabled.
- Production serves the app at `http://recurrator/` over the tailnet: `recurrator_setup` maps host port 80 to 8000, and the `provisioner` cron probes that address. Local compose binds host 80 too, so a port change touches all three repos.
- `PUBLIC_DIR` walks up from `api.py` to the directory containing `public/index.html`, so app import and tests work from any working directory and under mutmut.
- The app is reached over plain HTTP on Tailscale, where `crypto.subtle` is unavailable; the frontend skips monster avatars instead of failing the page.

## Mutation Testing

Configured in `setup.cfg` under `[mutmut]`. Run `make mutants` inside container. Check survivors with `mutmut results`.

## TODO.md

`TODO.md` keeps one checklist above detail sections: every `##` section appears as an item linked with `details below`, and items without one end with `backlog only`.

---

## Development Environment

```shell
docker compose --profile develop build develop
docker compose --profile develop run --interactive --name recurrator_dev --rm --tty develop bash
# Inside container:
make setup && make check && make tests
make verify
# Or directly:
docker compose --profile develop exec -T develop make setup
docker compose --profile develop exec -T develop make tests
docker compose --profile develop exec -T develop make verify
```

The `develop` service shares the production-data mount with `api` and `cli`. `make setup` (`clean` + `install`) bootstraps with no production data; only `check_production_data` reads it, and its single caller, `make check_data`, is never run by CI.

**TZ=America/Los_Angeles** in Dockerfile. `POST /task/{id}/done` uses `date.today()` reflecting this timezone. Do not change without updating all date-dependent assertions.

**Useful make targets:** `tests` (pytest unit tests), `check` (lint + typecheck + test data validation), `coverage`, `mutants` (mutation testing via mutmut), `check_data` (Frictionless Data validation), `format` (black formatter), `setup` (`clean` + `install`), `verify` (qed and ShellSpec acceptance tests, inside the develop image).

`pyproject.toml` declares only `typer`. `fastapi`, `uvicorn` and `requests` come from `Dockerfile`; `black`, `flake8`, `mypy`, `pylint`, `pytest`, `pytest-cov`, `mutmut`, `frictionless`, `httpx` and ShellSpec come from `Dockerfile.dev`. A native install needs both lists.

`make tests` is the unit suite, `make check` the gate, and `make verify` runs the acceptance tests inside the develop image. CI runs all three in the develop image; `coverage` and `mutants` report and do not gate the publish.

The editable install lives in the image, so `docker compose --profile develop run --rm develop make tests` works without a long-lived container. CI still starts one — `docker compose --profile develop run --name recurrator_dev --rm --detach develop sleep infinity` — and `exec`s into it, because the targets share generated modules and caches.
