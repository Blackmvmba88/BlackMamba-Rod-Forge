from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Iterable

from .cognition import ExperienceEpisode, ExperienceMemory


def build_cognitive_report(
    memory: ExperienceMemory | Iterable[ExperienceEpisode],
    *,
    window: int = 10,
    trend_tolerance: float = 0.01,
) -> dict[str, Any]:
    """Measure whether Rod Forge is getting better at predicting outcomes.

    The report intentionally evaluates predictions against later observations;
    it does not infer quality from sample count alone. A falling prediction
    MAE means the system's expectation is becoming closer to what actually
    happens.

    Reference-aware diagnostics separate exact-input experience from unbound
    legacy episodes and estimate whether comparable strategies behave
    consistently across multiple visual references.
    """
    episodes = list(memory.episodes if isinstance(memory, ExperienceMemory) else memory)
    predictions = [episode for episode in episodes if episode.predicted_score is not None]

    source_counts = Counter(episode.source for episode in episodes)
    source_groups: dict[str, list[ExperienceEpisode]] = defaultdict(list)
    metric_groups: dict[str, list[ExperienceEpisode]] = defaultdict(list)
    strategy_groups: dict[str, list[ExperienceEpisode]] = defaultdict(list)
    reference_groups: dict[str, list[ExperienceEpisode]] = defaultdict(list)
    for episode in episodes:
        source_groups[episode.source].append(episode)
        metric_groups[episode.metric].append(episode)
        strategy_groups[episode.strategy].append(episode)
        reference_groups[episode.reference_sha256 or "unbound"].append(episode)

    overall = _prediction_stats(predictions)
    trend = _trend(
        predictions,
        window=max(1, int(window)),
        tolerance=max(0.0, float(trend_tolerance)),
    )
    bound_references = sorted(
        key for key in reference_groups
        if key != "unbound"
    )

    return {
        "episodes_total": len(episodes),
        "sources": dict(sorted(source_counts.items())),
        "references": {
            "unique_bound": len(bound_references),
            "bound_episodes": sum(
                len(reference_groups[key]) for key in bound_references
            ),
            "unbound_episodes": len(reference_groups.get("unbound", [])),
        },
        "predictions_total": len(predictions),
        "prediction_accuracy": overall,
        "learning_trend": trend,
        "transfer_stability": _transfer_stability(episodes),
        "by_source": {
            name: _group_stats(group)
            for name, group in sorted(source_groups.items())
        },
        "by_metric": {
            name: _group_stats(group)
            for name, group in sorted(metric_groups.items())
        },
        "by_strategy": {
            name: _group_stats(group)
            for name, group in sorted(strategy_groups.items())
        },
        "by_reference": {
            name: _group_stats(group)
            for name, group in sorted(reference_groups.items())
        },
    }


def _group_stats(episodes: list[ExperienceEpisode]) -> dict[str, Any]:
    predictions = [episode for episode in episodes if episode.predicted_score is not None]
    observed = [episode.observed_score for episode in episodes]
    return {
        "episodes": len(episodes),
        "predictions": len(predictions),
        "mean_observed_score": _mean(observed),
        "prediction_accuracy": _prediction_stats(predictions),
    }


def _prediction_stats(episodes: list[ExperienceEpisode]) -> dict[str, Any]:
    if not episodes:
        return {
            "count": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
            "skill": None,
            "direction_accuracy": None,
            "direction_samples": 0,
        }

    errors = [episode.observed_score - float(episode.predicted_score) for episode in episodes]
    absolute_errors = [abs(error) for error in errors]
    mae = _mean(absolute_errors)
    rmse = math.sqrt(_mean([error * error for error in errors]))
    direction_hits, direction_samples = _direction_accuracy(episodes)

    return {
        "count": len(episodes),
        "mae": mae,
        "rmse": rmse,
        "bias": _mean(errors),
        "skill": max(0.0, min(1.0, 1.0 - mae)),
        "direction_accuracy": (
            direction_hits / direction_samples if direction_samples else None
        ),
        "direction_samples": direction_samples,
    }


def _direction_accuracy(episodes: list[ExperienceEpisode]) -> tuple[int, int]:
    hits = 0
    samples = 0
    epsilon = 1e-9
    for episode in episodes:
        if episode.metric != "improvement_score" or episode.predicted_score is None:
            continue
        predicted_delta = float(episode.predicted_score) - 0.5
        observed_delta = episode.observed_score - 0.5
        if abs(predicted_delta) <= epsilon or abs(observed_delta) <= epsilon:
            continue
        samples += 1
        if (predicted_delta > 0) == (observed_delta > 0):
            hits += 1
    return hits, samples


def _transfer_stability(episodes: list[ExperienceEpisode]) -> dict[str, Any]:
    """Summarize observed cross-reference consistency for comparable actions.

    This is deliberately not called proof of generalization. Low spread across
    references means the same signature/strategy/metric has behaved similarly
    on multiple inputs, which is evidence worth tracking before transfer is
    trusted more aggressively.
    """
    grouped: dict[tuple[str, str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    reference_ids = {
        episode.reference_sha256
        for episode in episodes
        if episode.reference_sha256 is not None
    }

    for episode in episodes:
        if episode.reference_sha256 is None:
            continue
        key = (episode.signature, episode.strategy, episode.metric)
        grouped[key][episode.reference_sha256].append(episode.observed_score)

    spreads: list[float] = []
    for per_reference in grouped.values():
        if len(per_reference) < 2:
            continue
        means = [sum(values) / len(values) for values in per_reference.values()]
        spreads.append(max(means) - min(means))

    stable_threshold = 0.10
    return {
        "reference_count": len(reference_ids),
        "comparable_groups": len(spreads),
        "stable_groups": sum(spread <= stable_threshold for spread in spreads),
        "stable_threshold": stable_threshold,
        "mean_reference_spread": _mean(spreads),
        "max_reference_spread": max(spreads) if spreads else None,
    }


def _trend(
    episodes: list[ExperienceEpisode],
    *,
    window: int,
    tolerance: float,
) -> dict[str, Any]:
    if len(episodes) < 4:
        return {
            "status": "insufficient_data",
            "window": 0,
            "early_mae": None,
            "recent_mae": None,
            "mae_improvement": None,
        }

    sample_window = min(window, len(episodes) // 2)
    early = episodes[:sample_window]
    recent = episodes[-sample_window:]
    early_mae = _prediction_stats(early)["mae"]
    recent_mae = _prediction_stats(recent)["mae"]
    improvement = early_mae - recent_mae

    if improvement > tolerance:
        status = "improving"
    elif improvement < -tolerance:
        status = "regressing"
    else:
        status = "stable"

    return {
        "status": status,
        "window": sample_window,
        "early_mae": early_mae,
        "recent_mae": recent_mae,
        "mae_improvement": improvement,
    }


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None
