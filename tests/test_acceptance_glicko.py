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


def test_glicko_inactivity_growth():
    """An older rating anchor projects a larger deviation at the same reference date."""
    fixture = "tests/data/acceptance_glicko_inactivity_growth.csv"
    reference_date = "2026-11-08"

    older = client.get(f"/task/1?csv={fixture}&date={reference_date}")
    newer = client.get(f"/task/2?csv={fixture}&date={reference_date}")

    assert older.status_code == 200
    assert newer.status_code == 200

    older_deviation = older.json()["rating_deviation"]
    newer_deviation = newer.json()["rating_deviation"]

    assert older_deviation > newer_deviation
    assert 45 <= older_deviation <= 500
    assert 45 <= newer_deviation <= 500
