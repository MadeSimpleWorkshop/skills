---
name: camtasia-youtube-timestamps
description: Parse Camtasia-exported XML/XMP marker files into YouTube chapter timestamps and optionally inject or update chapter blocks in YouTube description text. Use when a user provides Camtasia metadata files (for example `xmpFile.xml`) and asks to generate timestamps, clean marker labels, or insert chapters into upload details.
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

# Camtasia YouTube Timestamps

## Overview
Convert Camtasia table-of-contents markers into YouTube-ready chapter lines.
Use the bundled parser script for deterministic extraction, formatting, filtering, and description merging.

## Workflow
1. Confirm the Camtasia metadata file path (`xmpFile.xml` or similar XMP/XML).
2. Run the parser script to generate chapter lines.
3. Review labels and optionally adjust filtering.
4. Merge chapters into a YouTube description text file when requested.
5. Return final chapters (and output file path if written).

## Quick Start
Run commands from the skill directory.

- Generate chapter lines:
```bash
python3 scripts/parse_camtasia_xmp.py /path/to/xmpFile.xml
```

- Generate JSON payload:
```bash
python3 scripts/parse_camtasia_xmp.py /path/to/xmpFile.xml --format json
```

- Keep placeholder markers (default behavior skips `Marker`):
```bash
python3 scripts/parse_camtasia_xmp.py /path/to/xmpFile.xml --include-placeholder
```

- Merge chapters into an existing description:
```bash
python3 scripts/parse_camtasia_xmp.py /path/to/xmpFile.xml \
  --description-in /path/to/description.txt \
  --description-out /path/to/description.with-chapters.txt
```

## Defaults
- Skip placeholder names equal to `Marker` (case-insensitive).
- Add `0:00 Intro` when first marker starts after zero.
- Convert marker start times from milliseconds to YouTube timestamp format (`M:SS` or `H:MM:SS`).
- De-duplicate repeated markers.

## Output Behavior
- Emit chapter lines to stdout by default.
- Support `--output` for writing chapters to file.
- Use block markers when merging descriptions:
  - `<!-- CAMTASIA_CHAPTERS_START -->`
  - `<!-- CAMTASIA_CHAPTERS_END -->`
- Replace existing chapter block on re-run instead of appending duplicates.

## Resources
- Parser script: `scripts/parse_camtasia_xmp.py`
- Format and troubleshooting notes: `references/camtasia-xmp-format.md`
