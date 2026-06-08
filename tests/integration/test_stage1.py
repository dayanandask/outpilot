import pytest
import respx
from httpx import Response
from pipeline.models import SeedInput
from pipeline.stages.s1_apollo import ApolloStage


@pytest.mark.asyncio
@respx.mock
async def test_apollo_stage_happy_path() -> None:
    respx.post("https://api.apollo.io/v1/organizations/search").mock(
        return_value=Response(
            200,
            json={"organizations": [{"name": "Stripe", "domain": "stripe.com"}]},
        )
    )
    respx.post("https://api.apollo.io/v1/mixed_people/search").mock(
        return_value=Response(
            200,
            json={
                "people": [
                    {
                        "name": "Patrick Collison",
                        "title": "CEO",
                        "linkedin_url": "https://linkedin.com/in/patrick",
                        "id": "person_1",
                    }
                ]
            },
        )
    )

    stage = ApolloStage()
    inputs = [SeedInput(domain="stripe.com")]
    companies, prospects = await stage.execute(inputs)

    assert len(companies) == 1
    assert companies[0].name == "Stripe"
    assert len(prospects) == 1
    assert prospects[0].full_name == "Patrick Collison"

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_apollo_stage_falls_back_to_prospeo() -> None:
    respx.post("https://api.apollo.io/v1/organizations/search").mock(
        return_value=Response(
            200,
            json={"organizations": [{"name": "Acme", "domain": "acme.com"}]},
        )
    )
    respx.post("https://api.apollo.io/v1/mixed_people/search").mock(
        return_value=Response(403, json={"error": "blocked"})
    )
    respx.post("https://api.prospeo.io/search-person").mock(
        return_value=Response(
            200,
            json={
                "people": [
                    {
                        "name": "Priya Nair",
                        "title": "CTO",
                        "linkedin_url": "https://linkedin.com/in/priya",
                        "id": "prospeo_1",
                    }
                ]
            },
        )
    )

    stage = ApolloStage()
    inputs = [SeedInput(domain="acme.com")]
    companies, prospects = await stage.execute(inputs)

    assert len(companies) == 1
    assert len(prospects) == 1
    assert prospects[0].full_name == "Priya Nair"

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_apollo_stage_empty_results() -> None:
    respx.post("https://api.apollo.io/v1/organizations/search").mock(
        return_value=Response(200, json={"organizations": []})
    )

    stage = ApolloStage()
    inputs = [SeedInput(domain="unknown.com")]
    companies, prospects = await stage.execute(inputs)

    assert companies == []
    assert prospects == []

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_apollo_stage_both_people_searches_fail() -> None:
    respx.post("https://api.apollo.io/v1/organizations/search").mock(
        return_value=Response(
            200,
            json={"organizations": [{"name": "Acme", "domain": "acme.com"}]},
        )
    )
    respx.post("https://api.apollo.io/v1/mixed_people/search").mock(
        return_value=Response(403, json={"error": "blocked"})
    )
    respx.post("https://api.prospeo.io/search-person").mock(
        return_value=Response(403, json={"error": "rate limited"})
    )

    stage = ApolloStage()
    inputs = [SeedInput(domain="acme.com")]
    companies, prospects = await stage.execute(inputs)

    assert len(companies) == 1
    assert prospects == []

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_apollo_stage_skips_non_decision_makers() -> None:
    respx.post("https://api.apollo.io/v1/organizations/search").mock(
        return_value=Response(
            200,
            json={"organizations": [{"name": "Acme", "domain": "acme.com"}]},
        )
    )
    respx.post("https://api.apollo.io/v1/mixed_people/search").mock(
        return_value=Response(
            200,
            json={
                "people": [
                    {
                        "name": "John Intern",
                        "title": "Software Engineer Intern",
                        "linkedin_url": "https://linkedin.com/in/john",
                        "id": "person_1",
                    }
                ]
            },
        )
    )

    stage = ApolloStage()
    inputs = [SeedInput(domain="acme.com")]
    companies, prospects = await stage.execute(inputs)

    assert len(companies) == 1
    assert prospects == []

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_apollo_stage_respects_max_prospects_limit() -> None:
    respx.post("https://api.apollo.io/v1/organizations/search").mock(
        return_value=Response(
            200,
            json={"organizations": [{"name": "BigCorp", "domain": "bigcorp.com"}]},
        )
    )
    respx.post("https://api.apollo.io/v1/mixed_people/search").mock(
        return_value=Response(
            200,
            json={
                "people": [
                    {
                        "name": "Person 1",
                        "title": "CEO",
                        "linkedin_url": "https://linkedin.com/in/p1",
                    },
                    {
                        "name": "Person 2",
                        "title": "CTO",
                        "linkedin_url": "https://linkedin.com/in/p2",
                    },
                    {
                        "name": "Person 3",
                        "title": "CFO",
                        "linkedin_url": "https://linkedin.com/in/p3",
                    },
                ]
            },
        )
    )

    stage = ApolloStage()
    inputs = [SeedInput(domain="bigcorp.com")]
    companies, prospects = await stage.execute(inputs)

    assert len(companies) == 1
    assert len(prospects) == 3

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_apollo_stage_skips_person_without_name() -> None:
    respx.post("https://api.apollo.io/v1/organizations/search").mock(
        return_value=Response(
            200,
            json={
                "organizations": [{"name": "NoNameCorp", "domain": "nonamecorp.com"}]
            },
        )
    )
    respx.post("https://api.apollo.io/v1/mixed_people/search").mock(
        return_value=Response(
            200,
            json={
                "people": [
                    {
                        "name": "",
                        "first_name": "",
                        "last_name": "",
                        "title": "CEO",
                        "linkedin_url": "https://linkedin.com/in/noname",
                    }
                ]
            },
        )
    )

    stage = ApolloStage()
    inputs = [SeedInput(domain="nonamecorp.com")]
    companies, prospects = await stage.execute(inputs)

    assert len(companies) == 1
    assert prospects == []

    await stage.close()
