import pytest
from pathlib import Path
from pipeline.utils.email_copy import EmailTemplateEngine
from pipeline.models import Prospect, Contact


@pytest.fixture
def contact() -> Contact:
    prospect = Prospect(
        company_domain="example.com",
        full_name="Jane Doe",
        title="Chief Executive Officer",
        linkedin_url="https://www.linkedin.com/in/jane",
    )
    return Contact(prospect=prospect, work_email="jane@example.com", verified=True)


def test_engine_raises_when_template_missing(tmp_path: Path) -> None:
    missing = tmp_path / "outreach.txt"
    with pytest.raises(FileNotFoundError):
        EmailTemplateEngine(template_path=str(missing))


def test_engine_render(contact: Contact) -> None:
    engine = EmailTemplateEngine()
    result = engine.render(contact)

    assert "subject" in result
    assert "body" in result
    assert result["to"] == "jane@example.com"
    assert result["name"] == "Jane Doe"


def test_engine_render_with_company_name(contact: Contact) -> None:
    engine = EmailTemplateEngine()
    result = engine.render(contact, company_name="AcmeCorp")

    assert result["body"] is not None
