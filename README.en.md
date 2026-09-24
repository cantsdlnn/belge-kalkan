# BelgeKalkan

BelgeKalkan is a local, deterministic redaction service and CLI for Turkish personal-data patterns. It detects Turkish identity numbers and IBANs with checksum validation, as well as email addresses and Turkish mobile numbers. The API returns finding types and coordinates without echoing raw sensitive values.

The project includes FastAPI, a CLI, 18 automated tests with 97% line coverage, Ruff checks, Docker packaging, CI, a security boundary, and an explicit AI-use disclosure. It is a pre-sharing aid, not a complete DLP system; human review remains necessary.

See the [Turkish README](README.md) for setup, architecture, limitations, and screenshots.

