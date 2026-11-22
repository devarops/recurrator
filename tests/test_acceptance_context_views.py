from datetime import date

from conftest import client

TASKS_CSV = "tests/data/test_three_tasks.csv"
CONTEXTS_CSV = "tests/data/acceptance_context_views_all_contexts.csv"


def test_all_contexts_are_listed():
    """The collection lists every stored context, including one no task names."""
    response = client.get(f"/api/context/?csv={TASKS_CSV}&contexts_csv={CONTEXTS_CSV}")

    assert response.status_code == 200

    assert response.json() == ["casa", "chores", "garden"]


def test_contexts_csv_selects_the_context_file():
    """The collection returns the IDs from the file named by contexts_csv."""
    acceptance = client.get(
        f"/api/context/?csv={TASKS_CSV}&contexts_csv={CONTEXTS_CSV}"
    )
    shared = client.get("/api/context/?contexts_csv=tests/data/contexts.csv")

    assert acceptance.json() == ["casa", "chores", "garden"]
    assert shared.json() == ["casa", "chores", "laptop"]


def test_due_contexts_are_listed_for_a_date():
    """The dated due read lists contexts with a due task and excludes the rest."""
    response = client.get(
        f"/api/context/due/2026-05-01?csv={TASKS_CSV}&contexts_csv={CONTEXTS_CSV}"
    )

    assert response.status_code == 200

    assert response.json() == ["casa", "chores"]


def test_undated_due_read_uses_today():
    """The undated due read matches the dated read for today."""
    dated = client.get(
        f"/api/context/due/{date.today().isoformat()}"
        f"?csv={TASKS_CSV}&contexts_csv={CONTEXTS_CSV}"
    )
    undated = client.get(
        f"/api/context/due/?csv={TASKS_CSV}&contexts_csv={CONTEXTS_CSV}"
    )

    assert undated.json() == dated.json()
