import type { Caption } from "@remotion/captions";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { Background } from "./components/Background";
import { Captions } from "./components/Captions";

export type CaptionedVideoProps = {
  // File in public/, e.g. "talking-head.mp4". Leave empty to preview captions on the background.
  videoFile: string;
  captionsFile: string;
  // Optional overrides. Set them to the footage's values (see probe_media.py); otherwise 1080x1920 and speech length.
  durationSeconds?: number;
  width?: number;
  height?: number;
  // Filled in by calculateMetadata; do not set by hand.
  captions?: Caption[];
};

export const CaptionedVideo: React.FC<CaptionedVideoProps> = ({ videoFile, captions = [] }) => (
  <AbsoluteFill style={{ backgroundColor: "black" }}>
    {videoFile ? (
      <OffthreadVideo src={staticFile(videoFile)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    ) : (
      <Background />
    )}
    <Captions captions={captions} />
  </AbsoluteFill>
);
