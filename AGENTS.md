Task creation, updates, and deletion are handled through API access.
Each task stores the timestamps of its last four completions, and the next due date is computed as the median interval derived from those completions.
Scheduling is deterministic and executed via a lightweight background process that runs at midnight.
Task selection is capped at six per day and is driven by a prioritization algorithm that first ranks tasks by consecutive skip count.
If more than six tasks share the maximum skip count, selection is refined by choosing three tasks with longer recurrence intervals and three with the oldest due dates.
Completing a task resets its skip count, while skipping a task increments it by one.
Storage should be abstracted, with an initial implementation using flat files such as CSV or JSON and the option to migrate to a relational database.


```shell
$ docker compose run --rm -it --name recurrator_ci cli bash
# make init
```

```shell
docker exec recurrator_ci make tests
```


### Architecture: API-First Design

The system uses a **layered, API-first design**:

- **FastAPI (Primary Interface)**: RESTful API serving reads and writes over HTTP
- **Business Logic**: Pure functions used by the API
- **Storage (CSV)**: Persistent task data in CSV format at `~/.config/recurrator/tasks.csv`
- **CLI (Thin Wrapper)**: A thin Typer-based client. It serves as a implementation of the "Thin Wrapper" pattern, containing zero business logic and communicating exclusively with the API.

**Design Rationale**:
- Single source of truth: API owns all business logic
- Scalability: Easy to add web UI or mobile app (all call the same API)
- Architectural Integrity: The CLI demonstrates that the API is fully decoupled and self-sufficient.

**Deployment**:
- Docker-based architecture managed via `docker-compose`
- `api` service: Runs FastAPI with uvicorn (exposes port 8000), mounts `~/.config/recurrator/` for CSV persistence
- `cli` service: Finalized command-line environment for task management and automated testing.
- Both services use the same Docker image built from the project's Dockerfile

### CLI Specification

- **Thin Wrapper Pattern**: The CLI is a stateless HTTP client.
- **Zero-Logic Client**: The CLI does not import `io.py` or `compute.py`, proving a strict separation of concerns.
- **Mandatory Configuration**: The CLI enforces the `--csv` flag at the interface level, ensuring API-side data consistency.
- **Subcommand Preservation**: The CLI uses a minimal command registry to maintain a robust, extensible subcommand structure.

**Commands:**
- `recurrator list-all --csv <path>`: Lists task IDs (by querying the API).
- `recurrator version`: Displays current system version.


### Documentation Structure

Separation of concerns across markdown files:

| File | Audience | Purpose | Change Frequency |
|------|-----------|---------|------------------|
| **README.md** | End user | What the app does, how to use it | Rare |
| **AGENTS.md** | Developer | Constants, conventions, slow-changing rules and patterns | Very slow |
| **TODO.md** | Developer | Active work items, current Gold, implementation status | Frequent |

**Key principle**: If information changes frequently (e.g., "Functions Implemented", "Refactorings Applied"), it belongs in TODO.md, not AGENTS.md.

### REST API Endpoints

#### Reads (GET)
- ✅ `GET /tasks/` → Returns list of task IDs only (implemented)
  - Response: `[{"id": 8}]` (JSON array of IDs)
  - Use case: Quick listing without full task data
- ✅ `GET /tasks/:id` → Returns full task object (implemented)
  - Response: `{"id": 8, "description": "TypeLit.io", "context": "laptop", "skip_count": 1, "starred": false, "latest_date": "2025-08-19", "recurrence_days": 14, "due_date": "2025-09-02"}`
  - Use case: Display complete task information

#### Writes (POST)
- ⏳ `POST /tasks/:id/done` → Mark task as done (not yet implemented)
  - Response: `{"status": "success", "id": 8}`
  - Behavior:
    1. Reset `skip_count` to 0
    2. Rotate completion dates: shift `date_1` ← `date_2`, `date_2` ← `date_3`, `date_3` ← `date_4`, `date_4` ← today
    3. Leave `skipped_date` unchanged (handled by `compute_latest_date()`)
    4. Recalculation of `recurrence_days` and `due_date` handled by separate batch process (not immediate)

#### Task Response Schema
```json
{
  "id": 8,
  "description": "TypeLit.io",
  "context": "laptop",
  "skip_count": 1,
  "starred": false,
  "latest_date": "2025-08-19",
  "recurrence_days": 14,
  "due_date": "2025-09-02"
}
```

### Implementation Notes

**Testing Approach**:
- No mocks in test suite — tests assume API is running
- Tests are integration-style, not unit tests
- Run tests with: `docker exec recurrator_ci make tests`
- The `make init` step is required to set up the test environment in the recurrator_ci container before running tests

**Docker Compose Architecture**:
- Two services: `api` (FastAPI + uvicorn) and `cli` (Test environment)
- `cli` service has `depends_on: api` for startup order
- Both services share `~/.config/recurrator/` volume mount for CSV persistence and configuration
- Internal Docker DNS resolves `api` to the API service container

### Naming Conventions

#### Internal Functions (verbs → nouns, snake_case)

**In-memory (no side effects)**
- **Verbs:** `compute`, `create`, `filter`, `get`, `is`, `remove`, `set`, `update`
- **Nouns:** `description`, `due_date`, `due`, `intervals`, `recurrence_days`, `task`
- **Valid Examples:**
  - `compute_due_date(task)`
  - `compute_intervals(dates)`
  - `compute_recurrence_days(intervals)`
  - `create_task(task)`
  - `filter_by_context(tasks, context)`
  - `filter_starred(tasks)`
  - `get_description(task)`
  - `is_due(task, today)`
  - `remove_task(task)`
  - `set_description(task, description)`
  - `update_task(task)`

**Disk I/O (CSV/JSON)**
- **Verbs:** `import`, `export`
- **Nouns:** `tasks`, `csv`
- **Examples:**
  - `export_tasks_to_csv(tasks, path)`
  - `import_tasks_from_csv(path)`
- **CSV Schema:**
  - Columns: `id`, `context`, `description`, `date_1`, `date_2`, `date_3`, `date_4`, `skip_count`, `skipped_date`, `starred`
  - `date_1` through `date_4`: Last four completion timestamps (ISO 8601 dates, `NA` for missing)
  - `skip_count`: Consecutive skip count (integer, starts at 0)
  - `skipped_date`: Date of last skip (`NA` if never skipped)
  - `starred`: Starred status (0 = no, 1 = yes)

#### Task Class (Python)
- **Location:** `recurrator/io.py`
- **Attributes:** `id` (int), `description` (str), `context` (Context), `skip_count` (int), `starred` (bool), `latest_date` (date), `recurrence_days` (int)
- **Context Enum:** `Context.LAPTOP = "laptop"` (extend as needed)
- **Design Decision:** Raw CSV dates (`date_1`-`date_4`, `skipped_date`) are NOT exposed as Task attributes
- **Computed Properties:** 
  - `latest_date` is computed from `date_4` and `skipped_date` using `compute_latest_date()`
  - `recurrence_days` is computed from date intervals using `compute_recurrence_days()`

#### Refactoring Approach
- Follows **Martin Fowler's Refactoring Catalog (2nd Edition)**
- Key principle: *"The purpose of refactoring is not to reduce the number of lines, but to make the code more readable"*
- Rejected refactorings that sacrificed readability for fewer lines
- (Applied refactorings tracked in TODO.md)

#### Readability Rules

**Use extracted variables to express intent clearly.**

Avoid inlining values when it obscures meaning. Instead, extract values into well-named variables that express *what* is being tested or computed:

**Good (extracted variables):**
```python
# Test example
expected_value = 42
obtained_value = some_function()
assert obtained_value == expected_value

# Production code example
valid_dates = [d for d in dates if d is not None]
intervals = compute_intervals(valid_dates)
recurrence_days = compute_recurrence_days(intervals)
```

**Bad (inlined, hard to debug):**
```python
# Test example (avoid)
assert some_function() == 42

# Production code example (avoid)
return [(b - a).days for a, b in zip([d for d in dates if d is not None], [d for d in dates if d is not None][1:])]
```

**Why this matters:**
1. **Clear intent**: Variable names express *what* we expect and *what* we got
2. **Debugable**: On failure, both values are visible in the debugger
3. **Readable**: The code tells a story — "I expect X, I got Y, they should match"
4. **Consistent**: All code in the project follows this pattern

#### CSV Value Conversion Rules
- `starred`: `0` → `False`, `1` → `True` (use `bool(int(row["starred"]))`)
- `skip_count`: Direct `int()` conversion
- `id`: Direct `int()` conversion
- Date fields (`skipped_date`, `date_1`-`date_4`): `"NA"` → `None`, otherwise parse as `date.fromisoformat()`
- `context`: String matched to `Context` enum member

#### Import Conventions
- Use explicit imports in `__init__.py` (e.g., `from .compute import compute_intervals`) instead of wildcards
- Group imports with comments: internal pure functions vs I/O utilities

#### Consistency Rules
- Use snake_case for internal functions.
- Do not use `get_*` unless paired with `set_*`.
- Avoid abbreviations (e.g., use `context` not `ctx`).
- Avoid mixing multiple verbs in a single function name.

### Design Principles

- **Readability over brevity**: Clear variable names and extracted functions express intent
- **Explicit imports**: All dependencies visible at module level (PEP 8)
- **Single responsibility**: Helper functions do one thing well
- **Test-driven**: Only implement what tests require; generalize safely

### Commit Message Conventions

Follow a structured pattern for all commits:

1. **Emoji Prefix**:
   - ✅ `Implement/Fix`: Functional changes or bug fixes.
   - 📝 `Docs`: Documentation updates.
   - ♻️ `Refactor`: Code changes that don't change behavior.
   - 🛑🧪 `Failing Test`: Adding expected failing tests (TDD).
2. **Summary Line**: Concise, imperative description (e.g., "Implement feature X").
3. **Detailed Description**: Explain the "why" and "how," referencing design decisions or patterns.
4. **Tone**: Professional, technical, and direct.
