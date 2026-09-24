from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .service import redact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metindeki kişisel verileri yerelde maskele.")
    parser.add_argument("input", type=Path, help="UTF-8 metin dosyası")
    parser.add_argument("--output", "-o", type=Path, help="Maskelenmiş çıktı dosyası")
    parser.add_argument("--manifest", type=Path, help="Değer içermeyen işlem manifesti")
    parser.add_argument("--mode", choices=("label", "mask"), default="label")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    text = args.input.read_text(encoding="utf-8")
    result = redact(text, args.mode)
    if args.output:
        args.output.write_text(result.redacted_text, encoding="utf-8")
    else:
        sys.stdout.write(result.redacted_text)
    if args.manifest:
        args.manifest.write_text(
            json.dumps(result.manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

