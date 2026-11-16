import hashlib
from datetime import date
from shutil import copyfile

from fastapi.testclient import TestClient

import recurrator.io as io
from recurrator.api import app

client = TestClient(app)

# Test data constants
THREE_TASKS_CSV = "tests/data/test_three_tasks.csv"
CONTEXTS_CSV = "tests/data/test_contexts.csv"
SINGLE_TASK_CSV = "tests/data/test_single_task.csv"
GLICKO_CONTRACT_CSV = "tests/data/acceptance_glicko_integer_contract.csv"
GLICKO_INACTIVITY_CSV = "tests/data/acceptance_glicko_inactivity_growth.csv"
GLICKO_SOLO_CSV = "tests/data/acceptance_glicko_solo_completion.csv"
GLICKO_DEFAULT_DATE_CSV = "tests/data/acceptance_glicko_default_date_projection.csv"
TWO_RATINGS_CSV = "tests/data/test_two_ratings.csv"
TWO_RATINGS_FROZEN_CSV = "tests/data/test_two_ratings_frozen.csv"
UNIVERSE_MEDIANS_EVEN_CSV = "tests/data/test_universe_medians_even.csv"
EIGHT_TASKS_CSV = "tests/data/test_eight_tasks.csv"

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


def _read_task(csv_path, task_id):
    """Read one task through the API."""
    return client.get(f"/api/task/{task_id}?csv={csv_path}")


def _read_task_on(csv_path, task_id, reference_date):
    """Read one task through the API at a reference date."""
    return client.get(f"/api/task/{task_id}?csv={csv_path}&date={reference_date}")


def _complete(csv_path, task_id):
    """Mark a task done through the API."""
    return client.post(f"/api/task/{task_id}/done?csv={csv_path}")


def _read_context_task_ids(csv_path, context, reference_date):
    """Read the prioritized task ids for one context at a reference date."""
    return client.get(f"/api/context/{context}?csv={csv_path}&date={reference_date}")


def _read_task_ids(csv_path):
    """Read the ids of every task through the API."""
    return client.get(f"/api/task/?csv={csv_path}")


def _copy_fixture(fixture, tmp_path):
    """Copy a task fixture into the test's temporary directory."""
    csv_path = tmp_path / "tasks.csv"
    copyfile(fixture, csv_path)
    return csv_path


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

    io.update_task_as_done(task_id, completion_date, csv_path)
    assert io.get_task_by_id(task_id, csv_path).skip_count == 0

    assert io.import_dates_from_csv(task_id, csv_path) == expected_dates

    # Undo changes to CSV file for other tests
    io.update_task_skip_count(task_id, original_skip_count, csv_path)
    io.update_task_dates(task_id, original_dates, csv_path)
