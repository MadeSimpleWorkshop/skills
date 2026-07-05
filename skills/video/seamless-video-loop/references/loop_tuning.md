# Loop Tuning Notes

## Recommended Starting Values
- Fireplace/ambient/static scenes: `--xfade-duration 0.8` to `1.5`
- Moderate motion scenes: `0.5` to `1.0`
- Fast cuts/movement: `0.3` to `0.8`

## Quality Tips
- Keep clip fps and resolution consistent before joining.
- Prefer visually similar boundary frames for smoother end-to-start transitions.
- If transitions look washed out, shorten fade duration.
- If boundaries are obvious, slightly increase fade duration.
- For natural motion, try `--transition dissolve` or `--transition fadefast` before more stylized wipes.
- For custom reveals, use `--expr` with simple masks first, such as `if(lte(X,W*P),B,A)`.
