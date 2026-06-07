from typing import Dict, Any
from pipeline.clients.base import BaseAPIClient
from pipeline.config import settings, mask_key
import structlog

logger = structlog.get_logger(__name__)


class BrevoClient(BaseAPIClient):
    """Client for Brevo Transactional Email API."""

    def __init__(self) -> None:
        super().__init__(
            base_url="https://api.brevo.com/v3",
            stage_name="brevo",
            requests_per_minute=100,
            headers={
                "api-key": settings.brevo_api_key,
                "Content-Type": "application/json",
            },
        )

    async def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """Sends a single transactional email via Brevo.

        Args:
            to_email: Recipient email address.
            to_name: Recipient name.
            subject: Email subject line.
            body: Plain text email body.

        Returns:
            JSON response from Brevo containing messageId and other details.

        Raises:
            AuthError: If 401/403 response is received.
            RuntimeError: If the send fails after retries.
        """
        payload: Dict[str, Any] = {
            "sender": {
                "email": settings.from_email,
                "name": settings.from_name,
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name,
                }
            ],
            "subject": subject,
            "textContent": body,
        }

        response = await self.request("POST", "/smtp/email", json=payload)
        data = response.json()
        message_id = data.get("messageId")
        logger.info(
            "brevo_email_sent",
            stage=self.stage_name,
            to=mask_key(to_email),
            message_id=message_id,
        )
        return data  # type: ignore[no-any-return]

    async def get_daily_sent_count(self) -> int:
        """Returns the number of outreach records sent today.

        Note:
            This is a best-effort count based on DB records for this run_id/pipeline execution.
            In this prototype, the orchestrator tracks daily counts via DB query.
        """
        return 0
