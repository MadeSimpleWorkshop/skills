---
name: youtube-to-suno-prompts
description: Download YouTube audio you own/are permitted to use, extract basic metadata plus optional audio features (BPM/key/energy), and generate multiple Suno prompt variants that capture the reference track's genre/mood/instrumentation/production without copying lyrics or melodies. Use when a user provides a YouTube URL (or local audio path) and asks for Suno prompts, vibe profiles, or prompt variations inspired by the track.
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

# Youtube To Suno Prompts

## Purpose

Turn a reference track into:
- A compact vibe profile (what it sounds like)
- Multiple copy-paste Suno prompts (style prompts; optional lyric concepts)

## Workflow

### 1) Rights + scope check

- Only download content you own or have permission to download/use. Respect YouTube Terms of Service and copyright.
- Generate "inspired by" prompts. Do not include exact lyrics, melodies, or the original song title/artist.

### 2) Run the pipeline script

Generate a vibe profile + prompt variants from a YouTube URL:

```bash
python3 scripts/youtube_to_suno_prompts.py \
  'https://www.youtube.com/watch?v=TzEZNxk8W7c' \
  --outdir ./output
```

Generate prompts from a local audio file instead (skip downloading):

```bash
python3 scripts/youtube_to_suno_prompts.py \
  --audio /path/to/reference.mp3 \
  --title 'Reference track' \
  --outdir ./output
```

Default outputs (inside the created run folder):
- `vibe_profile.json`
- `suno_prompts.txt`
- `audio.wav` (when downloading or converting succeeds)
- `segments/segment_*.wav`

### 3) Tune prompt quality (when metadata is sparse)

Use one or more of:
- Add manual hints: `--hint 'dreamy, minor key, cinematic synths'`
- Increase prompt count: `--count 20`
- Extend keyword detection by editing `references/keyword_lexicon.json`

### 4) Deliver the result to the user

When answering, return:
1. A short vibe profile summary (genre/mood/instruments/tempo if known)
2. A numbered list of Suno prompts
3. Any uncertainty (e.g., "BPM estimate unavailable: `librosa` not installed")

## Notes

- Dependencies: `yt-dlp` (URL mode), `ffmpeg`, `ffprobe`. Optional: `librosa` for BPM/key estimates.
- This skill intentionally avoids "clone the song" instructions; keep prompts descriptive and general.

## Troubleshooting

- `yt-dlp: command not found`: install `yt-dlp` (or use `--audio ...` mode).
  - macOS (Homebrew): `brew install yt-dlp`
- `ffmpeg: command not found`: install `ffmpeg` and ensure it is in `PATH`.
  - macOS (Homebrew): `brew install ffmpeg` (includes `ffprobe`)
- BPM/key missing: install optional deps with `pip3 install librosa soundfile numpy`.
