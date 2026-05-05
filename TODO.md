# To Do

## Gold

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
