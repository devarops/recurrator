# The Gold

Idempotency for Done command — a task cannot be marked as done twice on the same day nor on two consecutive days.

## Plan

### 1. Validation function in compute.py

**Red:**

- File: `tests/test_compute.py`
- Scenario: Test `is_done_allowed(last_completion_date, today)` returns:
  - `False` when `last_completion_date == today` (same day)
  - `False` when `last_completion_date == today - 1` (consecutive day)
  - `True` when `last_completion_date == today - 2` (allowed)
  - `True` when `last_completion_date` is `None` (no prior completion)
- Fails because: `is_done_allowed` does not exist in `compute.py`.

**Green:**

- Implement `is_done_allowed(last_completion_date: date | None, today: date) -> bool` in `compute.py`.

### 2. API enforcement

**Red:**

- File: `tests/test_api.py`
- Scenario: Call `POST /task/{id}/done` twice in a row on the same task. First call returns 200. Second call returns 409 with `{"error": "<message>"}`. Restore CSV state after the test.
- Fails because: `post_task_done` handler does not check idempotency before updating.

**Green:**

- Update `post_task_done` in `api.py` to read the last completion date from the task, call `is_done_allowed`, and return 409 with an error envelope if the request is rejected.

## Outside the Plan

- **Document 409 response in DOCS.md:** Add the 409 Conflict status and error envelope to the `POST /task/{id}/done` endpoint documentation. Does not follow the Red/Green TDD format because it is a documentation-only change with no test or production behavior evolution.

---

# Backlog not part of the current Gold

The following items were removed from the original TODO.md to keep the plan focused on The Gold.
They remain valid work items for future cycles.

- Centralize Configuration: Refactor to use config.json.
- Set min and max recurrence days.
- Test frontend with Playwright or FastAPI TestClient.
- Prioritization algorithm.
- Add one extra task when we have lest than 6 tasks

## Prioritization algorithm

new function in `compute.py`:

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

## One extra task algorithm

**Purpose:** When a context has fewer than 6 due tasks, pick one upcoming (not yet due) task to pad the list. Complementary to `filter_six_tasks_by_context`.

**Scope:** Within a single context (matching `filter_six_tasks_by_context`).

**Side effects:** None. Skip tracking is handled elsewhere (API layer of prioritization algorithm).

new function in `compute.py`:

```python
def filter_one_extra_task(
    tasks: list[Task], context: Context, reference_date: date
) -> list[Task]:
```

**Contract:**
1. Start with `all_tasks_in_context = filter_all_tasks_by_context(tasks, context)`.
2. Exclude tasks where `due_date <= reference_date` (already due/overdue — handled by other algorithms).
3. Filter for `recurrence_days > 30` (strict; same as `>= 31`).
4. Sort by `due_date` ASC, then `recurrence_days` DESC (closest due date first; larger recurrence breaks ties).
5. Take the first element (nearest upcoming), return it as `[task]`, or `[]` if none qualify.
