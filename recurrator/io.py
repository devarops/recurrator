import csv
from collections.abc import Callable, Sequence
from datetime import date

from .compute import (
    compute_due_date,
    compute_intervals,
    compute_latest_date,
    compute_recurrence_days,
    filter_four_dates,
)
from .models import Context, Dates, Task, SKIP_COUNT_RESET


def _parse_date(date_str: str) -> date | None:
    """Parse an ISO 8601 date string, returning None for 'NA'."""
    return date.fromisoformat(date_str) if date_str != "NA" else None


def _format_date(d: date | None) -> str:
    """Format a date to ISO 8601 string, or 'NA' for None."""
    return d.isoformat() if d is not None else "NA"


def _parse_row_dates(row: dict) -> list[date | None]:
    """Extract and parse the four date fields from a CSV row."""
    return [
        _parse_date(row["date_1"]),
        _parse_date(row["date_2"]),
        _parse_date(row["date_3"]),
        _parse_date(row["date_4"]),
    ]


def _compute_dates(row: dict) -> Dates:
    """Compute latest_date, recurrence_days, and due_date from CSV row.

    Returns:
        Dates object with computed values
    """
    date_4 = _parse_date(row["date_4"])
    assert date_4 is not None

    skipped_date = _parse_date(row["skipped_date"])
    latest_date = compute_latest_date(date_4, skipped_date)

    dates = _parse_row_dates(row)
    intervals = compute_intervals(dates)
    recurrence_days = compute_recurrence_days(intervals)

    due_date = compute_due_date(latest_date, recurrence_days)

    return Dates(
        latest_date=latest_date,
        recurrence_days=recurrence_days,
        due_date=due_date,
    )


def _row_to_task(row: dict) -> Task:
    """Convert a CSV row dictionary to a Task object."""
    dates = _compute_dates(row)

    return Task(
        id=int(row["id"]),
        description=row["description"],
        context=Context(row["context"]),
        skip_count=int(row["skip_count"]),
        starred=bool(int(row["starred"])),
        dates=dates,
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


def import_dates_from_csv(task_id: int, path: str) -> list[date | None]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["id"]) == task_id:
                return _parse_row_dates(row)
    raise ValueError(f"Task {task_id} not found in {path}")


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


def _update_task_in_csv(
    task_id: int, modify_row: Callable[[dict, int], None], csv_path: str
) -> None:
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


def update_task_dates(task_id: int, dates: list[date | None], path: str) -> None:
    def modify_row(row: dict, task_id: int) -> None:
        if int(row["id"]) == task_id:
            row["date_1"] = _format_date(dates[0])
            row["date_2"] = _format_date(dates[1])
            row["date_3"] = _format_date(dates[2])
            row["date_4"] = _format_date(dates[3])

    _update_task_in_csv(task_id, modify_row, path)


def update_task_as_done(task_id: int, completion_date: date, csv_path: str) -> None:
    current_dates = import_dates_from_csv(task_id, csv_path)
    rotated_dates = filter_four_dates(current_dates, completion_date)
    update_task_dates(task_id, rotated_dates, csv_path)
    update_task_skip_count(task_id, SKIP_COUNT_RESET, csv_path)


def update_task_skip_count(task_id: int, skip_count: int, csv_path: str) -> None:
    def modify_row(row: dict, task_id: int) -> None:
        if int(row["id"]) == task_id:
            row["skip_count"] = str(skip_count)

    _update_task_in_csv(task_id, modify_row, csv_path)


def get_task_by_id(task_id: int, csv_path: str) -> Task:
    """Get a task by ID from a CSV file.

    Args:
        task_id: The task ID to find
        csv_path: Path to the CSV file

    Returns:
        Task object matching the ID

    Raises:
        ValueError: If task not found
    """
    tasks = import_tasks_from_csv(csv_path)
    for task in tasks:
        if task.id == task_id:
            return task
    raise ValueError(f"Task {task_id} not found in {csv_path}")
