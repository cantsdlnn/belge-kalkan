from __future__ import annotations

import hashlib
import hmac
from collections import Counter
from dataclasses import asdict, dataclass

from .detectors import DataKind, Finding, detect

DETECTOR_VERSION = "rules-1.0.0"


@dataclass(frozen=True, slots=True)
class RedactionResult:
    redacted_text: str
    findings: list[Finding]
    manifest: dict[str, object]


def _replacement(finding: Finding, mode: str, secret: str | None) -> str:
    if mode == "label":
        return f"[{finding.kind.value.upper()}]"
    if mode == "mask":
        visible = 4 if finding.kind in {DataKind.TCKN, DataKind.IBAN, DataKind.PHONE} else 0
        if visible:
            compact = "".join(char for char in finding.value if char.isalnum())
            return "*" * max(len(compact) - visible, 4) + compact[-visible:]
        return "***"
    if mode == "token":
        if not secret:
            raise ValueError("Token modu için bir gizli anahtar gerekir.")
        digest = hmac.new(secret.encode(), finding.value.encode(), hashlib.sha256).hexdigest()[:10]
        return f"[{finding.kind.value.upper()}:{digest}]"
    raise ValueError("Geçersiz maskeleme modu.")


def redact(text: str, mode: str = "label", secret: str | None = None) -> RedactionResult:
    findings = detect(text)
    output = text
    for finding in reversed(findings):
        replacement = _replacement(finding, mode, secret)
        output = output[: finding.start] + replacement + output[finding.end :]

    counts = Counter(finding.kind.value for finding in findings)
    manifest: dict[str, object] = {
        "detector_version": DETECTOR_VERSION,
        "mode": mode,
        "finding_count": len(findings),
        "counts": dict(sorted(counts.items())),
        "input_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "raw_values_stored": False,
    }
    return RedactionResult(output, findings, manifest)


def serialize_findings(findings: list[Finding]) -> list[dict[str, object]]:
    """Expose coordinates and type, but never echo the sensitive raw value."""
    return [
        {key: value for key, value in asdict(finding).items() if key != "value"}
        for finding in findings
    ]
