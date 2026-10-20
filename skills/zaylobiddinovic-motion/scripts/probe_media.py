#!/usr/bin/env python3
"""Summarize media files: duration, resolution, fps, codecs, audio layout.

Usage: python3 probe_media.py FILE [FILE ...] [--json]
"""
import json
import subprocess
import sys
from fractions import Fraction


def probe(path):
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"ffprobe failed for {path}: {res.stderr.strip()}")
    data = json.loads(res.stdout)
    fmt = data.get("format", {})
    summary = {"file": path, "duration_s": round(float(fmt.get("duration", 0) or 0), 3),
               "size_mb": round(int(fmt.get("size", 0) or 0) / 1e6, 2), "video": [], "audio": []}
    for s in data.get("streams", []):
        if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic") != 1:
            rate = s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/1"
            fps = float(Fraction(rate)) if rate != "0/0" else 0.0
            summary["video"].append({"codec": s.get("codec_name"), "width": s.get("width"), "height": s.get("height"),
                                     "fps": round(fps, 3), "pix_fmt": s.get("pix_fmt")})
        elif s.get("codec_type") == "audio":
            summary["audio"].append({"codec": s.get("codec_name"), "sample_rate": s.get("sample_rate"),
                                     "channels": s.get("channels")})
    return summary


def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return
    results = [probe(p) for p in args]
    if "--json" in sys.argv:
        print(json.dumps(results, indent=2))
        return
    for r in results:
        print(f"{r['file']}: {r['duration_s']}s, {r['size_mb']} MB")
        for v in r["video"]:
            print(f"  video {v['codec']} {v['width']}x{v['height']} @ {v['fps']} fps ({v['pix_fmt']})")
        for a in r["audio"]:
            print(f"  audio {a['codec']} {a['sample_rate']} Hz, {a['channels']} ch")
        if not r["audio"]:
            print("  audio: none")


if __name__ == "__main__":
    main()
