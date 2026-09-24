from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .service import redact, serialize_findings

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="BelgeKalkan",
    version="1.0.0",
    description="Yerel ve deterministik kişisel veri maskeleme servisi.",
)


class RedactRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)
    mode: Literal["label", "mask"] = "label"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/redact")
def redact_endpoint(request: RedactRequest) -> dict[str, object]:
    result = redact(request.text, request.mode)
    return {
        "redacted_text": result.redacted_text,
        "findings": serialize_findings(result.findings),
        "manifest": result.manifest,
    }


app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")

