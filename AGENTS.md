The system is a cloud-based, single-user API with a minimal HTML interface limited to listing today’s tasks, retrieving a single task, and marking completion or skip actions.
Task creation, updates, and deletion are handled through CLI or direct API access.
Each task stores the timestamps of its last three completions, and the next due date is computed as the median interval derived from those completions.
Scheduling is deterministic and executed via a lightweight background process that runs at midnight.
Task selection is capped at six per day and is driven by a prioritization algorithm that first ranks tasks by consecutive skip count.
If more than six tasks share the maximum skip count, selection is refined by choosing three tasks with longer recurrence intervals and three with the oldest due dates.
Completing a task resets its skip count, while skipping a task increments it by one.
Storage should be abstracted, with an initial implementation using flat files such as CSV or JSON and the option to migrate to a relational database.

### Minimal CLI (week one)

Using **Typer**

Commands:

* `list-all`
* `list-today`
* `mark-done --id <id>`

### Naming Conventions

#### CLI Commands (verbs → nouns, hyphen-case)
- **Verbs:** `add`, `list`, `mark`, `remove`, `reset`, `show`, `update`
- **Nouns:** `all`, `context`, `done`, `skips`, `starred`, `task`, `today`
- **Recommended Combinations:**
  - `add-task`
  - `list-all`
  - `list-context`
  - `list-starred`
  - `list-today`
  - `mark-done`
  - `remove-task`
  - `reset-skips`
  - `show-task`
  - `update-task`

#### Internal Functions (verbs → nouns, snake_case)

**In-memory (no side effects)**
- **Verbs:** `compute`, `create`, `filter`, `get`, `is`, `remove`, `set`, `update`
- **Nouns:** `description`, `due_date`, `due` `intervals`, `recurrence_days`, `task`
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
- **Attributes:** `id` (int), `description` (str), `context` (Context), `skip_count` (int), `starred` (bool), `skipped_date` (date | None)
- **Context Enum:** `Context.LAPTOP = "laptop"` (extend as needed)

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
- Use hyphen-case for CLI, snake_case for internal functions.
- Do not use `get_*` unless paired with `set_*`.
- Avoid abbreviations (e.g., use `context` not `ctx`).
- Avoid mixing multiple verbs in a single function name.
- CLI verbs (add, list, etc.) are for the interface; internal verbs (compute, is, filter) are for logic only.
