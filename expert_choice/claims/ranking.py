from __future__ import annotations

from heapq import heappop, heappush
from math import ceil
from typing import Optional

from expert_choice.claims.base import BaseClaimSchema
from expert_choice.core.types import VerifiedClaim


class PerItemRankSchema(BaseClaimSchema):
    """One sub-claim per item; discrete choice is the integer rank."""

    name = "per_item_rank"

    def claim_ids(self, items: list[str]) -> list[str]:
        return list(items)

    def extract(self, ranking: dict[str, int], items: list[str]) -> dict[str, str]:
        return {item: str(ranking[item]) for item in items if item in ranking}

    def assemble(
        self, verified: list[VerifiedClaim], items: list[str]
    ) -> Optional[dict[str, int]]:
        ranking: dict[str, int] = {}
        for claim in verified:
            try:
                rank = int(claim.choice)
            except ValueError:
                return None
            if claim.claim_id in ranking and ranking[claim.claim_id] != rank:
                return None
            ranking[claim.claim_id] = rank
        if set(ranking) != set(items):
            return None
        ranks = sorted(ranking.values())
        if ranks != list(range(1, len(items) + 1)):
            return None
        return ranking

    def describe_claim(self, claim_id: str, choice: str) -> str:
        return f'"{claim_id}" should be ranked {choice}'


class PairwiseOrderSchema(BaseClaimSchema):
    """Sub-claims are pairwise orderings. Choice is which item ranks better."""

    name = "pairwise_order"

    def claim_ids(self, items: list[str]) -> list[str]:
        ids: list[str] = []
        for i, left in enumerate(items):
            for right in items[i + 1 :]:
                ids.append(_pair_id(left, right))
        return ids

    def extract(self, ranking: dict[str, int], items: list[str]) -> dict[str, str]:
        extracted: dict[str, str] = {}
        for i, left in enumerate(items):
            if left not in ranking:
                continue
            for right in items[i + 1 :]:
                if right not in ranking:
                    continue
                claim_id = _pair_id(left, right)
                a, b = _pair_items(claim_id)
                extracted[claim_id] = "a_before_b" if ranking[a] < ranking[b] else "b_before_a"
        return extracted

    def assemble(
        self, verified: list[VerifiedClaim], items: list[str]
    ) -> Optional[dict[str, int]]:
        better: dict[str, set[str]] = {item: set() for item in items}
        worse: dict[str, set[str]] = {item: set() for item in items}
        indegree = {item: 0 for item in items}
        weight = {item: 0.0 for item in items}

        for claim in verified:
            a, b = _pair_items(claim.claim_id)
            if a not in indegree or b not in indegree:
                continue
            winner, loser = (a, b) if claim.choice == "a_before_b" else (b, a)
            if loser in better[winner]:
                continue
            better[winner].add(loser)
            worse[loser].add(winner)
            indegree[loser] += 1
            weight[winner] += claim.replication_rate

        heap: list[tuple[float, str]] = []
        for item in items:
            if indegree[item] == 0:
                heappush(heap, (-weight[item], item))

        order: list[str] = []
        while heap:
            _, item = heappop(heap)
            order.append(item)
            for nxt in sorted(better[item]):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    heappush(heap, (-weight[nxt], nxt))

        if len(order) != len(items):
            return None
        return {item: rank for rank, item in enumerate(order, start=1)}

    def describe_claim(self, claim_id: str, choice: str) -> str:
        a, b = _pair_items(claim_id)
        if choice == "a_before_b":
            return f'"{a}" should be ranked above "{b}"'
        return f'"{b}" should be ranked above "{a}"'

    def _needles(self, claim_id: str) -> list[str]:
        a, b = _pair_items(claim_id)
        return [a, b]


class RankBucketSchema(BaseClaimSchema):
    """Coarse top / mid / bottom buckets. Cannot uniquely assemble a permutation."""

    name = "rank_buckets"

    def claim_ids(self, items: list[str]) -> list[str]:
        return list(items)

    def extract(self, ranking: dict[str, int], items: list[str]) -> dict[str, str]:
        bounds = _bucket_bounds(len(items))
        extracted: dict[str, str] = {}
        for item in items:
            if item not in ranking:
                continue
            extracted[item] = _bucket_for_rank(ranking[item], bounds)
        return extracted

    def assemble(
        self, verified: list[VerifiedClaim], items: list[str]
    ) -> Optional[dict[str, int]]:
        return None

    def describe_claim(self, claim_id: str, choice: str) -> str:
        return f'"{claim_id}" belongs in the {choice} bucket'


class GlobalRankingSchema(BaseClaimSchema):
    """Single claim: the full ranking. Recovers a global-winner ablation."""

    name = "global_ranking"

    def claim_ids(self, items: list[str]) -> list[str]:
        return ["global"]

    def extract(self, ranking: dict[str, int], items: list[str]) -> dict[str, str]:
        if not ranking:
            return {}
        serialized = "|".join(
            f"{item}:{ranking[item]}" for item in items if item in ranking
        )
        return {"global": serialized}

    def assemble(
        self, verified: list[VerifiedClaim], items: list[str]
    ) -> Optional[dict[str, int]]:
        if not verified:
            return None
        best = max(verified, key=lambda c: (c.replication_rate, c.coalition_size))
        ranking: dict[str, int] = {}
        for part in best.choice.split("|"):
            if ":" not in part:
                return None
            item, rank_s = part.rsplit(":", 1)
            ranking[item] = int(rank_s)
        if set(ranking) != set(items):
            return None
        return ranking

    def describe_claim(self, claim_id: str, choice: str) -> str:
        return f"full ranking: {choice.replace('|', ', ')}"

    def slice_rationale(self, draft, claim_id: str) -> str:
        return draft.rationale


def _pair_id(left: str, right: str) -> str:
    a, b = sorted((left, right))
    return f"{a}||{b}"


def _pair_items(claim_id: str) -> tuple[str, str]:
    left, right = claim_id.split("||", 1)
    return left, right


def _bucket_bounds(n: int) -> tuple[int, int]:
    top_end = max(1, ceil(n / 3))
    bottom_start = n - top_end + 1
    if bottom_start <= top_end:
        bottom_start = top_end + 1
    return top_end, bottom_start


def _bucket_for_rank(rank: int, bounds: tuple[int, int]) -> str:
    top_end, bottom_start = bounds
    if rank <= top_end:
        return "top"
    if rank >= bottom_start:
        return "bottom"
    return "mid"


SCHEMAS: dict[str, type[BaseClaimSchema]] = {
    "per_item_rank": PerItemRankSchema,
    "pairwise_order": PairwiseOrderSchema,
    "rank_buckets": RankBucketSchema,
    "global_ranking": GlobalRankingSchema,
}


def get_claim_schema(name: str) -> BaseClaimSchema:
    try:
        return SCHEMAS[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown claim schema: {name}") from exc
