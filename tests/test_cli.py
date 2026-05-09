from recurrator.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_help():
    """Smoke test: CLI help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_list_all_help():
    """Smoke test: list-all-tasks help works."""
    result = runner.invoke(app, ["list-all-tasks", "--help"])
    assert result.exit_code == 0


def test_list_all():
    """Smoke test: list-all-tasks command executes and returns data."""
    result = runner.invoke(app, ["list-all-tasks", "--csv", "tests/data/test_single_task.csv"])
    assert result.exit_code == 0
    assert "id" in result.stdout
    assert "8" in result.stdout
