import io
import json

from fastapi.testclient import TestClient
from PIL import Image

from belgekalkan.api import app
from belgekalkan.documents import MAX_UPLOAD_BYTES, OcrLine, scan_document

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.json() == {"status": "ok"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"


def test_redact_endpoint_never_echoes_raw_findings() -> None:
    response = client.post("/api/redact", json={"text": "Ara: test@example.com", "mode": "label"})
    assert response.status_code == 200
    body = response.json()
    assert body["redacted_text"] == "Ara: [EMAIL]"
    assert "test@example.com" not in response.text


def test_rejects_empty_text() -> None:
    assert client.post("/api/redact", json={"text": ""}).status_code == 422


class FakeOcr:
    def recognize(self, _image: Image.Image) -> list[OcrLine]:
        return [OcrLine("10000000146", 0.99, ((5, 5), (120, 5), (120, 40), (5, 40)))]


def image_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (200, 100), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_document_scan_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        "belgekalkan.api.scan_document",
        lambda data, filename: scan_document(data, filename, FakeOcr()),
    )
    response = client.post(
        "/api/document/scan", files={"file": ("shot.png", image_bytes(), "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["summary"]["region_count"] == 1


def test_document_redact_endpoint() -> None:
    source = image_bytes()
    scan = scan_document(source, "shot.png", FakeOcr())
    regions = [{
        "page": 0, "x": 5, "y": 5, "width": 115, "height": 35,
        "preview_width": 200, "preview_height": 100,
    }]
    response = client.post(
        "/api/document/redact",
        files={"file": ("shot.png", source, "image/png")},
        data={"regions": json.dumps(regions), "fingerprint": scan.fingerprint},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "shot-maskeli.png" in response.headers["content-disposition"]

    black_response = client.post(
        "/api/document/redact",
        files={"file": ("shot.png", source, "image/png")},
        data={
            "regions": json.dumps(regions),
            "fingerprint": scan.fingerprint,
            "mask_style": "black",
        },
    )
    black_image = Image.open(io.BytesIO(black_response.content)).convert("RGB")
    assert black_response.status_code == 200
    assert black_image.getpixel((20, 20)) == (0, 0, 0)

    invalid_style = client.post(
        "/api/document/redact",
        files={"file": ("shot.png", source, "image/png")},
        data={
            "regions": json.dumps(regions),
            "fingerprint": scan.fingerprint,
            "mask_style": "blur",
        },
    )
    assert invalid_style.status_code == 422


def test_document_endpoints_reject_invalid_or_oversized_uploads() -> None:
    invalid = client.post(
        "/api/document/scan", files={"file": ("fake.pdf", b"not-pdf", "application/pdf")}
    )
    assert invalid.status_code == 400
    assert "PDF dosyası açılamadı" in invalid.json()["detail"]

    oversized = client.post(
        "/api/document/scan",
        files={"file": ("large.png", b"x" * (MAX_UPLOAD_BYTES + 1), "image/png")},
    )
    assert oversized.status_code == 413
