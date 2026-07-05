# Text Cleanup Methods

## Method Selection
Use this table to select the least destructive approach.

| Scenario | Method | Why |
|---|---|---|
| Static subtitle or lower-third in a fixed rectangle | `delogo` | Interpolates pixels in-place and keeps framing unchanged |
| Thin text strip along the very bottom edge | `crop-bottom` | Removes text region entirely, then restores output dimensions |
| Moving text or animated overlays across large areas | Re-edit from source timeline | Inpainting will usually leave visible artifacts |

## Coordinate Tuning Workflow
1. Probe dimensions with ffprobe.
2. Start with a slightly oversized box in `delogo` mode.
3. Use `--show-box` and run a short preview (`--start`, `--duration`).
4. Shrink `--w` and `--h` until text is gone but nearby detail is preserved.

## Quality Guardrails
- Keep source and output codecs practical: `libx264` CRF 18 for high-quality masters.
- Use `libx265` only when smaller size matters more than encode speed.
- Avoid repeated lossy exports; tune once with previews, then render one master.
- Spot-check at start, middle, and end for temporal artifacts.

## Compliance Guardrail
Do not use this skill to remove watermarks, logos, copyright notices, or attribution text.
