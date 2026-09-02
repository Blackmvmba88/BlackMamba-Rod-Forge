# Rod Forge v2 — Parametric Mechanical Graph

Rod Forge v2 adds a vehicle-specific geometry contract without weakening the existing cognitive loop.

The cognitive system still decides how to build, observe, compare, repair and learn. The new layer answers a different question:

> What must be true about this vehicle and what must already exist before a mechanical part is allowed to be built?

## Geometry contract

The current Hot Rod 04 contract lives at:

```text
configs/vehicle_geometry.yaml
```

It stores only known dimensions and explicit modeling priors. Unknown technical dimensions stay unspecified instead of being guessed from a single reference image.

Current anchored values include:

```text
overall: 2710 x 1710 x 1260 mm
front tire: 580 x 200 mm, 17 in rim, 5 lug
rear tire: 680 x 320 mm, 20 in rim, deep dish
front suspension: double wishbone
steering: rack and pinion with Ackermann intent
powertrain: exposed V8, front-engine / rear-drive
```

The scrub-radius and roll-center ranges in the file are editable Rod Forge modeling targets, not manufacturing specifications.

## Mechanical task graph

The original artistic construction graph now has a mechanical backbone:

```text
chassis_blockout
├── front_wheels
│   └── front_hubs_brakes
│       └── front_suspension
│           └── steering
├── rear_wheels
│   └── rear_axle
│       └── rear_links
└── engine_volume
    └── engine_block
        ├── engine_mounts
        └── driveshaft ← rear_axle
```

`secondary_details` cannot complete until steering, rear locating links and driveshaft dependencies have completed.

## Constraint injection

When the project config declares:

```yaml
vehicle_geometry_file: configs/vehicle_geometry.yaml
```

`build_hotrod_plan()` receives a validated `VehicleGeometry` contract. Matching task constraints are copied into:

```python
task.metadata["geometry_constraints"]
```

The copy is deliberate. A strategy may inspect or transform its local constraint set without mutating the authoritative vehicle contract.

## Graph introspection

`PartGraph` now exposes two deterministic inspection tools:

```python
graph.execution_layers()
graph.dependency_closure("secondary_details")
```

`execution_layers()` returns topological groups that are dependency-safe to execute in parallel.

`dependency_closure(task_id)` returns every transitive prerequisite in topological order. This is useful for debugging, visualization, selective rebuilds and future graph-aware repair.

## CLI validation

Validate the geometry contract without running Blender:

```bash
rodforge geometry-check --config configs/project.yaml
```

Then smoke-test the complete v2 planning loop:

```bash
rodforge run --config configs/project.yaml --executor dry-run
```

## Next step

This phase deliberately stops before pretending that generic boxes are a final suspension system.

The next implementation phase should introduce dedicated Blender builders for:

1. hub and brake assembly,
2. upper/lower control arms,
3. steering rack and tie rods,
4. rear differential and axle tubes,
5. rear locating links,
6. engine mounts,
7. driveshaft and clearance validation.

At that point the geometry constraints can move from metadata-only planning evidence into measured Blender-space validation.
