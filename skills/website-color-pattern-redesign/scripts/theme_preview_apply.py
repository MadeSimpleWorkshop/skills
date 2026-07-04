#!/usr/bin/env python3
"""Generate website color redesign previews and apply approved palette updates."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


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

STYLE_SUFFIXES = {".css", ".scss", ".sass", ".less"}
TEXT_SUFFIXES = {
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

INJECT_START = "<!-- codex-theme:start -->"
INJECT_END = "<!-- codex-theme:end -->"
INJECT_PATTERN = re.compile(
    r"<!--\s*codex-theme:start\s*-->.*?<!--\s*codex-theme:end\s*-->\s*",
    flags=re.DOTALL | re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or apply website palette updates using a JSON palette contract.",
    )
    parser.add_argument(
        "--mode",
        choices=("preview", "apply"),
        default="preview",
        help="Run in preview mode (default) or apply mode.",
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Website root directory.",
    )
    parser.add_argument(
        "--entry",
        default="index.html",
        help="Entry HTML file relative to --root (default: index.html).",
    )
    parser.add_argument(
        "--palette",
        required=True,
        help="Palette JSON path. Must include a 'variables' object.",
    )
    parser.add_argument(
        "--out",
        help="Preview output directory (preview mode only). Default: <root>-theme-preview",
    )
    parser.add_argument(
        "--replace-literals",
        action="store_true",
        help="Apply literal_replacements across text files in apply mode.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Command output format (default: text).",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write command output.",
    )
    return parser.parse_args()


def load_palette(path: Path) -> Dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Palette file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in palette file: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Palette JSON must be an object")

    variables = data.get("variables")
    if not isinstance(variables, dict) or not variables:
        raise ValueError("Palette JSON must include a non-empty 'variables' object")

    normalized_variables: Dict[str, str] = {}
    for key, value in variables.items():
        if not isinstance(key, str) or not key.startswith("--"):
            raise ValueError(f"Invalid variable name '{key}'. Use CSS custom property names.")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Variable '{key}' must have a non-empty string value.")
        normalized_variables[key.strip()] = value.strip()

    pattern_css = data.get("pattern_css", "")
    if pattern_css is None:
        pattern_css = ""
    if not isinstance(pattern_css, str):
        raise ValueError("'pattern_css' must be a string when provided.")

    literal_replacements = data.get("literal_replacements", {})
    if literal_replacements is None:
        literal_replacements = {}
    if not isinstance(literal_replacements, dict):
        raise ValueError("'literal_replacements' must be an object when provided.")

    normalized_literal_replacements: Dict[str, str] = {}
    for old, new in literal_replacements.items():
        if not isinstance(old, str) or not isinstance(new, str):
            raise ValueError("literal_replacements keys and values must be strings.")
        if not old.strip():
            raise ValueError("literal_replacements cannot include empty keys.")
        normalized_literal_replacements[old] = new

    name = data.get("name") if isinstance(data.get("name"), str) else ""
    return {
        "name": name,
        "variables": normalized_variables,
        "pattern_css": pattern_css.strip(),
        "literal_replacements": normalized_literal_replacements,
    }


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def iter_files(root: Path, suffixes: Iterable[str]) -> Iterable[Path]:
    suffix_set = {suffix.lower() for suffix in suffixes}
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        current = Path(current_root)
        for filename in files:
            path = current / filename
            if path.suffix.lower() in suffix_set:
                yield path


def render_override_css(variables: Dict[str, str], pattern_css: str, palette_name: str) -> str:
    lines: List[str] = []
    label = palette_name if palette_name else "unnamed-palette"
    lines.append("/* Generated by theme_preview_apply.py */")
    lines.append(f"/* Palette: {label} */")
    lines.append(":root {")
    for key, value in sorted(variables.items()):
        lines.append(f"  {key}: {value};")
    lines.append("}")
    if pattern_css:
        lines.append("")
        lines.append("/* Pattern layer overrides */")
        lines.append(pattern_css)
    lines.append("")
    return "\n".join(lines)


def inject_stylesheet(entry_path: Path, stylesheet_href: str) -> bool:
    html = entry_path.read_text(encoding="utf-8", errors="ignore")
    block = (
        f"{INJECT_START}\n"
        f"<link rel=\"stylesheet\" href=\"{stylesheet_href}\" />\n"
        f"{INJECT_END}\n"
    )
    cleaned = INJECT_PATTERN.sub("", html)
    lower = cleaned.lower()
    head_index = lower.find("</head>")
    if head_index >= 0:
        updated = cleaned[:head_index] + block + cleaned[head_index:]
    else:
        updated = block + cleaned

    if updated != html:
        entry_path.write_text(updated, encoding="utf-8")
        return True
    return False


def copy_site(root: Path, destination: Path) -> None:
    if root == destination or is_relative_to(destination, root):
        raise ValueError("Preview output directory must be outside the source root.")

    def ignore_filter(directory: str, names: List[str]) -> List[str]:
        ignored = []
        for name in names:
            if name in IGNORE_DIRS or name.startswith("."):
                ignored.append(name)
        return ignored

    shutil.copytree(root, destination, dirs_exist_ok=True, ignore=ignore_filter)


def apply_variable_definitions(
    root: Path,
    variables: Dict[str, str],
) -> Tuple[int, List[str], List[str]]:
    updated_files: List[str] = []
    matched_variables = set()
    total_replacements = 0

    for path in iter_files(root, STYLE_SUFFIXES):
        original = path.read_text(encoding="utf-8", errors="ignore")
        updated = original
        file_replacements = 0

        for variable, value in variables.items():
            pattern = re.compile(rf"({re.escape(variable)}\s*:\s*)([^;{{}}]+)(;)")
            updated, count = pattern.subn(rf"\1{value}\3", updated)
            if count > 0:
                matched_variables.add(variable)
                file_replacements += count

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            updated_files.append(str(path))
            total_replacements += file_replacements

    missing_variables = [name for name in variables if name not in matched_variables]
    return total_replacements, sorted(updated_files), missing_variables


def apply_literal_replacements(root: Path, replacements: Dict[str, str]) -> Tuple[int, List[str]]:
    if not replacements:
        return 0, []

    updated_files: List[str] = []
    replacement_count = 0

    for path in iter_files(root, TEXT_SUFFIXES):
        original = path.read_text(encoding="utf-8", errors="ignore")
        updated = original
        file_count = 0

        for old, new in replacements.items():
            pattern = re.compile(re.escape(old), flags=re.IGNORECASE)
            updated, count = pattern.subn(new, updated)
            file_count += count

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            updated_files.append(str(path))
            replacement_count += file_count

    return replacement_count, sorted(updated_files)


def resolve_entry(root: Path, entry: str) -> Path:
    entry_path = (root / entry).resolve()
    if not entry_path.exists() or not entry_path.is_file():
        raise ValueError(f"Entry file not found: {entry_path}")
    if not is_relative_to(entry_path, root):
        raise ValueError("Entry path must stay inside root.")
    return entry_path


def relative_href(from_file: Path, to_file: Path) -> str:
    relative = os.path.relpath(to_file, start=from_file.parent)
    return relative.replace(os.sep, "/")


def run_preview_mode(
    root: Path,
    entry: str,
    palette: Dict[str, object],
    out_dir: Path,
) -> Dict[str, object]:
    copy_site(root, out_dir)

    preview_entry = resolve_entry(out_dir, entry)
    preview_css = out_dir / "codex-theme-preview.css"
    preview_css.write_text(
        render_override_css(
            variables=palette["variables"],
            pattern_css=palette["pattern_css"],
            palette_name=palette["name"],
        ),
        encoding="utf-8",
    )

    href = relative_href(preview_entry, preview_css)
    injected = inject_stylesheet(preview_entry, href)

    return {
        "mode": "preview",
        "preview_root": str(out_dir),
        "entry_file": str(preview_entry),
        "override_file": str(preview_css),
        "variables_count": len(palette["variables"]),
        "injected_stylesheet": injected,
    }


def run_apply_mode(
    root: Path,
    entry: str,
    palette: Dict[str, object],
    replace_literals: bool,
) -> Dict[str, object]:
    entry_path = resolve_entry(root, entry)

    replacement_count, variable_updated_files, missing_variables = apply_variable_definitions(
        root=root,
        variables=palette["variables"],
    )

    override_file = None
    injected_stylesheet = False
    if missing_variables or palette["pattern_css"]:
        override_variables = {name: palette["variables"][name] for name in missing_variables}
        override_path = root / "codex-theme-overrides.css"
        override_path.write_text(
            render_override_css(
                variables=override_variables,
                pattern_css=palette["pattern_css"],
                palette_name=palette["name"],
            ),
            encoding="utf-8",
        )
        override_file = str(override_path)
        href = relative_href(entry_path, override_path)
        injected_stylesheet = inject_stylesheet(entry_path, href)

    literal_count = 0
    literal_updated_files: List[str] = []
    if replace_literals and palette["literal_replacements"]:
        literal_count, literal_updated_files = apply_literal_replacements(
            root=root,
            replacements=palette["literal_replacements"],
        )

    return {
        "mode": "apply",
        "entry_file": str(entry_path),
        "variable_replacements": replacement_count,
        "variable_updated_files": variable_updated_files,
        "missing_variables": missing_variables,
        "override_file": override_file,
        "injected_stylesheet": injected_stylesheet,
        "literal_replacements": literal_count,
        "literal_updated_files": literal_updated_files,
    }


def format_text_output(result: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append(f"Mode: {result['mode']}")

    if result["mode"] == "preview":
        lines.append(f"Preview root: {result['preview_root']}")
        lines.append(f"Entry file: {result['entry_file']}")
        lines.append(f"Override file: {result['override_file']}")
        lines.append(f"Variables: {result['variables_count']}")
        lines.append(f"Stylesheet injected: {result['injected_stylesheet']}")
    else:
        lines.append(f"Entry file: {result['entry_file']}")
        lines.append(f"Variable replacements: {result['variable_replacements']}")
        lines.append(f"Variable-updated files: {len(result['variable_updated_files'])}")
        lines.append(f"Missing variables: {len(result['missing_variables'])}")
        if result["override_file"]:
            lines.append(f"Override file: {result['override_file']}")
            lines.append(f"Stylesheet injected: {result['injected_stylesheet']}")
        lines.append(f"Literal replacements: {result['literal_replacements']}")
        if result["literal_updated_files"]:
            lines.append(f"Literal-updated files: {len(result['literal_updated_files'])}")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] Root directory not found: {root}", file=sys.stderr)
        return 1

    palette_path = Path(args.palette).expanduser().resolve()
    try:
        palette = load_palette(palette_path)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    try:
        if args.mode == "preview":
            default_out = root.parent / f"{root.name}-theme-preview"
            out_dir = Path(args.out).expanduser().resolve() if args.out else default_out.resolve()
            result = run_preview_mode(root=root, entry=args.entry, palette=palette, out_dir=out_dir)
        else:
            result = run_apply_mode(
                root=root,
                entry=args.entry,
                palette=palette,
                replace_literals=args.replace_literals,
            )
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"[ERROR] File operation failed: {exc}", file=sys.stderr)
        return 1

    output = json.dumps(result, indent=2) if args.format == "json" else format_text_output(result)
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.write_text(output + ("\n" if not output.endswith("\n") else ""), encoding="utf-8")
        print(f"[OK] Wrote result: {output_path}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
