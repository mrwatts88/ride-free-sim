"""Insurance: engine settlement, rules toggle, strategy hook, and the exact-EV
validation gate (doctrine: validate on the standard game against an independently
computed reference before trusting any variant behavior).

Deal order: player1, dealer-up, player2, dealer-hole, then draws in play order.
Insurance stakes half the main bet and pays rules.insurance_pays (2:1).
"""

import dataclasses

import pytest

from ridefree.engine import Action, play_round
from ridefree.player_ev import CompositionPlayer, OptimalStrategy
from ridefree.rules import RIDE_FREE, STANDARD_6D_H17
from ridefree.simulator import simulate
from ridefree.strategy import BasicStrategy, ScriptedStrategy
from test_engine import StackedShoe


class InsuringScript(ScriptedStrategy):
    def take_insurance(self, cards, rules):
        return True


class InsuringBasic(BasicStrategy):
    def take_insurance(self, cards, rules):
        return True


def test_insurance_pays_on_dealer_blackjack():
    # Player T,T=20 vs ace up, hole T -> dealer natural. Main loses 1; the 0.5
    # insurance pays 2:1 (+1.0) -> round exactly breaks even.
    r = play_round(STANDARD_6D_H17, StackedShoe([10, 1, 10, 10]), InsuringScript([]), bet=1.0)
    assert r.insurance_stake == pytest.approx(0.5)
    assert r.insurance_profit == pytest.approx(1.0)
    assert r.profit == pytest.approx(0.0)
    # Ledger: the hand line excludes insurance; only the round profit includes it.
    assert r.hands[0].profit == pytest.approx(-1.0)


def test_insurance_loses_without_dealer_blackjack():
    # Player T,9=19 vs ace up, hole 9 (soft 20, dealer stands). Main -1, insurance -0.5.
    r = play_round(
        STANDARD_6D_H17, StackedShoe([10, 1, 9, 9]), InsuringScript([Action.STAND]), bet=1.0
    )
    assert r.insurance_stake == pytest.approx(0.5)
    assert r.insurance_profit == pytest.approx(-0.5)
    assert r.profit == pytest.approx(-1.5)


def test_even_money_emerges_from_the_ledger():
    # Player blackjack + insurance, no dealer natural: 1.5 - 0.5 = the classic
    # "even money" +1.0, with no special-case code.
    r = play_round(STANDARD_6D_H17, StackedShoe([1, 1, 10, 9]), InsuringScript([]), bet=1.0)
    assert r.player_natural
    assert r.insurance_profit == pytest.approx(-0.5)
    assert r.profit == pytest.approx(1.0)


def test_no_insurance_without_ace_up():
    # Ten up never offers insurance (standard rule), even to a willing strategy.
    r = play_round(
        STANDARD_6D_H17, StackedShoe([10, 10, 9, 7]), InsuringScript([Action.STAND]), bet=1.0
    )
    assert r.insurance_stake == 0.0 and r.insurance_profit == 0.0


def test_insurance_rules_toggle():
    rules = dataclasses.replace(STANDARD_6D_H17, insurance_offered=False)
    r = play_round(rules, StackedShoe([10, 1, 9, 9]), InsuringScript([Action.STAND]), bet=1.0)
    assert r.insurance_stake == 0.0
    assert r.profit == pytest.approx(-1.0)


def test_default_strategies_never_insure():
    r = play_round(
        STANDARD_6D_H17, StackedShoe([10, 1, 9, 9]), BasicStrategy(), bet=1.0
    )
    assert r.insurance_stake == 0.0


def test_insurance_ev_matches_exact_six_deck_value():
    # Validation gate (computed reference, not a remembered figure): off the top
    # of a fresh 6-deck shoe, P(hole is ten | ace up) = 96/311 exactly, so
    # always-insure EV per insured round = 0.5 * (3 * 96/311 - 1) = -3.698%.
    # csm mode deals every round off a fresh shoe, matching that model.
    rules = dataclasses.replace(STANDARD_6D_H17, shoe_end_mode="csm")
    m = simulate(rules, InsuringBasic(), seed=20260717, rounds=60_000)
    p_ten = 96 / 311
    exact = 0.5 * ((1 + rules.insurance_pays) * p_ten - 1)
    assert m.insured_rounds / m.rounds == pytest.approx(1 / 13, abs=0.005)
    per_insured = m.insurance_profit_total / m.insured_rounds
    assert per_insured == pytest.approx(exact, abs=0.03)  # ~3 s.e. at this n
    # Bookkeeping: profit totals include insurance; stake totals are explainable.
    assert m.insurance_stake_total == pytest.approx(0.5 * m.insured_rounds)


def test_composition_player_both_off_matches_optimal():
    # With insurance and deviations disabled the CompositionPlayer must replay
    # OptimalStrategy's rounds identically (same seed, same shoe timeline).
    a = simulate(
        RIDE_FREE,
        CompositionPlayer(RIDE_FREE.decks, insurance=False, deviations=False),
        seed=6, rounds=4_000,
    )
    b = simulate(RIDE_FREE, OptimalStrategy(), seed=6, rounds=4_000)
    assert a.total_profit == b.total_profit
    assert a.hands == b.hands
    assert a.insured_rounds == 0


def test_composition_player_insures_selectively():
    # Insurance-only mode: takes insurance on composition, never always.
    m = simulate(
        RIDE_FREE,
        CompositionPlayer(RIDE_FREE.decks, insurance=True, deviations=False),
        seed=8, rounds=8_000,
    )
    ace_up_rate = 1 / 13  # rough; cut-card shoe varies
    assert 0 < m.insured_rounds < m.rounds * ace_up_rate  # some, never all ace-ups


def test_composition_player_full_smoke():
    # Both features on (the CLI sim default): runs, stays deterministic, sane edge.
    m1 = simulate(RIDE_FREE, CompositionPlayer(RIDE_FREE.decks), seed=9, rounds=1_500)
    m2 = simulate(RIDE_FREE, CompositionPlayer(RIDE_FREE.decks), seed=9, rounds=1_500)
    assert m1.total_profit == m2.total_profit  # deterministic under seed
    assert -0.10 < m1.edge < 0.05
