from datetime import date

import recurrator.io as io
from conftest import (
    client,
    _copy_fixture,
    _get_file_checksum,
    _assert_error_response,
    _assert_file_unchanged,
    _read_task,
    _read_task_on,
    _complete,
    _read_context_task_ids,
    _read_due_task_ids,
    _read_due_context_ids,
    _read_response_schema,
    _read_task_ids,
    _patch_description,
    _patch_description_body,
    _restore_completion_fields,
    CONTEXT_TASKS_CSV,
    EIGHT_TASKS_CSV,
    GLICKO_CONTRACT_CSV,
    GLICKO_DEFAULT_DATE_CSV,
    GLICKO_INACTIVITY_CSV,
    GLICKO_SOLO_CSV,
    SINGLE_TASK_CSV,
    THREE_TASKS_CSV,
    TWO_RATINGS_CSV,
    TWO_RATINGS_FROZEN_CSV,
    TASK_2_ORIGINAL_DATES,
    TASK_5_ORIGINAL_DATES,
)


def _snapshot_tasks_file(csv_path):
    """Record a file's checksum and its tasks before a test mutates it."""
    return _get_file_checksum(csv_path), io.import_tasks_from_csv(csv_path)


def _restore_rating_fields(csv_path, tasks):
    """Restore every task's rating, deviation, and anchor."""
    for task in tasks:
        assert task.rating_date is not None
        io.update_task_rating_fields(
            task.id, task.rating, task.rating_deviation, task.rating_date, csv_path
        )


def _task_field(csv_path, task_id, field_name):
    """Read one field of a stored task through the API."""
    return _read_task(csv_path, task_id).json()[field_name]


def _field_before_and_after_completion(csv_path, completed_task_id, observed_task_id, field_name):
    """Return the observed task's field before and after a completion."""
    before = _task_field(csv_path, observed_task_id, field_name)
    _complete(csv_path, completed_task_id)
    after = _task_field(csv_path, observed_task_id, field_name)
    return before, after


def _completed_field_before_and_after(csv_path, task_id, field_name):
    """Return the completed task's field before the completion and in its response."""
    before = _task_field(csv_path, task_id, field_name)
    response = _complete(csv_path, task_id)
    return before, response.json()[field_name]


def _assert_undated_matches_today(fixture, task_id):
    """Assert that an undated read projects the deviation to today."""
    undated = _read_task(fixture, task_id)
    dated = _read_task_on(fixture, task_id, date.today().isoformat())

    assert undated.json()["rating_deviation"] == dated.json()["rating_deviation"]


def _assert_opponent_rating_rises(fixture, tmp_path):
    """Assert that completing task 1 raises task 2's rating."""
    csv_path = _copy_fixture(fixture, tmp_path)

    before, after = _field_before_and_after_completion(csv_path, 1, 2, "rating")

    assert after > before


def test_get_single_task_id():
    """Verify GET /task/ returns a list of raw task IDs."""
    response = _read_task_ids(SINGLE_TASK_CSV)

    assert response.status_code == 200

    assert response.json() == [8]


def test_get_multiple_task_ids():
    """Verify GET /task/ returns a list of raw task IDs when multiple tasks are present."""
    response = _read_task_ids(THREE_TASKS_CSV)

    assert response.json() == [2, 3, 5]


def test_due_task_ids_malformed_date_returns_422():
    """Verify a malformed due date is refused as invalid input."""
    response = _read_due_task_ids(THREE_TASKS_CSV, "not-a-date")

    assert response.status_code == 422


def test_due_task_ids_list_only_tasks_due_by_the_date():
    """Verify a dated due read lists only the tasks due by that date."""
    response = _read_due_task_ids(THREE_TASKS_CSV, "2026-01-01")

    assert response.json() == [5]


def test_get_task_by_id_default_csv():
    """Verify GET /task/{id} returns the correct task details."""
    response = _read_task_on(SINGLE_TASK_CSV, 8, "2025-08-19")

    assert response.status_code == 200

    expected_data = {
        "id": 8,
        "description": "TypeLit.io",
        "contexts": ["laptop"],
        "skip_count": 1,
        "starred": False,
        "latest_date": "2025-11-17",
        "latest_done_date": "2025-08-19",
        "recurrence_days": 14,
        "due_date": "2025-12-01",
        "coins": 14,
        "rating": 1500,
        "rating_deviation": 350,
    }
    assert response.json() == expected_data


def test_get_task_by_id_alternative_csv():

    response = _read_task_on(THREE_TASKS_CSV, 3, "2026-03-07")

    expected_data = {
        "id": 3,
        "description": "Lavar trapos",
        "contexts": ["chores"],
        "skip_count": 0,
        "starred": False,
        "latest_date": "2026-03-07",
        "latest_done_date": "2026-03-07",
        "recurrence_days": 33,
        "due_date": "2026-04-09",
        "coins": 33,
        "rating": 1500,
        "rating_deviation": 350,
    }

    assert response.json() == expected_data


def test_get_task_by_id_starred():
    """Verify GET /task/{id} returns coins doubled for a starred task."""
    response = _read_task_on(CONTEXT_TASKS_CSV, 1, "2026-04-04")

    assert response.status_code == 200

    expected_data = {
        "id": 1,
        "description": "Reparar fuga escusado",
        "contexts": ["casa"],
        "skip_count": 0,
        "starred": True,
        "latest_date": "2026-04-04",
        "latest_done_date": "2026-04-04",
        "recurrence_days": 21,
        "due_date": "2026-04-25",
        "coins": 42,
        "rating": 1500,
        "rating_deviation": 350,
    }
    assert response.json() == expected_data


def test_get_task_by_id_reports_last_completion():
    """Verify GET /task/{id} returns the fourth stored completion date."""
    response = _read_task(THREE_TASKS_CSV, 2)

    assert response.json()["latest_done_date"] == "2024-12-07"


def test_get_nonexistent_task_returns_404():
    """Verify GET /task/{id} returns 404 when the task is not found."""
    response = _read_task(SINGLE_TASK_CSV, 999)

    assert response.status_code == 404


def test_set_task_as_done():
    """Verify POST /task/{id}/done marks the task as done and updates the due date correctly."""

    csv_path = THREE_TASKS_CSV
    original_checksum, original_tasks = _snapshot_tasks_file(csv_path)

    task_id = 5
    original_task = _read_task(csv_path, task_id).json()
    response = _complete(csv_path, task_id)

    assert response.status_code == 200

    completed = response.json()
    assert completed["skip_count"] == 0

    original_skip_count = original_task["skip_count"]
    assert completed["skip_count"] != original_skip_count

    assert completed["due_date"] != original_task["due_date"]

    # Undo changes to CSV file for other tests
    _restore_completion_fields(task_id, original_skip_count, TASK_5_ORIGINAL_DATES, csv_path)
    _restore_rating_fields(csv_path, original_tasks)

    _assert_file_unchanged(csv_path, original_checksum)


def test_task_done_idempotency():
    """Verify POST /task/{id}/done returns 409 on consecutive duplicate completion."""

    csv_path = THREE_TASKS_CSV
    original_checksum, original_tasks = _snapshot_tasks_file(csv_path)

    task_id = 2
    original_skip_count = io.get_task_by_id(task_id, csv_path).skip_count

    try:
        first_response = _complete(csv_path, task_id)
        assert first_response.status_code == 200

        second_response = _complete(csv_path, task_id)
        _assert_error_response(second_response, 409)
    finally:
        # Undo changes to CSV file for other tests
        _restore_completion_fields(task_id, original_skip_count, TASK_2_ORIGINAL_DATES, csv_path)
        _restore_rating_fields(csv_path, original_tasks)

    _assert_file_unchanged(csv_path, original_checksum)


def test_get_due_contexts():
    """Verify GET /context/due/{date} lists the contexts with a due task."""

    csv_path = CONTEXT_TASKS_CSV
    reference_date = "2026-05-01"
    response = _read_due_context_ids(csv_path, reference_date)

    assert response.status_code == 200

    assert response.json() == ["casa", "chores", "laptop"]


def test_get_contexts():
    """Verify GET /context/ returns the stored context ids."""
    response = client.get(
        "/api/context/?contexts_csv=tests/data/acceptance_context_views_all_contexts.csv"
    )

    assert response.json() == ["casa", "chores", "garden"]


def test_get_due_contexts_today():
    """Verify GET /context/due/ returns the contexts due today."""
    response = client.get(f"/api/context/due/?csv={CONTEXT_TASKS_CSV}")

    assert response.status_code == 200


def test_get_due_tasks_today():
    """Verify GET /task/due/ returns the tasks due today."""
    response = client.get(f"/api/task/due/?csv={THREE_TASKS_CSV}")

    assert response.status_code == 200


def test_get_context_detail():
    """Verify GET /context/{id}/ returns the stored context."""
    response = client.get(
        "/api/context/garden/"
        "?contexts_csv=tests/data/acceptance_context_views_context_detail.csv"
    )

    assert response.json()["id"] == "garden"


def test_due_read_defers_tasks_beyond_the_available_slots(tmp_path):
    """Verify a single-context due read defers the surplus tasks."""
    csv_path = _copy_fixture(EIGHT_TASKS_CSV, tmp_path)

    response = _read_context_task_ids(csv_path, "chores", "2026-05-02")

    assert response.status_code == 200
    selected_ids = response.json()
    assert len(selected_ids) == 6

    deferred_tasks = [
        task for task in io.import_tasks_from_csv(csv_path) if task.id not in selected_ids
    ]
    assert [task.id for task in deferred_tasks] == [7, 8]
    assert all(task.skip_count == 1 for task in deferred_tasks)
    assert all(task.latest_date == date(2026, 5, 2) for task in deferred_tasks)


def test_due_read_reduces_the_slots_for_completions_today(tmp_path):
    """Verify a completion today costs one slot in the same context."""
    csv_path = _copy_fixture(EIGHT_TASKS_CSV, tmp_path)
    reference_date = date.today()

    completion = _complete(csv_path, 1)
    assert completion.status_code == 200

    response = _read_context_task_ids(csv_path, "chores", reference_date.isoformat())

    assert response.status_code == 200
    assert len(response.json()) == 5


def test_get_task_by_id_rating():
    """Verify GET /task/{id} returns the task rating."""
    response = _read_task(GLICKO_CONTRACT_CSV, 8)

    assert response.json()["rating"] == 1500


def test_get_task_by_id_rating_deviation():
    """Verify GET /task/{id} returns the projected task rating deviation."""
    _assert_undated_matches_today(GLICKO_CONTRACT_CSV, 8)


def test_get_task_by_id_projects_rating_deviation():
    """Verify GET /task/{id} projects the deviation to the requested date."""
    response = _read_task_on(GLICKO_INACTIVITY_CSV, 1, "2026-11-08")

    assert response.json()["rating_deviation"] > 350


def test_get_task_by_id_projects_deviation_to_today():
    """Verify GET /task/{id} without a date projects the deviation to today."""
    _assert_undated_matches_today(GLICKO_DEFAULT_DATE_CSV, 1)


def test_task_done_rating(tmp_path):
    """Verify POST /task/{id}/done returns the task rating."""
    csv_path = _copy_fixture(GLICKO_CONTRACT_CSV, tmp_path)

    response = _complete(csv_path, 8)

    assert response.json()["rating"] == _task_field(csv_path, 8, "rating")


def test_task_done_rating_deviation(tmp_path):
    """Verify POST /task/{id}/done returns the task rating deviation."""
    csv_path = _copy_fixture(GLICKO_CONTRACT_CSV, tmp_path)

    response = _complete(csv_path, 8)

    assert isinstance(response.json()["rating_deviation"], int)


def test_task_done_reports_last_completion(tmp_path):
    """Verify POST /task/{id}/done includes the last completion date."""
    csv_path = _copy_fixture(GLICKO_CONTRACT_CSV, tmp_path)

    response = _complete(csv_path, 8)

    assert "latest_done_date" in response.json()


def test_task_done_decreases_completed_rating(tmp_path):
    """Verify completing one of two tasks lowers its rating."""
    csv_path = _copy_fixture(TWO_RATINGS_CSV, tmp_path)

    before, after = _completed_field_before_and_after(csv_path, 1, "rating")

    assert after < before


def test_task_done_increases_opponent_rating(tmp_path):
    """Verify completing one of two tasks raises the opponent rating."""
    _assert_opponent_rating_rises(TWO_RATINGS_CSV, tmp_path)


def test_task_done_changes_equal_rated_opponent(tmp_path):
    """Verify completing a task raises an equal-rated opponent in the same context."""
    _assert_opponent_rating_rises("tests/data/test_two_equal_ratings.csv", tmp_path)


def test_task_done_keeps_not_due_peer_rating(tmp_path):
    """Verify completing a due task leaves a not-due peer's rating unchanged."""
    csv_path = _copy_fixture("tests/data/test_due_and_not_due.csv", tmp_path)

    before, after = _field_before_and_after_completion(csv_path, 1, 2, "rating")

    assert after == before


def test_task_done_drops_completed_rating_more_than_one_point(tmp_path):
    """Verify the completed rating change exceeds the one-point placeholder."""
    csv_path = _copy_fixture(TWO_RATINGS_CSV, tmp_path)

    before, after = _completed_field_before_and_after(csv_path, 1, "rating")

    assert before - after > 1


def test_task_done_preserves_total_rating(tmp_path):
    """Verify a two-participant match conserves the total rating."""
    csv_path = _copy_fixture(TWO_RATINGS_CSV, tmp_path)

    before = sum(_task_field(csv_path, task_id, "rating") for task_id in (1, 2))
    response = _complete(csv_path, 1)
    opponent_rating = _task_field(csv_path, 2, "rating")

    assert response.json()["rating"] + opponent_rating == before


def test_task_done_lowers_completed_rating_deviation(tmp_path):
    """Verify a completion lowers the completed task deviation."""
    csv_path = _copy_fixture(TWO_RATINGS_FROZEN_CSV, tmp_path)

    before, after = _completed_field_before_and_after(csv_path, 1, "rating_deviation")

    assert after < before


def test_task_done_lowers_opponent_rating_deviation(tmp_path):
    """Verify a completion lowers the opponent deviation."""
    csv_path = _copy_fixture(TWO_RATINGS_FROZEN_CSV, tmp_path)

    before, after = _field_before_and_after_completion(csv_path, 1, 2, "rating_deviation")

    assert after < before


def test_task_done_drops_completed_deviation_more_than_one_point(tmp_path):
    """Verify the completed deviation drop exceeds the placeholder."""
    csv_path = _copy_fixture(TWO_RATINGS_FROZEN_CSV, tmp_path)

    before, after = _completed_field_before_and_after(csv_path, 1, "rating_deviation")

    assert before - after > 1


def test_task_done_sets_completed_rating_to_simultaneous_value(tmp_path):
    """Verify the completed rating matches a simultaneous Glicko update."""
    csv_path = _copy_fixture(TWO_RATINGS_FROZEN_CSV, tmp_path)

    response = _complete(csv_path, 1)

    assert response.json()["rating"] == 1367


def test_task_done_changes_solo_rating(tmp_path):
    """Verify completing a solo task changes its rating."""
    csv_path = _copy_fixture(GLICKO_SOLO_CSV, tmp_path)

    before, after = _field_before_and_after_completion(csv_path, 1, 1, "rating")

    assert after != before


def test_task_done_updates_rating_date_anchor(tmp_path):
    """Verify a completion moves the completed task's rating anchor to today."""
    csv_path = _copy_fixture(TWO_RATINGS_CSV, tmp_path)

    _complete(csv_path, 1)

    task = io.get_task_by_id(1, csv_path)
    assert task.rating_date == date.today()


def test_empty_description_for_unknown_task_returns_404(tmp_path):
    """An unknown task answers 404 before its empty text is refused."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)

    response = _patch_description(csv_path, 999, "")

    assert response.status_code == 404


def test_malformed_description_body_returns_error_field(tmp_path):
    """A body without the text is refused with the shared error envelope."""
    csv_path = _copy_fixture(THREE_TASKS_CSV, tmp_path)

    response = _patch_description_body(csv_path, 2, {})

    assert "error" in response.json()


def test_openapi_task_collection_declares_a_response_schema():
    """Verify GET /api/task/ declares a non-empty 200 response schema."""
    document = client.get("/api/openapi.json").json()

    assert _read_response_schema(document, "/api/task/")


def test_openapi_task_detail_declares_a_response_schema():
    """Verify GET /api/task/{task_id} declares a non-empty 200 response schema."""
    document = client.get("/api/openapi.json").json()

    assert _read_response_schema(document, "/api/task/{task_id}")
