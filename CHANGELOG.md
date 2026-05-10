# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-05-09

### Added

- `filter_due_contexts` to list unique contexts from due/overdue tasks, sorted alphabetically

## [0.1.0] - 2026-05-09

### Added

- Task model with id, description, context, skip_count, starred attributes
- Context enum (CASA, LAPTOP, LIMPIAR)
- CSV-based persistence via `import_tasks_from_csv`
- 4-date completion tracking with date rotation on completion
- Adaptive recurrence: due date computed as median of last 4 completion
  intervals, defaulting to 14 days when insufficient data
- `compute_intervals`, `compute_latest_date`, `compute_recurrence_days`,
  `compute_due_date` business logic functions
- `filter_four_dates` to keep only the 4 most recent completion dates
- `filter_all_tasks_by_context` to filter tasks by context
- `filter_due_tasks_by_context` to find due/overdue tasks in a context
- `filter_due_tasks` to find all due/overdue tasks regardless of context
- Task retrieval and update via `get_task_by_id`, `update_task_as_done`,
  `update_task_skip_count`
- Skip count attribute: completing a task resets skip_count to 0
- Starred task support (boolean flag from CSV)
- FastAPI REST API with endpoints:
  - `GET /task/` — list all task IDs
  - `GET /task/{task_id}` — get single task details
  - `POST /task/{task_id}/done` — mark task as done, returns updated
    skip_count and due_date
- CLI with `list-all-tasks` command

[unreleased]: https://github.com/devarops/recurrator/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/devarops/recurrator/releases/tag/v0.2.0
[0.1.0]: https://github.com/devarops/recurrator/releases/tag/v0.1.0
