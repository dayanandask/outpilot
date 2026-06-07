from typer.testing import CliRunner
from pipeline.main import app

runner = CliRunner()


def test_cli_help_commands() -> None:
    for cmd in [["run", "--help"], ["status", "--help"], ["list-runs", "--help"]]:
        result = runner.invoke(app, cmd)
        assert result.exit_code == 0


def test_status_not_found() -> None:
    result = runner.invoke(app, ["status", "nonexistent_run_id"])
    assert result.exit_code == 0
    assert "not found" in result.output.lower()


def test_run_dry_run_invalid_domain() -> None:
    result = runner.invoke(app, ["run", "not-a-domain"])
    assert result.exit_code == 1
