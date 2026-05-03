# recurrator

This application presents a minimal interface focused on completing recurring administrative tasks.
Each day, you are shown up to six tasks selected by the system as the most relevant for that day.
Completing a task requires a single click, and you may also skip any task shown.
The system adapts automatically to your behavior and schedules future occurrences without requiring configuration.
You do not see future tasks or manage scheduling rules.
A small gamification layer awards points for each completed task, and these points accumulate daily until you choose to expend them.

## Getting Started

### Start the API Server
```bash
docker-compose up
```

The API will be available at `http://localhost:8000`

### Access Tasks via Browser or cURL

List all task IDs:
```bash
curl http://localhost:8000/tasks/
```

Get a single task with all fields:
```bash
curl http://localhost:8000/tasks/8
```

Mark a task as done:
```bash
curl -X POST http://localhost:8000/tasks/8/done
```

### Using the CLI (Optional)

The CLI is a thin wrapper around the API and requires the server to be running:

```bash
recurrator list-all
recurrator show-task --id 8
recurrator mark-done --id 8
```

