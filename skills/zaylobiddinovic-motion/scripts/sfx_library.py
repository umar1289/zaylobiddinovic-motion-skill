#!/usr/bin/env python3
"""Index the user's own sound-effects folder and search it by meaning, length and character.

Index (incremental; re-run after adding files):
  python3 sfx_library.py index ~/Sounds/SFX [--licence "Soundly Pro, commercial OK"] [--out ~/Sounds/SFX/sfx_index.json]
Search:
  python3 sfx_library.py search ~/Sounds/SFX/sfx_index.json "soft whoosh" [--max-ms 800] [--kind swell] [--limit 10]

Tags come from folder and file names ("UI/Clicks/button_soft_03.wav" -> ui, clicks, button, soft). A licence
is taken from --licence or from the nearest LICENSE*/licence*/readme* file found walking up from each sound.
"""
import argparse
import json
import os
import re
import sys

AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".oga", ".aif", ".aiff", ".m4a", ".opus", ".caf"}
LICENCE_NAMES = re.compile(r"^(licen[cs]e|copying|readme|terms)[^/]*$", re.I)
STOP = {"sfx", "sound", "sounds", "fx", "the", "and", "of", "wav", "mp3", "final", "new", "copy", "mono", "stereo"}

# Words that mean roughly the same thing to an editor. Searching one finds the others (at a lower score).
SYNONYMS = [
    {"whoosh", "woosh", "swoosh", "swish", "swoop", "pass", "passby", "flyby"},
    {"hit", "impact", "punch", "thud", "slam", "boom", "smash", "bang"},
    {"click", "tick", "tap", "press", "button", "toggle"},
    {"riser", "rise", "build", "uplifter", "tension", "swell"},
    {"downer", "drop", "fall", "downlifter", "sweep"},
    {"ding", "bell", "chime", "notification", "notify", "alert", "success"},
    {"pop", "bubble", "blip", "plop"},
    {"glitch", "digital", "stutter", "data", "error", "distort"},
    {"typing", "keyboard", "keys", "typewriter", "type"},
    {"transition", "swipe", "slide", "transition"},
    {"ui", "interface", "menu", "app"},
    {"sparkle", "shine", "glitter", "magic", "twinkle"},
    {"camera", "shutter", "photo", "snapshot"},
    {"paper", "page", "flip", "rustle"},
    {"cash", "coin", "money", "register", "kaching"},
]


def tokens(text):
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    parts = re.split(r"[^A-Za-z]+", text.lower())
    return [p for p in parts if len(p) > 1 and p not in STOP]


def find_licence(path, root):
    d = os.path.dirname(path)
    root = os.path.abspath(root)
    while True:
        try:
            for name in sorted(os.listdir(d)):
                if LICENCE_NAMES.match(name) and os.path.isfile(os.path.join(d, name)):
                    return os.path.relpath(os.path.join(d, name), root)
        except OSError:
            pass
        if os.path.abspath(d) == root or os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def cmd_index(a):
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from sfx_analyze import analyze

    root = os.path.abspath(os.path.expanduser(a.folder))
    out = a.out or os.path.join(root, "sfx_index.json")
    old = {}
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            old = {e["path"]: e for e in json.load(f).get("sounds", [])}

    sounds, reused, failed = [], 0, []
    for dirpath, _, files in os.walk(root):
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() not in AUDIO_EXT:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            st = os.stat(full)
            prev = old.get(rel)
            if prev and prev.get("size") == st.st_size and prev.get("mtime") == int(st.st_mtime):
                sounds.append(prev)
                reused += 1
                continue
            try:
                info = analyze(full)
            except SystemExit as e:
                failed.append(f"{rel}: {e}")
                continue
            sounds.append({
                "path": rel, "size": st.st_size, "mtime": int(st.st_mtime),
                "tags": sorted(set(tokens(os.path.splitext(rel)[0]))),
                "duration_ms": info["duration_ms"], "hit_ms": info["hit_ms"], "tail_end_ms": info["tail_end_ms"],
                "peak_dbfs": info["peak_dbfs"], "rms_dbfs": info["rms_dbfs"], "character": info["character"],
                "licence": a.licence or find_licence(full, root),
            })
            if len(sounds) % 50 == 0:
                print(f"  ...{len(sounds)} files", file=sys.stderr)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"root": root, "sounds": sounds}, f, indent=1, ensure_ascii=False)
    print(f"Indexed {len(sounds)} sounds ({reused} unchanged) -> {out}")
    unlicensed = sum(1 for s in sounds if not s.get("licence"))
    if unlicensed:
        print(f"{unlicensed} sounds have no licence info; confirm their rights before using them in a delivery.")
    for msg in failed[:10]:
        print("  skipped " + msg, file=sys.stderr)


def score(sound, query):
    tags = set(sound["tags"])
    s = 0.0
    for q in query:
        if q in tags:
            s += 3
        elif any(t.startswith(q) or q.startswith(t) for t in tags if len(t) > 2):
            s += 1.5
        else:
            group = next((g for g in SYNONYMS if q in g), set())
            if tags & group:
                s += 1.2
            else:
                s -= 0.5  # wanted word missing
    return s


def cmd_search(a):
    with open(a.index, encoding="utf-8") as f:
        data = json.load(f)
    q = tokens(a.query)
    if not q:
        raise SystemExit("query has no searchable words")
    hits = []
    for snd in data["sounds"]:
        if a.max_ms and snd["duration_ms"] > a.max_ms:
            continue
        if a.min_ms and snd["duration_ms"] < a.min_ms:
            continue
        if a.kind and snd["character"] != a.kind:
            continue
        sc = score(snd, q)
        if sc > 0:
            hits.append((sc, snd))
    hits.sort(key=lambda h: (-h[0], h[1]["duration_ms"]))
    if a.json:
        print(json.dumps([dict(h[1], score=h[0], abs_path=os.path.join(data["root"], h[1]["path"]))
                          for h in hits[: a.limit]], indent=1))
        return
    if not hits:
        print("No matches. Try a synonym, drop filters, or generate/synthesize the sound.")
        return
    for sc, snd in hits[: a.limit]:
        lic = snd.get("licence") or "NO LICENCE INFO"
        print(f"{sc:4.1f}  {snd['duration_ms']:>7.0f} ms  hit@{snd['hit_ms']:<6} {snd['character']:<9} "
              f"{os.path.join(data['root'], snd['path'])}  [{lic}]")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("index")
    pi.add_argument("folder")
    pi.add_argument("--out")
    pi.add_argument("--licence", help="licence note applied to every file in this folder")
    ps = sub.add_parser("search")
    ps.add_argument("index")
    ps.add_argument("query")
    ps.add_argument("--max-ms", type=float)
    ps.add_argument("--min-ms", type=float)
    ps.add_argument("--kind", choices=["transient", "swell"])
    ps.add_argument("--limit", type=int, default=10)
    ps.add_argument("--json", action="store_true")
    a = p.parse_args()
    cmd_index(a) if a.cmd == "index" else cmd_search(a)


if __name__ == "__main__":
    main()
