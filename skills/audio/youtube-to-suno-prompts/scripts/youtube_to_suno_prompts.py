#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_LEXICON_PATH = SKILL_DIR / "references" / "keyword_lexicon.json"


def _eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def _run(cmd: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        capture_output=capture,
        text=True,
    )


def _require_tool(name: str) -> str | None:
    path = shutil.which(name)
    if path:
        return path

    # Homebrew "keg-only" formula: ffmpeg-full.
    if name in {"ffmpeg", "ffprobe"}:
        alt = Path("/opt/homebrew/opt/ffmpeg-full/bin") / name
        if alt.exists():
            return str(alt)
    return None


def _has_py_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _yt_dlp_cmd() -> list[str] | None:
    # Prefer the binary if available; otherwise fall back to the Python module
    # (useful when installed via `pip3 install --user yt-dlp` and PATH isn't updated).
    if _require_tool("yt-dlp"):
        return ["yt-dlp"]
    if _has_py_module("yt_dlp"):
        return [sys.executable, "-m", "yt_dlp"]
    return None


def _safe_slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "run"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _load_lexicon(path: Path) -> dict[str, dict[str, list[str]]]:
    if not path.exists():
        return {"genres": {}, "moods": {}, "instruments": {}, "vocal_styles": {}, "production": {}}
    data = _load_json(path)
    # Basic shape validation (keep forgiving; users may edit this file).
    out: dict[str, dict[str, list[str]]] = {}
    for section in ("genres", "moods", "instruments", "vocal_styles", "production"):
        sec = data.get(section, {})
        if not isinstance(sec, dict):
            sec = {}
        cleaned: dict[str, list[str]] = {}
        for k, v in sec.items():
            if not isinstance(k, str):
                continue
            if isinstance(v, list):
                cleaned[k] = [str(x) for x in v if str(x).strip()]
            else:
                cleaned[k] = [str(v)]
        out[section] = cleaned
    return out  # type: ignore[return-value]


def _contains_pattern(text: str, pattern: str) -> bool:
    p = pattern.strip().lower()
    if not p:
        return False
    # For single token patterns, use word boundaries to avoid substring false-positives.
    if re.fullmatch(r"[a-z0-9]+", p):
        return re.search(rf"\b{re.escape(p)}\b", text) is not None
    return p in text


def _detect_from_text(text: str, lexicon: dict[str, dict[str, list[str]]]) -> dict[str, list[str]]:
    t = text.lower()
    detected: dict[str, list[str]] = {}
    for section, mapping in lexicon.items():
        hits: list[str] = []
        for canonical, patterns in mapping.items():
            for pat in patterns:
                if _contains_pattern(t, pat):
                    hits.append(canonical)
                    break
        # Preserve order but de-dupe.
        seen: set[str] = set()
        hits_deduped: list[str] = []
        for h in hits:
            if h not in seen:
                hits_deduped.append(h)
                seen.add(h)
        detected[section] = hits_deduped
    return detected


def _yt_dlp_metadata(url: str) -> dict[str, Any] | None:
    cmd = _yt_dlp_cmd()
    if not cmd:
        return None
    res = _run([*cmd, "-J", "--no-playlist", "--no-warnings", "--skip-download", url], capture=True)
    if res.returncode != 0:
        _eprint("yt-dlp metadata fetch failed:", (res.stderr or "").strip())
        return None
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        _eprint("yt-dlp returned non-JSON output; continuing without metadata.")
        return None


def _yt_dlp_download_audio(url: str, out_template: str) -> bool:
    cmd = _yt_dlp_cmd()
    if not cmd:
        return False
    res = _run(
        [*cmd, "-f", "bestaudio", "--no-playlist", "--no-warnings", "-o", out_template, url],
        capture=False,
    )
    return res.returncode == 0


def _find_downloaded_source(run_dir: Path) -> Path | None:
    # yt-dlp might emit .part and other helper files; prefer a real media file.
    candidates = sorted(run_dir.glob("source.*"))
    for p in candidates:
        if p.suffix in {".part", ".json", ".tmp"}:
            continue
        if p.is_file():
            return p
    # Fallback: any audio-like file in the run dir.
    for p in sorted(run_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() in {".m4a", ".mp3", ".wav", ".flac", ".opus", ".ogg", ".webm"}:
            return p
    return None


def _ffmpeg_convert_to_wav(src: Path, dst: Path) -> bool:
    ffmpeg = _require_tool("ffmpeg")
    if not ffmpeg:
        return False
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "44100",
        "-c:a",
        "pcm_s16le",
        "-af",
        "loudnorm=I=-16:LRA=11:TP=-1.5",
        str(dst),
    ]
    res = _run(cmd, capture=True)
    if res.returncode != 0:
        _eprint("ffmpeg convert failed; continuing without WAV:", (res.stderr or "").strip())
        return False
    return True


def _ffprobe_duration_seconds(path: Path) -> float | None:
    ffprobe = _require_tool("ffprobe")
    if not ffprobe:
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    res = _run(cmd, capture=True)
    if res.returncode != 0:
        return None
    try:
        return float(res.stdout.strip())
    except ValueError:
        return None


def _segment_starts(duration_s: float, segment_s: int) -> list[float]:
    if duration_s <= segment_s + 5:
        return [0.0]
    starts: list[float] = []
    if duration_s <= 90:
        starts = [0.0, max(0.0, (duration_s / 2.0) - (segment_s / 2.0))]
    else:
        starts = [
            0.0,
            max(0.0, (duration_s / 3.0) - (segment_s / 2.0)),
            max(0.0, (2.0 * duration_s / 3.0) - (segment_s / 2.0)),
        ]
    # Clamp and de-dupe.
    max_start = max(0.0, duration_s - segment_s)
    out: list[float] = []
    for s in starts:
        s = min(max(0.0, s), max_start)
        s = round(s, 3)
        if s not in out:
            out.append(s)
    return out


def _ffmpeg_extract_segment(src_wav: Path, dst_wav: Path, start_s: float, segment_s: int) -> bool:
    ffmpeg = _require_tool("ffmpeg")
    if not ffmpeg:
        return False
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        str(start_s),
        "-t",
        str(segment_s),
        "-i",
        str(src_wav),
        "-c:a",
        "pcm_s16le",
        str(dst_wav),
    ]
    res = _run(cmd, capture=True)
    if res.returncode != 0:
        _eprint("ffmpeg segment extract failed:", (res.stderr or "").strip())
        return False
    return True


def _try_librosa_features(wav_path: Path) -> dict[str, Any]:
    try:
        import librosa  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return {"available": False, "reason": "librosa not installed"}

    try:
        y, sr = librosa.load(str(wav_path), sr=22050, mono=True, duration=120.0)
        if y.size == 0:
            return {"available": False, "reason": "empty audio"}

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo) if tempo and float(tempo) > 0 else None

        # Rough energy.
        rms = float(np.sqrt(np.mean(y**2)))
        rms_db = float(20.0 * np.log10(max(rms, 1e-9)))

        # Rough key estimation via chroma correlation.
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        chroma_norm = chroma_mean / (np.linalg.norm(chroma_mean) + 1e-9)

        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

        def best_key(profile: "np.ndarray[Any, Any]") -> tuple[int, float]:
            best_i = 0
            best_score = -1e9
            p = profile / (np.linalg.norm(profile) + 1e-9)
            for i in range(12):
                score = float(np.dot(chroma_norm, np.roll(p, i)))
                if score > best_score:
                    best_score = score
                    best_i = i
            return best_i, best_score

        maj_i, maj_score = best_key(major_profile)
        min_i, min_score = best_key(minor_profile)

        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        if maj_score >= min_score:
            key = f"{note_names[maj_i]} major"
            key_score = maj_score
        else:
            key = f"{note_names[min_i]} minor"
            key_score = min_score

        return {
            "available": True,
            "bpm_estimate": round(bpm, 1) if bpm is not None else None,
            "key_estimate": key,
            "key_confidence": round(float(key_score), 4),
            "rms_db_estimate": round(rms_db, 2),
            "analysis_seconds": 120.0,
        }
    except Exception as e:
        return {"available": False, "reason": f"librosa error: {e}"}


def _tempo_descriptor(bpm: float | None) -> str:
    if bpm is None:
        return "mid-tempo"
    b = float(bpm)
    if b < 70:
        return f"slow (~{b:.0f} BPM)"
    if b < 95:
        return f"laid-back (~{b:.0f} BPM)"
    if b < 120:
        return f"mid-tempo (~{b:.0f} BPM)"
    if b < 150:
        return f"up-tempo (~{b:.0f} BPM)"
    return f"fast (~{b:.0f} BPM)"


def _pick(n: int, items: list[str]) -> list[str]:
    return [x for x in items[:n] if x]


def _join_phrases(items: list[str], *, fallback: str) -> str:
    items = [x.strip() for x in items if x.strip()]
    if not items:
        return fallback
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _generate_prompts(
    *,
    seed: int,
    count: int,
    genres: list[str],
    moods: list[str],
    instruments: list[str],
    vocal_styles: list[str],
    production: list[str],
    bpm: float | None,
    key: str | None,
    hint: str | None,
) -> list[str]:
    rnd = random.Random(seed)

    genre_phrase = _join_phrases(_pick(2, genres), fallback="modern genre-blend")
    mood_phrase = _join_phrases(_pick(3, moods), fallback="atmospheric")
    instr_phrase = _join_phrases(_pick(4, instruments), fallback="lush synths, tasteful bass, and tight drums")
    prod_phrase = _join_phrases(_pick(3, production), fallback="modern polished mix, warm saturation, spacious reverb")

    tempo_phrase = _tempo_descriptor(bpm)
    key_phrase = f"in {key}" if key else "in a minor-leaning vibe"

    # If we can't reliably detect vocals, emit both instrumental and light-vocal variants.
    vocal_pool = vocal_styles[:] if vocal_styles else []
    if not vocal_pool:
        vocal_pool = ["instrumental", "with airy vocals", "with vocal chops"]

    hint_phrase = (hint or "").strip()
    hint_extra = f" Extra hints: {hint_phrase}." if hint_phrase else ""

    templates = [
        "{genre}; {mood}; {tempo}; {instr}; {prod}; {voc}. {key}.{hint}",
        "A {mood} {genre} track that feels {key} and {tempo}. Feature {instr}. Keep {prod}. Vocals: {voc}.{hint}",
        "Style: {genre}. Mood: {mood}. Tempo: {tempo}. Instruments: {instr}. Production: {prod}. Vocals: {voc}. Key: {key}.{hint}",
        "{mood} {genre}, {tempo}, {instr}; {prod}. {voc}. {key}.{hint}",
        "Create an original {genre} song: {mood}, {tempo}, {instr}. Production: {prod}. {voc}. {key}.{hint}",
    ]

    prompts: list[str] = []
    for i in range(count):
        tpl = templates[i % len(templates)]
        voc = rnd.choice(vocal_pool)
        prompt = tpl.format(
            genre=genre_phrase,
            mood=mood_phrase,
            tempo=tempo_phrase,
            instr=instr_phrase,
            prod=prod_phrase,
            voc=voc,
            key=key_phrase,
            hint=hint_extra,
        )
        # Minor cleanup to keep copy/paste friendly.
        prompt = re.sub(r"\s{2,}", " ", prompt).strip()
        prompts.append(prompt)
    return prompts


def _summarize_profile(profile: dict[str, Any]) -> str:
    meta = profile.get("metadata", {}) or {}
    det = profile.get("detected", {}) or {}
    feats = profile.get("audio_features", {}) or {}

    lines: list[str] = []
    if meta.get("title"):
        lines.append(f"Title: {meta.get('title')}")
    if meta.get("url"):
        lines.append(f"URL: {meta.get('url')}")

    if det.get("genres"):
        lines.append(f"Genres: {', '.join(det.get('genres'))}")
    if det.get("moods"):
        lines.append(f"Moods: {', '.join(det.get('moods'))}")
    if det.get("instruments"):
        lines.append(f"Instruments: {', '.join(det.get('instruments'))}")
    if det.get("vocal_styles"):
        lines.append(f"Vocals: {', '.join(det.get('vocal_styles'))}")
    if det.get("production"):
        lines.append(f"Production: {', '.join(det.get('production'))}")

    bpm = feats.get("bpm_estimate")
    key = feats.get("key_estimate")
    if bpm is not None:
        lines.append(f"BPM (estimate): {bpm}")
    if key:
        lines.append(f"Key (estimate): {key}")

    notes = profile.get("notes") or []
    if notes:
        lines.append("Notes:")
        for n in notes:
            lines.append(f"- {n}")

    return "\n".join(lines).strip() + "\n"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download/analyze a reference track and generate Suno prompt variants.",
    )
    p.add_argument("source", nargs="?", help="YouTube URL or local audio path (optional if --url/--audio used)")
    p.add_argument("--url", help="YouTube URL (overrides positional source)")
    p.add_argument("--audio", help="Local audio file path (overrides positional source)")
    p.add_argument("--title", help="Title to use when analyzing local audio")
    p.add_argument("--hint", action="append", default=[], help="Extra hint text to guide keyword detection/prompting")
    p.add_argument("--count", type=int, default=10, help="Number of prompt variants to generate")
    p.add_argument("--segment-seconds", type=int, default=30, help="Segment length (seconds) for preview clips")
    p.add_argument("--outdir", default="./output/youtube-to-suno-prompts", help="Base output directory")
    p.add_argument("--lexicon", default=str(DEFAULT_LEXICON_PATH), help="Keyword lexicon JSON path")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    url = args.url
    audio = args.audio
    if not url and not audio and args.source:
        if re.match(r"^https?://", args.source):
            url = args.source
        else:
            audio = args.source
    if not url and not audio:
        _eprint("Error: provide a YouTube URL or a local audio file via positional arg, --url, or --audio.")
        return 2

    base_outdir = Path(args.outdir).expanduser()
    base_outdir.mkdir(parents=True, exist_ok=True)

    lexicon = _load_lexicon(Path(args.lexicon))

    notes: list[str] = []
    metadata: dict[str, Any] = {}
    downloaded_source: Path | None = None
    wav_path: Path | None = None

    run_tag = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    if url:
        info = _yt_dlp_metadata(url) or {}
        video_id = str(info.get("id") or _safe_slug(url))[:32]
        run_dir = base_outdir / f"{run_tag}-{video_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "title": info.get("title"),
            "uploader": info.get("uploader") or info.get("channel"),
            "duration": info.get("duration"),
            "webpage_url": info.get("webpage_url") or url,
            "tags": info.get("tags") or [],
        }
        metadata["url"] = metadata.get("webpage_url") or url

        if not _require_tool("yt-dlp"):
            notes.append("yt-dlp not found; skipped downloading and metadata enrichment.")
        else:
            ok = _yt_dlp_download_audio(url, str(run_dir / "source.%(ext)s"))
            if not ok:
                notes.append("yt-dlp download failed; generated prompts from text only.")
            else:
                downloaded_source = _find_downloaded_source(run_dir)
                if not downloaded_source:
                    notes.append("Download finished but no source file found; generated prompts from text only.")
    else:
        audio_path = Path(audio).expanduser().resolve()
        if not audio_path.exists():
            _eprint(f"Error: audio file not found: {audio_path}")
            return 2
        stem = _safe_slug(args.title or audio_path.stem)
        run_dir = base_outdir / f"{run_tag}-{stem}"
        run_dir.mkdir(parents=True, exist_ok=True)
        downloaded_source = audio_path
        metadata = {
            "title": args.title or audio_path.stem,
            "url": None,
        }

    # Build keyword text from metadata + hints.
    hint_text = " ".join([h.strip() for h in (args.hint or []) if h.strip()]).strip()
    text_bits: list[str] = []
    if metadata.get("title"):
        text_bits.append(str(metadata.get("title")))
    if metadata.get("tags"):
        text_bits.append(" ".join([str(t) for t in metadata.get("tags")]))
    if hint_text:
        text_bits.append(hint_text)
    keyword_text = "\n".join(text_bits).strip()

    detected = _detect_from_text(keyword_text, lexicon)

    # Convert to WAV and extract segments if we have a source and ffmpeg.
    if downloaded_source and _require_tool("ffmpeg"):
        wav_path = run_dir / "audio.wav"
        if not _ffmpeg_convert_to_wav(downloaded_source, wav_path):
            wav_path = None
            notes.append("ffmpeg WAV conversion failed; skipped audio feature extraction.")
        else:
            seg_dir = run_dir / "segments"
            seg_dir.mkdir(parents=True, exist_ok=True)
            dur = _ffprobe_duration_seconds(wav_path) or float(metadata.get("duration") or 0.0)
            if dur and dur > 0:
                for idx, start in enumerate(_segment_starts(dur, args.segment_seconds)):
                    seg_path = seg_dir / f"segment_{idx:02d}_{start:.3f}s.wav"
                    _ffmpeg_extract_segment(wav_path, seg_path, start, args.segment_seconds)
            else:
                notes.append("Could not determine duration; skipped segment extraction.")
    elif downloaded_source and not _require_tool("ffmpeg"):
        notes.append("ffmpeg not found; skipped WAV conversion and segment extraction.")

    audio_features: dict[str, Any] = {"available": False}
    if wav_path and wav_path.exists():
        audio_features = _try_librosa_features(wav_path)
        if not audio_features.get("available"):
            notes.append(str(audio_features.get("reason", "Audio analysis unavailable.")))

    bpm = audio_features.get("bpm_estimate") if audio_features.get("available") else None
    key = audio_features.get("key_estimate") if audio_features.get("available") else None

    seed_str = str(metadata.get("url") or downloaded_source or "") + "|" + (metadata.get("title") or "")
    # Use a stable hash (Python's built-in hash() is intentionally randomized between runs).
    seed = int.from_bytes(hashlib.sha256(seed_str.encode("utf-8")).digest()[:4], "big")
    prompts = _generate_prompts(
        seed=seed,
        count=max(1, int(args.count)),
        genres=detected.get("genres", []),
        moods=detected.get("moods", []),
        instruments=detected.get("instruments", []),
        vocal_styles=detected.get("vocal_styles", []),
        production=detected.get("production", []),
        bpm=bpm if isinstance(bpm, (int, float)) else None,
        key=key if isinstance(key, str) else None,
        hint=hint_text or None,
    )

    profile: dict[str, Any] = {
        "created_at": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
        "source": {
            "url": url,
            "audio": str(downloaded_source) if downloaded_source else None,
            "run_dir": str(run_dir),
        },
        "metadata": metadata,
        "detected": detected,
        "audio_features": audio_features,
        "notes": notes,
        "prompts": prompts,
    }

    _write_json(run_dir / "vibe_profile.json", profile)
    txt_lines = ["# Vibe profile", _summarize_profile(profile), "# Suno prompts"]
    for i, pr in enumerate(prompts, start=1):
        txt_lines.append(f"{i}. {pr}")
    txt_lines.append("")
    _write_text(run_dir / "suno_prompts.txt", "\n".join(txt_lines))

    print("\n".join(txt_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
