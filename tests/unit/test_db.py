import os
import pytest
from pipeline.db import (
    DatabaseManager,
    Run,
    CompanyRecord,
    ProspectRecord,
)


import uuid


@pytest.mark.asyncio
async def test_db_lifecycle_and_persistence() -> None:
    run_id = f"test_run_{uuid.uuid4().hex}"
    db_manager = DatabaseManager(run_id)

    try:
        # 1. Initialize DB
        await db_manager.initialize()
        assert os.path.exists(db_manager.db_path)

        # 2. Create main run record
        run = await db_manager.create_run(seed_domain="stripe.com")
        assert run.run_id == run_id
        assert run.seed_domain == "stripe.com"
        assert run.status == "running"

        # 3. Save and retrieve companies
        companies = [
            CompanyRecord(
                run_id=run_id,
                domain="company-a.com",
                name="Company A",
                source="apollo_io",
                status="completed",
            ),
            CompanyRecord(
                run_id=run_id,
                domain="company-b.com",
                name="Company B",
                source="apollo_io",
                status="pending",
            ),
        ]
        await db_manager.save_companies(companies)

        saved_companies = await db_manager.get_companies()
        assert len(saved_companies) == 2
        assert {c.domain for c in saved_companies} == {"company-a.com", "company-b.com"}

        # 4. Save and retrieve prospects
        prospects = [
            ProspectRecord(
                run_id=run_id,
                company_domain="company-a.com",
                full_name="Alice CEO",
                title="Chief Executive Officer",
                linkedin_url="https://www.linkedin.com/in/alice-ceo",
                status="completed",
            )
        ]
        await db_manager.save_prospects(prospects)

        saved_prospects = await db_manager.get_prospects()
        assert len(saved_prospects) == 1
        assert saved_prospects[0].full_name == "Alice CEO"

        # 5. Update run status (e.g. to completed)
        await db_manager.update_run_status("completed")

        # Verify run was updated
        async with await db_manager.get_session() as session:
            from sqlmodel import select

            statement = select(Run).where(Run.run_id == run_id)  # type: ignore[arg-type]
            result = await session.exec(statement)
            updated_run = result.one_or_none()
            assert updated_run is not None
            assert updated_run.status == "completed"

    finally:
        # Close connection and cleanup db file
        await db_manager.close()
        try:
            if os.path.exists(db_manager.db_path):
                os.remove(db_manager.db_path)
        except PermissionError:
            pass


@pytest.mark.asyncio
async def test_db_resume_logic() -> None:
    run_id = f"test_resume_run_{uuid.uuid4().hex}"
    db_manager = DatabaseManager(run_id)

    try:
        await db_manager.initialize()
        await db_manager.create_run(seed_domain="resumable.com")

        companies = [
            CompanyRecord(
                run_id=run_id,
                domain="c1.com",
                name="C1",
                source="apollo_io",
                status="completed",
            ),
        ]
        await db_manager.save_companies(companies)
        await db_manager.close()

        # Re-initialize a new manager pointing to the same DB
        db_manager_new = DatabaseManager(run_id)
        await db_manager_new.initialize()

        # Retrieve previously saved data to check resume capability
        existing_companies = await db_manager_new.get_companies()
        assert len(existing_companies) == 1
        assert existing_companies[0].domain == "c1.com"
        assert existing_companies[0].status == "completed"

        await db_manager_new.close()

    finally:
        try:
            if os.path.exists(db_manager.db_path):
                os.remove(db_manager.db_path)
        except PermissionError:
            pass
        # Try to clean up runs folder if empty (will fail silently if not, which is fine)
        try:
            os.rmdir("runs")
        except OSError:
            pass
