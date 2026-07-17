import dataclasses

import pytest

from ridefree.rules import RIDE_FREE_PLACEHOLDER, STANDARD_6D_H17, Rules


def test_standard_preset_is_plain_blackjack():
    r = STANDARD_6D_H17
    assert r.decks == 6
    assert r.dealer_hits_soft_17
    assert r.blackjack_payout == 1.5
    assert not r.dealer_22_pushes
    assert r.free_double_totals == frozenset()
    assert r.free_split_ranks == frozenset()


def test_ride_free_preset_features():
    r = RIDE_FREE_PLACEHOLDER
    assert r.dealer_22_pushes
    assert r.free_double_totals == frozenset({9, 10, 11})
    assert not r.free_double_soft_allowed  # toggle; hard-only until confirmed
    assert 10 not in r.free_split_ranks  # no free splits on ten-value pairs
    assert r.free_split_ranks == frozenset(range(1, 10))
    assert r.blackjack_payout == 1.5


def test_rules_are_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        STANDARD_6D_H17.decks = 8  # type: ignore[misc]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"decks": 0},
        {"penetration": 0.0},
        {"penetration": 1.5},
        {"max_hands": 0},
        {"free_split_ranks": frozenset({0})},
        {"free_split_ranks": frozenset({11})},
    ],
)
def test_invalid_rules_rejected(kwargs):
    with pytest.raises(ValueError):
        Rules(**kwargs)
