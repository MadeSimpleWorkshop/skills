#!/usr/bin/env bash
set -euo pipefail

FFPROBE_BIN="${FFPROBE_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffprobe}"

if [[ $# -ne 1 ]]; then
  echo "Usage: verify_video_output.sh <video-file>" >&2
  exit 1
fi

video="$1"
if [[ ! -f "$video" ]]; then
  echo "Missing file: $video" >&2
  exit 1
fi

if [[ ! -x "$FFPROBE_BIN" ]]; then
  echo "ffprobe not found at: $FFPROBE_BIN" >&2
  exit 1
fi

"$FFPROBE_BIN" -v error \
  -show_entries stream=width,height \
  -select_streams v:0 \
  -show_entries format=duration,size \
  -of default=nw=1:nk=0 \
  "$video"

ac="$($FFPROBE_BIN -v error -select_streams a -show_entries stream=index -of csv=p=0 "$video" | wc -l | tr -d ' ')"
echo "audioTracks=$ac"
