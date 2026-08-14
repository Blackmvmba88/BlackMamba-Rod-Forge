# Cognitive learning trajectory

A final cognition report answers **where Rod Forge ended**. A learning trajectory answers the more important question:

> **Did it actually improve while moving from figure to figure?**

`curriculum-run` now captures a cognition snapshot at baseline and after every attempted figure.

## Output

Alongside `curriculum_report.json`, the curriculum writes:

```text
<output_root>/learning_trajectory.json
```

Each point records:

```text
step
run_id
status
episodes_total
episodes_added
predictions_total
prediction_mae
prediction_rmse
prediction_skill
prediction_bias
direction_accuracy
bound_references
learning_trend
transfer_comparable_groups
transfer_stable_groups
mean_reference_spread
```

Blocked references remain visible in the trajectory with `episodes_added: 0`. That makes it explicit that invalid input did not silently become learning evidence.

## Summary

The trajectory summary compares the first measurable prediction error with the latest one:

```text
initial_mae
final_mae
mae_improvement
initial_skill
final_skill
skill_improvement
status
```

Status is:

- `improving` when MAE falls by more than 0.01,
- `regressing` when MAE rises by more than 0.01,
- `stable` inside that tolerance,
- `insufficient_data` before enough measured steps exist.

## Reading the curve

A useful real run may look like:

```text
figure 01  MAE 0.26
figure 02  MAE 0.23
figure 03  MAE 0.19
figure 04  MAE 0.15
figure 05  MAE 0.12
```

That is evidence that expectations are becoming closer to observed outcomes.

A growing memory with flat or rising MAE is **not** treated as cognitive improvement.

## Two separate curves

The long-term experiment should keep two questions separate:

```text
prediction curve
"am I getting better at anticipating what will happen?"

construction curve
"are the actual models getting better?"
```

Prediction improvement without construction improvement means the system is learning to forecast its own limitations. Construction improvement without prediction improvement means useful behavior exists but the world model remains poorly calibrated.

The strongest result is improvement in both.
