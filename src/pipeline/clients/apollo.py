from typing import Any, Dict, List
from pipeline.clients.base import BaseAPIClient
from pipeline.config import settings


class ApolloClient(BaseAPIClient):
    """Client for Apollo.io API to search organizations and people."""

    def __init__(self) -> None:
        super().__init__(
            base_url="https://api.apollo.io/v1",
            stage_name="apollo_io",
            requests_per_minute=settings.apollo_rpm,
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "x-api-key": settings.apollo_api_key,
            },
        )

    async def search_organizations(
        self, domain: str, max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Searches for organizations similar to domain."""
        payload = {
            "q_organization_domains": domain,
            "page": 1,
            "per_page": max_results,
        }
        response = await self.request(
            "POST",
            "/organizations/search",
            json=payload,
        )
        data = response.json()
        return data.get("organizations", [])  # type: ignore[no-any-return]

    async def search_people(self, domain: str, page: int = 1) -> List[Dict[str, Any]]:
        """Searches for people at a given company domain."""
        payload = {
            "q_organization_domains": domain,
            "page": page,
        }
        response = await self.request(
            "POST",
            "/mixed_people/search",
            json=payload,
        )
        data = response.json()
        return data.get("people", [])  # type: ignore[no-any-return]
