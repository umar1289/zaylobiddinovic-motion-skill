#!/usr/bin/env python3
"""Make one image grid of evenly spaced frames from a video, for fast visual review.

Usage: python3 contact_sheet.py VIDEO OUT.png [--count 12] [--cols 4] [--width 480] [--start S] [--end S]
"""
import argparse
import json
import math
import os
import subprocess
import tempfile


def duration_of(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video")
    p.add_argument("out")
    p.add_argument("--count", type=int, default=12)
    p.add_argument("--cols", type=int, default=4)
    p.add_argument("--width", type=int, default=480, help="width of each tile in pixels")
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--end", type=float, default=None)
    a = p.parse_args()
    if a.count < 1 or a.cols < 1 or a.width < 16:
        p.error("count and cols must be >= 1, width >= 16")

    end = a.end if a.end is not None else duration_of(a.video)
    span = end - a.start
    if span <= 0:
        p.error("end must be after start")
    cols = min(a.cols, a.count)
    rows = math.ceil(a.count / cols)
    # Sample the middle of each slot so the first tile is not a black fade-in frame.
    times = [a.start + span * (i + 0.5) / a.count for i in range(a.count)]

    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", a.video, "-frames:v", "1",
                            "-vf", f"scale={a.width}:-2,setsar=1", os.path.join(tmp, f"{i:04d}.png")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", os.path.join(tmp, "%04d.png"),
                        "-vf", f"tile={cols}x{rows}:padding=4:margin=4", "-frames:v", "1", a.out], check=True)

    print(f"Wrote {a.out}: {a.count} frames, {cols}x{rows} grid, {a.start:.2f}s to {end:.2f}s")
    for i, t in enumerate(times):
        print(f"  tile {i + 1}: {t:.2f}s")


if __name__ == "__main__":
    main()
