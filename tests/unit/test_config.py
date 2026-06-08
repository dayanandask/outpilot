import pytest
from pipeline.config import Settings
from pydantic import ValidationError


def test_settings_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APOLLO_API_KEY", "a" * 20)
    monkeypatch.setenv("PROSPEO_API_KEY", "b" * 20)
    monkeypatch.setenv("BREVO_API_KEY", "c" * 20)
    monkeypatch.setenv("FROM_EMAIL", "test@example.com")
    monkeypatch.setenv("FROM_NAME", "Test")
    settings = Settings()
    assert settings.apollo_api_key == "a" * 20


def test_settings_invalid_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APOLLO_API_KEY", "a" * 20)
    monkeypatch.setenv("PROSPEO_API_KEY", "b" * 20)
    monkeypatch.setenv("BREVO_API_KEY", "c" * 20)
    monkeypatch.setenv("FROM_EMAIL", "not-an-email")
    monkeypatch.setenv("FROM_NAME", "Test")
    with pytest.raises(ValidationError):
        Settings()


def test_settings_empty_key_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APOLLO_API_KEY", "")
    monkeypatch.setenv("PROSPEO_API_KEY", "b" * 20)
    monkeypatch.setenv("BREVO_API_KEY", "c" * 20)
    monkeypatch.setenv("FROM_EMAIL", "test@example.com")
    monkeypatch.setenv("FROM_NAME", "Test")
    with pytest.raises(ValidationError):
        Settings()


def test_settings_short_key_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APOLLO_API_KEY", "short")
    monkeypatch.setenv("PROSPEO_API_KEY", "b" * 20)
    monkeypatch.setenv("BREVO_API_KEY", "c" * 20)
    monkeypatch.setenv("FROM_EMAIL", "test@example.com")
    monkeypatch.setenv("FROM_NAME", "Test")
    with pytest.raises(ValidationError):
        Settings()
