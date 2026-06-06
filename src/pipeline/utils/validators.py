import re
from email_validator import validate_email as validate_ev, EmailNotValidError

DOMAIN_REGEX = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}$")
LINKEDIN_URL_REGEX = re.compile(
    r"^(https?://)?(www\.)?linkedin\.com/(in|company|school|share|messaging)/[a-zA-Z0-9\-_%]+/?.*$",
    re.IGNORECASE,
)


def is_valid_domain(domain: str) -> bool:
    """Validates if a domain matches the standard pattern (e.g., example.com)."""
    if not domain:
        return False
    # Ensure lowercase for comparison/regex match
    domain_lower = domain.strip().lower()
    return bool(DOMAIN_REGEX.match(domain_lower))


def is_valid_linkedin_url(url: str) -> bool:
    """Validates if a URL is a valid LinkedIn profile or company URL."""
    if not url:
        return False
    return bool(LINKEDIN_URL_REGEX.match(url.strip()))


def is_valid_email(email: str) -> bool:
    """Validates if an email address is structurally valid."""
    if not email:
        return False
    try:
        validate_ev(email.strip(), check_deliverability=False)
        return True
    except EmailNotValidError:
        return False
