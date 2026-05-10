# To Do

## The Gold: `api.py` | `GET /context/` | Endpoint returning unique contexts from due/overdue tasks

## List Contexts From Due/Overdue Tasks
- [ ] **`api.py`: Add `GET /context/`** — Endpoint returning `{"contexts": [...]}` based on tasks due/overdue today.
- [ ] **public/index.html** — Add section to display contexts with links to context pages.

## List Due/Overdue Tasks by Context
- [ ] **`api.py`: Add `GET /context/{context_id}`** — Endpoint returning due/overdue tasks as JSON array filtered by context.
- [ ] **public/context.html** — Create page to display tasks within context, with links to each task.

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
| `api.py` | `get_due_contexts` | `get` | To Do | GET /context/ — list unique contexts from due/overdue tasks |
| `api.py` | `get_tasks_by_context` | `get` | To Do | GET /context/{context_id} — list due/overdue tasks by context |
