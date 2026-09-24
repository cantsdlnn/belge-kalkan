import io
import json
from types import SimpleNamespace

import numpy as np
import pymupdf
import pytest
from PIL import Image, ImageDraw

from belgekalkan.documents import (
    DocumentError,
    OcrLine,
    RapidOcrEngine,
    content_fingerprint,
    get_ocr_engine,
    load_pages,
    parse_redaction_boxes,
    redact_document,
    scan_document,
    serialize_scan,
)


class FakeOcr:
    def __init__(self, lines: list[OcrLine] | None = None) -> None:
        self.lines = lines or []

    def recognize(self, _image: Image.Image) -> list[OcrLine]:
        return self.lines


def png_bytes(
    width: int = 500, height: int = 200, color: str | tuple[int, int, int] = "white"
) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="PNG")
    return buffer.getvalue()


def pdf_bytes() -> bytes:
    document = pymupdf.open()
    page = document.new_page(width=300, height=200)
    page.insert_text((30, 60), "10000000146", fontsize=18)
    data = document.tobytes()
    document.close()
    return data


def test_scan_finds_sensitive_line_without_returning_raw_ocr_text() -> None:
    line = OcrLine("T.C. 10000000146", 0.94, ((30, 20), (260, 20), (260, 70), (30, 70)))
    result = scan_document(png_bytes(), "shot.png", FakeOcr([line]))

    assert result.source_kind == "image"
    assert result.regions[0].kinds == ("tckn",)
    assert result.regions[0].x > 70
    assert result.regions[0].width < 190
    payload = serialize_scan(result)
    assert payload["raw_ocr_text_returned"] is False
    assert "10000000146" not in json.dumps(payload)
    assert str(payload["pages"][0]["image"]).startswith("data:image/jpeg;base64,")


def test_scan_creates_separate_tight_regions_for_multiple_findings_on_one_line() -> None:
    text = "Kimlik 10000000146 E-posta test@example.com"
    line = OcrLine(text, 0.96, ((20, 20), (440, 20), (440, 60), (20, 60)))
    result = scan_document(png_bytes(), "shot.png", FakeOcr([line]))

    assert [region.kinds for region in result.regions] == [("tckn",), ("email",)]
    assert result.regions[0].x + result.regions[0].width < result.regions[1].x
    assert all(region.width < 220 for region in result.regions)


def test_scan_counts_low_confidence_lines_even_without_detection() -> None:
    line = OcrLine("okunamayan alan", 0.31, ((1, 1), (20, 1), (20, 10), (1, 10)))
    result = scan_document(png_bytes(), "shot.png", FakeOcr([line]))
    assert result.low_confidence_count == 1
    assert result.regions == []


def test_scan_rejects_excessive_ocr_output_instead_of_silent_truncation() -> None:
    plain = OcrLine("normal", 0.9, ((1, 1), (20, 1), (20, 10), (1, 10)))
    with pytest.raises(DocumentError, match="OCR satırı sınırı"):
        scan_document(png_bytes(), "shot.png", FakeOcr([plain] * 5_001))

    sensitive = OcrLine("10000000146", 0.9, ((1, 1), (20, 1), (20, 10), (1, 10)))
    with pytest.raises(DocumentError, match="Hassas alan sınırı"):
        scan_document(png_bytes(), "shot.png", FakeOcr([sensitive] * 501))


def test_rapid_ocr_adapter_maps_engine_output() -> None:
    engine = RapidOcrEngine.__new__(RapidOcrEngine)
    engine._engine = lambda _array: SimpleNamespace(
        boxes=np.array([[[1, 2], [20, 2], [20, 10], [1, 10]]]),
        txts=("test@example.com",),
        scores=(0.88,),
    )
    lines = engine.recognize(Image.new("RGB", (30, 20), "white"))
    expected_polygon = ((1.0, 2.0), (20.0, 2.0), (20.0, 10.0), (1.0, 10.0))
    assert lines == [OcrLine("test@example.com", 0.88, expected_polygon)]


def test_rapid_ocr_adapter_handles_empty_result() -> None:
    engine = RapidOcrEngine.__new__(RapidOcrEngine)
    engine._engine = lambda _array: None
    assert engine.recognize(Image.new("RGB", (20, 20))) == []


def test_real_rapid_ocr_engine_smoke() -> None:
    get_ocr_engine.cache_clear()
    engine = get_ocr_engine()
    assert engine is get_ocr_engine()
    lines = engine.recognize(Image.new("RGB", (320, 120), "white"))
    assert isinstance(lines, list)


def test_large_page_preview_and_region_coordinates_are_scaled() -> None:
    line = OcrLine("10000000146", 0.9, ((100, 10), (500, 10), (500, 60), (100, 60)))
    result = scan_document(png_bytes(1600, 200), "wide.png", FakeOcr([line]))
    payload = serialize_scan(result)
    page = payload["pages"][0]
    region = payload["regions"][0]
    assert page["width"] == 1400
    assert region["x"] < 100
    assert region["width"] < 400


def test_redacts_selected_image_area_to_black() -> None:
    source = png_bytes(100, 100)
    boxes = json.dumps([{
        "page": 0, "x": 10, "y": 20, "width": 30, "height": 20,
        "preview_width": 100, "preview_height": 100,
    }])
    output, media_type, filename = redact_document(
        source, "shot.png", boxes, content_fingerprint(source), "black"
    )
    image = Image.open(io.BytesIO(output)).convert("RGB")
    assert image.getpixel((20, 30)) == (0, 0, 0)
    assert image.getpixel((80, 80)) == (255, 255, 255)
    assert media_type == "image/png"
    assert filename == "shot-maskeli.png"


def test_redacts_image_area_with_sampled_local_background_by_default() -> None:
    background = (244, 240, 232)
    image = Image.new("RGB", (120, 90), background)
    ImageDraw.Draw(image).rectangle((30, 30, 79, 54), fill=(15, 15, 15))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    source = buffer.getvalue()
    boxes = json.dumps([{
        "page": 0, "x": 30, "y": 30, "width": 50, "height": 25,
        "preview_width": 120, "preview_height": 90,
    }])

    output, _, _ = redact_document(source, "form.png", boxes, content_fingerprint(source))
    redacted = Image.open(io.BytesIO(output)).convert("RGB")

    assert redacted.getpixel((50, 40)) == background
    assert redacted.getpixel((10, 10)) == background


def test_rejects_unknown_mask_style() -> None:
    source = png_bytes()
    with pytest.raises(DocumentError, match="Maske stili"):
        redact_document(source, "shot.png", "[]", content_fingerprint(source), "blur")  # type: ignore[arg-type]


def test_rebuilds_pdf_without_original_text_layer() -> None:
    source = pdf_bytes()
    boxes = json.dumps([{
        "page": 0, "x": 0, "y": 0, "width": 120, "height": 80,
        "preview_width": 625, "preview_height": 417,
    }])
    output, media_type, filename = redact_document(
        source, "form.pdf", boxes, content_fingerprint(source)
    )
    document = pymupdf.open(stream=output, filetype="pdf")
    try:
        assert document.page_count == 1
        assert document[0].get_text() == ""
    finally:
        document.close()
    assert media_type == "application/pdf"
    assert filename == "form-maskeli.pdf"


def test_rejects_mismatched_file_and_invalid_boxes() -> None:
    source = png_bytes()
    with pytest.raises(DocumentError, match="eşleşmiyor"):
        redact_document(source, "shot.png", "[]", "0" * 64)
    with pytest.raises(DocumentError, match="eşleşmiyor"):
        redact_document(source, "shot.png", "[]", "ş" * 64)
    _, pages = load_pages(source, "shot.png")
    with pytest.raises(DocumentError, match="JSON"):
        parse_redaction_boxes("not-json", pages)
    with pytest.raises(DocumentError, match="boyutu sıfır"):
        parse_redaction_boxes(
            '[{"page":0,"x":1,"y":1,"width":0,"height":2,"preview_width":500,"preview_height":200}]',
            pages,
        )


def test_rejects_fake_pdf_and_unsupported_image() -> None:
    with pytest.raises(DocumentError, match="boş"):
        load_pages(b"", "empty.png")
    with pytest.raises(DocumentError, match="PDF dosyası açılamadı"):
        load_pages(b"not a pdf", "fake.pdf")
    gif = io.BytesIO()
    Image.new("RGB", (20, 20)).save(gif, format="GIF")
    with pytest.raises(DocumentError, match="Yalnız PNG"):
        load_pages(gif.getvalue(), "image.gif")
    with pytest.raises(DocumentError, match="20.000"):
        load_pages(png_bytes(20_001, 1), "too-wide.png")


def test_rejects_multi_frame_image_and_too_many_pdf_pages() -> None:
    tiff = io.BytesIO()
    first = Image.new("RGB", (20, 20), "white")
    first.save(
        tiff,
        format="TIFF",
        save_all=True,
        append_images=[Image.new("RGB", (20, 20), "black")],
    )
    with pytest.raises(DocumentError, match="Çok kareli"):
        load_pages(tiff.getvalue(), "multi.tiff")

    document = pymupdf.open()
    for _ in range(11):
        document.new_page(width=100, height=100)
    data = document.tobytes()
    document.close()
    with pytest.raises(DocumentError, match="en fazla 10"):
        load_pages(data, "long.pdf")
