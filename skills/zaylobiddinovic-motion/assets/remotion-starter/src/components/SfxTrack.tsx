import { useEffect, useState } from "react";
import { Audio, continueRender, delayRender, Sequence, staticFile, useVideoConfig } from "remotion";

// A cue as written by `scripts/sfx_cues.py prepare`: start_s already accounts for where the sound's hit is.
export type SfxCue = {
  id: string;
  file: string;
  start_s: number;
  gain_db?: number;
  duration_ms?: number;
};

type Props = {
  // Prepared cue sheet in public/, e.g. "sfx_cues.json". Its file paths are relative to public/.
  cuesFile: string;
  // Master trim for all effects, in dB.
  masterDb?: number;
};

const dbToGain = (db: number) => Math.pow(10, db / 20);

export const SfxTrack: React.FC<Props> = ({ cuesFile, masterDb = 0 }) => {
  const { fps } = useVideoConfig();
  const [cues, setCues] = useState<SfxCue[] | null>(null);
  const [handle] = useState(() => delayRender(`Loading SFX cues ${cuesFile}`));

  useEffect(() => {
    fetch(staticFile(cuesFile))
      .then((r) => {
        if (!r.ok) throw new Error(`${cuesFile}: HTTP ${r.status}`);
        return r.json();
      })
      .then((sheet: { cues: SfxCue[] }) => {
        const unprepared = sheet.cues.filter((c) => typeof c.start_s !== "number");
        if (unprepared.length) {
          throw new Error(`Run "sfx_cues.py prepare" first; unprepared cues: ${unprepared.map((c) => c.id).join(", ")}`);
        }
        setCues(sheet.cues);
      })
      .finally(() => continueRender(handle));
  }, [cuesFile, handle]);

  if (!cues) return null;
  return (
    <>
      {cues.map((cue) => (
        <Sequence
          key={cue.id}
          name={`sfx ${cue.id}`}
          from={Math.round(cue.start_s * fps)}
          durationInFrames={cue.duration_ms ? Math.ceil((cue.duration_ms / 1000) * fps) + 1 : undefined}
          layout="none"
        >
          <Audio src={staticFile(cue.file)} volume={dbToGain((cue.gain_db ?? 0) + masterDb)} />
        </Sequence>
      ))}
    </>
  );
};
