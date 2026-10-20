import { useVideoConfig } from "remotion";

// 1 unit = 1% of the shorter frame side. Sizing in units keeps layouts valid for 16:9, 9:16 and 1:1.
export const useUnit = () => {
  const { width, height } = useVideoConfig();
  return Math.min(width, height) / 100;
};
