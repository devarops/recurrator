# recurrator

Recurrator — recurring tasks that know when to come back.

Recurrator helps you manage recurring household and personal tasks.
The more often you complete a task, the more frequently it comes back.
If you take longer between completions, it shows up less often.
Recurrator learns your personal rhythm — no calendars, no complicated rules.

---

## How it works

Open your browser to see a list of contexts (areas of your life).
Click a context to see the tasks that are due or overdue in that area.
Click a task to see its details and mark it as done.

| Page | Status |
|------|--------|
| **Index** — lists your contexts | ✅ Ready |
| **Context** — lists tasks in one context | ✅ Ready |
| **Task** — view and complete a task | ✅ Ready |

Navigation is point-and-click. You never type task IDs or file paths.

---

## Before you start: your task file

Recurrator stores your tasks in a CSV file.
The default location is:

```
~/.config/recurrator/tasks.csv
```

You need to create this file before using Recurrator.
You can point to a different file later — but the default path is what the
application looks for unless you tell it otherwise.

---

## Run Recurrator

### With Docker (recommended)

```bash
docker compose up
```

This starts the API server at `http://localhost:8000`.

### Without Docker

```bash
make install
uvicorn recurrator.api:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000/task.html?id=1` in your browser to see a task.

---

## Adaptive recurrence explained

Every task has a natural rhythm that comes from how you do it.

- **Do a task often** → it comes back sooner
- **Take longer between completions** → it waits longer before reappearing

Recurrator watches your last few completions and adjusts automatically.
You never set a schedule — the schedule sets itself based on your behavior.

---

## Coming soon

- **Skip button** — postpone a task for the day
- **Starred tasks** — pin important tasks so they can't be skipped
- **Create and edit tasks** from the browser
- **Dashboard** — see your progress over time
