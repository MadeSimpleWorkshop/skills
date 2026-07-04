# Per-skill license header

Paste one of these into each skill file so the terms travel with any single
copied skill. Update the year if needed.

---

## For a Markdown skill file (recommended)

Put this at the very top, **above** the YAML frontmatter. It's an HTML comment,
so it stays invisible when the Markdown is rendered but is preserved on copy.

```markdown
<!--
  Copyright © 2026 MadeSimple Workshop. All rights reserved.
  Licensed under PolyForm Noncommercial License 1.0.0 + AI/ML Addendum.
  Noncommercial use only. NOT for training/fine-tuning AI/ML models.
  Full terms: https://github.com/MadeSimpleWorkshop/skills/blob/main/LICENSE.md
  Commercial license: https://github.com/MadeSimpleWorkshop
-->
```

If your tooling requires YAML frontmatter to be the first thing in the file,
put the comment immediately **after** the closing `---` of the frontmatter
instead.

---

## As a YAML frontmatter field (optional, machine-readable)

Add these keys inside the skill's existing frontmatter block:

```yaml
license: PolyForm-Noncommercial-1.0.0 AND LicenseRef-No-AI-Training
license_url: https://github.com/MadeSimpleWorkshop/skills/blob/main/LICENSE.md
copyright: © 2026 MadeSimple Workshop
```

---

## One-line minimal notice (for non-Markdown / code files)

```text
Copyright © 2026 MadeSimple Workshop — PolyForm Noncommercial 1.0.0 + no-AI-training. Commercial: https://github.com/MadeSimpleWorkshop
```

Use `#` for shell/YAML, `//` for JS/TS, `<!-- -->` for HTML/XML, etc.
