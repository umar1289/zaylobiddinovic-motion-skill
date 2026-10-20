import { createTikTokStyleCaptions, type Caption, type TikTokPage } from "@remotion/captions";
import { useMemo } from "react";
import { AbsoluteFill, Sequence, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { useUnit } from "./useUnit";

type Props = {
  captions: Caption[];
  // Tokens closer together than this are shown on the same page. Lower = fewer words on screen.
  combineWithinMs?: number;
};

// Renders caption "pages" in sequence; the word being spoken is highlighted.
export const Captions: React.FC<Props> = ({ captions, combineWithinMs = 1200 }) => {
  const { fps } = useVideoConfig();
  const { pages } = useMemo(
    () => createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds: combineWithinMs }),
    [captions, combineWithinMs],
  );

  return (
    <AbsoluteFill>
      {pages.map((page, i) => {
        const next = pages[i + 1];
        const from = Math.round((page.startMs / 1000) * fps);
        const endMs = next ? next.startMs : page.startMs + page.durationMs;
        const duration = Math.max(1, Math.round(((endMs - page.startMs) / 1000) * fps));
        return (
          <Sequence key={i} from={from} durationInFrames={duration} layout="none">
            <CaptionPage page={page} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const CaptionPage: React.FC<{ page: TikTokPage }> = ({ page }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const u = useUnit();
  // Inside a Sequence the frame restarts at 0, so add the page start back to get absolute time.
  const nowMs = page.startMs + (frame / fps) * 1000;
  const enter = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 6 });
  // Vertical video: keep captions above the bottom ~25% where platform UI sits.
  const bottom = height > width ? "26%" : "10%";

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: bottom }}>
      <div
        style={{
          fontFamily: theme.fontFamily,
          fontWeight: 800,
          fontSize: 7 * u,
          lineHeight: 1.15,
          textAlign: "center",
          maxWidth: "84%",
          whiteSpace: "pre-wrap",
          transform: `scale(${0.92 + 0.08 * enter})`,
          // A thick outline keeps captions legible on any footage without a background box.
          WebkitTextStroke: `${0.9 * u}px #000`,
          paintOrder: "stroke fill",
        }}
      >
        {page.tokens.map((token, i) => {
          const active = token.fromMs <= nowMs && nowMs < token.toMs;
          return (
            <span key={i} style={{ color: active ? theme.colors.accent : theme.colors.text }}>
              {token.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
