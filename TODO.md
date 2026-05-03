# To Do

## Gold
- [ ] **POST /tasks/{id}/done API endpoint**: Mark task as done.

## API Endpoints

## CLI Commands
- [ ] **show-task**: Show single task.
- [ ] **mark-done**: Mark task as done.

## Features
- [ ] **Gamification System**: Add point accumulation for completed tasks.

## Refactoring
- [ ] **Centralize Configuration**: Refactor to use config.json.

---

# Done

## API Endpoints
- [x] **GET /tasks/**: List task IDs.
- [x] **GET /tasks/:id**: Get single task.

## CLI Commands
- [x] **list-all**: List all tasks.

## Functions
- [x] `compute_intervals(dates: list[date | None]) -> list[int]` (in `compute.py`): Compute intervals in days between consecutive non-None dates
- [x] `compute_latest_date(date_4, skipped_date) -> date` (in `compute.py`): Returns max of two dates, handling None for skipped_date only
- [x] `compute_recurrence_days(intervals) -> int` (in `compute.py`): Compute recurrence days as median of intervals, defaulting to 14 days
- [x] `_parse_date(date_str) -> date | None` (in `io.py`): Helper to parse ISO 8601 strings, returns None for "NA"
- [x] `_row_to_task(row: dict) -> Task` (in `io.py`): Helper to convert CSV row to Task object
- [x] `import_tasks_from_csv(path) -> list[Task]` (in `io.py`): Import tasks from CSV file

## Features
- [x] **Static Frontend**: HTML task viewer with Pico.css.

## Infrastructure
- [x] **FastAPI app**: Create FastAPI app.
- [x] **Docker Compose**: Two-service setup.
- [x] **CLI migration**: HTTP calls wrapper.
- [x] **All tests passing**: 13 tests.
- [x] **CORS middleware**: file:// protocol support.

## Refactoring
- [x] **I/O Module**: Extract Function, Introduce Parameter Object, Standardize None Handling, Replace Magic Number.
- [x] **API Module**: Extract Function, Add Type Hints, Rename Constant.
- [x] **CLI Module**: Remove CSV Import, Add HTTP Client, Refactor list_all(), Update _print_task_ids(), Add Error Handling.
