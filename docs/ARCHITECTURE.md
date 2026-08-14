# Architecture

## Mission

Rod Forge is an autonomous builder, not a monolithic Blender script. The system must be able to stop and resume without losing semantic state, and every generated artifact must be attributable to a task.

## Core invariants

1. A task never runs before its dependencies are complete.
2. Every state mutation is persisted.
3. Every executor result carries evidence.
4. Every failure consumes bounded retry/fallback budget.
5. A non-critical failure cannot terminate the whole project.
6. Critical blockers are explicit and inspectable.
7. Geometry generation is replaceable independently from orchestration.
8. Visual intelligence is replaceable independently from geometry execution.

## Layers

### Intelligence layer

`reference_analyzer` → `task_planner` → future multimodal critic.

This layer reasons about what should exist.

### Control layer

`part_graph` → `orchestrator` → `repair_engine` → `state_manager`.

This layer decides what may execute and what happens after success/failure.

### Execution layer

`DryRunExecutor` and `BlenderExecutor` implement the same task boundary.

The dry-run executor is intentionally first-class. It allows the autonomous control plane to be hardened before Blender complexity is introduced.

### Evidence layer

Every successful task returns evidence such as object name, dimensions, executor, strategy, preview path, mesh statistics, or later visual scores.

## Future visual loop

```text
Blender task
   ↓
preview render
   ↓
visual critic
   ↓
reference comparison
   ↓
score + diagnosis
   ↓
parameter adjustment / repair task
   ↓
Blender task
```

The visual critic must never directly mutate Blender. It only emits diagnoses and proposed changes. Mutation remains inside the executor boundary.

## Determinism

For equivalent task input, configuration and seed, deterministic operations should produce equivalent topology/proportions whenever possible. Creative variation belongs behind explicit parameters or seeds.

## Recovery

The recoverable unit is the task. State JSON answers what the system believes. Blender checkpoints answer what geometry physically existed at a stable moment. Neither is enough alone in production; both are retained.

## Long-term direction

The hot rod is the first proving ground. Once the contracts are stable, the same control plane can support props, machines, stylized vehicles, stage objects and other modular 3D builds by replacing analyzers, planners and geometry libraries while keeping the autonomous kernel intact.
