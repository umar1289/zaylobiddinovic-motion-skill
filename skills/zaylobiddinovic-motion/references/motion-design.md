# Motion design

Use this when deciding how things look and move. These are defaults; a brand guide or the user's references override them.

## Contents
1. Timing
2. Easing
3. Hierarchy and choreography
4. Typography
5. Colour
6. Layout and safe areas
7. Pacing by video type
8. Amateur tells to avoid

## 1. Timing

Durations at 30 fps; scale proportionally for other rates.

| Motion | Duration |
|---|---|
| Small UI element in/out, icon pop | 6–10 frames (0.2–0.33 s) |
| Headline entrance | 12–20 frames |
| Full-screen transition | 12–24 frames |
| Stagger between list items / words | 2–5 frames per word, 6–12 per list item |
| Hold a line of text so it can be read | ≈ 0.3 s per word + 1 s, never under 1.5 s |
| Logo sting | 2–4 s total |

Exits are shorter than entrances (about two-thirds) because the viewer's attention is already moving on.

## 2. Easing

- Linear motion looks mechanical. Use it only for constant things: scrolling tickers, rotating backgrounds, progress bars tied to real time.
- Entrances: ease-out (fast start, soft stop), e.g. `Easing.bezier(0.16, 1, 0.3, 1)` or `spring({ damping: 200 })`.
- Exits: ease-in (slow start, fast leave), e.g. `Easing.bezier(0.7, 0, 0.84, 0)`.
- Moving from A to B on screen: ease-in-out, e.g. `Easing.bezier(0.65, 0, 0.35, 1)`.
- Overshoot (bouncy springs) suits playful brands, buttons and icons; keep it off body text and serious topics.

## 3. Hierarchy and choreography

- One focal point at a time. If two things animate together, one leads and the other follows 3–6 frames later.
- Order of arrival = order of reading: headline → support line → detail → call to action.
- Move things along a consistent direction within a video (e.g. content enters from the right, leaves to the left) so cuts feel connected.
- Group related elements and animate the group, rather than every element doing its own trick.
- Leave a beat of stillness (0.5–1 s) after a key message lands before the next change.
- Continuous subtle motion (slow drift, parallax, gentle scale of 1.00→1.04 over a scene) keeps static scenes alive without distracting.

## 4. Typography

- Two typefaces at most; usually one family in two or three weights is enough.
- Minimum on-screen text size: about 4% of frame height for body text on mobile (≈ 75 px at 1920 tall), headlines 7–12%.
- Tighten letter spacing slightly on large bold headlines (−1% to −3%); loosen small caps and labels (+5% to +10%).
- Line length under ~35 characters for video headlines; break lines by meaning, not by width ("Make videos / with code", not "Make videos with / code").
- Contrast: light text on dark or vice-versa, at least 4.5:1. Over footage, add a gradient scrim, text shadow, or outline.
- Check the font covers every character you need (Uzbek Latin oʻ/gʻ use U+02BB; Cyrillic needs a Cyrillic subset).

## 5. Colour

- Pick a background, a text colour, one accent and one muted neutral. Most frames should be ~70% background, ~25% text/neutral, ~5% accent.
- Reserve the accent for what the viewer should look at: the key word, the button, the active caption word.
- Dark backgrounds feel premium/tech and hide compression banding less well, so add a subtle gradient or grain rather than a flat colour on big areas.
- Match footage: sample colours from the footage or product for graphics that sit on top of it.

## 6. Layout and safe areas

- Keep important content inside an 8% margin on all sides (title-safe).
- Vertical social (9:16): keep text out of the bottom ~25% and the right ~12% (captions, buttons, usernames) and the top ~10%.
- Square/4:5 feed: keep the centre 80% for anything critical; previews may crop to 4:5 or 1:1.
- Design for the smallest format first if a video ships in several aspect ratios, then let wider formats breathe.
- Align to a few strong lines (left edge, centre line), not dozens of slightly different positions.

## 7. Pacing by video type

| Type | Pacing |
|---|---|
| Social reel / ad (≤ 30 s) | Hook in the first 1–2 s (the payoff or a bold claim), a cut or change every 1.5–3 s, CTA in the last 2–3 s |
| Product promo (30–90 s) | Problem → product → 3 key benefits → proof → CTA; one benefit per scene |
| Explainer (1–3 min) | Follows the voiceover; one idea per scene; visuals illustrate the sentence being spoken, never a different one |
| Logo sting / intro | 2–4 s; build-up, reveal, short hold |
| Talking head edit | Cut dead air and false starts, punch-in (scale 1.0→1.15) on emphasis, captions on |

## 8. Amateur tells to avoid

- Everything animating at once with the same duration and easing.
- Every element bouncing.
- Different transition styles at every cut.
- Text too small for a phone, or held too briefly to read.
- Drop shadows and glows on everything.
- Content in the platform UI zones.
- Motion that does not relate to the message (spinning for no reason).
- Music louder than the voice, or SFX on every single movement.
