import pytest
from pipeline.utils.validators import (
    is_valid_domain,
    is_valid_linkedin_url,
    is_valid_email,
)


@pytest.mark.parametrize(
    "domain,expected",
    [
        ("stripe.com", True),
        ("sub.domain.co.uk", True),
        ("https://stripe.com", False),
        ("notadomain", False),
        ("", False),
    ],
)
def test_valid_domains(domain: str, expected: bool) -> None:
    assert is_valid_domain(domain) is expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.linkedin.com/in/john-doe-123456", True),
        ("http://linkedin.com/in/jane_smith", True),
        ("https://facebook.com/in/username", False),
        ("", False),
    ],
)
def test_valid_linkedin(url: str, expected: bool) -> None:
    assert is_valid_linkedin_url(url) is expected


@pytest.mark.parametrize(
    "email,expected",
    [
        ("test@example.com", True),
        ("john.doe+alias@sub.example.co.uk", True),
        ("", False),
        ("not-an-email", False),
        ("test@", False),
        ("test@example", False),
    ],
)
def test_valid_email(email: str, expected: bool) -> None:
    assert is_valid_email(email) is expected
