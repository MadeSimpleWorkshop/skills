#!/usr/bin/env python3
"""Generate layered sine-tone audio from a list of frequencies."""

from __future__ import annotations

import argparse
import math
import re
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path


TWO_PI = 2.0 * math.pi


@dataclass(frozen=True)
class Tone:
    frequency_hz: float
    weight: float = 1.0


def parse_duration(raw: str) -> float:
    value = raw.strip().lower()
    if not value:
        raise argparse.ArgumentTypeError("Duration cannot be empty")

    if ":" in value:
        parts = value.split(":")
        try:
            numbers = [float(part) for part in parts]
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid duration '{raw}'. Use seconds, 1m, or hh:mm:ss."
            ) from exc
        if len(numbers) == 2:
            minutes, seconds = numbers
            total = (minutes * 60.0) + seconds
        elif len(numbers) == 3:
            hours, minutes, seconds = numbers
            total = (hours * 3600.0) + (minutes * 60.0) + seconds
        else:
            raise argparse.ArgumentTypeError(
                f"Invalid duration '{raw}'. Use mm:ss or hh:mm:ss."
            )
        if total <= 0:
            raise argparse.ArgumentTypeError("Duration must be > 0")
        return total

    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        total = float(value)
        if total <= 0:
            raise argparse.ArgumentTypeError("Duration must be > 0")
        return total

    match = re.fullmatch(r"(\d+(?:\.\d+)?)(ms|s|m|h)", value)
    if not match:
        raise argparse.ArgumentTypeError(
            f"Invalid duration '{raw}'. Use examples like 60, 1m, 90s, 00:01:00."
        )

    amount = float(match.group(1))
    unit = match.group(2)
    if unit == "ms":
        total = amount / 1000.0
    elif unit == "s":
        total = amount
    elif unit == "m":
        total = amount * 60.0
    else:
        total = amount * 3600.0

    if total <= 0:
        raise argparse.ArgumentTypeError("Duration must be > 0")
    return total


def parse_frequency_list(raw: str) -> list[Tone]:
    normalized = raw.replace(",", " ")
    tokens = [token.strip() for token in normalized.split() if token.strip()]
    if not tokens:
        raise argparse.ArgumentTypeError("Provide at least one frequency")

    tones: list[Tone] = []
    for token in tokens:
        freq_text, weight_text = (token.split("@", 1) + ["1"])[:2]
        freq_text = freq_text.lower().removesuffix("hz")
        try:
            frequency_hz = float(freq_text)
            weight = float(weight_text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid frequency token '{token}'. Use '528' or '528@0.5'."
            ) from exc

        if frequency_hz <= 0:
            raise argparse.ArgumentTypeError(
                f"Frequency must be > 0 Hz (got {frequency_hz})"
            )
        if weight <= 0:
            raise argparse.ArgumentTypeError(
                f"Weight must be > 0 (got {weight})"
            )
        tones.append(Tone(frequency_hz=frequency_hz, weight=weight))

    return tones


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an exact-length WAV file by layering sine tones "
            "from a list of frequencies."
        )
    )
    parser.add_argument(
        "frequencies",
        type=parse_frequency_list,
        help=(
            "Comma/space-separated frequencies in Hz. "
            "Optional per-tone weights via @, e.g. '396,417,528@0.5'."
        ),
    )
    parser.add_argument(
        "--duration",
        required=True,
        type=parse_duration,
        help="Target duration (examples: 60, 1m, 90s, 00:01:00)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output WAV path",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=48000,
        help="Sample rate in Hz (default: 48000)",
    )
    parser.add_argument(
        "--channels",
        type=int,
        choices=(1, 2),
        default=2,
        help="Channel count (1=mono, 2=stereo; default: 2)",
    )
    parser.add_argument(
        "--peak",
        type=float,
        default=0.9,
        help=(
            "Max peak target before int16 conversion (0-1). "
            "Script auto-scales to avoid clipping. Default: 0.9"
        ),
    )
    parser.add_argument(
        "--fade-in-ms",
        type=float,
        default=10.0,
        help="Fade-in length in milliseconds (default: 10)",
    )
    parser.add_argument(
        "--fade-out-ms",
        type=float,
        default=250.0,
        help="Fade-out length in milliseconds (default: 250)",
    )
    parser.add_argument(
        "--chunk-samples",
        type=int,
        default=4096,
        help=argparse.SUPPRESS,
    )
    return parser


def frame_envelope(
    frame_index: int,
    total_frames: int,
    fade_in_frames: int,
    fade_out_frames: int,
) -> float:
    gain = 1.0
    if fade_in_frames > 0 and frame_index < fade_in_frames:
        gain *= frame_index / fade_in_frames

    if fade_out_frames > 0:
        frames_remaining = total_frames - 1 - frame_index
        if frames_remaining < fade_out_frames:
            gain *= max(frames_remaining, 0) / fade_out_frames

    return gain


def generate_audio(
    tones: list[Tone],
    duration_seconds: float,
    sample_rate: int,
    channels: int,
    peak: float,
    fade_in_ms: float,
    fade_out_ms: float,
    chunk_samples: int,
    output_path: Path,
) -> tuple[int, float]:
    if sample_rate <= 0:
        raise ValueError("sample_rate must be > 0")
    if chunk_samples <= 0:
        raise ValueError("chunk_samples must be > 0")
    if not (0 < peak <= 1.0):
        raise ValueError("--peak must be in the range (0, 1]")
    if fade_in_ms < 0 or fade_out_ms < 0:
        raise ValueError("Fade durations must be >= 0")

    total_frames = max(1, int(round(duration_seconds * sample_rate)))
    actual_duration = total_frames / sample_rate
    fade_in_frames = min(int(round((fade_in_ms / 1000.0) * sample_rate)), total_frames)
    fade_out_frames = min(int(round((fade_out_ms / 1000.0) * sample_rate)), total_frames)

    total_weight = sum(tone.weight for tone in tones)
    amplitudes = [(tone.weight / total_weight) * peak for tone in tones]
    phase_steps = [TWO_PI * tone.frequency_hz / sample_rate for tone in tones]
    phases = [0.0 for _ in tones]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # int16 PCM
        wf.setframerate(sample_rate)

        frame_start = 0
        while frame_start < total_frames:
            frame_end = min(frame_start + chunk_samples, total_frames)
            pcm = array("h")

            for frame_index in range(frame_start, frame_end):
                mixed = 0.0
                for idx, phase in enumerate(phases):
                    mixed += math.sin(phase) * amplitudes[idx]
                    next_phase = phase + phase_steps[idx]
                    if next_phase >= TWO_PI:
                        next_phase %= TWO_PI
                    phases[idx] = next_phase

                mixed *= frame_envelope(
                    frame_index=frame_index,
                    total_frames=total_frames,
                    fade_in_frames=fade_in_frames,
                    fade_out_frames=fade_out_frames,
                )

                sample = int(max(-32768, min(32767, round(mixed * 32767.0))))
                if channels == 1:
                    pcm.append(sample)
                else:
                    pcm.append(sample)
                    pcm.append(sample)

            wf.writeframes(pcm.tobytes())
            frame_start = frame_end

    return total_frames, actual_duration


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()
    tones: list[Tone] = args.frequencies

    try:
        frames, actual_duration = generate_audio(
            tones=tones,
            duration_seconds=args.duration,
            sample_rate=args.sample_rate,
            channels=args.channels,
            peak=args.peak,
            fade_in_ms=args.fade_in_ms,
            fade_out_ms=args.fade_out_ms,
            chunk_samples=args.chunk_samples,
            output_path=output_path,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    tone_summary = ", ".join(
        f"{tone.frequency_hz:g}Hz@{tone.weight:g}" for tone in tones
    )
    print(f"Wrote: {output_path}")
    print(f"Frequencies: {tone_summary}")
    print(
        "Audio: "
        f"{args.channels}ch, {args.sample_rate}Hz, 16-bit PCM WAV, "
        f"{frames} frames ({actual_duration:.6f}s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
