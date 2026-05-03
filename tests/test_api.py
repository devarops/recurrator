from fastapi.testclient import TestClient
import pytest

# This will fail because recurrator.api doesn't exist yet
from recurrator.api import app

client = TestClient(app)


def test_get_tasks_ids():
    """Verify GET /tasks/ returns a list of task ID objects."""
    response = client.get("/tasks/")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code
