from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, field_validator, EmailStr
from pipeline.utils.validators import is_valid_domain, is_valid_linkedin_url


class SeedInput(BaseModel):
    domain: str

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not is_valid_domain(v_clean):
            raise ValueError(f"Invalid domain format: {v}")
        return v_clean


class Company(BaseModel):
    domain: str
    name: Optional[str] = None
    source: Literal["apollo_io"] = "apollo_io"

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not is_valid_domain(v_clean):
            raise ValueError(f"Invalid domain format: {v}")
        return v_clean


class Prospect(BaseModel):
    company_domain: str
    full_name: str
    title: str
    linkedin_url: str
    apollo_email: str | None = None

    @field_validator("company_domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not is_valid_domain(v_clean):
            raise ValueError(f"Invalid domain format: {v}")
        return v_clean

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin(cls, v: str) -> str:
        v_clean = v.strip()
        if not is_valid_linkedin_url(v_clean):
            raise ValueError(f"Invalid LinkedIn URL: {v}")
        return v_clean

    def is_decision_maker(self) -> bool:
        """Determines if the prospect holds a decision-making role based on their title."""
        keywords = [
            "ceo",
            "cto",
            "cfo",
            "coo",
            "cmo",
            "cpo",
            "vp",
            "vice president",
            "director",
            "head of",
        ]
        title_lower = self.title.lower()
        return any(k in title_lower for k in keywords)


class Contact(BaseModel):
    prospect: Prospect
    work_email: EmailStr
    verified: bool
    source: str = "apollo"


class OutreachRecord(BaseModel):
    contact: Contact
    email_subject: str
    email_body: str
    sent_at: Optional[datetime] = None
    brevo_message_id: Optional[str] = None
    status: Literal["pending", "sent", "failed"] = "pending"
