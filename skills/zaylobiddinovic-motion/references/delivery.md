# Delivery and QA

## 1. Platform presets

Platform limits change; when length or file size matters, check the platform's current help page.

| Platform | Size | fps | Notes |
|---|---|---|---|
| YouTube | 1920×1080 or 3840×2160 | source fps (24/25/30/60) | H.264 high profile, CRF 16–18; upload SRT separately |
| YouTube Shorts / Reels / TikTok | 1080×1920 | 30 (or 60 for gameplay/screen) | Burned-in captions, UI safe zones, hook in the first 2 s |
| Instagram / LinkedIn feed | 1080×1350 (4:5) or 1080×1080 | 30 | Center-weighted layout; may be shown muted, so captions matter |
| X / Twitter | 1920×1080 or 1080×1350 | 30 | Keep files small; H.264 + AAC |
| Website hero loop | 1920×1080 | 24–30 | Muted, seamless loop, small file: CRF 23–26, also export WebM VP9 |
| Editing hand-off / overlay | source size | source fps | ProRes 422 HQ, or ProRes 4444 for alpha |

Standard final export (H.264, broad compatibility):

```bash
npx remotion render <Comp> final/<name>-v1.mp4 --codec=h264 --crf=18 --pixel-format=yuv420p --audio-codec=aac
```

Web loop as WebM:

```bash
npx remotion render <Comp> final/<name>-loop-v1.webm --codec=vp9 --crf=30 --muted
```

Re-encoding a finished FFmpeg edit for upload:

```bash
ffmpeg -i out/edit.mp4 -c:v libx264 -profile:v high -crf 18 -preset slow -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 256k -ar 48000 final/<name>-v1.mp4
```

`-movflags +faststart` lets web players start before the file finishes downloading.

## 2. QA checklist

Run through this before calling something final. Report each item as **measured** (a tool said so), **checked by eye** (you inspected stills/sheets), or **not checked** (needs human listening, etc.).

**Technical** (`probe_media.py`, `loudness.py`)
- [ ] Resolution, aspect ratio and fps match the brief
- [ ] Duration matches the brief / platform limit
- [ ] H.264 + yuv420p (or the requested codec); audio AAC 48 kHz
- [ ] Integrated loudness and true peak within target
- [ ] No black frames at the start or end unless intended

**Visual** (stills at key frames + contact sheet)
- [ ] Every text is inside safe margins and readable at phone size
- [ ] No overlaps, clipped words, widows, or typos (read every on-screen string)
- [ ] Captions match the speech, stay out of platform UI zones
- [ ] Brand colours, logo and fonts are correct
- [ ] Transitions land cleanly; no flash frames between scenes

**Sound** (needs a human ear for the final say)
- [ ] Voice intelligible over music throughout
- [ ] Sound effects land on their visual moments
- [ ] No clicks at cuts, no abrupt music ending

**Rights**
- [ ] `final/credits.txt` lists every third-party font, track, SFX and clip with source and licence

## 3. Handing over

Put deliverables in `final/` with version numbers, never overwriting an approved version:

```
final/
  brand-reel-v3.mp4
  brand-reel-v3.srt
  credits.txt
```

In the hand-off message, give the file paths, the specs (size, fps, length, loudness), what you verified and how, and anything the user should still check themselves (usually: listen on a phone speaker and on headphones).
