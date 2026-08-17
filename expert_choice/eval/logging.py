from __future__ import annotations

import json
from pathlib import Path

from expert_choice.core.types import PipelineState


def write_trace(path: str | Path, state: PipelineState) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(state.model_dump_json() + "\n")


def write_summary(path: str | Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
