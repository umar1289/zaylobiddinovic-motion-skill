#!/usr/bin/env python3
"""Measure loudness (EBU R128) or normalize a file with two-pass loudnorm.

Measure:   python3 loudness.py measure FILE
Normalize: python3 loudness.py normalize IN OUT [--target -14] [--true-peak -1.0] [--lra 11]

Video streams are copied untouched when normalizing; only audio is re-encoded (AAC for mp4/mov, PCM for wav).
"""
import argparse
import json
import os
import re
import subprocess
import sys


def measure(path, target=-14.0, tp=-1.0, lra=11.0):
    flt = f"loudnorm=I={target}:TP={tp}:LRA={lra}:print_format=json"
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", flt, "-f", "null", "-"],
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"ffmpeg failed: {res.stderr.strip()[-500:]}")
    blocks = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.S)
    if not blocks:
        raise SystemExit("No loudness data found (does the file have an audio stream?)")
    return json.loads(blocks[-1])


def normalize(src, dst, target, tp, lra):
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit("Refusing to overwrite the input; choose a new output name.")
    m = measure(src, target, tp, lra)
    flt = (f"loudnorm=I={target}:TP={tp}:LRA={lra}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
           f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
           ":linear=true:print_format=summary")
    ext = os.path.splitext(dst)[1].lower()
    acodec = ["-c:a", "pcm_s24le"] if ext == ".wav" else ["-c:a", "aac", "-b:a", "256k"]
    # loudnorm resamples internally to 192 kHz; pin the output back to 48 kHz.
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", src, "-map", "0", "-c:v", "copy",
           "-af", flt, "-ar", "48000", *acodec, dst]
    subprocess.run(cmd, check=True)
    after = measure(dst, target, tp, lra)
    return m, after


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pm = sub.add_parser("measure")
    pm.add_argument("file")
    pn = sub.add_parser("normalize")
    pn.add_argument("src")
    pn.add_argument("dst")
    for sp in (pm, pn):
        sp.add_argument("--target", type=float, default=-14.0, help="integrated LUFS (social: -14, broadcast: -23)")
        sp.add_argument("--true-peak", type=float, default=-1.0)
        sp.add_argument("--lra", type=float, default=11.0)
    a = p.parse_args()

    if a.cmd == "measure":
        m = measure(a.file, a.target, a.true_peak, a.lra)
        print(f"Integrated {m['input_i']} LUFS | true peak {m['input_tp']} dBTP | LRA {m['input_lra']} LU")
    else:
        before, after = normalize(a.src, a.dst, a.target, a.true_peak, a.lra)
        print(f"Before: {before['input_i']} LUFS, {before['input_tp']} dBTP")
        print(f"After:  {after['input_i']} LUFS, {after['input_tp']} dBTP -> {a.dst}")
        if abs(float(after["input_i"]) - a.target) > 1.0:
            print("Warning: result is more than 1 LU from target (very short or very dynamic audio?)", file=sys.stderr)


if __name__ == "__main__":
    main()
