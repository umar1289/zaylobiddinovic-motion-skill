import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { useUnit } from "./useUnit";

type Props = { label: string; detail?: string };

export const CallToAction: React.FC<Props> = ({ label, detail }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = useUnit();

  const pop = spring({ frame, fps, config: { damping: 12, stiffness: 140 } });
  // A gentle breathing pulse after the pop settles draws the eye without feeling busy.
  const pulse = 1 + 0.02 * Math.sin(Math.max(0, frame - fps) / (fps / 3));
  const detailOpacity = interpolate(frame, [fps * 0.6, fps * 1.1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          fontFamily: theme.fontFamily,
          fontWeight: 800,
          fontSize: 5.5 * u,
          color: theme.colors.accentText,
          background: theme.colors.accent,
          padding: `${2.4 * u}px ${5 * u}px`,
          borderRadius: 100 * u,
          transform: `scale(${pop * pulse})`,
          boxShadow: `0 ${2 * u}px ${6 * u}px ${theme.colors.accent}55`,
        }}
      >
        {label}
      </div>
      {detail ? (
        <div
          style={{
            fontFamily: theme.fontFamily,
            fontSize: 3.2 * u,
            color: theme.colors.muted,
            marginTop: 4 * u,
            opacity: detailOpacity,
          }}
        >
          {detail}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
