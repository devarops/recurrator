# To Do

## The Gold: Add task description to context page | Show each task's description alongside its ID in context.html

## Algorithm
- [ ] Idempotency for Done command.
- [ ] Set min and max recurrence days.
- [ ] Prioritization algorithm.
  **Specification (per `AGENTS.md` per-context and 6-per-day cap):**

  New function in `compute.py`:
  ```python
  def filter_six_tasks_by_context(
      tasks: list[Task], context: Context, reference_date: date
  ) -> tuple[list[Task], list[Task]]:
  ```

  **Contract:**
  1. Start with `due_tasks = filter_due_tasks_by_context(tasks, context, reference_date)`.
  2. If `len(due_tasks) <= 6`, return `(due_tasks, [])` — no selection or skip needed.
  3. Precondition for prioritization: `len(due_tasks) >= 7`.
  4. Build `selected = []`, `remaining = copy(due_tasks)`, `i = 0`.
  5. While `len(selected) < 6` and `remaining` not empty:
     - `i += 1`
     - **Sort order for this cycle**:
       - Odd `i`: sort key = (`skip_count` DESC, `due_date` ASC, `recurrence_days` DESC)
       - Even `i`: sort key = (`skip_count` DESC, `recurrence_days` DESC, `due_date` ASC)
     - **Starred pick**: filter starred from remaining, sort by cycle key, take first → `selected`, remove from `remaining`. Break if 6 reached.
     - **Non-starred pick**: filter non-starred from remaining, sort by same cycle key, take first → `selected`, remove from `remaining`.
  6. After loop: `non_starred_remaining = [t in remaining if not t.starred]`.
  7. Return `(selected, non_starred_remaining)`.

  **Side effect (API layer):** The API calls `io.update_task_skip_count(task_id, skipped_date=today(), csv_path)` for each task in the second list.


## Frontend
- [ ] Show each task's description next to its ID on the context page

## Features
- [ ] Return coins in the Task object in the API response.

## Refactoring
- [ ] **Centralize Configuration**: Refactor to use config.json.

## Some day/Maybe
- [ ] Test frontend with Playwright or FastAPI TestClient.
