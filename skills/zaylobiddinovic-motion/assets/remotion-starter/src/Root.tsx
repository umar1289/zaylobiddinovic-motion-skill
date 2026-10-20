import type { Caption } from "@remotion/captions";
import { Composition, staticFile, type CalculateMetadataFunction } from "remotion";
import { CaptionedVideo, type CaptionedVideoProps } from "./CaptionedVideo";
import { Promo } from "./Promo";
import { defaultStoryboard, storyboardDurationSeconds } from "./storyboard";

const FPS = 30;

const promoDuration = Math.round(storyboardDurationSeconds(defaultStoryboard) * FPS);

// Captions are loaded before rendering so duration can follow the speech (plus a short tail).
const loadCaptions: CalculateMetadataFunction<CaptionedVideoProps> = async ({ props }) => {
  const res = await fetch(staticFile(props.captionsFile));
  const captions = (await res.json()) as Caption[];
  const lastMs = captions.length ? captions[captions.length - 1].endMs : 3000;
  const seconds = props.durationSeconds ?? (lastMs + 600) / 1000;
  return {
    durationInFrames: Math.ceil(seconds * FPS),
    width: props.width,
    height: props.height,
    props: { ...props, captions },
  };
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Promo"
      component={Promo}
      width={1920}
      height={1080}
      fps={FPS}
      durationInFrames={promoDuration}
      defaultProps={{ storyboard: defaultStoryboard, sfxCuesFile: "sfx_cues.demo.json" }}
    />
    <Composition
      id="PromoVertical"
      component={Promo}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={promoDuration}
      defaultProps={{ storyboard: defaultStoryboard, sfxCuesFile: "sfx_cues.demo.json" }}
    />
    <Composition
      id="CaptionedVideo"
      component={CaptionedVideo}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={FPS * 5}
      defaultProps={{ videoFile: "", captionsFile: "captions.demo.json" }}
      calculateMetadata={loadCaptions}
    />
  </>
);
