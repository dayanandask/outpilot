from pipeline.main import (
    _model_to_company_record,
    _model_to_prospect_record,
    _model_to_contact_record,
)
from pipeline.models import Company, Prospect, Contact


def test_db_model_converters() -> None:
    run_id = "test_db_converters"

    company = Company(domain="stripe.com", name="Stripe", source="apollo_io")
    rec = _model_to_company_record(company, run_id)
    assert rec.domain == "stripe.com"
    assert rec.name == "Stripe"

    prospect = Prospect(
        company_domain="stripe.com",
        full_name="Jane Doe",
        title="CEO",
        linkedin_url="https://www.linkedin.com/in/jane",
    )
    prec = _model_to_prospect_record(prospect, run_id)
    assert prec.full_name == "Jane Doe"
    assert prec.title == "CEO"

    contact = Contact(prospect=prospect, work_email="jane@stripe.com", verified=True)
    crec = _model_to_contact_record(contact, run_id)
    assert crec.work_email == "jane@stripe.com"
    assert crec.verified is True
