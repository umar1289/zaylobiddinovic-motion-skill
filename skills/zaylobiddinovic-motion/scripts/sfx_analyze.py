#!/usr/bin/env python3
"""Measure sound effects for placement: where the sound starts, where it peaks, where it dies away.

Analyze:   python3 sfx_analyze.py FILE [FILE ...] [--json]
Trim:      python3 sfx_analyze.py FILE --trim OUT.wav [--tail-db -45] [--max-length 1.5]
Spectrum:  python3 sfx_analyze.py FILE --spectrogram OUT.png      (visual check, needs ffmpeg)

Why it matters: a whoosh swells to its middle, an impact hits at once. To make the audible hit land on a
visual event at time T, start the file at T - hit_ms. `sfx_cues.py` does this automatically (align "hit").
  hit_ms   first moment within 3 dB of the loudest point (what the ear hears as "the hit")
  peak_ms  centre of the single loudest 5 ms window
  onset_ms first moment within 30 dB of the loudest point
Any format FFmpeg reads is accepted. Times are in milliseconds.
"""
import argparse
import json
import math
import os
import subprocess
import sys
from array import array

SR = 48000
WIN = 240  # 5 ms analysis windows


def decode(path):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise SystemExit(f"Could not decode {path}: {res.stderr.decode(errors='replace').strip()}")
    a = array("f")
    a.frombytes(res.stdout)
    if sys.byteorder == "big":
        a.byteswap()
    return a


def db(x):
    return 20 * math.log10(x) if x > 1e-9 else -180.0


def analyze(path, tail_db=-45.0, onset_db=-30.0):
    s = decode(path)
    if not s:
        raise SystemExit(f"{path}: no audio")
    rms = []
    for i in range(0, len(s), WIN):
        w = s[i:i + WIN]
        rms.append(math.sqrt(sum(v * v for v in w) / len(w)))
    peak_sample = max(range(len(s)), key=lambda i: abs(s[i]))
    peak = abs(s[peak_sample])
    loudest_win = max(range(len(rms)), key=lambda i: rms[i])
    ref = rms[loudest_win] or 1e-9
    onset_win = next((i for i, r in enumerate(rms) if db(r / ref) > onset_db), 0)
    # First window within 3 dB of the loudest: where a listener hears the hit. Percussive sounds reach it
    # immediately; swells (whoosh, riser) reach it near their peak.
    hit_win = next((i for i, r in enumerate(rms) if db(r / ref) > -3.0), loudest_win)
    silent_win = next((i for i, r in enumerate(rms) if db(r / ref) > -60.0), 0)
    tail_win = max((i for i, r in enumerate(rms) if db(r / ref) > tail_db), default=len(rms) - 1)
    total_rms = math.sqrt(sum(v * v for v in s) / len(s))
    ms = lambda win: round(win * WIN / SR * 1000, 1)
    return {
        "file": path,
        "duration_ms": round(len(s) / SR * 1000, 1),
        "peak_dbfs": round(db(peak), 1),
        "rms_dbfs": round(db(total_rms), 1),
        "crest_db": round(db(peak) - db(total_rms), 1),
        "onset_ms": ms(onset_win),
        "hit_ms": ms(hit_win),
        "peak_ms": round(ms(loudest_win) + WIN / SR * 500, 1),
        "tail_end_ms": ms(tail_win + 1),
        "lead_silence_ms": ms(silent_win),
        "trailing_ms": round(len(s) / SR * 1000 - ms(tail_win + 1), 1),
        "character": "transient" if ms(hit_win) - ms(onset_win) < 25 else "swell",
    }


def trim(path, out, tail_db, max_length):
    info = analyze(path, tail_db=tail_db)
    if os.path.abspath(path) == os.path.abspath(out):
        raise SystemExit("Refusing to overwrite the input; choose a new output name.")
    start = max(0.0, info["onset_ms"] - 3) / 1000
    end = info["tail_end_ms"] / 1000
    if max_length:
        end = min(end, start + max_length)
    dur = max(0.01, end - start)
    fade = min(0.03, dur / 4)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", path, "-ss", f"{start:.4f}", "-t", f"{dur:.4f}",
           "-af", f"afade=t=in:d=0.001,afade=t=out:st={max(0, dur - fade):.4f}:d={fade:.4f}",
           "-ar", str(SR), "-c:a", "pcm_s24le", out]
    subprocess.run(cmd, check=True)
    print(f"Trimmed {path}: {info['duration_ms']} ms -> {round(dur * 1000, 1)} ms ({out})")


def spectrogram(path, out):
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", path, "-lavfi",
           "showspectrumpic=s=800x300:legend=1:scale=log:fscale=log", out]
    subprocess.run(cmd, check=True)
    print(f"Wrote {out}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+")
    p.add_argument("--json", action="store_true")
    p.add_argument("--trim", metavar="OUT")
    p.add_argument("--tail-db", type=float, default=-45.0, help="tail ends when level falls this far below the loudest point")
    p.add_argument("--max-length", type=float, default=None, help="seconds; cap when trimming")
    p.add_argument("--spectrogram", metavar="OUT.png")
    a = p.parse_args()

    if a.trim or a.spectrogram:
        if len(a.files) != 1:
            p.error("--trim/--spectrogram take exactly one input file")
        if a.trim:
            trim(a.files[0], a.trim, a.tail_db, a.max_length)
        if a.spectrogram:
            spectrogram(a.files[0], a.spectrogram)
        return

    results = [analyze(f, tail_db=a.tail_db) for f in a.files]
    if a.json:
        print(json.dumps(results, indent=2))
        return
    print(f"{'file':<28} {'dur':>7} {'onset':>6} {'hit@':>7} {'tail':>7} {'peak':>6} {'rms':>6}  kind")
    for r in results:
        print(f"{os.path.basename(r['file'])[:28]:<28} {r['duration_ms']:>7} {r['onset_ms']:>6} {r['hit_ms']:>7} "
              f"{r['tail_end_ms']:>7} {r['peak_dbfs']:>6} {r['rms_dbfs']:>6}  {r['character']}")
        if r["lead_silence_ms"] > 20:
            print(f"   ^ {r['lead_silence_ms']} ms of silence before the sound starts; consider --trim")
        if r["trailing_ms"] > 300:
            print(f"   ^ {r['trailing_ms']} ms of near-silent tail; consider --trim")


if __name__ == "__main__":
    main()
