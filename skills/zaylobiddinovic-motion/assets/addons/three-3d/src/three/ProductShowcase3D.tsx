import { ContactShadows, RoundedBox, useTexture } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import { AbsoluteFill, Easing, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { useUnit } from "../components/useUnit";
import { theme } from "../theme";
import { CameraRig } from "./CameraRig";
import { Stage } from "./Stage";

export type ProductShowcase3DProps = {
  title: string;
  subtitle?: string;
  // Image in public/ shown on the device screen (portrait, ~9:19.5). Empty = glowing accent screen.
  screenImage?: string;
  bodyColor?: string;
};

const PHONE = { w: 1, h: 2.05, d: 0.1, r: 0.12 };

const Screen: React.FC<{ image: string }> = ({ image }) => {
  const texture = useTexture(staticFile(image));
  return (
    <mesh position={[0, 0, PHONE.d / 2 + 0.002]}>
      <planeGeometry args={[PHONE.w * 0.9, PHONE.h * 0.93]} />
      <meshBasicMaterial map={texture} toneMapped={false} />
    </mesh>
  );
};

// Placeholder app UI drawn on a canvas: deterministic, no files needed. Replace with screenImage for real work.
const PlaceholderScreen: React.FC = () => {
  const texture = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = 540;
    c.height = 1116;
    const g = c.getContext("2d")!;
    const grad = g.createLinearGradient(0, 0, 0, c.height);
    grad.addColorStop(0, theme.colors.accent);
    grad.addColorStop(1, theme.colors.background);
    g.fillStyle = grad;
    g.fillRect(0, 0, c.width, c.height);
    g.fillStyle = "rgba(255,255,255,0.9)";
    g.beginPath();
    g.roundRect(40, 120, 300, 40, 20);
    g.fill();
    g.fillStyle = "rgba(255,255,255,0.18)";
    [260, 470, 680].forEach((y) => {
      g.beginPath();
      g.roundRect(40, y, c.width - 80, 170, 28);
      g.fill();
    });
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []);
  return (
    <mesh position={[0, 0, PHONE.d / 2 + 0.002]}>
      <planeGeometry args={[PHONE.w * 0.9, PHONE.h * 0.93]} />
      <meshBasicMaterial map={texture} toneMapped={false} />
    </mesh>
  );
};

const Phone: React.FC<{ screenImage?: string; bodyColor: string }> = ({ screenImage, bodyColor }) => (
  <group>
    <RoundedBox args={[PHONE.w, PHONE.h, PHONE.d]} radius={PHONE.r} smoothness={6} castShadow>
      <meshPhysicalMaterial color={bodyColor} metalness={0.6} roughness={0.25} clearcoat={1} clearcoatRoughness={0.1} />
    </RoundedBox>
    {screenImage ? <Screen image={screenImage} /> : <PlaceholderScreen />}
  </group>
);

export const ProductShowcase3D: React.FC<ProductShowcase3DProps> = ({
  title,
  subtitle,
  screenImage,
  bodyColor = "#1c1f26",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();
  const u = useUnit();

  // Camera orbits from left to right over the whole shot with an ease-in-out.
  const orbit = interpolate(frame, [0, durationInFrames], [-0.6, 0.35], {
    easing: Easing.bezier(0.65, 0, 0.35, 1),
  });
  const radius = height > width ? 7.2 : 5.6;
  const camPos: [number, number, number] = [Math.sin(orbit) * radius, 0.4, Math.cos(orbit) * radius];

  // Device rises in, then floats. The float is a function of frame, not of a clock.
  const rise = spring({ frame, fps, config: { damping: 200 }, durationInFrames: Math.round(fps * 1.2) });
  const floatY = Math.sin((frame / fps) * 1.6) * 0.05;
  const y = interpolate(rise, [0, 1], [-1.2, 0]) + floatY;
  const tilt = interpolate(rise, [0, 1], [0.5, 0.12]);

  const textIn = spring({ frame: frame - Math.round(fps * 0.6), fps, config: { damping: 200 } });
  // Landscape: device right, text left. Portrait: device centred, text at the top.
  const portrait = height > width;
  const deviceX = portrait ? 0 : 1.1;

  return (
    <AbsoluteFill>
      <Background />
      <Stage>
        <CameraRig position={camPos} target={[deviceX * 0.5, 0, 0]} />
        <group position={[deviceX, y, 0]} rotation={[tilt * 0.3, -tilt, 0]} scale={portrait ? 1 : 1.15}>
          <Phone screenImage={screenImage} bodyColor={bodyColor} />
        </group>
        <ContactShadows position={[deviceX, -1.25, 0]} opacity={0.5} scale={6} blur={2.4} far={2} />
      </Stage>
      <AbsoluteFill
        style={{
          justifyContent: portrait ? "flex-start" : "center",
          alignItems: portrait ? "center" : "flex-start",
          padding: portrait ? `${12 * u}px ${8 * u}px` : `0 ${10 * u}px`,
          pointerEvents: "none",
        }}
      >
        <div style={{ maxWidth: portrait ? "90%" : "45%", textAlign: portrait ? "center" : "left" }}>
          <div
            style={{
              fontFamily: theme.fontFamily,
              fontWeight: 800,
              fontSize: 8 * u,
              lineHeight: 1.05,
              color: theme.colors.text,
              opacity: textIn,
              transform: `translateY(${(1 - textIn) * 3 * u}px)`,
            }}
          >
            {title}
          </div>
          {subtitle ? (
            <div
              style={{
                fontFamily: theme.fontFamily,
                fontSize: 3.6 * u,
                color: theme.colors.muted,
                marginTop: 2.5 * u,
                opacity: textIn,
              }}
            >
              {subtitle}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
