"""Tests for shoe-end modes: cut_card, fixed_rounds, csm."""

import dataclasses

import pytest

from ridefree.rules import Rules
from ridefree.simulator import _MIN_CARDS, _needs_reshuffle, simulate
from ridefree.strategy import BasicStrategy


class FakeShoe:
    def __init__(self, remaining: int, needs_shuffle: bool) -> None:
        self.cards_remaining = remaining
        self.needs_shuffle = needs_shuffle


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        Rules(shoe_end_mode="banana")
    with pytest.raises(ValueError):
        Rules(rounds_per_shoe=0)


def test_cut_card_reshuffles_on_flag():
    r = Rules(shoe_end_mode="cut_card")
    assert not _needs_reshuffle(r, FakeShoe(200, needs_shuffle=False), rounds_since=99)
    assert _needs_reshuffle(r, FakeShoe(200, needs_shuffle=True), rounds_since=1)


def test_fixed_rounds_reshuffles_on_count_not_depth():
    r = Rules(shoe_end_mode="fixed_rounds", rounds_per_shoe=10)
    # cut card irrelevant in this mode
    assert not _needs_reshuffle(r, FakeShoe(200, needs_shuffle=True), rounds_since=5)
    assert _needs_reshuffle(r, FakeShoe(200, needs_shuffle=False), rounds_since=10)


def test_csm_reshuffles_every_round():
    r = Rules(shoe_end_mode="csm")
    assert not _needs_reshuffle(r, FakeShoe(300, needs_shuffle=False), rounds_since=0)
    assert _needs_reshuffle(r, FakeShoe(300, needs_shuffle=False), rounds_since=1)


def test_safety_floor_forces_reshuffle_in_every_mode():
    low = FakeShoe(_MIN_CARDS - 1, needs_shuffle=False)
    for mode in ("cut_card", "fixed_rounds", "csm"):
        r = Rules(shoe_end_mode=mode, rounds_per_shoe=10_000)
        assert _needs_reshuffle(r, low, rounds_since=0)


def test_all_modes_run_and_stay_solvent():
    # Smoke test: every mode completes a small sim without exhausting a shoe.
    for mode in ("cut_card", "fixed_rounds", "csm"):
        r = dataclasses.replace(Rules(), shoe_end_mode=mode)
        m = simulate(r, BasicStrategy(), seed=1, rounds=3000, bet=1.0)
        assert m.rounds == 3000
        assert -0.10 < m.edge < 0.05  # sane ballpark, not a validation gate
