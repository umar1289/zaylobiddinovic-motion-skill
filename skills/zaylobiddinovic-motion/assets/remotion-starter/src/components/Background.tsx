import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

// Slow drifting gradient. Motion comes only from the frame number, so every render is identical.
export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const angle = interpolate(frame, [0, durationInFrames], [120, 160]);
  const glowX = interpolate(frame, [0, durationInFrames], [30, 70]);

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at ${glowX}% 35%, ${theme.colors.accent}33 0%, transparent 45%),
          linear-gradient(${angle}deg, ${theme.colors.background} 0%, ${theme.colors.backgroundAlt} 100%)`,
      }}
    />
  );
};
