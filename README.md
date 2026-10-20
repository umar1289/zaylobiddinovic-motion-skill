# zaylobiddinovic-motion

A Claude Code skill for making videos with code. Describe the video; Claude writes a storyboard, builds it in [Remotion](https://www.remotion.dev/) (React) or edits your footage with FFmpeg, checks its own frames, and renders the final file on your machine. No After Effects needed.

**What it handles**

- Motion graphics: product promos, explainers, title cards, logo stings, kinetic typography
- 3D: app/device mockups turning in space, extruded 3D logos from your SVG, camera moves (React Three Fiber)
- Footage edits: trim, join, reframe 16:9 → 9:16, speed changes, crossfades, logos, jump cuts on silence
- Animated word-by-word captions from local Whisper transcription, plus SRT files
- Sound design: 20 built-in synthesized effects (whoosh, pop, click, impact, riser, typing…), search in your own SFX library, optional ElevenLabs generation, cue sheets that land each sound's hit exactly on the animation, and masking checks against voice and music
- Music, voiceover ducking and loudness normalization (−14 LUFS for social)
- Platform-ready exports for YouTube, Reels, TikTok, Shorts, feeds and web loops

## Install

In Claude Code:

```
/plugin marketplace add umar1289/zaylobiddinovic-motion-skill
/plugin install zaylobiddinovic-motion@zaylobiddinovic-motion
```

Or copy `skills/zaylobiddinovic-motion/` into `~/.claude/skills/` (all projects) or `<project>/.claude/skills/` (one project).

## Requirements

- Node.js 18+ and npm (Remotion)
- FFmpeg and ffprobe
- Python 3.9+ (helper scripts, standard library only)
- Optional: `pip install faster-whisper` for transcription/captions
- Optional: an ElevenLabs API key (`ELEVENLABS_API_KEY`) for AI-generated sound effects; everything else works offline

Check with:

```bash
python3 skills/zaylobiddinovic-motion/scripts/check_env.py
```

Claude asks before installing packages, downloading models or calling paid APIs. ElevenLabs requests are shown as a plan first and only sent after you agree.

## Try it

- "Make a 15-second vertical promo for my coffee app, brand colour #6B4EFF, ending with 'Download now'."
- "Add animated captions to `talk.mp4` and give me an SRT too."
- "Cut the silences out of this interview and reframe it for Reels."
- "Here's my logo, animate a 3-second intro sting."
- "Make my logo.svg 3D, swing it in with a heavy impact sound."
- "Add sound effects to this promo: whooshes on transitions, pops when icons appear."

## What's inside

```
skills/zaylobiddinovic-motion/
  SKILL.md                 workflow Claude follows
  references/              Remotion, motion design, FFmpeg, captions, audio, delivery guides
  scripts/                 environment check, media probe, contact sheets, transcription, loudness,
                           SFX synthesis / generation / analysis / library / cue sheets
  assets/remotion-starter/ storyboard-driven Remotion project (16:9, 9:16, captions, SFX track)
  assets/addons/three-3d/  3D product and logo compositions
```

## Licences

This skill is MIT licensed (see `LICENSE`). Remotion has its own licence: free for individuals, non-profits and companies with up to 3 employees; larger companies need a [Remotion company licence](https://www.remotion.dev/license). FFmpeg, Whisper and fonts are under their own licences. You are responsible for the rights to music, footage and fonts you use in your videos.

---

### O'zbekcha qisqacha

Claude Code uchun video yaratish skilli. Videoni so'z bilan tasvirlaysiz, Claude esa ssenariy (storyboard) tuzadi, Remotion yoki FFmpeg yordamida videoni yig'adi, kadrlarni o'zi tekshiradi va tayyor faylni kompyuteringizda render qiladi. Motion grafika, 3D (mahsulot va logo), montaj, animatsion subtitrlar, ovoz effektlari (sintez, o'z kutubxonangiz yoki ElevenLabs), musiqa va Reels/TikTok/YouTube uchun eksport bilan ishlaydi. O'rnatish buyruqlari yuqorida.
