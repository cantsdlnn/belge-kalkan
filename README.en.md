# BelgeKalkan

BelgeKalkan is a local redaction web service for Turkish personal-data patterns in text, screenshots, and scanned PDFs, with an additional CLI for text input. It runs OCR locally with RapidOCR and ONNX Runtime, detects Turkish identity numbers and IBANs with checksum validation, and supports email addresses and Turkish mobile numbers. Users review the detected boxes, toggle them individually, add manual regions, and download a redacted PNG or flattened PDF.

The API does not persist uploads or return raw OCR text as a separate field. PDF output is rebuilt from redacted page images so the original selectable text layer is not retained. The project includes FastAPI, a CLI, automated tests, Ruff checks, Docker packaging, CI, documented limits, and an explicit AI-use disclosure. It is a pre-sharing aid, not a complete DLP system; human review remains necessary.

See the [Turkish README](README.md) for setup, architecture, limitations, and screenshots.
