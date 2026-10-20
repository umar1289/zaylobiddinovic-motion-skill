# Sound design for motion graphics

Read this when a video needs sound effects. Mixing levels, music and voice are covered in `audio.md`.

## Contents
1. Workflow
2. Spotting: which moments get a sound
3. Choosing sounds: palette and mapping
4. Getting the files (library, synthesis, ElevenLabs)
5. Placing cues precisely
6. Layering and variation
7. Checking the mix
8. Prompting ElevenLabs

## 1. Workflow

1. **Spot** the video: list the visual events from `storyboard.md` / `src/storyboard.ts` and decide which get sound (section 2).
2. **Palette:** pick 4–8 sound types that fit the brand (section 3) and agree them with the user if the brief is sensitive about sound.
3. **Source** each sound: the user's library first, then synthesis, then ElevenLabs generation with approval (section 4). Put files in `video/public/sfx/`.
4. **Cue sheet:** write `video/public/sfx_cues.json` with one cue per event, timed in seconds from the storyboard (section 5). Run `sfx_cues.py prepare`.
5. **Play** it in Remotion with `<SfxTrack cuesFile="sfx_cues.json" />` (the starter's `Promo` takes `sfxCuesFile`).
6. **Check:** `sfx_cues.py check` against the voice/music bed, render a short draft with audio, and ask the user to listen (section 7).

When scene timing changes, update the cue times and re-run `prepare`. The storyboard and the cue sheet must move together.

## 2. Spotting: which moments get a sound

Give sound to moments that carry meaning or physical weight:

- arrivals of key elements (logo lands, product appears, headline slams in)
- scene changes and big camera moves
- interactions (button press, toggle, swipe, typing, notification)
- counters and data reveals (a tick per step, a ding at the final number)
- the call to action

Leave the rest quiet: background drift, secondary labels, every word of body text, small easing adjustments. A video where everything makes a noise sounds like a demo reel of a sound pack. For a 30-second promo, 8–20 cues is typical.

Grouped motion gets one sound, not one per element: a list of five items popping in quickly can share one textured sound, or use a soft tick on each with decreasing gain.

## 3. Choosing sounds: palette and mapping

Pick a palette from the brand's character, then use it consistently:

| Brand feel | Palette |
|---|---|
| Clean tech / SaaS | soft clicks, ticks, airy swishes, gentle chimes; no booms |
| Premium / luxury | low soft impacts, slow whooshes, sparkles used sparingly, room reverb |
| Playful / kids / consumer app | pops, bubbly blips, boings, bright chimes, pitch variation |
| Bold / sports / trailer | hits, risers into impacts, deep booms, glitches |
| Corporate / finance | very few sounds: subtle ticks, one soft whoosh per transition |

Typical mapping (starting points; synthesize with `sfx_synth.py <recipe>`):

| Visual event | Sound | Align |
|---|---|---|
| Element slides in fast | `swish` | hit at the moment it stops |
| Full-screen transition, camera move | `whoosh` | hit at the transition midpoint |
| Shape / icon appears with scale-up | `pop` | hit when it reaches full size |
| Card lands, soft UI | `tap` | hit on landing |
| Button press, toggle, cursor click | `click` | hit on the press frame |
| Counter / list step | `tick` | hit on each change |
| Text typing on | `typing` with `--count` = characters, `--rate` = chars/s | start with the first character |
| Logo or hero reveal | `riser` ending into `impact` | riser align `end`, impact align `hit`, same event time |
| Bold text slam | `hit` | hit on contact |
| Success / complete | `chime` or `ding` | hit when the checkmark completes |
| Tech transition, error | `glitch`, `error` | hit at the cut |
| Shine, premium highlight | `sparkle` | start as the shine begins |
| Screenshot, photo | `shutter` | hit at the flash |

Realistic Foley (footsteps, glass, liquid, cloth, specific machines) is beyond simple synthesis. Use the user's library or ElevenLabs for those.

## 4. Getting the files

**The user's library** (preferred when they have one):

```bash
python3 "<skill>/scripts/sfx_library.py" index "/path/to/SFX"            # once; re-run after adding files
python3 "<skill>/scripts/sfx_library.py" search "/path/to/SFX/sfx_index.json" "soft whoosh" --max-ms 900
```

Copy the chosen files into `video/public/sfx/` (keep originals untouched) and note their licence in `final/credits.txt`. Files without licence information must be confirmed by the user before delivery.

**Synthesis** (free, offline, deterministic; best for UI and abstract motion):

```bash
python3 "<skill>/scripts/sfx_synth.py" --list
python3 "<skill>/scripts/sfx_synth.py" pop --variations 4 --out video/public/sfx/
python3 "<skill>/scripts/sfx_synth.py" whoosh --length 1.4 --pitch -5 --out video/public/sfx/whoosh-slow.wav
```

`--pitch` (semitones) changes size and weight: lower = bigger/heavier, higher = smaller/lighter. `--length` stretches build-ups and tails. Same seed = same file, so results are reproducible.

**ElevenLabs** (paid, the user's key, approval first; best for realistic or very specific sounds):

```bash
python3 "<skill>/scripts/sfx_generate.py" --prompt "..." --duration 1.0 --variations 3 --out-dir video/public/sfx   # plan only
python3 "<skill>/scripts/sfx_generate.py" ... --yes                                                                 # after the user agrees
```

Show the user the plan (number of requests, prompts) before `--yes`. Generate 2–3 variations of a key sound and pick by listening; don't generate dozens. The script records prompts and settings in `sfx_manifest.json`.

**Finishing any file:** `sfx_analyze.py FILE` shows onset, hit, tail and leading silence; `--trim OUT.wav` removes silence and long tails with a short fade. Short, dry sounds sit better in motion graphics than long reverberant ones.

## 5. Placing cues precisely

The cue sheet names the visual event time and lets the script work out when the file must start:

```json
{ "fps": 30, "public_dir": ".", "cues": [
  { "id": "logo-build", "t": 3.0, "file": "sfx/riser.wav",  "gain_db": -12, "align": "end" },
  { "id": "logo-land",  "t": 3.0, "file": "sfx/impact.wav", "gain_db": -6,  "align": "hit" },
  { "id": "cta",        "frame": 240, "file": "sfx/click.wav", "gain_db": -10 }
]}
```

- `t` comes from the same numbers that time the animation: scene start + the element's delay + its settle time. For springs, the visual "arrival" is roughly when the value first reaches ~95%; render a still or two around that frame to confirm.
- `align: "hit"` puts the audible hit (first moment within 3 dB of the loudest point) on the event. Whooshes swell, so their hit sits mid-file; impacts hit immediately.
- `nudge_ms`: sound 0–20 ms early feels in sync; late sound feels wrong quickly. Nudge with negative values when in doubt.
- `prepare` writes `start_s` for Remotion and warns about: missing files, cues before 0, tails past the end, hits closer than 50 ms, the same file back to back, more than ~4 cues per second, and a cue landing inside a louder sound (likely masked).
- Captions: `sfx_cues.py from-captions public/captions.json --file sfx/tick-1.wav --file sfx/tick-2.wav --out public/sfx_cues_caps.json --every phrase` creates one cue per phrase (or per word), rotating variations. Keep these very quiet (−20 dB or lower) under a voice.

## 6. Layering and variation

- A big moment usually has three layers: a transient (click/crack) for timing, a body (thump/tone) for weight, a tail (air/reverb) for space. Place them as separate cues at the same `t` and balance with `gain_db`.
- Riser → impact: riser `align: "end"` and impact `align: "hit"` at the same `t`; drop the music or leave a few frames of near-silence before the hit to make it land harder.
- Repeated events (list items, caption pops, ticks) need variations: `--variations 3–4` from synthesis, or several takes from the library, rotated. Small pitch differences (±1–2 semitones) also help.
- Match the stereo picture to motion when it matters: left-to-right movement can use a panned sound (`ffmpeg -i in.wav -af "pan=stereo|c0=1.0*c0|c1=0.4*c0" out.wav` for left-heavy).
- Keep low-frequency booms rare; they eat headroom and get lost on phone speakers anyway. Add a click or crack layer so a boom is audible on small speakers.

## 7. Checking the mix

```bash
python3 "<skill>/scripts/sfx_cues.py" mix public/sfx_cues.json ../out/sfx-stem.wav --duration 30                 # the effects alone
python3 "<skill>/scripts/sfx_cues.py" mix public/sfx_cues.json ../out/preview-mix.wav --bed public/vo.wav --bed public/music.mp3 --duration 30
python3 "<skill>/scripts/sfx_cues.py" check public/sfx_cues.json --bed ../out/bed.wav                             # bed = voice+music without SFX
```

- `check` compares each cue's short-term level with the bed at its hit. "MASKED" means it will likely vanish: raise its gain, choose a brighter sound (more high frequencies cut through music), or move it away from a loud word.
- Typical relative levels: UI ticks and clicks well under the voice; transitions just under the music peaks; hero impacts may briefly be the loudest thing. Don't let effects cover consonants of important words.
- Make the bed by rendering with SFX off (`sfxCuesFile: ""`) and extracting audio: `ffmpeg -i out/nosfx.mp4 -vn out/bed.wav`.
- Then render a draft with audio and listen, or ask the user to listen on a phone speaker and on headphones. Measurements predict audibility; only listening confirms taste and sync. Report it that way.

## 8. Prompting ElevenLabs

Describe the sound, not the scene. A useful order: **source/material → action → character → space/perspective → length**.

| Weak | Better |
|---|---|
| "logo sound" | "Deep cinematic impact, short sub boom with a bright metallic crack on top, dry, no reverb tail, 1.5 seconds" |
| "whoosh" | "Fast airy whoosh passing left to right, smooth, clean, no tonal elements, 0.6 seconds" |
| "button" | "Single soft plastic UI click, close microphone, very short, dry" |
| "magic" | "Delicate glittering sparkle, high chimes with fast decay, gentle, 1 second" |

- Set `--duration` for timing-critical sounds; leave it out for natural-length sounds.
- `--influence` 0.3 (default) gives variety; 0.6–0.8 follows the words more literally.
- `--loop` for ambiences and hums that must repeat seamlessly.
- Ask for "dry", "no music", "no voice" when that's what you need; models sometimes add musical elements to vague prompts.
- After generating, run `sfx_analyze.py` and trim; generated files often carry leading silence or long tails.
- Usage rights for generated audio depend on the user's ElevenLabs plan; record the plan in `final/credits.txt`.
