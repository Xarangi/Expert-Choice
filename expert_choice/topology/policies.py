from __future__ import annotations

from collections import defaultdict

from expert_choice.core.types import Coalition, ReplicationResult, Topology, VerifiedClaim


def _replication_index(
    replications: list[ReplicationResult],
) -> dict[tuple[str, str], ReplicationResult]:
    return {(result.claim_id, result.choice): result for result in replications}


def _verified_from_coalition(
    coalition: Coalition,
    result: ReplicationResult | None,
    extra_hubs: list[str] | None = None,
) -> VerifiedClaim:
    rate = 1.0 if result is None and not extra_hubs else (result.replication_rate if result else 0.0)
    if result is not None:
        rate = result.replication_rate
    hub_ids = extra_hubs if extra_hubs is not None else [coalition.thesis.author_id]
    return VerifiedClaim(
        claim_id=coalition.claim_id,
        choice=coalition.choice,
        rationale=coalition.thesis.rationale,
        hub_ids=list(dict.fromkeys(hub_ids)),
        replication_rate=rate,
        coalition_size=coalition.coalition_size,
    )


def _topology_from_verified(
    agent_ids: list[str], verified: list[VerifiedClaim]
) -> Topology:
    hubs_by_claim: dict[str, list[str]] = {}
    hub_set: set[str] = set()
    for claim in verified:
        hubs_by_claim[claim.claim_id] = list(claim.hub_ids)
        hub_set.update(claim.hub_ids)

    speaking_rights = {agent_id: (1.0 if agent_id in hub_set else 0.0) for agent_id in agent_ids}
    edges: list[tuple[str, str]] = []
    for hub in sorted(hub_set):
        for listener in agent_ids:
            if listener != hub:
                edges.append((hub, listener))
    return Topology(
        speaking_rights=speaking_rights,
        hubs_by_claim=hubs_by_claim,
        verified_claims=verified,
        edges=edges,
    )


def _best_coalitions_by_key(
    coalitions: list[Coalition],
    key_fn,
) -> dict[str, list[Coalition]]:
    grouped: dict[str, list[Coalition]] = defaultdict(list)
    for coalition in coalitions:
        grouped[coalition.claim_id].append(coalition)

    winners: dict[str, list[Coalition]] = {}
    for claim_id, group in grouped.items():
        scored = [(key_fn(c), c) for c in group]
        best = max(scored, key=lambda row: row[0])[0]
        winners[claim_id] = [c for score, c in scored if score == best]
    return winners


class MaxReplicationPolicy:
    """Threshold-free: per claim, promote the thesis with highest complement replication."""

    name = "max_replication"

    def build(
        self,
        agent_ids: list[str],
        coalitions: list[Coalition],
        replications: list[ReplicationResult],
    ) -> Topology:
        index = _replication_index(replications)
        tested = {(c.claim_id, c.choice) for c in coalitions if (c.claim_id, c.choice) in index}

        def key(coalition: Coalition) -> tuple[float, int]:
            result = index.get((coalition.claim_id, coalition.choice))
            if result is None:
                return (float("-inf"), coalition.coalition_size)
            return (result.replication_rate, coalition.coalition_size)

        candidates = [
            c for c in coalitions if (c.claim_id, c.choice) in tested or not index
        ]
        if not candidates:
            candidates = coalitions
        winners = _best_coalitions_by_key(candidates, key)
        verified: list[VerifiedClaim] = []
        for group in winners.values():
            for coalition in group:
                co_hubs = [c.thesis.author_id for c in group]
                verified.append(
                    _verified_from_coalition(
                        coalition,
                        index.get((coalition.claim_id, coalition.choice)),
                        extra_hubs=co_hubs,
                    )
                )
        return _topology_from_verified(agent_ids, verified)


class MajoritySizePolicy:
    """Negative control: promote the largest coalition per claim (tyranny of majority)."""

    name = "majority_size"

    def build(
        self,
        agent_ids: list[str],
        coalitions: list[Coalition],
        replications: list[ReplicationResult],
    ) -> Topology:
        index = _replication_index(replications)
        winners = _best_coalitions_by_key(
            coalitions, lambda c: (c.coalition_size, -len(c.thesis.author_id))
        )
        verified: list[VerifiedClaim] = []
        for group in winners.values():
            co_hubs = [c.thesis.author_id for c in group]
            for coalition in group:
                verified.append(
                    _verified_from_coalition(
                        coalition,
                        index.get((coalition.claim_id, coalition.choice)),
                        extra_hubs=co_hubs,
                    )
                )
        return _topology_from_verified(agent_ids, verified)


class ReplicationAtLeastKPolicy:
    """Promote every thesis whose complement replication is at least k."""

    name = "replication_at_least_k"

    def __init__(self, k: float = 0.5) -> None:
        self.k = k

    def build(
        self,
        agent_ids: list[str],
        coalitions: list[Coalition],
        replications: list[ReplicationResult],
    ) -> Topology:
        index = _replication_index(replications)
        by_claim: dict[str, list[Coalition]] = defaultdict(list)
        for coalition in coalitions:
            by_claim[coalition.claim_id].append(coalition)

        verified: list[VerifiedClaim] = []
        for claim_id, group in by_claim.items():
            promoted = [
                c
                for c in group
                if (result := index.get((c.claim_id, c.choice))) is not None
                and result.replication_rate >= self.k
            ]
            if not promoted:
                continue
            for coalition in promoted:
                verified.append(
                    _verified_from_coalition(
                        coalition, index.get((coalition.claim_id, coalition.choice))
                    )
                )
        return _topology_from_verified(agent_ids, verified)


class GlobalWinnerPolicy:
    """Original single-expert method: one hub whose theses win the most claims."""

    name = "global_winner"

    def __init__(self) -> None:
        self._inner = MaxReplicationPolicy()

    def build(
        self,
        agent_ids: list[str],
        coalitions: list[Coalition],
        replications: list[ReplicationResult],
    ) -> Topology:
        multi = self._inner.build(agent_ids, coalitions, replications)
        counts: dict[str, float] = defaultdict(float)
        for claim in multi.verified_claims:
            for hub in claim.hub_ids:
                counts[hub] += 1.0 + claim.replication_rate
        if not counts:
            winner = agent_ids[0]
        else:
            winner = max(counts, key=lambda aid: (counts[aid], -agent_ids.index(aid)))

        index = _replication_index(replications)
        winner_coalitions = [
            c for c in coalitions if c.thesis.author_id == winner or winner in c.agent_ids
        ]
        # Prefer the coalition the winner actually belongs to for each claim.
        by_claim: dict[str, Coalition] = {}
        for coalition in winner_coalitions:
            if winner in coalition.agent_ids:
                by_claim[coalition.claim_id] = coalition
        verified = [
            _verified_from_coalition(
                coalition,
                index.get((coalition.claim_id, coalition.choice)),
                extra_hubs=[winner],
            )
            for coalition in by_claim.values()
        ]
        return _topology_from_verified(agent_ids, verified)


POLICIES = {
    "max_replication": MaxReplicationPolicy,
    "majority_size": MajoritySizePolicy,
    "replication_at_least_k": ReplicationAtLeastKPolicy,
    "global_winner": GlobalWinnerPolicy,
}


def get_topology_policy(name: str, replication_k: float = 0.5):
    if name == "replication_at_least_k":
        return ReplicationAtLeastKPolicy(k=replication_k)
    try:
        return POLICIES[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown topology policy: {name}") from exc
