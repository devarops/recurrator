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
- Error envelope: `{"error": "<message>"}`; non-200 responses use `JSONResponse(content=..., status_code=N)`, not a returned `(dict, int)`, which serializes as a JSON array.
- CLI tabular output MUST be valid CSV (header + data rows); non-tabular output uses JSON.

**Documentation:** `DOCS.md` lists the HTTP API only; describe the frontend and CLI in `README.md`. `CHANGELOG.md` records only endpoint changes.

**No Derived Values in Presentation Layer:** The frontend may transform data for display but must never compute new atomic values (no arithmetic, statistics, joins, or aggregations); derived values belong in `compute_*`.

**Naming conventions in `compute.py`:** Pure functions use `reference_date` (not `today`) for the cut-off/current date parameter, and `is_*` prefix for boolean-returning functions.

**Visual approval:** `tests/visual/capture.py` lists the scenarios; `make visual` rewrites `received/` and the human approves. The local `ui-red`, `ui-green`, `ui-refactor`, and `ui-approve` commands run the frontend TDD loop; `ui-approve` requires a fresh capture, runs the three suites, writes `tests/visual/review.html`, and on approval copies `received/` into `approved/` and updates the spec and styleguide in the same commit. `tests/visual/specs/recurrator-frontend-spec.md` is the only reference, and the browser tests, approved PNGs, spec, and styleguide must agree. `renderMarkdown` decodes the CSV's literal `\n` before parsing.

## TDD Cycle

```
Red → Fail (commit failing test) → Green (make it pass, commit) → Refactor
```

- **Fail sub-phase**: Write the test, run suite, confirm exactly one test fails for the right reason, commit.
- Defer extra tests for the same behavioral gap so exactly one test fails per Red phase; add them back after Green.
- Failing test convention: use `pass` body only when the target function doesn't exist yet (fails at import); otherwise write real assertions.
- Tests that modify the CSV restore with the matching `update_*` and assert `_assert_file_unchanged`; see `_verify_task_as_done` or `test_task_done_idempotency`.

**Commit emoji prefixes:** 🛑🧪 (Red), ✅🧪 (Green), ♻️ (refactor), 📝 (docs), 👾 (mutmut config), 🏹👾 (mutant hunting), 👷 (CI).

Run a unit test with `pytest tests/test_api.py::test_get_due_contexts`; browser: `RUN_BROWSER=1 pytest tests/browser/test_home.py::test_all_tile_shows_due_contexts`; CLI tests need the compose `api` service.

## Data Modeling & CSV Mapping

- `Task` is a plain class with a `Dates` dataclass for date fields. Computed attributes (`latest_date`, `recurrence_days`, `due_date`, `coins`) are computed at read time in `io._row_to_task()`; they are not stored.
- `latest_done_date` is stored in `date_4` but lives in `Dates` alongside computed fields, first.
- Add a computed field in `compute.py`, orchestrate it in `_row_to_task`, and pass it to `Task.__init__`.
- CSV conversion: `starred` `0`/`1` → `False`/`True`; dates `"NA"` → `None`, else `date.fromisoformat()`; `id`/`skip_count` → `int()`.
- `recurrator/_contexts.py` is generated from the Frictionless datapackage and `_config.py` from `config.json` by `make install`/`src/entrypoint.sh`; both are gitignored, and `create_contexts.sh` falls back to `tests/data/datapackage.json` without production files.

## Container Startup and Deployment

- `Dockerfile.dev` adds the test and verification tools on top of `evaristor/recurrator:latest`; build prod first or the dev layer takes a stale base.
- The editable install is baked in at build time; the image has no default command, so every runner supplies uvicorn.
- `.github/workflows/actions.yml` builds `latest` then `develop`, runs `check`, `tests`, `test-frontend`, `coverage`, `mutants` and `verify`, smoke-tests prod, and pushes only if all pass; tags are `latest` and `%y%V`.
- FastAPI serves `public/` at `/` after the API routes. Frontend and API share an origin, use root-relative API paths, and have no API-address setting; CORS is not enabled.
- `PUBLIC_DIR` walks up from `api.py` to `public/index.html`, so app import and tests work from any working directory and under mutmut.
- The frontend uses local art and makes no remote requests.

## Mutation Testing

Configured in `setup.cfg` under `[mutmut]`; run `make mutants` inside the container and check survivors with `mutmut results`.

## TODO.md

`TODO.md` keeps one checklist above detail sections: every `##` section appears as an item linked with `details below`, and items without one end with `backlog only`.

## Development Environment

Run targets inside `develop`: `make setup && make check && make tests`, then `make verify`. The service shares the production-data mount; only `make check_data` reads it, and CI never runs it.

`TZ=America/Los_Angeles` in `Dockerfile`; `POST /task/{id}/done` uses `date.today()` in that timezone. Do not change without updating date-dependent assertions.

Targets: `tests`, `test-cli`, `test-frontend`, `check`, `coverage`, `mutants`, `check_data`, `format`, `setup`, `verify`, `visual`. `make tests` is the unit suite, `make check` the gate, and `make verify` runs qed acceptance tests in the develop image.

`pyproject.toml` declares `typer` and `glicko2==2.1.0`; `fastapi`, `uvicorn`, `requests` and `glicko2` come from `Dockerfile`, and the test tools from `Dockerfile.dev`. `glicko2` has no type stubs, so `compute.py` carries a scoped `# type: ignore[import-untyped]`. The dev tools are unpinned; run `make format` before pushing.

The editable install lives in the image, so `docker compose --profile develop run --rm develop make tests` works without a long-lived container; CI starts `recurrator_dev` and `exec`s into it.
