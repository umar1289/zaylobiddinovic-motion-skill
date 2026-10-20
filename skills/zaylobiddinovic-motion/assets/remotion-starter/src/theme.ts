import { loadFont } from "@remotion/google-fonts/Inter";

// Change these per project. Every component reads from here, so a rebrand is one edit.
const { fontFamily } = loadFont("normal", {
  weights: ["400", "600", "800"],
  subsets: ["latin"],
});

export const theme = {
  fontFamily,
  colors: {
    background: "#0B0D12",
    backgroundAlt: "#1A1F2B",
    text: "#F5F7FA",
    muted: "#9AA3B2",
    accent: "#4F8CFF",
    accentText: "#FFFFFF",
  },
  // Fraction of the frame kept clear of important content (title-safe area).
  safeMargin: 0.08,
} as const;
