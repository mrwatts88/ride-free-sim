"""Tests for effects of removal and the derived Ride Free count."""

import pytest

from ridefree.counting import RIDE_FREE_EOR, STANDARD_H17_EOR, CompositionTracker
from ridefree.eor import PER_DECK, effects_of_removal, eor_ev_shift
from ridefree.rules import RIDE_FREE, STANDARD_6D_H17

# Griffin, Theory of Blackjack p.44 (single deck S17): sign/order anchor.
GRIFFIN_SIGNS = {1: -1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 0, 9: -1, 10: -1}


def test_standard_eors_match_griffin_signs_and_order():
    _, eors = effects_of_removal(STANDARD_6D_H17)
    for rank, sign in GRIFFIN_SIGNS.items():
        if sign > 0:
            assert eors[rank] > 0.001
        elif sign < 0:
            assert eors[rank] < -0.001
        else:
            assert abs(eors[rank]) < 0.001  # the 8 is ~neutral
    # The 5 is the most valuable removal; the ace and ten the most costly.
    assert eors[5] == max(eors.values())
    assert min(eors, key=eors.get) in (1, 10)


def test_hardcoded_eors_regenerate():
    # The constants in counting.py must equal a fresh derivation (provenance).
    _, eor_h = effects_of_removal(STANDARD_6D_H17)
    _, eor_r = effects_of_removal(RIDE_FREE)
    for r in range(1, 11):
        assert STANDARD_H17_EOR[r] == pytest.approx(eor_h[r], abs=1e-6)
        assert RIDE_FREE_EOR[r] == pytest.approx(eor_r[r], abs=1e-6)


def test_ride_free_eors_differ_from_standard_as_expected():
    # The headline structural differences (Matt's hypothesis, confirmed):
    assert abs(RIDE_FREE_EOR[10]) < abs(STANDARD_H17_EOR[10]) / 2 * 1.2  # tens devalued
    assert abs(RIDE_FREE_EOR[1]) > 2.5 * abs(RIDE_FREE_EOR[10])  # ace >> ten
    assert RIDE_FREE_EOR[3] < STANDARD_H17_EOR[3] / 2  # 3s collapse
    assert RIDE_FREE_EOR[7] < STANDARD_H17_EOR[7] / 2  # 7s collapse
    assert RIDE_FREE_EOR[8] < -0.0005  # 8s flip negative


def test_eor_shift_matches_single_removal():
    # Removing one 5 from a single deck should shift the estimate by ~ +EOR[5].
    counts = dict(PER_DECK)
    counts[5] -= 1
    shift = eor_ev_shift(RIDE_FREE_EOR, counts, 51)
    assert shift == pytest.approx(RIDE_FREE_EOR[5], rel=0.10)


def test_rf_l2_count_is_balanced_and_tracks():
    from ridefree.counting import RF_L2_TAGS

    per_deck = {r: (16 if r == 10 else 4) for r in range(1, 11)}
    assert sum(RF_L2_TAGS[r] * per_deck[r] for r in per_deck) == 0
    t = CompositionTracker(6)
    assert t.rf_l2_true() == 0.0
    # Running count = sum of DEALT tags (hi-lo convention): a dealt 5 (+2) raises
    # it, a dealt ace (-2) cancels it exactly, a dealt ten (-1) sends it negative.
    t.observe_card(5)
    assert t.rf_l2_true() > 0
    t.observe_card(1)
    assert t.rf_l2_true() == pytest.approx(0.0)
    t.observe_card(10)
    assert t.rf_l2_true() < 0


def test_fresh_shoe_shift_is_zero():
    t = CompositionTracker(6)
    assert t.rf_ev_shift() == pytest.approx(0.0, abs=1e-12)
    # Depleting tens/aces (bad cards gone... tens are good to HOLD) lowers the shift.
    for _ in range(12):
        t.observe_card(10)
    for _ in range(4):
        t.observe_card(1)
    assert t.rf_ev_shift() < 0
    # Depleting small cards raises it.
    t2 = CompositionTracker(6)
    for _ in range(8):
        t2.observe_card(5)
        t2.observe_card(4)
    assert t2.rf_ev_shift() > 0
