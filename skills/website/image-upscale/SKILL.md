---
name: image-upscale
description: Upscale local images (photos, screenshots, artwork) to larger dimensions using deterministic local workflows and backend selection guidance. Use when a user asks to enlarge an image (for example 2x/4x), hit a target resolution, batch upscale a folder, preserve aspect ratio, compare resize methods, or evaluate AI super-resolution options versus standard interpolation tools.
license: PolyForm-Noncommercial-1.0.0 AND LicenseRef-No-AI-Training
license_url: https://github.com/MadeSimpleWorkshop/skills/blob/main/LICENSE.md
copyright: © 2026 MadeSimple Workshop
---
<!--
  Copyright © 2026 MadeSimple Workshop. All rights reserved.
  Licensed under PolyForm Noncommercial License 1.0.0 + AI/ML Addendum.
  Noncommercial use only. NOT for training/fine-tuning AI/ML models.
  Full terms: https://github.com/MadeSimpleWorkshop/skills/blob/main/LICENSE.md
  Commercial license: https://github.com/MadeSimpleWorkshop
-->

# Image Upscale

## Overview

Upscale existing image files with a bundled local script first, then escalate to specialized AI tools only when the user explicitly needs super-resolution detail recovery. This skill also includes a short research note comparing practical upscalers with DyPE so Codex can choose the right tool for the request.

## Quick Start

Upscale a single image by 2x using Pillow Lanczos (default):

```bash
python3 scripts/upscale_image.py input.jpg --scale 2
```

Upscale to a target width while preserving aspect ratio:

```bash
python3 scripts/upscale_image.py input.png --width 3840
```

Batch upscale all images in a folder:

```bash
python3 scripts/upscale_image.py ./images --scale 2 --output-dir ./upscaled --recursive
```

## Workflow

1. Confirm the request is for upscaling an existing image (not prompt-based image generation).
2. Choose a target: `--scale` (for example `2`, `4`) or `--width` / `--height`.
3. Run `scripts/upscale_image.py` with the default Pillow backend.
4. If the user needs better detail recovery or deartifacting than interpolation can provide, switch to an AI super-resolution workflow (for example Real-ESRGAN) and document any install/setup requirements.
5. If the request is actually "generate a very high-resolution image from a prompt" (or a diffusion re-render workflow), review `references/upscaling-options.md` and treat DyPE as a separate generative path, not a direct replacement for classic upscaling.

## Backend Selection

- `pillow-lanczos` (default): Best first choice for deterministic local resizing with no extra installs. Good for screenshots/UI assets and simple enlargements.
- `pillow-bicubic`: Softer fallback when Lanczos introduces ringing on some edges.
- `ffmpeg-lanczos`: Useful when the user already has an ffmpeg-based media pipeline or wants consistent scaling behavior across images/video workflows.
- AI super-resolution (not bundled): Use when the user asks for detail recovery, denoising, deartifacting, or "make this blurry image sharp." Real-ESRGAN is the practical default to evaluate before heavier research code.
- DyPE (research option): Use for diffusion-based ultra-high-resolution image generation or iterative high-res synthesis workflows, not routine enlargement of an existing photo.

## Common Commands

Upscale a single file to 4K width:

```bash
python3 scripts/upscale_image.py input.jpg --width 3840
```

Upscale to an exact height (aspect ratio preserved):

```bash
python3 scripts/upscale_image.py input.png --height 2160
```

Use ffmpeg Lanczos backend:

```bash
python3 scripts/upscale_image.py input.webp --scale 2 --backend ffmpeg-lanczos
```

Preview batch output paths without writing files:

```bash
python3 scripts/upscale_image.py ./input-folder --scale 2 --output-dir ./out --recursive --dry-run
```

Overwrite an existing destination file explicitly:

```bash
python3 scripts/upscale_image.py input.jpg --scale 2 --output /tmp/input_2x.jpg --overwrite
```

## Script Behavior Notes

- The script accepts image files and directories; directories can be scanned recursively with `--recursive`.
- Provide one sizing strategy: `--scale` or `--width` / `--height`.
- If only one of `--width` or `--height` is provided, aspect ratio is preserved automatically.
- Default output is written next to the source with an `_upscaled` suffix.
- JPEG output drops alpha (converts to RGB) when needed.
- Pillow path preserves EXIF bytes when available.

## Research Note (DyPE vs Practical Upscaling)

The user-supplied DyPE references are useful, but DyPE is primarily a diffusion-based high-resolution generation method (dynamic patching for efficient large-image synthesis). For a request like "upscale this local image," start with interpolation or a dedicated super-resolution model first. See `references/upscaling-options.md` for concise guidance and source links to revisit.

## Resources

### `scripts/upscale_image.py`

Use this for deterministic local upscaling with Pillow or ffmpeg backends.

### `references/upscaling-options.md`

Use this reference when choosing between interpolation, AI super-resolution, and DyPE-style generative high-resolution workflows.
