import { Composition } from "remotion";
import { LogoExtrude3D } from "./LogoExtrude3D";
import { ProductShowcase3D } from "./ProductShowcase3D";

// Add <ThreeCompositions /> inside RemotionRoot in src/Root.tsx.
export const ThreeCompositions: React.FC = () => (
  <>
    <Composition
      id="Product3D"
      component={ProductShowcase3D}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={150}
      defaultProps={{ title: "Meet the new app", subtitle: "Shown on a 3D device", screenImage: "" }}
    />
    <Composition
      id="Product3DVertical"
      component={ProductShowcase3D}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={150}
      defaultProps={{ title: "Meet the new app", subtitle: "Shown on a 3D device", screenImage: "" }}
    />
    <Composition
      id="Logo3D"
      component={LogoExtrude3D}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={120}
      defaultProps={{ svgFile: "logo-demo.svg", tagline: "Your tagline here" }}
    />
  </>
);
