from typing import Any, Dict, List, Optional
from pipeline.clients.base import BaseAPIClient
from pipeline.config import settings


class ProspeoClient(BaseAPIClient):
    """Client for Prospeo API to find and enrich people."""

    def __init__(self) -> None:
        super().__init__(
            base_url="https://api.prospeo.io",
            stage_name="prospeo",
            requests_per_minute=settings.prospeo_rpm,
            headers={
                "Content-Type": "application/json",
                "X-KEY": settings.prospeo_api_key,
            },
        )

    async def search_person(
        self, domain: str, title_keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for people at a company domain by title keywords."""
        title_keywords = title_keywords or [
            "CEO",
            "CTO",
            "CFO",
            "COO",
            "CMO",
            "CPO",
            "VP",
            "Vice President",
            "Director",
            "Head",
        ]
        payload = {
            "company_domain": domain,
            "title_keywords": title_keywords,
            "limit": settings.max_prospects_per_domain,
        }
        response = await self.request(
            "POST",
            "/search-person",
            json=payload,
        )
        data = response.json()
        return data.get("people", [])  # type: ignore[no-any-return]

    async def enrich_person(self, person_id: str) -> Optional[Dict[str, Any]]:
        """Enrich a person by Prospeo person ID to get email."""
        payload = {
            "person_id": person_id,
        }
        response = await self.request(
            "POST",
            "/enrich-person",
            json=payload,
        )
        data = response.json()
        return data.get("person")  # type: ignore[no-any-return]
