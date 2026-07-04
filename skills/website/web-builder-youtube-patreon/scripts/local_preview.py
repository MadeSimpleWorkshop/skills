#!/usr/bin/env python3
"""Serve a local website directory for quick manual review."""

from __future__ import annotations

import argparse
import functools
import http.server
import pathlib
import socketserver
import sys
import webbrowser


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve a local website folder for browser review."
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Website root directory to serve.",
    )
    parser.add_argument(
        "--entry",
        default="index.html",
        help="Entry file relative to --root (default: index.html).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4173,
        help="Port to bind (default: 4173).",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate paths and print URL without starting the server.",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the page in the default browser after starting.",
    )
    return parser.parse_args()


def validate_inputs(root: pathlib.Path, entry: str) -> pathlib.Path:
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Root directory not found: {root}")
    entry_path = root / entry
    if not entry_path.exists() or not entry_path.is_file():
        raise FileNotFoundError(f"Entry file not found: {entry_path}")
    return entry_path


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.root).expanduser().resolve()

    try:
        validate_inputs(root, args.entry)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    url = f"http://{args.host}:{args.port}/{args.entry}"
    print(f"[OK] Root: {root}")
    print(f"[OK] URL:  {url}")

    if args.check_only:
        return 0

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    try:
        with ReusableTCPServer((args.host, args.port), handler) as server:
            if args.open_browser:
                webbrowser.open(url)
            print("[INFO] Press Ctrl+C to stop.")
            server.serve_forever()
    except OSError as exc:
        print(f"[ERROR] Failed to start server on {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
