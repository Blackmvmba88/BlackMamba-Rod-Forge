from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import Task


@dataclass(slots=True)
class CandidatePrediction:
    strategy: str
    expected_score: float
    confidence: float
    samples: int
    scope: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Hypothesis:
    task_id: str
    signature: str
    metric: str
    current_strategy: str
    recommended_strategy: str
    candidates: list[CandidatePrediction] = field(default_factory=list)

    def prediction_for(self, strategy: str) -> CandidatePrediction | None:
        return next((item for item in self.candidates if item.strategy == strategy), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "signature": self.signature,
            "metric": self.metric,
            "current_strategy": self.current_strategy,
            "recommended_strategy": self.recommended_strategy,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


@dataclass(slots=True)
class ExperienceEpisode:
    timestamp: str
    project_name: str
    task_id: str
    signature: str
    strategy: str
    metric: str
    predicted_score: float | None
    observed_score: float
    prediction_error: float | None
    accepted: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperienceEpisode":
        return cls(**data)


class ExperienceMemory:
    """Persistent episodic memory shared across Rod Forge runs.

    The store intentionally keeps raw episodes instead of prematurely turning
    them into permanent rules. Predictions are rebuilt from observed history,
    which lets new evidence correct old expectations.
    """

    VERSION = 1

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.episodes: list[ExperienceEpisode] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if int(payload.get("version", 0)) != self.VERSION:
            raise ValueError(f"Unsupported cognition memory version: {payload.get('version')}")
        self.episodes = [ExperienceEpisode.from_dict(item) for item in payload.get("episodes", [])]

    def append(self, episode: ExperienceEpisode) -> None:
        self.episodes.append(episode)
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": self.VERSION,
            "episodes": [episode.to_dict() for episode in self.episodes],
        }
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def scores(self, *, signature: str | None, strategy: str, metric: str) -> list[float]:
        return [
            episode.observed_score
            for episode in self.episodes
            if episode.strategy == strategy
            and episode.metric == metric
            and (signature is None or episode.signature == signature)
        ]


class CognitiveEngine:
    """Imagine -> act -> compare -> learn loop.

    `shadow` mode learns and writes hypotheses but never changes execution.
    `active` mode may select a historically better candidate only after both a
    confidence threshold and a minimum predicted improvement are satisfied.
    """

    def __init__(
        self,
        memory: ExperienceMemory,
        *,
        mode: str = "shadow",
        min_samples: int = 3,
        activation_confidence: float = 0.70,
        activation_margin: float = 0.05,
    ):
        if mode not in {"shadow", "active"}:
            raise ValueError("Cognitive mode must be 'shadow' or 'active'")
        self.memory = memory
        self.mode = mode
        self.min_samples = max(1, int(min_samples))
        self.activation_confidence = self._clamp01(activation_confidence)
        self.activation_margin = max(0.0, float(activation_margin))

    @staticmethod
    def signature(task: Task) -> str:
        explicit = task.metadata.get("cognitive_signature")
        if explicit:
            return str(explicit)
        family = task.metadata.get("part_family") or task.task_id.split("_", 1)[0]
        return f"{family}:{task.strategy}"

    @staticmethod
    def metric(task: Task) -> str:
        return str(task.metadata.get("cognitive_metric", "structural_score"))

    def imagine(self, task: Task) -> Hypothesis:
        signature = self.signature(task)
        metric = self.metric(task)
        strategies = [task.strategy]
        for candidate in task.metadata.get("cognitive_candidates", []):
            candidate = str(candidate)
            if candidate not in strategies:
                strategies.append(candidate)

        predictions = [self._predict(signature, strategy, metric) for strategy in strategies]
        current = predictions[0]
        best = max(
            predictions,
            key=lambda item: (item.expected_score, item.confidence, item.strategy == task.strategy),
        )

        recommended = task.strategy
        if (
            self.mode == "active"
            and best.strategy != task.strategy
            and best.samples >= self.min_samples
            and best.confidence >= self.activation_confidence
            and best.expected_score - current.expected_score >= self.activation_margin
        ):
            recommended = best.strategy

        return Hypothesis(
            task_id=task.task_id,
            signature=signature,
            metric=metric,
            current_strategy=task.strategy,
            recommended_strategy=recommended,
            candidates=predictions,
        )

    def apply(self, task: Task, hypothesis: Hypothesis) -> str:
        original = task.strategy
        selected = hypothesis.recommended_strategy
        cognition = task.metadata.setdefault("cognition", {})
        cognition["mode"] = self.mode
        cognition["hypothesis"] = hypothesis.to_dict()
        cognition["planned_strategy"] = original
        cognition["selected_strategy"] = selected
        cognition["strategy_changed"] = selected != original
        task.strategy = selected
        return selected

    def learn(
        self,
        *,
        project_name: str,
        task: Task,
        accepted: bool,
        metrics: dict[str, float] | None,
        hypothesis: Hypothesis,
    ) -> ExperienceEpisode:
        metrics = metrics or {}
        metric = hypothesis.metric
        if metric in metrics:
            observed = self._clamp01(float(metrics[metric]))
        else:
            observed = 1.0 if accepted else 0.0
            metric = "acceptance"

        prediction = hypothesis.prediction_for(task.strategy)
        predicted = prediction.expected_score if prediction and hypothesis.metric == metric else None
        error = observed - predicted if predicted is not None else None

        episode = ExperienceEpisode(
            timestamp=datetime.now(timezone.utc).isoformat(),
            project_name=project_name,
            task_id=task.task_id,
            signature=hypothesis.signature,
            strategy=task.strategy,
            metric=metric,
            predicted_score=predicted,
            observed_score=observed,
            prediction_error=error,
            accepted=accepted,
        )
        self.memory.append(episode)

        cognition = task.metadata.setdefault("cognition", {})
        cognition["last_episode"] = episode.to_dict()
        return episode

    def _predict(self, signature: str, strategy: str, metric: str) -> CandidatePrediction:
        exact = self.memory.scores(signature=signature, strategy=strategy, metric=metric)
        if exact:
            return CandidatePrediction(
                strategy=strategy,
                expected_score=sum(exact) / len(exact),
                confidence=self._confidence(exact, scope_weight=1.0),
                samples=len(exact),
                scope="signature",
            )

        general = self.memory.scores(signature=None, strategy=strategy, metric=metric)
        if general:
            return CandidatePrediction(
                strategy=strategy,
                expected_score=sum(general) / len(general),
                confidence=self._confidence(general, scope_weight=0.55),
                samples=len(general),
                scope="strategy",
            )

        return CandidatePrediction(
            strategy=strategy,
            expected_score=0.5,
            confidence=0.0,
            samples=0,
            scope="prior",
        )

    def _confidence(self, scores: list[float], *, scope_weight: float) -> float:
        n = len(scores)
        sample_confidence = n / (n + self.min_samples)
        if n <= 1:
            stability = 0.5
        else:
            mean = sum(scores) / n
            variance = sum((score - mean) ** 2 for score in scores) / n
            stability = 1.0 - min(1.0, math.sqrt(variance))
        return self._clamp01(sample_confidence * stability * scope_weight)

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
