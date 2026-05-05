from fastapi.testclient import TestClient

from recurrator.api import app

client = TestClient(app)


def test_get_single_task_id():
    """Verify GET /task/ returns a list of task ID objects."""
    response = client.get("/task/?csv=tests/data/test_single_task.csv")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

    expected_data = [{"id": 8}]
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_multiple_task_ids():
    """Verify GET /task/ returns a list of task ID objects when multiple tasks are present."""
    response = client.get("/task/?csv=tests/data/test_three_tasks.csv")

    expected_data = [{"id": 2}, {"id": 3}, {"id": 5}]
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
    task_id = 5
    original_task = client.get(
        "/task/{task_id}?csv=tests/data/test_three_tasks.csv".format(task_id=task_id)
    ).json()
    response = client.post(
        "/task/{task_id}/done?csv=tests/data/test_three_tasks.csv".format(task_id=task_id)
    )

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
