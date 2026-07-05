#!/usr/bin/env bash
set -euo pipefail

FFMPEG_BIN="${FFMPEG_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg}"
FFPROBE_BIN="${FFPROBE_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffprobe}"

WIDTH=3840
HEIGHT=2160
FPS=24
CRF=18
PRESET="slow"
TRANSITION="fade"
XFADE_DURATION="0.8"
XFADE_EXPR=""
XFADE_EXPR_PRESET=""
OUTPUT=""
DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage:
  loopable_join_ffmpeg.sh [options] <clip1> <clip2> [clip3 ...]

Description:
  Create a seamless loopable output by crossfading each clip to the next,
  then crossfading the last clip back into the first clip.

Defaults:
  - Output resolution: 3840x2160
  - Output FPS: 24
  - Transition: fade
  - Crossfade duration: 0.8s
  - Video codec: libx265 (HEVC), CRF 18, preset slow
  - Audio removed (-an)

Options:
  --width <n>            Output width (default: 3840)
  --height <n>           Output height (default: 2160)
  --fps <n>              Output fps (default: 24)
  --crf <n>              libx265 CRF (default: 18)
  --preset <name>        libx265 preset (default: slow)
  --transition <name>    xfade transition (default: fade)
  --xfade-duration <s>   xfade duration seconds (default: 0.8)
  --expr <expr>          xfade custom expression; implies --transition custom
  --output <path>        Output file path
  --dry-run              Print command without running
  -h, --help             Show help

Examples:
  loopable_join_ffmpeg.sh clip1.mov clip2.mov clip3.mov
  loopable_join_ffmpeg.sh --xfade-duration 1.0 --output /tmp/loop.mov a.mp4 b.mp4 c.mp4 d.mp4
  loopable_join_ffmpeg.sh --expr 'if(lte(X,W*P),B,A)' --output /tmp/loop.mov a.mp4 b.mp4
USAGE
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

escape_filter_expr() {
  local value="$1"
  value="${value//\\/\\\\}"
  printf "%s" "$value"
}

resolve_expr_preset() {
  case "$1" in
    horizontal-reveal)
      printf "%s" "if(lte(X,W*P),B,A)"
      ;;
    vertical-reveal)
      printf "%s" "if(lte(Y,H*P),B,A)"
      ;;
    diagonal-reveal)
      printf "%s" "if(lte(X+Y,(W+H)*P),B,A)"
      ;;
    center-open)
      printf "%s" "if(gte(X,W/2-W/2*P)*lte(X,W/2+W/2*P)*gte(Y,H/2-H/2*P)*lte(Y,H/2+H/2*P),B,A)"
      ;;
    *)
      echo "Unknown --expr-preset: $1" >&2
      echo "Available presets: horizontal-reveal, vertical-reveal, diagonal-reveal, center-open" >&2
      exit 1
      ;;
  esac
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
    --fps)
      FPS="$2"
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
    --transition)
      TRANSITION="$2"
      shift 2
      ;;
    --xfade-duration)
      XFADE_DURATION="$2"
      shift 2
      ;;
    --expr)
      XFADE_EXPR="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
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
    -* )
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 2 ]]; then
  echo "Need at least 2 clips." >&2
  usage
  exit 1
fi

if [[ ! -x "$FFMPEG_BIN" ]]; then
  echo "ffmpeg not found at: $FFMPEG_BIN" >&2
  exit 1
fi

if [[ ! -x "$FFPROBE_BIN" ]]; then
  echo "ffprobe not found at: $FFPROBE_BIN" >&2
  exit 1
fi

input_files=("$@")
for input_path in "${input_files[@]}"; do
  if [[ ! -f "$input_path" ]]; then
    echo "Missing file: $input_path" >&2
    exit 1
  fi
done

if [[ -z "$OUTPUT" ]]; then
  first_dir="$(dirname "${input_files[0]}")"
  first_stem="$(basename "${input_files[0]}")"
  first_stem="${first_stem%.*}"
  OUTPUT="${first_dir}/${first_stem}_loopable_${WIDTH}x${HEIGHT}_silent_ffmpeg.mov"
fi

if [[ -n "$XFADE_EXPR" ]]; then
  if [[ "$TRANSITION" == "fade" ]]; then
    TRANSITION="custom"
  elif [[ "$TRANSITION" != "custom" ]]; then
    echo "When --expr is provided, --transition must be custom or omitted." >&2
    exit 1
  fi
fi

escaped_xfade_expr=""
if [[ -n "$XFADE_EXPR" ]]; then
  escaped_xfade_expr="$(escape_filter_expr "$XFADE_EXPR")"
fi

durations=()
for input_path in "${input_files[@]}"; do
  duration="$($FFPROBE_BIN -v error -show_entries format=duration -of default=nw=1:nk=1 "$input_path" || true)"
  if [[ -z "$duration" ]]; then
    echo "Could not read duration: $input_path" >&2
    exit 1
  fi
  duration="$(awk -v d="$duration" 'BEGIN { printf "%.6f", d + 0 }')"

  if awk -v d="$duration" -v x="$XFADE_DURATION" 'BEGIN { exit !(d <= x) }'; then
    echo "Clip is too short for selected xfade duration ($XFADE_DURATION s): $input_path" >&2
    exit 1
  fi

  durations+=("$duration")
done

clip_count=${#input_files[@]}
offsets=()
cumulative="0"
for ((i = 0; i < clip_count; i++)); do
  cumulative="$(float_add "$cumulative" "${durations[$i]}")"
  fade_total="$(float_mul "$XFADE_DURATION" "$((i + 1))")"
  offset="$(float_sub "$cumulative" "$fade_total")"
  offsets+=("$(float_non_negative "$offset")")
done

loop_duration="$(float_sub "$cumulative" "$(float_mul "$XFADE_DURATION" "$clip_count")")"
if awk -v d="$loop_duration" 'BEGIN { exit !(d <= 0) }'; then
  echo "Calculated loop duration is not positive. Reduce xfade duration." >&2
  exit 1
fi

filter_parts=()
for idx in "${!input_files[@]}"; do
  filter_parts+=("[${idx}:v]zscale=w=${WIDTH}:h=${HEIGHT}:filter=lanczos:dither=error_diffusion,fps=${FPS},format=yuv420p,setpts=PTS-STARTPTS[v${idx}]")
done

repeat_idx=$clip_count
filter_parts+=("[${repeat_idx}:v]zscale=w=${WIDTH}:h=${HEIGHT}:filter=lanczos:dither=error_diffusion,fps=${FPS},format=yuv420p,setpts=PTS-STARTPTS[v${repeat_idx}]")

prev_label="v0"
for ((i = 0; i < clip_count; i++)); do
  next_idx=$((i + 1))
  out_label="vx${next_idx}"
  xfade_filter="xfade=transition=${TRANSITION}:duration=${XFADE_DURATION}:offset=${offsets[$i]}"
  if [[ -n "$XFADE_EXPR" ]]; then
    xfade_filter="${xfade_filter}:expr='${escaped_xfade_expr}'"
  fi
  filter_parts+=("[${prev_label}][v${next_idx}]${xfade_filter}[${out_label}]")
  prev_label="$out_label"
done

filter_parts+=("[${prev_label}]trim=start=${XFADE_DURATION}:duration=${loop_duration},setpts=PTS-STARTPTS[vout]")
filter_complex="$(IFS=';'; echo "${filter_parts[*]}")"

cmd=("$FFMPEG_BIN" -hide_banner -y)
for input_path in "${input_files[@]}"; do
  cmd+=(-i "$input_path")
done
cmd+=(-i "${input_files[0]}")
cmd+=(
  -filter_complex "$filter_complex"
  -map "[vout]"
  -an
  -c:v libx265
  -preset "$PRESET"
  -crf "$CRF"
  -pix_fmt yuv420p
  -tag:v hvc1
  -movflags +faststart
  "$OUTPUT"
)

echo "Creating loopable seamless output"
echo "Clips:       $clip_count"
echo "Resolution:  ${WIDTH}x${HEIGHT}"
echo "Transition:  ${TRANSITION} (${XFADE_DURATION}s)"
if [[ -n "$XFADE_EXPR" ]]; then
  echo "Expression:  ${XFADE_EXPR}"
fi
echo "Loop length: ${loop_duration}s"
echo "Output:      $OUTPUT"

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf 'Command: '
  printf '%q ' "${cmd[@]}"
  printf '\n'
  exit 0
fi

"${cmd[@]}"

dims="$($FFPROBE_BIN -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$OUTPUT" || true)"
audio_count="$($FFPROBE_BIN -v error -select_streams a -show_entries stream=index -of csv=p=0 "$OUTPUT" | wc -l | tr -d ' ')"
duration="$($FFPROBE_BIN -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUTPUT" || true)"

echo "Verified: ${dims:-unknown}, duration=${duration:-unknown}, audioTracks=${audio_count:-unknown}"
