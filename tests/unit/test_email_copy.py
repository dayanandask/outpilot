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
