import csv
from datetime import date

from conftest import (
    GLICKO_CONTRACT_CSV,
    GLICKO_DEFAULT_DATE_CSV,
    GLICKO_INACTIVITY_CSV,
    GLICKO_SOLO_CSV,
    _copy_fixture,
    _read_task,
    _read_task_on,
    _complete,
    _read_context_task_ids,
    _read_task_ids,
)


def _ratings(csv_path, task_ids):
    """Return each task's rating from the fixture."""
    return {task_id: _read_task(csv_path, task_id).json()["rating"] for task_id in task_ids}


def _ratings_before_and_after_completion(csv_path, task_ids, completed_task_id):
    """Return every task's rating before and after completing one task."""
    before = _ratings(csv_path, task_ids)
    response = _complete(csv_path, completed_task_id)
    assert response.status_code == 200
    after = _ratings(csv_path, task_ids)
    return before, after


def test_glicko_integer_contract(tmp_path):
    """Rating and rating deviation are integers when a task is read or completed."""
    response = _read_task(GLICKO_CONTRACT_CSV, 8)
    assert response.status_code == 200

    task = response.json()
    assert isinstance(task["rating"], int)
    assert isinstance(task["rating_deviation"], int)

    completion_csv = _copy_fixture(GLICKO_CONTRACT_CSV, tmp_path)

    response = _complete(completion_csv, 8)
    assert response.status_code == 200

    completed = response.json()
    assert isinstance(completed["rating"], int)
    assert isinstance(completed["rating_deviation"], int)


def test_glicko_four_tasks(tmp_path):
    """The completed task loses rating, its three due peers change, and others keep theirs."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_four_tasks.csv", tmp_path)

    before, after = _ratings_before_and_after_completion(csv_path, range(1, 7), 1)

    assert after[1] < before[1]
    for task_id in (2, 3, 4):
        assert after[task_id] != before[task_id]
    for task_id in (5, 6):
        assert after[task_id] == before[task_id]


def test_glicko_early_completion(tmp_path):
    """A not-yet-due completion joins the four due tasks and all five ratings change."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_early_completion.csv", tmp_path)

    before, after = _ratings_before_and_after_completion(csv_path, range(1, 6), 5)

    assert after[5] < before[5]
    for task_id in range(1, 5):
        assert after[task_id] != before[task_id]


def test_glicko_inactivity_growth():
    """An older rating anchor projects a larger deviation at the same reference date."""
    fixture = GLICKO_INACTIVITY_CSV
    reference_date = "2026-11-08"

    older = _read_task_on(fixture, 1, reference_date)
    newer = _read_task_on(fixture, 2, reference_date)

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

    response = _complete(csv_path, 1)
    assert response.status_code == 200

    completed = response.json()
    opponent = _read_task(csv_path, 2).json()

    assert (completed["rating"], completed["rating_deviation"]) == (1367, 292)
    assert (opponent["rating"], opponent["rating_deviation"]) == (1733, 292)


def test_glicko_context_isolation(tmp_path):
    """Completing a task in one context leaves another context's rating unchanged."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_context_isolation.csv", tmp_path)

    before, after = _ratings_before_and_after_completion(csv_path, range(1, 4), 1)

    assert after[2] != before[2]
    assert after[3] == before[3]


def test_glicko_solo_completion(tmp_path):
    """A solo completion changes the rating and leaves no synthetic task."""
    csv_path = _copy_fixture(GLICKO_SOLO_CSV, tmp_path)
    reference_date = "2026-11-08"

    context_before = _read_context_task_ids(csv_path, "chores", reference_date)
    assert context_before.status_code == 200
    assert context_before.json() == [1]

    before = _read_task(csv_path, 1).json()["rating"]

    response = _complete(csv_path, 1)
    assert response.status_code == 200

    after = _read_task(csv_path, 1).json()["rating"]
    assert after != before

    assert _read_task_ids(csv_path).json() == [1]
    assert _read_context_task_ids(csv_path, "chores", reference_date).json() == []


def test_glicko_default_date_projection(tmp_path):
    """A read without a date projects the deviation to today."""
    csv_path = _copy_fixture(GLICKO_DEFAULT_DATE_CSV, tmp_path)
    today = date.today().isoformat()

    undated = _read_task(csv_path, 1)
    dated = _read_task_on(csv_path, 1, today)

    assert undated.status_code == 200
    assert dated.status_code == 200
    assert undated.json()["rating_deviation"] == dated.json()["rating_deviation"]


def test_glicko_completion_anchor(tmp_path):
    """A completion moves the anchor so the next undated read matches."""
    csv_path = _copy_fixture(GLICKO_CONTRACT_CSV, tmp_path)

    completed = _complete(csv_path, 8)
    assert completed.status_code == 200

    undated = _read_task(csv_path, 8)

    assert undated.json()["rating_deviation"] == completed.json()["rating_deviation"]


def test_glicko_deviation_growth():
    """A year without a match projects the deviation to 362."""
    fixture = "tests/data/acceptance_glicko_deviation_growth.csv"

    response = _read_task_on(fixture, 1, "2026-11-08")

    assert response.json()["rating_deviation"] == 362


def test_glicko_shared_context_event(tmp_path):
    """A two-context completion forms one event with every shared-context peer."""
    csv_path = _copy_fixture(
        "tests/data/acceptance_glicko_shared_context_event.csv", tmp_path
    )

    before, after = _ratings_before_and_after_completion(csv_path, range(1, 6), 1)

    assert after[1] < before[1]
    for task_id in (2, 3, 4):
        assert after[task_id] != before[task_id]
    assert after[5] == before[5]


def test_glicko_second_context_participates(tmp_path):
    """A peer that shares only the second context changes rating."""
    csv_path = _copy_fixture(
        "tests/data/acceptance_glicko_second_context_participates.csv", tmp_path
    )

    before, after = _ratings_before_and_after_completion(csv_path, range(1, 3), 1)

    assert after[1] < before[1]
    assert after[2] != before[2]
