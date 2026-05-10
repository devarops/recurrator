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
- **Data Models**: Domain constants and data classes belong in `models.py` (e.g., `SKIP_COUNT_RESET`, `DEFAULT_RECURRENCE_DAYS`, `Context`, `Task`).
- **Parameter Ordering**: `task_id` (specific) → specific parameters → `csv_path` (general).
- **Private Helpers**: Prefix internal-only functions with `_` and do not expose them in `__init__.py`.
- **Dependency Direction**: Enforce strict one-way dependencies. Never import from higher layers into lower layers.

---

## III. Verification & Environment Phase
*Ensuring functional parity and technical correctness.*

### Development Environment
```shell
# Build the image (use --no-cache to force a fresh pip install)
docker build --no-cache --tag evaristor/recurrator:latest .

# Initialize environment (interactive session)
docker compose run --rm -it --name recurrator_ci cli bash

# Inside container:
make install
make tests

# Run CI commands without entering the container:
docker compose run --rm cli make check
docker compose run --rm cli make coverage
docker compose run --rm cli make mutants
```

### Data Validation
Test CSV fixtures live in `tests/data/` and are validated against a
[Frictionless Data](https://frictionlessdata.io/) Tabular Data Package
descriptor (`tests/data/datapackage.json`).

- Schema constraints include field types, formats, required flags, and
  uniqueness. The `missingValues: ["NA"]` declaration recognizes `"NA"`
  as a null marker for optional date fields.
- Run `make check_data` to validate all CSV fixtures against the schema.
  The `check` target depends on `check_data`, so data integrity is
  verified alongside linting.
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
- **Request**: Accepts optional JSON. If empty, uses today's date.
- **Response**: 200 OK (no body).

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
    - 👾 For mutation testing: killing survivors, configuring mutmut.
    - 👷 For CI and infrastructure: pipeline changes, container setup.
2. **Structure**:
    - First line: Emoji prefix + imperative verb + concise description. Max 72 characters including emoji.
    - Second line: Blank.
    - Third line onward: Detailed explanation of the change explaining the "why" and "how" (wrap at 72 chars).
3. **Tone**: Professional, technical, and direct. Proper English grammar and punctuation.
