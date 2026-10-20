// Author timings in seconds, convert once. Keeps storyboards readable and fps-independent.
export const toFrames = (seconds: number, fps: number) => Math.round(seconds * fps);

// Index-based delay for staggered entrances.
export const stagger = (index: number, stepSeconds: number, fps: number) =>
  toFrames(index * stepSeconds, fps);
