---
name: ffmpeg-video-upscale
description: Upscale and process local video files with ffmpeg-full. Use when requests involve resizing videos (for example 1080p to 3840x2160 or 7680x4320), removing audio, or creating non-loop seamless joins between clips.
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

# FFmpeg Video Upscale

## Overview
Use bundled ffmpeg-full scripts to run deterministic local video processing without API calls. Produce macOS-compatible HEVC outputs tagged as `hvc1`.

## Quick Checks
- Confirm ffmpeg-full is installed: `brew list --versions ffmpeg-full`
- Set binaries if needed:
  - `export FFMPEG_BIN=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`
  - `export FFPROBE_BIN=/opt/homebrew/opt/ffmpeg-full/bin/ffprobe`

## Tasks

### Upscale to 3840x2160 and remove audio
Run:
`./scripts/upscale_videos_ffmpeg.sh "/path/a.mp4" "/path/b.mp4"`

Defaults:
- 3840x2160
- Silent output (`-an`)
- `libx265 -preset slow -crf 18`
- Suffix `_3840x2160_silent_ffmpeg.mov`

Useful options:
- `--width --height`
- `--crf --preset`
- `--suffix`
- `--dry-run`

### Seamless linear join (non-looping)
Use when the last clip does not need to blend into the first clip.

Run:
`./scripts/upscale_videos_ffmpeg.sh --join-seamless --xfade-duration 0.8 --transition fade --join-output "/path/joined.mov" clip1.mov clip2.mov clip3.mov`

## Verification
Run:
`./scripts/verify_video_output.sh "/path/output.mov"`

Report:
- Width x height
- Duration
- File size
- Audio track count

## Operating Rules
- Keep source files unchanged and write new outputs.
- Use `--dry-run` before long renders.
- Keep `-tag:v hvc1` for Apple playback compatibility.
- Ask for escalated permissions when input or output paths are outside writable sandbox roots.
- Lower CRF for higher quality; use a faster preset only when speed is the priority.
- For end-to-start loopable outputs, use `seamless-video-loop`.
