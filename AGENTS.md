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

**Visual approval:** `tests/visual/capture.py` lists the scenarios; `make visual` rewrites `received/` and the human approves. The local `ui-red`, `ui-green`, `ui-refactor`, and `ui-approve` commands run the frontend TDD loop; `ui-approve` requires a fresh capture, runs the three suites, writes `tests/visual/review.html`, and on approval copies `received/` into `approved/` and updates the spec and styleguide in the same commit. `tests/visual/specs/recurrator-frontend-spec.md` is the only reference, the mockups are retired, and the browser tests, approved PNGs, spec, and styleguide must agree. `renderMarkdown` decodes the CSV's literal `\n` before parsing.

## TDD Cycle

```
Red → Fail (commit failing test) → Green (make it pass, commit) → Refactor
```

- **Fail sub-phase**: Write the test, run suite, confirm exactly one test fails for the right reason, commit.
- Defer extra tests for the same behavioral gap so exactly one test fails per Red phase; add them back after Green.
- Failing test convention: use `pass` body only when the target function doesn't exist yet (fails at import). Otherwise write real assertions.
- Tests that modify the CSV restore it with the matching `update_*` function and assert `_assert_file_unchanged`; see `_verify_task_as_done` in `conftest.py` or the `try/finally` in `test_task_done_idempotency`.

**Commit emoji prefixes:** 🛑🧪 (Red), ✅🧪 (Green), ♻️ (refactor), 📝 (docs), 👾 (mutmut config), 🏹👾 (mutant hunting), 👷 (CI).

Run one test with `pytest tests/test_api.py::test_get_due_contexts`, or one ShellSpec example with `shellspec spec/create_config_spec.sh`. `tests/test_frontend.py` checks static markers, and `tests/test_api.py::test_frontend_is_served_from_the_api_app` checks the served index and JavaScript. The browser suite starts its own API on an ephemeral port and copies the fixture per test; run one case with `RUN_BROWSER=1 pytest tests/browser/test_home.py::test_all_tile_shows_due_contexts`. CLI tests need the compose `api` service.

## Data Modeling & CSV Mapping

- `Task` is a plain class with `Dates` dataclass for computed date fields.
- Computed attributes (`latest_date`, `recurrence_days`, `due_date`, `coins`) are NOT stored in CSV. They are computed at read time in `io._row_to_task()` and stored as instance attributes.
- `latest_done_date` is a stored attribute (read from `date_4` in CSV) but lives in the `Dates` dataclass alongside computed fields. It is the first field in `Dates`.
- Pattern for adding a new computed field: (1) pure function in `compute.py`, (2) orchestrate computation in `_row_to_task` via `io._compute_dates()` or equivalent, (3) add parameter to `Task.__init__` in `models.py`.
- CSV conversion: `starred`: `0`→`False`, `1`→`True`. Date fields: `"NA"`→`None`, else `date.fromisoformat()`. `id`/`skip_count`: `int()`.
- `recurrator/_contexts.py` is generated from the Frictionless `datapackage.json`, and `recurrator/_config.py` from `config.json` (built-in defaults when absent), by `make install` and by `src/entrypoint.sh` from `/root/.config/recurrator` at container start. Both are gitignored. Without production files `create_contexts.sh` falls back to `tests/data/datapackage.json`.

## Container Startup and Deployment

- `Dockerfile.dev` adds every test and verification tool to the app image, for the `develop` service: `black`, `flake8`, `frictionless`, `httpx`, `mutmut`, `mypy`, `playwright` with Chromium, `pylint`, `pytest`, `pytest-cov`, ShellSpec, qed and Lean. It builds `FROM evaristor/recurrator:latest`, so build the prod image first or the dev layer takes a stale base.
- The published image runs without a code checkout in `recurrator_setup`; keep it self-contained and never add a bind mount. Deployment runs no initialization step: the editable install is baked in at build time. The image has no default command, so every runner supplies uvicorn.
- `.github/workflows/actions.yml` builds `evaristor/recurrator:latest`, builds `evaristor/recurrator:develop` on top, and runs `check`, `tests`, `coverage`, `mutants` and `verify` in the dev image. It pushes only if they pass, so a red run leaves the previous `latest` in production. Before pushing, it boots the prod image alone, with no volumes, and requires `/openapi.json` and `/` to respond. Tags are `latest` plus `%y%V`; `:develop` is never published.
- FastAPI serves `public/` at `/` after the API routes. The frontend and API share an origin, use root-relative API paths, and have no API-address setting; CORS is not enabled.
- Production serves the app at `http://recurrator/` over the tailnet: `recurrator_setup` maps host port 80 to 8000, and the `provisioner` cron probes that address. Local compose binds host 80 too, so a port change touches all three repos.
- `PUBLIC_DIR` walks up from `api.py` to the directory containing `public/index.html`, so app import and tests work from any working directory and under mutmut.
- The app is reached over plain HTTP on Tailscale, where `crypto.subtle` is unavailable; the frontend uses the local placeholder art and makes no remote requests.

## Mutation Testing

Configured in `setup.cfg` under `[mutmut]`; run `make mutants` inside the container and check survivors with `mutmut results`.

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

**Useful make targets:** `tests` (pytest unit tests), `test-cli` (ShellSpec), `test-frontend` (Playwright browser suite), `check` (lint + typecheck + test data validation), `coverage`, `mutants` (mutation testing via mutmut), `check_data` (Frictionless Data validation), `format` (black formatter), `setup` (`clean` + `install`), `verify` (qed acceptance tests, inside the develop image), `visual` (capture approval screenshots into `tests/visual/received`), `visual-check` (capture twice and confirm the screenshots are identical).

`pyproject.toml` declares only `typer`. `fastapi`, `uvicorn` and `requests` come from `Dockerfile`; `black`, `flake8`, `mypy`, `pylint`, `playwright`, `pytest`, `pytest-cov`, `mutmut`, `frictionless`, `httpx` and ShellSpec come from `Dockerfile.dev`. A native install needs both lists.

`make tests` is the unit suite, `make check` the gate, and `make verify` runs the qed acceptance tests inside the develop image. CI runs all three in the develop image; `coverage` and `mutants` report and do not gate the publish.

The editable install lives in the image, so `docker compose --profile develop run --rm develop make tests` works without a long-lived container. CI still starts one — `docker compose --profile develop run --name recurrator_dev --rm --detach develop sleep infinity` — and `exec`s into it, because the targets share generated modules and caches.
