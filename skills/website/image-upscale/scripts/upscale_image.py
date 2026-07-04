#!/usr/bin/env python3
"""Upscale local images with Pillow or ffmpeg backends."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upscale image files or directories using Pillow or ffmpeg."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Image files and/or directories to process.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        help="Scale factor (for example 2 or 4). Mutually exclusive with --width/--height.",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Target width in pixels. If --height is omitted, preserve aspect ratio.",
    )
    parser.add_argument(
        "--height",
        type=int,
        help="Target height in pixels. If --width is omitted, preserve aspect ratio.",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "pillow-lanczos", "pillow-bicubic", "ffmpeg-lanczos"),
        default="auto",
        help="Upscaling backend. Default: auto (pillow-lanczos).",
    )
    parser.add_argument(
        "--output",
        help="Explicit output file path (single input file only).",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for batch processing. Keeps relative filenames for directory inputs.",
    )
    parser.add_argument(
        "--suffix",
        default="_upscaled",
        help="Filename suffix for generated files when --output is not provided.",
    )
    parser.add_argument(
        "--format",
        help="Override output format (jpg, jpeg, png, webp, tiff, bmp).",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=95,
        help="JPEG quality (1-100). Default: 95.",
    )
    parser.add_argument(
        "--png-compress-level",
        type=int,
        default=6,
        help="PNG compression level (0-9). Default: 6.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into directories.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned operations without writing files.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.scale is None and args.width is None and args.height is None:
        raise SystemExit("Provide --scale or at least one of --width/--height.")
    if args.scale is not None:
        if args.scale <= 0:
            raise SystemExit("--scale must be > 0.")
        if args.width is not None or args.height is not None:
            raise SystemExit("Use --scale or --width/--height, not both.")
    if args.width is not None and args.width <= 0:
        raise SystemExit("--width must be > 0.")
    if args.height is not None and args.height <= 0:
        raise SystemExit("--height must be > 0.")
    if not (1 <= args.jpeg_quality <= 100):
        raise SystemExit("--jpeg-quality must be in the range 1-100.")
    if not (0 <= args.png_compress_level <= 9):
        raise SystemExit("--png-compress-level must be in the range 0-9.")
    if args.output and len(args.inputs) != 1:
        raise SystemExit("--output is only supported with a single input path.")
    if args.output and Path(args.inputs[0]).is_dir():
        raise SystemExit("--output cannot be used when the single input path is a directory.")


def normalize_format(raw: str | None) -> str | None:
    if raw is None:
        return None
    normalized = raw.strip().lower()
    aliases = {"jpg": "jpeg", "tif": "tiff"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"jpeg", "png", "webp", "tiff", "bmp"}:
        raise SystemExit(
            f"Unsupported --format '{raw}'. Use jpg/jpeg, png, webp, tiff, or bmp."
        )
    return normalized


def iter_input_files(input_paths: list[str], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for raw in input_paths:
        path = Path(raw).expanduser()
        if not path.exists():
            raise SystemExit(f"Input path not found: {path}")
        if path.is_file():
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)
            else:
                raise SystemExit(f"Unsupported image extension: {path}")
            continue

        if recursive:
            candidates: Iterable[Path] = path.rglob("*")
        else:
            candidates = path.iterdir()
        for candidate in sorted(candidates):
            if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(candidate)
    if not files:
        raise SystemExit("No supported image files found in the provided input paths.")
    return files


def compute_target_size(
    original_width: int,
    original_height: int,
    scale: float | None,
    target_width: int | None,
    target_height: int | None,
) -> tuple[int, int]:
    if scale is not None:
        width = max(1, int(round(original_width * scale)))
        height = max(1, int(round(original_height * scale)))
        return width, height

    if target_width is None and target_height is None:
        raise ValueError("One sizing strategy must be provided.")
    if target_width is None:
        ratio = target_height / original_height
        target_width = max(1, int(round(original_width * ratio)))
    elif target_height is None:
        ratio = target_width / original_width
        target_height = max(1, int(round(original_height * ratio)))
    return target_width, target_height


def default_output_path(
    source: Path,
    output_dir: Path | None,
    output_format: str | None,
    suffix: str,
    anchor_root: Path | None,
) -> Path:
    if output_dir is None:
        base_dir = source.parent
        stem = source.stem + suffix
        suffix_ext = extension_for_format(output_format) if output_format else source.suffix
        return base_dir / f"{stem}{suffix_ext}"

    if anchor_root is not None:
        relative_parent = source.parent.relative_to(anchor_root)
        target_parent = output_dir / relative_parent
    else:
        target_parent = output_dir
    stem = source.stem + suffix
    suffix_ext = extension_for_format(output_format) if output_format else source.suffix
    return target_parent / f"{stem}{suffix_ext}"


def extension_for_format(output_format: str) -> str:
    return {
        "jpeg": ".jpg",
        "png": ".png",
        "webp": ".webp",
        "tiff": ".tiff",
        "bmp": ".bmp",
    }[output_format]


def choose_backend(requested: str) -> str:
    if requested != "auto":
        return requested
    return "pillow-lanczos"


def upscale_with_pillow(
    source: Path,
    dest: Path,
    target_size: tuple[int, int],
    backend: str,
    output_format: str | None,
    jpeg_quality: int,
    png_compress_level: int,
) -> None:
    resample = Image.Resampling.LANCZOS
    if backend == "pillow-bicubic":
        resample = Image.Resampling.BICUBIC

    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as im:
        transposed = ImageOps.exif_transpose(im)
        exif_bytes = im.info.get("exif")
        resized = transposed.resize(target_size, resample=resample)

        fmt = output_format or (im.format.lower() if im.format else None) or "png"
        if fmt == "jpeg" and resized.mode in {"RGBA", "LA"}:
            resized = resized.convert("RGB")
        if fmt == "jpeg" and resized.mode == "P":
            resized = resized.convert("RGB")

        save_kwargs: dict[str, object] = {}
        if fmt == "jpeg":
            save_kwargs["quality"] = jpeg_quality
            save_kwargs["optimize"] = True
        elif fmt == "png":
            save_kwargs["compress_level"] = png_compress_level
        if exif_bytes and fmt in {"jpeg", "tiff", "webp"}:
            save_kwargs["exif"] = exif_bytes

        resized.save(dest, format=fmt.upper(), **save_kwargs)


def upscale_with_ffmpeg(
    source: Path,
    dest: Path,
    target_size: tuple[int, int],
) -> None:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg not found in PATH.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    width, height = target_size
    cmd = [
        ffmpeg_path,
        "-v",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        f"scale={width}:{height}:flags=lanczos",
        str(dest),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "ffmpeg failed"
        raise RuntimeError(message)


def process_files(args: argparse.Namespace) -> int:
    output_format = normalize_format(args.format)
    files = iter_input_files(args.inputs, recursive=args.recursive)
    backend = choose_backend(args.backend)

    if backend == "ffmpeg-lanczos" and not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg-lanczos backend requested but ffmpeg is not installed.")

    if args.output and len(files) != 1:
        raise SystemExit("--output resolved to multiple files after directory expansion.")

    explicit_output = Path(args.output).expanduser() if args.output else None
    explicit_output_dir = Path(args.output_dir).expanduser() if args.output_dir else None

    # Preserve subdirectory layout only when a single directory input is provided.
    anchor_root: Path | None = None
    if len(args.inputs) == 1:
        candidate = Path(args.inputs[0]).expanduser()
        if candidate.is_dir():
            anchor_root = candidate

    wrote_count = 0
    for source in files:
        with Image.open(source) as probe:
            current_width, current_height = ImageOps.exif_transpose(probe).size

        target_size = compute_target_size(
            current_width,
            current_height,
            args.scale,
            args.width,
            args.height,
        )

        if explicit_output is not None:
            dest = explicit_output
        else:
            dest = default_output_path(
                source=source,
                output_dir=explicit_output_dir,
                output_format=output_format,
                suffix=args.suffix,
                anchor_root=anchor_root,
            )

        if not args.overwrite and dest.exists():
            raise SystemExit(f"Output exists (use --overwrite): {dest}")

        print(
            f"[PLAN] {source} ({current_width}x{current_height}) -> "
            f"{dest} ({target_size[0]}x{target_size[1]}) via {backend}"
        )

        if args.dry_run:
            continue

        if backend.startswith("pillow-"):
            upscale_with_pillow(
                source=source,
                dest=dest,
                target_size=target_size,
                backend=backend,
                output_format=output_format,
                jpeg_quality=args.jpeg_quality,
                png_compress_level=args.png_compress_level,
            )
        elif backend == "ffmpeg-lanczos":
            upscale_with_ffmpeg(
                source=source,
                dest=dest,
                target_size=target_size,
            )
        else:
            raise RuntimeError(f"Unsupported backend: {backend}")

        wrote_count += 1
        print(f"[OK] Wrote {dest}")

    print(
        f"[DONE] {'Planned' if args.dry_run else 'Processed'} "
        f"{len(files)} file(s)."
    )
    return wrote_count


def main() -> int:
    args = parse_args()
    validate_args(args)
    try:
        process_files(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001 - CLI should surface failures directly
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
