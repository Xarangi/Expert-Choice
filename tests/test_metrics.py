from __future__ import annotations

from expert_choice.eval.metrics import relative_synergy_gap


def test_relative_synergy_gap_error_metric():
    assert relative_synergy_gap(20, 10) == 1.0
    assert relative_synergy_gap(10, 10) == 0.0
    assert relative_synergy_gap(0, 0) == 0.0
    assert relative_synergy_gap(5, 0) == 5.0
