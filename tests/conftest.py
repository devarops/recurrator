import hashlib
from datetime import date
import recurrator.io as io

# Test data constants
TASK_2_ORIGINAL_DATES = [None, None, date(2024, 1, 8), date(2024, 12, 7)]
TASK_2_UPDATED_DATES = [None, None, date(2025, 2, 1), date(2025, 11, 2)]
TASK_2_COMPLETION_DATE = date(2025, 2, 28)
TASK_2_EXPECTED_AFTER_COMPLETION = [None, date(2024, 1, 8), date(2024, 12, 7), date(2025, 2, 28)]

TASK_5_ORIGINAL_DATES = [
    date(2024, 8, 26),
    date(2024, 10, 12),
    date(2025, 1, 31),
    date(2025, 3, 14),
]
TASK_5_COMPLETION_DATE = date(2026, 5, 4)
TASK_5_EXPECTED_AFTER_COMPLETION = [
    date(2024, 10, 12),
    date(2025, 1, 31),
    date(2025, 3, 14),
    date(2026, 5, 4),
]


def _get_file_checksum(path: str) -> str:
    """Get MD5 checksum of a file."""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _assert_file_unchanged(path: str, original_checksum: str) -> None:
    """Verify file has not changed by comparing checksums."""
    final_checksum = _get_file_checksum(path)
    assert final_checksum == original_checksum, "CSV was modified after undo"


def _verify_task_as_done(
    task_id: int,
    csv_path: str,
    completion_date: date,
    expected_dates: list,
    original_dates: list,
) -> None:
    """Verify and undo task completion scenario.

    Args:
        task_id: ID of the task to test
        csv_path: Path to CSV file
        completion_date: Date the task was marked as done
        expected_dates: Expected dates after completion
        original_dates: Original dates to restore after test
    """
    original_task = io.get_task_by_id(task_id, csv_path)
    original_skip_count = original_task.skip_count

    expected_skip_count = 0
    io.update_task_as_done(task_id, completion_date, csv_path)
    updated_task = io.get_task_by_id(task_id, csv_path)
    obtained_skip_count = updated_task.skip_count
    assert obtained_skip_count == expected_skip_count

    obtained_dates = io.import_dates_from_csv(task_id, csv_path)
    assert obtained_dates == expected_dates

    # Undo changes to CSV file for other tests
    io.update_task_skip_count(task_id, original_skip_count, csv_path)
    io.update_task_dates(task_id, original_dates, csv_path)
