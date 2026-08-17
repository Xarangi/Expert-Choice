from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Optional

from expert_choice.core.types import Draft, VerifiedClaim


RANKING_MARKER = re.compile(r"MY RANKING:", re.IGNORECASE)


def split_rationale_and_ranking(text: str) -> tuple[str, str]:
    match = RANKING_MARKER.search(text)
    if not match:
        return text.strip(), text
    return text[: match.start()].strip(), text[match.start() :]


def sentences_mentioning(text: str, *needles: str) -> str:
    if not text.strip():
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    lowered = [n.lower() for n in needles if n]
    hits = [part for part in parts if any(n in part.lower() for n in lowered)]
    return " ".join(hits).strip()


def format_ranking(ranking: dict[str, int]) -> str:
    ordered = sorted(ranking.items(), key=lambda kv: (kv[1], kv[0]))
    lines = ["MY RANKING:"]
    for item, rank in ordered:
        lines.append(f"{rank}. {item}")
    return "\n".join(lines)


class BaseClaimSchema(ABC):
    name: str

    @abstractmethod
    def claim_ids(self, items: list[str]) -> list[str]: ...

    @abstractmethod
    def extract(self, ranking: dict[str, int], items: list[str]) -> dict[str, str]: ...

    def slice_rationale(self, draft: Draft, claim_id: str) -> str:
        span = sentences_mentioning(draft.rationale, *self._needles(claim_id))
        return span or draft.rationale

    def assemble(
        self, verified: list[VerifiedClaim], items: list[str]
    ) -> Optional[dict[str, int]]:
        return None

    def format_constraints(self, verified: list[VerifiedClaim]) -> str:
        if not verified:
            return "No verified sub-claims."
        lines = ["Verified sub-claims (treat as hard constraints when possible):"]
        for claim in verified:
            lines.append(f"- {self.describe_claim(claim.claim_id, claim.choice)}")
            if claim.rationale.strip():
                lines.append(f"  Rationale: {claim.rationale.strip()}")
        return "\n".join(lines)

    def describe_claim(self, claim_id: str, choice: str) -> str:
        return f"{claim_id} = {choice}"

    def _needles(self, claim_id: str) -> list[str]:
        return [claim_id]
