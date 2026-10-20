# Remotion guide

Patterns verified against Remotion 4.0.5xx. If the project pins another version, check its `node_modules/remotion` types before relying on a prop name.

## Contents
1. Mental model
2. Animating values
3. Arranging time
4. Transitions
5. Media
6. Fonts and text
7. Data-driven videos
8. Rendering from the CLI
9. Common errors

## 1. Mental model

A composition is a React component plus `width`, `height`, `fps`, `durationInFrames`. Remotion renders frame N by mounting the component with `useCurrentFrame() === N` and taking a screenshot. Frames render in parallel, out of order, in separate tabs, so a frame must be a pure function of (frame number, props).

```tsx
const frame = useCurrentFrame();
const { fps, width, height, durationInFrames } = useVideoConfig();
```

Register compositions in `src/Root.tsx`; the entry `src/index.ts` calls `registerRoot`.

## 2. Animating values

**interpolate:** map a frame range to a value range. Clamp unless you want overshoot past the ends.

```tsx
import { Easing, interpolate } from "remotion";
const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
const x = interpolate(frame, [10, 40], [-200, 0], {
  easing: Easing.bezier(0.16, 1, 0.3, 1), // fast start, soft landing
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});
```

Multi-stop: `interpolate(frame, [0, 10, 50, 60], [0, 1, 1, 0])` gives fade in, hold, fade out.

**spring:** physical motion from 0 to 1. Feed it into `interpolate` for any range.

```tsx
const s = spring({ frame: frame - 12, fps, config: { damping: 200 } }); // starts at frame 12, no bounce
const scale = interpolate(s, [0, 1], [0.8, 1]);
```

| Feel | config |
|---|---|
| Smooth, no overshoot (UI, text) | `{ damping: 200 }` |
| Snappy with a small bounce (buttons, icons) | `{ damping: 12, stiffness: 140 }` |
| Heavy, slow settle (big shapes) | `{ damping: 20, stiffness: 60, mass: 2 }` |

`durationInFrames` on `spring` stretches it to an exact length when timing must hit a beat.

**Randomness:** `random("star-" + i)` returns the same 0–1 value every render. Use it for particle positions, jitter and noise.

**Exit animations:** compute from the end: `const outStart = durationInFrames - 15;`.

## 3. Arranging time

- `<Sequence from={30} durationInFrames={60}>` shifts time for its children: inside, `useCurrentFrame()` starts at 0. Add `premountFor={fps}` when children load media, so it is ready before it appears. `layout="none"` stops it from wrapping children in an `AbsoluteFill`.
- `<Series>` puts `<Series.Sequence durationInFrames>` items back to back; `offset` overlaps or gaps them.
- `<Loop durationInFrames={30}>` repeats children; `<Freeze frame={10}>` holds one frame.
- Keep scene lengths in one place (the starter's `src/storyboard.ts`) and derive the composition duration from them, so changing a scene never desyncs the total.

## 4. Transitions

`@remotion/transitions` overlaps two sequences and blends them.

```tsx
import { linearTiming, springTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><SceneA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={springTiming({ config: { damping: 200 } })} />
  <TransitionSeries.Sequence durationInFrames={90}><SceneB /></TransitionSeries.Sequence>
</TransitionSeries>
```

Total length = sum of sequences minus sum of transition lengths. Presets in this version include `fade`, `slide`, `wipe`, `flip`, `clock-wipe`, `iris`, `push-cut`, `zoom-in-out`, `dissolve`, `cross-zoom`, `blur-slide` and more (import path `@remotion/transitions/<name>`, export name in camelCase). Prefer one or two transition types per video; a different transition at every cut looks like a template demo.

## 5. Media

Put files in `public/` and reference them with `staticFile("name.ext")`. Remote URLs work but make renders depend on the network.

```tsx
import { Audio, Img, OffthreadVideo, staticFile } from "remotion";
<OffthreadVideo src={staticFile("clip.mp4")} trimBefore={fps * 2} trimAfter={fps * 8} muted />
<Img src={staticFile("logo.png")} />
<Audio src={staticFile("music.mp3")} volume={(f) => interpolate(f, [0, 30], [0, 0.6], { extrapolateRight: "clamp" })} />
```

- `trimBefore`/`trimAfter` (frames) replaced the deprecated `startFrom`/`endAt`.
- `playbackRate` changes speed; `volume` accepts a number or a per-frame function (use it for fades and ducking; see `audio.md`).
- `<OffthreadVideo>` extracts exact frames with FFmpeg and is the safe default for rendering. Use `objectFit: "cover"` to fill a different aspect ratio.
- Transparent overlays: render ProRes 4444 (see section 8) or use WebM VP9 with alpha.
- SVG and CSS shapes scale cleanly; `@remotion/shapes` and `@remotion/paths` help with drawn-on lines (`evolvePath`).

## 6. Fonts and text

```tsx
import { loadFont } from "@remotion/google-fonts/Montserrat";
const { fontFamily } = loadFont("normal", { weights: ["600", "800"], subsets: ["latin", "cyrillic"] });
```

Include `cyrillic` / `latin-ext` subsets when text uses Uzbek Cyrillic, Russian, Turkish etc. Local font files: `@remotion/fonts` `loadFont({ family, url: staticFile("Brand.woff2") })`.

Fitting text: `measureText` / `fitText` from `@remotion/layout-utils` (install it when needed) to size a headline to a box. Measure after the font loads.

Per-word or per-letter animation: split the string, give each piece its own delay (`frame - i * 3`), keep `display: inline-block` so transforms apply.

## 7. Data-driven videos

- Default props live on `<Composition defaultProps>`; override at render time with `--props='{"headline":"Hi"}'` or `--props=./props.json`. This is how one template renders many variants.
- `calculateMetadata` runs before rendering and may be async: load JSON, measure a voiceover's length, and return `{ durationInFrames, props, width, height }`. The starter's `CaptionedVideo` uses it to load captions and size the duration to the speech.
- Audio length: `parseMedia` from `@remotion/media-parser` (`fields: { durationInSeconds: true }`) or `getAudioDurationInSeconds` from `@remotion/media-utils`.

## 8. Rendering from the CLI

```bash
npx remotion compositions                                   # list ids, sizes, durations
npx remotion studio                                          # interactive preview at localhost:3000
npx remotion still Promo out/f90.png --frame=90              # one frame
npx remotion render Promo out/draft.mp4 --scale=0.5          # half-size draft
npx remotion render Promo out/part.mp4 --frames=60-149       # a range
npx remotion render Promo final/promo-v1.mp4 --codec=h264 --crf=18
npx remotion render Promo final/promo-v1.mov --codec=prores --prores-profile=4444 --image-format=png --pixel-format=yuva444p10le   # with alpha
npx remotion render Promo out/x.mp4 --props=./variant.json
```

Useful flags: `--concurrency=50%` (lower if the machine struggles), `--muted`, `--audio-codec=aac`, `--every-nth-frame` (GIF), `--log=verbose` for debugging. `--crf` lower = better/larger; 18 is visually lossless for H.264.

## 9. Common errors

| Symptom | Cause / fix |
|---|---|
| Flicker or different results between renders | Time-based code (CSS animation, `Math.random`, `Date`, state carried across frames). Derive from `useCurrentFrame()` |
| Text jumps on first frames | Font not loaded; use `@remotion/google-fonts`/`@remotion/fonts` |
| "A delayRender() was called but not cleared" | An async load never finished or threw; check the URL, call `continueRender` in `finally`, or move the work into `calculateMetadata` |
| Video frame black or offset | Use `<OffthreadVideo>`; check `trimBefore` is in frames, not seconds |
| Element appears late inside `<Sequence>` | Its frame is relative to the sequence start; don't subtract the offset twice |
| Render is very slow | Large images: downscale in `public/`; heavy blur/shadow filters; try `--concurrency` and `--scale` for drafts |
| `staticFile` 404 | File must be inside `public/`; names are case-sensitive |
