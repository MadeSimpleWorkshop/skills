#!/usr/bin/env python3
"""Parse Camtasia XMP/XML markers into YouTube chapter timestamps."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

XMP_DM_NS = "http://ns.adobe.com/xmp/1.0/DynamicMedia/"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

NS = {
    "xmpDM": XMP_DM_NS,
    "rdf": RDF_NS,
}

START_ATTR = f"{{{XMP_DM_NS}}}startTime"
NAME_ATTR = f"{{{XMP_DM_NS}}}name"
CHAPTERS_START_TAG = "<!-- CAMTASIA_CHAPTERS_START -->"
CHAPTERS_END_TAG = "<!-- CAMTASIA_CHAPTERS_END -->"


@dataclass(frozen=True)
class Marker:
    start_ms: int
    name: str


def normalize_label(value: str) -> str:
    return " ".join(value.split()).strip()


def format_timestamp(start_ms: int) -> str:
    total_seconds = max(0, start_ms // 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def parse_markers(
    xml_path: Path,
    include_placeholder: bool,
    placeholder_names: set[str],
    min_gap_seconds: float,
) -> list[Marker]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    markers: list[Marker] = []
    for entry in root.findall(".//xmpDM:markers/rdf:Seq/rdf:li/rdf:Description", NS):
        raw_start = entry.attrib.get(START_ATTR)
        raw_name = entry.attrib.get(NAME_ATTR, "")
        if raw_start is None:
            continue

        try:
            start_ms = int(float(raw_start))
        except ValueError:
            continue

        name = normalize_label(raw_name)
        if not name:
            continue

        if not include_placeholder and name.lower() in placeholder_names:
            continue

        markers.append(Marker(start_ms=start_ms, name=name))

    markers.sort(key=lambda item: item.start_ms)

    deduped: list[Marker] = []
    seen: set[tuple[int, str]] = set()
    min_gap_ms = max(0, int(min_gap_seconds * 1000))
    last_kept_ms: int | None = None

    for marker in markers:
        key = (marker.start_ms, marker.name.lower())
        if key in seen:
            continue
        seen.add(key)

        if last_kept_ms is not None and (marker.start_ms - last_kept_ms) < min_gap_ms:
            continue

        deduped.append(marker)
        last_kept_ms = marker.start_ms

    return deduped


def build_chapter_lines(
    markers: list[Marker],
    ensure_zero: bool,
    intro_title: str,
) -> list[str]:
    chapter_markers = list(markers)

    if ensure_zero and (not chapter_markers or chapter_markers[0].start_ms > 0):
        chapter_markers.insert(0, Marker(start_ms=0, name=normalize_label(intro_title) or "Intro"))

    lines: list[str] = []
    used_timestamps: set[str] = set()

    for marker in chapter_markers:
        timestamp = format_timestamp(marker.start_ms)
        if timestamp in used_timestamps:
            continue
        used_timestamps.add(timestamp)
        lines.append(f"{timestamp} {marker.name}")

    return lines


def build_json_payload(lines: list[str]) -> str:
    chapters = []
    for line in lines:
        stamp, title = line.split(" ", 1)
        chapters.append({"timestamp": stamp, "title": title})

    return json.dumps({"chapters": chapters, "count": len(chapters)}, indent=2)


def merge_chapters_into_description(
    existing: str,
    chapter_lines: list[str],
    heading: str,
) -> str:
    section_parts = [CHAPTERS_START_TAG]
    if heading.strip():
        section_parts.append(heading.rstrip())
    section_parts.extend(chapter_lines)
    section_parts.append(CHAPTERS_END_TAG)
    section = "\n".join(section_parts)

    pattern = re.compile(
        re.escape(CHAPTERS_START_TAG) + r".*?" + re.escape(CHAPTERS_END_TAG),
        re.DOTALL,
    )

    if CHAPTERS_START_TAG in existing and CHAPTERS_END_TAG in existing:
        updated = pattern.sub(section, existing)
        return updated.rstrip() + "\n"

    if existing.strip():
        return existing.rstrip() + "\n\n" + section + "\n"

    return section + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Camtasia XMP/XML markers into YouTube chapter timestamps."
    )
    parser.add_argument("xml_file", type=Path, help="Path to Camtasia XML/XMP marker file")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for chapter output",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write chapter output (text/json) to this file instead of stdout",
    )
    parser.add_argument(
        "--include-placeholder",
        action="store_true",
        help="Keep placeholder markers (default skips names like 'Marker')",
    )
    parser.add_argument(
        "--placeholder-name",
        action="append",
        default=["Marker"],
        help="Marker name to treat as placeholder (repeatable)",
    )
    parser.add_argument(
        "--min-gap-seconds",
        type=float,
        default=0.0,
        help="Drop markers that occur within this many seconds of a kept marker",
    )

    zero_group = parser.add_mutually_exclusive_group()
    zero_group.add_argument(
        "--ensure-zero",
        dest="ensure_zero",
        action="store_true",
        default=True,
        help="Ensure a 0:00 chapter exists (default: true)",
    )
    zero_group.add_argument(
        "--no-ensure-zero",
        dest="ensure_zero",
        action="store_false",
        help="Do not add a 0:00 chapter automatically",
    )

    parser.add_argument(
        "--intro-title",
        default="Intro",
        help="Title to use when auto-inserting a 0:00 chapter",
    )
    parser.add_argument(
        "--description-in",
        type=Path,
        help="Optional existing YouTube description file to inject chapters into",
    )
    parser.add_argument(
        "--description-out",
        type=Path,
        help="Write merged description with chapter block to this file",
    )
    parser.add_argument(
        "--heading",
        default="Chapters:",
        help="Heading line used in merged description",
    )

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if not args.xml_file.exists():
        print(f"Error: file not found: {args.xml_file}", file=sys.stderr)
        return 1

    placeholder_names = {normalize_label(name).lower() for name in args.placeholder_name if name.strip()}

    try:
        markers = parse_markers(
            xml_path=args.xml_file,
            include_placeholder=args.include_placeholder,
            placeholder_names=placeholder_names,
            min_gap_seconds=args.min_gap_seconds,
        )
    except ET.ParseError as exc:
        print(f"Error: invalid XML: {exc}", file=sys.stderr)
        return 1

    if not markers:
        print("Error: no usable markers found", file=sys.stderr)
        return 1

    chapter_lines = build_chapter_lines(
        markers=markers,
        ensure_zero=args.ensure_zero,
        intro_title=args.intro_title,
    )

    chapter_output = "\n".join(chapter_lines)
    formatted_output = build_json_payload(chapter_lines) if args.format == "json" else chapter_output

    if args.output:
        write_text(args.output, formatted_output + ("\n" if not formatted_output.endswith("\n") else ""))
    else:
        print(formatted_output)

    if args.description_in or args.description_out:
        existing = ""
        if args.description_in:
            if not args.description_in.exists():
                print(f"Error: description file not found: {args.description_in}", file=sys.stderr)
                return 1
            existing = args.description_in.read_text(encoding="utf-8")

        merged = merge_chapters_into_description(
            existing=existing,
            chapter_lines=chapter_lines,
            heading=args.heading,
        )

        if args.description_out:
            write_text(args.description_out, merged)
        else:
            print("\n" + merged)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
