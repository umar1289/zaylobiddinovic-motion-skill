# 3D scenes (React Three Fiber in Remotion)

Use 3D when depth carries the message: a product turning in space, a logo with real material and light, a camera flying through data. A flat design with a fake 3D tilt is often cheaper and cleaner; suggest it when the brief does not need real depth.

## Contents
1. Setup
2. The one rule: frame-driven everything
3. Camera
4. Light and materials
5. Content: product mockups, logos, models, video on surfaces
6. Combining 3D with 2D layers
7. Rendering and performance
8. Common errors

## 1. Setup

The bundled add-on `assets/addons/three-3d/` provides `Stage` (canvas + light rig), `CameraRig`, `ProductShowcase3D` (phone mockup with your screenshot) and `LogoExtrude3D` (flat SVG logo → extruded 3D). Follow its README: copy `src/three`, install `@remotion/three` (same version as `remotion`), `three`, `@react-three/fiber`, `@react-three/drei`, `@types/three`, register `<ThreeCompositions />`, set `Config.setChromiumOpenGlRenderer("angle")`.

```bash
npx remotion still Product3D out/p.png --frame=90 --props='{"title":"Budget in 3 taps","screenImage":"app-screen.png"}'
npx remotion still Logo3D out/l.png --frame=60 --props='{"svgFile":"client-logo.svg","tagline":"Since 2012"}'
```

## 2. The one rule: frame-driven everything

`<ThreeCanvas>` (from `@remotion/three`, never R3F's plain `<Canvas>`) switches R3F to manual rendering and draws once per Remotion frame. Anything that advances on its own clock will be wrong in the render:

- Don't animate in `useFrame((state, delta) => …)`; `delta` and `state.clock` are wall-clock. Compute rotation/position from `useCurrentFrame()` and pass them as props.
- Avoid self-animating drei helpers: `Float`, `Sparkles`, `Stars` (animated), `MeshWobbleMaterial`, `MeshDistortMaterial`, `Trail`, `CameraShake`, `OrbitControls`/`PresentationControls` (interactive). Rebuild the effect from the frame instead: e.g. float = `Math.sin(frame / fps * 1.6) * 0.05`.
- Randomness: `random("particle-" + i)` from `remotion`, never `Math.random()`.
- Camera and other imperative changes go in `useLayoutEffect` (see `CameraRig`), so they apply before the frame is drawn; `useEffect` lands one frame late.
- Loading: `useTexture`, `useLoader`, `useGLTF` suspend; `ThreeCanvas` waits for Suspense, so they are safe. Avoid assets fetched from the network at render time.

## 3. Camera

- Default: `fov` 30–40 for product work (less distortion), 50–60 for immersive fly-throughs.
- Move the camera or the object, rarely both. Slow orbits (20–40° over a shot) and dolly-ins (5–15% closer) read as premium; fast spins read as cheap.
- Ease every camera move (`Easing.bezier(0.65, 0, 0.35, 1)`); a linear orbit starts and stops with a jolt.
- Visible height at distance `d` = `2 * d * tan(fov / 2)`. Use it to size objects to the frame instead of guessing, and pull the camera back for 9:16 (the starter does: radius 7.2 vs 5.6).

## 4. Light and materials

- `Stage` uses key (warm-neutral, casts shadows), fill (weak, opposite side) and a rim light in the brand accent from behind. Adjust intensities before adding more lights.
- Without an environment map, metals reflect nothing and go black. Either keep `metalness` ≤ 0.4, or ship a small local HDR in `public/` and use `<Environment files={staticFile("studio.hdr")} />`. Don't use `<Environment preset="…">`: it downloads from a CDN during render.
- `meshPhysicalMaterial` with `clearcoat` gives glossy plastic/paint; `roughness` 0.2–0.4 for products, 0.6–0.9 for matte.
- Grounding: `ContactShadows` under the object stops it floating in a void.
- Screens and UI textures: `meshBasicMaterial` with `toneMapped={false}` keeps screenshot colours accurate.

## 5. Content

- **App/product mockup:** `ProductShowcase3D` with `screenImage` (portrait screenshot in `public/`, about 9:19.5). For a laptop or box, swap `RoundedBox` dimensions or load a model.
- **Logo:** `LogoExtrude3D` needs a clean SVG with filled paths. Convert text to outlines and expand strokes first (in Figma/Illustrator/Inkscape). Multi-colour logos: split paths by `path.color` and give each its own material.
- **3D text:** drei `<Text3D font={staticFile("Font_Bold.json")}>` needs a typeface JSON (convert a licensed font with facetype.js). drei `<Text>` downloads a default font unless you pass `font={staticFile("Font.woff")}`.
- **GLTF/GLB models:** put them in `public/`, load with `useGLTF(staticFile("model.glb"))`. Check the model's licence (Sketchfab/Poly Haven etc. vary) and record it in `final/credits.txt`. Draco-compressed models fetch a decoder from a CDN by default; copy the decoder into `public/draco/` and call `useGLTF.setDecoderPath(staticFile("draco/"))`, or ask for an uncompressed model.
- **Video on a surface:** `useOffthreadVideoTexture({ src: staticFile("clip.mp4") })` from `@remotion/three` gives a frame-accurate texture during rendering.

## 6. Combining 3D with 2D layers

Put the `<Stage>` in an `AbsoluteFill` and HTML/2D layers above or below it (the add-on puts the background below and titles above). Text is sharper and easier to edit as HTML than as 3D geometry, so use 3D text only when the text itself must turn in space.

## 7. Rendering and performance

- `dpr={1}` in `Stage` matches canvas pixels to video pixels; raise it only for supersampling small details.
- Shadows and high `smoothness`/`curveSegments` cost render time. Drafts: `--scale=0.5`; heavy scenes: `--concurrency=2` to avoid running out of GPU memory.
- If frames come out black or WebGL fails: confirm `setChromiumOpenGlRenderer("angle")`, try `--gl=swangle` (software, slow but reliable), and check `npx remotion still` with `--log=verbose`.

## 8. Common errors

| Symptom | Fix |
|---|---|
| Animation differs between preview and render, or stutters | Something uses `useFrame`/clock/drei animated helper; drive it from `useCurrentFrame()` |
| Camera one frame behind | Move camera code from `useEffect` to `useLayoutEffect` |
| Black metal object | Lower `metalness` or add a local environment map |
| Logo upside down / mirrored | SVG y-axis points down: scale geometry by `(s, -s, s)` (the add-on does) |
| Logo missing pieces | Strokes aren't filled shapes; outline them in a vector editor |
| Texture colours look washed out | `toneMapped={false}` on the material; `colorSpace = SRGBColorSpace` on canvas textures |
| Render hangs on "Waiting for <Suspense />" | An asset URL 404s; check the file is in `public/` and the name matches |
