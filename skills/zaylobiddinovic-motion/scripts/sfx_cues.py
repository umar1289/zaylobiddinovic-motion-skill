#!/usr/bin/env python3
"""Place sound effects on visual events, check they are audible, and preview the mix.

The cue sheet (JSON) is the single list of every sound in the video:
  {
    "fps": 30,
    "public_dir": ".",                         # where "file" paths resolve, relative to this JSON
    "cues": [
      {"id": "logo-lands", "t": 2.4, "file": "sfx/impact.wav", "gain_db": -6, "align": "hit"},
      {"id": "reveal",     "frame": 90, "file": "sfx/riser.wav", "gain_db": -10, "align": "end"}
    ]
  }
  t / frame  time of the VISUAL event (seconds, or a frame number at "fps")
  align      which point of the sound lands on the event: hit (default: the audible hit), start, peak, end
  nudge_ms   optional fine offset; negative = earlier. Sound slightly early (0-20 ms) reads as in sync.

Commands:
  prepare CUES                 measure every file, write start_s/hit_ms/duration_ms into the sheet, report problems
  mix CUES OUT.wav             render the cues to one stem (optionally over --bed voice/music) to listen or mux
  check CUES --bed BED         is each cue audible over the voice/music at its moment? (run after prepare)
  from-captions CAPS --file F [--file F2 ...] --out CUES [--every word|phrase] [--gain-db -20]
                               cues for word-by-word caption pops, rotating through variations
The Remotion <SfxTrack cuesFile="..."/> component plays a prepared sheet from public/.
"""
import argparse
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sfx_analyze import SR, analyze, decode  # noqa: E402


def load(path):
    with open(path, encoding="utf-8") as f:
        sheet = json.load(f)
    sheet.setdefault("fps", 30)
    sheet.setdefault("public_dir", ".")
    sheet.setdefault("cues", [])
    return sheet


def resolve(sheet_path, sheet, file):
    base = os.path.join(os.path.dirname(os.path.abspath(sheet_path)), sheet["public_dir"])
    return os.path.normpath(os.path.join(base, file))


def event_time(cue, fps):
    if "t" in cue:
        return float(cue["t"])
    if "frame" in cue:
        return float(cue["frame"]) / fps
    raise SystemExit(f"cue {cue.get('id', '?')} needs 't' (seconds) or 'frame'")


def cmd_prepare(a):
    sheet = load(a.cues)
    fps = sheet["fps"]
    problems, cache = [], {}
    for i, c in enumerate(sheet["cues"]):
        c.setdefault("id", f"cue-{i + 1}")
        c.setdefault("gain_db", 0)
        c.setdefault("align", "hit")
        path = resolve(a.cues, sheet, c["file"])
        if not os.path.exists(path):
            problems.append(f"{c['id']}: file not found: {path}")
            continue
        info = cache.get(path) or analyze(path)
        cache[path] = info
        offset = {"start": 0.0, "hit": info["hit_ms"], "peak": info["peak_ms"], "end": info["tail_end_ms"]}.get(c["align"])
        if offset is None:
            problems.append(f"{c['id']}: unknown align '{c['align']}'")
            continue
        t = event_time(c, fps)
        start = t - offset / 1000 + float(c.get("nudge_ms", 0)) / 1000
        c.update({"hit_ms": info["hit_ms"], "duration_ms": info["duration_ms"], "tail_end_ms": info["tail_end_ms"],
                  "start_s": round(start, 4)})
        if start < 0:
            problems.append(f"{c['id']}: would start {abs(start):.3f}s before 0; move the event or use a shorter sound")
            c["start_s"] = 0.0
        if info["lead_silence_ms"] > 20 and c["align"] == "start":
            problems.append(f"{c['id']}: file has {info['lead_silence_ms']} ms leading silence; trim it or align 'hit'")
        if a.duration and start + info["tail_end_ms"] / 1000 > a.duration:
            problems.append(f"{c['id']}: tail runs past the end of the video ({a.duration}s)")

    timed = sorted((c for c in sheet["cues"] if "start_s" in c), key=lambda c: c["start_s"] + c["hit_ms"] / 1000)
    for prev, cur in zip(timed, timed[1:]):
        gap = (cur["start_s"] + cur["hit_ms"] / 1000) - (prev["start_s"] + prev["hit_ms"] / 1000)
        if gap < 0.05:
            problems.append(f"{prev['id']} and {cur['id']} hit {gap * 1000:.0f} ms apart; they will smear into one sound")
        if prev["file"] == cur["file"] and gap < 0.6:
            problems.append(f"{prev['id']} -> {cur['id']}: same file back to back; use variations to avoid a machine-gun effect")
    # A cue whose hit lands inside a louder, still-sounding cue tends to disappear (e.g. a pop during a whoosh).
    for cur in timed:
        hit_t = cur["start_s"] + cur["hit_ms"] / 1000
        for other in timed:
            if other is cur:
                continue
            o_hit = other["start_s"] + other["hit_ms"] / 1000
            inside = other["start_s"] <= hit_t <= other["start_s"] + other["tail_end_ms"] / 1000
            if inside and abs(o_hit - hit_t) >= 0.05 and other.get("gain_db", 0) >= cur.get("gain_db", 0) - 2:
                problems.append(f"{cur['id']} hits while {other['id']} is still sounding at a similar or higher level; "
                                f"it may be masked (lower {other['id']}, raise {cur['id']}, or separate them)")
    if timed:
        span = max(c["start_s"] for c in timed) - min(c["start_s"] for c in timed) or 1
        density = len(timed) / span
        if density > 4:
            problems.append(f"{density:.1f} cues per second on average; consider fewer, more meaningful sounds")

    with open(a.cues, "w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=2, ensure_ascii=False)
    print(f"Prepared {len(timed)} cues in {a.cues}")
    for c in timed:
        print(f"  {c['start_s']:7.3f}s  {c['id']:<18} {c['file']}  ({c['align']} @ {event_time(c, fps):.3f}s, {c['gain_db']} dB)")
    for p_ in problems:
        print("  ! " + p_)
    return 1 if any("not found" in p_ for p_ in problems) else 0


def ffmpeg_mix(a, sheet, cues, out, beds):
    inputs, chains, labels = [], [], []
    for k, (path, gain_db) in enumerate(beds):
        inputs += ["-i", path]
        chains.append(f"[{k}:a]aresample={SR},aformat=channel_layouts=stereo,volume={gain_db}dB[b{k}]")
        labels.append(f"[b{k}]")
    for j, c in enumerate(cues):
        idx = len(beds) + j
        inputs += ["-i", resolve(a.cues, sheet, c["file"])]
        ms = max(0, round(c["start_s"] * 1000))
        chains.append(f"[{idx}:a]aresample={SR},aformat=channel_layouts=stereo,adelay={ms}|{ms},"
                      f"volume={c.get('gain_db', 0)}dB[c{j}]")
        labels.append(f"[c{j}]")
    if not labels:
        raise SystemExit("nothing to mix")
    tail = f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:dropout_transition=0"
    if a.duration:
        tail += f",apad,atrim=0:{a.duration}"
    chains.append(tail + "[out]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains), "-map", "[out]",
           "-c:a", "pcm_s24le", "-ar", str(SR), out]
    subprocess.run(cmd, check=True)


def prepared_cues(sheet):
    cues = [c for c in sheet["cues"] if "start_s" in c]
    if len(cues) < len(sheet["cues"]):
        raise SystemExit("Run 'prepare' first: some cues have no start_s")
    return cues


def cmd_mix(a):
    sheet = load(a.cues)
    beds = [(b, a.bed_gain_db) for b in a.bed or []]
    ffmpeg_mix(a, sheet, prepared_cues(sheet), a.out, beds)
    peak = max(abs(v) for v in decode(a.out)) or 1e-9
    print(f"Wrote {a.out} ({len(sheet['cues'])} cues{', over ' + str(len(beds)) + ' bed(s)' if beds else ''}); "
          f"peak {20 * math.log10(peak):.1f} dBFS")
    if peak >= 1.0:
        print("  ! clipping: lower cue gains or the bed")


def window_rms(samples, start_s, length_s):
    i0, i1 = int(max(0, start_s) * SR), int(max(0, start_s + length_s) * SR)
    w = samples[i0:i1]
    if not w:
        return 1e-9
    return math.sqrt(sum(v * v for v in w) / len(w)) or 1e-9


def cmd_check(a):
    sheet = load(a.cues)
    cues = prepared_cues(sheet)
    bed = decode(a.bed)
    print(f"{'cue':<18} {'hit at':>8} {'cue dB':>7} {'bed dB':>7} {'margin':>7}  verdict")
    worst = 0
    for c in sorted(cues, key=lambda c: c["start_s"]):
        snd = decode(resolve(a.cues, sheet, c["file"]))
        g = 10 ** (c.get("gain_db", 0) / 20)
        hit = c["hit_ms"] / 1000
        win = min(0.12, max(0.02, c["tail_end_ms"] / 1000 - hit))
        cue_db = 20 * math.log10(window_rms(snd, hit, win) * g)
        bed_db = 20 * math.log10(window_rms(bed, c["start_s"] + hit, win))
        margin = cue_db - bed_db
        if bed_db < -60:
            verdict = "clear (bed silent here)"
        elif margin < -6:
            verdict, worst = "MASKED: raise gain, brighten, or move it", max(worst, 2)
        elif margin < 0:
            verdict, worst = "borderline: listen", max(worst, 1)
        elif margin > 14 and a.flag_loud:
            verdict = "very loud vs bed"
        else:
            verdict = "audible"
        print(f"{c['id']:<18} {c['start_s'] + hit:8.3f} {cue_db:7.1f} {bed_db:7.1f} {margin:7.1f}  {verdict}")
    print("Margins compare short-term levels in the hit window; they predict audibility but are not a substitute for listening.")
    return 2 if worst == 2 else 0


def cmd_from_captions(a):
    with open(a.captions, encoding="utf-8") as f:
        caps = json.load(f)
    cues, k = [], 0
    for i, c in enumerate(caps):
        if a.every == "phrase":
            prev = caps[i - 1] if i else None
            if prev and c["startMs"] - prev["endMs"] < a.gap_ms and not prev["text"].rstrip().endswith((".", "!", "?", ",")):
                continue
        cues.append({"id": f"cap-{i + 1}", "t": round(c["startMs"] / 1000, 3), "file": a.file[k % len(a.file)],
                     "gain_db": a.gain_db, "align": "hit", "note": c["text"].strip()})
        k += 1
    # Sound paths are usually relative to the folder holding the captions (Remotion's public/).
    public_dir = a.public_dir if a.public_dir is not None else os.path.relpath(
        os.path.dirname(os.path.abspath(a.captions)), os.path.dirname(os.path.abspath(a.out)))
    sheet = {"fps": a.fps, "public_dir": public_dir, "cues": cues}
    if a.append and os.path.exists(a.out):
        old = load(a.out)
        old["cues"] = [c for c in old["cues"] if not str(c.get("id", "")).startswith("cap-")] + cues
        sheet = old
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(cues)} caption cues to {a.out}; run 'prepare' next.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("prepare")
    pp.add_argument("cues")
    pp.add_argument("--duration", type=float, help="video length in seconds, to flag tails running past the end")
    pm = sub.add_parser("mix")
    pm.add_argument("cues")
    pm.add_argument("out")
    pm.add_argument("--bed", action="append", help="voice/music file under the cues (repeatable)")
    pm.add_argument("--bed-gain-db", type=float, default=0.0)
    pm.add_argument("--duration", type=float)
    pc = sub.add_parser("check")
    pc.add_argument("cues")
    pc.add_argument("--bed", required=True, help="the mix WITHOUT sound effects (voice + music), or a render of it")
    pc.add_argument("--flag-loud", action="store_true")
    pf = sub.add_parser("from-captions")
    pf.add_argument("captions")
    pf.add_argument("--file", action="append", required=True, help="sound file (relative to public_dir); repeat for variations")
    pf.add_argument("--out", required=True)
    pf.add_argument("--every", choices=["word", "phrase"], default="word")
    pf.add_argument("--gap-ms", type=float, default=300, help="phrase mode: pause that starts a new phrase")
    pf.add_argument("--gain-db", type=float, default=-20)
    pf.add_argument("--fps", type=int, default=30)
    pf.add_argument("--public-dir", default=None, help="folder --file paths are relative to, from the output sheet "
                    "(default: the captions file's folder)")
    pf.add_argument("--append", action="store_true", help="replace only cap-* cues in an existing sheet")
    a = p.parse_args()
    fn = {"prepare": cmd_prepare, "mix": cmd_mix, "check": cmd_check, "from-captions": cmd_from_captions}[a.cmd]
    sys.exit(fn(a) or 0)


if __name__ == "__main__":
    main()
