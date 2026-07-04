#!/usr/bin/env python3
"""Audit website color tokens, variable usage, and pattern coverage."""

from __future__ import annotations

import argparse
import colorsys
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


IGNORE_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "coverage",
    ".cache",
    ".idea",
    ".vscode",
    "__pycache__",
}

SOURCE_SUFFIXES = {
    ".html",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
}

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB_RE = re.compile(r"rgba?\([^()]+\)", flags=re.IGNORECASE)
HSL_RE = re.compile(r"hsla?\([^()]+\)", flags=re.IGNORECASE)
VAR_DEF_RE = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;}{\n]+)")
GRADIENT_RE = re.compile(
    r"(?:linear|radial|conic)-gradient\([^;}{\n]+\)",
    flags=re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a website codebase for color token quality and pattern consistency.",
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Website root directory to scan.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Top N color tokens to report (default: 20).",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path.",
    )
    return parser.parse_args()


def normalize_color_token(raw_token: str) -> str:
    token = raw_token.strip().lower()
    if token.startswith("#"):
        hex_part = token[1:]
        if len(hex_part) in (3, 4):
            expanded = "".join(ch * 2 for ch in hex_part)
            return f"#{expanded}"
        return token
    return re.sub(r"\s+", "", token)


def hex_to_rgb(color: str) -> Optional[Tuple[int, int, int]]:
    token = normalize_color_token(color)
    if not token.startswith("#"):
        return None
    hex_part = token[1:]
    if len(hex_part) == 8:
        hex_part = hex_part[:6]
    if len(hex_part) != 6:
        return None
    try:
        return (
            int(hex_part[0:2], 16),
            int(hex_part[2:4], 16),
            int(hex_part[4:6], 16),
        )
    except ValueError:
        return None


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    def to_linear(channel: int) -> float:
        value = channel / 255.0
        if value <= 0.03928:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    r_lin = to_linear(r)
    g_lin = to_linear(g)
    b_lin = to_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def saturation_score(rgb: Tuple[int, int, int]) -> float:
    r, g, b = rgb
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    _ = h, l
    return s


def contrast_ratio(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    lum_a = relative_luminance(a)
    lum_b = relative_luminance(b)
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def iter_source_files(root: Path) -> Iterable[Path]:
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        current = Path(current_root)
        for filename in files:
            file_path = current / filename
            if file_path.suffix.lower() in SOURCE_SUFFIXES:
                yield file_path


def collect_color_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    for pattern in (HEX_RE, RGB_RE, HSL_RE):
        tokens.extend(pattern.findall(text))
    return [normalize_color_token(token) for token in tokens]


def build_recommendations(
    total_tokens: int,
    unique_tokens: int,
    variable_defs_total: int,
    gradient_count: int,
    color_counter: Counter,
) -> List[str]:
    recommendations: List[str] = []
    hardcoded_ratio = 0.0
    if total_tokens:
        hardcoded_ratio = max(total_tokens - variable_defs_total, 0) / total_tokens

    if unique_tokens > 16:
        recommendations.append(
            "Reduce palette sprawl by mapping repeated literals into semantic CSS variables."
        )
    if variable_defs_total == 0:
        recommendations.append(
            "Define a :root token system before redesign work to centralize theme updates."
        )
    if variable_defs_total > 0 and hardcoded_ratio > 0.65:
        recommendations.append(
            "Replace hard-coded literals with token references to make future rebranding safer."
        )
    if gradient_count == 0:
        recommendations.append(
            "Introduce a subtle background pattern or gradient layer to add depth."
        )

    hex_candidates = [token for token in color_counter if token.startswith("#") and hex_to_rgb(token)]
    if len(hex_candidates) >= 2:
        darkest = min(hex_candidates, key=lambda token: relative_luminance(hex_to_rgb(token) or (0, 0, 0)))
        lightest = max(
            hex_candidates,
            key=lambda token: relative_luminance(hex_to_rgb(token) or (255, 255, 255)),
        )
        contrast = contrast_ratio(hex_to_rgb(darkest) or (0, 0, 0), hex_to_rgb(lightest) or (255, 255, 255))
        if contrast < 4.5:
            recommendations.append(
                "Increase contrast between primary text and background tokens to meet readability goals."
            )

    if not recommendations:
        recommendations.append(
            "Color token structure is reasonably controlled; prioritize pattern and accent hierarchy experiments."
        )
    return recommendations


def report_to_markdown(report: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# Color Design Audit")
    lines.append("")
    lines.append(f"- Root: `{report['root']}`")
    lines.append(f"- Files scanned: `{report['files_scanned']}`")
    lines.append(f"- Files with color tokens: `{report['files_with_colors']}`")
    lines.append(f"- Total color token hits: `{report['total_color_tokens']}`")
    lines.append(f"- Unique color tokens: `{report['unique_color_tokens']}`")
    lines.append(f"- Gradient hits: `{report['gradient_hits']}`")
    lines.append("")

    lines.append("## Top Color Tokens")
    lines.append("")
    if report["top_color_tokens"]:
        for item in report["top_color_tokens"]:
            detail = f"- `{item['token']}` x `{item['count']}`"
            if "luminance" in item and "saturation" in item:
                detail += f" (lum={item['luminance']}, sat={item['saturation']})"
            lines.append(detail)
            if item["example_files"]:
                lines.append(f"  examples: `{', '.join(item['example_files'])}`")
    else:
        lines.append("- No color tokens found.")
    lines.append("")

    lines.append("## CSS Variables")
    lines.append("")
    if report["top_variables"]:
        for item in report["top_variables"]:
            lines.append(
                f"- `{item['name']}` defined `{item['count']}` times; common values: `{', '.join(item['values'])}`"
            )
    else:
        lines.append("- No CSS variable definitions detected.")
    lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    for index, recommendation in enumerate(report["recommendations"], start=1):
        lines.append(f"{index}. {recommendation}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] Root directory not found: {root}", file=sys.stderr)
        return 1

    color_counter: Counter = Counter()
    color_examples: Dict[str, List[str]] = defaultdict(list)
    variable_counts: Counter = Counter()
    variable_values: Dict[str, Counter] = defaultdict(Counter)
    gradient_hits = 0
    files_scanned = 0
    files_with_colors = 0
    variable_defs_total = 0

    for path in iter_source_files(root):
        files_scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        relative_path = str(path.relative_to(root))
        file_color_tokens = collect_color_tokens(text)
        if file_color_tokens:
            files_with_colors += 1
            for token in file_color_tokens:
                color_counter[token] += 1
                if relative_path not in color_examples[token] and len(color_examples[token]) < 3:
                    color_examples[token].append(relative_path)

        for var_name, value in VAR_DEF_RE.findall(text):
            variable_counts[var_name] += 1
            variable_values[var_name][" ".join(value.split())] += 1
            variable_defs_total += 1

        gradient_hits += len(GRADIENT_RE.findall(text))

    top_color_tokens = []
    for token, count in color_counter.most_common(max(args.top, 1)):
        item: Dict[str, object] = {
            "token": token,
            "count": count,
            "example_files": color_examples[token],
        }
        rgb = hex_to_rgb(token)
        if rgb:
            item["luminance"] = round(relative_luminance(rgb), 3)
            item["saturation"] = round(saturation_score(rgb), 3)
        top_color_tokens.append(item)

    top_variables = []
    for name, count in variable_counts.most_common(20):
        common_values = [value for value, _ in variable_values[name].most_common(3)]
        top_variables.append(
            {
                "name": name,
                "count": count,
                "values": common_values,
            }
        )

    total_color_tokens = sum(color_counter.values())
    report = {
        "root": str(root),
        "files_scanned": files_scanned,
        "files_with_colors": files_with_colors,
        "total_color_tokens": total_color_tokens,
        "unique_color_tokens": len(color_counter),
        "gradient_hits": gradient_hits,
        "top_color_tokens": top_color_tokens,
        "top_variables": top_variables,
        "recommendations": build_recommendations(
            total_tokens=total_color_tokens,
            unique_tokens=len(color_counter),
            variable_defs_total=variable_defs_total,
            gradient_count=gradient_hits,
            color_counter=color_counter,
        ),
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = report_to_markdown(report)

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.write_text(output + ("\n" if not output.endswith("\n") else ""), encoding="utf-8")
        print(f"[OK] Wrote audit report: {output_path}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
