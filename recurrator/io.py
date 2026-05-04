import csv
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum

from .compute import (
    compute_due_date,
    compute_intervals,
    compute_latest_date,
    compute_recurrence_days,
)


class Context(Enum):
    """Valid task contexts."""

    CASA = "casa"
    LAPTOP = "laptop"
    LIMPIAR = "limpiar"


@dataclass
class ComputedDates:
    """Computed date attributes for a task."""

    latest_date: date
    recurrence_days: int
    due_date: date


class Task:
    """Represents a task imported from CSV."""

    def __init__(
        self,
        id: int,
        description: str,
        context: Context,
        skip_count: int,
        starred: bool,
        computed_dates: ComputedDates,
    ):
        self.id = id
        self.description = description
        self.context = context
        self.skip_count = skip_count
        self.starred = starred
        self.latest_date = computed_dates.latest_date
        self.recurrence_days = computed_dates.recurrence_days
        self.due_date = computed_dates.due_date


def _parse_date(date_str: str) -> date | None:
    """Parse an ISO 8601 date string, returning None for 'NA'."""
    return date.fromisoformat(date_str) if date_str != "NA" else None


def _format_date(d: date | None) -> str:
    """Format a date to ISO 8601 string, or 'NA' for None."""
    return d.isoformat() if d is not None else "NA"


def _compute_dates(row: dict) -> ComputedDates:
    """Compute latest_date, recurrence_days, and due_date from CSV row.

    Returns:
        ComputedDates object with computed values
    """
    date_4 = _parse_date(row["date_4"])
    assert date_4 is not None

    skipped_date = _parse_date(row["skipped_date"])
    latest_date = compute_latest_date(date_4, skipped_date)

    dates = [_parse_date(row[f"date_{i}"]) for i in range(1, 5)]
    intervals = compute_intervals(dates)
    recurrence_days = compute_recurrence_days(intervals)

    due_date = compute_due_date(latest_date, recurrence_days)

    return ComputedDates(
        latest_date=latest_date,
        recurrence_days=recurrence_days,
        due_date=due_date,
    )


def _row_to_task(row: dict) -> Task:
    """Convert a CSV row dictionary to a Task object."""
    computed_dates = _compute_dates(row)

    return Task(
        id=int(row["id"]),
        description=row["description"],
        context=Context(row["context"]),
        skip_count=int(row["skip_count"]),
        starred=bool(int(row["starred"])),
        computed_dates=computed_dates,
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


def import_dates_from_csv(task_id: int, path: str) -> list[date | None] | None:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["id"]) == task_id:
                return [
                    _parse_date(row["date_1"]),
                    _parse_date(row["date_2"]),
                    _parse_date(row["date_3"]),
                    _parse_date(row["date_4"]),
                ]
    return None


def _format_csv_line(fieldnames: Sequence[str] | None, row: dict) -> str:
    """Format a CSV row, quoting only the description field."""
    if fieldnames is None:
        return ""
    line_parts = []
    for field in fieldnames:
        value = row[field]
        if field == "description":
            line_parts.append(f'"{value}"')
        else:
            line_parts.append(value)
    return ",".join(line_parts)


def _update_task_in_csv(task_id: int, modify_row: callable, csv_path: str) -> None:
    """Generic CSV update: read, apply modification callback, write back."""
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    for row in rows:
        modify_row(row, task_id)
    assert fieldnames is not None
    with open(csv_path, "w", newline="") as f:
        f.write(",".join(fieldnames) + "\n")
        for row in rows:
            line = _format_csv_line(fieldnames, row)
            f.write(line + "\n")


def update_task_dates_in_csv(task_id: int, dates: list[date | None], path: str) -> None:
    def modify_row(row: dict, task_id: int) -> None:
        if int(row["id"]) == task_id:
            row["date_1"] = _format_date(dates[0])
            row["date_2"] = _format_date(dates[1])
            row["date_3"] = _format_date(dates[2])
            row["date_4"] = _format_date(dates[3])

    _update_task_in_csv(task_id, modify_row, path)


def update_task_as_done(task_id: int, csv_path: str) -> None:
    update_task_skip_count(task_id, 0, csv_path)


def update_task_skip_count(task_id: int, skip_count: int, csv_path: str) -> None:
    def modify_row(row: dict, task_id: int) -> None:
        if int(row["id"]) == task_id:
            row["skip_count"] = str(skip_count)

    _update_task_in_csv(task_id, modify_row, csv_path)
