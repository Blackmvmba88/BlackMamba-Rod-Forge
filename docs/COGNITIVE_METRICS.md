# Cognitive Calibration Metrics v0

Rod Forge should not be declared "smarter" because it has more memory. The useful question is whether its expectations become **more accurate against observed outcomes**.

The calibration report turns raw episodic memory into a measurable learning curve.

## Command

```bash
rodforge cognition-report --config configs/project.yaml --window 10
```

The command reads the configured cognition memory and emits JSON. It does not open Blender, mutate state, or create new experience.

## Core metrics

### MAE — mean absolute prediction error

```text
MAE = mean(abs(observed_score - predicted_score))
```

Lower is better. This is the primary metric for the question:

> Is Rod Forge getting better at predicting what will happen before it acts?

### RMSE — root mean squared error

RMSE punishes large misses more strongly than MAE. A system with mostly good predictions but occasional disastrous expectations will show a larger RMSE penalty.

### Bias

```text
bias = mean(observed_score - predicted_score)
```

Interpretation:

```text
bias < 0  expectations are too optimistic
bias > 0  expectations are too pessimistic
bias ≈ 0  no strong directional bias
```

### Skill

For normalized 0..1 outcomes, the report exposes:

```text
skill = 1 - MAE
```

This is a compact readability metric, not a replacement for MAE. `1.0` means perfect predictions in the evaluated sample.

### Direction accuracy

For `improvement_score`, neutral is `0.5`.

Direction accuracy asks whether Rod Forge correctly predicted the **sign** of the change:

```text
predicted > 0.5 and observed > 0.5  -> correct: expected improvement, got improvement
predicted < 0.5 and observed < 0.5  -> correct: expected regression, got regression
opposite signs                       -> wrong direction
```

Neutral predictions or neutral observations are excluded from this metric.

## Learning trend

A report compares an early prediction window with a recent window of the same size.

```text
mae_improvement = early_mae - recent_mae
```

Interpretation:

```text
positive beyond tolerance -> improving
near zero                 -> stable
negative beyond tolerance -> regressing
```

At least four predicted episodes are required so the early and recent windows can be disjoint.

This does not prove general intelligence. It answers a narrower and operationally important question: **is prediction error falling over accumulated construction experience?**

## Breakdowns

The report also groups performance by:

- evidence source (`execution` vs `counterfactual_probe`),
- metric,
- strategy.

That allows diagnoses such as:

```text
Overall MAE is improving,
but wheel_cylinder predictions are still poor.
```

or:

```text
Counterfactual probes are accurate,
but executed body strategies remain over-optimistic.
```

## Example shape

```json
{
  "episodes_total": 42,
  "predictions_total": 31,
  "prediction_accuracy": {
    "mae": 0.09,
    "rmse": 0.13,
    "bias": -0.02,
    "skill": 0.91,
    "direction_accuracy": 0.82
  },
  "learning_trend": {
    "status": "improving",
    "window": 10,
    "early_mae": 0.21,
    "recent_mae": 0.08,
    "mae_improvement": 0.13
  }
}
```

Values above are illustrative only.

## Invariant

```text
more experience != better cognition
lower verified prediction error = evidence of better prediction
```

The report exists specifically so Rod Forge cannot congratulate itself for merely accumulating episodes.

## Next step

Once real Blender/reference runs accumulate enough episodes, the calibration history can be persisted as run-level snapshots and plotted over figure number to show whether prediction skill improves, plateaus, or regresses across the training sequence.
