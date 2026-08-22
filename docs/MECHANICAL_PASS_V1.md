# Mechanical Pass v1

`blender/mechanics/hotrod_mechanics_pass_v1.py` preserves the first believable mechanical layer calibrated against the hand-authored BlackMamba hot rod scene.

Rod Forge now also contains a procedural adapter in `src/rodforge/mechanics.py` so the autonomous pipeline can build the same mechanical families from its generated `RF_*` wheel geometry instead of copying source-scene coordinates.

## What it builds

- Four brake disc + hub assemblies.
- Five-lug wheel pattern on all four corners.
- Front steering knuckles.
- Front double-wishbone suspension.
- Front coilovers.
- Steering rack and tie rods.
- Front structural crossmember.
- Rear solid axle.
- Rear differential.
- Driveshaft.
- Rear trailing arms and upper links.
- Rear coilovers.
- Rear Panhard bar.
- Engine-mount crossbar and left/right mounts.

## Two mechanical paths

### 1. Source-scene baseline

`blender/mechanics/hotrod_mechanics_pass_v1.py`

This path is calibrated against the existing `hotrod.blend` wheel objects and is kept as the visual/mechanical baseline that proved the topology.

Generated source-scene objects live below the `BM_Mechanics_v1` collection so the pass can be removed or rebuilt without deleting the rest of the vehicle.

### 2. Autonomous Rod Forge path

`src/rodforge/mechanics.py`

The procedural path derives its envelope from:

- `RF_front_wheels`,
- `RF_front_wheels__R`,
- `RF_rear_wheels`,
- `RF_rear_wheels__R`.

It calculates:

- front axle X,
- rear axle X,
- longitudinal wheelbase,
- front/rear half-track,
- centerline Y,
- front/rear wheel-center Z.

Those dimensions drive suspension, steering, axle, driveshaft and mount hard-points. No `hotrod.blend` coordinates are copied into the autonomous builder.

All autonomous mechanical objects use the `RF_mechanical_systems` task prefix, which makes retries idempotent through the existing executor cleanup logic.

## Task-graph integration

The planner now creates a `mechanical_systems` task after:

- `chassis_blockout`,
- `engine_volume`,
- `front_wheels`,
- `rear_wheels`.

`body_shell` depends on `mechanical_systems`, so the body is refined around an established rolling/mechanical package rather than treating mechanics as decoration added at the end.

The Blender executor dispatches the `mechanical_systems` strategy to `build_mechanical_systems()`.

## Source scene anchors

The baseline script was calibrated against:

- `Torus.002` — front right,
- `Torus.003` — front left,
- `Torus.001` — rear left,
- rear right mirrored from rear left when no explicit reference is present.

Fallback coordinates remain embedded only in the source-scene script.

## Source-scene Blender usage

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

The source-scene script removes the previous `BM_Mechanics_v1` collection before rebuilding.

The autonomous executor already removes every object named `RF_mechanical_systems` or prefixed with `RF_mechanical_systems__` before retrying the task.

Both paths therefore replace their own generated mechanics instead of stacking duplicates.

## Scene metadata

Source-scene pass:

```text
BM_MECHANICS_PASS = v1
BM_WHEEL_PATTERN = 5-lug
BM_MECHANICS_COMPONENTS = 64
```

Autonomous pass:

```text
RF_MECHANICAL_SYSTEMS = v1-procedural
RF_WHEEL_PATTERN = 5-lug
RF_MECHANICAL_COMPONENTS = <generated count>
RF_WHEELBASE = <derived value>
```

## Current engineering boundary

This remains a mechanically coherent **visual/procedural topology**, not a vehicle-dynamics or structural simulation.

The procedural v1 currently derives its main envelope from wheel centers. `chassis_blockout` and `engine_volume` are explicit dependencies so the scene is structurally ready, but their bounds are not yet consumed to solve packaging clearances.

The next mechanical refinement should therefore derive mount/control-arm hard-points from chassis and engine bounds, then add clearance checks and steering/suspension travel validation.

## Acceptance criteria for v1

- Four hubs are generated.
- Twenty lug objects are generated total.
- Both front corners have upper/lower control arms and coilovers.
- Steering rack connects through two tie rods.
- Rear axle contains a differential and longitudinal driveshaft.
- Rear suspension contains trailing links, upper links, coilovers and a Panhard bar.
- Engine mounts are represented independently from the engine mesh.
- Re-running either path does not duplicate its generated mechanics.
- Autonomous mechanics are derived from `RF_*` wheel geometry, not source-scene constants.
- Planner enforces mechanics before `body_shell`.

## Validation still required

- Run the branch in Blender 5.x against a clean Rod Forge execution.
- Inspect left/right orientation and wheel-plane alignment.
- Verify control arms do not visibly cross the wheel/tire envelope.
- Verify driveshaft and engine mounts remain inside the chassis package.
- Capture a real `.blend` and preview artifact as evidence.
