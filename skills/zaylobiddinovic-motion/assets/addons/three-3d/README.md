# 3D add-on for the Remotion starter

Adds `Product3D`, `Product3DVertical` and `Logo3D` compositions (React Three Fiber via `@remotion/three`).

1. Copy into the project created from `remotion-starter`:
   ```bash
   cp -R "<skill>/assets/addons/three-3d/src/three" "<project>/video/src/three"
   cp "<skill>/assets/addons/three-3d/public/logo-demo.svg" "<project>/video/public/"
   ```
2. Install (ask the user first; about 55 packages):
   ```bash
   npm install @remotion/three@<same version as remotion> three@0.186.1 @react-three/fiber@9.8.1 @react-three/drei@10.7.9 @types/three@0.186.0
   ```
3. In `src/Root.tsx`: `import { ThreeCompositions } from "./three/compositions";` and render `<ThreeCompositions />` inside `RemotionRoot`.
4. In `remotion.config.ts`: `Config.setChromiumOpenGlRenderer("angle");` (reliable WebGL in headless rendering).

Check: `npx remotion still Logo3D out/logo.png --frame=60`.
