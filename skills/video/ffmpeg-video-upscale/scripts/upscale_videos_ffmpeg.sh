#!/usr/bin/env bash
set -euo pipefail

FFMPEG_BIN="${FFMPEG_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg}"
FFPROBE_BIN="${FFPROBE_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffprobe}"

WIDTH=3840
HEIGHT=2160
CRF=18
PRESET="slow"
SUFFIX=""
DRY_RUN=0
JOIN_MODE=0
JOIN_OUTPUT=""
JOIN_XFADE_DURATION="0.8"
JOIN_TRANSITION="fade"
JOIN_FPS=24

usage() {
  cat <<'EOF'
Usage:
  upscale_videos_ffmpeg.sh [options] <video1> [video2 ...]

Defaults:
  - Upscale to 3840x2160
  - Strip audio (silent output)
  - HEVC via libx265, CRF 18, preset slow
  - Per-file output suffix: _<width>x<height>_silent_ffmpeg.mov
  - Seamless join mode uses xfade transition "fade" for 0.8s

Options:
  --width <n>          Output width (default: 3840)
  --height <n>         Output height (default: 2160)
  --crf <n>            libx265 CRF quality (default: 18)
  --preset <name>      libx265 preset (default: slow)
  --suffix <text>      Custom suffix before .mov extension
  --join-seamless      Join all inputs into one seamless output using xfade
  --join-output <path> Output file path for join mode
  --xfade-duration <s> Crossfade duration in seconds (default: 0.8)
  --transition <name>  xfade transition type (default: fade)
  --join-fps <n>       Force FPS in join mode (default: 24)
  --dry-run            Print ffmpeg commands without running
  -h, --help           Show this help text

Examples:
  scripts/upscale_videos_ffmpeg.sh "/path/input 1.mp4" "/path/input 2.mp4"
  scripts/upscale_videos_ffmpeg.sh --crf 16 --preset medium *.mp4
  scripts/upscale_videos_ffmpeg.sh --join-seamless --xfade-duration 1.0 clip1.mp4 clip2.mp4 clip3.mp4
EOF
}

float_add() {
  awk -v a="$1" -v b="$2" 'BEGIN { printf "%.6f", a + b }'
}

float_sub() {
  awk -v a="$1" -v b="$2" 'BEGIN { printf "%.6f", a - b }'
}

float_mul() {
  awk -v a="$1" -v b="$2" 'BEGIN { printf "%.6f", a * b }'
}

float_non_negative() {
  awk -v v="$1" 'BEGIN { if (v < 0) v = 0; printf "%.6f", v }'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --width)
      WIDTH="$2"
      shift 2
      ;;
    --height)
      HEIGHT="$2"
      shift 2
      ;;
    --crf)
      CRF="$2"
      shift 2
      ;;
    --preset)
      PRESET="$2"
      shift 2
      ;;
    --suffix)
      SUFFIX="$2"
      shift 2
      ;;
    --join-seamless)
      JOIN_MODE=1
      shift
      ;;
    --join-output)
      JOIN_OUTPUT="$2"
      shift 2
      ;;
    --xfade-duration)
      JOIN_XFADE_DURATION="$2"
      shift 2
      ;;
    --transition)
      JOIN_TRANSITION="$2"
      shift 2
      ;;
    --join-fps)
      JOIN_FPS="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

if [[ ! -x "$FFMPEG_BIN" ]]; then
  echo "ffmpeg not found at: $FFMPEG_BIN" >&2
  echo "Set FFMPEG_BIN or add /opt/homebrew/opt/ffmpeg-full/bin to PATH." >&2
  exit 1
fi

if [[ ! -x "$FFPROBE_BIN" ]]; then
  echo "ffprobe not found at: $FFPROBE_BIN" >&2
  echo "Set FFPROBE_BIN or add /opt/homebrew/opt/ffmpeg-full/bin to PATH." >&2
  exit 1
fi

if [[ "$JOIN_MODE" -eq 1 ]]; then
  if [[ $# -lt 2 ]]; then
    echo "--join-seamless requires at least 2 input videos." >&2
    exit 1
  fi

  input_files=("$@")
  for input_path in "${input_files[@]}"; do
    if [[ ! -f "$input_path" ]]; then
      echo "Missing file: $input_path" >&2
      exit 1
    fi
  done

  if [[ -z "$JOIN_OUTPUT" ]]; then
    first_dir="$(dirname "${input_files[0]}")"
    JOIN_OUTPUT="${first_dir}/seamless_join_${WIDTH}x${HEIGHT}_silent_ffmpeg.mov"
  fi

  durations=()
  for input_path in "${input_files[@]}"; do
    duration="$("$FFPROBE_BIN" -v error -show_entries format=duration -of default=nw=1:nk=1 "$input_path" || true)"
    if [[ -z "$duration" ]]; then
      echo "Could not read duration: $input_path" >&2
      exit 1
    fi
    durations+=("$(awk -v d="$duration" 'BEGIN { printf "%.6f", d + 0 }')")
  done

  filter_parts=()
  for idx in "${!input_files[@]}"; do
    filter_parts+=("[${idx}:v]zscale=w=${WIDTH}:h=${HEIGHT}:filter=lanczos:dither=error_diffusion,fps=${JOIN_FPS},format=yuv420p,setpts=PTS-STARTPTS[v${idx}]")
  done

  prev_label="v0"
  cumulative="0"
  transition_steps=()
  for ((i = 0; i < ${#input_files[@]} - 1; i++)); do
    cumulative="$(float_add "$cumulative" "${durations[$i]}")"
    fade_total="$(float_mul "$JOIN_XFADE_DURATION" "$((i + 1))")"
    offset="$(float_sub "$cumulative" "$fade_total")"
    offset="$(float_non_negative "$offset")"
    next_idx=$((i + 1))
    out_label="vx${next_idx}"
    filter_parts+=("[${prev_label}][v${next_idx}]xfade=transition=${JOIN_TRANSITION}:duration=${JOIN_XFADE_DURATION}:offset=${offset}[${out_label}]")
    transition_steps+=("transition_${next_idx}: offset=${offset}s")
    prev_label="$out_label"
  done

  filter_complex="$(IFS=';'; echo "${filter_parts[*]}")"

  cmd=("$FFMPEG_BIN" -hide_banner -y)
  for input_path in "${input_files[@]}"; do
    cmd+=(-i "$input_path")
  done
  cmd+=(
    -filter_complex "$filter_complex"
    -map "[${prev_label}]"
    -an
    -c:v libx265
    -preset "$PRESET"
    -crf "$CRF"
    -pix_fmt yuv420p
    -tag:v hvc1
    -movflags +faststart
    "$JOIN_OUTPUT"
  )

  echo "Processing seamless join with ${#input_files[@]} inputs"
  echo "Output:     $JOIN_OUTPUT"
  echo "Transition: ${JOIN_TRANSITION} (${JOIN_XFADE_DURATION}s)"
  for step in "${transition_steps[@]}"; do
    echo "  $step"
  done

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf 'Command: '
    printf '%q ' "${cmd[@]}"
    printf '\n\n'
    exit 0
  fi

  "${cmd[@]}"

  dims="$("$FFPROBE_BIN" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$JOIN_OUTPUT" || true)"
  audio_count="$("$FFPROBE_BIN" -v error -select_streams a -show_entries stream=index -of csv=p=0 "$JOIN_OUTPUT" | wc -l | tr -d ' ')"
  echo "Verified:   ${dims:-unknown}, audioTracks=${audio_count:-unknown}"
  exit 0
fi

if [[ -z "$SUFFIX" ]]; then
  SUFFIX="_${WIDTH}x${HEIGHT}_silent_ffmpeg"
fi

for input_path in "$@"; do
  if [[ ! -f "$input_path" ]]; then
    echo "Skipping missing file: $input_path" >&2
    continue
  fi

  input_dir="$(dirname "$input_path")"
  input_file="$(basename "$input_path")"
  input_stem="${input_file%.*}"
  output_path="${input_dir}/${input_stem}${SUFFIX}.mov"

  filter_graph="zscale=w=${WIDTH}:h=${HEIGHT}:filter=lanczos:dither=error_diffusion,format=yuv420p"

  cmd=(
    "$FFMPEG_BIN"
    -hide_banner
    -y
    -i "$input_path"
    -map_metadata 0
    -map_chapters -1
    -an
    -vf "$filter_graph"
    -c:v libx265
    -preset "$PRESET"
    -crf "$CRF"
    -pix_fmt yuv420p
    -tag:v hvc1
    -movflags +faststart
    "$output_path"
  )

  echo "Processing: $input_path"
  echo "Output:     $output_path"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf 'Command: '
    printf '%q ' "${cmd[@]}"
    printf '\n\n'
    continue
  fi

  "${cmd[@]}"

  dims="$("$FFPROBE_BIN" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$output_path" || true)"
  audio_count="$("$FFPROBE_BIN" -v error -select_streams a -show_entries stream=index -of csv=p=0 "$output_path" | wc -l | tr -d ' ')"
  echo "Verified:   ${dims:-unknown}, audioTracks=${audio_count:-unknown}"
  echo
done
