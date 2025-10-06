"""Command line interface for the Multiscope analysis pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .report import generate_demo_report, generate_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Multiscope multimodal analysis pipeline")
    parser.add_argument(
        "media",
        type=Path,
        nargs="?",
        help="Path to the video file to analyse (omit when using --demo)",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Optional JSON file containing contextual metadata (location, era, etc.)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="If provided, write the resulting report to this JSON file instead of stdout",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Generate a sample report without requiring a media file for quick previewing",
    )

    args = parser.parse_args(argv)

    if args.demo and args.media is not None:
        parser.error("Positional media argument is not allowed when using --demo.")
    if not args.demo and args.media is None:
        parser.error("the following arguments are required: media")

    return args


def _load_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")
    with path.open("r", encoding="utf8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    metadata = _load_metadata(args.metadata)

    if args.demo:
        report = generate_demo_report(metadata=metadata)
    else:
        report = generate_report(args.media, metadata=metadata)
    payload = {
        "musical": report.musical.__dict__,
        "dance": report.dance.__dict__,
        "ethnography": {
            "summary": report.ethnography.summary,
            "musical_context": report.ethnography.musical_context,
            "dance_context": report.ethnography.dance_context,
            "cultural_indicators": report.ethnography.cultural_indicators,
        },
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf8") as handle:
            json.dump(payload, handle, indent=2)
    else:
        print(json.dumps(payload, indent=2))

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

