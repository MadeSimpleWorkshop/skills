# Camtasia XMP Marker Notes

## Marker Fields Used
- Marker title: `xmpDM:name`
- Marker time (milliseconds): `xmpDM:startTime`
- Typical marker container path:
  - `xmpDM:Tracks -> rdf:Bag -> rdf:li -> rdf:Description (track) -> xmpDM:markers -> rdf:Seq -> rdf:li -> rdf:Description (marker)`

## YouTube Chapter Rules (Practical)
- Keep timestamps in ascending order.
- Include a `0:00` first chapter (script handles this by default).
- Prefer short, clear labels.

## Common Cleanup Steps
- Remove generic placeholders like `Marker`.
- Collapse duplicate titles/timestamps.
- Rename rough draft labels before publish.

## Script Options You Will Use Most
- `--no-ensure-zero`: do not auto-add `0:00 Intro`
- `--intro-title "Welcome"`: customize inserted zero marker title
- `--min-gap-seconds 5`: suppress noisy, near-duplicate chapters
- `--description-in` + `--description-out`: inject chapters into a description file
