#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: qc_youtube_4k_silent.sh <video1> [video2 ...]" >&2
  exit 2
fi

"${SCRIPT_DIR}/qc_video_ffmpeg.sh" \
  --expect-width 3840 \
  --expect-height 2160 \
  --expect-fps 24 \
  --expect-video-codec hevc \
  --expect-pix-fmt yuv420p \
  --expect-audio absent \
  --max-black-duration 1.5 \
  "$@"
