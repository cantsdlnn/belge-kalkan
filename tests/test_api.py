from fastapi.testclient import TestClient

from belgekalkan.api import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_redact_endpoint_never_echoes_raw_findings() -> None:
    response = client.post("/api/redact", json={"text": "Ara: test@example.com", "mode": "label"})
    assert response.status_code == 200
    body = response.json()
    assert body["redacted_text"] == "Ara: [EMAIL]"
    assert "test@example.com" not in response.text


def test_rejects_empty_text() -> None:
    assert client.post("/api/redact", json={"text": ""}).status_code == 422

