# Captions

Captions do two jobs: accessibility (people watch muted) and pacing (word-by-word captions add energy to talking heads). Plan for both.

## 1. Get word timings

**From speech (most common):**

```bash
python3 "<skill>/scripts/check_env.py"                 # is a Whisper engine installed?
# if not, ask the user, then:  pip install faster-whisper
python3 "<skill>/scripts/transcribe.py" assets/talk.mp4 --out video/public/captions.json --srt final/talk.srt --model small --language en
```

- Model choice: `small` is a good default; `medium`/`large-v3` for accents, noisy audio or non-English (Uzbek and other lower-resource languages benefit from `large-v3`). The engine downloads the model on first use (small ≈ 0.5 GB, large-v3 ≈ 3 GB); tell the user before running.
- Pass `--language` when you know it; auto-detect can mislabel short clips.
- The script prints low-confidence words. Read them, compare with the user's script if there is one, and fix `captions.json` by hand: correct `text`, keep the timings.
- Existing Whisper JSON from another tool: `--from-json whisper.json`.

**From a known script with no audio yet:** write `captions.json` by hand with estimated timings (≈ 2.5 words per second for normal speech), and replace it once the voiceover is recorded.

**Format** (`@remotion/captions` `Caption[]`), one entry per word, times in milliseconds, a leading space on every word except the first:

```json
[{ "text": "Hello", "startMs": 100, "endMs": 400, "timestampMs": 250, "confidence": 0.98 },
 { "text": " world", "startMs": 450, "endMs": 800, "timestampMs": 625, "confidence": 0.95 }]
```

## 2. Render them

The starter's `CaptionedVideo` composition loads `public/<captionsFile>` in `calculateMetadata`, sets the duration to the speech, and draws pages with the active word highlighted:

```bash
npx remotion render CaptionedVideo final/talk-captioned-v1.mp4 --props='{"videoFile":"talk.mp4","captionsFile":"captions.json"}'
```

`createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds })` groups words into pages. Lower values (400–800 ms) show 1–3 words at a time (high energy, reels); higher values (1200–2000 ms) show full phrases (calmer, explainers).

Match the footage: pass its size and length from `probe_media.py`, e.g. `--props='{"videoFile":"talk.mp4","captionsFile":"captions.json","width":1920,"height":1080,"durationSeconds":42.5}'`. Without them the output is 1080×1920 (footage cropped by `objectFit: cover`) and ends 0.6 s after the last word. If the footage is not 30 fps, change `FPS` in `Root.tsx`.

## 3. Style options

Change `src/components/Captions.tsx` to match the brief:

| Style | How |
|---|---|
| Karaoke highlight (starter default) | Active token gets the accent colour |
| Word pop | Each token scales from 0.8 → 1 with a short spring when its `fromMs` arrives |
| One word at a time | `combineWithinMs` ≈ 0, big centred text |
| Boxed | Background pill behind the page; good over busy footage |
| Lower-third sentences | Calm, smaller, bottom-left, for interviews and documentaries |

Keep: maximum two lines, 84% width or less, an outline/shadow/box for contrast, and the vertical-video safe zone (above the bottom ~25%). Emphasize key words (numbers, product names) with the accent colour or a weight change, and only a few per sentence.

## 4. Platform files

- Upload `.srt` separately where the platform supports it (YouTube, LinkedIn, Facebook) — it is searchable and viewers can turn it off.
- Burn captions into the picture for Reels/TikTok/Shorts, where styled captions are expected.
- `transcribe.py --srt` groups up to 7 words per line, breaking on pauses. Edit long lines by hand.

## 5. Languages and scripts

- Load a font subset that covers the language (`subsets: ["latin", "latin-ext", "cyrillic"]`). Uzbek Latin uses ʻ (U+02BB) in oʻ and gʻ; check the font renders it, and don't let it be replaced by an apostrophe.
- Right-to-left languages (Arabic, Persian, Hebrew): set `direction: "rtl"` on the caption container and test word order on a still.
- Translating captions: translate per line, then retime by distributing the original line's span across the translated words. Tell the user that translated timings are approximate.
