import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, EmailStr


class Settings(BaseSettings):
    apollo_api_key: str = Field(alias="APOLLO_API_KEY")
    prospeo_api_key: str = Field(alias="PROSPEO_API_KEY")
    brevo_api_key: str = Field(alias="BREVO_API_KEY")

    from_email: EmailStr = Field(alias="FROM_EMAIL")
    from_name: str = Field(alias="FROM_NAME")

    max_lookalikes: int = Field(default=20, alias="MAX_LOOKALIKES")
    max_prospects_per_domain: int = Field(default=3, alias="MAX_PROSPECTS_PER_DOMAIN")
    daily_email_cap: int = Field(default=100, alias="DAILY_EMAIL_CAP")
    apollo_rpm: int = Field(default=200, alias="APOLLO_RPM")
    prospeo_rpm: int = Field(default=10, alias="PROSPEO_RPM")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_pii: bool = Field(default=False, alias="LOG_PII")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("apollo_api_key", "prospeo_api_key", "brevo_api_key")
    @classmethod
    def validate_keys(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("API Key cannot be empty")
        if len(v) < 8:
            raise ValueError("API Key must be at least 8 characters long")
        return v.strip()

    @field_validator("from_email")
    @classmethod
    def validate_email(cls, v: EmailStr) -> EmailStr:
        if not v or "@" not in v:
            raise ValueError("Invalid email address")
        return v


def mask_key(key: str) -> str:
    """Masks an API key for safe logging, showing only the last 4 characters.

    Example:
        >>> mask_key("mysecretapikey1234")
        '****************1234'
    """
    if not key:
        return ""
    if len(key) <= 4:
        return "****"
    return key[-4:].rjust(20, "*")


# Load settings
try:
    settings = Settings()  # type: ignore[call-arg]
except Exception as e:
    logging.error(f"Configuration validation failed: {e}")
    raise e
