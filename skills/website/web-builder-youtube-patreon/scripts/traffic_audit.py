#!/usr/bin/env python3
"""Audit local and live HTML for YouTube/Patreon traffic conversion signals."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional


CTA_KEYWORDS = {
    "subscribe",
    "watch",
    "youtube",
    "patreon",
    "join",
    "support",
    "member",
    "members",
}


def contains_any(text: str, values: set[str]) -> bool:
    lowered = text.lower()
    return any(value in lowered for value in values)


def normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


@dataclass
class AuditResult:
    source: str
    title: str = ""
    meta_description: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    h1_count: int = 0
    h2_count: int = 0
    forms_count: int = 0
    iframe_count: int = 0
    links_count: int = 0
    cta_links_count: int = 0
    youtube_links_count: int = 0
    patreon_links_count: int = 0
    cta_examples: List[str] = field(default_factory=list)

    def key_metrics(self) -> Dict[str, object]:
        return {
            "title_present": bool(self.title),
            "meta_description_present": bool(self.meta_description),
            "og_title_present": bool(self.og_title),
            "og_description_present": bool(self.og_description),
            "og_image_present": bool(self.og_image),
            "h1_count": self.h1_count,
            "h2_count": self.h2_count,
            "forms_count": self.forms_count,
            "iframe_count": self.iframe_count,
            "links_count": self.links_count,
            "cta_links_count": self.cta_links_count,
            "youtube_links_count": self.youtube_links_count,
            "patreon_links_count": self.patreon_links_count,
        }


class SignalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_text: List[str] = []
        self.h1_count = 0
        self.h2_count = 0
        self.forms_count = 0
        self.iframe_count = 0
        self.links_count = 0
        self.cta_links_count = 0
        self.youtube_links_count = 0
        self.patreon_links_count = 0
        self.cta_examples: List[str] = []
        self.meta: Dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        attrs_map = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower == "title":
            self.in_title = True
        if tag_lower == "h1":
            self.h1_count += 1
        if tag_lower == "h2":
            self.h2_count += 1
        if tag_lower == "form":
            self.forms_count += 1
        if tag_lower == "iframe":
            self.iframe_count += 1
        if tag_lower == "meta":
            self._parse_meta(attrs_map)
        if tag_lower == "a":
            self._parse_anchor(attrs_map)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_text.append(data)

    def _parse_meta(self, attrs_map: Dict[str, str]) -> None:
        name = attrs_map.get("name", "").strip().lower()
        prop = attrs_map.get("property", "").strip().lower()
        content = normalize_text(attrs_map.get("content", ""))
        if not content:
            return
        if name == "description":
            self.meta["description"] = content
        if prop == "og:title":
            self.meta["og:title"] = content
        if prop == "og:description":
            self.meta["og:description"] = content
        if prop == "og:image":
            self.meta["og:image"] = content

    def _parse_anchor(self, attrs_map: Dict[str, str]) -> None:
        self.links_count += 1
        href = attrs_map.get("href", "")
        text_fields = [
            attrs_map.get("aria-label", ""),
            attrs_map.get("title", ""),
            attrs_map.get("class", ""),
            attrs_map.get("id", ""),
        ]
        joined_text = normalize_text(" ".join(text_fields))
        joined = normalize_text(f"{href} {joined_text}")

        if "youtube.com" in href or "youtu.be" in href:
            self.youtube_links_count += 1
        if "patreon.com" in href:
            self.patreon_links_count += 1

        if contains_any(joined, CTA_KEYWORDS):
            self.cta_links_count += 1
            example = normalize_text(href or joined_text)
            if example and len(self.cta_examples) < 5:
                self.cta_examples.append(example)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit local/live HTML and generate YouTube+Patreon traffic recommendations."
    )
    parser.add_argument(
        "--html",
        help="Local HTML file path to audit.",
    )
    parser.add_argument(
        "--live-url",
        help="Live URL to fetch and audit.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the report.",
    )
    return parser.parse_args()


def read_local_html(path: str) -> str:
    html_path = pathlib.Path(path).expanduser().resolve()
    if not html_path.exists() or not html_path.is_file():
        raise FileNotFoundError(f"Local HTML file not found: {html_path}")
    return html_path.read_text(encoding="utf-8")


def read_live_html(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "web-builder-youtube-patreon-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def audit_html(source: str, html: str) -> AuditResult:
    parser = SignalParser()
    parser.feed(html)
    parser.close()

    return AuditResult(
        source=source,
        title=normalize_text("".join(parser.title_text)),
        meta_description=parser.meta.get("description", ""),
        og_title=parser.meta.get("og:title", ""),
        og_description=parser.meta.get("og:description", ""),
        og_image=parser.meta.get("og:image", ""),
        h1_count=parser.h1_count,
        h2_count=parser.h2_count,
        forms_count=parser.forms_count,
        iframe_count=parser.iframe_count,
        links_count=parser.links_count,
        cta_links_count=parser.cta_links_count,
        youtube_links_count=parser.youtube_links_count,
        patreon_links_count=parser.patreon_links_count,
        cta_examples=parser.cta_examples,
    )


def build_recommendations(local: Optional[AuditResult], live: Optional[AuditResult]) -> List[str]:
    target = local or live
    if target is None:
        return []

    recs: List[str] = []
    metrics = target.key_metrics()

    if target.youtube_links_count == 0:
        recs.append("Add a prominent YouTube CTA above the fold with a clear value promise.")
    if target.patreon_links_count == 0:
        recs.append("Add a Patreon CTA that explains supporter benefits before asking for commitment.")
    if target.cta_links_count < 2:
        recs.append("Increase CTA frequency and include both primary and mid-page CTA blocks.")
    if not metrics["meta_description_present"]:
        recs.append("Add a meta description tuned for the audience intent and YouTube/Patreon offer.")
    if not metrics["og_image_present"]:
        recs.append("Add an OpenGraph image to improve social preview click-through.")
    if target.h1_count != 1:
        recs.append("Use exactly one focused H1 to clarify the core promise on page load.")
    if target.forms_count == 0:
        recs.append("Add an email capture or freebie form to recover visitors not ready to convert.")

    if local and live:
        if local.youtube_links_count != live.youtube_links_count:
            recs.append("Align local and live YouTube link coverage to avoid rollout drift.")
        if local.patreon_links_count != live.patreon_links_count:
            recs.append("Align local and live Patreon link coverage to avoid rollout drift.")
        if bool(local.meta_description) != bool(live.meta_description):
            recs.append("Sync metadata between local and live pages before publishing.")

    if not recs:
        recs.append("Keep current structure and start A/B testing CTA copy and hero messaging.")
    return recs


def compare_metrics(local: Optional[AuditResult], live: Optional[AuditResult]) -> Dict[str, Dict[str, object]]:
    if not local or not live:
        return {}
    compared: Dict[str, Dict[str, object]] = {}
    local_metrics = local.key_metrics()
    live_metrics = live.key_metrics()
    for key in sorted(local_metrics.keys()):
        local_value = local_metrics[key]
        live_value = live_metrics[key]
        if local_value != live_value:
            compared[key] = {"local": local_value, "live": live_value}
    return compared


def to_markdown(
    local: Optional[AuditResult],
    live: Optional[AuditResult],
    differences: Dict[str, Dict[str, object]],
    recommendations: List[str],
) -> str:
    lines: List[str] = []
    lines.append("# Traffic Audit")
    lines.append("")

    def append_section(result: AuditResult, header: str) -> None:
        lines.append(f"## {header}")
        lines.append("")
        lines.append(f"- Source: `{result.source}`")
        lines.append(f"- Title present: `{bool(result.title)}`")
        lines.append(f"- Meta description present: `{bool(result.meta_description)}`")
        lines.append(f"- OG image present: `{bool(result.og_image)}`")
        lines.append(f"- H1 count: `{result.h1_count}`")
        lines.append(f"- CTA links: `{result.cta_links_count}`")
        lines.append(f"- YouTube links: `{result.youtube_links_count}`")
        lines.append(f"- Patreon links: `{result.patreon_links_count}`")
        if result.cta_examples:
            lines.append(f"- CTA examples: `{', '.join(result.cta_examples)}`")
        lines.append("")

    if local:
        append_section(local, "Local")
    if live:
        append_section(live, "Live")

    lines.append("## Key Differences")
    lines.append("")
    if differences:
        for key, values in differences.items():
            lines.append(f"- `{key}`: local=`{values['local']}` live=`{values['live']}`")
    else:
        lines.append("- None detected or only one source provided.")
    lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    for index, recommendation in enumerate(recommendations, start=1):
        lines.append(f"{index}. {recommendation}")
    lines.append("")

    return "\n".join(lines)


def to_json(
    local: Optional[AuditResult],
    live: Optional[AuditResult],
    differences: Dict[str, Dict[str, object]],
    recommendations: List[str],
) -> str:
    payload = {
        "local": local.__dict__ if local else None,
        "live": live.__dict__ if live else None,
        "differences": differences,
        "recommendations": recommendations,
    }
    return json.dumps(payload, indent=2)


def write_output(content: str, output_path: Optional[str]) -> None:
    if output_path:
        out = pathlib.Path(output_path).expanduser().resolve()
        out.write_text(content, encoding="utf-8")
        print(f"[OK] Wrote report: {out}", file=sys.stderr)
    else:
        print(content)


def main() -> int:
    args = parse_args()
    if not args.html and not args.live_url:
        print("[ERROR] Provide --html, --live-url, or both.", file=sys.stderr)
        return 1

    local_result: Optional[AuditResult] = None
    live_result: Optional[AuditResult] = None

    if args.html:
        try:
            local_html = read_local_html(args.html)
            local_result = audit_html(args.html, local_html)
        except (FileNotFoundError, OSError) as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    if args.live_url:
        try:
            live_html = read_live_html(args.live_url)
            live_result = audit_html(args.live_url, live_html)
        except (urllib.error.URLError, OSError) as exc:
            print(f"[ERROR] Failed to fetch {args.live_url}: {exc}", file=sys.stderr)
            return 1

    differences = compare_metrics(local_result, live_result)
    recommendations = build_recommendations(local_result, live_result)

    if args.format == "json":
        content = to_json(local_result, live_result, differences, recommendations)
    else:
        content = to_markdown(local_result, live_result, differences, recommendations)

    write_output(content, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
