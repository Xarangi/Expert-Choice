from __future__ import annotations

from expert_choice.claims.ranking import (
    GlobalRankingSchema,
    PairwiseOrderSchema,
    PerItemRankSchema,
    RankBucketSchema,
)
from expert_choice.core.types import VerifiedClaim


ITEMS = ["Alpha", "Beta", "Gamma", "Delta"]


def _v(claim_id: str, choice: str, rate: float = 1.0) -> VerifiedClaim:
    return VerifiedClaim(
        claim_id=claim_id,
        choice=choice,
        rationale="r",
        hub_ids=["0"],
        replication_rate=rate,
        coalition_size=1,
    )


def test_per_item_assembly_valid_permutation():
    verified = [
        _v("Alpha", "1"),
        _v("Beta", "2"),
        _v("Gamma", "3"),
        _v("Delta", "4"),
    ]
    ranking = PerItemRankSchema().assemble(verified, ITEMS)
    assert ranking == {"Alpha": 1, "Beta": 2, "Gamma": 3, "Delta": 4}


def test_per_item_assembly_rejects_collisions():
    verified = [
        _v("Alpha", "1"),
        _v("Beta", "1"),
        _v("Gamma", "3"),
        _v("Delta", "4"),
    ]
    assert PerItemRankSchema().assemble(verified, ITEMS) is None


def test_pairwise_assembly_topological_sort():
    schema = PairwiseOrderSchema()
    ranking = {"Alpha": 1, "Beta": 2, "Gamma": 3, "Delta": 4}
    extracted = schema.extract(ranking, ITEMS)
    verified = [_v(cid, choice) for cid, choice in extracted.items()]
    assembled = schema.assemble(verified, ITEMS)
    assert assembled == ranking


def test_rank_buckets_cannot_uniquely_assemble():
    verified = [_v(item, "top") for item in ITEMS]
    assert RankBucketSchema().assemble(verified, ITEMS) is None


def test_global_ranking_roundtrip():
    schema = GlobalRankingSchema()
    ranking = {"Alpha": 1, "Beta": 2, "Gamma": 3, "Delta": 4}
    choice = schema.extract(ranking, ITEMS)["global"]
    assembled = schema.assemble([_v("global", choice)], ITEMS)
    assert assembled == ranking
