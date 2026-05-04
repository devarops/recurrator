# Design Principles, Conventions, and Development Guidelines

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


### Architecture Principles

The system is designed with an **API-first, layered architecture**:

- **API as Single Source of Truth**: All business logic resides in the API; no logic in CLI
- **Scalability**: The design enables future clients (web UI, mobile) without code duplication
- **Separation of Concerns**: CLI is a thin stateless HTTP client with zero business logic

### CLI Design Pattern

- **Thin Wrapper**: The CLI does not import `io.py` or `compute.py`; it communicates exclusively with the API
- **Stateless Client**: All state management is server-side
- **Mandatory CSV Configuration**: The CLI enforces `--csv` parameter to ensure API-side data consistency

### Documentation Structure

Separation of concerns across markdown files:

| File | Audience | Purpose | Change Frequency |
|------|-----------|---------|------------------|
| **README.md** | End user | What the app does, how to use it | Rare |
| **AGENTS.md** | Developer | Design principles, conventions, patterns | Very slow |
| **IMPLEMENTATION.md** | Developer | Observable behavior from test suite | Only with code changes |
| **TODO.md** | Developer | Active work items, current Gold, implementation status | Frequent |

**Key principle**: If information changes frequently (e.g., "Functions Implemented", "Refactorings Applied"), it belongs in TODO.md, not AGENTS.md.

### Naming Conventions

#### Internal Functions (verbs → nouns, snake_case)

**In-memory (no side effects)**
- **Verbs:** `compute`, `filter`, `get`, `is`, `set`
- **Nouns:** `description`, `due_date`, `due`, `intervals`, `recurrence_days`, `task`
- **Valid Examples:**
  - `compute_due_date(task)`
  - `compute_intervals(dates)`
  - `compute_recurrence_days(intervals)`
  - `filter_by_context(tasks, context)`
  - `filter_starred(tasks)`
  - `get_description(task)`
  - `is_due(task, today)`
  - `set_description(task, description)`

**Disk I/O (CSV/JSON)**
- **Verbs:** `import`, `export`, `create`, `update`, `remove`
- **Nouns:** `tasks`, `csv`
- **Examples:**
  - `export_tasks_to_csv(tasks, path)`
  - `import_tasks_from_csv(path)`
  - `update_task_dates(task_id, dates, path)`
  - `update_task_skip_count(task_id, skip_count, csv_path)`
  - `update_task_as_done(task_id, completion_date, csv_path)`
  - `create_task_in_csv(task, path)`
  - `remove_task_from_csv(task_id, path)`

#### Task Class Design Decision

- **Location:** `recurrator/io.py`
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

**Parameter Ordering**
- `task_id` first (specific identifier)
- Other parameters in middle (specific to general)
- `csv_path` last (general file path)

**Helper Functions**
- Functions prefixed with `_` are private/internal helpers
- Not exposed in `__init__.py` for external import
- Used to reduce duplication within a module

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
