# Reference-bound cognition

Rod Forge now treats the visual reference as part of the cognitive context, not merely as an input path.

When `reference-check` validates an image, its SHA-256 fingerprint is passed into the cognitive engine. Every new execution episode and counterfactual-probe episode stores that fingerprint as `reference_sha256`.

This gives the memory three useful scopes:

```text
same reference + same cognitive signature
        ↓ strongest evidence
reference_signature

same signature across other references
        ↓ lower-confidence transfer
signature_transfer

same strategy across broader history
        ↓ weakest learned transfer
strategy_transfer
```

If no usable history exists, prediction still falls back to the neutral prior.

## Why this matters

A score learned from one figure is not automatically a universal rule. Rod Forge must be able to distinguish:

- "this worked on this exact reference",
- "this has worked on similar tasks across other references",
- "this strategy tends to work in general",
- "I do not have enough evidence yet".

Exact-reference evidence receives the highest confidence weight. Cross-reference evidence is intentionally discounted so `active` mode cannot treat transfer as if it were direct observation.

## Backward compatibility

Memory format version remains `1`. Older episodes that do not contain `reference_sha256` load as `reference_sha256: null` and are classified as `unbound` history.

That legacy history is not discarded. It may still contribute to lower-confidence transfer predictions.

## Cognitive report

`rodforge cognition-report` now exposes:

```text
references.unique_bound
references.bound_episodes
references.unbound_episodes
by_reference
transfer_stability
```

`transfer_stability` compares the same `(signature, strategy, metric)` across multiple bound references and reports the spread between per-reference mean observations.

A low spread is evidence that behavior may transfer consistently. It is **not proof of generalization**. The system keeps that distinction explicit.

## Invariant

```text
experience without stimulus identity
        must never outrank
experience observed on the current exact stimulus
```

This keeps the learning loop empirical while allowing cross-figure experience to become useful gradually.
