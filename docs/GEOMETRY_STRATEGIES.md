# Geometry Strategy Families v0

Rod Forge now distinguishes **strategy labels** from **materially different construction methods**.

A cognitive candidate is only useful if changing the strategy changes the geometry that Blender actually builds. Two names that produce the same mesh are not two experiences; they are one experience with aliases.

## Initial families

| Family | Baseline | Alternative | Geometric difference |
| --- | --- | --- | --- |
| chassis | `chassis_slab` | `chassis_rails` | monolithic slab vs open ladder frame |
| cabin | `cabin_box` | `cabin_chopped` | single volume vs lower cab + separate chopped roof mass |
| wheel | `wheel_torus` | `wheel_cylinder` | open torus tire silhouette vs solid cylindrical wheel mass |
| body | `body_box` | `body_tapered` | rectangular envelope vs front-narrowing tapered prism |

The catalog lives in `src/rodforge/geometry_strategies.py`. The planner attaches alternatives through `task.metadata["cognitive_candidates"]`, and the Blender executor dispatches those names to distinct builders.

## Repair behavior

For tasks with a real geometry family, the concrete alternative is inserted before generic fallbacks. Example:

```text
front_wheels
  current: wheel_torus
  retry_same
  wheel_cylinder
  split_task
  simplify_geometry
  alternate_method
  rebuild_from_checkpoint
```

That matters because a failed construction can now gather experience from a genuinely different method instead of merely renaming the same cube operation.

## Cognitive behavior

The cognitive engine still starts in `shadow` mode. It may compare historical expectations for the baseline and candidate, but it does not switch purely because one prediction looks better.

A concrete alternative can now gather observed `improvement_score` evidence in two ways:

- real execution through repair/training/guarded selection,
- a bounded counterfactual probe that builds, renders, scores and discards the candidate before final execution.

Repeated runs can therefore build separate distributions such as:

```text
wheel_torus     -> mean improvement 0.61, confidence 0.72
wheel_cylinder  -> mean improvement 0.47, confidence 0.69
```

Only then does "I think torus will work better here" have empirical content.

Counterfactual behavior is specified in `docs/COUNTERFACTUAL_PROBES.md`.

## Invariant

```text
same objective + different strategy
        must imply
materially different geometry construction
```

If two candidates converge to the same builder and parameters, the catalog test should fail or the duplicate should be removed.

## Next step

Expand each strategy family beyond a binary choice and evaluate candidates across multiple canonical camera views so learned preferences do not overfit one projection.
