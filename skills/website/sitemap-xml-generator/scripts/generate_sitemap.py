#!/usr/bin/env python3

import argparse
import datetime as dt
import fnmatch
import os
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", SITEMAP_NS)


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    "node_modules",
    "vendor",
}


def _iso_date_from_mtime(mtime: float) -> str:
    # Sitemaps accept full timestamps, but date-only is widely used and stable.
    return dt.datetime.fromtimestamp(mtime, tz=dt.timezone.utc).date().isoformat()


def _validate_base_url(base_url: str) -> str:
    base_url = base_url.strip()
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit(f"Invalid --base-url: {base_url!r} (expected https://example.com)")
    return base_url.rstrip("/")


def _should_exclude_path(rel_posix: str, exclude_globs: list[str]) -> bool:
    for g in exclude_globs:
        if fnmatch.fnmatch(rel_posix, g):
            return True
    return False


def _iter_files(root: Path, include_exts: set[str], exclude_dirs: set[str]) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune unwanted directories in-place.
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith(".")]
        for name in filenames:
            # Ignore hidden/metadata files (e.g. .DS_Store, AppleDouble "._*" files).
            if name.startswith("."):
                continue
            p = Path(dirpath) / name
            if not p.is_file():
                continue
            if p.suffix.lower() not in include_exts:
                continue
            out.append(p)
    return out


def _path_to_url_path(rel_posix: str, strip_html_ext: bool, trailing_slash: bool) -> str:
    # Always treat index.html as the directory URL.
    lower = rel_posix.lower()
    if lower.endswith("/index.html") or lower == "index.html" or lower.endswith("/index.htm") or lower == "index.htm":
        rel_dir = rel_posix.rsplit("/", 1)[0] if "/" in rel_posix else ""
        if rel_dir == "":
            return "/"
        return f"/{rel_dir.strip('/')}/"

    if strip_html_ext and (lower.endswith(".html") or lower.endswith(".htm")):
        rel_posix = rel_posix.rsplit(".", 1)[0]

    url_path = "/" + rel_posix.lstrip("/")
    if trailing_slash and not url_path.endswith("/"):
        # Only add slash for "extensionless" paths.
        last_seg = url_path.rsplit("/", 1)[-1]
        if "." not in last_seg:
            url_path += "/"
    return url_path


def _write_robots_sitemap_line(robots_path: Path, sitemap_url: str) -> None:
    robots_path.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if robots_path.exists():
        existing = robots_path.read_text(encoding="utf-8", errors="replace")

    if existing.strip() == "":
        # Initialize a minimal, standards-friendly robots.txt and include the sitemap.
        robots_path.write_text(
            "\n".join(
                [
                    "User-agent: *",
                    "Allow: /",
                    "",
                    f"Sitemap: {sitemap_url}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return

    lines = existing.splitlines()
    new_lines: list[str] = []
    saw_sitemap = False
    for line in lines:
        if line.strip().lower().startswith("sitemap:"):
            if not saw_sitemap:
                new_lines.append(f"Sitemap: {sitemap_url}")
                saw_sitemap = True
            # Drop any additional sitemap lines (avoid duplicates).
            continue
        new_lines.append(line)

    if not saw_sitemap:
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(f"Sitemap: {sitemap_url}")

    robots_path.write_text("\n".join(new_lines).rstrip("\n") + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate sitemap.xml by scanning a local site folder.")
    ap.add_argument("--root", required=True, help="Local site root directory to scan (should contain index.html).")
    ap.add_argument("--base-url", required=True, help="Base URL, e.g. https://example.com")
    ap.add_argument("--out", required=True, help="Output sitemap.xml path.")
    ap.add_argument(
        "--include-ext",
        action="append",
        default=[".html", ".htm"],
        help="File extension to include (repeatable). Default: .html, .htm",
    )
    ap.add_argument(
        "--ignore-ext",
        action="append",
        default=[".php"],
        help="File extension to ignore (repeatable). Default: .php",
    )
    ap.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude while walking (repeatable).",
    )
    ap.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="Glob (posix-style, relative to --root) to exclude (repeatable), e.g. 'admin/*' or '**/drafts/*'.",
    )
    ap.add_argument("--no-lastmod", action="store_true", help="Omit <lastmod> tags.")
    ap.add_argument("--strip-html-ext", action="store_true", help="Convert /page.html -> /page (no extension).")
    ap.add_argument("--trailing-slash", action="store_true", help="Append / to extensionless URLs (e.g. /about/).")
    ap.add_argument(
        "--robots",
        default="",
        help="Optional robots.txt path to update (adds/updates a single Sitemap: line).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Do not write files; print summary only.")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"--root does not exist or is not a directory: {str(root)!r}")

    base_url = _validate_base_url(args.base_url)
    out_path = Path(args.out).expanduser().resolve()

    include_exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.include_ext}
    ignore_exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.ignore_ext}
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS) | set(args.exclude_dir)
    exclude_globs = list(args.exclude_glob)

    files = _iter_files(root, include_exts=include_exts, exclude_dirs=exclude_dirs)

    # Map loc -> lastmod (max), to avoid duplicates if different files map to same URL.
    entries: dict[str, str | None] = {}
    excluded = 0

    for p in files:
        if p.suffix.lower() in ignore_exts:
            excluded += 1
            continue
        rel = p.relative_to(root).as_posix()
        if _should_exclude_path(rel, exclude_globs):
            excluded += 1
            continue
        url_path = _path_to_url_path(rel, strip_html_ext=args.strip_html_ext, trailing_slash=args.trailing_slash)
        loc = f"{base_url}{url_path}"
        lastmod = None if args.no_lastmod else _iso_date_from_mtime(p.stat().st_mtime)
        if loc in entries:
            if lastmod is not None and entries[loc] is not None:
                entries[loc] = max(entries[loc], lastmod)  # type: ignore[arg-type]
            elif lastmod is not None:
                entries[loc] = lastmod
            continue
        entries[loc] = lastmod

    urlset = ET.Element(ET.QName(SITEMAP_NS, "urlset"))
    for loc in sorted(entries.keys()):
        url_el = ET.SubElement(urlset, ET.QName(SITEMAP_NS, "url"))
        ET.SubElement(url_el, ET.QName(SITEMAP_NS, "loc")).text = loc
        lastmod = entries[loc]
        if lastmod:
            ET.SubElement(url_el, ET.QName(SITEMAP_NS, "lastmod")).text = lastmod

    tree = ET.ElementTree(urlset)
    xml_bytes = ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)

    print(f"Scanned:   {str(root)}")
    print(f"Included:  {len(entries)} urls (from {len(files)} candidate files; excluded={excluded})")
    print(f"Base URL:  {base_url}")
    print(f"Output:    {str(out_path)}")

    if args.dry_run:
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(xml_bytes + b"\n")

    if args.robots:
        robots_path = Path(args.robots).expanduser().resolve()
        sitemap_url = f"{base_url}/sitemap.xml"
        _write_robots_sitemap_line(robots_path, sitemap_url=sitemap_url)
        print(f"Updated:   {str(robots_path)} (Sitemap: {sitemap_url})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
