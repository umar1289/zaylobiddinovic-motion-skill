# zaylobiddinovic-motion

**English** · [O'zbekcha](README.md)

A Claude Code skill that acts as director, motion designer, editor and sound designer for your videos. Describe the video; Claude reverse-engineers your references, writes the voiceover script and storyboard, builds a visual design file for approval, renders deterministic code-drawn animation in headless Chrome, checks timestamped contact sheets of every change, and delivers a versioned final file. No After Effects needed.

**What it handles**

- Motion graphics: kinetic typography, explainers, UI/SaaS promos, logo stings, 2D and 3D (Three.js / React Three Fiber) scenes
- Three pipelines: A code-drawn, B mixed AI assets + code, C footage edits (talking heads, tutorials, UGC)
- Reference analysis: timestamped contact sheets, every frame of the hook, scene cuts, spectrogram, onset candidates
- Voiceover: paste-ready ElevenLabs scripts with word budgets; timing locked to your final recording
- Sound design: seeded procedural SFX, your own licensed library with a verifiable catalog, optional ElevenLabs generation, optional local CLAP/PANNs analysis
- Project memory (`TASTE.md`, `PROGRESS.md`, `LOG.md`, `manifest.json`) so a new chat continues in the same style
- QA and delivery: safe zones, contrast, sync, loudness (−14 LUFS / −1.5 dBTP), licences, versioned outputs

## Install

In Claude Code:

```
/plugin marketplace add umar1289/zaylobiddinovic-motion-skill
/plugin install zaylobiddinovic-motion@zaylobiddinovic-motion
```

Or copy `skills/zaylobiddinovic-motion/` into `~/.claude/skills/` (all projects) or `<project>/.claude/skills/` (one project). See `skills/zaylobiddinovic-motion/reference/installation.md` for the Claude app and host limits.

## Requirements

- Python 3.10+ (helper scripts)
- FFmpeg and ffprobe
- Node.js 18+ with Playwright and Chromium for code-rendered scenes
- Optional: NumPy + SciPy (procedural SFX), librosa + soundfile (waveform analysis), Pillow (labelled reference sheets)
- Optional: an ElevenLabs API key (`ELEVENLABS_API_KEY`) for generated sound effects

Check with:

```bash
python3 skills/zaylobiddinovic-motion/scripts/preflight.py
```

The check is read-only. Claude asks before installing packages, downloading models or making paid API calls.

## Try it

- "Create a 10-second kinetic typography video."
- "Here's a reference reel, reverse-engineer it and make one for my app."
- "Write a 30-second voiceover script for ElevenLabs about my product."
- "Fix only the title size at 0:04 in this project."
- "Add sound effects: soft ticks on each word, a pop when the card lands."

## What's inside

```
skills/zaylobiddinovic-motion/
  SKILL.md            workflow Claude follows
  reference/          planning, visual design, voiceover, 3D, sound, fonts, recipes, delivery guides
  scripts/            preflight, reference analysis, range previews, SFX tools, env helpers
  templates/          TASTE.md, design.html, SFX catalog, deterministic render starter
```

## Licences

MIT licensed (see `LICENSE`). Third-party software, models, fonts, footage, music and sound effects keep their own licences; you are responsible for the rights to assets used in your videos.
