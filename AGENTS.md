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
- **Verbs:** `list`, `mark`, `add`, `update`, `remove`, `show`, `reset`
- **Nouns:** `tasks`, `task`, `today`, `context`, `starred`, `done`, `skips`, `all`
- **Recommended Combinations:**
  - `list-tasks`, `list-today`, `list-all`
  - `show-task`
  - `add-task`
  - `update-task`
  - `remove-task`
  - `mark-done`
  - `reset-skips`

#### Internal Functions (verbs → nouns, snake_case)

**In-memory (no side effects)**
- **Verbs:** `compute`, `is`, `select`, `filter`, `sort`
- **Nouns:** `intervals`, `median_interval`, `recurrence_days`, `due_date`, `due_tasks`, `description`, `tasks`, `due`
- **Valid Examples:**
  - `compute_intervals(dates)`
  - `compute_median_interval(intervals)`
  - `compute_due_date(task)`
  - `is_due(task, today)`
  - `select_tasks(tasks, context)`
  - `filter_starred(tasks)`
  - `sort_tasks_by_due_date(tasks)`
  - `description(task)` (Noun allowed for simple accessors)

**Disk I/O (CSV/JSON)**
- **Verbs:** `import`, `export`
- **Nouns:** `tasks`, `tasks_csv`
- **Examples:**
  - `import_tasks_from_csv(path)`
  - `export_tasks_to_csv(tasks, path)`

**Application-level (controlled side effects)**
- **Verbs:** `create`, `update`, `remove`, `mark`
- **Nouns:** `task`, `tasks`, `completion`, `done`
- **Examples:**
  - `create_task(task, path)`
  - `update_task(task, path)`
  - `remove_task(id, path)`
  - `mark_task_done(id, date, path)`

#### Consistency Rules
- Use hyphen-case for CLI, snake_case for internal functions.
- Do not use `get_*` unless paired with `set_*`.
- Avoid abbreviations (e.g., use `context` not `ctx`).
- Avoid mixing multiple verbs in a single function name.
- CLI verbs (add, list, etc.) are for the interface; internal verbs (compute, is, filter) are for logic only.
