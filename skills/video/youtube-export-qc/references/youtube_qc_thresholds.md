# YouTube QC Thresholds

## Recommended Baselines
- Resolution:
  - 4K UHD: `3840x2160`
  - 8K UHD: `7680x4320`
- Frame rate: match source intent (`24`, `30`, or `60`) and keep consistent.
- Codec/pix_fmt (common delivery):
  - `hevc` with `yuv420p` for broad compatibility.
- Audio policy:
  - Silent ambience loops: expect no audio tracks.
  - Music videos: require audio track, check for long silences.

## Detector Defaults in This Skill
- `blackdetect`: `d=0.5`, `pix_th=0.10`, `pic_th=0.98`
- `silencedetect`: `noise=-50dB`, `d=1.0`

## Practical Fail Thresholds
Adjust by content type:
- Static ambience/fireplace loops:
  - `--max-black-duration 1.5`
  - no silence check if output is intentionally silent
- Music content:
  - `--max-black-duration 1.5`
  - `--max-silence-duration 4.0`

## Notes
- Crossfades can produce short near-black or near-silence intervals; tune thresholds per project.
- If expected intentional fades are flagged, raise thresholds slightly rather than disabling checks.
