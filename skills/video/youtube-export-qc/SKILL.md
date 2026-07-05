---
name: youtube-export-qc
description: Run pre-upload video quality-control checks for YouTube exports using ffprobe and ffmpeg. Use when verifying resolution, frame rate, codec/profile, pixel format, bitrate, duration, audio-track presence/absence, and detecting black segments or long silence before upload.
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

# YouTube Export QC

## Overview
Use this skill as a release gate before upload. It validates export specs and flags common delivery issues that cause rejected or low-quality uploads.

## Quick Start
Run generic QC:
`./scripts/qc_video_ffmpeg.sh /path/video.mov`

Run 4K silent preset:
`./scripts/qc_youtube_4k_silent.sh /path/video.mov`

Run 4K with-audio preset:
`./scripts/qc_youtube_4k_with_audio.sh /path/video.mov`

## Main Checks
- Metadata via ffprobe:
  - `width`, `height`, `avg_frame_rate`
  - `codec_name`, `profile`, `pix_fmt`
  - `duration`, `bit_rate`, `format_name`
  - audio stream count
- Timeline analysis via ffmpeg:
  - `blackdetect` for black segments
  - `silencedetect` for silence spans (when audio exists)

## Commands

### Validate explicit target spec
`./scripts/qc_video_ffmpeg.sh --expect-width 3840 --expect-height 2160 --expect-fps 24 --expect-video-codec hevc --expect-pix-fmt yuv420p --expect-audio absent /path/output.mov`

### Fail when long black/silent sections are present
`./scripts/qc_video_ffmpeg.sh --max-black-duration 1.5 --max-silence-duration 4.0 /path/output.mov`

### Print detailed detector lines
`./scripts/qc_video_ffmpeg.sh --details /path/output.mov`

## Interpreting Results
- `RESULT: PASS`: No failures or warnings for that file.
- `RESULT: WARN`: No hard failure, but suspicious black/silence segments were detected.
- `RESULT: FAIL`: One or more spec checks failed.
- `SUMMARY: FAIL`: Script exits with status `1`.

## Operating Rules
- Treat mismatch on required export specs as failure.
- Use `WARN` to review suspicious but potentially intentional content.
- For silent ambience loops, set `--expect-audio absent`.
- For music uploads, set `--expect-audio present` and `--max-silence-duration`.
- Keep checks deterministic and local; do not use network services.

## Resources
- Threshold guidance: `references/youtube_qc_thresholds.md`
