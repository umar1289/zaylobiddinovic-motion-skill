import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { stagger } from "../lib/time";
import { theme } from "../theme";
import { useUnit } from "./useUnit";

type Props = { headline: string; subline?: string };

// Words rise in one by one, then the subline fades up once the headline has landed.
export const KineticTitle: React.FC<Props> = ({ headline, subline }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useUnit();
  const words = headline.split(" ");

  const sublineStart = stagger(words.length, 0.08, fps) + 6;
  const sublineOpacity = interpolate(frame, [sublineStart, sublineStart + 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: `${theme.safeMargin * 100}%` }}>
      <div
        style={{
          fontFamily: theme.fontFamily,
          fontWeight: 800,
          fontSize: 9 * u,
          lineHeight: 1.05,
          color: theme.colors.text,
          textAlign: "center",
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: `0 ${2.2 * u}px`,
        }}
      >
        {words.map((word, i) => {
          const progress = spring({ frame: frame - stagger(i, 0.08, fps), fps, config: { damping: 200 } });
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                opacity: progress,
                transform: `translateY(${(1 - progress) * 4 * u}px)`,
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
      {subline ? (
        <div
          style={{
            fontFamily: theme.fontFamily,
            fontWeight: 400,
            fontSize: 3.6 * u,
            color: theme.colors.muted,
            marginTop: 3 * u,
            opacity: sublineOpacity,
            transform: `translateY(${(1 - sublineOpacity) * 1.5 * u}px)`,
            textAlign: "center",
          }}
        >
          {subline}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
