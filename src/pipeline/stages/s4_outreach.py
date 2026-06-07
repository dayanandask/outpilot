from datetime import datetime, timezone
from typing import List, Optional
from pipeline.stages.base import BaseStage
from pipeline.models import Contact, OutreachRecord
from pipeline.clients.brevo import BrevoClient
from pipeline.db import DatabaseManager, OutreachRecordTable
from pipeline.utils.email_copy import EmailTemplateEngine
from pipeline.config import settings, mask_key
import structlog

logger = structlog.get_logger(__name__)


class OutreachStage(BaseStage):
    name = "brevo"

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.client = BrevoClient()
        self.db_manager = db_manager
        self.template_engine = EmailTemplateEngine()
        self.daily_sent = 0
        self.daily_cap = settings.daily_email_cap

    async def run(self, contacts: List[Contact]) -> List[OutreachRecord]:
        records: List[OutreachRecord] = []

        for contact in contacts:
            if self.daily_sent >= self.daily_cap:
                logger.warning(
                    "daily_cap_reached",
                    stage=self.name,
                    sent=self.daily_sent,
                    cap=self.daily_cap,
                )
                break

            try:
                rendered = self.template_engine.render(contact)
                data = await self.client.send_email(
                    to_email=rendered["to"],
                    to_name=rendered["name"],
                    subject=rendered["subject"],
                    body=rendered["body"],
                )
                message_id = data.get("messageId")
                sent_at = datetime.now(timezone.utc)

                record = OutreachRecord(
                    contact=contact,
                    email_subject=rendered["subject"],
                    email_body=rendered["body"],
                    sent_at=sent_at,
                    brevo_message_id=str(message_id) if message_id else None,
                    status="sent",
                )
                records.append(record)
                self.daily_sent += 1

                if self.db_manager:
                    table_rec = OutreachRecordTable(
                        run_id=self.db_manager.run_id,
                        work_email=contact.work_email,
                        email_subject=record.email_subject,
                        email_body=record.email_body,
                        sent_at=sent_at,
                        brevo_message_id=str(message_id) if message_id else None,
                        status="sent",
                    )
                    await self.db_manager.save_outreach_records([table_rec])

            except Exception as e:
                logger.error(
                    "brevo_send_failed",
                    stage=self.name,
                    email=mask_key(contact.work_email),
                    error=str(e),
                )
                await self.on_error(contact, e)

                record = OutreachRecord(
                    contact=contact,
                    email_subject="",
                    email_body="",
                    status="failed",
                )
                records.append(record)

                if self.db_manager:
                    table_rec = OutreachRecordTable(
                        run_id=self.db_manager.run_id,
                        work_email=contact.work_email,
                        email_subject="",
                        email_body="",
                        status="failed",
                        error_msg=str(e),
                    )
                    await self.db_manager.save_outreach_records([table_rec])

        return records

    async def close(self) -> None:
        await self.client.close()
