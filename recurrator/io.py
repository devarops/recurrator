import csv
from enum import Enum


class Context(Enum):
    """Valid task contexts."""

    LAPTOP = "laptop"


class Task:
    """Represents a task imported from CSV."""


def import_tasks_from_csv(path):
    """Import tasks from a CSV file.

    Args:
        path: Path to the CSV file.

    Returns:
        List of Task objects with attributes from CSV rows.
    """
    tasks = []
    with open(path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            task = Task()
            task.id = int(row["id"])
            task.description = row["description"]
            task.context = Context(row["context"])
            tasks.append(task)
    return tasks
