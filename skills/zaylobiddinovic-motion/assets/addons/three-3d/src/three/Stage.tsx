import { ThreeCanvas } from "@remotion/three";
import { useVideoConfig } from "remotion";
import { theme } from "../theme";

type Props = { children: React.ReactNode; fov?: number };

// Full-frame 3D canvas with a neutral three-point light rig.
// No environment map by default: drei <Environment preset> downloads HDR files at render time.
export const Stage: React.FC<Props> = ({ children, fov = 35 }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas
      width={width}
      height={height}
      shadows
      dpr={1}
      camera={{ fov, position: [0, 0, 6], near: 0.1, far: 100 }}
      gl={{ antialias: true, preserveDrawingBuffer: true }}
    >
      <ambientLight intensity={0.35} />
      {/* key */}
      <directionalLight
        position={[3, 4, 5]}
        intensity={2.2}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      {/* fill */}
      <directionalLight position={[-4, 1, 3]} intensity={0.6} />
      {/* rim, tinted with the brand accent */}
      <pointLight position={[0, 2, -4]} intensity={30} color={theme.colors.accent} />
      {children}
    </ThreeCanvas>
  );
};
