# Developer Manual

## Public Interface

The public interface is the current task and context HTTP API under `/api`, defined in `recurrator/api.py`. The browser frontend and the terminal client are separate repositories; both are clients of this API, speak only HTTP, and never access the CSV directly. `DOCS.md` lists the current elements. Planned elements are not part of the current interface; they live in `specs/*.spec.toml` and `DESIGN.md`.

## Operational map

- `models.py` — domain data structures; no external dependencies.
- `compute.py` — pure business logic; depends on `models`, `_config`, and `glicko2`.
- `io.py` — persistence; depends on `compute` and `models`.
- `api.py` — the HTTP interface; depends on `io`.
- Lower layers never import from higher layers.

The workflow, data model, API shape, and the reasons behind them are in `DESIGN.md`. Do not restate them here.

## Development environment

Run targets inside `develop`: `make setup && make check && make tests`, then `make verify`. The service shares the production-data mount; only `make check_data` reads it, and CI never runs it.

`TZ=America/Los_Angeles` in `Dockerfile`; `POST /api/task/{id}/done` uses `date.today()` in that timezone. Do not change without updating date-dependent assertions.

Targets: `tests`, `test-shell`, `check`, `coverage`, `mutants`, `check_data`, `format`, `setup`, `verify`. `make tests` is the unit suite, `make check` the gate, and `make verify` runs qed acceptance tests in the develop image.

`pyproject.toml` declares `glicko2==2.1.0`; `fastapi`, `uvicorn` and `glicko2` come from `Dockerfile`, and the test tools from `Dockerfile.dev`. `glicko2` has no type stubs, so `compute.py` carries a scoped `# type: ignore[import-untyped]`. The dev tools are unpinned; run `make format` before pushing.

The editable install lives in the image, so `docker compose --profile develop run --rm develop make tests` works without a long-lived container; CI starts `recurrator_dev` and `exec`s into it.

`.githooks/pre-push` runs `.pipelines/check.sh` on every push, which execs `make check tests` in the running `recurrator_dev` and aborts the push on failure; `.pipelines/init.sh` sets `core.hooksPath` to activate it.

## TDD cycle

Red → Fail (commit failing test) → Green (make it pass, commit) → Refactor.

- **Fail sub-phase**: write the test, run the suite, confirm exactly one test fails for the right reason, commit.
- Defer extra tests for the same behavioral gap so exactly one test fails per Red phase; add them back after Green.
- Failing test convention: use `pass` body only when the target function doesn't exist yet (fails at import); otherwise write real assertions.
- Tests that modify the CSV restore with the matching `update_*` and assert `_assert_file_unchanged`; see `_verify_task_as_done` or `test_task_done_idempotency`.

## Acceptance specs

`specs/*.spec.toml` holds the qed criteria; each names one user-observable HTTP API scenario and a pytest command. A criterion carries `skip = "Not implemented"` until its test in `tests/test_acceptance_*.py` exists.

## Commit emoji prefixes

🛑🧪 (Red), ✅🧪 (Green), ♻️ (refactor), 📝 (docs), 👾 (mutmut config), 🏹👾 (mutant hunting), 👷 (CI).

Example unit test: `pytest tests/test_api.py::test_get_single_task_id`.

## Naming conventions

Pure functions use `reference_date` (not `today`) for the cut-off/current date parameter, and `is_*` prefix for boolean-returning functions.

## Documentation

`README.md` is the overview for non-technical readers. `DOCS.md` lists the current HTTP API elements. `DESIGN.md` is the system's workflow and design. `TODO.md` is the ordered backlog. `specs/*.spec.toml` holds the observable criteria. The frontend, the TUI, and their documents live in their own repositories.

## Container and deployment

`Dockerfile.dev` adds the test and verification tools on top of `evaristor/recurrator:latest`; build prod first or the dev layer takes a stale base. The editable install is baked in at build time; the image has no default command, so every runner supplies uvicorn.

FastAPI serves the API under `/api`; `GET /` is not a route, there is no static mount, and this repository holds no frontend. The contract surface is `GET /api/openapi.json`, `GET /api/docs`, and `GET /api/redoc`.

`.github/workflows/actions.yml` builds `latest` then `develop`, runs `check`, `tests`, `coverage`, `mutants` and `verify`, smoke-tests prod, and pushes only if all pass; tags are `latest` and `%yV`.

The gateway that fronts this API and the frontend belongs to `recurrator_setup`; this image publishes no static files.

## Mutation testing

Configured in `setup.cfg` under `[mutmut]`; `make mutants` runs the suite and fails when any mutant survives, and `mutmut results` lists it.

## TODO.md

`TODO.md` is a flat ordered list: one `- [ ]` item and a six-space `Test:` line per task. The list order is the build order. The design lives in `DESIGN.md`; do not restate it here. It empties when the work is done.
