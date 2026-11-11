import csv
from datetime import date

from fastapi.testclient import TestClient
from recurrator.api import app
from conftest import _copy_fixture

client = TestClient(app)

FIXTURE = "tests/data/acceptance_glicko_integer_contract.csv"


def _ratings(csv_path, task_ids):
    """Return each task's rating from the fixture."""
    return {
        task_id: client.get(f"/api/task/{task_id}?csv={csv_path}").json()["rating"]
        for task_id in task_ids
    }


def test_glicko_integer_contract(tmp_path):
    """Rating and rating deviation are integers when a task is read or completed."""
    response = client.get(f"/api/task/8?csv={FIXTURE}")
    assert response.status_code == 200

    task = response.json()
    assert isinstance(task["rating"], int)
    assert isinstance(task["rating_deviation"], int)

    completion_csv = _copy_fixture(FIXTURE, tmp_path)

    response = client.post(f"/api/task/8/done?csv={completion_csv}")
    assert response.status_code == 200

    completed = response.json()
    assert isinstance(completed["rating"], int)
    assert isinstance(completed["rating_deviation"], int)


def test_glicko_four_tasks(tmp_path):
    """The completed task loses rating, its three due peers change, and others keep theirs."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_four_tasks.csv", tmp_path)

    before = _ratings(csv_path, range(1, 7))

    response = client.post(f"/api/task/1/done?csv={csv_path}")
    assert response.status_code == 200

    after = _ratings(csv_path, range(1, 7))

    assert after[1] < before[1]
    for task_id in (2, 3, 4):
        assert after[task_id] != before[task_id]
    for task_id in (5, 6):
        assert after[task_id] == before[task_id]


def test_glicko_early_completion(tmp_path):
    """A not-yet-due completion joins the four due tasks and all five ratings change."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_early_completion.csv", tmp_path)

    before = _ratings(csv_path, range(1, 6))

    response = client.post(f"/api/task/5/done?csv={csv_path}")
    assert response.status_code == 200

    after = _ratings(csv_path, range(1, 6))

    assert after[5] < before[5]
    for task_id in range(1, 5):
        assert after[task_id] != before[task_id]


def test_glicko_inactivity_growth():
    """An older rating anchor projects a larger deviation at the same reference date."""
    fixture = "tests/data/acceptance_glicko_inactivity_growth.csv"
    reference_date = "2026-11-08"

    older = client.get(f"/api/task/1?csv={fixture}&date={reference_date}")
    newer = client.get(f"/api/task/2?csv={fixture}&date={reference_date}")

    assert older.status_code == 200
    assert newer.status_code == 200

    older_deviation = older.json()["rating_deviation"]
    newer_deviation = newer.json()["rating_deviation"]

    assert older_deviation > newer_deviation
    assert 45 <= older_deviation <= 500
    assert 45 <= newer_deviation <= 500


def test_glicko_simultaneous_update(tmp_path):
    """Two different ratings match a simultaneous update, not a sequential one."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_simultaneous_update.csv", tmp_path)

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

    response = client.post(f"/api/task/1/done?csv={csv_path}")
    assert response.status_code == 200

    completed = response.json()
    opponent = client.get(f"/api/task/2?csv={csv_path}").json()

    assert (completed["rating"], completed["rating_deviation"]) == (1367, 292)
    assert (opponent["rating"], opponent["rating_deviation"]) == (1733, 292)


def test_glicko_context_isolation(tmp_path):
    """Completing a task in one context leaves another context's rating unchanged."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_context_isolation.csv", tmp_path)

    before = _ratings(csv_path, range(1, 4))

    response = client.post(f"/api/task/1/done?csv={csv_path}")
    assert response.status_code == 200

    after = _ratings(csv_path, range(1, 4))

    assert after[2] != before[2]
    assert after[3] == before[3]


def test_glicko_solo_completion(tmp_path):
    """A solo completion changes the rating and leaves no synthetic task."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_solo_completion.csv", tmp_path)
    reference_date = "2026-11-08"

    context_before = client.get(f"/api/context/chores?csv={csv_path}&date={reference_date}")
    assert context_before.status_code == 200
    assert context_before.json() == [1]

    before = client.get(f"/api/task/1?csv={csv_path}").json()["rating"]

    response = client.post(f"/api/task/1/done?csv={csv_path}")
    assert response.status_code == 200

    after = client.get(f"/api/task/1?csv={csv_path}").json()["rating"]
    assert after != before

    assert client.get(f"/api/task/?csv={csv_path}").json() == [1]
    assert client.get(f"/api/context/chores?csv={csv_path}&date={reference_date}").json() == []


def test_glicko_default_date_projection(tmp_path):
    """A read without a date projects the deviation to today."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_default_date_projection.csv", tmp_path)
    today = date.today().isoformat()

    undated = client.get(f"/api/task/1?csv={csv_path}")
    dated = client.get(f"/api/task/1?csv={csv_path}&date={today}")

    assert undated.status_code == 200
    assert dated.status_code == 200
    assert undated.json()["rating_deviation"] == dated.json()["rating_deviation"]


def test_glicko_completion_anchor(tmp_path):
    """A completion moves the anchor so the next undated read matches."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_integer_contract.csv", tmp_path)

    completed = client.post(f"/api/task/8/done?csv={csv_path}")
    assert completed.status_code == 200

    undated = client.get(f"/api/task/8?csv={csv_path}")

    assert undated.json()["rating_deviation"] == completed.json()["rating_deviation"]


def test_glicko_deviation_growth():
    """A year without a match projects the deviation to 362."""
    fixture = "tests/data/acceptance_glicko_deviation_growth.csv"

    response = client.get(f"/api/task/1?csv={fixture}&date=2026-11-08")

    assert response.json()["rating_deviation"] == 362
