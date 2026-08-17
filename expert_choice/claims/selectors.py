from __future__ import annotations

from expert_choice.core.types import Draft, Thesis


class RationaleSpanSelector:
    """Pick the cleanest item-specific rationale; shortest complete span wins."""

    name = "rationale_span"

    def select(
        self,
        drafts: dict[str, Draft],
        agent_ids: list[str],
        claim_id: str,
        schema,
    ) -> Thesis:
        scored: list[tuple[int, int, str, str]] = []
        for agent_id in agent_ids:
            draft = drafts[agent_id]
            span = schema.slice_rationale(draft, claim_id)
            text = (span or draft.rationale or "").strip()
            complete = 1 if text and text != draft.rationale else (1 if text else 0)
            if text and any(
                needle.lower() in text.lower()
                for needle in getattr(schema, "_needles", lambda _cid: [_cid])(claim_id)
            ):
                complete = 1
            length = len(text) if text else 10**9
            scored.append((complete, length, agent_id, text or draft.rationale))

        scored.sort(key=lambda row: (-row[0], row[1], row[2]))
        author_id, rationale = scored[0][2], scored[0][3]
        draft = drafts[author_id]
        choice = schema.extract(draft.ranking, list(draft.ranking.keys())).get(claim_id, "")
        return Thesis(
            claim_id=claim_id,
            choice=choice,
            author_id=author_id,
            rationale=rationale,
            coalition_agent_ids=list(agent_ids),
            coalition_size=len(agent_ids),
        )


class LogprobSelector:
    """Use mean token logprob when present; otherwise fall back to rationale span."""

    name = "logprob"

    def __init__(self) -> None:
        self._fallback = RationaleSpanSelector()

    def select(
        self,
        drafts: dict[str, Draft],
        agent_ids: list[str],
        claim_id: str,
        schema,
    ) -> Thesis:
        if not any(drafts[aid].logprob is not None for aid in agent_ids if aid in drafts):
            return self._fallback.select(drafts, agent_ids, claim_id, schema)
        author_id = max(
            agent_ids,
            key=lambda aid: (
                drafts[aid].logprob if drafts[aid].logprob is not None else float("-inf"),
                -len(schema.slice_rationale(drafts[aid], claim_id)),
            ),
        )
        draft = drafts[author_id]
        choice = schema.extract(draft.ranking, list(draft.ranking.keys())).get(claim_id, "")
        return Thesis(
            claim_id=claim_id,
            choice=choice,
            author_id=author_id,
            rationale=schema.slice_rationale(draft, claim_id) or draft.rationale,
            coalition_agent_ids=list(agent_ids),
            coalition_size=len(agent_ids),
        )


SELECTORS = {
    "rationale_span": RationaleSpanSelector,
    "logprob": LogprobSelector,
}


def get_thesis_selector(name: str):
    try:
        return SELECTORS[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown thesis selector: {name}") from exc
