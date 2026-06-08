from pipeline.main import _render_checkpoint
from pipeline.models import Prospect, Contact


def test_render_checkpoint_empty(capsys) -> None:
    _render_checkpoint([])
    captured = capsys.readouterr()
    assert "0" in captured.out


def test_render_checkpoint_with_contact() -> None:
    prospect = Prospect(
        company_domain="example.com",
        full_name="Jane Doe",
        title="CEO",
        linkedin_url="https://www.linkedin.com/in/jane",
    )
    contact = Contact(prospect=prospect, work_email="jane@example.com", verified=True)
    _render_checkpoint([contact])
    assert True
