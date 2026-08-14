# Visual Feedback Loop v0

Rod Forge now has a deterministic visual observation layer that turns Blender previews into learning signals.

The goal is not to claim that a cheap image metric understands design. The goal is narrower and operationally useful: after each construction step, measure whether the rendered result moved closer to or farther from the visual reference.

## Runtime loop

```text
Current Blender state
        ↓
Task hypothesis
        ↓
Execute geometry
        ↓
Save .blend
        ↓
Render transparent observation
        ↓
Extract preview silhouette
        ↓
Extract reference silhouette
        ↓
Compare shape + proportion
        ↓
reference_match
        ↓
Compare with previous observation
        ↓
improvement_score
        ↓
Prediction error
        ↓
Episodic memory
```

## Scores

All cognitive scores are normalized to `[0, 1]`.

### `silhouette_score`

Intersection-over-union of normalized subject masks. The comparison is translation tolerant and preserves aspect ratio.

### `proportion_score`

Similarity between reference and preview subject bounding-box aspect ratios.

### `reference_match`

Current v0 blend:

```text
0.75 * silhouette_score + 0.25 * proportion_score
```

### `improvement_score`

This is the important cognitive signal. It answers whether the most recent operation improved the observed result relative to the previous observation.

```text
reference_delta = current_reference_match - previous_reference_match
improvement_score = clamp(0.5 + reference_delta / 2)
```

Interpretation:

```text
< 0.5  -> the last step made the visual match worse
= 0.5  -> neutral / no measurable change
> 0.5  -> the last step improved the visual match
```

For the first observation of a new run, the baseline is zero.

## Why every task gets an observation

A single final render can tell us whether the whole object resembles the reference, but it cannot tell us which construction decision helped or hurt.

Rendering after every task creates an attribution signal:

```text
chassis        -> +0.18
cabin          -> +0.07
engine volume  -> -0.02
wheel placement-> +0.11
body shell     -> +0.16
```

Across repeated figures, Rod Forge can begin estimating the expected effect of each task before it executes it.

## Background extraction

Preview renders use RGBA transparency when Blender can provide it, so their silhouettes are direct alpha masks.

Reference images may be ordinary RGB images. Their background color is estimated from border pixels and pixels sufficiently far from that color are treated as foreground.

This is deliberately deterministic and cheap. Difficult references can later switch to a stronger segmentation provider without changing the cognitive memory contract.

## Camera stability

The cognitive camera is generated automatically from scene bounds and uses an orthographic projection. Stable framing is more important than cinematic framing for measurable learning.

A later phase can add multiple canonical views and view-specific memory.

## Failure behavior

Visual feedback is observational by default.

If a reference image or preview cannot be measured, structural execution may still succeed. The error is preserved in evidence instead of being silently converted into a fake score.

A task can explicitly require visual validation through success criteria when a later production phase needs it.

## Current boundary

This layer measures visible geometric agreement. It does not yet judge:

- semantic style,
- elegance,
- mechanical plausibility,
- topology quality,
- surface continuity,
- material fidelity,
- artistic intent.

Those are future critics. They should contribute independent metrics rather than corrupting the meaning of silhouette and proportion scores.

## Cognitive invariant

```text
prediction != observation
observation != improvement
improvement != permanent rule
repeated measured improvement + confidence -> learned expectation
```

That distinction is the core of the system: Rod Forge is allowed to imagine that an operation will help, but the rendered evidence gets the final vote.
