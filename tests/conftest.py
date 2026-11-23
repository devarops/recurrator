import hashlib
from datetime import date
from shutil import copyfile

from fastapi.testclient import TestClient

import recurrator.io as io
from recurrator.api import app

client = TestClient(app)

# Test data constants
THREE_TASKS_CSV = "tests/data/test_three_tasks.csv"
CONTEXT_TASKS_CSV = "tests/data/test_contexts.csv"
CONTEXTS_CSV = "tests/data/contexts.csv"
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
TASK_2_ORIGINAL_SKIP_COUNT = 10
TASK_2_ORIGINAL_SKIP_DATE = date(2025, 5, 2)

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


def _read_response_schema(document, path):
    """Return the 200 response schema of one GET path from an OpenAPI document."""
    response = document["paths"][path]["get"]["responses"]["200"]
    return response["content"]["application/json"]["schema"]


def _read_task(csv_path, task_id, reference_date=None):
    """Read one task through the API, optionally at a reference date."""
    query = f"&date={reference_date}" if reference_date else ""
    return client.get(f"/api/task/{task_id}?csv={csv_path}{query}")


def _complete(csv_path, task_id):
    """Mark a task done through the API."""
    return client.post(f"/api/task/{task_id}/done?csv={csv_path}")


def _patch_description_body(csv_path, task_id, body):
    """Send a description request body through the API."""
    return client.patch(f"/api/task/{task_id}/description?csv={csv_path}", json=body)


def _patch_description(csv_path, task_id, text):
    """Send a description through the API."""
    return _patch_description_body(csv_path, task_id, {"description": text})


def _read_task_ids(csv_path):
    """Read the ids of every task through the API."""
    return client.get(f"/api/task/?csv={csv_path}")


def _read_due_task_ids(csv_path, reference_date, contexts=None, contexts_csv=None):
    """Read the ids of the tasks due on or before a reference date."""
    query = f"&contexts_csv={contexts_csv}" if contexts_csv else ""
    query += "".join(f"&context={context}" for context in contexts or [])
    return client.get(f"/api/task/due/{reference_date}?csv={csv_path}{query}")


def _read_context_task_ids(csv_path, context, reference_date):
    """Read the task ids selected for one context at a reference date."""
    return _read_due_task_ids(csv_path, reference_date, [context], CONTEXTS_CSV)


def _read_due_context_ids(csv_path, reference_date):
    """Read the contexts with a due task at a reference date."""
    return client.get(
        f"/api/context/due/{reference_date}?csv={csv_path}&contexts_csv={CONTEXTS_CSV}"
    )


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


def _assert_error_response(response, status_code: int) -> None:
    """Assert a refused request carries the status and the shared error envelope."""
    assert response.status_code == status_code
    assert "error" in response.json()


def _restore_completion_fields(task_id: int, skip_count: int, dates: list, csv_path: str) -> None:
    """Restore the fields a completion changes on the completed task."""
    io.update_task_skip_count(task_id, skip_count, csv_path)
    io.update_task_dates(task_id, dates, csv_path)
