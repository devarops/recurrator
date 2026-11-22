from conftest import client

TASKS_CSV = "tests/data/test_three_tasks.csv"
CONTEXTS_CSV = "tests/data/acceptance_context_views_all_contexts.csv"


def test_all_contexts_are_listed():
    """The collection lists every stored context, including one no task names."""
    response = client.get(f"/api/context/?csv={TASKS_CSV}&contexts_csv={CONTEXTS_CSV}")

    assert response.status_code == 200

    assert response.json() == ["casa", "chores", "garden"]
