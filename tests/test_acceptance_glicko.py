import csv
from datetime import date
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


def test_glicko_four_tasks(tmp_path):
    """The completed task loses rating, its three due peers change, and others keep theirs."""
    csv_path = tmp_path / "tasks.csv"
    copyfile("tests/data/acceptance_glicko_four_tasks.csv", csv_path)

    before = {
        task_id: client.get(f"/task/{task_id}?csv={csv_path}").json()["rating"]
        for task_id in range(1, 7)
    }

    response = client.post(f"/task/1/done?csv={csv_path}")
    assert response.status_code == 200

    after = {
        task_id: client.get(f"/task/{task_id}?csv={csv_path}").json()["rating"]
        for task_id in range(1, 7)
    }

    assert after[1] < before[1]
    for task_id in (2, 3, 4):
        assert after[task_id] != before[task_id]
    for task_id in (5, 6):
        assert after[task_id] == before[task_id]


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


def test_glicko_simultaneous_update(tmp_path):
    """Two different ratings match a simultaneous update, not a sequential one."""
    csv_path = tmp_path / "tasks.csv"
    copyfile("tests/data/acceptance_glicko_simultaneous_update.csv", csv_path)

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    assert fieldnames is not None
    for row in rows:
        row["rating_date"] = date.today().isoformat()
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    response = client.post(f"/task/1/done?csv={csv_path}")
    assert response.status_code == 200

    completed = response.json()
    opponent = client.get(f"/task/2?csv={csv_path}").json()

    assert (completed["rating"], completed["rating_deviation"]) == (1367, 292)
    assert (opponent["rating"], opponent["rating_deviation"]) == (1733, 292)
