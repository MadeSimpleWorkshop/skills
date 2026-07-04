# Palette and Pattern Playbook

Use this guide to produce clear redesign options before touching source files.

## 1) Define color roles before choosing colors

Use semantic roles instead of raw literals:
- `--color-bg`
- `--color-surface`
- `--color-text`
- `--color-text-muted`
- `--color-primary`
- `--color-accent`
- `--color-border`

This keeps redesigns portable across pages/components.

## 2) Build at least two distinct directions

Direction A should optimize familiarity and safety.
Direction B should create stronger visual separation from the current look.

Use deliberate contrast differences:
- Conservative: neutral base + one accent family
- Expressive: neutral base + strong primary + contrasting accent

## 3) Pattern strategy options

Choose one pattern approach at a time:
- Depth layer: low-opacity radial/linear gradient in page background
- Section rhythm: alternating surface/background tokens by section
- Texture hint: subtle repeating pattern with low alpha

Avoid combining multiple strong patterns in one pass.

## 4) Contrast checks

Target minimum readability:
- Body text vs main background: 4.5:1 or better
- Large headings: 3:1 or better
- Buttons and interactive states: visually distinct in default/hover/focus

## 5) Palette JSON contract

Save palette specs in this shape:

```json
{
  "name": "warm-editorial",
  "variables": {
    "--color-bg": "#f7f2ea",
    "--color-surface": "#fffdf9",
    "--color-text": "#1f2933",
    "--color-text-muted": "#536471",
    "--color-primary": "#0f766e",
    "--color-accent": "#c2410c",
    "--color-border": "#d9cfc0"
  },
  "pattern_css": "body { background-image: radial-gradient(circle at 12% 18%, rgba(15,118,110,0.12), transparent 45%); }",
  "literal_replacements": {
    "#2f3e46": "#1f2933"
  }
}
```

## 6) Decision framing for user review

Present each option with:
- Mood statement in one sentence
- Top 3 color-role differences from current site
- Expected UX impact (clarity, warmth, contrast, visual hierarchy)
- Rollout risk level (`low`, `medium`, `high`)
