import pytest

from belgekalkan.service import redact, serialize_findings


def test_label_redaction_and_privacy_manifest() -> None:
    source = "Kimlik: 10000000146, e-posta: test@example.com"
    result = redact(source)
    assert result.redacted_text == "Kimlik: [TCKN], e-posta: [EMAIL]"
    assert result.manifest["finding_count"] == 2
    assert result.manifest["raw_values_stored"] is False
    assert "10000000146" not in str(result.manifest)
    assert all("value" not in finding for finding in serialize_findings(result.findings))


def test_mask_keeps_last_four_digits() -> None:
    result = redact("Tel: 0555 123 45 67", "mask")
    assert result.redacted_text.endswith("4567")
    assert "0555" not in result.redacted_text


def test_mask_hides_email_completely() -> None:
    assert redact("test@example.com", "mask").redacted_text == "***"


def test_token_mode_is_stable_and_secret_dependent() -> None:
    first = redact("test@example.com", "token", "secret-a").redacted_text
    again = redact("test@example.com", "token", "secret-a").redacted_text
    other = redact("test@example.com", "token", "secret-b").redacted_text
    assert first == again
    assert first != other


def test_token_requires_secret() -> None:
    with pytest.raises(ValueError, match="gizli anahtar"):
        redact("test@example.com", "token")


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="Geçersiz"):
        redact("test@example.com", "unknown")

