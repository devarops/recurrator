# To Do

## The Gold: List Contexts From Due/Overdue Tasks
- [ ] **`compute.py`: Add `get_contexts_from_tasks`** — Given a list of tasks, return sorted unique `Context` values.
- [ ] **`api.py`: Add `GET /context/due`** — Endpoint returning `{"contexts": [...]}` based on tasks due/overdue today.
- [ ] **`tests/`: Add tests for `get_contexts_from_tasks`** — Test with mixed contexts, empty list, single context.
- [ ] **`tests/`: Add tests for `GET /context/due`** — Test response shape and content.

## List Due/Overdue Tasks by Context
- [ ] **`compute.py`: Add `filter_tasks_by_context`** — Given a list of tasks and a `Context` enum, return only tasks matching that context.
- [ ] **`compute.py`: Add `filter_due_or_overdue`** — Given a list of tasks and a reference date, return only tasks where `due_date <= reference_date`.
- [ ] **`api.py`: Add `GET /task/due?context=`** — Endpoint returning due/overdue tasks as JSON array. Optional `context` query param to filter.
- [ ] **`tests/`: Add tests for `filter_tasks_by_context`** — Test with matching context, non-matching context, empty result.
- [ ] **`tests/`: Add tests for `filter_due_or_overdue`** — Test with due today, overdue, future date, mixed cases.
- [ ] **`tests/`: Add tests for `GET /task/due`** — Test API response shape, with and without context filter.

## Bug Fixes
- [ ] **Fix GitHub Actions workflow**: CLI test_list_all fails in CI because workflow doesn't start docker compose before running tests. All tests pass locally.

## Features
- [ ] **Gamification System**: Add point accumulation for completed tasks.

## Refactoring
- [ ] **Centralize Configuration**: Refactor to use config.json.

---

# Done

## Gold
- [x] **POST /task/{id}/done API endpoint**: Mark task as done.

## API Endpoints
- [x] **GET /task/**: List task IDs.
- [x] **GET /task/{id}**: Get single task.
- [x] **Change endpoints from `/tasks/` to `/task/`**: Singular resource naming consistency.

## Functions
- [x] `compute_intervals(dates: list[date | None]) -> list[int]` (in `compute.py`): Compute intervals in days between consecutive non-None dates
- [x] `compute_latest_date(date_4, skipped_date) -> date` (in `compute.py`): Returns max of two dates, handling None for skipped_date only
- [x] `compute_recurrence_days(intervals) -> int` (in `compute.py`): Compute recurrence days as median of intervals, defaulting to 14 days
- [x] `_parse_date(date_str) -> date | None` (in `io.py`): Helper to parse ISO 8601 strings, returns None for "NA"
- [x] `_row_to_task(row: dict) -> Task` (in `io.py`): Helper to convert CSV row to Task object
- [x] `import_tasks_from_csv(path) -> list[Task]` (in `io.py`): Import tasks from CSV file
- [x] `update_task_as_done(task_id, completion_date, csv_path) -> None` (in `io.py`): Mark task as done by rotating completion dates and resetting skip_count to 0

## Features
- [x] **Static Frontend**: HTML task viewer with Pico.css.

## Infrastructure
- [x] **FastAPI app**: Create FastAPI app.
- [x] **Docker Compose**: Two-service setup.
- [x] **All tests passing**: 19 tests.
- [x] **CORS middleware**: file:// protocol support.
