from typing import List
from pipeline.stages.base import BaseStage
from pipeline.models import Prospect, Contact
from pipeline.clients.prospeo import ProspeoClient
import structlog

logger = structlog.get_logger(__name__)


class EmailStage(BaseStage):
    name = "email_resolution"

    def __init__(self) -> None:
        self.client = ProspeoClient()

    async def run(self, inputs: List[Prospect]) -> List[Contact]:
        contacts: List[Contact] = []
        seen_emails = set()

        for prospect in inputs:
            try:
                email: str | None = None
                source: str = "apollo"

                # 1st: Apollo email
                if prospect.apollo_email:
                    email = prospect.apollo_email

                # 2nd: Prospeo enrich fallback
                if not email:
                    source = "prospeo"
                    people = await self.client.search_person(prospect.company_domain)
                    person_id = None
                    for person in people:
                        full_name = person.get("full_name") or f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
                        if full_name.lower() == prospect.full_name.lower():
                            person_id = person.get("id")
                            break
                    
                    if person_id:
                        enriched = await self.client.enrich_person(person_id)
                        if enriched:
                            email = enriched.get("email", {}).get("value")

                # 3rd: skip
                if not email:
                    logger.warning("no_email_resolved", full_name=prospect.full_name)
                    continue

                email_lower = email.lower()
                if email_lower in seen_emails:
                    logger.warning("duplicate_email_skipped", email=email)
                    continue

                seen_emails.add(email_lower)
                contacts.append(
                    Contact(
                        prospect=prospect,
                        work_email=email,
                        verified=True,
                        source=source,
                    )
                )
            except Exception as e:
                logger.warning("email_resolution_failed", full_name=prospect.full_name, error=str(e))
                await self.on_error(prospect, e)

        return contacts

    async def close(self) -> None:
        await self.client.close()
