import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { Fragment } from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { Background } from "./components/Background";
import { BulletList } from "./components/BulletList";
import { CallToAction } from "./components/CallToAction";
import { KineticTitle } from "./components/KineticTitle";
import { SfxTrack } from "./components/SfxTrack";
import { toFrames } from "./lib/time";
import type { Scene, Storyboard } from "./storyboard";

const renderScene = (scene: Scene) => {
  switch (scene.kind) {
    case "title":
      return <KineticTitle headline={scene.headline} subline={scene.subline} />;
    case "bullets":
      return <BulletList heading={scene.heading} items={scene.items} />;
    case "cta":
      return <CallToAction label={scene.label} detail={scene.detail} />;
  }
};

// sfxCuesFile: a prepared cue sheet in public/ (see scripts/sfx_cues.py). Empty string = no sound effects.
export const Promo: React.FC<{ storyboard: Storyboard; sfxCuesFile?: string }> = ({ storyboard, sfxCuesFile }) => {
  const { fps } = useVideoConfig();
  const transition = toFrames(storyboard.transitionSeconds, fps);

  return (
    <AbsoluteFill>
      <Background />
      <TransitionSeries>
        {storyboard.scenes.map((scene, i) => (
          <Fragment key={scene.id}>
            {i > 0 ? (
              <TransitionSeries.Transition
                presentation={i % 2 === 0 ? fade() : slide({ direction: "from-right" })}
                timing={linearTiming({ durationInFrames: transition })}
              />
            ) : null}
            <TransitionSeries.Sequence durationInFrames={toFrames(scene.seconds, fps)}>
              {renderScene(scene)}
            </TransitionSeries.Sequence>
          </Fragment>
        ))}
      </TransitionSeries>
      {sfxCuesFile ? <SfxTrack cuesFile={sfxCuesFile} /> : null}
    </AbsoluteFill>
  );
};
