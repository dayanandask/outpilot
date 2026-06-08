import os

import pytest
import respx
from httpx import Response
from pipeline.models import Prospect, Contact
from pipeline.stages.s4_outreach import OutreachStage
from pipeline.db import DatabaseManager


@pytest.fixture
def contact() -> Contact:
    prospect = Prospect(
        company_domain="example.com",
        full_name="Jane Doe",
        title="Chief Executive Officer",
        linkedin_url="https://www.linkedin.com/in/jane",
    )
    return Contact(prospect=prospect, work_email="jane@example.com", verified=True)


@pytest.mark.asyncio
@respx.mock
async def test_brevo_stage_sends_email(contact: Contact) -> None:
    respx.post("https://api.brevo.com/v3/smtp/email").mock(
        return_value=Response(201, json={"messageId": "msg_123"})
    )

    stage = OutreachStage()
    records = await stage.run([contact])

    assert len(records) == 1
    assert records[0].status == "sent"
    assert records[0].brevo_message_id == "msg_123"

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_brevo_stage_handles_api_error(contact: Contact) -> None:
    respx.post("https://api.brevo.com/v3/smtp/email").mock(
        return_value=Response(500, json={"error": "server_error"})
    )

    stage = OutreachStage()
    records = await stage.run([contact])

    assert len(records) == 1
    assert records[0].status == "failed"

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_brevo_stage_respects_daily_cap(contact: Contact) -> None:
    respx.post("https://api.brevo.com/v3/smtp/email").mock(
        return_value=Response(201, json={"messageId": "msg_123"})
    )

    stage = OutreachStage()
    stage.daily_sent = stage.daily_cap

    records = await stage.run([contact])

    assert len(records) == 0
    assert stage.daily_sent == stage.daily_cap

    await stage.close()


@pytest.mark.asyncio
@respx.mock
async def test_brevo_stage_saves_to_db(contact: Contact) -> None:
    respx.post("https://api.brevo.com/v3/smtp/email").mock(
        return_value=Response(201, json={"messageId": "msg_db_123"})
    )

    run_id = "test_outreach_db"
    db_manager = DatabaseManager(run_id)
    await db_manager.initialize()

    try:
        stage = OutreachStage(db_manager=db_manager)
        records = await stage.run([contact])

        assert len(records) == 1
        assert records[0].status == "sent"

        saved = await db_manager.get_outreach_records()
        assert len(saved) == 1
        assert saved[0].brevo_message_id == "msg_db_123"

        await stage.close()
    finally:
        await db_manager.close()
        try:
            if os.path.exists(db_manager.db_path):
                os.remove(db_manager.db_path)
        except PermissionError:
            pass


@pytest.mark.asyncio
@respx.mock
async def test_brevo_stage_saves_failed_to_db(contact: Contact) -> None:
    respx.post("https://api.brevo.com/v3/smtp/email").mock(
        return_value=Response(500, json={"error": "server_error"})
    )

    run_id = "test_outreach_db_fail"
    db_manager = DatabaseManager(run_id)
    await db_manager.initialize()

    try:
        stage = OutreachStage(db_manager=db_manager)
        records = await stage.run([contact])

        assert len(records) == 1
        assert records[0].status == "failed"

        saved = await db_manager.get_outreach_records()
        assert len(saved) == 1
        assert saved[0].status == "failed"

        await stage.close()
    finally:
        await db_manager.close()
        try:
            if os.path.exists(db_manager.db_path):
                os.remove(db_manager.db_path)
        except PermissionError:
            pass
