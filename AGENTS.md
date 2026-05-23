# Developer Guidelines & Project Standards

This document outlines the lifecycle of development for the `recurrator` project, from initial design to final submission.

---

## I. Design & Analysis Phase
*Understanding the system logic and architectural constraints before implementation.*

### Business Logic & Task Recurrence
- **Recurrence Algorithm**: Each task stores the timestamps of its last four completions. The next due date is computed as the median interval derived from those completions.
- **Scheduling**: Scheduling is deterministic and executed via a lightweight background process that runs at midnight.
- **Prioritization**: Task selection is capped at six per day. Ranks are determined first by consecutive skip count. If tied, selection favors tasks with longer recurrence intervals and older due dates.
- **State Changes**: Completing a task resets its skip count to zero; skipping a task increments it by one.
- **Storage Strategy**: Storage is abstracted (currently flat-file CSV/JSON) to allow for future migration to a relational database.

### Architecture Principles
The system follows an **API-first, layered architecture** with strict one-way dependencies:

**Layered Module Structure:**
- **`models.py`**: Domain data structures (enums, dataclasses, constants). Zero external dependencies.
- **`compute.py`**: Pure business logic functions. Depends only on `models`.
- **`io.py`**: Persistence and I/O operations. Depends on `compute` and `models`.
- **`api.py`** & **`cli.py`**: Interface layers. Depend on `io` and `models`.

**Dependency Rule:** Lower layers NEVER import from higher layers. This prevents circular dependencies and maintains clean separation of concerns.

**API Design:**
- **API as Single Source of Truth**: All business logic resides in the API; the CLI contains zero business logic.
- **Stateless CLI**: The CLI is a thin HTTP client. It does not import `io.py` or `compute.py` and communicates exclusively with the API.
- **Mandatory Configuration**: The CLI enforces the `--csv` parameter to ensure data consistency on the API side.
- **Single-Responsibility Endpoints**: Each API endpoint returns only the data scoped to its resource. List endpoints return identities; detail endpoints return attributes. If a client needs richer data, it composes from multiple endpoints rather than inflating a list endpoint's contract.
    - **Example**: `GET /context/{context_id}` returns only task IDs. When the context page needs to show task descriptions, the frontend fetches each task individually from `GET /task/{task_id}` instead of making the context endpoint also return descriptions.
- **Action Responses are Confirmation Subsets**: State-changing endpoints (POST, PUT, DELETE) return only the subset of fields needed to confirm what changed, rather than the full resource. The response typically includes the resource `id` and the fields that were modified. Returning the full resource is permitted as a special case of a "subset that includes everything" — it is not the default.
    - **Example**: `POST /task/{id}/done` returns `{id, skip_count, due_date}`, not the full task dict. The client learns the new `skip_count` (always 0) and the new `due_date` — exactly what it needs to update its UI.
- **Error Envelope**: Every error response uses a JSON body with a single `"error"` key containing a human-readable message string, paired with an appropriate HTTP status code.
    - **Example**: `{"error": "Task not found"}` with status `404`. This is consistent regardless of which layer detects the error.
- **CLI Output is CSV or JSON**: CLI commands producing tabular data MUST output valid CSV (header row + data rows), making `command --csv path/to/file.csv > table.csv` a valid pipeline producing a correct CSV file. When the output is inherently non-tabular (single value, unstructured text, nested data), JSON is the acceptable alternative.
    - **Example**: `list-all-tasks` prints an `id` header then one ID per line — valid CSV with one column. A future `show-config` command might output JSON since config is nested key-value data.
- **Presentation is a Client Responsibility**: The client transforms API data for display but does not derive new values through computation. Every value in the rendered output must directly correspond to a value that existed as an independent atomic entity in the API response. Adding `?sort`, computed display fields, or presentation-only filters to API contracts couples presentation to the backend and is avoided.
    - **Example**: The context page sorts tasks by Coins descending. The frontend receives `coins` from `GET /task/{id}` and sorts the array in JavaScript. No new value is computed on the client.
- **No Derived Values in the Presentation Layer**: The frontend may transform data for display, but it must never introduce new atomic values through computation. A value that does not exist as an independent entity in the source (the API response) must be added to the backend, not derived on the client.

    **Permitted frontend adaptations** (transformations that preserve atomic identity):
    - Conversion of file types to native language types (string → number, etc.)
    - Type coercion (e.g., as.numeric, as.Date, as.character)
    - Normalization of missing values (NaN, NA, None, Null → language-native null)
    - Character transformations that do not alter meaning (tolower, toupper, trimws, substr)
    - Renaming and reordering columns
    - Selecting columns
    - Filtering rows
    - Mechanical restructuring (individual scalars → vector or table)

    **Prohibited in the presentation layer** (these belong in `compute_*`):
    - Any arithmetic operations (+, -, *, /, ^)
    - Statistical operations (mean, sum, sd, quantile)
    - Joins between tables
    - Aggregations (group_by + summarize)
    - Any operation that derives a value that did not exist as an independent atomic entity in the source
- **Frontend Growth Threshold**: When `public/main.js` exceeds 400 lines, evaluate whether its complexity warrants dedicated frontend tests (e.g., Playwright, component tests, or end-to-end browser automation). The current smoke test (HTML structure check) and inline console.asserts serve as a lightweight safety net below that threshold.

    The current frontend safety net consists of two layers:

    - **pytest structural check** (`test_frontend.py`): Reads each HTML file from disk and asserts the presence of key DOM landmarks — `<div id="contexts">` on the index page, `<div id="tasks">` and `<h2 id="contextName">` on the context page, `<div id="task">` and `<a id="contextLink">` on the task page, plus `<script src="main.js">` and the `<title>` on every page. This catches broken merges, accidental deletions, or structural edits that strip required elements.

    - **Inline JS assertions**: Each page init function (`initTaskPage`, `initContextPage`, `initIndexPage`) runs `console.assert` on the DOM elements it depends on before proceeding, reporting missing elements to the browser console. A `_selfCheck()` function runs once at page load and verifies all expected function names exist in the global scope, catching accidental function renames or deletions before they cause silent failures downstream.

### Documentation Meta-Structure
| File | Audience | Purpose | Change Frequency |
|------|-----------|---------|------------------|
| **README.md** | End user | What the app does, how to use it | Rare |
| **AGENTS.md** | Developer | Design principles, conventions, guidelines, patterns | Very slow |
| **DOCS.md** | Developer | Observable behavior from test suite | Frequent |
| **CHANGELOG.md** | Developer | Record of interface changes following SemVer and Keep a Changelog | Every release |
| **TODO.md** | Developer | Active work items, backlog, current Gold | Frequent |

---

## II. Coding & Implementation Phase
*Tactical rules for writing clean, maintainable, and idiomatic code.*

### Core Philosophy
- **Readability over Brevity**: Follow Martin Fowler's Refactoring Catalog. The goal is to make code more readable, not necessarily shorter.
- **Test-Driven Development (TDD)**: Only implement what tests require.
- **Single Responsibility**: Each function or helper should do one thing well.

### TDD Cycle Details
The standard Red-Green-Refactor cycle includes a distinct **Fail sub-phase** between Red and Green:

1. **Red** — Identify the next smallest failing test in plain English (no code).
2. **Fail** — Write the test code, run the suite, confirm exactly one test fails for the right reason, commit the failing test.
3. **Green** — Implement the minimal production code to make the failing test pass, verify all tests pass, commit.
4. **Refactor** — Improve internal structure without changing observable behavior.

**Failing test convention:** The initial test body uses `pass` — it fails at import/resolution time because the target function doesn't exist. After Green, the `pass` is replaced with real assertions.

**After-Gold test pattern:** Once Green reaches The Gold, subsequent commits add strengthening assertions (specific IDs, counts, alternative scenarios) to the same test. These use the `🥇🧪` emoji prefix.

### Naming Conventions (Verbs → Nouns)
Use `snake_case` and avoid abbreviations (e.g., `context` instead of `ctx`).

**In-memory (Pure functions in `compute.py`)**
- **Verbs**: `compute`, `filter`, `is`
- **Nouns**: `description`, `due_date`, `intervals`, `recurrence_days`, `task`
- *Example*: `compute_recurrence_days(intervals)`

**Disk I/O (Persistence in `io.py`)**
- **Verbs**: `import`, `export`, `get`, `set`, `create`, `update`, `remove`
- **Nouns**: `tasks`, `csv`
- *Example*: `get_task_by_id(task_id, csv_path)`, `update_task_as_done(task_id, completion_date, csv_path)`

### Data Modeling & CSV Mapping
- **Task Object Design**: Raw CSV dates (`date_1` to `date_4`) are NOT exposed as attributes. Instead, use computed properties like `latest_date` and `recurrence_days`.
- **CSV Conversion Rules**:
    - `starred`: `0` → `False`, `1` → `True`.
    - `date fields`: `"NA"` → `None`, otherwise `date.fromisoformat()`.
    - `id`/`skip_count`: Direct `int()` conversion.

### Readability Standards: Extracted Variables
Avoid inlining complex logic. Use well-named variables to express intent.

**Good (Expressive)**
```python
valid_dates = [d for d in dates if d is not None]
intervals = compute_intervals(valid_dates)
recurrence_days = compute_recurrence_days(intervals)
```

**Bad (Obscure)**
```python
return [(b - a).days for a, b in zip([d for d in dates if d is not None], [d for d in dates if d is not None][1:])]
```

### Module Hygiene
- **Imports**: Use explicit imports in `__init__.py`. Group imports by layer: "Data models", "Internal Pure Functions", "I/O Utilities".
- **Data Models**: Domain constants and data classes belong in `models.py` (e.g., `SKIP_COUNT_RESET`, `DEFAULT_RECURRENCE_DAYS`, `Task`). The `Context` enum is generated at build time from `datapackage.json` — see `src/create_contexts.sh`.
- **Parameter Ordering**: `task_id` (specific) → specific parameters → `csv_path` (general).
- **Private Helpers**: Prefix internal-only functions with `_` and do not expose them in `__init__.py`.
- **Dependency Direction**: Enforce strict one-way dependencies. Never import from higher layers into lower layers.

---

## III. Verification & Environment Phase
*Ensuring functional parity and technical correctness.*

### Development Environment
```shell
# Build the Docker image (needed on first setup or after changes to Dockerfile):
docker build --tag evaristor/recurrator:latest .

# Initialize a container with an interactive shell:
docker compose run --interactive --name recurrator_ci --rm --tty cli bash

# Inside container:
make init
make tests

# Alternatively, run tests directly without entering the container:
docker compose run --detach --name recurrator_ci --rm cli sleep infinity
docker compose exec cli make init
docker compose exec cli make check
docker compose exec cli make tests
docker compose exec cli make coverage
docker compose exec cli make mutants
```

**Important**: The container runs in `America/Los_Angeles` timezone. The
`POST /task/{id}/done` endpoint uses `date.today()` which reflects this
timezone. Do not change the `TZ` env var in the Dockerfile without updating
all date-dependent assertions.

### Data Validation
Test CSV fixtures live in `tests/data/` and are validated against a
[Frictionless Data](https://frictionlessdata.io/) Tabular Data Package
descriptor (`tests/data/datapackage.json`).

- Schema constraints include field types, formats, required flags, and
  uniqueness. The `missingValues: ["NA"]` declaration recognizes `"NA"`
  as a null marker for optional date fields.
- The schema's `enum` constraint on the `context` field is the single source of
  truth for valid task contexts. The Python `Context` enum is generated from it
  at build time by `src/create_contexts.sh` (requires `jq`).
- Run `make check_data` to validate all CSV fixtures against the schema.
  `check_test_data` validates test fixtures only; `check_production_data`
  validates the production file. The `check` target runs `check_test_data`
  before linting and type checking.
- Use the `/data-mutation-test` OpenCode command (defined in
  `~/.config/opencode/commands/`) to verify the schema catches specific
  mutations: the workflow mutates a CSV, runs validation expecting failure,
  restores the file, and tightens the schema if the mutation goes
  undetected.

### Mutation Testing
- Configuration lives in `setup.cfg` under the `[mutmut]` section.
- The `paths_to_mutate` option tells mutmut which package directory to mutate.
- Run `make mutants` to execute mutation testing inside the container.
- To verify no surviving mutants remain, run `mutmut results` — survivors are
  listed as output; an empty result means zero survivors.

### Feature Specifications
**POST task/{id}/done**
- **Behavior**: Marks task as done by rotating completion dates (date_1 ← date_2 ← date_3 ← date_4 ← completion_date), resets `skip_count` to 0, and clears `skipped_date`.
- **Request**: Accepts optional JSON. If empty, uses today's date (America/Los_Angeles timezone).
- **Response**: 200 OK with JSON body containing `id`, `skip_count`, and `due_date`.

---

## IV. Release & Submission Phase
*Finalizing and documenting changes.*

### Commit Message Conventions
1. **Emoji Prefix**:
    - 🛑🧪 For red phase of TDD: failing test code only.
    - ✅ For green phase of TDD: functional changes.
    - ♻️ For refactoring phase of TDD: non-functional code changes.
    - 📝 For documentation updates.
    - 🥇🧪 For after-gold test pattern: strengthening assertions added after The Gold is reached.
    - 👾 For mutation testing: configuring mutmut.
    - 🏹👾 For mutation testing: hunting surviving mutants.
    - 👷 For CI and infrastructure: pipeline changes, container setup.
2. **Structure**:
    - First line: Emoji prefix + imperative verb + concise description. Max 72 characters including emoji.
    - Second line: Blank.
    - Third line onward: Detailed explanation of the change explaining the "why" and "how" (wrap at 72 chars).
3. **Tone**: Professional, technical, and direct. Proper English grammar and punctuation.
