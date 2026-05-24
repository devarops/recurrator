# To Do

## The Gold

Return coins in the Task object in the API response, and consume it from the frontend instead of computing it client-side.

## Plan

1. **Add `coins` attribute to Task model, computed during CSV import**

   **Red:**
   - File: `tests/test_io.py`
   - Scenario: In `test_import_tasks_from_csv_single_task`, assert `first_task.coins == 14` (task 8: unstarred, recurrence_days=14 → coins=14). Add a new test importing `test_contexts.csv` that asserts `task.coins` for a starred task, e.g. task 1 (starred, recurrence_days=21 → coins=42).
   - Expected: Imported tasks have a `coins` attribute matching the expected value, with starred tasks producing double the recurrence days.
   - Fails because: `Task` has no `coins` attribute and `_row_to_task` does not compute it.

   **Green:**
   - Add `coins: int` parameter to `Task.__init__` in `models.py`.
   - Import `compute_coins` in `io.py` and call it in `_row_to_task` to produce the `coins` value from `dates.recurrence_days` and the task's `starred` flag.

2. **Return `coins` from the task detail API endpoint**

   **Red:**
   - File: `tests/test_api.py`
   - Scenario: Add a new test fetching a starred task from `test_contexts.csv` (task 1) and asserting `"coins": 42`.
   - Expected: API response for `GET /task/{id}` includes a `"coins"` field.
   - Fails because: `_task_to_dict` in `api.py` does not include `coins` in the response dict.
   - Note: Two additional test updates were deferred to keep exactly one failing test:
     - `test_get_task_by_id_default_csv`: add `"coins": 14` (task 8, unstarred)
     - `test_get_task_by_id_alternative_csv`: add `"coins": 33` (task 3, unstarred)

   **Green:**
   - Add `"coins": task.coins` to the dict returned by `_task_to_dict` in `api.py`.

## Outside the Plan

- **Frontend migration:** Update `public/main.js` — replace client-side coin computation (`a.starred ? a.recurrence_days * 2 : a.recurrence_days` and analogous lines) with `a.coins` from the API response.
- **Documentation update:** Add `coins` field to the `GET /task/{id}` response in `DOCS.md` and to the Task object model section.

## Backlog

The following items were removed from the original TODO.md to keep the plan focused on The Gold. They remain valid work items for future cycles.

- Centralize Configuration: Refactor to use config.json.
- Idempotency for Done command.
- Set min and max recurrence days.
- Test frontend with Playwright or FastAPI TestClient.
- Prioritization algorithm.
