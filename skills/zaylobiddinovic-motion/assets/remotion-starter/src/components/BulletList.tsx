import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { stagger } from "../lib/time";
import { theme } from "../theme";
import { useUnit } from "./useUnit";

type Props = { heading: string; items: string[] };

export const BulletList: React.FC<Props> = ({ heading, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useUnit();

  const headingIn = spring({ frame, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: `0 ${theme.safeMargin * 100 + 4}%` }}>
      <div
        style={{
          fontFamily: theme.fontFamily,
          fontWeight: 800,
          fontSize: 6.5 * u,
          color: theme.colors.text,
          opacity: headingIn,
          marginBottom: 4 * u,
        }}
      >
        {heading}
      </div>
      {items.map((item, i) => {
        const start = stagger(i, 0.35, fps) + 10;
        const progress = spring({ frame: frame - start, fps, config: { damping: 18, stiffness: 120 } });
        const barWidth = interpolate(progress, [0, 1], [0, 1.2 * u]);
        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 2.5 * u,
              marginBottom: 2.6 * u,
              opacity: Math.min(1, progress),
              transform: `translateX(${(1 - progress) * -6 * u}px)`,
            }}
          >
            <div style={{ width: barWidth, height: 4.4 * u, borderRadius: u, background: theme.colors.accent }} />
            <div style={{ fontFamily: theme.fontFamily, fontWeight: 600, fontSize: 4.4 * u, color: theme.colors.text }}>
              {item}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
