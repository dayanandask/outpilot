import pytest
from pipeline.main import _mask


def test_mask_none() -> None:
    assert _mask(None) == ""


def test_mask_short() -> None:
    result = _mask("abc")
    assert result == result.rjust(20, "*")
    assert result.endswith("abc")


def test_mask_normal() -> None:
    result = _mask("secret123")
    assert result == result.rjust(20, "*")
    assert result.endswith("t123")
