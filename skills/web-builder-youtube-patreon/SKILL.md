---
name: web-builder-youtube-patreon
description: Build, review, and optimize websites that drive traffic to YouTube and Patreon. Use when asked to create or improve landing pages, review existing local HTML files, confirm behavior on a live website, research high-impact growth approaches, or recommend conversion-focused changes for YouTube and Patreon traffic funnels.
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

# Web Builder Youtube Patreon

## Purpose

Use this skill to ship web pages that move visitors into two target actions:
1. Watch/subscribe on YouTube.
2. Join/support on Patreon.

## Workflow

### 1) Intake the growth objective

Capture:
- Primary conversion goal (`youtube_click`, `youtube_subscribe_intent`, `patreon_click`, `patreon_signup_intent`)
- Audience segment and promise of value
- Existing local HTML path and optional live URL

Define success metrics before editing:
- CTR to YouTube link/button
- CTR to Patreon link/button
- Scroll depth to primary CTA block

### 2) Review local HTML quickly

Run local preview:

```bash
python3 scripts/local_preview.py --root <site_dir> --entry index.html --port 4173
```

Use this pass to verify:
- Above-the-fold headline clarity
- Presence and placement of YouTube and Patreon CTAs
- Mobile readability
- Page speed risks (heavy hero media, oversized scripts)

Use `--check-only` for non-blocking validation in automated flows:

```bash
python3 scripts/local_preview.py --root <site_dir> --entry index.html --check-only
```

### 3) Confirm live-site behavior and detect gaps

Run a local + live audit:

```bash
python3 scripts/traffic_audit.py --html <site_dir>/index.html --live-url https://example.com --format markdown
```

Use the audit output to compare:
- Metadata parity (`title`, meta description, OpenGraph tags)
- CTA coverage (YouTube/Patreon links and keyword intent)
- Structural quality (headings, forms, embed presence)

### 4) Research and recommend the approach

Read:
- `references/research-framework.md` for positioning and funnel strategy
- `references/traffic-checklist.md` for implementation checks

Prioritize recommendations by:
1. Expected impact on conversion
2. Complexity/time to ship
3. Confidence from available evidence

Always return:
- `Now`: top 1-3 edits to ship immediately
- `Next`: testable experiments with measurable hypotheses
- `Later`: lower-priority improvements

### 5) Build and deliver updates

Edit the site with explicit conversion intent:
- Keep one primary action per section
- Pair YouTube and Patreon CTAs without forcing a choice too early
- Add UTM parameters to outbound campaign links when provided by the user

Use `assets/templates/youtube-patreon-landing.html` as a starting point when asked to build from scratch.

## Output Standard

Return:
1. Changed files and rationale.
2. Audit summary (local, live, key differences).
3. Prioritized recommendation list with expected metric movement.
4. Test plan with at least one A/B variant idea.

## Guardrails

- Preserve brand voice and existing legal/footer requirements.
- Avoid inventing analytics numbers; label assumptions.
- Call out missing data required for confident recommendations.
