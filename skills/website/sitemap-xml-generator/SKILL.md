---
name: sitemap-xml-generator
description: Generate or update a standards-compliant sitemap.xml for Google/Bing by scanning a local website folder (static build output like dist/build/public/out/_site). Use when asked to create sitemap.xml, add sitemap to robots.txt, or list site URLs for search indexing.
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

# Sitemap XML Generator

## Quick Start

Generate `sitemap.xml` from a local site folder:

```bash
python3 scripts/generate_sitemap.py \
  --root /path/to/site-root \
  --base-url https://example.com \
  --out /path/to/site-root/sitemap.xml
```

Defaults:
- Includes: `.html`, `.htm`
- Ignores: `.php`
- Ignores hidden/metadata files (anything starting with `.` like `.DS_Store`, `._*`)

Also add/update a `Sitemap:` line in `robots.txt`:
If `robots.txt` does not exist, it will be created with a minimal allow-all record plus the sitemap line.

```bash
python3 scripts/generate_sitemap.py \
  --root /path/to/site-root \
  --base-url https://example.com \
  --out /path/to/site-root/sitemap.xml \
  --robots /path/to/site-root/robots.txt
```

## Workflow

1. Choose the correct `--root` directory.
   - Use the folder that maps to your web root (the one that contains `index.html`).
   - Common static output folders: `dist/`, `build/`, `public/`, `out/`, `_site/`.
2. Run the generator and review the URL count + any warnings.
3. If URLs look wrong, adjust flags:
   - `--exclude-glob` to skip admin/test pages.
   - `--strip-html-ext` if your server rewrites `*.html` to extensionless URLs.
   - `--trailing-slash` if you want `/about/` instead of `/about`.

## Output Standard

- Write `sitemap.xml` to the path given by `--out`.
- Include `<loc>` and (by default) `<lastmod>` based on file mtime.
- Keep output stable by sorting URLs.

## After Deploy

- Ensure the sitemap is publicly reachable at `https://your-domain.com/sitemap.xml`.
- Submit that URL in Google Search Console and Bing Webmaster Tools.
