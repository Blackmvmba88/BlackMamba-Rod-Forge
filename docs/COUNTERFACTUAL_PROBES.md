# Counterfactual Geometry Probes v0

Rod Forge can now gather evidence about an alternative geometry strategy **before** committing that strategy to the final scene.

This is operational imagination, not hidden certainty: the candidate is actually built in Blender, rendered, measured against the reference, recorded as a bounded probe episode, and then discarded.

## Loop

```text
current task
    ↓
historical hypothesis
    ↓
select underexplored candidate
    ↓
build candidate temporarily
    ↓
render probe preview
    ↓
reference_match + improvement_score
    ↓
record counterfactual_probe episode
    ↓
delete candidate geometry
    ↓
refresh hypothesis
    ↓
execute planned/guarded strategy normally
```

## Scene isolation contract

A probe must not become the final scene accidentally.

The Blender executor therefore:

1. removes geometry owned by the current task,
2. builds the candidate strategy,
3. renders a probe image with a dedicated filename,
4. never saves the `.blend` during the probe,
5. removes the candidate geometry in a `finally` path,
6. lets normal execution rebuild the selected strategy afterward.

Probe previews are durable evidence; probe geometry is disposable.

## Visual baseline isolation

The real visual critic keeps the previous accepted/executed reference match as its temporal baseline.

Counterfactual scoring uses that baseline but does **not** advance it. Otherwise a candidate that was never committed could distort the improvement score of the real next action.

```text
real baseline = 0.40
probe candidate = 0.70  -> probe improvement_score = 0.65
real baseline remains 0.40
actual action = 0.55    -> actual improvement_score uses 0.40, not 0.70
```

## Memory provenance

Experience episodes now include a `source` field:

```text
execution
counterfactual_probe
```

Both are empirical observations, but provenance remains explicit. A future confidence model can weight them differently without losing the raw history.

Old memory files remain readable because missing `source` values default to `execution`.

## Probe budget

Counterfactual exploration is bounded by configuration:

```yaml
cognition:
  counterfactual_probes: true
  max_probes_per_task: 1
  probe_sample_target: 3
```

A candidate is probed only while its sample count is below `probe_sample_target`. This prevents every run from paying an unlimited render tax for alternatives that are already well observed.

## Missing reference behavior

Probing requires a real visual reference on disk. If the configured reference is absent, Rod Forge skips counterfactual rendering instead of treating missing visual evidence as a failed construction task.

This is important for the current repository state: the cognitive machinery can be tested in CI without pretending CI performed a real Blender/reference experiment.

## Shadow mode remains authoritative

A probe can change the evidence available to the hypothesis, but `shadow` mode still keeps the planned strategy.

```text
probe says candidate looks better
        ≠
automatic strategy switch
```

Only guarded `active` mode may eventually switch, and only after the existing sample, confidence, and improvement gates pass.

## Failure semantics

Probe failures are diagnostic, not construction failures:

- they do not consume the global task failure budget,
- they do not block the task,
- they are recorded under `task.metadata["cognition"]["probe_errors"]`,
- normal execution continues.

## Next step

The next useful expansion is **multi-view counterfactual probing**: score the same temporary candidate from canonical side/front/rear/three-quarter views, then learn whether a strategy improves the object globally rather than from one projection only.
