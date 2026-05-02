# Gold (TDD Target)

## Current: CLI command `list-all`
- **Description**: A Typer command that loads tasks from the default CSV file and displays them in a readable format showing id, description, context, skip_count, starred, latest_date, recurrence_days, and due_date for each task.
- **Status**: Not Started

---

## Completed

### CLI command `import_tasks_from_csv(path)`
- Status: ✅ Complete

---

## Chores

- [x] Verify `compute_latest_date(date_4, skipped_date)` returns `date_4` if `skipped_date` is `None`
