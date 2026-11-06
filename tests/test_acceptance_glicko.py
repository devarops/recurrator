from shutil import copyfile

from fastapi.testclient import TestClient
from recurrator.api import app

client = TestClient(app)

FIXTURE = "tests/data/acceptance_glicko_integer_contract.csv"


def test_glicko_integer_contract(tmp_path):
    """Rating and rating deviation are integers when a task is read or completed."""
    response = client.get(f"/task/8?csv={FIXTURE}")
    assert response.status_code == 200

    task = response.json()
    assert isinstance(task["rating"], int)
    assert isinstance(task["rating_deviation"], int)

    completion_csv = tmp_path / "task.csv"
    copyfile(FIXTURE, completion_csv)

    response = client.post(f"/task/8/done?csv={completion_csv}")
    assert response.status_code == 200

    completed = response.json()
    assert isinstance(completed["rating"], int)
    assert isinstance(completed["rating_deviation"], int)
