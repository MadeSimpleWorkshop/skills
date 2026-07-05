#!/usr/bin/env bash
set -euo pipefail

FFMPEG_BIN="${FFMPEG_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg}"
FFPROBE_BIN="${FFPROBE_BIN:-/opt/homebrew/opt/ffmpeg-full/bin/ffprobe}"

EXPECT_WIDTH=""
EXPECT_HEIGHT=""
EXPECT_FPS=""
EXPECT_VIDEO_CODEC=""
EXPECT_PIX_FMT=""
EXPECT_AUDIO="any"  # any|present|absent

BLACK_DETECT_DURATION="0.5"
BLACK_DETECT_PIX_TH="0.10"
BLACK_DETECT_PIC_TH="0.98"
MAX_BLACK_DURATION=""

SILENCE_DETECT_DURATION="1.0"
SILENCE_DETECT_NOISE="-50dB"
MAX_SILENCE_DURATION=""

SHOW_DETAILS=0

usage() {
  cat <<'USAGE'
Usage:
  qc_video_ffmpeg.sh [options] <video1> [video2 ...]

Description:
  Run pre-upload QC checks on one or more videos.
  Reports PASS/WARN/FAIL and exits non-zero if any file fails.

Metadata checks (ffprobe):
  - resolution, fps, codec, profile, pixel format, bitrate, duration, audio tracks

Signal checks (ffmpeg):
  - black segment detection (blackdetect)
  - silence segment detection (silencedetect, when audio exists)

Options:
  --expect-width <n>              Expected width
  --expect-height <n>             Expected height
  --expect-fps <n>                Expected fps (rounded to 3 decimals)
  --expect-video-codec <name>     Expected video codec (e.g., hevc, h264)
  --expect-pix-fmt <name>         Expected pixel format (e.g., yuv420p)
  --expect-audio <mode>           any|present|absent (default: any)

  --max-black-duration <seconds>  Fail if any black segment exceeds this
  --max-silence-duration <sec>    Fail if any silence segment exceeds this

  --black-detect-duration <sec>   blackdetect d (default: 0.5)
  --black-detect-pix-th <float>   blackdetect pix_th (default: 0.10)
  --black-detect-pic-th <float>   blackdetect pic_th (default: 0.98)
  --silence-detect-duration <sec> silencedetect d (default: 1.0)
  --silence-detect-noise <db>     silencedetect noise (default: -50dB)

  --details                       Print command-level diagnostic lines
  -h, --help                      Show help

Examples:
  qc_video_ffmpeg.sh --expect-width 3840 --expect-height 2160 --expect-fps 24 --expect-audio absent file.mov
  qc_video_ffmpeg.sh --expect-video-codec hevc --expect-pix-fmt yuv420p --max-black-duration 1.5 *.mov
USAGE
}

float_from_fraction() {
  awk -v f="$1" 'BEGIN {
    n=split(f,a,"/");
    if (n==2 && a[2] != 0) printf "%.6f", a[1]/a[2];
    else if (n==1) printf "%.6f", a[1]+0;
    else printf "0.000000";
  }'
}

float_gt() {
  awk -v a="$1" -v b="$2" 'BEGIN { exit !(a > b) }'
}

abs_diff() {
  awk -v a="$1" -v b="$2" 'BEGIN { d=a-b; if (d<0) d=-d; printf "%.6f", d }'
}

require_bins() {
  if [[ ! -x "$FFPROBE_BIN" ]]; then
    echo "ffprobe not found at: $FFPROBE_BIN" >&2
    exit 2
  fi
  if [[ ! -x "$FFMPEG_BIN" ]]; then
    echo "ffmpeg not found at: $FFMPEG_BIN" >&2
    exit 2
  fi
}

run_blackdetect() {
  local file="$1"
  local log
  log="$($FFMPEG_BIN -hide_banner -v info -i "$file" -vf "blackdetect=d=${BLACK_DETECT_DURATION}:pix_th=${BLACK_DETECT_PIX_TH}:pic_th=${BLACK_DETECT_PIC_TH}" -an -f null - 2>&1 || true)"

  local max_black
  max_black="$(printf '%s\n' "$log" | awk '
    BEGIN { m=0 }
    /black_duration:/ {
      for (i=1; i<=NF; i++) {
        if ($i ~ /^black_duration:/) {
          sub("black_duration:","",$i)
          v=$i+0
          if (v>m) m=v
        }
      }
    }
    END { printf "%.6f", m }
  ')"

  local black_count
  black_count="$(printf '%s\n' "$log" | awk '/black_start:/ {c++} END {print c+0}')"

  if [[ "$SHOW_DETAILS" -eq 1 ]]; then
    printf '%s\n' "$log" | awk '/black_start:/ { print "  blackdetect> " $0 }'
  fi

  echo "$black_count|$max_black"
}

run_silencedetect() {
  local file="$1"
  local log
  log="$($FFMPEG_BIN -hide_banner -v info -i "$file" -af "silencedetect=n=${SILENCE_DETECT_NOISE}:d=${SILENCE_DETECT_DURATION}" -vn -f null - 2>&1 || true)"

  local max_silence
  max_silence="$(printf '%s\n' "$log" | awk '
    BEGIN { m=0 }
    /silence_duration:/ {
      for (i=1; i<=NF; i++) {
        if ($i ~ /^silence_duration:/) {
          sub("silence_duration:","",$i)
          v=$i+0
          if (v>m) m=v
        }
      }
    }
    END { printf "%.6f", m }
  ')"

  local silence_count
  silence_count="$(printf '%s\n' "$log" | awk '/silence_start:/ {c++} END {print c+0}')"

  if [[ "$SHOW_DETAILS" -eq 1 ]]; then
    printf '%s\n' "$log" | awk '/silence_start:|silence_end:/ { print "  silencedetect> " $0 }'
  fi

  echo "$silence_count|$max_silence"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --expect-width)
      EXPECT_WIDTH="$2"; shift 2 ;;
    --expect-height)
      EXPECT_HEIGHT="$2"; shift 2 ;;
    --expect-fps)
      EXPECT_FPS="$2"; shift 2 ;;
    --expect-video-codec)
      EXPECT_VIDEO_CODEC="$2"; shift 2 ;;
    --expect-pix-fmt)
      EXPECT_PIX_FMT="$2"; shift 2 ;;
    --expect-audio)
      EXPECT_AUDIO="$2"; shift 2 ;;
    --max-black-duration)
      MAX_BLACK_DURATION="$2"; shift 2 ;;
    --max-silence-duration)
      MAX_SILENCE_DURATION="$2"; shift 2 ;;
    --black-detect-duration)
      BLACK_DETECT_DURATION="$2"; shift 2 ;;
    --black-detect-pix-th)
      BLACK_DETECT_PIX_TH="$2"; shift 2 ;;
    --black-detect-pic-th)
      BLACK_DETECT_PIC_TH="$2"; shift 2 ;;
    --silence-detect-duration)
      SILENCE_DETECT_DURATION="$2"; shift 2 ;;
    --silence-detect-noise)
      SILENCE_DETECT_NOISE="$2"; shift 2 ;;
    --details)
      SHOW_DETAILS=1; shift ;;
    -h|--help)
      usage
      exit 0 ;;
    --)
      shift
      break ;;
    -* )
      echo "Unknown option: $1" >&2
      usage
      exit 2 ;;
    *)
      break ;;
  esac
done

if [[ "$EXPECT_AUDIO" != "any" && "$EXPECT_AUDIO" != "present" && "$EXPECT_AUDIO" != "absent" ]]; then
  echo "Invalid --expect-audio value: $EXPECT_AUDIO" >&2
  exit 2
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

require_bins

overall_fail=0
overall_warn=0

for file in "$@"; do
  echo "=== QC: $file ==="

  if [[ ! -f "$file" ]]; then
    echo "RESULT: FAIL"
    echo "- Missing file"
    overall_fail=1
    echo
    continue
  fi

  meta="$($FFPROBE_BIN -v error -show_entries \
    stream=codec_name,profile,width,height,pix_fmt,avg_frame_rate,bit_rate \
    -show_entries format=duration,bit_rate,format_name \
    -of default=nw=1:nk=0 "$file" || true)"

  width="$(printf '%s\n' "$meta" | awk -F= '/^width=/{print $2; exit}')"
  height="$(printf '%s\n' "$meta" | awk -F= '/^height=/{print $2; exit}')"
  codec="$(printf '%s\n' "$meta" | awk -F= '/^codec_name=/{print $2; exit}')"
  profile="$(printf '%s\n' "$meta" | awk -F= '/^profile=/{print $2; exit}')"
  pix_fmt="$(printf '%s\n' "$meta" | awk -F= '/^pix_fmt=/{print $2; exit}')"
  fps_raw="$(printf '%s\n' "$meta" | awk -F= '/^avg_frame_rate=/{print $2; exit}')"
  fps="$(float_from_fraction "${fps_raw:-0/1}")"
  duration="$(printf '%s\n' "$meta" | awk -F= '/^duration=/{print $2; exit}')"
  format_name="$(printf '%s\n' "$meta" | awk -F= '/^format_name=/{print $2; exit}')"
  bitrate="$(printf '%s\n' "$meta" | awk -F= '/^bit_rate=/{print $2; exit}')"

  audio_tracks="$($FFPROBE_BIN -v error -select_streams a -show_entries stream=index -of csv=p=0 "$file" | wc -l | tr -d ' ')"

  echo "- format: ${format_name:-unknown}"
  echo "- video: ${codec:-unknown} (${profile:-unknown}), ${width:-?}x${height:-?}, pix_fmt=${pix_fmt:-unknown}, fps=${fps}, bitrate=${bitrate:-unknown}"
  echo "- duration: ${duration:-unknown}"
  echo "- audio tracks: ${audio_tracks}"

  fails=()
  warns=()

  if [[ -n "$EXPECT_WIDTH" && "${width:-}" != "$EXPECT_WIDTH" ]]; then
    fails+=("Expected width ${EXPECT_WIDTH}, got ${width:-unknown}")
  fi
  if [[ -n "$EXPECT_HEIGHT" && "${height:-}" != "$EXPECT_HEIGHT" ]]; then
    fails+=("Expected height ${EXPECT_HEIGHT}, got ${height:-unknown}")
  fi
  if [[ -n "$EXPECT_VIDEO_CODEC" && "${codec:-}" != "$EXPECT_VIDEO_CODEC" ]]; then
    fails+=("Expected codec ${EXPECT_VIDEO_CODEC}, got ${codec:-unknown}")
  fi
  if [[ -n "$EXPECT_PIX_FMT" && "${pix_fmt:-}" != "$EXPECT_PIX_FMT" ]]; then
    fails+=("Expected pix_fmt ${EXPECT_PIX_FMT}, got ${pix_fmt:-unknown}")
  fi

  if [[ -n "$EXPECT_FPS" ]]; then
    fps_diff="$(abs_diff "$fps" "$EXPECT_FPS")"
    if float_gt "$fps_diff" "0.020"; then
      fails+=("Expected fps ${EXPECT_FPS}, got ${fps}")
    fi
  fi

  if [[ "$EXPECT_AUDIO" == "present" && "$audio_tracks" -eq 0 ]]; then
    fails+=("Expected audio track(s), found none")
  fi
  if [[ "$EXPECT_AUDIO" == "absent" && "$audio_tracks" -gt 0 ]]; then
    fails+=("Expected no audio tracks, found ${audio_tracks}")
  fi

  black_info="$(run_blackdetect "$file")"
  black_count="${black_info%%|*}"
  max_black="${black_info##*|}"
  echo "- black segments: ${black_count}, max_black_duration=${max_black}s"
  if [[ -n "$MAX_BLACK_DURATION" ]] && float_gt "$max_black" "$MAX_BLACK_DURATION"; then
    fails+=("Max black duration ${max_black}s exceeds limit ${MAX_BLACK_DURATION}s")
  elif [[ "$black_count" -gt 0 ]]; then
    warns+=("Detected ${black_count} black segment(s); max ${max_black}s")
  fi

  if [[ "$audio_tracks" -gt 0 ]]; then
    silence_info="$(run_silencedetect "$file")"
    silence_count="${silence_info%%|*}"
    max_silence="${silence_info##*|}"
    echo "- silence segments: ${silence_count}, max_silence_duration=${max_silence}s"
    if [[ -n "$MAX_SILENCE_DURATION" ]] && float_gt "$max_silence" "$MAX_SILENCE_DURATION"; then
      fails+=("Max silence duration ${max_silence}s exceeds limit ${MAX_SILENCE_DURATION}s")
    elif [[ "$silence_count" -gt 0 ]]; then
      warns+=("Detected ${silence_count} silence segment(s); max ${max_silence}s")
    fi
  else
    echo "- silence segments: skipped (no audio)"
  fi

  if [[ ${#fails[@]} -gt 0 ]]; then
    echo "RESULT: FAIL"
    for msg in "${fails[@]}"; do
      echo "- $msg"
    done
    overall_fail=1
  elif [[ ${#warns[@]} -gt 0 ]]; then
    echo "RESULT: WARN"
    for msg in "${warns[@]}"; do
      echo "- $msg"
    done
    overall_warn=1
  else
    echo "RESULT: PASS"
  fi

  echo
done

if [[ "$overall_fail" -eq 1 ]]; then
  echo "SUMMARY: FAIL"
  exit 1
fi

if [[ "$overall_warn" -eq 1 ]]; then
  echo "SUMMARY: WARN"
  exit 0
fi

echo "SUMMARY: PASS"
exit 0
