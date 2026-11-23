import csv
import json
import os
from collections.abc import Iterable, Sequence
from datetime import date

from .compute import (
    compute_coins,
    compute_due_date,
    compute_intervals,
    compute_latest_date,
    compute_recurrence_days,
    compute_rolling_dates,
)
from .models import (
    Context,
    Dates,
    Task,
    GLICKO_RATING_DEFAULT,
    GLICKO_RATING_DEVIATION_DEFAULT,
    N_DATES,
    SKIP_COUNT_RESET,
)

DATE_COLUMNS = tuple(f"date_{index}" for index in range(1, N_DATES + 1))
MISSING_DATE = "NA"


def _parse_date(date_str: str) -> date | None:
    """Parse an ISO 8601 date string, returning None for the missing-date sentinel."""
    return date.fromisoformat(date_str) if date_str != MISSING_DATE else None


def _format_date(date_value: date | None) -> str:
    """Format a date to ISO 8601 string, or the missing-date sentinel for None."""
    return date_value.isoformat() if date_value is not None else MISSING_DATE


def _read_csv_rows(csv_path: str) -> tuple[list[dict], Sequence[str] | None]:
    """Read the task file as rows plus the header that names their columns."""
    with open(csv_path, newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        return rows, reader.fieldnames


def _parse_row_dates(row: dict) -> list[date | None]:
    """Extract and parse the four date fields from a CSV row."""
    return [_parse_date(row[column]) for column in DATE_COLUMNS]


def _row_to_dates(row: dict) -> Dates:
    """Convert a CSV row to its computed Dates object."""
    dates = _parse_row_dates(row)
    latest_done_date = dates[N_DATES - 1]
    assert latest_done_date is not None

    skip_date = _parse_date(row["skip_date"])
    latest_date = compute_latest_date(latest_done_date, skip_date)

    intervals = compute_intervals(dates)
    recurrence_days = compute_recurrence_days(intervals)

    due_date = compute_due_date(latest_date, recurrence_days)

    return Dates(
        latest_done_date=latest_done_date,
        latest_date=latest_date,
        recurrence_days=recurrence_days,
        due_date=due_date,
    )


def _parse_json_id_array(cell: str) -> list[str]:
    """Parse a JSON string array cell into sorted, unique ids."""
    return sorted(set(json.loads(cell)))


def _row_to_task(row: dict) -> Task:
    """Convert a CSV row dictionary to a Task object."""
    dates = _row_to_dates(row)
    starred = bool(int(row["starred"]))

    return Task(
        id=int(row["id"]),
        description=row["description"],
        contexts=_parse_json_id_array(row["contexts"]),
        skip_count=int(row["skip_count"]),
        starred=starred,
        dates=dates,
        coins=compute_coins(dates.recurrence_days, starred),
        rating=int(row.get("rating", GLICKO_RATING_DEFAULT)),
        rating_deviation=int(row.get("rating_deviation", GLICKO_RATING_DEVIATION_DEFAULT)),
        rating_date=_parse_date(row["rating_date"]) if "rating_date" in row else None,
    )


def import_tasks_from_csv(csv_path: str) -> list[Task]:
    """Import tasks from a CSV file.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        List of Task objects with attributes from CSV rows.
    """
    rows, _ = _read_csv_rows(csv_path)
    return [_row_to_task(row) for row in rows]


def _reject_empty_field(row: dict, field: str) -> None:
    """Reject a context row whose field is empty or blank."""
    value = row.get(field)
    if not value or not value.strip():
        raise ValueError(f"Context {field.replace('_', ' ')} must not be empty")


def _reject_invalid_context_id(row: dict) -> None:
    """Reject a context id that is empty, reserved, or spans path segments."""
    _reject_empty_field(row, "id")
    if row["id"] == "due":
        raise ValueError("Context id due is reserved")
    if "/" in row["id"]:
        raise ValueError("Context id must be a single path segment")


def _parse_context_scopes(row: dict) -> list[str]:
    """Parse a context row's scopes array into sorted, unique ids, rejecting an empty one."""
    scopes = _parse_json_id_array(row["scopes"])
    if scopes == []:
        raise ValueError("Context scopes must not be empty")
    return scopes


def _reject_invalid_context_fields(row: dict) -> None:
    """Reject a context row with an invalid id or an empty required field."""
    _reject_invalid_context_id(row)
    _reject_empty_field(row, "display_name")
    _reject_empty_field(row, "description")
    _reject_empty_field(row, "scopes")


def _reject_duplicate_context_ids(rows: list[dict]) -> None:
    """Reject duplicate context ids across the given rows."""
    ids = {row["id"] for row in rows}
    if len(ids) != len(rows):
        raise ValueError("Context ids must be unique")


def _row_to_context(row: dict) -> Context:
    """Validate a context row and convert it to a Context object."""
    _reject_invalid_context_fields(row)
    return Context(
        id=row["id"],
        display_name=row["display_name"],
        description=row["description"],
        scopes=_parse_context_scopes(row),
    )


def import_contexts_from_csv(csv_path: str) -> list[Context]:
    """Import every stored context from the given context file."""
    rows, _ = _read_csv_rows(csv_path)
    contexts = [_row_to_context(row) for row in rows]
    _reject_duplicate_context_ids(rows)
    return contexts


def _is_task_row(row: dict, task_id: int) -> bool:
    """Return whether the row's id column names the task."""
    return int(row["id"]) == task_id


def _find_task_row(rows: Iterable[dict], task_id: int, csv_path: str) -> dict:
    """Return the CSV row whose id column matches, or raise ValueError."""
    for row in rows:
        if _is_task_row(row, task_id):
            return row
    raise ValueError(f"Task {task_id} not found in {csv_path}")


def import_dates_from_csv(task_id: int, csv_path: str) -> list[date | None]:
    """Import the raw date fields for a given task from a CSV file.

    Args:
        task_id: The task ID to look up.
        csv_path: Path to the CSV file.

    Returns:
        A list with one value per date column (None for "NA" entries).

    Raises:
        ValueError: If task_id is not found in the CSV.
    """
    rows, _ = _read_csv_rows(csv_path)
    return _parse_row_dates(_find_task_row(rows, task_id, csv_path))


def _format_csv_field(field: str, value: str) -> str:
    """Quote a CSV field when its name or its content requires it."""
    needs_quotes = field in ("description", "contexts") or any(
        character in value for character in ',"\n'
    )
    if needs_quotes:
        return '"' + value.replace('"', '""') + '"'
    return value


def _format_csv_line(fieldnames: Sequence[str], row: dict) -> str:
    """Format a CSV row, quoting the fields that need it."""
    return ",".join(_format_csv_field(field, row[field]) for field in fieldnames)


def _set_csv_fields(task_id: int, values: dict[str, str], csv_path: str) -> None:
    """Set several CSV fields of the matching task in a single atomic write."""
    rows, fieldnames = _read_csv_rows(csv_path)
    for row in rows:
        if _is_task_row(row, task_id):
            row.update(values)
    assert fieldnames is not None

    temporary_path = f"{csv_path}.tmp"
    try:
        with open(temporary_path, "w", newline="") as temporary_file:
            temporary_file.write(",".join(fieldnames) + "\n")
            for row in rows:
                temporary_file.write(_format_csv_line(fieldnames, row) + "\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, csv_path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def _format_row_dates(dates: list[date | None]) -> dict[str, str]:
    """Pair each date column with its formatted value."""
    return {column: _format_date(dates[index]) for index, column in enumerate(DATE_COLUMNS)}


def update_task_dates(task_id: int, dates: list[date | None], csv_path: str) -> None:
    _set_csv_fields(task_id, _format_row_dates(dates), csv_path)


def update_task_description(task_id: int, description: str, csv_path: str) -> None:
    _set_csv_fields(task_id, {"description": description}, csv_path)


def update_task_skip_count(task_id: int, skip_count: int, csv_path: str) -> None:
    _set_csv_fields(task_id, {"skip_count": str(skip_count)}, csv_path)


def update_task_skip_date(task_id: int, skip_date: date | None, csv_path: str) -> None:
    _set_csv_fields(task_id, {"skip_date": _format_date(skip_date)}, csv_path)


def update_task_rating_date(task_id: int, rating_date: date, csv_path: str) -> None:
    _set_csv_fields(task_id, {"rating_date": _format_date(rating_date)}, csv_path)


def update_task_rating_fields(
    task_id: int,
    rating: int,
    rating_deviation: int,
    rating_date: date,
    csv_path: str,
) -> None:
    """Set the task's rating, deviation, and anchor in a single write."""
    _set_csv_fields(
        task_id,
        {
            "rating": str(rating),
            "rating_deviation": str(rating_deviation),
            "rating_date": _format_date(rating_date),
        },
        csv_path,
    )


def update_task_as_skipped(task_id: int, skip_date: date, csv_path: str) -> None:
    current_task = get_task_by_id(task_id, csv_path)
    _set_csv_fields(
        task_id,
        {
            "skip_count": str(current_task.skip_count + 1),
            "skip_date": _format_date(skip_date),
        },
        csv_path,
    )


def update_task_as_done(task_id: int, completion_date: date, csv_path: str) -> None:
    current_dates = import_dates_from_csv(task_id, csv_path)
    rotated_dates = compute_rolling_dates(current_dates, completion_date)
    updated_fields = _format_row_dates(rotated_dates)
    updated_fields["skip_count"] = str(SKIP_COUNT_RESET)
    _set_csv_fields(task_id, updated_fields, csv_path)


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
    rows, _ = _read_csv_rows(csv_path)
    return _row_to_task(_find_task_row(rows, task_id, csv_path))
