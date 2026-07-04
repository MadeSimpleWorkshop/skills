---
name: website-color-pattern-redesign
description: Review and modernize website color systems and visual pattern styling with safe rollout controls. Use when asked to audit an existing site's colors, recommend refreshed palette/pattern directions, generate preview variants, or apply approved color updates to local HTML/CSS codebases.
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

# Website Color Pattern Redesign

## Purpose

Review existing website color usage, propose stronger visual direction, generate a preview build, and apply approved color changes with controlled file updates.

## Workflow

### 1) Capture constraints before editing

Collect:
- Site root path and entry HTML (for example `index.html`)
- Brand constraints (must-keep colors, prohibited colors, accessibility target)
- Desired direction (modern minimal, editorial, playful, premium)
- Scope for rollout (preview only or approved apply)

### 2) Audit current color/pattern usage

Run:

```bash
python3 scripts/color_design_audit.py --root <site_root> --format markdown
```

Use the report to identify:
- Hard-coded colors vs CSS variable usage
- Color sprawl and token duplication
- Gradient/pattern usage and consistency gaps
- Quick wins (tokenization, contrast, accent hierarchy)

### 3) Propose 2-3 redesign directions

Use `references/palette-pattern-playbook.md` to pick a design direction and build a palette spec JSON.
Keep options intentionally different in mood and contrast strategy.

### 4) Generate a non-destructive preview

Create a preview copy and inject a theme override stylesheet:

```bash
python3 scripts/theme_preview_apply.py \
  --mode preview \
  --root <site_root> \
  --entry index.html \
  --palette <palette.json> \
  --out <preview_root>
```

Then serve `<preview_root>` locally and review visual results before touching production files.

### 5) Apply approved updates safely

Apply variable updates directly when variables exist, otherwise write an override file and inject it into the entry HTML:

```bash
python3 scripts/theme_preview_apply.py \
  --mode apply \
  --root <site_root> \
  --entry index.html \
  --palette <palette.json>
```

Use `--replace-literals` only when the palette JSON includes `literal_replacements` and the user approves broad hard-coded replacements.

### 6) Re-audit and summarize outcome

Run `color_design_audit.py` again and compare before/after:
- Changed files
- Variables updated
- Remaining hard-coded color debt
- Follow-up suggestions for additional polish

## Palette Spec Contract

Use this JSON shape:

```json
{
  "name": "coastal-modern",
  "variables": {
    "--color-bg": "#f6f4ef",
    "--color-surface": "#ffffff",
    "--color-text": "#1f2a2e",
    "--color-primary": "#0f766e",
    "--color-accent": "#d97706"
  },
  "pattern_css": "body { background-image: radial-gradient(circle at 10% 20%, rgba(15,118,110,0.08), transparent 45%); }",
  "literal_replacements": {
    "#2f3e46": "#1f2a2e"
  }
}
```

## Guardrails

- Keep preview mode as default. Do not apply without explicit approval.
- Preserve readability and contrast in body text and interactive states.
- Avoid forced brand changes when the user says specific colors are fixed.
- Prefer token-based updates over broad literal replacement.
