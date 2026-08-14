# Cognitive curriculum

Rod Forge can now run a **sequence of visual references against one shared episodic memory**.

The goal is to make learning measurable across figures instead of treating every reconstruction as an isolated project.

## Manifest

Start from:

```text
configs/curriculum.example.yaml
```

Example:

```yaml
name: hotrod_school
output_root: data/outputs/curriculum
memory_file: data/outputs/cognition/experience.json
report_window: 10
continue_on_error: true

runs:
  - id: hotrod_001
    reference_image: data/references/hotrod_001.png
  - id: hotrod_002
    reference_image: data/references/hotrod_002.png
```

Every reference is validated and fingerprinted before the figure is attempted.

## Dry-run school

```bash
rodforge curriculum-run \
  --config configs/project.yaml \
  --manifest configs/curriculum.example.yaml \
  --executor dry-run
```

This validates sequencing, isolated state, shared memory, reference fingerprints and reporting without requiring Blender geometry.

## Blender school

Inside Blender headless:

```bash
blender --background --python blender/startup.py -- \
  curriculum-run \
  --config configs/project.yaml \
  --manifest configs/curriculum.example.yaml \
  --executor blender
```

Each figure gets its own output directory:

```text
data/outputs/curriculum/<run-id>/
├── model.blend
├── state.json
├── checkpoints/
└── previews/
```

The cognitive memory is shared across the entire curriculum.

## Isolation contract

Between Blender figures, Rod Forge removes objects whose names start with `RF_` before the next run starts. State, checkpoints, previews and `.blend` outputs are also separated per figure.

That prevents the previous vehicle from contaminating the next figure's visual observation while still preserving cognitive experience.

## Failure behavior

An invalid or missing reference becomes `blocked_reference` and is never used as training evidence.

With `continue_on_error: true`, later figures continue. With it disabled, the curriculum stops at the first blocked/error run.

## Output report

At the end, Rod Forge writes:

```text
<output_root>/curriculum_report.json
```

The report contains:

- completed, blocked and errored figure counts,
- the exact reference fingerprint for each figure,
- per-run output locations,
- the full cognition calibration report,
- bound-reference counts,
- transfer-stability diagnostics.

## Intended experiment

A useful real sequence is:

```text
figure 001
figure 002
figure 003
...
figure 020
        ↓
compare prediction error over time
        ↓
compare construction quality over time
        ↓
compare transfer stability across references
```

The important distinction remains:

> More experience is not evidence of learning by itself. Better prediction and better observed outcomes are.
