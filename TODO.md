# The Gold

- Idempotency for Done command

## Plan

A task should no be able to be mark as done twice in the same day nor in two consecutive days.

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
