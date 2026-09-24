from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .documents import (
    MAX_UPLOAD_BYTES,
    DocumentError,
    redact_document,
    scan_document,
    serialize_scan,
)
from .service import redact, serialize_findings

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="BelgeKalkan",
    version="2.0.0",
    description="Metin, görsel ve PDF için yerel kişisel veri maskeleme servisi.",
)


@app.middleware("http")
async def prevent_api_caching(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data: blob:; "
        "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
        "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


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


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Dosya boyutu 10 MB sınırını aşıyor.")
    return data


@app.post("/api/document/scan")
async def scan_document_endpoint(file: Annotated[UploadFile, File(...)]) -> JSONResponse:
    data = await _read_upload(file)
    try:
        result = await run_in_threadpool(scan_document, data, file.filename or "document")
        payload = await run_in_threadpool(serialize_scan, result)
    except DocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="OCR işlemi başlatılamadı.") from exc
    return JSONResponse(payload, headers={"Cache-Control": "no-store"})


@app.post("/api/document/redact")
async def redact_document_endpoint(
    file: Annotated[UploadFile, File(...)],
    regions: Annotated[str, Form(...)],
    fingerprint: Annotated[str, Form(...)],
) -> Response:
    data = await _read_upload(file)
    try:
        output, media_type, filename = await run_in_threadpool(
            redact_document, data, file.filename or "document", regions, fingerprint
        )
    except DocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    disposition = f"attachment; filename*=UTF-8''{quote(filename)}"
    return Response(
        output,
        media_type=media_type,
        headers={"Content-Disposition": disposition, "Cache-Control": "no-store"},
    )


app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
