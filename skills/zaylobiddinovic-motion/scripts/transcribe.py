#!/usr/bin/env python3
"""Transcribe speech to word-level captions for Remotion (@remotion/captions `Caption[]`) and optional SRT.

Runs locally. Engines (install one; ask the user first):
  faster-whisper   pip install faster-whisper     (default when installed)
  openai-whisper   pip install openai-whisper

Usage:
  python3 transcribe.py MEDIA --out public/captions.json [--srt out.srt] [--model small] [--language en]
  python3 transcribe.py --from-json whisper_output.json --out public/captions.json   # convert existing Whisper JSON

The model is downloaded by the engine on first use; mention the size to the user before running.
"""
import argparse
import importlib.util
import json
import sys


def words_from_whisper_json(data):
    """Accept openai-whisper / faster-whisper style dicts: {segments: [{words: [{word,start,end,probability}]}]}."""
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words") or []:
            words.append((w.get("word", ""), float(w["start"]), float(w["end"]), float(w.get("probability", 1.0))))
    if not words:
        raise SystemExit("No word timestamps found. Re-run Whisper with word timestamps enabled.")
    return words


def run_faster_whisper(media, model_name, language):
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segments, info = model.transcribe(media, language=language, word_timestamps=True, vad_filter=True)
    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append((w.word, float(w.start), float(w.end), float(w.probability)))
    print(f"Detected language: {info.language}", file=sys.stderr)
    return words


def run_openai_whisper(media, model_name, language):
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(media, language=language, word_timestamps=True)
    return words_from_whisper_json(result)


def to_captions(words):
    captions = []
    for i, (text, start, end, prob) in enumerate(words):
        if not text.strip():
            continue
        # @remotion/captions expects a leading space on every token except the first; Whisper already does this.
        token = text if captions else text.lstrip()
        if captions and not token.startswith(" "):
            token = " " + token
        start_ms, end_ms = round(start * 1000), round(max(end, start + 0.05) * 1000)
        captions.append({"text": token, "startMs": start_ms, "endMs": end_ms,
                         "timestampMs": (start_ms + end_ms) // 2, "confidence": round(prob, 3)})
    return captions


def srt_time(ms):
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def to_srt(captions, max_words=7, max_gap_ms=700):
    lines, group = [], []
    for c in captions:
        if group and (len(group) >= max_words or c["startMs"] - group[-1]["endMs"] > max_gap_ms):
            lines.append(group)
            group = []
        group.append(c)
    if group:
        lines.append(group)
    out = []
    for i, g in enumerate(lines, 1):
        text = "".join(c["text"] for c in g).strip()
        out.append(f"{i}\n{srt_time(g[0]['startMs'])} --> {srt_time(g[-1]['endMs'])}\n{text}\n")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("media", nargs="?")
    p.add_argument("--out", required=True, help="captions JSON path, usually <project>/public/captions.json")
    p.add_argument("--srt", help="also write an SRT file")
    p.add_argument("--from-json", help="convert an existing Whisper JSON instead of transcribing")
    p.add_argument("--engine", choices=["auto", "faster-whisper", "openai-whisper"], default="auto")
    p.add_argument("--model", default="small", help="tiny|base|small|medium|large-v3 (bigger = slower, better)")
    p.add_argument("--language", default=None, help="ISO code such as en, uz, ru; omit to auto-detect")
    a = p.parse_args()

    if a.from_json:
        with open(a.from_json, encoding="utf-8") as f:
            words = words_from_whisper_json(json.load(f))
    else:
        if not a.media:
            p.error("give a media file or --from-json")
        engine = a.engine
        if engine == "auto":
            engine = next((e for e, m in [("faster-whisper", "faster_whisper"), ("openai-whisper", "whisper")]
                           if importlib.util.find_spec(m)), None)
            if engine is None:
                raise SystemExit("No transcription engine installed. Ask the user, then: pip install faster-whisper")
        runner = run_faster_whisper if engine == "faster-whisper" else run_openai_whisper
        words = runner(a.media, a.model, a.language)

    captions = to_captions(words)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(captions, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(captions)} words to {a.out}")
    if a.srt:
        with open(a.srt, "w", encoding="utf-8") as f:
            f.write(to_srt(captions))
        print(f"Wrote {a.srt}")
    low = [c for c in captions if c["confidence"] < 0.5]
    if low:
        print(f"{len(low)} low-confidence words; review: " + ", ".join(c["text"].strip() for c in low[:15]))


if __name__ == "__main__":
    main()
