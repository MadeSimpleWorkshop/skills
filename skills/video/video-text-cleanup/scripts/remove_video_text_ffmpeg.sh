#!/usr/bin/env bash
set -euo pipefail

FFMPEG_BIN="${FFMPEG_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg}"
FFPROBE_BIN="${FFPROBE_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffprobe}"

MODE="delogo"
X=""
Y=""
W=""
H=""
SHOW_BOX=0
CROP_PX=""
OUTPUT=""
CODEC="libx264"
CRF=18
PRESET="slow"
AUDIO_MODE="copy"
START=""
DURATION=""
DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage:
  remove_video_text_ffmpeg.sh [options] <input-video>

Description:
  Removes burned-in text overlays from user-owned videos.
  This script is for subtitles/lower-thirds/timestamps, not watermark removal.

Options:
  --mode <delogo|crop-bottom>   Cleanup method (default: delogo)
  --x <px>                      Left position for delogo box
  --y <px>                      Top position for delogo box
  --w <px>                      Width for delogo box
  --h <px>                      Height for delogo box
  --show-box                    Draw the delogo rectangle (preview tuning)
  --crop-px <px>                Bottom pixels to remove for crop-bottom mode
  --start <time>                Optional start position (e.g. 30 or 00:00:30)
  --duration <sec>              Optional render duration (preview)
  --audio <copy|aac|none>       Audio handling (default: copy)
  --codec <libx264|libx265>     Video codec (default: libx264)
  --crf <n>                     CRF quality (default: 18)
  --preset <name>               Encoder preset (default: slow)
  --output <path>               Output path (default: alongside input)
  --dry-run                     Print ffmpeg command and exit
  -h, --help                    Show help

Examples:
  remove_video_text_ffmpeg.sh --mode delogo --x 1240 --y 980 --w 620 --h 86 input.mp4
  remove_video_text_ffmpeg.sh --mode crop-bottom --crop-px 88 --output clean.mp4 input.mp4
  remove_video_text_ffmpeg.sh --mode delogo --x 1240 --y 980 --w 620 --h 86 --start 30 --duration 12 input.mp4
USAGE
}

is_int() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"; shift 2 ;;
    --x)
      X="$2"; shift 2 ;;
    --y)
      Y="$2"; shift 2 ;;
    --w)
      W="$2"; shift 2 ;;
    --h)
      H="$2"; shift 2 ;;
    --show-box)
      SHOW_BOX=1; shift ;;
    --crop-px)
      CROP_PX="$2"; shift 2 ;;
    --start)
      START="$2"; shift 2 ;;
    --duration)
      DURATION="$2"; shift 2 ;;
    --audio)
      AUDIO_MODE="$2"; shift 2 ;;
    --codec)
      CODEC="$2"; shift 2 ;;
    --crf)
      CRF="$2"; shift 2 ;;
    --preset)
      PRESET="$2"; shift 2 ;;
    --output)
      OUTPUT="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    --)
      shift; break ;;
    -* )
      echo "Unknown option: $1" >&2
      usage
      exit 2 ;;
    *)
      break ;;
  esac
done

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

INPUT="$1"
if [[ ! -f "$INPUT" ]]; then
  echo "Missing input file: $INPUT" >&2
  exit 1
fi

if [[ ! -x "$FFMPEG_BIN" || ! -x "$FFPROBE_BIN" ]]; then
  echo "ffmpeg/ffprobe not found. Set FFMPEG_BIN and FFPROBE_BIN." >&2
  exit 1
fi

case "$MODE" in
  delogo|crop-bottom) ;;
  *)
    echo "Unsupported --mode: $MODE" >&2
    exit 2 ;;
esac

case "$AUDIO_MODE" in
  copy|aac|none) ;;
  *)
    echo "Unsupported --audio mode: $AUDIO_MODE" >&2
    exit 2 ;;
esac

case "$CODEC" in
  libx264|libx265) ;;
  *)
    echo "Unsupported --codec: $CODEC" >&2
    exit 2 ;;
esac

if ! is_int "$CRF"; then
  echo "--crf must be an integer" >&2
  exit 2
fi

dims="$($FFPROBE_BIN -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$INPUT")"
if [[ -z "$dims" ]]; then
  echo "Unable to probe width/height: $INPUT" >&2
  exit 1
fi

WIDTH="${dims%x*}"
HEIGHT="${dims#*x}"

if ! is_int "$WIDTH" || ! is_int "$HEIGHT"; then
  echo "Invalid probed dimensions: $dims" >&2
  exit 1
fi

DURATION_TOTAL="$($FFPROBE_BIN -v error -show_entries format=duration -of default=nw=1:nk=1 "$INPUT")"

if [[ -z "$OUTPUT" ]]; then
  input_dir="$(dirname "$INPUT")"
  input_name="$(basename "$INPUT")"
  input_stem="${input_name%.*}"
  OUTPUT="${input_dir}/${input_stem}_${MODE}_clean.mp4"
fi

if [[ "$MODE" == "delogo" ]]; then
  for val in "$X" "$Y" "$W" "$H"; do
    if ! is_int "$val"; then
      echo "--x --y --w --h are required integer values for delogo mode" >&2
      exit 2
    fi
  done

  if [[ "$W" -le 0 || "$H" -le 0 ]]; then
    echo "--w and --h must be > 0" >&2
    exit 2
  fi

  if [[ "$X" -lt 0 || "$Y" -lt 0 ]]; then
    echo "--x and --y must be >= 0" >&2
    exit 2
  fi

  if [[ $((X + W)) -gt "$WIDTH" || $((Y + H)) -gt "$HEIGHT" ]]; then
    echo "Delogo box exceeds frame bounds (${WIDTH}x${HEIGHT})" >&2
    exit 2
  fi

  FILTER="delogo=x=${X}:y=${Y}:w=${W}:h=${H}"
  if [[ "$SHOW_BOX" -eq 1 ]]; then
    FILTER+="\:show=1"
  fi
else
  if ! is_int "$CROP_PX" || [[ "$CROP_PX" -le 0 ]]; then
    echo "--crop-px must be an integer > 0 for crop-bottom mode" >&2
    exit 2
  fi

  if [[ "$CROP_PX" -ge "$HEIGHT" ]]; then
    echo "--crop-px must be smaller than frame height (${HEIGHT})" >&2
    exit 2
  fi

  NEW_HEIGHT=$((HEIGHT - CROP_PX))
  FILTER="crop=iw:${NEW_HEIGHT}:0:0,scale=${WIDTH}:${HEIGHT}:flags=lanczos"
fi

cmd=(
  "$FFMPEG_BIN" -hide_banner -y
)

if [[ -n "$START" ]]; then
  cmd+=( -ss "$START" )
fi

cmd+=( -i "$INPUT" )

if [[ -n "$DURATION" ]]; then
  cmd+=( -t "$DURATION" )
fi

cmd+=(
  -map 0:v:0
  -vf "$FILTER"
  -c:v "$CODEC"
  -preset "$PRESET"
  -crf "$CRF"
  -pix_fmt yuv420p
)

case "$AUDIO_MODE" in
  copy)
    cmd+=( -map 0:a? -c:a copy ) ;;
  aac)
    cmd+=( -map 0:a? -c:a aac -b:a 192k ) ;;
  none)
    cmd+=( -an ) ;;
esac

cmd+=( -movflags +faststart "$OUTPUT" )

echo "Input:           $INPUT"
echo "Frame size:      ${WIDTH}x${HEIGHT}"
echo "Input duration:  ${DURATION_TOTAL}s"
echo "Mode:            $MODE"
if [[ "$MODE" == "delogo" ]]; then
  echo "Delogo box:      x=$X y=$Y w=$W h=$H show_box=$SHOW_BOX"
else
  echo "Crop bottom px:  $CROP_PX"
fi
if [[ -n "$START" ]]; then
  echo "Start:           $START"
fi
if [[ -n "$DURATION" ]]; then
  echo "Duration:        $DURATION"
fi
echo "Output:          $OUTPUT"

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf 'Command: '
  printf '%q ' "${cmd[@]}"
  printf '\n'
  exit 0
fi

"${cmd[@]}"

"$FFPROBE_BIN" -v error \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate \
  -show_entries format=duration,size \
  -of default=nw=1:nk=0 \
  "$OUTPUT"
