from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum


class DataKind(StrEnum):
    TCKN = "tckn"
    IBAN = "iban"
    EMAIL = "email"
    PHONE = "phone"


@dataclass(frozen=True, slots=True)
class Finding:
    kind: DataKind
    start: int
    end: int
    value: str
    confidence: str


_EMAIL = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)
_TCKN = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")
_IBAN = re.compile(r"(?<![A-Z0-9])TR(?:[\s-]?\d){24}(?![A-Z0-9])", re.I)
_PHONE = re.compile(
    r"(?<!\d)(?:(?:\+|00)90[\s().-]*|0)?5\d{2}[\s().-]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2}(?!\d)"
)


def is_valid_tckn(value: str) -> bool:
    """Validate a Turkish identity number using its public checksum rules."""
    if not re.fullmatch(r"[1-9]\d{10}", value):
        return False
    digits = [int(char) for char in value]
    odd_sum = sum(digits[index] for index in (0, 2, 4, 6, 8))
    even_sum = sum(digits[index] for index in (1, 3, 5, 7))
    tenth = ((odd_sum * 7) - even_sum) % 10
    eleventh = sum(digits[:10]) % 10
    return digits[9] == tenth and digits[10] == eleventh


def is_valid_iban(value: str) -> bool:
    """Validate a Turkish IBAN with the ISO 13616 mod-97 check."""
    compact = re.sub(r"[\s-]", "", value).upper()
    if not re.fullmatch(r"TR\d{24}", compact):
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged)
    remainder = 0
    for char in numeric:
        remainder = (remainder * 10 + int(char)) % 97
    return remainder == 1


def _scan(
    text: str,
    pattern: re.Pattern[str],
    kind: DataKind,
    validator: Callable[[str], bool] | None = None,
    confidence: str = "pattern",
) -> Iterable[Finding]:
    for match in pattern.finditer(text):
        raw = match.group(0)
        compact = re.sub(r"[\s-]", "", raw)
        if validator is not None and not validator(compact):
            continue
        yield Finding(kind, match.start(), match.end(), raw, confidence)


def detect(text: str) -> list[Finding]:
    """Return deterministic, validated and non-overlapping findings."""
    candidates = [
        *_scan(text, _TCKN, DataKind.TCKN, is_valid_tckn, "checksum"),
        *_scan(text, _IBAN, DataKind.IBAN, is_valid_iban, "checksum"),
        *_scan(text, _EMAIL, DataKind.EMAIL),
        *_scan(text, _PHONE, DataKind.PHONE),
    ]
    candidates.sort(key=lambda finding: (finding.start, -(finding.end - finding.start)))

    accepted: list[Finding] = []
    for finding in candidates:
        if any(finding.start < current.end and finding.end > current.start for current in accepted):
            continue
        accepted.append(finding)
    return sorted(accepted, key=lambda finding: finding.start)
