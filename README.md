# recurrator

Recurring tasks that know when to come back.

## What it does

Household and personal chores do not follow a fixed calendar. Recurrator learns
how often you actually complete each task and adjusts when it appears again.
Tasks you do often return sooner; tasks you do rarely wait longer. There is
nothing to schedule and no recurrence rule to configure.

## How to use it

1. Open the start page to see the areas of your life that have work waiting.
2. Choose an area to see the tasks that are due there.
3. Pick a task to view its details.
4. Select **Mark as Done** when you finish it.

The task stops appearing in the due list until its next due date. Completed work
also updates the task's rhythm, so the schedule keeps adapting.

For terminal users, `recurrator list-all-tasks --csv <file>` prints the task IDs
from the same task file while the service is running.

## Before you start

Recurrator keeps your tasks in a file at:

```
~/.config/recurrator/tasks.csv
```

The file must exist before you start. It records each task, its area, and the
dates it was completed. Keep it backed up; it is your task history.

## Run the project

### With Docker (recommended)

```bash
docker compose up
```

This starts the service at `http://localhost:8000`. Then open
`public/index.html` in your browser.

### Without Docker

```bash
make install
uvicorn recurrator.api:app --host 0.0.0.0 --port 8000 --reload
```

Then open `public/index.html` in your browser.
