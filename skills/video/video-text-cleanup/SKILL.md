---
name: video-text-cleanup
description: Remove burned-in text overlays from user-owned videos with ffmpeg using delogo or crop-and-rescale workflows. Use when requests involve removing subtitles, timestamps, or lower-thirds while preserving quality. Do not use this skill to remove watermarks, logos, copyright notices, or attribution marks.
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

# Video Text Cleanup

## Overview
Use the bundled script to remove burned-in text from local videos when the user owns the content or has clear permission to edit it.

## Hard Boundary
- Refuse requests to remove or hide watermarks, logos, copyright notices, or attribution text.
- Offer compliant alternatives when needed: crop, blur, replace source footage, or re-render from original project files.

## Quick Start
Probe input details:
`/opt/homebrew/opt/ffmpeg-full/bin/ffprobe -v error -show_entries stream=width,height,r_frame_rate -select_streams v:0 -show_entries format=duration -of default=nw=1:nk=0 "/path/input.mp4"`

Remove a fixed subtitle/lower-third with interpolation:
`./scripts/remove_video_text_ffmpeg.sh --mode delogo --x 1240 --y 980 --w 620 --h 86 --output "/path/output_clean.mp4" "/path/input.mp4"`

Remove bottom text strip by cropping and restoring frame size:
`./scripts/remove_video_text_ffmpeg.sh --mode crop-bottom --crop-px 88 --output "/path/output_clean.mp4" "/path/input.mp4"`

## Workflow
1. Confirm the request is compliant (not watermark/logo removal).
2. Probe the source with ffprobe and record width, height, fps, duration.
3. Choose method:
   - `delogo` for fixed text blocks in one area.
   - `crop-bottom` when text is in a thin strip at the bottom.
4. Run a short preview first with `--start` and `--duration`.
5. Run full export once settings are clean.
6. QC output with ffprobe and visual spot checks at start/middle/end.

## Tuning Rules
- Keep `--w` and `--h` only as large as needed.
- Use `--show-box` to tune coordinates before full render.
- For `crop-bottom`, keep crop height small to limit composition changes.
- Prefer `--audio copy` unless the container/codec combo requires re-encode.

## Commands
Preview 12 seconds around a known text area:
`./scripts/remove_video_text_ffmpeg.sh --mode delogo --x 1240 --y 980 --w 620 --h 86 --start 00:00:30 --duration 12 --output "/tmp/preview_clean.mp4" "/path/input.mp4"`

Full export with HEVC:
`./scripts/remove_video_text_ffmpeg.sh --mode delogo --x 1240 --y 980 --w 620 --h 86 --codec libx265 --crf 20 --preset slow --output "/path/output_clean_hevc.mp4" "/path/input.mp4"`

Dry-run command check:
`./scripts/remove_video_text_ffmpeg.sh --mode crop-bottom --crop-px 88 --dry-run "/path/input.mp4"`

## Resources
- Main script: `scripts/remove_video_text_ffmpeg.sh`
- Method guide: `references/text-cleanup-methods.md`
