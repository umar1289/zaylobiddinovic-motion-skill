# Audio: voice, music, sound effects

Viewers forgive rough visuals faster than bad sound. Priorities, in order: the voice is clear → the music supports without competing → sound effects make key moments feel physical.

## 1. Sources and rights

- Use only audio the user supplies or that is clearly licensed for this use (royalty-free libraries the user subscribes to, CC0/public domain, or the user's own recordings). Record the source and licence of every file in `final/credits.txt`.
- Don't pull a track from a reference video or a streaming service. "No copyright" uploads on video sites are not a licence.
- No music unless the brief asks for it or the user agrees; some videos (tutorials, interviews) are better without.

## 2. Voiceover

Options, in order of preference: the user's own recording → a TTS service the user chooses and pays for (ElevenLabs, OpenAI, etc.) → a temporary guide track the user explicitly accepts.

- A paid TTS call needs the user's approval, the user's own API key in an environment variable, and an agreed script. Never print the key.
- Remotion has `@remotion/elevenlabs` and `@remotion/openai-whisper` helpers; a plain HTTPS request from a small script also works.
- Clean-up chain for a home recording (in this order): high-pass ~80 Hz → light denoise → gentle compression → loudness normalize.
  `ffmpeg -i vo.wav -af "highpass=f=80,afftdn=nf=-25,acompressor=threshold=-18dB:ratio=3:attack=10:release=150" out/vo-clean.wav`
- Lock the voiceover before final animation timing; transcribe it for word timestamps (`captions.md`).

## 3. Music

- Choose by energy curve, not genre: does it build where the video builds?
- Cut on the beat. At tempo B BPM and F fps, one beat = `F * 60 / B` frames (120 BPM at 30 fps = 15 frames). Ask the user for the BPM or measure it from the waveform in a DAW; place major scene changes on downbeats (every 4 beats).
- Start/end: fade in 0.3–1 s unless the track has a clean start; end on the track's natural ending or a 1–2 s fade.
- Under a voice, music sits roughly 15–20 dB below the voice.

## 4. Mixing in Remotion

```tsx
import { Audio, interpolate, Sequence, staticFile } from "remotion";
import { SfxTrack } from "./components/SfxTrack";

// Duck music to 15% while the voice speaks (voice from 2 s to 20 s at 30 fps), with 0.5 s ramps.
const musicVolume = (f: number) =>
  interpolate(f, [0, 15, 45, 60, 600, 615], [0, 0.6, 0.6, 0.15, 0.15, 0.6], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

<Audio src={staticFile("music.mp3")} volume={musicVolume} />
<Sequence from={60}><Audio src={staticFile("vo.wav")} /></Sequence>
<SfxTrack cuesFile="sfx_cues.json" />  {/* sound effects from the prepared cue sheet, see sound-design.md */}
```

Derive duck points from the voiceover's caption timings instead of typing them by hand when there are many phrases.

## 5. Sound effects

Sound effects have their own guide: `sound-design.md` (spotting, palettes, the cue sheet, synthesis, library search, ElevenLabs prompting and audibility checks). In short: few, meaningful sounds; the audible hit on the visual event; variations for repeats; check them against the voice and music bed.

## 6. Loudness targets

| Destination | Integrated | True peak |
|---|---|---|
| YouTube, Instagram, TikTok, most web | −14 LUFS | −1 dBTP |
| Podcasts / voice-only | −16 LUFS | −1 dBTP |
| Broadcast (EBU R128) | −23 LUFS | −1 dBTP |

```bash
python3 "<skill>/scripts/loudness.py" measure final/promo-v1.mp4
python3 "<skill>/scripts/loudness.py" normalize final/promo-v1.mp4 final/promo-v1-14lufs.mp4 --target -14
```

Normalize the final mix, not individual stems, and measure again after. Integrated loudness says nothing about whether the voice is intelligible over the music, so listen or ask the user to listen.
