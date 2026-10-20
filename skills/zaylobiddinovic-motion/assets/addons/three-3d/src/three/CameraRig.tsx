import { useThree } from "@react-three/fiber";
import { useLayoutEffect } from "react";

type Props = { position: [number, number, number]; target?: [number, number, number] };

// Positions the camera for the current frame. useLayoutEffect runs before <ThreeCanvas> renders the
// frame, so the camera is never one frame behind. Compute `position` from useCurrentFrame() in the parent.
export const CameraRig: React.FC<Props> = ({ position, target = [0, 0, 0] }) => {
  const camera = useThree((s) => s.camera);
  useLayoutEffect(() => {
    camera.position.set(...position);
    camera.lookAt(...target);
    camera.updateProjectionMatrix();
  }, [camera, position, target]);
  return null;
};
