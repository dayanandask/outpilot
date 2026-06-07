import pytest
import respx
from httpx import Response
from pipeline.models import Prospect
from pipeline.stages.s2_email import EmailStage


@pytest.fixture
def prospect() -> Prospect:
    return Prospect(
        company_domain="example.com",
        full_name="Jane Doe",
        title="Chief Executive Officer",
        linkedin_url="https://www.linkedin.com/in/jane",
    )


@pytest.mark.asyncio
@respx.mock
async def test_email_stage_prospeo_fallback(prospect: Prospect) -> None:
    respx.post("https://api.prospeo.io/search-person").mock(
        return_value=Response(200, json={"people": [{"full_name": "Jane Doe", "id": "prospeo_1"}]})
    )
    respx.post("https://api.prospeo.io/enrich-person").mock(
        return_value=Response(200, json={"person": {"email": {"value": "jane@example.com", "type": "professional"}}})
    )

    stage = EmailStage()
    contacts = await stage.execute([prospect])

    assert len(contacts) == 1
    assert contacts[0].work_email == "jane@example.com"

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_email_stage_skips_unresolvable(prospect: Prospect) -> None:
    respx.post("https://api.prospeo.io/search-person").mock(
        return_value=Response(200, json={"people": []})
    )

    stage = EmailStage()
    contacts = await stage.execute([prospect])

    assert contacts == []

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_email_stage_deduplicates(prospect: Prospect) -> None:
    duplicate = Prospect(
        company_domain="example.com",
        full_name="Jane D",
        title="Chief Executive Officer",
        linkedin_url="https://www.linkedin.com/in/jane2",
    )

    respx.post("https://api.prospeo.io/search-person").mock(
        return_value=Response(200, json={"people": [{"full_name": "Jane Doe", "id": "prospeo_1"}]})
    )
    respx.post("https://api.prospeo.io/enrich-person").mock(
        return_value=Response(200, json={"person": {"email": {"value": "jane@example.com", "type": "professional"}}})
    )

    stage = EmailStage()
    contacts = await stage.execute([prospect, duplicate])

    assert len(contacts) == 1
    assert contacts[0].work_email == "jane@example.com"

    await stage.close()


@pytest.mark.asyncio
async def test_email_stage_partial_failure(prospect: Prospect) -> None:
    from unittest.mock import patch

    stage = EmailStage()
    with patch.object(stage.client, "search_person", side_effect=Exception("network error")):
        contacts = await stage.execute([prospect])

    assert contacts == []
