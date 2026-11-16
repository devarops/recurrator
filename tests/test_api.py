from datetime import date

from fastapi.testclient import TestClient
from recurrator.api import app
import recurrator.io as io
from conftest import (
    _copy_fixture,
    _get_file_checksum,
    _assert_file_unchanged,
    TASK_2_ORIGINAL_DATES,
    TASK_5_ORIGINAL_DATES,
)

client = TestClient(app)


def _restore_rating_fields(csv_path, tasks):
    """Restore every task's rating, deviation, and anchor."""
    for task in tasks:
        assert task.rating_date is not None
        io.update_task_rating(task.id, task.rating, csv_path)
        io.update_task_rating_deviation(task.id, task.rating_deviation, csv_path)
        io.update_task_rating_date(task.id, task.rating_date, csv_path)


def _restore_skip_fields(csv_path, tasks):
    """Restore the skip fields of tasks that a context read deferred."""
    for task_id, task in tasks.items():
        io.update_task_skip_count(task_id, task.skip_count, csv_path)
        io.update_task_skip_date(task_id, None, csv_path)


def _stored_tasks(csv_path, task_ids):
    """Read the stored tasks for the given ids, keyed by id."""
    return {task_id: io.get_task_by_id(task_id, csv_path) for task_id in task_ids}


def _task_field(csv_path, task_id, field_name):
    """Read one field of a stored task through the API."""
    return client.get(f"/api/task/{task_id}?csv={csv_path}").json()[field_name]


def _complete(csv_path, task_id):
    """Mark a task done through the API."""
    return client.post(f"/api/task/{task_id}/done?csv={csv_path}")


def test_get_single_task_id():
    """Verify GET /task/ returns a list of raw task IDs."""
    response = client.get("/api/task/?csv=tests/data/test_single_task.csv")

    assert response.status_code == 200

    expected_data = [8]
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_multiple_task_ids():
    """Verify GET /task/ returns a list of raw task IDs when multiple tasks are present."""
    response = client.get("/api/task/?csv=tests/data/test_three_tasks.csv")

    expected_data = [2, 3, 5]
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_task_by_id_default_csv():
    """Verify GET /task/{id} returns the correct task details."""
    response = client.get("/api/task/8?csv=tests/data/test_single_task.csv&date=2025-08-19")

    assert response.status_code == 200

    expected_data = {
        "id": 8,
        "description": "TypeLit.io",
        "context": "laptop",
        "skip_count": 1,
        "starred": False,
        "latest_date": "2025-11-17",
        "recurrence_days": 14,
        "due_date": "2025-12-01",
        "coins": 14,
        "rating": 1500,
        "rating_deviation": 350,
    }
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_task_by_id_alternative_csv():

    response = client.get("/api/task/3?csv=tests/data/test_three_tasks.csv&date=2026-03-07")

    expected_data = {
        "id": 3,
        "description": "Lavar trapos",
        "context": "chores",
        "skip_count": 0,
        "starred": False,
        "latest_date": "2026-03-07",
        "recurrence_days": 33,
        "due_date": "2026-04-09",
        "coins": 33,
        "rating": 1500,
        "rating_deviation": 350,
    }

    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_task_by_id_starred():
    """Verify GET /task/{id} returns coins doubled for a starred task."""
    response = client.get("/api/task/1?csv=tests/data/test_contexts.csv&date=2026-04-04")

    assert response.status_code == 200

    expected_data = {
        "id": 1,
        "description": "Reparar fuga escusado",
        "context": "casa",
        "skip_count": 0,
        "starred": True,
        "latest_date": "2026-04-04",
        "recurrence_days": 21,
        "due_date": "2026-04-25",
        "coins": 42,
        "rating": 1500,
        "rating_deviation": 350,
    }
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_nonexistent_task_returns_404():
    """Verify GET /task/{id} returns 404 when the task is not found."""
    response = client.get("/api/task/999?csv=tests/data/test_single_task.csv")

    assert response.status_code == 404


def test_set_task_as_done():
    """Verify POST /task/{id}/done marks the task as done and updates the due date correctly."""

    csv_path = "tests/data/test_three_tasks.csv"
    original_checksum = _get_file_checksum(csv_path)
    original_tasks = io.import_tasks_from_csv(csv_path)

    task_id = 5
    original_task = client.get(f"/api/task/{task_id}?csv={csv_path}").json()
    response = _complete(csv_path, task_id)

    assert response.status_code == 200

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
    _restore_rating_fields(csv_path, original_tasks)

    _assert_file_unchanged(csv_path, original_checksum)


def test_task_done_idempotency():
    """Verify POST /task/{id}/done returns 409 on consecutive duplicate completion."""

    csv_path = "tests/data/test_three_tasks.csv"
    original_checksum = _get_file_checksum(csv_path)
    original_tasks = io.import_tasks_from_csv(csv_path)

    task_id = 2
    original_skip_count = io.get_task_by_id(task_id, csv_path).skip_count

    try:
        first_response = _complete(csv_path, task_id)
        assert first_response.status_code == 200

        second_response = _complete(csv_path, task_id)
        assert second_response.status_code == 409
        assert "error" in second_response.json()
    finally:
        # Undo changes to CSV file for other tests
        io.update_task_skip_count(task_id, original_skip_count, csv_path)
        io.update_task_dates(task_id, TASK_2_ORIGINAL_DATES, csv_path)
        _restore_rating_fields(csv_path, original_tasks)

    _assert_file_unchanged(csv_path, original_checksum)


def test_get_due_contexts():
    """Verify GET /context/ returns the correct list of contexts from due tasks."""

    csv_path = "tests/data/test_contexts.csv"
    reference_date = "2026-05-01"
    response = client.get(f"/api/context/?csv={csv_path}&date={reference_date}")

    assert response.status_code == 200

    expected_contexts = ["casa", "chores", "laptop"]
    obtained_contexts = response.json()
    assert obtained_contexts == expected_contexts


def test_get_tasks_by_context():
    """Verify GET /context/{context_id} returns prioritized task IDs."""

    csv_path = "tests/data/test_eight_tasks.csv"
    reference_date = "2026-05-02"
    context = "chores"

    original_checksum = _get_file_checksum(csv_path)

    deferred_task_ids = [7, 8]
    original_deferred_tasks = _stored_tasks(csv_path, deferred_task_ids)

    response = client.get(f"/api/context/{context}?csv={csv_path}&date={reference_date}")

    assert response.status_code == 200

    expected_task_ids = [1, 2, 3, 4, 5, 6]
    obtained_task_ids = response.json()
    assert obtained_task_ids == expected_task_ids

    _restore_skip_fields(csv_path, original_deferred_tasks)

    _assert_file_unchanged(csv_path, original_checksum)


def test_get_tasks_by_context_defers_remaining_tasks():
    """Verify deferred tasks get skip_count incremented and skip_date set."""

    csv_path = "tests/data/test_eight_tasks.csv"
    reference_date = "2026-05-02"
    context = "chores"

    original_checksum = _get_file_checksum(csv_path)

    deferred_task_ids = [7, 8]
    original_deferred_tasks = _stored_tasks(csv_path, deferred_task_ids)

    response = client.get(f"/api/context/{context}?csv={csv_path}&date={reference_date}")

    assert response.status_code == 200

    deferred_task_id = 7
    original_skip_count = original_deferred_tasks[deferred_task_id].skip_count
    updated_task = io.get_task_by_id(deferred_task_id, csv_path)
    obtained_skip_count = updated_task.skip_count
    assert obtained_skip_count == original_skip_count + 1

    expected_latest_date = date(2026, 5, 2)
    obtained_latest_date = updated_task.latest_date
    assert obtained_latest_date == expected_latest_date

    _restore_skip_fields(csv_path, original_deferred_tasks)

    _assert_file_unchanged(csv_path, original_checksum)


def test_get_task_by_id_rating():
    """Verify GET /task/{id} returns the task rating."""
    response = client.get("/api/task/8?csv=tests/data/acceptance_glicko_integer_contract.csv")

    assert response.json()["rating"] == 1500


def _assert_undated_matches_today(fixture, task_id):
    """Assert that an undated read projects the deviation to today."""
    undated = client.get(f"/api/task/{task_id}?csv={fixture}")
    dated = client.get(f"/api/task/{task_id}?csv={fixture}&date={date.today().isoformat()}")

    assert undated.json()["rating_deviation"] == dated.json()["rating_deviation"]


def test_get_task_by_id_rating_deviation():
    """Verify GET /task/{id} returns the projected task rating deviation."""
    _assert_undated_matches_today("tests/data/acceptance_glicko_integer_contract.csv", 8)


def test_get_task_by_id_projects_rating_deviation():
    """Verify GET /task/{id} projects the deviation to the requested date."""
    response = client.get(
        "/api/task/1?csv=tests/data/acceptance_glicko_inactivity_growth.csv&date=2026-11-08"
    )

    assert response.json()["rating_deviation"] > 350


def test_get_task_by_id_projects_deviation_to_today():
    """Verify GET /task/{id} without a date projects the deviation to today."""
    _assert_undated_matches_today("tests/data/acceptance_glicko_default_date_projection.csv", 1)


def test_task_done_rating(tmp_path):
    """Verify POST /task/{id}/done returns the task rating."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_integer_contract.csv", tmp_path)

    response = _complete(csv_path, 8)

    assert response.json()["rating"] == _task_field(csv_path, 8, "rating")


def test_task_done_rating_deviation(tmp_path):
    """Verify POST /task/{id}/done returns the task rating deviation."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_integer_contract.csv", tmp_path)

    response = _complete(csv_path, 8)

    assert isinstance(response.json()["rating_deviation"], int)


def test_task_done_decreases_completed_rating(tmp_path):
    """Verify completing one of two tasks lowers its rating."""
    csv_path = _copy_fixture("tests/data/test_two_ratings.csv", tmp_path)

    before = _task_field(csv_path, 1, "rating")
    response = _complete(csv_path, 1)

    assert response.json()["rating"] < before


def _assert_opponent_rating_rises(fixture, tmp_path):
    """Assert that completing task 1 raises task 2's rating."""
    csv_path = _copy_fixture(fixture, tmp_path)

    before = _task_field(csv_path, 2, "rating")
    _complete(csv_path, 1)
    after = _task_field(csv_path, 2, "rating")

    assert after > before


def test_task_done_increases_opponent_rating(tmp_path):
    """Verify completing one of two tasks raises the opponent rating."""
    _assert_opponent_rating_rises("tests/data/test_two_ratings.csv", tmp_path)


def test_task_done_changes_equal_rated_opponent(tmp_path):
    """Verify completing a task raises an equal-rated opponent in the same context."""
    _assert_opponent_rating_rises("tests/data/test_two_equal_ratings.csv", tmp_path)


def test_task_done_keeps_not_due_peer_rating(tmp_path):
    """Verify completing a due task leaves a not-due peer's rating unchanged."""
    csv_path = _copy_fixture("tests/data/test_due_and_not_due.csv", tmp_path)

    before = _task_field(csv_path, 2, "rating")
    _complete(csv_path, 1)
    after = _task_field(csv_path, 2, "rating")

    assert after == before


def test_task_done_drops_completed_rating_more_than_one_point(tmp_path):
    """Verify the completed rating change exceeds the one-point placeholder."""
    csv_path = _copy_fixture("tests/data/test_two_ratings.csv", tmp_path)

    before = _task_field(csv_path, 1, "rating")
    response = _complete(csv_path, 1)

    assert before - response.json()["rating"] > 1


def test_task_done_preserves_total_rating(tmp_path):
    """Verify a two-participant match conserves the total rating."""
    csv_path = _copy_fixture("tests/data/test_two_ratings.csv", tmp_path)

    before = sum(_task_field(csv_path, task_id, "rating") for task_id in (1, 2))
    response = _complete(csv_path, 1)
    opponent_rating = _task_field(csv_path, 2, "rating")

    assert response.json()["rating"] + opponent_rating == before


def test_task_done_lowers_completed_rating_deviation(tmp_path):
    """Verify a completion lowers the completed task deviation."""
    csv_path = _copy_fixture("tests/data/test_two_ratings_frozen.csv", tmp_path)

    before = _task_field(csv_path, 1, "rating_deviation")
    response = _complete(csv_path, 1)

    assert response.json()["rating_deviation"] < before


def test_task_done_lowers_opponent_rating_deviation(tmp_path):
    """Verify a completion lowers the opponent deviation."""
    csv_path = _copy_fixture("tests/data/test_two_ratings_frozen.csv", tmp_path)

    before = _task_field(csv_path, 2, "rating_deviation")
    _complete(csv_path, 1)
    after = _task_field(csv_path, 2, "rating_deviation")

    assert after < before


def test_task_done_drops_completed_deviation_more_than_one_point(tmp_path):
    """Verify the completed deviation drop exceeds the placeholder."""
    csv_path = _copy_fixture("tests/data/test_two_ratings_frozen.csv", tmp_path)

    before = _task_field(csv_path, 1, "rating_deviation")
    response = _complete(csv_path, 1)

    assert before - response.json()["rating_deviation"] > 1


def test_task_done_sets_completed_rating_to_simultaneous_value(tmp_path):
    """Verify the completed rating matches a simultaneous Glicko update."""
    csv_path = _copy_fixture("tests/data/test_two_ratings_frozen.csv", tmp_path)

    response = _complete(csv_path, 1)

    assert response.json()["rating"] == 1367


def test_task_done_changes_solo_rating(tmp_path):
    """Verify completing a solo task changes its rating."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_solo_completion.csv", tmp_path)

    before = _task_field(csv_path, 1, "rating")
    _complete(csv_path, 1)
    after = _task_field(csv_path, 1, "rating")

    assert after != before


def test_task_done_updates_rating_date_anchor(tmp_path):
    """Verify a completion moves the completed task's rating anchor to today."""
    csv_path = _copy_fixture("tests/data/test_two_ratings.csv", tmp_path)

    _complete(csv_path, 1)

    task = io.get_task_by_id(1, csv_path)
    assert task.rating_date == date.today()
