from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Protocol

import pymupdf
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from .detectors import detect

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PAGES = 10
PDF_DPI = 150
MAX_IMAGE_SIDE = 20_000
MAX_OCR_LINES = 5_000
MAX_REDACTION_BOXES = 500
SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "TIFF"}


class DocumentError(ValueError):
    """Raised when an uploaded document cannot be processed safely."""


@dataclass(frozen=True, slots=True)
class OcrLine:
    text: str
    confidence: float
    polygon: tuple[tuple[float, float], ...]


@dataclass(frozen=True, slots=True)
class PageImage:
    number: int
    image: Image.Image


@dataclass(frozen=True, slots=True)
class SensitiveRegion:
    id: str
    page: int
    x: int
    y: int
    width: int
    height: int
    kinds: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class ScanResult:
    fingerprint: str
    source_kind: str
    pages: list[PageImage]
    regions: list[SensitiveRegion]
    ocr_line_count: int
    low_confidence_count: int


@dataclass(frozen=True, slots=True)
class RedactionBox:
    page: int
    x: int
    y: int
    width: int
    height: int


class OcrEngine(Protocol):
    def recognize(self, image: Image.Image) -> list[OcrLine]: ...


class RapidOcrEngine:
    """Lazy adapter around RapidOCR so importing the API does not load models."""

    _inference_lock = Lock()

    def __init__(self) -> None:
        from rapidocr import RapidOCR

        self._engine = RapidOCR()

    def recognize(self, image: Image.Image) -> list[OcrLine]:
        import numpy as np

        with self._inference_lock:
            result = self._engine(np.asarray(image.convert("RGB")))
        if result is None or result.boxes is None or result.txts is None or result.scores is None:
            return []
        lines: list[OcrLine] = []
        for box, text, score in zip(result.boxes, result.txts, result.scores, strict=True):
            polygon = tuple((float(point[0]), float(point[1])) for point in box)
            lines.append(OcrLine(str(text), float(score), polygon))
        return lines


@lru_cache(maxsize=1)
def get_ocr_engine() -> OcrEngine:
    return RapidOcrEngine()


def content_fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_image(data: bytes) -> Image.Image:
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in SUPPORTED_IMAGE_FORMATS:
                raise DocumentError("Yalnız PNG, JPEG, WEBP ve TIFF görselleri desteklenir.")
            if getattr(source, "n_frames", 1) > 1:
                raise DocumentError("Çok kareli görseller yerine PDF kullanın.")
            if source.width * source.height > 30_000_000:
                raise DocumentError("Görsel çözünürlüğü 30 megapikseli aşamaz.")
            if source.width > MAX_IMAGE_SIDE or source.height > MAX_IMAGE_SIDE:
                raise DocumentError("Görselin bir kenarı 20.000 pikseli aşamaz.")
            source.load()
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as exc:
        raise DocumentError("Görsel dosyası okunamadı.") from exc
    return image


def load_pages(data: bytes, filename: str = "document") -> tuple[str, list[PageImage]]:
    if not data:
        raise DocumentError("Dosya boş.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentError("Dosya boyutu 10 MB sınırını aşıyor.")

    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" or b"%PDF-" in data[:1024]:
        try:
            document = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise DocumentError("PDF dosyası açılamadı.") from exc
        try:
            if document.needs_pass:
                raise DocumentError("Parolalı PDF dosyaları desteklenmiyor.")
            if document.page_count == 0:
                raise DocumentError("PDF içinde sayfa bulunamadı.")
            if document.page_count > MAX_PAGES:
                raise DocumentError(f"PDF en fazla {MAX_PAGES} sayfa olabilir.")
            pages: list[PageImage] = []
            for number, page in enumerate(document):
                estimated_width = page.rect.width * PDF_DPI / 72
                estimated_height = page.rect.height * PDF_DPI / 72
                if estimated_width * estimated_height > 30_000_000:
                    raise DocumentError(f"PDF sayfa {number + 1}, 30 megapiksel sınırını aşıyor.")
                if estimated_width > MAX_IMAGE_SIDE or estimated_height > MAX_IMAGE_SIDE:
                    message = f"PDF sayfa {number + 1}, 20.000 piksel kenar sınırını aşıyor."
                    raise DocumentError(message)
                pixmap = page.get_pixmap(dpi=PDF_DPI, colorspace=pymupdf.csRGB, alpha=False)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                pages.append(PageImage(number, image))
            return "pdf", pages
        finally:
            document.close()

    return "image", [PageImage(0, _load_image(data))]


def _rect_from_polygon(
    polygon: tuple[tuple[float, float], ...], image: Image.Image, padding: int = 6
) -> tuple[int, int, int, int]:
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    left = max(0, int(min(xs)) - padding)
    top = max(0, int(min(ys)) - padding)
    right = min(image.width, int(max(xs)) + padding)
    bottom = min(image.height, int(max(ys)) + padding)
    return left, top, max(1, right - left), max(1, bottom - top)


def scan_document(
    data: bytes, filename: str, engine: OcrEngine | None = None, confidence_threshold: float = 0.55
) -> ScanResult:
    source_kind, pages = load_pages(data, filename)
    ocr = engine or get_ocr_engine()
    regions: list[SensitiveRegion] = []
    line_count = 0
    low_confidence_count = 0

    for page in pages:
        lines = ocr.recognize(page.image)
        line_count += len(lines)
        if line_count > MAX_OCR_LINES:
            message = "Belgedeki OCR satırı sınırı aşıldı; belgeyi bölerek yeniden deneyin."
            raise DocumentError(message)
        for line_number, line in enumerate(lines):
            if line.confidence < confidence_threshold:
                low_confidence_count += 1
            findings = detect(line.text)
            if not findings:
                continue
            x, y, width, height = _rect_from_polygon(line.polygon, page.image)
            kinds = tuple(sorted({finding.kind.value for finding in findings}))
            regions.append(
                SensitiveRegion(
                    id=f"p{page.number}-l{line_number}", page=page.number,
                    x=x, y=y, width=width, height=height,
                    kinds=kinds, confidence=round(line.confidence, 3),
                )
            )
            if len(regions) > MAX_REDACTION_BOXES:
                raise DocumentError("Hassas alan sınırı aşıldı; belgeyi bölerek yeniden deneyin.")

    return ScanResult(
        fingerprint=content_fingerprint(data), source_kind=source_kind, pages=pages,
        regions=regions, ocr_line_count=line_count, low_confidence_count=low_confidence_count,
    )


def page_to_data_url(page: PageImage, max_preview_width: int = 1400) -> tuple[str, int, int]:
    image = page.image
    if image.width > max_preview_width:
        ratio = max_preview_width / image.width
        size = (max_preview_width, round(image.height * ratio))
        preview = image.resize(size, Image.Resampling.LANCZOS)
    else:
        preview = image.copy()
    buffer = io.BytesIO()
    preview.save(buffer, format="JPEG", quality=86, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}", preview.width, preview.height


def serialize_scan(result: ScanResult) -> dict[str, object]:
    previews: list[dict[str, object]] = []
    scales: dict[int, tuple[float, float]] = {}
    for page in result.pages:
        data_url, width, height = page_to_data_url(page)
        previews.append(
            {"number": page.number, "width": width, "height": height, "image": data_url}
        )
        scales[page.number] = (width / page.image.width, height / page.image.height)

    regions = []
    for region in result.regions:
        scale_x, scale_y = scales[region.page]
        regions.append({
            "id": region.id,
            "page": region.page,
            "x": round(region.x * scale_x),
            "y": round(region.y * scale_y),
            "width": round(region.width * scale_x),
            "height": round(region.height * scale_y),
            "kinds": region.kinds,
            "confidence": region.confidence,
        })
    return {
        "fingerprint": result.fingerprint,
        "source_kind": result.source_kind,
        "pages": previews,
        "regions": regions,
        "summary": {
            "page_count": len(result.pages), "ocr_line_count": result.ocr_line_count,
            "region_count": len(result.regions),
            "low_confidence_count": result.low_confidence_count,
        },
        "raw_ocr_text_returned": False,
    }


def parse_redaction_boxes(raw: str, pages: list[PageImage]) -> list[RedactionBox]:
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DocumentError("Maskeleme alanları geçerli JSON değil.") from exc
    if not isinstance(items, list) or len(items) > MAX_REDACTION_BOXES:
        message = f"Maskeleme alanları bir liste olmalı ve {MAX_REDACTION_BOXES} adedi aşmamalıdır."
        raise DocumentError(message)

    boxes: list[RedactionBox] = []
    for item in items:
        if not isinstance(item, dict):
            raise DocumentError("Maskeleme alanı biçimi geçersiz.")
        try:
            page_number = int(item["page"])
            preview_width = float(item["preview_width"])
            preview_height = float(item["preview_height"])
            x, y = float(item["x"]), float(item["y"])
            width, height = float(item["width"]), float(item["height"])
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise DocumentError("Maskeleme alanında eksik veya geçersiz değer var.") from exc
        numeric_values = (preview_width, preview_height, x, y, width, height)
        if not all(math.isfinite(value) for value in numeric_values):
            raise DocumentError("Maskeleme alanındaki değerler sonlu sayı olmalıdır.")
        unknown_page = page_number < 0 or page_number >= len(pages)
        invalid_preview = not (
            1 <= preview_width <= MAX_IMAGE_SIDE and 1 <= preview_height <= MAX_IMAGE_SIDE
        )
        if unknown_page or invalid_preview:
            raise DocumentError("Maskeleme alanı bilinmeyen bir sayfaya ait.")
        if width <= 0 or height <= 0:
            raise DocumentError("Maskeleme alanının boyutu sıfır olamaz.")
        outside_preview = (
            x < 0
            or y < 0
            or x >= preview_width
            or y >= preview_height
            or x + width > preview_width + 1
            or y + height > preview_height + 1
        )
        if outside_preview:
            raise DocumentError("Maskeleme alanı sayfa sınırları dışında.")
        page = pages[page_number]
        scale_x = page.image.width / preview_width
        scale_y = page.image.height / preview_height
        left = max(0, min(page.image.width, round(x * scale_x)))
        top = max(0, min(page.image.height, round(y * scale_y)))
        right = max(left, min(page.image.width, round((x + width) * scale_x)))
        bottom = max(top, min(page.image.height, round((y + height) * scale_y)))
        if right <= left or bottom <= top:
            raise DocumentError("Maskeleme alanı piksele dönüştürülemedi.")
        boxes.append(RedactionBox(page_number, left, top, right - left, bottom - top))
    return boxes


def redact_document(
    data: bytes, filename: str, raw_boxes: str, fingerprint: str
) -> tuple[bytes, str, str]:
    valid_fingerprint = re.fullmatch(r"[0-9a-fA-F]{64}", fingerprint)
    if valid_fingerprint is None or not hmac.compare_digest(
        content_fingerprint(data), fingerprint.lower()
    ):
        raise DocumentError("Dosya, taranan belgeyle eşleşmiyor.")
    source_kind, pages = load_pages(data, filename)
    boxes = parse_redaction_boxes(raw_boxes, pages)
    by_page: dict[int, list[RedactionBox]] = {}
    for box in boxes:
        by_page.setdefault(box.page, []).append(box)

    redacted_pages: list[Image.Image] = []
    for page in pages:
        image = page.image.copy()
        draw = ImageDraw.Draw(image)
        for box in by_page.get(page.number, []):
            draw.rectangle(
                (box.x, box.y, box.x + box.width, box.y + box.height),
                fill=(0, 0, 0), outline=(0, 0, 0), width=2,
            )
        redacted_pages.append(image)

    stem = Path(filename).stem or "belge"
    if source_kind == "image":
        output = io.BytesIO()
        redacted_pages[0].save(output, format="PNG", optimize=True)
        return output.getvalue(), "image/png", f"{stem}-maskeli.png"

    output_pdf = pymupdf.open()
    try:
        for image in redacted_pages:
            png = io.BytesIO()
            image.save(png, format="PNG", optimize=True)
            width_points = image.width * 72 / PDF_DPI
            height_points = image.height * 72 / PDF_DPI
            page = output_pdf.new_page(width=width_points, height=height_points)
            page.insert_image(page.rect, stream=png.getvalue())
        return output_pdf.tobytes(garbage=4, deflate=True), "application/pdf", f"{stem}-maskeli.pdf"
    finally:
        output_pdf.close()
