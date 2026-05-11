from fastapi.testclient import TestClient
from recurrator.api import app
import recurrator.io as io
from conftest import (
    _get_file_checksum,
    _assert_file_unchanged,
    TASK_5_ORIGINAL_DATES,
)

client = TestClient(app)


def test_get_single_task_id():
    """Verify GET /task/ returns a list of raw task IDs."""
    response = client.get("/task/?csv=tests/data/test_single_task.csv")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

    expected_data = [8]
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_multiple_task_ids():
    """Verify GET /task/ returns a list of raw task IDs when multiple tasks are present."""
    response = client.get("/task/?csv=tests/data/test_three_tasks.csv")

    expected_data = [2, 3, 5]
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_task_by_id_default_csv():
    """Verify GET /task/{id} returns the correct task details."""
    response = client.get("/task/8?csv=tests/data/test_single_task.csv")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

    expected_data = {
        "id": 8,
        "description": "TypeLit.io",
        "context": "laptop",
        "skip_count": 1,
        "starred": False,
        "latest_date": "2025-11-17",
        "recurrence_days": 14,
        "due_date": "2025-12-01",
    }
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_task_by_id_alternative_csv():

    response = client.get("/task/3?csv=tests/data/test_three_tasks.csv")

    expected_data = {
        "id": 3,
        "description": "Lavar trapos",
        "context": "limpiar",
        "skip_count": 0,
        "starred": False,
        "latest_date": "2026-03-07",
        "recurrence_days": 33,
        "due_date": "2026-04-09",
    }

    obtained_data = response.json()
    assert obtained_data == expected_data


def test_set_task_as_done():
    """Verify POST /task/{id}/done marks the task as done and updates the due date correctly."""

    csv_path = "tests/data/test_three_tasks.csv"
    original_checksum = _get_file_checksum(csv_path)

    task_id = 5
    original_task = client.get(f"/task/{task_id}?csv={csv_path}").json()
    response = client.post(f"/task/{task_id}/done?csv={csv_path}")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

    expected_skip_count = 0
    obtained_task = response.json()
    obtained_skip_count = obtained_task["skip_count"]
    assert obtained_skip_count == expected_skip_count

    original_skip_count = original_task["skip_count"]
    assert obtained_skip_count != original_skip_count

    original_due_date = original_task["due_date"]
    obtained_due_date = obtained_task["due_date"]
    assert obtained_due_date != original_due_date

    # Undo changes to CSV file for other tests
    io.update_task_skip_count(task_id, original_skip_count, csv_path)
    io.update_task_dates(task_id, TASK_5_ORIGINAL_DATES, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)


def test_get_due_contexts():
    """Verify GET /context/ returns the correct list of contexts from due tasks."""

    csv_path = "tests/data/test_contexts.csv"
    reference_date = "2026-05-01"
    response = client.get(f"/context/?csv={csv_path}&date={reference_date}")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

    expected_contexts = ["casa", "laptop", "limpiar"]
    obtained_contexts = response.json()
    assert obtained_contexts == expected_contexts


def test_get_tasks_by_context():
    """Verify GET /context/{context_id} returns task IDs due in that context."""

    csv_path = "tests/data/test_contexts.csv"
    reference_date = "2026-05-02"
    response = client.get(f"/context/casa?csv={csv_path}&date={reference_date}")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code
