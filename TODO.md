# To Do

## The Gold: `compute.py` | `filter_due_contexts` | Return sorted unique Context values from due/overdue tasks

## List Contexts From Due/Overdue Tasks
- [ ] **`compute.py`: Add `filter_due_contexts`** — Given a list of tasks, return sorted unique `Context` values from due/overdue tasks.
- [ ] **`api.py`: Add `GET /context/`** — Endpoint returning `{"contexts": [...]}` based on tasks due/overdue today.
- [ ] **`tests/`: Add tests for `filter_due_contexts`** — Test with mixed contexts, empty list, single context.
- [ ] **`tests/`: Add tests for `GET /context/`** — Test response shape and content.

## List Due/Overdue Tasks by Context
- [ ] **`api.py`: Add `GET /context/{context_id}`** — Endpoint returning due/overdue tasks as JSON array filtered by context.
- [ ] **`tests/`: Add tests for `GET /context/{context_id}`** — Test API response shape, with and without context filter.

## Bug Fixes
- [ ] **Fix GitHub Actions workflow**: CLI test_list_all fails in CI because workflow doesn't start docker compose before running tests. All tests pass locally.

## Features
- [ ] **Gamification System**: Add point accumulation for completed tasks.

## Refactoring
- [ ] **Centralize Configuration**: Refactor to use config.json.

---

## Inventory of future functions

| File | Function Name | Verb | Status | Description |
|------|--------------|------|--------|-------------|
| `compute.py` | `filter_due_contexts` | `filter` | To Do | Return sorted unique Context values from due/overdue tasks |
| `api.py` | `get_due_contexts` | `get` | To Do | GET /context/ — list unique contexts from due/overdue tasks |
| `api.py` | `get_tasks_by_context` | `get` | To Do | GET /context/{context_id} — list due/overdue tasks by context |
