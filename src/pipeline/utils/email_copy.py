import string
from pathlib import Path
from typing import Any, Dict, Optional
from pipeline.models import Contact


class EmailTemplateEngine:
    """Renders personalized email copy from a template file using string.Template."""

    def __init__(self, template_path: str = "templates/outreach.txt") -> None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        full_path = base_dir / template_path
        if not full_path.exists():
            raise FileNotFoundError(f"Template file not found: {full_path}")
        self.template_path = full_path
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        self._template = string.Template(content)

    def render(self, contact: Contact, company_name: Optional[str] = None) -> Dict[str, Any]:
        """Renders the email template with contact data.

        Args:
            contact: Contact model with prospect info and email.
            company_name: Optional override for company name.

        Returns:
            Dictionary with subject, body, to, and name fields.

        Raises:
            ValueError: If template contains unfilled placeholders after rendering.
        """
        first_name = contact.prospect.full_name.split()[0]
        domain = contact.prospect.company_domain
        display_company = company_name or domain.replace(".com", "").replace(".io", "").capitalize()

        mapping = {
            "first_name": first_name,
            "company_name": display_company,
            "title": contact.prospect.title,
            "domain": domain,
        }

        rendered = self._template.safe_substitute(mapping)
        placeholders = list(self._template.pattern.findall(rendered))

        if placeholders:
            raise ValueError(f"Unfilled template placeholders: {placeholders}")

        lines = [line.strip() for line in rendered.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Rendered template is empty")

        subject = lines[0]
        body = "\n".join(lines[1:])

        return {
            "subject": subject,
            "body": body,
            "to": contact.work_email,
            "name": contact.prospect.full_name,
        }
