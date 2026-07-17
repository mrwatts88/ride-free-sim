"""Tests for shoe replay, the composition strategy, and the paired harness."""

import pytest

from ridefree.cards import Shoe
from ridefree.experiments import run_deviation_value
from ridefree.player_ev import CompositionStrategy, OptimalStrategy
from ridefree.rules import RIDE_FREE
from ridefree.engine import play_round


def test_shoe_snapshot_restore_replays_identically():
    shoe = Shoe(6, 0.75, seed=5)
    pos = shoe.snapshot()
    first = [shoe.deal() for _ in range(20)]
    shoe.restore(pos)
    again = [shoe.deal() for _ in range(20)]
    assert first == again


def test_composition_strategy_matches_optimal_on_fresh_shoe():
    # With a full-shoe composition the live-weights model is ~the infinite-deck
    # model, so decisions should agree on the same dealt rounds (same shoe replay).
    base, dev = OptimalStrategy(), CompositionStrategy()
    shoe = Shoe(RIDE_FREE.decks, RIDE_FREE.penetration, seed=9)
    from ridefree.counting import CompositionTracker

    tracker = CompositionTracker(RIDE_FREE.decks)
    agree = 0
    total = 0
    for _ in range(30):  # one shoe's worth; no reshuffle logic in this loop
        start = shoe.snapshot()
        r1 = play_round(RIDE_FREE, shoe, base, bet=1.0)
        end = shoe.snapshot()
        shoe.restore(start)
        dev.set_composition(RIDE_FREE, tracker.counts)
        r2 = play_round(RIDE_FREE, shoe, dev, bet=1.0)
        shoe.restore(end)
        tracker.observe_round(r1)
        total += 1
        if r1.profit == r2.profit:
            agree += 1
    # Early in shoes the compositions are near-fresh: overwhelming agreement.
    assert agree / total > 0.90


def test_paired_harness_smoke():
    r = run_deviation_value(RIDE_FREE, seed=3, rounds=1_500)
    assert r.rounds == 1_500
    # Deviations should be rare and their absolute value bounded sanely.
    assert r.rounds_changed / r.rounds < 0.5
    assert abs(r.deviation_value) < 0.05
    # Windowed accumulators are consistent.
    assert 0 <= r.window_rounds <= r.rounds
