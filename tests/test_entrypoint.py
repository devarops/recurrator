import json
import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ["create_config.sh", "create_contexts.sh", "entrypoint.sh"]


def _write_fixture_data(config_dir: Path) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(
        json.dumps(
            {
                "api_base_url": "http://api:8000",
                "default_recurrence_days": 14,
                "default_tasks_csv_path": "/root/.config/recurrator/tasks.csv",
                "min_days_gap": 2,
                "wip_limit": 9,
            }
        )
    )
    (config_dir / "datapackage.json").write_text(
        json.dumps(
            {
                "resources": [
                    {
                        "schema": {
                            "fields": [
                                {
                                    "name": "context",
                                    "constraints": {"enum": ["casa", "mandado"]},
                                }
                            ]
                        }
                    }
                ]
            }
        )
    )


def _copy_scripts(repo: Path) -> None:
    (repo / "src").mkdir(parents=True)
    (repo / "recurrator").mkdir()
    for name in SCRIPTS:
        destination = repo / "src" / name
        shutil.copy2(REPO_ROOT / "src" / name, destination)
        os.chmod(destination, 0o755)


def test_entrypoint_generates_modules_and_executes_command(tmp_path):
    """The entrypoint must generate both modules before running the command."""
    repo = tmp_path / "repo"
    _copy_scripts(repo)

    config_dir = tmp_path / "config"
    _write_fixture_data(config_dir)

    result = subprocess.run(
        [str(repo / "src" / "entrypoint.sh"), "echo", "command-ran"],
        cwd=repo,
        env={**os.environ, "RECURRATOR_CONFIG_DIR": str(config_dir)},
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "command-ran"
    assert "WIP_LIMIT = 9" in (repo / "recurrator" / "_config.py").read_text()
    assert 'MANDADO = "mandado"' in (repo / "recurrator" / "_contexts.py").read_text()
