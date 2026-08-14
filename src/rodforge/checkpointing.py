from __future__ import annotations

import json
from pathlib import Path

from .schemas import ProjectState


class CheckpointManager:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, state: ProjectState) -> Path:
        state.checkpoint_index += 1
        path = self.directory / f"checkpoint_{state.checkpoint_index:04d}.json"
        path.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return path

    def latest(self) -> Path | None:
        checkpoints = sorted(self.directory.glob("checkpoint_*.json"))
        return checkpoints[-1] if checkpoints else None
