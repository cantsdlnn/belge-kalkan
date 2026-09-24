import pytest

from belgekalkan.detectors import DataKind, detect, is_valid_iban, is_valid_tckn


@pytest.mark.parametrize("value", ["10000000146", "11111111110"])
def test_accepts_checksum_valid_tckn(value: str) -> None:
    assert is_valid_tckn(value)


@pytest.mark.parametrize("value", ["01234567890", "10000000145", "abc"])
def test_rejects_invalid_tckn(value: str) -> None:
    assert not is_valid_tckn(value)


def test_validates_turkish_iban() -> None:
    assert is_valid_iban("TR33 0006 1005 1978 6457 8413 26")
    assert not is_valid_iban("TR34 0006 1005 1978 6457 8413 26")


def test_detects_supported_data_without_false_tckn() -> None:
    text = "10000000146, test@example.com, +90 555 123 45 67, 12345678901"
    assert [finding.kind for finding in detect(text)] == [
        DataKind.TCKN,
        DataKind.EMAIL,
        DataKind.PHONE,
    ]

