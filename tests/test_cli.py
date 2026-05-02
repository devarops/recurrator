from recurrator.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_list_all_help():
    result = runner.invoke(app, ["list-all", "--help"])
    assert result.exit_code == 0

def test_list_all():
    result = runner.invoke(app, ["list-all"])
    assert result.exit_code == 0
    # Verify that the output contains expected task information (id, description, context, etc.)
    assert "id" in result.stdout
    assert "8" in result.stdout  # ID of the single task in the test CSV
