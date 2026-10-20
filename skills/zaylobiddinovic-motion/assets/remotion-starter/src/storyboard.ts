// The storyboard is the single source of truth for scene order and timing.
// Edit this file after the user approves the written storyboard; components stay generic.

export type Scene =
  | { id: string; kind: "title"; seconds: number; headline: string; subline?: string }
  | { id: string; kind: "bullets"; seconds: number; heading: string; items: string[] }
  | { id: string; kind: "cta"; seconds: number; label: string; detail?: string };

export type Storyboard = {
  transitionSeconds: number;
  scenes: Scene[];
};

export const defaultStoryboard: Storyboard = {
  transitionSeconds: 0.5,
  scenes: [
    { id: "intro", kind: "title", seconds: 3, headline: "Make videos with code", subline: "Deterministic. Editable. Fast." },
    {
      id: "features",
      kind: "bullets",
      seconds: 4,
      heading: "What you get",
      items: ["Storyboard-driven scenes", "Animated captions", "Clean final renders"],
    },
    { id: "outro", kind: "cta", seconds: 3, label: "Start your project", detail: "zaylobiddinovic-motion" },
  ],
};

export const storyboardDurationSeconds = (board: Storyboard) =>
  board.scenes.reduce((sum, s) => sum + s.seconds, 0) -
  Math.max(0, board.scenes.length - 1) * board.transitionSeconds;
