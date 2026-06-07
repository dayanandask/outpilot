import pytest
import respx
from httpx import Response
from typer.testing import CliRunner
from pipeline.main import app

runner = CliRunner()


def test_run_help() -> None:
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0


def test_invalid_domain_exits() -> None:
    result = runner.invoke(app, ["run", "not-a-domain"])
    assert result.exit_code == 1


def test_list_runs_empty() -> None:
    result = runner.invoke(app, ["list-runs"])
    assert result.exit_code == 0


@respx.mock
def test_full_pipeline_dry_run() -> None:
    respx.post("https://api.apollo.io/v1/organizations/search").mock(
        return_value=Response(200, json={"organizations": [{"name": "Stripe", "domain": "stripe.com"}]})
    )
    respx.post("https://api.apollo.io/v1/mixed_people/search").mock(
        return_value=Response(200, json={"people": [{"name": "Patrick Collison", "title": "CEO", "linkedin_url": "https://linkedin.com/in/patrick", "id": "person_1"}]})
    )
    respx.post("https://api.prospeo.io/search-person").mock(
        return_value=Response(200, json={"people": []})
    )

    result = runner.invoke(app, ["run", "stripe.com", "--dry-run"])
    assert result.exit_code == 0
    assert "Pipeline complete" in result.output
