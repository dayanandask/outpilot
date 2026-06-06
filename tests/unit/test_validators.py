from pipeline.utils.validators import (
    is_valid_domain,
    is_valid_linkedin_url,
    is_valid_email,
)


def test_is_valid_domain_valid() -> None:
    assert is_valid_domain("example.com") is True
    assert is_valid_domain("sub-domain.example.co.uk") is True
    assert is_valid_domain("domain123.io") is True


def test_is_valid_domain_invalid() -> None:
    assert is_valid_domain("") is False
    assert is_valid_domain("example") is False
    assert is_valid_domain("example.") is False
    assert is_valid_domain(".com") is False
    assert is_valid_domain("http://example.com") is False
    assert is_valid_domain("example.com/page") is False


def test_is_valid_linkedin_url_valid() -> None:
    assert is_valid_linkedin_url("https://www.linkedin.com/in/john-doe-123456") is True
    assert is_valid_linkedin_url("http://linkedin.com/in/jane_smith") is True
    assert is_valid_linkedin_url("linkedin.com/in/username") is True
    assert is_valid_linkedin_url("https://linkedin.com/company/some-corp") is True


def test_is_valid_linkedin_url_invalid() -> None:
    assert is_valid_linkedin_url("") is False
    assert is_valid_linkedin_url("https://facebook.com/in/username") is False
    assert is_valid_linkedin_url("linkedin.com/search") is False
    assert is_valid_linkedin_url("http://linkedin.com") is False


def test_is_valid_email_valid() -> None:
    assert is_valid_email("test@example.com") is True
    assert is_valid_email("john.doe+alias@sub.example.co.uk") is True


def test_is_valid_email_invalid() -> None:
    assert is_valid_email("") is False
    assert is_valid_email("test") is False
    assert is_valid_email("test@") is False
    assert is_valid_email("test@example") is False
    assert is_valid_email("john.doe@.com") is False
