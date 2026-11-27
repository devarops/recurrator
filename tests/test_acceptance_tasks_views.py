from datetime import date

from conftest import (
    client,
    _assert_redirect_to_trailing_slash,
    _copy_fixture,
    _read_due_task_ids,
    _read_task_body,
    _read_task_ids,
)

TASKS_VIEWS_CSV = "tests/data/acceptance_tasks_views_all_tasks.csv"
CONTEXT_FILTER_CSV = "tests/data/acceptance_tasks_views_context_filter_returns_matching_tasks.csv"
EMPTY_CONTEXT_FILTER_CSV = "tests/data/acceptance_tasks_views_empty_context_filter_is_rejected.csv"
UNKNOWN_CONTEXT_FILTER_CSV = (
    "tests/data/acceptance_tasks_views_unknown_context_filter_returns_404.csv"
)
UNUSED_CONTEXT_FILTER_CSV = (
    "tests/data/acceptance_tasks_views_unused_context_filter_is_empty.csv"
)
MULTIPLE_CONTEXTS_CSV = "tests/data/acceptance_tasks_views_multiple_contexts_are_unioned.csv"
DUPLICATE_CONTEXTS_CSV = "tests/data/acceptance_tasks_views_duplicate_contexts_collapse.csv"
SHARED_CONTEXTS_CSV = "tests/data/contexts.csv"


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
    _assert_redirect_to_trailing_slash(f"/api/task/due?csv={TASKS_VIEWS_CSV}", "/api/task/due/")


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


def test_context_filter_returns_matching_tasks():
    """One context selects every task naming it, once each, in file order."""
    all_task_ids = _read_task_ids(CONTEXT_FILTER_CSV).json()
    details = {task_id: _read_task_body(CONTEXT_FILTER_CSV, task_id) for task_id in all_task_ids}
    requested_context = "chores"

    expected = [
        task_id for task_id in all_task_ids if requested_context in details[task_id]["contexts"]
    ]
    excluded = [
        task_id for task_id in all_task_ids if requested_context not in details[task_id]["contexts"]
    ]
    naming_several_contexts = [
        task_id for task_id in expected if len(details[task_id]["contexts"]) > 1
    ]

    response = _read_task_ids(CONTEXT_FILTER_CSV, [requested_context], SHARED_CONTEXTS_CSV)

    assert response.status_code == 200

    returned = response.json()
    assert returned == expected
    assert expected
    assert excluded
    assert naming_several_contexts
    for task_id in naming_several_contexts:
        assert returned.count(task_id) == 1


def test_multiple_contexts_are_unioned():
    """Several contexts select their OR-union once each, in file order."""
    requested_contexts = {"casa", "chores"}
    task_ids = _read_task_ids(MULTIPLE_CONTEXTS_CSV).json()
    details = {task_id: _read_task_body(MULTIPLE_CONTEXTS_CSV, task_id) for task_id in task_ids}

    expected = [
        task_id for task_id in task_ids if requested_contexts & set(details[task_id]["contexts"])
    ]
    excluded = [
        task_id
        for task_id in task_ids
        if not requested_contexts & set(details[task_id]["contexts"])
    ]
    in_every_requested_context = [
        task_id for task_id in task_ids if requested_contexts <= set(details[task_id]["contexts"])
    ]
    per_context = set().union(
        *(
            _read_task_ids(MULTIPLE_CONTEXTS_CSV, [context], SHARED_CONTEXTS_CSV).json()
            for context in sorted(requested_contexts)
        )
    )

    response = _read_task_ids(
        MULTIPLE_CONTEXTS_CSV, sorted(requested_contexts), SHARED_CONTEXTS_CSV
    )

    assert response.status_code == 200

    returned = response.json()
    assert returned == expected
    assert excluded
    assert in_every_requested_context
    assert set(returned) == per_context
    for task_id in in_every_requested_context:
        assert returned.count(task_id) == 1


def test_duplicate_contexts_collapse():
    """Repeating a context returns the same tasks as naming it once."""
    requested_context = "chores"

    single = _read_task_ids(DUPLICATE_CONTEXTS_CSV, [requested_context], SHARED_CONTEXTS_CSV)
    repeated = _read_task_ids(
        DUPLICATE_CONTEXTS_CSV,
        [requested_context, requested_context],
        SHARED_CONTEXTS_CSV,
    )

    assert single.status_code == 200
    assert repeated.status_code == 200

    expected = single.json()
    assert expected
    assert repeated.json() == expected
    assert len(expected) == len(set(expected))


def test_unknown_context_filter_returns_404():
    """The collection refuses a context the context data does not store."""
    known = client.get(
        f"/api/task/?csv={UNKNOWN_CONTEXT_FILTER_CSV}"
        f"&contexts_csv={SHARED_CONTEXTS_CSV}&context=chores"
    )
    unknown = client.get(
        f"/api/task/?csv={UNKNOWN_CONTEXT_FILTER_CSV}"
        f"&contexts_csv={SHARED_CONTEXTS_CSV}&context=garden"
    )

    assert known.status_code == 200
    assert known.json()

    assert unknown.status_code == 404
    assert "error" in unknown.json()


def test_unused_context_filter_is_empty():
    """A stored context that no task names selects no task rather than 404."""
    requested_context = "laptop"
    used_context = "chores"
    stored_contexts = client.get(
        f"/api/context/?csv={UNUSED_CONTEXT_FILTER_CSV}"
        f"&contexts_csv={SHARED_CONTEXTS_CSV}"
    )

    assert stored_contexts.status_code == 200
    assert requested_context in stored_contexts.json()

    task_ids = _read_task_ids(UNUSED_CONTEXT_FILTER_CSV).json()
    details = {
        task_id: _read_task_body(UNUSED_CONTEXT_FILTER_CSV, task_id) for task_id in task_ids
    }
    assert task_ids
    assert all(requested_context not in details[task_id]["contexts"] for task_id in task_ids)
    assert any(used_context in details[task_id]["contexts"] for task_id in task_ids)

    response = _read_task_ids(
        UNUSED_CONTEXT_FILTER_CSV, [requested_context], SHARED_CONTEXTS_CSV
    )
    used = _read_task_ids(UNUSED_CONTEXT_FILTER_CSV, [used_context], SHARED_CONTEXTS_CSV)

    assert used.status_code == 200
    assert used.json()

    assert response.status_code == 200
    assert response.json() == []


def test_empty_context_filter_is_rejected():
    """An empty context on the collection read is refused with an error message."""
    all_task_ids = _read_task_ids(EMPTY_CONTEXT_FILTER_CSV).json()
    valid_context = "chores"
    valid_read = _read_task_ids(EMPTY_CONTEXT_FILTER_CSV, [valid_context], SHARED_CONTEXTS_CSV)

    response = _read_task_ids(EMPTY_CONTEXT_FILTER_CSV, [""])

    assert valid_read.status_code == 200
    assert set(valid_read.json()) < set(all_task_ids)

    assert response.status_code == 422
    assert "error" in response.json()


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


def test_empty_context_in_due_read_is_rejected(tmp_path):
    """An empty context on a dated due read is refused without any write."""
    csv_path = _copy_fixture(
        "tests/data/acceptance_tasks_views_empty_context_in_due_read_is_rejected.csv",
        tmp_path,
    )
    task_ids = range(1, 9)
    before = _scheduling_state(csv_path, task_ids)

    response = _read_due_task_ids(csv_path, "2026-01-01", [""])

    assert response.status_code == 422
    assert "error" in response.json()
    assert _scheduling_state(csv_path, task_ids) == before


def test_multi_context_due_read_is_read_only(tmp_path):
    """A multiple-context due read unions the due tasks without deferring any."""
    csv_path = _copy_fixture(
        "tests/data/acceptance_tasks_views_multi_context_due_read_is_read_only.csv",
        tmp_path,
    )
    reference_date = "2026-01-01"
    requested_contexts = {"chores", "work"}
    task_ids = _read_task_ids(csv_path).json()
    before = _scheduling_state(csv_path, task_ids)

    details = {task_id: _read_task_body(csv_path, task_id, reference_date) for task_id in task_ids}
    due_ids = [task_id for task_id in task_ids if details[task_id]["due_date"] <= reference_date]
    contexts_by_task = {task_id: set(details[task_id]["contexts"]) for task_id in task_ids}
    expected = [task_id for task_id in due_ids if requested_contexts & contexts_by_task[task_id]]
    due_outside = [
        task_id for task_id in due_ids if not requested_contexts & contexts_by_task[task_id]
    ]
    due_in_every_context = [
        task_id for task_id in due_ids if requested_contexts <= contexts_by_task[task_id]
    ]

    response = _read_due_task_ids(csv_path, reference_date, sorted(requested_contexts))

    assert response.status_code == 200

    returned = response.json()
    assert returned == expected
    assert due_outside
    assert not set(returned) & set(due_outside)
    assert due_in_every_context
    for task_id in due_in_every_context:
        assert returned.count(task_id) == 1
    assert _scheduling_state(csv_path, task_ids) == before
