from conftest import _read_task_ids, client


def test_all_tasks_are_listed():
    """The collection lists every ID in file order, including the future task."""
    response = _read_task_ids("tests/data/acceptance_tasks_views_all_tasks.csv")

    assert response.status_code == 200

    assert response.json() == [7, 2, 9]


def test_date_query_parameter_is_ignored():
    """A date query does not narrow the task collection."""
    csv_path = "tests/data/acceptance_tasks_views_all_tasks.csv"

    undated = _read_task_ids(csv_path)
    dated = client.get(f"/api/task/?csv={csv_path}&date=2026-01-01")

    assert undated.status_code == 200

    assert dated.status_code == 200

    assert dated.json() == undated.json()

    assert dated.json() == [7, 2, 9]
