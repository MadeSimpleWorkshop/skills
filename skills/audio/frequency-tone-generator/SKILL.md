---
name: frequency-tone-generator
description: Generate exact-length layered frequency-tone audio (WAV) from a user-provided list of frequencies for meditation/frequency music, solfeggio-style tones, or YouTube audio beds. Use when a user wants to combine one or more frequencies (for example 396, 432, 528 Hz) into a single audio file for a specific duration such as 1 minute, 10 minutes, or 1 hour, with clipping-safe mixing and clean fades.
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

# Frequency Tone Generator

## Overview

Generate pure sine-tone audio by layering multiple frequencies into one exact-duration WAV file. Use the bundled script for deterministic output and clipping-safe gain scaling instead of rewriting tone-generation code each time.

## Quick Start

Run the bundled script:

```bash
python3 scripts/generate_frequency_audio.py "396,417,528" \
  --duration 1m \
  --output /tmp/frequency_mix_1m.wav
```

This produces a stereo 48 kHz, 16-bit PCM WAV file with exact frame-count timing (duration rounded to the nearest sample).

## Workflow

1. Gather the user's frequency list and target duration.
2. Generate the WAV with `scripts/generate_frequency_audio.py`.
3. Verify duration and format from the script output.
4. If the user wants a delivery format other than WAV, convert with `ffmpeg` after generation.
5. If the user wants a YouTube upload-ready video, pair the WAV with an image/video separately.

## Frequency Input Format

- Accept comma-separated or space-separated frequency values in Hz.
- Allow optional per-tone weights using `@` syntax (`frequency@weight`).
- Treat omitted weight as `1`.
- Examples:

```text
"528"
"396,417,528"
"40@0.2, 174@0.5, 432, 528@0.8"
```

## Duration Input Format

- Accept seconds as a number (`60`, `90.5`).
- Accept unit suffixes (`90s`, `1m`, `2h`, `500ms`).
- Accept time-style strings (`01:30`, `00:10:00`).

## Common Commands

Generate a 1-minute layered tone file:

```bash
python3 scripts/generate_frequency_audio.py "396,417,528" \
  --duration 1m \
  --output /tmp/solfeggio_1m.wav
```

Generate a longer mix with custom gains and slower fade-out:

```bash
python3 scripts/generate_frequency_audio.py "40@0.25,432,528@0.6" \
  --duration 10m \
  --fade-in-ms 50 \
  --fade-out-ms 1500 \
  --peak 0.85 \
  --output /tmp/frequency_mix_10m.wav
```

Generate mono output:

```bash
python3 scripts/generate_frequency_audio.py "528" \
  --duration 60 \
  --channels 1 \
  --output /tmp/528hz_60s_mono.wav
```

## Script Notes

- The script writes 16-bit PCM WAV (`.wav`) only.
- The mixer auto-scales tones by the sum of weights to avoid clipping.
- The `--peak` option controls the maximum combined peak target before int16 conversion.
- Default short fades remove clicks at the start/end of the file.
- Stereo output duplicates the same mixed signal to left and right channels.

## YouTube-Oriented Guidance

- Generate the exact target length needed for the video edit (for example `1m`, `10m`, `1h`).
- Keep exports as WAV during editing; convert later only if the user specifically needs MP3/AAC.
- If the user requests "music" with ambience, generate the tone bed first, then mix in ambience with a separate audio workflow.
- Avoid making medical or therapeutic claims unless the user provides approved wording.

## Resources

### `scripts/generate_frequency_audio.py`

Use this script for exact-length, layered sine-tone generation with clipping-safe weighting, fade-in/fade-out, and mono/stereo WAV export.
