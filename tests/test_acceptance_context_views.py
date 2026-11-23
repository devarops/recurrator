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


def _assert_slashless_read_redirects(path, target_path):
    """Assert a slashless context read redirects to its trailing-slash form."""
    response = client.get(_contexts_url(path), follow_redirects=False)

    assert response.status_code == 307
    assert target_path in response.headers["location"]
    assert response.content == b""


def test_due_read_without_trailing_slash_redirects():
    """The slashless due read redirects to the trailing-slash form."""
    _assert_slashless_read_redirects("context/due", "/api/context/due/")


def test_context_detail_reports_its_fields():
    """The detail route returns the context fields and sorted scopes."""
    response = client.get(
        _contexts_url(
            "context/garden/",
            "tests/data/acceptance_context_views_context_detail.csv",
        )
    )

    assert response.status_code == 200

    assert response.json() == {
        "id": "garden",
        "display_name": "Garden",
        "description": "Outdoor upkeep: beds, hedges, and the watering schedule.",
        "scopes": ["personal", "work"],
    }


def test_context_detail_lists_an_unused_context():
    """The detail route returns a context that no task names."""
    response = client.get(_contexts_url("context/garden/"))

    assert response.status_code == 200

    assert response.json()["id"] == "garden"

    assert response.json()["scopes"] == ["personal", "work"]


def test_unknown_context_returns_404():
    """The detail route returns 404 with an error message for an unknown context."""
    response = client.get(_contexts_url("context/missing/"))

    assert response.status_code == 404

    assert "error" in response.json()


def test_context_detail_without_trailing_slash_redirects():
    """The slashless detail read redirects to the trailing-slash form."""
    _assert_slashless_read_redirects("context/garden", "/api/context/garden/")
