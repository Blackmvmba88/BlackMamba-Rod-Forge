# Mechanical Pass v1

`blender/mechanics/hotrod_mechanics_pass_v1.py` captures the first believable mechanical layer for the BlackMamba hot rod scene.

## What it builds

- Four brake disc + hub assemblies.
- Five-lug wheel pattern on all four corners.
- Front steering knuckles.
- Front double-wishbone suspension.
- Front coilovers.
- Steering rack and tie rods.
- Front structural crossmember.
- Rear solid axle.
- Rear differential and differential nose.
- Driveshaft.
- Rear trailing arms and upper links.
- Rear coilovers.
- Rear Panhard bar.
- Engine-mount crossbar and left/right mounts.

Generated objects are grouped below the `BM_Mechanics_v1` collection so the pass can be removed or rebuilt without deleting the rest of the vehicle.

## Design intent

This pass is not a full engineering simulation. It establishes a mechanically coherent visual topology so later Rod Forge stages can reason about real component families instead of treating the vehicle as bodywork plus wheels.

The current architecture intentionally keeps:

1. visible components as separate named Blender objects,
2. wheel hardware centered from scene wheel references,
3. left/right suspension pieces separately addressable,
4. generated mechanics under one disposable root collection,
5. a non-destructive save path (`*_mechanical_pass.blend`).

## Current scene anchors

The script was calibrated against the existing `hotrod.blend` wheel objects:

- `Torus.002` — front right,
- `Torus.003` — front left,
- `Torus.001` — rear left,
- rear right mirrored from rear left when no explicit reference is present.

Fallback coordinates are embedded so the pass remains runnable when an expected wheel object is missing, but those coordinates are specific to the current source scene.

## Blender usage

Open the source `.blend`, then run the script from Blender's Scripting workspace.

Command-line equivalent:

```bash
blender hotrod.blend --python blender/mechanics/hotrod_mechanics_pass_v1.py
```

When the source file has a valid path, the script writes a non-destructive sibling copy:

```text
hotrod_mechanical_pass.blend
```

## Idempotence

Before rebuilding, the script removes the previous `BM_Mechanics_v1` collection recursively. Re-running the pass therefore replaces generated mechanics instead of stacking duplicate suspension and drivetrain parts.

## Scene metadata

The pass records:

```text
BM_MECHANICS_PASS = v1
BM_WHEEL_PATTERN = 5-lug
BM_MECHANICS_COMPONENTS = 64
```

These custom properties give later automation a cheap readiness check before attempting a second mechanical stage.

## Important boundary

`v1` is anchored to the hand-authored `hotrod.blend` coordinate convention. Rod Forge's autonomous executor currently creates its own `RF_*` wheel objects in a different procedural coordinate space.

The next integration step is therefore **not** to copy these constants into the executor. It is to add a mechanical adapter that derives suspension, steering and drivetrain hard-points from the generated `RF_front_wheels`, `RF_rear_wheels`, chassis bounds and engine volume.

That adapter should make the same mechanical topology reusable across different hot-rod proportions while keeping this script as the verified source-scene baseline.

## Acceptance criteria for v1

- Script can be run repeatedly without duplicating its generated collection.
- Four hubs exist.
- Twenty lug objects exist total.
- Both front corners have upper/lower control arms and coilovers.
- Steering rack connects through two tie rods.
- Rear axle contains a differential and longitudinal driveshaft.
- Rear suspension contains trailing links, upper links, coilovers and Panhard bar.
- Engine mounts are represented independently from the engine mesh.
- The source `.blend` is not overwritten by default behavior.
