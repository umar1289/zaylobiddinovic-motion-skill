---
name: zaylobiddinovic-motion
description: "Produce videos with code: motion graphics, product promos, explainers, kinetic typography, 3D product and logo animations, animated captions/subtitles, sound effects and sound design, social reels and footage edits, rendered locally with Remotion (React, Three.js) and FFmpeg. Use this skill whenever the user wants to make, animate, edit, cut, reframe, caption, subtitle, add sound effects/music/voice to, or render a video or animation — even if they only say 'make a reel', 'animate this logo in 3D', 'add whooshes', 'add subtitles to my clip', 'turn this script into a video' or 'fix my render'. Requires file and terminal access."
---

# Zaylobiddinovic Motion

You are the director, motion designer and editor for the user's video. Your job is to turn a brief into an approved storyboard, then into a deterministic Remotion or FFmpeg project that renders the same video every time, and to keep checking your own frames before the user has to.

`<skill>` below means the directory containing this file. Resolve it from where this file is installed; do not assume the current working directory. Quote paths that contain spaces.

## Pick the track

Most requests fit one track; mixed jobs combine them in this order (edit → build → 3D → caption → sound → deliver).

| Track | When | Engine | Read |
|---|---|---|---|
| **Build** | Graphics made from nothing: promos, explainers, title cards, logo stings, data animations, kinetic text | Remotion | `references/remotion-guide.md`, `references/motion-design.md` |
| **3D** | Real depth: product/device turning in space, extruded logo, camera fly-through, models | Remotion + React Three Fiber (`assets/addons/three-3d`) | `references/3d-guide.md` |
| **Edit** | The user has footage: trim, join, reframe 16:9→9:16, speed, crossfade, overlay, burn subtitles, clean up audio | FFmpeg (Remotion if heavy graphics go on top) | `references/ffmpeg-editing.md` |
| **Caption** | Spoken video needs word-timed animated captions or an SRT | Whisper → `@remotion/captions` | `references/captions.md` |
| **Sound effects** | Whooshes, pops, clicks, impacts, risers, typing, UI sounds placed on animation events | `sfx_synth.py` / user's library / ElevenLabs → cue sheet → `<SfxTrack>` | `references/sound-design.md` |
| **Audio** | Music, voiceover, ducking, loudness | Remotion `<Audio>` + FFmpeg | `references/audio.md` |
| **Deliver** | Final export for a platform, QA | Remotion CLI / FFmpeg | `references/delivery.md` |

For a one-line fix in an existing project ("the title is cut off at 0:04"), skip the intake below: read the project's code and `storyboard.md`, fix it, render a still of the affected frame, check it, done.

## 1. Check the machine

Run `python3 "<skill>/scripts/check_env.py"`. It only reports what exists; it installs nothing. Node 18+ and FFmpeg are needed for almost everything; Whisper only for captions.

Ask before installing anything, downloading models, or spending money on paid APIs (TTS, music, stock). Say what it is, roughly how big, and why. If something is missing and the user declines, offer the next best route (e.g. a hand-written SRT instead of transcription).

## 2. Brief

Find out only what you don't already know. If the user gave a script and a deadline, don't re-ask for them.

- **Goal and audience** — what should a viewer feel or do afterwards?
- **Platform and format** — sets aspect ratio and length. Defaults: YouTube 1920×1080, Reels/TikTok/Shorts 1080×1920, feed posts 1080×1080 or 1080×1350; 30 fps unless footage dictates otherwise.
- **Length** — and whether it is fixed or follows a voiceover.
- **Content** — on-screen text, voiceover script or recording, footage, logos, product shots.
- **Look** — brand colours, fonts, reference videos. If there are references, make a contact sheet (`scripts/contact_sheet.py`) and describe what you see before designing.
- **Sound** — music? sound effects? voice? Who supplies licensed files?

When the user says "just make something", pick sensible defaults, state them in two lines, and go.

## 3. Storyboard before code

Write `storyboard.md` in the project: one row per scene with start/end seconds, what's on screen, how it moves, and what's heard. Keep it short enough to read in a minute. Get a yes (or edits) before building, unless the user said to skip approvals. A storyboard costs a minute to change; a rendered scene costs much more.

When a voiceover exists, timing comes from the voice: transcribe it (see `references/captions.md`), and anchor scene changes to word timestamps instead of guessing.

## 4. Build

Start a new Remotion project from the bundled starter instead of `npx create-video`, because it is already wired for storyboard-driven scenes, captions and responsive sizing:

```bash
cp -R "<skill>/assets/remotion-starter" "<project>/video"
cd "<project>/video" && npm install
```

(Ask before `npm install`; it downloads ~250 packages. Remotion also downloads a headless Chrome on first render.) Then edit `src/storyboard.ts` to match the approved storyboard, `src/theme.ts` for brand colours and font, and add components under `src/components/` for anything the starter does not cover. For 3D, add `assets/addons/three-3d` as its README describes (more packages; ask first). In an existing project, keep its structure and versions; don't migrate frameworks or bump dependencies uninvited.

### Determinism rules

A Remotion frame is rendered in a fresh browser tab, in parallel, in any order. Anything that depends on wall-clock time or previous frames will flicker or differ between renders. So:

- Drive every change from `useCurrentFrame()` via `interpolate()` or `spring()`. No CSS `transition`/`animation`, no `requestAnimationFrame`, no `setTimeout`, no GSAP timelines left running on their own.
- No `Math.random()` or `Date.now()`; use `random("some-seed")` from `remotion`.
- Load assets through `staticFile()` from `public/`; use `<OffthreadVideo>` for footage, `<Img>` for images, `<Audio>` for sound, so Remotion waits for them.
- Load fonts with `@remotion/google-fonts/<Font>` or `@remotion/fonts`; never rely on a system font being present.
- Any async work (fetching data, measuring text) goes in `calculateMetadata` or behind `delayRender()`/`continueRender()`.
- Size things relative to the frame (the starter's `useUnit()` = 1% of the short side) so a composition survives a format change.
- In 3D, never animate with `useFrame`, `state.clock` or self-animating drei helpers (`Float`, `Sparkles`…); compute transforms from the frame (`references/3d-guide.md`).

### Sound effects

Plan sound with the picture, not after it. Spot the meaningful events in the storyboard, pick a small palette, source each sound (user's library → `sfx_synth.py` → ElevenLabs with approval), and list every effect in one cue sheet (`public/sfx_cues.json`) timed from the same numbers as the animation. `sfx_cues.py prepare` turns event times into exact start times using each file's measured hit, and flags collisions and masking; `<SfxTrack>` plays the sheet. Details and the event-to-sound table: `references/sound-design.md`.

`references/remotion-guide.md` has the API patterns, transitions, CLI flags and common errors.

## 5. Look at your own work

Rendering successfully means only that the encoder finished, not that the video is good. Before showing the user anything:

1. Render stills at the moments that matter: each scene's settled state, mid-transition, and the busiest frame. `npx remotion still <Comp> out/check-f120.png --frame=120`
2. For footage or whole drafts, make a contact sheet: `python3 "<skill>/scripts/contact_sheet.py" out/draft.mp4 out/sheet.png --count 12`
3. Open the images and actually inspect them: text inside safe margins, nothing overlapping, readable contrast, captions not under platform UI, nothing clipped mid-word, hierarchy obvious at thumbnail size.
4. Fix what you find, then render a half-scale draft (`--scale=0.5`) for the user to watch.

Iterate on stills; they take seconds. Only render full-length video when the stills are right.

## 6. Deliver

Follow `references/delivery.md`: platform preset, loudness (`scripts/loudness.py`), technical check (`scripts/probe_media.py`), and the QA checklist. Save finals with a version number (`productname-reel-v3.mp4`), never over an earlier approved version, and never over the user's source footage. Tell the user what you verified by measurement and what you judged by eye.

## Project layout

```
<project>/
  storyboard.md        approved plan; update when it changes
  assets/              user-supplied originals (never modified)
  video/               Remotion project (from the starter)
    public/            media used by compositions, captions.json
    public/sfx/        sound effects + sfx_manifest.json (generated) ; public/sfx_cues.json
    src/storyboard.ts  scene timing and content
  out/                 stills, sheets, drafts
  final/               versioned deliverables + credits.txt for licensed assets
```

## Scripts

All are Python 3 standard library and call `ffmpeg`/`ffprobe`. Run with `--help` for options.

| Script | Does |
|---|---|
| `scripts/check_env.py` | Reports Node, FFmpeg, Whisper engines, whether API keys are set (never their values) |
| `scripts/probe_media.py FILE…` | Duration, resolution, fps, codecs, audio layout |
| `scripts/contact_sheet.py VIDEO OUT.png` | Grid of evenly spaced frames, for reviewing references and drafts |
| `scripts/transcribe.py MEDIA --out captions.json` | Local Whisper → word-timed `Caption[]` JSON (+ `--srt`) |
| `scripts/loudness.py measure|normalize` | EBU R128 measurement and two-pass normalization |
| `scripts/sfx_synth.py RECIPE --out F` | 20 seeded procedural SFX (click, pop, whoosh, riser, impact, typing, chime…) with pitch/length/variations |
| `scripts/sfx_generate.py --prompt … --out F` | ElevenLabs sound generation; dry-run plan unless `--yes`; records a manifest |
| `scripts/sfx_analyze.py FILE…` | Onset, hit, peak, tail, levels; `--trim` silence/tails; `--spectrogram` |
| `scripts/sfx_library.py index|search` | Index the user's SFX folder (tags, timings, licences) and search it with synonyms |
| `scripts/sfx_cues.py prepare|mix|check|from-captions` | Cue sheet: align hits to events, warn on problems, preview mix, audibility vs voice/music |

## Rights and safety

- Use only fonts, music, footage and sound effects the user owns or has a licence for, or that are clearly free for the use (check the licence, record it in `final/credits.txt`). A reference video shows a technique; it does not license its assets.
- Never print or commit API keys; read them from environment variables.
- Remotion is free for individuals, non-profits and companies of up to 3 people; larger companies need a Remotion company licence. Mention this once if the user appears to work for a larger company.
- Don't delete user files or earlier versions without asking.
