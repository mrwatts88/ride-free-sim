"""Tests for the exact dealer-odds calculator.

Micro-cases are hand-verifiable; the aggregate is checked against well-known published
dealer statistics; and the exact calc is cross-checked against a Monte Carlo run of
the real engine's dealer logic.
"""

import pytest

from ridefree import dealer_odds
from ridefree.rules import Rules

H17 = Rules(dealer_hits_soft_17=True)
S17 = Rules(dealer_hits_soft_17=False)


def test_distribution_sums_to_one():
    for up in range(1, 11):
        dist = dealer_odds.dealer_distribution(up, H17)
        assert sum(dist.values()) == pytest.approx(1.0, abs=1e-9)


def test_dealer_20_stands_hardcoded():
    # Starting from a made 20 (T,T): dealer always stands on 20, never draws.
    from ridefree.hand import hand_total  # noqa: F401

    memo = {}
    dist = dealer_odds._distribution([10, 10], H17, memo)
    assert dist == {20: 1.0}


def test_hard_16_never_stands():
    # From hard 16 the dealer must draw; outcome is 17-22 or deeper bust, never 16.
    memo = {}
    dist = dealer_odds._distribution([10, 6], H17, memo)
    assert 16 not in dist
    assert set(dist) <= {17, 18, 19, 20, 21, 22, "bust"}


def test_soft_17_h17_vs_s17_differ():
    # Under S17 the dealer stands on soft 17 (A,6) -> always 17.
    memo_s = {}
    d_s = dealer_odds._distribution([1, 6], S17, memo_s)
    assert d_s == {17: 1.0}
    # Under H17 the dealer hits soft 17, so it is NOT a certain 17.
    memo_h = {}
    d_h = dealer_odds._distribution([1, 6], H17, memo_h)
    assert d_h.get(17, 0.0) < 1.0


def test_bust_rate_vs_six_up_is_highest():
    busts = {up: dealer_odds.bust_probability(up, H17) for up in range(2, 11)}
    # Small up-cards bust far more often than big ones; 5/6 are the peak.
    assert busts[6] > busts[10]
    assert busts[5] > 0.40
    assert busts[10] < 0.25


def test_aggregate_bust_matches_published_h17():
    # Well-known: dealer busts ~28-29% overall under H17 (up-card from full deck).
    agg = dealer_odds.aggregate_distribution(H17)
    assert agg[22] + agg["bust"] == pytest.approx(0.2836, abs=0.01)


def test_dealer_22_probability_near_published():
    # WoO publishes 0.073536 for six decks H17; infinite-deck should be close.
    assert dealer_odds.dealer_22_probability(H17) == pytest.approx(0.0735, abs=0.004)


def test_peek_conditioning_excludes_naturals_and_normalizes():
    dist = dealer_odds.dealer_distribution(1, H17, exclude_natural=True)
    assert sum(dist.values()) == pytest.approx(1.0, abs=1e-9)
    unconditioned = dealer_odds.dealer_distribution(1, H17)
    # Removing the natural (a guaranteed 21) must lower the 21 mass.
    assert dist[21] < unconditioned[21]


def test_exact_matches_engine_monte_carlo():
    from ridefree.validation import dealer_monte_carlo

    mc = dealer_monte_carlo(H17, seed=123, trials=600_000)
    for up in (2, 6, 10, 1):
        n = sum(mc[up].values())
        obs = (mc[up].get(22, 0) + mc[up].get(23, 0)) / n
        ref = dealer_odds.bust_probability(up, H17)
        # ~60k trials/up-card: 4 std errors is a safe band.
        se = (ref * (1 - ref) / n) ** 0.5
        assert abs(obs - ref) < 4 * se
