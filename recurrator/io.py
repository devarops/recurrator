import csv
from enum import Enum


class Context(Enum):
    """Valid task contexts."""

    LAPTOP = "laptop"


class Task:
    """Represents a task imported from CSV."""

    def __init__(self, id: int, description: str, context: Context):
        self.id = id
        self.description = description
        self.context = context


def import_tasks_from_csv(path):
    """Import tasks from a CSV file.

    Args:
        path: Path to the CSV file.

    Returns:
        List of Task objects with attributes from CSV rows.
    """
    with open(path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return [
            Task(
                id=int(row["id"]),
                description=row["description"],
                context=Context(row["context"]),
            )
            for row in reader
        ]
