from typer.testing import CliRunner
from pipeline.main import app

runner = CliRunner()


def test_run_help() -> None:
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0


def test_status_help() -> None:
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0


def test_list_runs_help() -> None:
    result = runner.invoke(app, ["list-runs", "--help"])
    assert result.exit_code == 0
