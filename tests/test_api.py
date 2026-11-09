from datetime import date
from shutil import copyfile

from fastapi.testclient import TestClient
from recurrator.api import app
import recurrator.io as io
from conftest import (
    _get_file_checksum,
    _assert_file_unchanged,
    TASK_2_ORIGINAL_DATES,
    TASK_5_ORIGINAL_DATES,
)

client = TestClient(app)


def _copy_fixture(fixture, tmp_path):
    """Copy a task fixture into the test's temporary directory."""
    csv_path = tmp_path / "tasks.csv"
    copyfile(fixture, csv_path)
    return csv_path


def test_frontend_is_served_from_the_api_app():
    """Verify the API serves the index page and its JavaScript assets."""
    index_response = client.get("/")

    assert index_response.status_code == 200
    assert '<div id="scopes"' in index_response.text

    script_response = client.get("/main.js")

    assert script_response.status_code == 200
    assert "function initPage" in script_response.text

    ui_response = client.get("/ui.js")

    assert ui_response.status_code == 200
    assert "renderMonsterCard" in ui_response.text


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
        "coins": 14,
        "rating": 1500,
        "rating_deviation": 350,
    }
    obtained_data = response.json()
    assert obtained_data == expected_data


def test_get_task_by_id_alternative_csv():

    response = client.get("/task/3?csv=tests/data/test_three_tasks.csv")

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
    response = client.get("/task/1?csv=tests/data/test_contexts.csv")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

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
    response = client.get("/task/999?csv=tests/data/test_single_task.csv")

    expected_status_code = 404
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code


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


def test_task_done_idempotency():
    """Verify POST /task/{id}/done returns 409 on consecutive duplicate completion."""

    csv_path = "tests/data/test_three_tasks.csv"
    original_checksum = _get_file_checksum(csv_path)

    task_id = 2
    original_skip_count = io.get_task_by_id(task_id, csv_path).skip_count

    try:
        first_response = client.post(f"/task/{task_id}/done?csv={csv_path}")
        assert first_response.status_code == 200

        second_response = client.post(f"/task/{task_id}/done?csv={csv_path}")
        assert second_response.status_code == 409
        assert "error" in second_response.json()
    finally:
        # Undo changes to CSV file for other tests
        io.update_task_skip_count(task_id, original_skip_count, csv_path)
        io.update_task_dates(task_id, TASK_2_ORIGINAL_DATES, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)


def test_get_due_contexts():
    """Verify GET /context/ returns the correct list of contexts from due tasks."""

    csv_path = "tests/data/test_contexts.csv"
    reference_date = "2026-05-01"
    response = client.get(f"/context/?csv={csv_path}&date={reference_date}")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

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
    original_deferred_tasks = {
        task_id: io.get_task_by_id(task_id, csv_path) for task_id in deferred_task_ids
    }

    response = client.get(f"/context/{context}?csv={csv_path}&date={reference_date}")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

    expected_task_ids = [1, 2, 3, 4, 5, 6]
    obtained_task_ids = response.json()
    assert obtained_task_ids == expected_task_ids

    # Undo changes to CSV file for other tests
    for task_id, original_task in original_deferred_tasks.items():
        io.update_task_skip_count(task_id, original_task.skip_count, csv_path)
        io.update_task_skip_date(task_id, None, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)


def test_get_tasks_by_context_defers_remaining_tasks():
    """Verify deferred tasks get skip_count incremented and skip_date set."""

    csv_path = "tests/data/test_eight_tasks.csv"
    reference_date = "2026-05-02"
    context = "chores"

    original_checksum = _get_file_checksum(csv_path)

    deferred_task_ids = [7, 8]
    original_deferred_tasks = {
        task_id: io.get_task_by_id(task_id, csv_path) for task_id in deferred_task_ids
    }

    response = client.get(f"/context/{context}?csv={csv_path}&date={reference_date}")

    expected_status_code = 200
    obtained_status_code = response.status_code
    assert obtained_status_code == expected_status_code

    deferred_task_id = 7
    original_skip_count = original_deferred_tasks[deferred_task_id].skip_count
    updated_task = io.get_task_by_id(deferred_task_id, csv_path)
    obtained_skip_count = updated_task.skip_count
    assert obtained_skip_count == original_skip_count + 1

    expected_latest_date = date(2026, 5, 2)
    obtained_latest_date = updated_task.latest_date
    assert obtained_latest_date == expected_latest_date

    # Undo changes to CSV file for other tests
    for task_id, original_task in original_deferred_tasks.items():
        io.update_task_skip_count(task_id, original_task.skip_count, csv_path)
        io.update_task_skip_date(task_id, None, csv_path)

    _assert_file_unchanged(csv_path, original_checksum)


def test_get_task_by_id_rating():
    """Verify GET /task/{id} returns the task rating."""
    response = client.get("/task/8?csv=tests/data/acceptance_glicko_integer_contract.csv")

    assert response.json()["rating"] == 1500


def test_get_task_by_id_rating_deviation():
    """Verify GET /task/{id} returns the task rating deviation."""
    response = client.get("/task/8?csv=tests/data/acceptance_glicko_integer_contract.csv")

    assert response.json()["rating_deviation"] == 350


def test_get_task_by_id_projects_rating_deviation():
    """Verify GET /task/{id} projects the deviation to the requested date."""
    response = client.get(
        "/task/1?csv=tests/data/acceptance_glicko_inactivity_growth.csv&date=2025-11-09"
    )

    assert response.json()["rating_deviation"] > 350


def test_task_done_rating(tmp_path):
    """Verify POST /task/{id}/done returns the task rating."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_integer_contract.csv", tmp_path)

    response = client.post(f"/task/8/done?csv={csv_path}")

    assert response.json()["rating"] == 1500


def test_task_done_rating_deviation(tmp_path):
    """Verify POST /task/{id}/done returns the task rating deviation."""
    csv_path = _copy_fixture("tests/data/acceptance_glicko_integer_contract.csv", tmp_path)

    response = client.post(f"/task/8/done?csv={csv_path}")

    assert response.json()["rating_deviation"] == 350


def test_task_done_decreases_completed_rating(tmp_path):
    """Verify completing one of two tasks lowers its rating."""
    csv_path = _copy_fixture("tests/data/test_two_ratings.csv", tmp_path)

    before = client.get(f"/task/1?csv={csv_path}").json()["rating"]
    response = client.post(f"/task/1/done?csv={csv_path}")

    assert response.json()["rating"] < before


def _assert_opponent_rating_rises(fixture, tmp_path):
    """Assert that completing task 1 raises task 2's rating."""
    csv_path = _copy_fixture(fixture, tmp_path)

    before = client.get(f"/task/2?csv={csv_path}").json()["rating"]
    client.post(f"/task/1/done?csv={csv_path}")
    after = client.get(f"/task/2?csv={csv_path}").json()["rating"]

    assert after > before


def test_task_done_increases_opponent_rating(tmp_path):
    """Verify completing one of two tasks raises the opponent rating."""
    _assert_opponent_rating_rises("tests/data/test_two_ratings.csv", tmp_path)


def test_task_done_changes_equal_rated_opponent(tmp_path):
    """Verify completing a task raises an equal-rated opponent in the same context."""
    _assert_opponent_rating_rises("tests/data/test_two_equal_ratings.csv", tmp_path)


def test_task_done_drops_completed_rating_more_than_one_point(tmp_path):
    """Verify the completed rating change exceeds the one-point placeholder."""
    csv_path = _copy_fixture("tests/data/test_two_ratings.csv", tmp_path)

    before = client.get(f"/task/1?csv={csv_path}").json()["rating"]
    response = client.post(f"/task/1/done?csv={csv_path}")

    assert before - response.json()["rating"] > 1


def test_task_done_preserves_total_rating(tmp_path):
    """Verify a two-participant match conserves the total rating."""
    csv_path = _copy_fixture("tests/data/test_two_ratings.csv", tmp_path)

    before = sum(
        client.get(f"/task/{task_id}?csv={csv_path}").json()["rating"] for task_id in (1, 2)
    )
    response = client.post(f"/task/1/done?csv={csv_path}")
    opponent = client.get(f"/task/2?csv={csv_path}").json()

    assert response.json()["rating"] + opponent["rating"] == before


def test_task_done_lowers_completed_rating_deviation(tmp_path):
    """Verify a completion lowers the completed task deviation."""
    csv_path = _copy_fixture("tests/data/test_two_ratings_frozen.csv", tmp_path)

    before = client.get(f"/task/1?csv={csv_path}").json()["rating_deviation"]
    response = client.post(f"/task/1/done?csv={csv_path}")

    assert response.json()["rating_deviation"] < before


def test_task_done_lowers_opponent_rating_deviation(tmp_path):
    """Verify a completion lowers the opponent deviation."""
    csv_path = _copy_fixture("tests/data/test_two_ratings_frozen.csv", tmp_path)

    before = client.get(f"/task/2?csv={csv_path}").json()["rating_deviation"]
    client.post(f"/task/1/done?csv={csv_path}")
    after = client.get(f"/task/2?csv={csv_path}").json()["rating_deviation"]

    assert after < before


def test_task_done_drops_completed_deviation_more_than_one_point(tmp_path):
    """Verify the completed deviation drop exceeds the placeholder."""
    csv_path = _copy_fixture("tests/data/test_two_ratings_frozen.csv", tmp_path)

    before = client.get(f"/task/1?csv={csv_path}").json()["rating_deviation"]
    response = client.post(f"/task/1/done?csv={csv_path}")

    assert before - response.json()["rating_deviation"] > 1


def test_task_done_sets_completed_rating_to_simultaneous_value(tmp_path):
    """Verify the completed rating matches a simultaneous Glicko update."""
    csv_path = _copy_fixture("tests/data/test_two_ratings_frozen.csv", tmp_path)

    response = client.post(f"/task/1/done?csv={csv_path}")

    assert response.json()["rating"] == 1367
