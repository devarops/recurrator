from datetime import date

from conftest import client

TASKS_CSV = "tests/data/test_three_tasks.csv"
CONTEXTS_CSV = "tests/data/acceptance_context_views_all_contexts.csv"


def _contexts_url(path, contexts_csv=CONTEXTS_CSV, csv=TASKS_CSV):
    """Build a context API URL with the optional task and context file parameters."""
    parameters = []
    if csv:
        parameters.append(f"csv={csv}")
    if contexts_csv:
        parameters.append(f"contexts_csv={contexts_csv}")
    return f"/api/{path}?" + "&".join(parameters)


def test_all_contexts_are_listed():
    """The collection lists every stored context, including one no task names."""
    response = client.get(_contexts_url("context/"))

    assert response.status_code == 200

    assert response.json() == ["casa", "chores", "garden"]


def test_contexts_csv_selects_the_context_file():
    """The collection returns the IDs from the file named by contexts_csv."""
    acceptance = client.get(_contexts_url("context/"))
    shared = client.get(_contexts_url("context/", "tests/data/contexts.csv", csv=None))

    assert acceptance.json() == ["casa", "chores", "garden"]
    assert shared.json() == ["casa", "chores", "laptop"]


def test_due_contexts_are_listed_for_a_date():
    """The dated due read lists contexts with a due task and excludes the rest."""
    response = client.get(_contexts_url("context/due/2026-05-01"))

    assert response.status_code == 200

    assert response.json() == ["casa", "chores"]


def test_undated_due_read_uses_today():
    """The undated due read matches the dated read for today."""
    dated = client.get(_contexts_url(f"context/due/{date.today().isoformat()}"))
    undated = client.get(_contexts_url("context/due/"))

    assert undated.json() == dated.json()


def test_due_read_without_trailing_slash_redirects():
    """The slashless due read redirects to the trailing-slash form."""
    response = client.get(
        _contexts_url("context/due"),
        follow_redirects=False,
    )

    assert response.status_code == 307

    assert "/api/context/due/" in response.headers["location"]

    assert response.content == b""
