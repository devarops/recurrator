# To Do

## The Gold: `public/context.html` | Context tasks page | Display due tasks within a context

## List Contexts From Due/Overdue Tasks
- [x] **`api.py`: Add `GET /context/`** — Endpoint returning contexts from due/overdue tasks.
- [x] **public/index.html** — Section displaying contexts with links to context pages.

## List Due/Overdue Tasks by Context
- [x] **`api.py`: Add `GET /context/{context_id}`** — Endpoint returning due/overdue tasks as JSON array filtered by context.
- [ ] **public/context.html** — Create page to display tasks within context, with links to each task.

## Features
- [ ] **Gamification System**: Add point accumulation for completed tasks.

## Refactoring
- [ ] **Centralize Configuration**: Refactor to use config.json.

---

## Inventory of future functions

| File | Function Name | Verb | Status | Description |
|------|--------------|------|--------|-------------|
| `api.py` | `get_due_contexts` | `get` | Done | GET /context/ — list unique contexts from due/overdue tasks |
| `api.py` | `get_tasks_by_context` | `get` | Done | GET /context/{context_id} — list due/overdue tasks by context |
