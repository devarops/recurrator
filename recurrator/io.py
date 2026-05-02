import csv
from datetime import date
from enum import Enum

from .compute import compute_latest_date


class Context(Enum):
    """Valid task contexts."""

    LAPTOP = "laptop"


class Task:
    """Represents a task imported from CSV."""

    def __init__(
        self,
        id: int,
        description: str,
        context: Context,
        skip_count: int,
        starred: bool,
        latest_date: date | None,
    ):
        self.id = id
        self.description = description
        self.context = context
        self.skip_count = skip_count
        self.starred = starred
        self.latest_date = latest_date


def _parse_date(date_str: str) -> date | None:
    """Parse an ISO 8601 date string, returning None for 'NA'."""
    return date.fromisoformat(date_str) if date_str != "NA" else None


def _row_to_task(row: dict) -> Task:
    """Convert a CSV row dictionary to a Task object."""
    date_4 = _parse_date(row["date_4"])
    assert date_4 is not None
    skipped_date = _parse_date(row["skipped_date"])
    latest_date = compute_latest_date(date_4, skipped_date)
    return Task(
        id=int(row["id"]),
        description=row["description"],
        context=Context(row["context"]),
        skip_count=int(row["skip_count"]),
        starred=bool(int(row["starred"])),
        latest_date=latest_date,
    )


def import_tasks_from_csv(path: str) -> list[Task]:
    """Import tasks from a CSV file.

    Args:
        path: Path to the CSV file.

    Returns:
        List of Task objects with attributes from CSV rows.
    """
    with open(path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return [_row_to_task(row) for row in reader]
