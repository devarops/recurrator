# recurrator

Recurring tasks that know when to come back.

## What it does

Household and personal chores do not follow a fixed calendar. Recurrator learns
how often you actually complete each task and adjusts when it appears again.
Tasks you do often return sooner; tasks you do rarely wait longer. There is
nothing to schedule and no recurrence rule to configure.

This repository is the API product. The browser frontend and the terminal client
are separate repositories; both consume this API over HTTP and never read the
task file directly.

## What it exposes

Every entry point lives under `/api`:

- `GET /api/task/` and `GET /api/task/{id}` — task identities and task detail
- `GET /api/context/` and `GET /api/context/{id}` — the areas of your life
- `PATCH /api/task/{id}/description` and `POST /api/task/{id}/done` — the writes
- `GET /api/openapi.json`, `GET /api/docs`, and `GET /api/redoc` — the published
  contract, generated from the code

`DOCS.md` is the reference for every entry point and the exact response fields.

## The task file

Recurrator keeps your tasks in a file at:

```
~/.config/recurrator/tasks.csv
```

The file must exist before you start. It records each task, its area, and the
dates it was completed. Keep it backed up; it is your task history.

## Run the project

```bash
docker compose up api
```

This starts the API at `http://localhost/`. Then open
`http://localhost/api/docs` for the interactive contract, or call an entry point
directly:

```bash
curl 'http://localhost/api/task/?csv=/root/.config/recurrator/tasks.csv'
```
