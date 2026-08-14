# Transfer promotion gate

Rod Forge separates **useful transfer evidence** from **evidence strong enough to change an authoritative action**.

A technique that looked good on one figure is not automatically a general rule.

## Active-mode hierarchy

When the current reference already has direct observations for the same cognitive signature, ordinary active-mode thresholds apply:

```text
samples
confidence
predicted improvement margin
```

When the prediction comes from other references, an additional replication gate applies.

Default configuration:

```yaml
cognition:
  min_transfer_references: 3
  max_transfer_spread: 0.10
```

A `signature_transfer` candidate is promotion-ready only when:

```text
distinct bound references >= min_transfer_references
AND
spread of per-reference mean observations <= max_transfer_spread
```

The prediction exposes:

```text
transfer_references
transfer_spread
promotion_ready
promotion_reason
```

Typical reasons are:

- `observed_on_current_reference`
- `insufficient_distinct_references`
- `cross_reference_results_unstable`
- `replicated_across_references`
- `strategy_only_transfer_never_activates`
- `no_observed_evidence`

## Why strategy-only transfer cannot activate

A strategy name used on unrelated parts is too broad to justify changing geometry by itself.

For example, evidence that a construction method worked well on a grille does not authorize using it on a wheel simply because the strategy label matches.

`strategy_transfer` can still influence exploration and diagnostics, but it never directly changes the authoritative strategy in active mode.

## Example

Suppose `wheel_cylinder` has been measured on three distinct references:

```text
reference A: 0.81
reference B: 0.84
reference C: 0.82
```

The spread is `0.03`, so with the default `0.10` threshold this experience is repeatable enough to pass the transfer gate. It must still pass sample, confidence and improvement-margin thresholds before active mode can choose it.

If the same observations were:

```text
reference A: 0.95
reference B: 0.72
reference C: 0.50
```

then the spread is `0.45`. The transfer remains knowledge worth storing, but it is not stable enough to become autonomous action.

## Invariant

```text
observed once      -> experience
observed repeatedly -> expectation
replicated across distinct references -> transferable evidence
stable + confident + useful -> eligible for autonomous action
```

The system is deliberately conservative at the boundary between **learning** and **acting**.
