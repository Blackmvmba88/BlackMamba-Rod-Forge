# Cognitive Loop v0

Rod Forge now has a guarded learning layer built around one rule:

> A hypothesis is not knowledge until observed results support it.

The cognitive loop is deliberately separate from the Blender executor. It does not pretend that a dry-run proves visual quality, and it does not silently turn one successful attempt into a permanent rule.

## Loop

```text
Task + current state
        ↓
Imagine candidate outcomes
        ↓
Prediction + confidence
        ↓
Shadow mode: keep planned action
Active mode: change only if evidence threshold is met
        ↓
Execute
        ↓
Critic metrics
        ↓
Observed score
        ↓
Prediction error
        ↓
Persistent episodic memory
        ↓
Future hypotheses
```

## Episodic memory

The memory file stores raw episodes:

- project name,
- task and cognitive signature,
- strategy used,
- metric being predicted,
- predicted score,
- observed score,
- prediction error,
- acceptance result,
- timestamp.

The default path is:

```text
data/outputs/cognition/experience.json
```

This memory is intentionally shared across runs so repeated construction jobs can improve future expectations.

## Prediction hierarchy

Predictions use the most specific useful evidence available:

1. matching cognitive signature + strategy + metric,
2. strategy-wide history for the same metric,
3. neutral prior when no evidence exists.

Confidence grows with sample count and consistency. High variance lowers confidence.

## Modes

### Shadow

Default and recommended while the system is young.

Rod Forge generates hypotheses, records what it expected, executes the original plan, measures the result and learns from the prediction error. It never changes the planned strategy.

```yaml
cognition:
  enabled: true
  mode: shadow
```

### Active

Active mode may select a candidate strategy only when all gates pass:

- enough samples exist,
- confidence exceeds the configured threshold,
- predicted improvement exceeds the configured margin.

This means experience can influence action, but uncertainty cannot masquerade as knowledge.

## Metrics

The structural critic always exposes `structural_score`.

Executors or future visual critics can additionally provide:

```text
quality_score
silhouette_score
proportion_score
reference_match
material_score
```

or any other normalized numeric metric in `evidence.scores`.

A task can choose what it is trying to predict through:

```python
task.metadata["cognitive_metric"] = "silhouette_score"
```

Alternative strategies can be proposed through:

```python
task.metadata["cognitive_candidates"] = ["method_b", "method_c"]
```

A reusable cross-run identity can be supplied explicitly with:

```python
task.metadata["cognitive_signature"] = "front-wheel-master"
```

## Safety invariant

The cognitive layer must preserve this distinction:

```text
prediction != observation
observation != rule
repeated evidence + bounded uncertainty -> actionable belief
```

The system is allowed to be uncertain. It is not allowed to erase uncertainty merely because it has an idea.

## Next step

The current loop can learn structural reliability immediately. The important next upgrade is to feed it visual metrics from rendered previews so it can learn whether geometric edits actually improve silhouette, proportion and reference similarity.
