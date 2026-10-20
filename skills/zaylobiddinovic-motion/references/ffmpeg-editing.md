# Editing footage with FFmpeg

Work on copies. Read originals from `assets/` and write to `out/` or `final/`; never pass the same path as input and output. Run `scripts/probe_media.py` on every source first, since fps, resolution, rotation and audio layout decide which recipe is safe.

## Contents
1. Trimming
2. Joining
3. Reframing (16:9 ↔ 9:16 ↔ 1:1)
4. Speed, freeze, reverse
5. Transitions between clips
6. Overlays, logos, burned-in subtitles
7. Audio operations
8. Finding cuts automatically (silence, scenes)
9. Proxies and normalizing mixed sources
10. When to switch to Remotion

## 1. Trimming

```bash
# Frame-accurate (re-encodes). -ss after -i = exact; -t is duration.
ffmpeg -i in.mp4 -ss 00:00:12.40 -t 8.5 -c:v libx264 -crf 18 -preset medium -c:a aac -b:a 192k out/clip.mp4
# Fast, no quality loss, but cuts snap to the nearest keyframe before -ss.
ffmpeg -ss 12.4 -i in.mp4 -t 8.5 -c copy out/clip-fast.mp4
```

Use stream copy only for rough cuts or when the user accepts keyframe snapping.

## 2. Joining

Same codec, resolution, fps and audio layout (e.g. clips from one camera):

```bash
printf "file '%s'\n" out/a.mp4 out/b.mp4 out/c.mp4 > out/list.txt
ffmpeg -f concat -safe 0 -i out/list.txt -c copy out/joined.mp4
```

Mixed sources: normalize first (section 9), or use the concat filter, which re-encodes:

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];\
  [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];\
  [0:a]aresample=48000[a0];[1:a]aresample=48000[a1];\
  [v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac out/joined.mp4
```

## 3. Reframing

```bash
# 16:9 → 9:16 centre crop (subject in the middle)
ffmpeg -i in.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1" -c:a copy out/vertical.mp4
# Off-centre subject: shift the crop. x is the left edge in source pixels.
ffmpeg -i in.mp4 -vf "crop=ih*9/16:ih:x=820:y=0,scale=1080:1920,setsar=1" -c:a copy out/vertical.mp4
# Keep the whole frame on a blurred, filled background
ffmpeg -i in.mp4 -filter_complex \
 "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:2[bg];\
  [0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1" -c:a copy out/vertical-blur.mp4
# 16:9 → 1:1 centre crop
ffmpeg -i in.mp4 -vf "crop=ih:ih,scale=1080:1080,setsar=1" -c:a copy out/square.mp4
```

When the subject moves across the frame, a fixed crop will lose it. Make a contact sheet, find where the subject is over time, and either cut the clip into pieces with different `x`, or do the reframe in Remotion where `x` can be animated with `interpolate`.

## 4. Speed, freeze, reverse

```bash
# 2× speed (video and audio). atempo accepts 0.5–100; chain for more.
ffmpeg -i in.mp4 -filter_complex "[0:v]setpts=PTS/2[v];[0:a]atempo=2[a]" -map "[v]" -map "[a]" out/fast.mp4
# 0.5× slow motion (frames are duplicated; for smooth slow-mo add minterpolate=fps=60, slow)
ffmpeg -i in.mp4 -filter_complex "[0:v]setpts=PTS*2[v];[0:a]atempo=0.5[a]" -map "[v]" -map "[a]" out/slow.mp4
# Freeze: first 3 s, then hold the last frame for 2 s (concat with the remainder afterwards)
ffmpeg -t 3 -i in.mp4 -vf "tpad=stop_mode=clone:stop_duration=2" -an out/a-freeze.mp4
# Reverse (loads the clip into memory; keep it short)
ffmpeg -i in.mp4 -vf reverse -af areverse out/reversed.mp4
```

## 5. Transitions between clips

Both inputs must share resolution, fps and pixel format. `offset` = first clip length − transition length.

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5,format=yuv420p[v];\
  [0:a][1:a]acrossfade=d=0.5[a]" -map "[v]" -map "[a]" out/ab.mp4
```

Other `transition=` values: `wipeleft`, `slideleft`, `circleopen`, `dissolve`, `smoothleft`, `fadeblack`. Hard cuts are the default in good editing; use transitions to mark a change of place, time or topic.

## 6. Overlays, logos, burned-in subtitles

```bash
# Logo top-right: 20% of video width, 4% margin ([1:v] is scaled relative to [0:v] via rw)
ffmpeg -i in.mp4 -i logo.png -filter_complex \
 "[1:v][0:v]scale=w=rw*0.2:h=-1[l];[0:v][l]overlay=W-w-W*0.04:H*0.04" -c:a copy out/logo.mp4
# Burn an SRT. Needs FFmpeg built with libass: check `ffmpeg -filters | grep subtitles`; if absent, render captions in Remotion
ffmpeg -i in.mp4 -vf "subtitles=captions.srt:force_style='FontName=Inter,FontSize=18,Outline=2,MarginV=60'" -c:a copy out/subbed.mp4
# Soft subtitles (selectable track, no re-encode)
ffmpeg -i in.mp4 -i captions.srt -c copy -c:s mov_text out/softsub.mp4
```

For styled, animated, word-by-word captions use Remotion instead (`captions.md`).

## 7. Audio operations

```bash
ffmpeg -i in.mp4 -vn -c:a pcm_s16le -ar 48000 out/voice.wav                       # extract
ffmpeg -i in.mp4 -i new.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest out/x.mp4  # replace
ffmpeg -i in.mp4 -an -c:v copy out/silent.mp4                                       # remove
ffmpeg -i in.mp4 -af "afade=t=in:d=0.3,afade=t=out:st=9.5:d=0.5" -c:v copy out/x.mp4    # fades
ffmpeg -i in.mp4 -af "highpass=f=80,afftdn=nf=-25" -c:v copy out/cleaner.mp4         # rumble + light denoise
```

Mixing music under voice with ducking and loudness targets: `audio.md`.

## 8. Finding cuts automatically

```bash
# Silences longer than 0.5 s below −35 dB (candidate jump cuts for talking heads)
ffmpeg -i in.mp4 -af silencedetect=noise=-35dB:d=0.5 -f null - 2>&1 | grep silence_
# Scene changes (score 0–1; 0.3 is a reasonable start)
ffmpeg -i in.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep -o "pts_time:[0-9.]*"
```

Turn the silence list into keep-ranges, leave ~0.1 s of padding around speech so words aren't clipped, then trim and concat. Show the user the proposed cut list (or a contact sheet of cut points) before rendering a long edit.

## 9. Proxies and mixed sources

Phones record variable frame rate and sometimes rotation metadata; screen recordings may be 60 fps; cameras 23.976/25. Normalize everything once before editing:

```bash
ffmpeg -i src.mov -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p" \
  -c:v libx264 -crf 18 -preset medium -c:a aac -ar 48000 -ac 2 out/norm/src.mp4
```

For 4K sources, make 720p proxies for previews and run the final render against the originals.

## 10. When to switch to Remotion

Move the edit into Remotion when you need animated graphics, text that moves, captions with per-word styling, a crop that tracks a subject, many layered elements, or easy re-timing from a storyboard. Put normalized clips in `public/` and sequence them with `<Series>` + `<OffthreadVideo trimBefore trimAfter>`.
