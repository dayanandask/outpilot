import os
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import SQLModel, Field, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker


# Mixin for common fields
class BaseRecord(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="pending")  # pending, completed, failed, unresolvable
    error_msg: Optional[str] = Field(default=None)


class Run(SQLModel, table=True):
    __tablename__ = "runs"
    run_id: str = Field(primary_key=True)
    seed_domain: str
    status: str = Field(default="running")  # running, completed, failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_msg: Optional[str] = Field(default=None)


class CompanyRecord(BaseRecord, table=True):
    __tablename__ = "companies"
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    domain: str = Field(index=True)
    name: Optional[str] = Field(default=None)
    source: str = Field(default="apollo_io")


class ProspectRecord(BaseRecord, table=True):
    __tablename__ = "prospects"
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    company_domain: str = Field(index=True)
    full_name: str
    title: str
    linkedin_url: str = Field(index=True)


class ContactRecord(BaseRecord, table=True):
    __tablename__ = "contacts"
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    linkedin_url: str = Field(index=True)
    full_name: str
    title: str
    company_domain: str
    work_email: str = Field(index=True)
    verified: bool


class OutreachRecordTable(BaseRecord, table=True):
    __tablename__ = "outreach_records"
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    work_email: str = Field(index=True)
    email_subject: str
    email_body: str
    sent_at: Optional[datetime] = Field(default=None)
    brevo_message_id: Optional[str] = Field(default=None)


class DatabaseManager:
    """Manages the lifecycle and state persistence of a pipeline run in SQLite."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        os.makedirs("runs", exist_ok=True)
        self.db_path = f"runs/{run_id}.db"
        self.engine: AsyncEngine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_path}", echo=False
        )
        self.async_session_maker = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )  # type: ignore

    async def initialize(self) -> None:
        """Initializes database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        """Helper to create a session."""
        return self.async_session_maker()  # type: ignore[no-any-return]

    async def create_run(self, seed_domain: str) -> Run:
        """Creates or registers a new run in the database."""
        async with self.async_session_maker() as session:
            # Check if run already exists
            statement = select(Run).where(Run.run_id == self.run_id)
            result = await session.exec(statement)
            run = result.one_or_none()
            if not run:
                run = Run(run_id=self.run_id, seed_domain=seed_domain, status="running")
                session.add(run)
                await session.commit()
                await session.refresh(run)
            return run  # type: ignore[no-any-return]

    async def update_run_status(
        self, status: str, error_msg: Optional[str] = None
    ) -> None:
        """Updates status of the main run record."""
        async with self.async_session_maker() as session:
            statement = select(Run).where(Run.run_id == self.run_id)
            result = await session.exec(statement)
            run = result.one_or_none()
            if run:
                run.status = status
                run.error_msg = error_msg
                run.updated_at = datetime.now(timezone.utc)
                session.add(run)
                await session.commit()

    async def get_companies(self) -> List[CompanyRecord]:
        """Fetches all companies retrieved in the current run."""
        async with self.async_session_maker() as session:
            statement = select(CompanyRecord).where(CompanyRecord.run_id == self.run_id)
            result = await session.exec(statement)
            return list(result.all())

    async def save_companies(self, companies: List[CompanyRecord]) -> None:
        """Saves or updates retrieved companies."""
        async with self.async_session_maker() as session:
            for company in companies:
                company.run_id = self.run_id
                session.add(company)
            await session.commit()

    async def get_prospects(self) -> List[ProspectRecord]:
        """Fetches all prospects discovered in the current run."""
        async with self.async_session_maker() as session:
            statement = select(ProspectRecord).where(
                ProspectRecord.run_id == self.run_id
            )
            result = await session.exec(statement)
            return list(result.all())

    async def save_prospects(self, prospects: List[ProspectRecord]) -> None:
        """Saves or updates discovered prospects."""
        async with self.async_session_maker() as session:
            for prospect in prospects:
                prospect.run_id = self.run_id
                session.add(prospect)
            await session.commit()

    async def get_contacts(self) -> List[ContactRecord]:
        """Fetches all contacts resolved in the current run."""
        async with self.async_session_maker() as session:
            statement = select(ContactRecord).where(ContactRecord.run_id == self.run_id)
            result = await session.exec(statement)
            return list(result.all())

    async def save_contacts(self, contacts: List[ContactRecord]) -> None:
        """Saves or updates resolved contacts."""
        async with self.async_session_maker() as session:
            for contact in contacts:
                contact.run_id = self.run_id
                session.add(contact)
            await session.commit()

    async def get_outreach_records(self) -> List[OutreachRecordTable]:
        """Fetches all outreach records from the current run."""
        async with self.async_session_maker() as session:
            statement = select(OutreachRecordTable).where(
                OutreachRecordTable.run_id == self.run_id
            )
            result = await session.exec(statement)
            return list(result.all())

    async def save_outreach_records(self, records: List[OutreachRecordTable]) -> None:
        """Saves or updates outreach records."""
        async with self.async_session_maker() as session:
            for rec in records:
                rec.run_id = self.run_id
                session.add(rec)
            await session.commit()

    async def close(self) -> None:
        """Closes connection engine."""
        await self.engine.dispose()
