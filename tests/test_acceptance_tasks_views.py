from datetime import date

from conftest import client, _copy_fixture, _read_due_task_ids, _read_task_body, _read_task_ids

TASKS_VIEWS_CSV = "tests/data/acceptance_tasks_views_all_tasks.csv"


def _scheduling_state(csv_path, task_ids):
    """Return each task's skip count and due date."""
    state = {}
    for task_id in task_ids:
        task = _read_task_body(csv_path, task_id)
        state[task_id] = {
            "skip_count": task["skip_count"],
            "due_date": task["due_date"],
        }
    return state


def test_all_tasks_are_listed():
    """The collection lists every ID in file order, including the future task."""
    response = _read_task_ids(TASKS_VIEWS_CSV)

    assert response.status_code == 200

    assert response.json() == [7, 2, 9]


def test_due_read_without_trailing_slash_redirects():
    """The slashless due read redirects and returns no task IDs."""
    response = client.get(
        f"/api/task/due?csv={TASKS_VIEWS_CSV}", follow_redirects=False
    )

    assert response.status_code == 307
    assert "/api/task/due/" in response.headers["location"]
    assert response.content == b""


def test_due_tasks_are_listed_for_a_date():
    """A dated due read returns the due IDs and excludes the later task."""
    response = _read_due_task_ids(TASKS_VIEWS_CSV, "2026-01-01")

    assert response.status_code == 200

    assert response.json() == [7, 9]


def test_undated_due_read_uses_today():
    """The undated due read matches the dated read for today."""
    dated = _read_due_task_ids(TASKS_VIEWS_CSV, date.today().isoformat())
    undated = client.get(f"/api/task/due/?csv={TASKS_VIEWS_CSV}")

    assert undated.status_code == 200

    assert undated.json() == dated.json()


def test_no_context_due_read_is_read_only(tmp_path):
    """A due read without a context writes no skip count or skip date."""
    csv_path = _copy_fixture(TASKS_VIEWS_CSV, tmp_path)
    task_ids = (7, 2, 9)
    before = _scheduling_state(csv_path, task_ids)

    response = _read_due_task_ids(csv_path, "2026-01-01")

    assert response.status_code == 200

    assert response.json() == [7, 9]
    assert _scheduling_state(csv_path, task_ids) == before


def test_duplicate_contexts_collapse_in_due_read(tmp_path):
    """A repeated context applies the single-context deferral rules."""
    csv_path = _copy_fixture(
        "tests/data/acceptance_tasks_views_duplicate_contexts_collapse_in_due_read.csv",
        tmp_path,
    )
    task_ids = range(1, 11)
    before = _scheduling_state(csv_path, task_ids)

    response = _read_due_task_ids(csv_path, "2026-01-01", ["chores", "chores"])

    assert response.status_code == 200

    returned = response.json()
    assert set(returned) < set(task_ids)
    after = _scheduling_state(csv_path, task_ids)
    deferred = set(task_ids) - set(returned)
    assert deferred
    for task_id in deferred:
        assert after[task_id]["skip_count"] == before[task_id]["skip_count"] + 1
    for task_id in returned:
        assert after[task_id]["skip_count"] == before[task_id]["skip_count"]
