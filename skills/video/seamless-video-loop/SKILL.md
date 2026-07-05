---
name: seamless-video-loop
description: Create seamless loopable videos from local clips with ffmpeg-full by crossfading clip boundaries and blending the final clip back into the first. Use when requests mention seamless loops, end-to-start blending, ambience loop videos, or loop-ready exports.
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

# Seamless Video Loop

## Overview
Use this skill when the final output must loop cleanly from end to beginning. It is focused on loopable joins rather than upscaling.

## Quick Checks
- Confirm ffmpeg-full is installed: `brew list --versions ffmpeg-full`
- Binaries (if needed):
  - `export FFMPEG_BIN=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`
  - `export FFPROBE_BIN=/opt/homebrew/opt/ffmpeg-full/bin/ffprobe`

## Core Command
`./scripts/loopable_join_ffmpeg.sh --xfade-duration 0.8 --output "/path/loopable.mov" clip1.mov clip2.mov clip3.mov clip4.mov`

What it does:
- Computes per-clip durations.
- Crossfades each clip into the next.
- Crossfades last clip into first clip.
- Trims to loop-safe duration and resets timestamps.
- Exports silent HEVC (`hvc1`) output.

Useful variants:
- Built-in transition: `./scripts/loopable_join_ffmpeg.sh --transition dissolve --xfade-duration 0.6 --output "/path/loopable.mov" clip1.mov clip2.mov`
- Custom transition expression: `./scripts/loopable_join_ffmpeg.sh --expr 'if(lte(X,W*P),B,A)' --xfade-duration 0.6 --output "/path/loopable.mov" clip1.mov clip2.mov`

## Verification
`./scripts/verify_video_output.sh "/path/loopable.mov"`

Reports:
- Width x height
- Duration
- File size
- Audio track count

## Tuning
- `--xfade-duration` controls smoothness and overlap.
- `--transition` selects an FFmpeg `xfade` transition such as `fade`, `dissolve`, `smoothleft`, `circleopen`, `zoomin`, `revealdown`, etc.
- `--expr` enables FFmpeg `xfade=transition=custom` expressions. If `--expr` is provided, the script treats the transition as `custom` unless `--transition custom` is already set.
- Use shorter fades for faster motion; longer fades for ambient/static scenes.
- Keep inputs with matching fps/resolution for the cleanest transitions.

## Custom Transition Notes
- Quote the expression in the shell, for example: `--expr 'if(lte(X,W*P),B,A)'`
- `P` is transition progress from `0` to `1`.
- `A` is the first input pixel value and `B` is the second input pixel value.
- Common expression variables include `X`, `Y`, `W`, `H`, `P`, `PLANE`, `A`, and `B`.
- Example left-to-right reveal: `if(lte(X,W*P),B,A)`
- Example top-to-bottom reveal: `if(lte(Y,H*P),B,A)`
- Example diagonal reveal: `if(lte(X+Y,(W+H)*P),B,A)`

## Operating Rules
- Keep source clips unchanged and write to new output paths.
- Use `--dry-run` for long jobs.
- Use this skill for loopability; use `ffmpeg-video-upscale` for upscale/export tasks.

## Resources
- Loop tuning notes: `references/loop_tuning.md`
