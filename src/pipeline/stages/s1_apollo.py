import re
from typing import List, Tuple
from pipeline.stages.base import BaseStage
from pipeline.models import SeedInput, Company, Prospect
from pipeline.clients.apollo import ApolloClient
from pipeline.clients.prospeo import ProspeoClient
from pipeline.config import settings
import structlog

logger = structlog.get_logger(__name__)

TITLE_REGEX = re.compile(r'\b(CEO|CTO|CFO|COO|CMO|CPO|VP|Vice President|Director|Head)\b', re.IGNORECASE)

class ApolloStage(BaseStage):
    name = "apollo"

    def __init__(self) -> None:
        self.apollo = ApolloClient()
        self.prospeo = ProspeoClient()

    async def run(self, inputs: List[SeedInput]) -> Tuple[List[Company], List[Prospect]]:
        all_companies: List[Company] = []
        all_prospects: List[Prospect] = []

        for seed in inputs:
            try:
                orgs = await self.apollo.search_organizations(seed.domain, max_results=settings.max_lookalikes)
                if not orgs:
                    logger.warning("no_organization_found", domain=seed.domain)
                    continue

                org = orgs[0]
                company = Company(
                    domain=seed.domain,
                    name=org.get("name") or seed.domain.split(".")[0].capitalize(),
                    source="apollo_io",
                )
                all_companies.append(company)

                people = []
                try:
                    people = await self.apollo.search_people(seed.domain)
                except Exception as people_err:
                    logger.warning(
                        "apollo_people_search_failed",
                        domain=seed.domain,
                        error=str(people_err),
                    )
                    # Fallback to Prospeo if Apollo fails (e.g. 403 on free tier)
                    try:
                        logger.info("falling_back_to_prospeo_for_people", domain=seed.domain)
                        people = await self.prospeo.search_person(seed.domain)
                    except Exception as prospeo_err:
                        logger.warning("prospeo_people_search_failed", domain=seed.domain, error=str(prospeo_err))
                        continue

                prospects_found = 0

                for person in people:
                    if prospects_found >= settings.max_prospects_per_domain:
                        break

                    title = person.get("title", "")
                    if not title or not TITLE_REGEX.search(title):
                        continue

                    full_name = person.get("name") or person.get("full_name") or f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
                    if not full_name:
                        continue

                    try:
                        prospect = Prospect(
                            company_domain=seed.domain,
                            full_name=full_name,
                            title=title,
                            linkedin_url=person.get("linkedin_url", ""),
                            apollo_email=person.get("email"),
                        )
                        all_prospects.append(prospect)
                        prospects_found += 1
                    except Exception as e:
                        await self.on_error(person, e)

            except Exception as e:
                await self.on_error(seed.domain, e)

        return all_companies, all_prospects

    async def close(self) -> None:
        await self.apollo.close()
        await self.prospeo.close()
