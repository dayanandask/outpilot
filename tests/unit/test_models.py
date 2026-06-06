import pytest
from pydantic import ValidationError
from pipeline.models import SeedInput, Company, Prospect, Contact


def test_seed_input_valid() -> None:
    seed = SeedInput(domain="stripe.com")
    assert seed.domain == "stripe.com"


def test_seed_input_invalid() -> None:
    with pytest.raises(ValidationError):
        SeedInput(domain="not-a-domain")


def test_company_valid() -> None:
    company = Company(domain="google.com", name="Google", source="apollo_io")
    assert company.domain == "google.com"
    assert company.name == "Google"
    assert company.source == "apollo_io"


def test_company_invalid() -> None:
    with pytest.raises(ValidationError):
        Company(domain="http://google.com")


def test_prospect_valid() -> None:
    prospect = Prospect(
        company_domain="stripe.com",
        full_name="John Doe",
        title="VP of Engineering",
        linkedin_url="https://www.linkedin.com/in/johndoe",
    )
    assert prospect.company_domain == "stripe.com"
    assert prospect.is_decision_maker() is True


def test_prospect_invalid_linkedin() -> None:
    with pytest.raises(ValidationError):
        Prospect(
            company_domain="stripe.com",
            full_name="John Doe",
            title="VP of Engineering",
            linkedin_url="https://not-linkedin.com/johndoe",
        )


def test_prospect_is_decision_maker() -> None:
    p1 = Prospect(
        company_domain="stripe.com",
        full_name="Alice",
        title="CEO & Founder",
        linkedin_url="https://www.linkedin.com/in/alice",
    )
    assert p1.is_decision_maker() is True

    p2 = Prospect(
        company_domain="stripe.com",
        full_name="Bob",
        title="Software Engineer Intern",
        linkedin_url="https://www.linkedin.com/in/bob",
    )
    assert p2.is_decision_maker() is False


def test_contact_valid() -> None:
    prospect = Prospect(
        company_domain="stripe.com",
        full_name="John Doe",
        title="VP of Engineering",
        linkedin_url="https://www.linkedin.com/in/johndoe",
    )
    contact = Contact(prospect=prospect, work_email="john@stripe.com", verified=True)
    assert contact.work_email == "john@stripe.com"
    assert contact.verified is True


def test_contact_invalid_email() -> None:
    prospect = Prospect(
        company_domain="stripe.com",
        full_name="John Doe",
        title="VP of Engineering",
        linkedin_url="https://www.linkedin.com/in/johndoe",
    )
    with pytest.raises(ValidationError):
        Contact(prospect=prospect, work_email="invalid-email", verified=True)
