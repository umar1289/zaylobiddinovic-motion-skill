#!/usr/bin/env python3
"""Generate sound effects with the ElevenLabs Sound Effects API (paid; uses the user's own key).

Plan only (default, no request sent, no credits used):
  python3 sfx_generate.py --prompt "Heavy metal door slam, short, dry, close mic" --duration 1.2 --out public/sfx/door.mp3
Send after the user approved the plan:
  python3 sfx_generate.py ... --yes
Batch file (JSON list of {"name", "prompt", "duration"?, "influence"?, "loop"?, "variations"?}):
  python3 sfx_generate.py --batch sfx_requests.json --out-dir public/sfx --yes

Key: read from the ELEVENLABS_API_KEY environment variable, or from KEY=VALUE lines in --env-file (parsed, never
executed). The key is never printed or written anywhere. Each request costs credits on the user's plan; check
current pricing on elevenlabs.io. Every generated file is recorded in sfx_manifest.json next to it.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

API_BASE = "https://api.elevenlabs.io"
MODEL = "eleven_text_to_sound_v2"
FORMATS = {"mp3_44100_128": ".mp3", "mp3_44100_192": ".mp3", "opus_48000_128": ".opus",
           "wav_44100": ".wav", "wav_48000": ".wav", "pcm_48000": ".pcm"}


def load_key(env_file):
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key and env_file:
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*(?:export\s+)?ELEVENLABS_API_KEY\s*=\s*(.*)\s*$", line)
                if m:
                    key = m.group(1).strip().strip("'\"")
    return key


def slug(text, limit=40):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].rstrip("-") or "sfx"


def build_jobs(a):
    if a.batch:
        with open(a.batch, encoding="utf-8") as f:
            items = json.load(f)
        if not isinstance(items, list):
            raise SystemExit("--batch must contain a JSON list")
        out_dir = a.out_dir or os.path.dirname(a.batch) or "."
    else:
        if not a.prompt:
            raise SystemExit("give --prompt or --batch")
        items = [{"name": None, "prompt": a.prompt, "duration": a.duration, "influence": a.influence,
                  "loop": a.loop, "variations": a.variations}]
        out_dir = a.out_dir or (os.path.dirname(a.out) if a.out else ".")
    ext = FORMATS[a.format]
    jobs = []
    for it in items:
        prompt = (it.get("prompt") or "").strip()
        if not prompt:
            raise SystemExit(f"empty prompt in {it}")
        dur = it.get("duration")
        if dur is not None and not (0.5 <= float(dur) <= 30):
            raise SystemExit(f"duration must be 0.5-30 s (got {dur}) for: {prompt}")
        infl = it.get("influence", 0.3)
        if infl is not None and not (0 <= float(infl) <= 1):
            raise SystemExit(f"influence must be 0-1 for: {prompt}")
        n = int(it.get("variations") or 1)
        base = it.get("name") or (os.path.splitext(os.path.basename(a.out))[0] if a.out and not a.batch else slug(prompt))
        for k in range(n):
            name = f"{base}-{k + 1}" if n > 1 else base
            path = a.out if (a.out and not a.batch and n == 1) else os.path.join(out_dir, name + ext)
            jobs.append({"path": path, "prompt": prompt, "duration": dur, "influence": infl,
                         "loop": bool(it.get("loop", False))})
    return jobs


def request(api_base, key, job, fmt, retries=1):
    body = {"text": job["prompt"], "model_id": MODEL}
    if job["duration"] is not None:
        body["duration_seconds"] = float(job["duration"])
    if job["influence"] is not None:
        body["prompt_influence"] = float(job["influence"])
    if job["loop"]:
        body["loop"] = True
    url = f"{api_base.rstrip('/')}/v1/sound-generation?output_format={fmt}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json",
                                          "Accept": "audio/*"})
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            return res.read(), res.headers.get("request-id") or res.headers.get("x-request-id")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        if e.code == 429 and retries > 0:
            print("  rate limited; waiting 10 s and retrying once", file=sys.stderr)
            time.sleep(10)
            return request(api_base, key, job, fmt, retries - 1)
        hint = {401: "key rejected (check ELEVENLABS_API_KEY)", 402: "not enough credits or plan limit",
                422: "invalid parameters"}.get(e.code, "request failed")
        raise SystemExit(f"ElevenLabs HTTP {e.code}: {hint}. {detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Network error: {e.reason}")


def update_manifest(path, entry):
    man_path = os.path.join(os.path.dirname(os.path.abspath(path)), "sfx_manifest.json")
    data = []
    if os.path.exists(man_path):
        with open(man_path, encoding="utf-8") as f:
            data = json.load(f)
    data = [d for d in data if d.get("file") != entry["file"]] + [entry]
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return man_path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt")
    p.add_argument("--duration", type=float, default=None, help="0.5-30 s; omit to let the model choose")
    p.add_argument("--influence", type=float, default=0.3, help="0-1, higher follows the prompt more literally")
    p.add_argument("--loop", action="store_true", help="seamless loop (ambiences, hums)")
    p.add_argument("--variations", type=int, default=1)
    p.add_argument("--out", help="output file for a single prompt")
    p.add_argument("--out-dir")
    p.add_argument("--batch", help="JSON list of requests")
    p.add_argument("--format", choices=sorted(FORMATS), default="mp3_44100_128",
                   help="44.1 kHz WAV/PCM need a Pro plan or higher")
    p.add_argument("--wav", action="store_true", help="also write a 48 kHz WAV copy for editing (needs ffmpeg)")
    p.add_argument("--max-requests", type=int, default=10, help="safety cap per run")
    p.add_argument("--yes", action="store_true", help="actually send the requests")
    p.add_argument("--env-file", help="file with an ELEVENLABS_API_KEY=... line")
    p.add_argument("--api-base", default=API_BASE, help="e.g. a regional/data-residency endpoint")
    p.add_argument("--overwrite", action="store_true")
    a = p.parse_args()

    jobs = build_jobs(a)
    secs = sum(float(j["duration"]) for j in jobs if j["duration"] is not None)
    auto = sum(1 for j in jobs if j["duration"] is None)
    print(f"Plan: {len(jobs)} request(s) to ElevenLabs {MODEL}, format {a.format}")
    print(f"      fixed durations total {secs:.1f} s" + (f", {auto} with model-chosen duration" if auto else ""))
    for j in jobs:
        d = f"{j['duration']}s" if j["duration"] is not None else "auto"
        print(f"  - {j['path']}  [{d}, influence {j['influence']}{', loop' if j['loop'] else ''}]  \"{j['prompt']}\"")
    if len(jobs) > a.max_requests:
        raise SystemExit(f"{len(jobs)} requests exceeds --max-requests {a.max_requests}; raise it only with the user's OK")
    clash = [j["path"] for j in jobs if os.path.exists(j["path"])]
    if clash and not a.overwrite:
        raise SystemExit("These files already exist (use new names or --overwrite): " + ", ".join(clash))
    if not a.yes:
        print("Dry run: nothing sent. Each request uses credits; get the user's approval, then re-run with --yes.")
        return

    key = load_key(a.env_file)
    if not key:
        raise SystemExit("ELEVENLABS_API_KEY is not set. Ask the user to set it in their shell or an env file; "
                         "do not paste it into chat or commit it.")

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from sfx_analyze import analyze  # noqa: E402

    for j in jobs:
        os.makedirs(os.path.dirname(os.path.abspath(j["path"])), exist_ok=True)
        audio, req_id = request(a.api_base, key, j, a.format)
        with open(j["path"], "wb") as f:
            f.write(audio)
        entry = {"file": os.path.basename(j["path"]), "source": "ElevenLabs Sound Effects API", "model": MODEL,
                 "prompt": j["prompt"], "duration_seconds": j["duration"], "prompt_influence": j["influence"],
                 "loop": j["loop"], "format": a.format, "request_id": req_id,
                 "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                 "rights": "Per the user's ElevenLabs plan terms; record the plan in final/credits.txt"}
        if a.wav and not a.format.startswith("pcm"):
            wav = os.path.splitext(j["path"])[0] + ".wav"
            if wav != j["path"]:
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", j["path"], "-ar", "48000", "-c:a", "pcm_s24le", wav],
                               check=True)
                entry["wav_copy"] = os.path.basename(wav)
                entry["note"] = "WAV converted from lossy " + a.format
        update_manifest(j["path"], entry)
        if not a.format.startswith("pcm"):
            info = analyze(j["path"])
            print(f"Saved {j['path']}: {info['duration_ms']} ms, hit at {info['hit_ms']} ms, tail ends {info['tail_end_ms']} ms")
        else:
            print(f"Saved {j['path']} (raw PCM 48 kHz s16le)")


if __name__ == "__main__":
    main()
