"""Tests for the composition tracker, signals, and conditional-EV harness."""

import pytest

from ridefree.cards import Shoe, deck_composition
from ridefree.counting import HILO_TAGS, CompositionTracker, FREE_DOUBLE_COMBOS
from ridefree.engine import play_round
from ridefree.experiments import run_conditional_ev
from ridefree.rules import RIDE_FREE, Rules
from ridefree.strategy import BasicStrategy
from ridefree.player_ev import OptimalStrategy


def test_tracker_matches_shoe_composition_exactly():
    # The strongest invariant: after any number of observed rounds, the tracker's
    # counts equal the shoe's own remaining composition.
    rules = RIDE_FREE
    shoe = Shoe(rules.decks, rules.penetration, seed=77)
    tracker = CompositionTracker(rules.decks)
    strategy = OptimalStrategy()
    for _ in range(50):
        result = play_round(rules, shoe, strategy, bet=1.0)
        tracker.observe_round(result)
    assert tracker.counts == shoe.remaining_composition()
    assert tracker.cards_remaining == shoe.cards_remaining


def test_hilo_tags_are_balanced():
    comp = deck_composition(1)
    assert sum(HILO_TAGS[r] * comp[r] for r in comp) == 0


def test_hilo_running_from_known_cards():
    t = CompositionTracker(1)
    for card in (2, 3, 10, 1, 5):  # +1 +1 -1 -1 +1
        t.observe_card(card)
    assert t.hilo_running() == 1
    # true count = running / decks remaining
    assert t.hilo_true() == pytest.approx(1 / ((52 - 5) / 52))


def test_free_double_combos_complete():
    # Exactly the unordered no-ace no-ten combos summing to 9, 10, or 11.
    expected = {(2, 7), (3, 6), (4, 5), (2, 8), (3, 7), (4, 6), (5, 5),
                (2, 9), (3, 8), (4, 7), (5, 6)}
    assert set(FREE_DOUBLE_COMBOS) == expected


def test_pair_probability_matches_brute_force():
    t = CompositionTracker(1)
    n = t.cards_remaining
    # Fresh single deck: P(pair of a specific rank) = 4*3/(52*51); 9 non-ten ranks.
    assert t.p_free_split_pair() == pytest.approx(9 * 4 * 3 / (52 * 51))
    # Remove three 8s: rank 8 contributes 1*0 now.
    for _ in range(3):
        t.observe_card(8)
    n = t.cards_remaining
    expected = (8 * 4 * 3 + 1 * 0) / (n * (n - 1))
    assert t.p_free_split_pair() == pytest.approx(expected)


def test_free_double_probability_fresh_deck():
    t = CompositionTracker(6)
    # Brute force over the same combo list with fresh 6-deck counts.
    n = 312
    num = 0
    for a, b in FREE_DOUBLE_COMBOS:
        num += 24 * 23 if a == b else 2 * 24 * 24
    assert t.p_free_double_hand() == pytest.approx(num / (n * (n - 1)))
    # Removing small cards lowers the signal; removing tens raises it.
    rich = CompositionTracker(6)
    for _ in range(20):
        rich.observe_card(10)
    assert rich.p_free_double_hand() > t.p_free_double_hand()
    poor = CompositionTracker(6)
    for _ in range(10):
        poor.observe_card(5)
        poor.observe_card(6)
    assert poor.p_free_double_hand() < t.p_free_double_hand()


def test_conditional_ev_smoke():
    result = run_conditional_ev(
        Rules(), BasicStrategy(), seed=11, rounds=5_000
    )
    assert result.rounds == 5_000
    # Every round lands in exactly one bin per signal.
    for name, bins in result.by_signal.items():
        assert sum(b.rounds for b in bins.values()) == 5_000
    assert ("p_pair", "p_free_double") in result.correlations
    # EV magnitudes are sane.
    assert -0.10 < result.overall_ev < 0.05
