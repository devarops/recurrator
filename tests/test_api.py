from fastapi.testclient import TestClient

from recurrator.api import app

client = TestClient(app)


def test_get_task_ids():
    """Verify GET /tasks/ returns a list of task ID objects."""
    response = client.get("/tasks/")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

    expected_data = [{"id": 8}]
    obtained_data = response.json()
    assert obtained_data == expected_data

def test_get_task_ids_multiple():
    """Verify GET /tasks/ returns a list of task ID objects when multiple tasks are present."""
    response = client.get("/tasks/?csv=tests/data/test_two_contexts.csv")

    expected_data = [{"id": 2}, {"id": 3}, {"id": 5}]
    obtained_data = response.json()
    assert obtained_data == expected_data

def test_get_task_by_id():
    """Verify GET /tasks/{id} returns the correct task details."""
    response = client.get("/tasks/8")

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
