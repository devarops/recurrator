import hashlib
from contextlib import contextmanager
from datetime import date
from shutil import copyfile

from fastapi.testclient import TestClient

import recurrator.io as io
from recurrator.api import app

client = TestClient(app)

# Test data constants
THREE_TASKS_CSV = "tests/data/test_three_tasks.csv"
CONTEXT_TASKS_CSV = "tests/data/test_contexts.csv"
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


def _read_openapi_document():
    """Read the published OpenAPI document, asserting that the read succeeds."""
    response = client.get("/api/openapi.json")

    assert response.status_code == 200

    return response.json()


def _read_responses(document, path, method="get"):
    """Return the responses of one path and method from an OpenAPI document."""
    return document["paths"][path][method]["responses"]


def _read_response_schema(document, path, method="get"):
    """Return the 200 response schema of one path and method from an OpenAPI document."""
    response = _read_responses(document, path, method)["200"]
    return response["content"]["application/json"]["schema"]


def _read_task(csv_path, task_id, reference_date=None):
    """Read one task through the API, optionally at a reference date."""
    query = f"&date={reference_date}" if reference_date else ""
    return client.get(f"/api/task/{task_id}?csv={csv_path}{query}")


def _read_task_body(csv_path, task_id, reference_date=None):
    """Read one task through the API, asserting that the read succeeds."""
    response = _read_task(csv_path, task_id, reference_date)

    assert response.status_code == 200

    return response.json()


def _complete(csv_path, task_id):
    """Mark a task done through the API."""
    return client.post(f"/api/task/{task_id}/done?csv={csv_path}")


def _patch_description_body(csv_path, task_id, body):
    """Send a description request body through the API."""
    return client.patch(f"/api/task/{task_id}/description?csv={csv_path}", json=body)


def _patch_description(csv_path, task_id, text):
    """Send a description through the API."""
    return _patch_description_body(csv_path, task_id, {"description": text})


def _patch_starred(csv_path, task_id, starred):
    """Send a starred flag through the API."""
    return client.patch(f"/api/task/{task_id}/starred?csv={csv_path}", json={"starred": starred})


def _read_task_ids(csv_path, contexts=None):
    """Read the ids of every task, optionally narrowed to some contexts."""
    query = "".join(f"&context={context}" for context in contexts or [])
    return client.get(f"/api/task/?csv={csv_path}{query}")


def _read_due_task_ids(csv_path, reference_date, contexts=None):
    """Read the ids of the tasks due on or before a reference date."""
    query = "".join(f"&context={context}" for context in contexts or [])
    return client.get(f"/api/task/due/{reference_date}?csv={csv_path}{query}")


def _read_context_task_ids(csv_path, context, reference_date):
    """Read the task ids selected for one context at a reference date."""
    return _read_due_task_ids(csv_path, reference_date, [context])


def _read_due_context_ids(csv_path, reference_date):
    """Read the contexts with a due task at a reference date."""
    return client.get(f"/api/context/due/{reference_date}?csv={csv_path}")


def _assert_redirect_to_trailing_slash(url, target_path):
    """Assert a slashless read redirects to its trailing-slash form without a body."""
    response = client.get(url, follow_redirects=False)

    assert response.status_code == 307
    assert target_path in response.headers["location"]
    assert response.content == b""


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


def _restore_rating_fields(csv_path: str, tasks: list) -> None:
    """Restore every task's rating, deviation, and anchor."""
    for task in tasks:
        assert task.rating_date is not None
        io.update_task_rating_fields(
            task.id, task.rating, task.rating_deviation, task.rating_date, csv_path
        )


@contextmanager
def _borrowed_tasks_file(csv_path: str, task_id: int, original_dates: list):
    """Restore a shared task file after a test mutates it, then verify it is unchanged."""
    original_checksum = _get_file_checksum(csv_path)
    original_tasks = io.import_tasks_from_csv(csv_path)
    original_skip_count = io.get_task_by_id(task_id, csv_path).skip_count

    try:
        yield
    finally:
        _restore_completion_fields(task_id, original_skip_count, original_dates, csv_path)
        _restore_rating_fields(csv_path, original_tasks)

    _assert_file_unchanged(csv_path, original_checksum)
