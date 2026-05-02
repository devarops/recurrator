import csv
from enum import Enum


class Context(Enum):
    """Valid task contexts."""

    LAPTOP = "laptop"


class Task:
    """Represents a task imported from CSV."""

    def __init__(self, id: int, description: str, context: Context, skip_count: int, starred: bool):
        self.id = id
        self.description = description
        self.context = context
        self.skip_count = skip_count
        self.starred = starred


def _row_to_task(row: dict) -> Task:
    """Convert a CSV row dictionary to a Task object."""
    return Task(
        id=int(row["id"]),
        description=row["description"],
        context=Context(row["context"]),
        skip_count=int(row["skip_count"]),
        starred=bool(int(row["starred"])),
    )


def import_tasks_from_csv(path):
    """Import tasks from a CSV file.

    Args:
        path: Path to the CSV file.

    Returns:
        List of Task objects with attributes from CSV rows.
    """
    with open(path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return [_row_to_task(row) for row in reader]
