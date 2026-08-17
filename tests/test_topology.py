from __future__ import annotations

from expert_choice.core.types import Coalition, ReplicationResult, Thesis
from expert_choice.topology.policies import (
    GlobalWinnerPolicy,
    MajoritySizePolicy,
    MaxReplicationPolicy,
    ReplicationAtLeastKPolicy,
)


def _coalition(claim: str, choice: str, agents: list[str], author: str | None = None) -> Coalition:
    author = author or agents[0]
    thesis = Thesis(
        claim_id=claim,
        choice=choice,
        author_id=author,
        rationale=f"{claim}={choice}",
        coalition_agent_ids=agents,
        coalition_size=len(agents),
    )
    return Coalition(claim_id=claim, choice=choice, agent_ids=agents, thesis=thesis)


def _rep(claim: str, choice: str, coalition: Coalition, rate: float) -> ReplicationResult:
    return ReplicationResult(
        claim_id=claim,
        choice=choice,
        thesis=coalition.thesis,
        complement_ids=[],
        replication_rate=rate,
        unanimous=rate == 1.0,
    )


def test_max_replication_promotes_replicable_minority_not_majority():
    majority = _coalition("Alpha", "2", ["1", "2"], author="1")
    expert = _coalition("Alpha", "1", ["0"], author="0")
    topology = MaxReplicationPolicy().build(
        ["0", "1", "2"],
        [majority, expert],
        [
            _rep("Alpha", "2", majority, 0.0),
            _rep("Alpha", "1", expert, 1.0),
        ],
    )
    assert topology.hubs_by_claim["Alpha"] == ["0"]
    assert topology.speaking_rights == {"0": 1.0, "1": 0.0, "2": 0.0}
    assert topology.verified_claims[0].choice == "1"


def test_majority_size_is_tyranny_control():
    majority = _coalition("Alpha", "2", ["1", "2"], author="1")
    expert = _coalition("Alpha", "1", ["0"], author="0")
    topology = MajoritySizePolicy().build(
        ["0", "1", "2"],
        [majority, expert],
        [_rep("Alpha", "2", majority, 0.0), _rep("Alpha", "1", expert, 1.0)],
    )
    assert topology.hubs_by_claim["Alpha"] == ["1"]
    assert topology.verified_claims[0].choice == "2"


def test_replication_at_least_k_can_leave_claim_unverified():
    weak = _coalition("Alpha", "1", ["0"], author="0")
    topology = ReplicationAtLeastKPolicy(k=0.75).build(
        ["0", "1"],
        [weak],
        [_rep("Alpha", "1", weak, 0.5)],
    )
    assert topology.verified_claims == []
    assert topology.speaking_rights == {"0": 0.0, "1": 0.0}


def test_global_winner_collapses_to_single_hub():
    a0 = _coalition("Alpha", "1", ["0"], author="0")
    b0 = _coalition("Beta", "1", ["0"], author="0")
    a1 = _coalition("Alpha", "2", ["1"], author="1")
    topology = GlobalWinnerPolicy().build(
        ["0", "1"],
        [a0, b0, a1],
        [
            _rep("Alpha", "1", a0, 1.0),
            _rep("Beta", "1", b0, 1.0),
            _rep("Alpha", "2", a1, 0.0),
        ],
    )
    hubs = {hub for group in topology.hubs_by_claim.values() for hub in group}
    assert hubs == {"0"}
    assert topology.speaking_rights["1"] == 0.0
