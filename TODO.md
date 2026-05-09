# To Do

## The Gold: filter_all_tasks_by_context() [compute.py]: Filter all tasks matching a given Context (Done)

## List Contexts From Due/Overdue Tasks
- [ ] **`compute.py`: Add `filter_due_contexts`** — Given a list of tasks, return sorted unique `Context` values from due/overdue tasks.
- [ ] **`api.py`: Add `GET /context/`** — Endpoint returning `{"contexts": [...]}` based on tasks due/overdue today.
- [ ] **`tests/`: Add tests for `filter_due_contexts`** — Test with mixed contexts, empty list, single context.
- [ ] **`tests/`: Add tests for `GET /context/`** — Test response shape and content.

## List Due/Overdue Tasks by Context
- [x] **`compute.py`: Add `filter_all_tasks_by_context`** — Given a list of tasks and a `Context` enum, return only tasks matching that context.

- [ ] **`api.py`: Add `GET /context/{context_id}`** — Endpoint returning due/overdue tasks as JSON array filtered by context.

- [x] **`tests/`: Add tests for `filter_all_tasks_by_context`** — Test with matching context, non-matching context, empty result.
- [ ] **`tests/`: Add tests for `GET /context/{context_id}`** — Test API response shape, with and without context filter.

## Bug Fixes
- [ ] **Fix GitHub Actions workflow**: CLI test_list_all fails in CI because workflow doesn't start docker compose before running tests. All tests pass locally.

## Features
- [ ] **Gamification System**: Add point accumulation for completed tasks.

## Refactoring
- [ ] **Centralize Configuration**: Refactor to use config.json.

---

## Inventory of future and current functions

| File | Function Name | Verb | Status | Description |
|------|--------------|------|--------|-------------|
| `compute.py` | `compute_intervals` | `compute` | Done | Compute intervals in days between consecutive non-None dates |
| `compute.py` | `compute_latest_date` | `compute` | Done | Returns max of date_4 and skipped_date |
| `compute.py` | `compute_recurrence_days` | `compute` | Done | Compute recurrence days as median of intervals, default 14 |
| `compute.py` | `compute_due_date` | `compute` | Done | Add recurrence_days to latest_date |
| `compute.py` | `filter_four_dates` | `filter` | Done | Keep 4 most recent dates from list + new date |
| `compute.py` | `filter_all_tasks_by_context` | `filter` | Done | Filter all tasks matching a given Context |
| `compute.py` | `filter_due_tasks_by_context` | `filter` | To Do | Filter due tasks matching a given Context |
| `compute.py` | `filter_due_contexts` | `filter` | To Do | Return sorted unique Context values from due/overdue tasks |
| `io.py` | `import_tasks_from_csv` | `import` | Done | Import tasks from CSV file |
| `io.py` | `import_dates_from_csv` | `import` | Done | Return list of 4 dates for a given task |
| `io.py` | `update_task_dates` | `update` | Done | Update date_1..date_4 for a task in CSV |
| `io.py` | `update_task_skip_count` | `update` | Done | Update skip_count for a task in CSV |
| `io.py` | `update_task_as_done` | `update` | Done | Mark task as done, rotate dates, reset skip_count |
| `io.py` | `get_task_by_id` | `get` | Done | Get a single Task object by ID from CSV |
| `api.py` | `get_all_tasks` | `get` | Done | GET /task/ — list task IDs (was `get_tasks`) |
| `api.py` | `get_task_by_id` | `get` | Done | GET /task/{id} — get single task (was `get_task`) |
| `api.py` | `post_task_done` | `post` | Done | POST /task/{id}/done — mark task as done |
| `api.py` | `get_due_contexts` | `get` | To Do | GET /context/ — list unique contexts from due/overdue tasks |
| `api.py` | `get_tasks_by_context` | `get` | To Do | GET /context/{context_id} — list due/overdue tasks by context |
| `cli.py` | `version` | — | Done | Print version |
| `cli.py` | `list_all_tasks` | `list` | Done | List all task IDs (was `list_all`) |
