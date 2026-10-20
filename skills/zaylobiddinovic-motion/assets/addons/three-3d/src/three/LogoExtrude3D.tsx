import { useLoader } from "@react-three/fiber";
import { useMemo } from "react";
import { AbsoluteFill, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";
import { SVGLoader } from "three/addons/loaders/SVGLoader.js";
import { Background } from "../components/Background";
import { useUnit } from "../components/useUnit";
import { theme } from "../theme";
import { CameraRig } from "./CameraRig";
import { Stage } from "./Stage";

export type LogoExtrude3DProps = {
  // Flat SVG in public/ (filled paths; strokes are ignored). Convert text to outlines first.
  svgFile: string;
  tagline?: string;
  color?: string;
  // Extrusion depth relative to logo width (0.08 = 8%).
  depth?: number;
};

// Longest side of the logo in world units. At the default camera distance the frame is ~3.5 units tall.
const TARGET_WIDTH = 1.9;

const useLogoGeometry = (url: string, depth: number) => {
  const data = useLoader(SVGLoader, url);
  return useMemo(() => {
    const shapes = data.paths.flatMap((p) => SVGLoader.createShapes(p));
    const flat = new THREE.ShapeGeometry(shapes);
    flat.computeBoundingBox();
    const size = new THREE.Vector3();
    flat.boundingBox!.getSize(size);
    flat.dispose();
    const scale = TARGET_WIDTH / Math.max(size.x, size.y);
    const geo = new THREE.ExtrudeGeometry(shapes, {
      depth: (depth * TARGET_WIDTH) / scale,
      bevelEnabled: true,
      bevelThickness: (0.015 * TARGET_WIDTH) / scale,
      bevelSize: (0.01 * TARGET_WIDTH) / scale,
      bevelSegments: 4,
      curveSegments: 24,
    });
    geo.center();
    // SVG y points down; flip so the logo is upright.
    geo.scale(scale, -scale, scale);
    geo.computeVertexNormals();
    return geo;
  }, [data, depth]);
};

const Logo: React.FC<{ svgFile: string; color: string; depth: number; rotY: number; scale: number }> = ({
  svgFile,
  color,
  depth,
  rotY,
  scale,
}) => {
  const geometry = useLogoGeometry(staticFile(svgFile), depth);
  return (
    <mesh geometry={geometry} position={[0, 0.4, 0]} rotation={[0, rotY, 0]} scale={scale} castShadow>
      {/* Low metalness: without an environment map, metals reflect nothing and look black. */}
      <meshPhysicalMaterial color={color} metalness={0.3} roughness={0.35} clearcoat={1} side={THREE.DoubleSide} />
    </mesh>
  );
};

export const LogoExtrude3D: React.FC<LogoExtrude3DProps> = ({
  svgFile,
  tagline,
  color = theme.colors.accent,
  depth = 0.08,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const u = useUnit();

  // Swing in from edge-on, settle with a slight overshoot, then drift slowly.
  const swing = spring({ frame, fps, config: { damping: 14, stiffness: 90 } });
  const rotY = interpolate(swing, [0, 1], [-Math.PI / 2, 0]) + Math.sin(frame / fps) * 0.06;
  const scale = interpolate(swing, [0, 1], [0.7, 1]) * (height > width ? 0.8 : 1);
  const dolly = interpolate(frame, [0, fps * 4], [6.5, 5.6], { extrapolateRight: "clamp" });
  const taglineIn = spring({ frame: frame - Math.round(fps * 1.1), fps, config: { damping: 200 } });

  return (
    <AbsoluteFill>
      <Background />
      <Stage>
        <CameraRig position={[0, 0.2, dolly]} />
        <Logo svgFile={svgFile} color={color} depth={depth} rotY={rotY} scale={scale} />
      </Stage>
      {tagline ? (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: "11%" }}>
          <div
            style={{
              fontFamily: theme.fontFamily,
              fontWeight: 600,
              fontSize: 4 * u,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: theme.colors.text,
              opacity: taglineIn,
              transform: `translateY(${(1 - taglineIn) * 2 * u}px)`,
            }}
          >
            {tagline}
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
