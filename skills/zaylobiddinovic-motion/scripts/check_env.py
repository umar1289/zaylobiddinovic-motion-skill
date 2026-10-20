#!/usr/bin/env python3
"""Report which video tools are available. Read-only: installs nothing, prints no secrets.

Usage: python3 check_env.py [--json]
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

TOOLS = {
    "node": (["node", "--version"], "required for Remotion (v18+)"),
    "npm": (["npm", "--version"], "required to install Remotion packages"),
    "ffmpeg": (["ffmpeg", "-version"], "required for editing, previews and audio"),
    "ffprobe": (["ffprobe", "-version"], "required for media inspection"),
    "git": (["git", "--version"], "optional, for project versioning"),
    "whisper-cli": (["whisper-cli", "--help"], "optional, whisper.cpp transcription"),
}

PY_MODULES = {
    "faster_whisper": "optional, local transcription (pip install faster-whisper)",
    "whisper": "optional, local transcription (pip install openai-whisper)",
}

ENV_KEYS = ["ELEVENLABS_API_KEY", "OPENAI_API_KEY"]


def first_line(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        text = (out.stdout or out.stderr).strip().splitlines()
        return text[0] if text else "available"
    except Exception as exc:  # tool exists but misbehaves
        return f"error: {exc.__class__.__name__}"


def main():
    report = {"python": sys.version.split()[0], "platform": sys.platform, "tools": {}, "python_modules": {}, "env": {}}
    for name, (cmd, note) in TOOLS.items():
        found = shutil.which(cmd[0]) is not None
        report["tools"][name] = {"found": found, "version": first_line(cmd) if found else None, "note": note}
    for mod, note in PY_MODULES.items():
        report["python_modules"][mod] = {"found": importlib.util.find_spec(mod) is not None, "note": note}
    for key in ENV_KEYS:
        # Only report presence, never the value.
        report["env"][key] = "set" if os.environ.get(key) else "not set"

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
        return

    print(f"Python {report['python']} on {report['platform']}")
    for name, info in report["tools"].items():
        mark = "OK " if info["found"] else "-- "
        print(f"  {mark}{name:<12} {info['version'] or 'not found'}  ({info['note']})")
    for mod, info in report["python_modules"].items():
        mark = "OK " if info["found"] else "-- "
        print(f"  {mark}{mod:<12} {'installed' if info['found'] else 'not installed'}  ({info['note']})")
    for key, state in report["env"].items():
        print(f"  env {key}: {state}")


if __name__ == "__main__":
    main()
