"""Pot of Gold side bet (M10a): settlement, engine token counting, wrappers.

Published references (Wizard of Odds Free Bet Blackjack page, fetched
2026-07-18, six decks on the RIDE_FREE_WOO ruleset): Pay Table 1 house edge
5.77% under normal play / 2.75% when free-splitting 5s; Pay Table 2 4.64%;
splitting 5s costs the main bet 0.15%. WoO's token probability table (the
distribution the M10a gate checks category by category):

    tokens:      0         1         2         3         4         5         6         7
    P:       0.833420  0.148155  0.013488  0.003866  0.000847  0.000194  0.000027  0.000002

Settlement semantics per the Nevada rules-of-play filing (fetched 2026-07-18):
a lammer is collected when the free bet is granted and KEPT whether that hand
wins, loses, or pushes; all Pot of Gold wagers lose to a dealer blackjack.
"""

import dataclasses

import pytest

from ridefree.engine import Action, play_round
from ridefree.rules import (
    PAYTABLE_POG_1,
    PAYTABLE_POG_2,
    PAYTABLE_POG_04,
    RIDE_FREE,
    RIDE_FREE_WOO,
    STANDARD_6D_H17,
)
from ridefree.side_bets import settle_pot_of_gold
from ridefree.simulator import simulate
from ridefree.strategy import (
    AlwaysPotOfGold,
    AlwaysSideBet,
    BasicStrategy,
    ScriptedStrategy,
    SplitFives,
)

RULES_POG = dataclasses.replace(RIDE_FREE_WOO, side_bet_pot_of_gold=PAYTABLE_POG_1)

# WoO's published token distribution (six decks, normal strategy,
# paytable-independent). Probabilities are backed out of their PT1 return
# column (return_k / pays_k), which carries more precision than the printed
# 6-decimal probability column; the printed values round to these.
WOO_TOKEN_P = {
    0: 0.833420,
    1: 0.444466 / 3,
    2: 0.134884 / 10,
    3: 0.115973 / 30,
    4: 0.050799 / 60,
    5: 0.019445 / 100,
    6: 0.008140 / 300,
    7: 0.002026 / 1000,
}


# --- settlement is paytable-as-data ------------------------------------------

def test_settle_every_rung_of_pay_table_1():
    pays = (3, 10, 30, 60, 100, 300, 1000)
    for tokens, pay in enumerate(pays, start=1):
        assert settle_pot_of_gold(PAYTABLE_POG_1, tokens, 1.0) == pay
    assert settle_pot_of_gold(PAYTABLE_POG_1, 0, 1.0) == -1.0
    assert settle_pot_of_gold(PAYTABLE_POG_1, 2, 5.0) == 50.0  # stake scales


def test_settle_caps_at_top_rung_and_variants_differ():
    # Beyond-top counts pay the top rung (data semantics; unreachable at
    # max_hands=4 where 3 free splits + 4 free doubles = 7 is the maximum).
    assert settle_pot_of_gold(PAYTABLE_POG_1, 8, 1.0) == 1000.0
    assert settle_pot_of_gold(PAYTABLE_POG_2, 2, 1.0) == 12.0
    assert settle_pot_of_gold(PAYTABLE_POG_2, 7, 1.0) == 100.0
    assert settle_pot_of_gold(PAYTABLE_POG_04, 6, 1.0) == 299.0  # NV POG-04


def test_published_table_arithmetic_pins_the_gate_targets():
    """The WoO probability table times each paytable must reproduce the
    published house edges — the arithmetic the M10a gate scores against."""
    def edge(paytable):
        return sum(
            p * settle_pot_of_gold(paytable, k, 1.0) for k, p in WOO_TOKEN_P.items()
        )

    assert edge(PAYTABLE_POG_1) == pytest.approx(-0.057687, abs=2e-6)
    assert edge(PAYTABLE_POG_2) == pytest.approx(-0.0464, abs=1e-4)


def test_negative_payout_rejected():
    with pytest.raises(ValueError):
        dataclasses.replace(RIDE_FREE, side_bet_pot_of_gold=(3.0, -1.0))


def test_exact_p0_is_dealing_arithmetic():
    """Tier-1 reference: P(0 lammers) is strategy-free — initial two cards not
    free-bet eligible, or dealer blackjack. Exact six-deck value 0.838228071.
    WoO's simulated table says 0.833420: irreconcilable with the stated rules
    (their sim appears to let lammers survive ten-up dealer naturals; the
    reconciliation arithmetic is E19). Resplit rules cannot touch P(0), so
    both Ride Free configs share the value."""
    from ridefree.side_bets import exact_p0_pot_of_gold

    assert exact_p0_pot_of_gold(RIDE_FREE_WOO) == pytest.approx(
        0.838228071, abs=1e-9
    )
    assert exact_p0_pot_of_gold(RIDE_FREE) == exact_p0_pot_of_gold(RIDE_FREE_WOO)
    # Identity: 1 - P(elig) + P(elig & BJ), with P(elig) itself pinned by the
    # component arithmetic (pairs A-9 + non-pair hard 9/10/11, six decks).
    pairs = 9 * (24 * 23) / (312 * 311)
    nonpair = 10 * 2 * (24 * 24) / (312 * 311)
    assert pairs + nonpair == pytest.approx(0.169923, abs=5e-7)


# --- engine token counting on scripted shoes ----------------------------------

class FakeShoe:
    """Deals a scripted card sequence with the Shoe's public deal() interface."""

    def __init__(self, cards):
        self._cards = list(cards)

    def deal(self):
        return self._cards.pop(0)


def _round(cards, actions, rules=RULES_POG, strategy=None):
    inner = strategy or ScriptedStrategy(list(actions))
    return play_round(rules, FakeShoe(cards), AlwaysPotOfGold(inner), bet=1.0)


def test_one_free_double_pays_three_to_one():
    # Player 6,4 (hard 10) vs 9: free double, draw 10 -> 20 beats dealer 17.
    r = _round([6, 9, 4, 8, 10], [Action.DOUBLE])
    assert r.free_doubles == 1 and r.free_splits == 0
    assert r.pog_stake == 1.0 and r.pog_tokens == 1 and r.pog_profit == 3.0
    assert r.profit == 2.0 + 3.0  # own 1 + free 1 win, plus the side bet


def test_lammer_kept_when_hands_lose():
    # 8,8 vs 10: free split, both hands stand 17 and lose to dealer 19 —
    # the lammer still pays 3:1 (NV rules: win/lose/push all keep it).
    r = _round([8, 10, 8, 9, 9, 9], [Action.SPLIT, Action.STAND, Action.STAND])
    assert r.free_splits == 1
    assert r.pog_tokens == 1 and r.pog_profit == 3.0
    assert r.profit == -1.0 + 0.0 + 3.0  # own-money hand loses, free hand costs 0


def test_lammer_kept_when_split_hand_busts():
    # 8,8 vs 10: free split; first hand hits 13 into a bust, second stands 18
    # and loses to the dealer 19 — the lammer still pays.
    r = _round(
        [8, 10, 8, 9, 5, 10, 10],
        [Action.SPLIT, Action.HIT, Action.STAND],
    )
    assert r.free_splits == 1 and r.pog_tokens == 1 and r.pog_profit == 3.0


def test_split_plus_two_free_doubles_is_three_lammers():
    # 3,3 vs 6: free split; both hands land two-card 9/10 and free-double.
    r = _round(
        [3, 6, 3, 10, 6, 10, 7, 9, 10],
        [Action.SPLIT, Action.DOUBLE, Action.DOUBLE],
    )
    assert r.free_splits == 1 and r.free_doubles == 2
    assert r.pog_tokens == 3 and r.pog_profit == 30.0
    assert r.profit == 4.0 + 30.0  # four winning wager units + the side bet


def test_seven_lammers_pay_the_jackpot():
    # 5,5 resplit to four hands, every hand free-doubles: 3 + 4 = 7 lammers.
    cards = [5, 6, 5, 10, 5, 5, 4, 10, 5, 10, 6, 10, 6, 9, 10]
    actions = [Action.SPLIT, Action.SPLIT, Action.SPLIT,
               Action.DOUBLE, Action.DOUBLE, Action.DOUBLE, Action.DOUBLE]
    r = _round(cards, actions)
    assert r.free_splits == 3 and r.free_doubles == 4
    assert r.pog_tokens == 7 and r.pog_profit == 1000.0
    assert r.profit == 8.0 + 1000.0  # all four doubled hands beat the bust


def test_dealer_blackjack_loses_the_stake():
    r = _round([5, 1, 5, 10], [])
    assert not r.dealer_played_out
    assert r.pog_stake == 1.0 and r.pog_tokens == 0 and r.pog_profit == -1.0
    assert r.profit == -1.0 - 1.0


def test_player_natural_loses_the_stake():
    r = _round([1, 9, 10, 8], [])
    assert r.player_natural
    assert r.pog_profit == -1.0
    assert r.profit == 1.5 - 1.0


def test_no_hook_and_no_paytable_mean_no_stake():
    # Strategy without the hook: nothing staked even though the rules offer it.
    r = play_round(RULES_POG, FakeShoe([8, 10, 7, 9, 10]), BasicStrategy(), bet=1.0)
    assert r.pog_stake == 0.0 and r.pog_profit == 0.0
    # Rules without the paytable: the wrapper's stake is never taken.
    r = _round([8, 10, 7, 9, 10], [Action.HIT, Action.STAND], rules=RIDE_FREE_WOO,
               strategy=BasicStrategy())
    assert r.pog_stake == 0.0 and r.pog_profit == 0.0


def test_wrappers_compose_in_either_order():
    both = AlwaysPotOfGold(AlwaysSideBet(BasicStrategy()))
    assert both.bet_pot_of_gold(RULES_POG) == 1.0
    assert both.bet_21p3(RULES_POG) == 1.0
    both = AlwaysSideBet(AlwaysPotOfGold(BasicStrategy()))
    assert both.bet_pot_of_gold(RULES_POG) == 1.0
    assert both.bet_21p3(RULES_POG) == 1.0


# --- the SplitFives farm wrapper ----------------------------------------------

def test_split_fives_takes_the_free_split():
    # 5,5 vs 6 with a free split on offer: the farm splits where basic play
    # free-doubles the hard 10. Cards: split hands draw 10,10 -> two 15s that
    # stand vs the dealer 6 per basic strategy... dealer 6,10,10 busts 26.
    r = play_round(
        RULES_POG, FakeShoe([5, 6, 5, 9, 10, 10, 10]),
        AlwaysPotOfGold(SplitFives(BasicStrategy())), bet=1.0,
    )
    assert r.free_splits >= 1 and r.did_split
    # Same deal WITHOUT the wrapper: BasicStrategy plays 5,5 as hard 10.
    r2 = play_round(
        RULES_POG, FakeShoe([5, 6, 5, 9, 10, 10, 10]),
        AlwaysPotOfGold(BasicStrategy()), bet=1.0,
    )
    assert not r2.did_split


def test_split_fives_delegates_when_split_is_not_free():
    # Standard blackjack: no free splits exist, so 5,5 falls through to the
    # inner strategy (hard 10 doubles vs 6).
    rules = STANDARD_6D_H17
    r = play_round(
        rules, FakeShoe([5, 6, 5, 9, 10, 10, 10]),
        SplitFives(BasicStrategy()), bet=1.0,
    )
    assert not r.did_split and r.did_double


def test_split_fives_farms_more_tokens():
    from ridefree.player_ev import OptimalStrategy

    rules = dataclasses.replace(RULES_POG, shoe_end_mode="csm")
    base = simulate(rules, AlwaysPotOfGold(OptimalStrategy()),
                    seed=16_800_000_001, rounds=20_000)
    farm = simulate(rules, AlwaysPotOfGold(SplitFives(OptimalStrategy())),
                    seed=16_800_000_001, rounds=20_000)
    def tokens(m):
        return sum(k * v for k, v in m.pog_tokens.items())
    def multi(m):
        return sum(v for k, v in m.pog_tokens.items() if k >= 2)
    assert tokens(farm) > tokens(base)
    assert multi(farm) > multi(base)
    # (The farm's ~0.15% main-game cost is real but far below noise at this
    # sample size — the 10M-round M10a gate is what measures it.)


# --- simulator integration, determinism, and the untouched-main brace ---------

def test_metrics_histogram_and_max_tokens():
    from ridefree.player_ev import OptimalStrategy

    rules = dataclasses.replace(RULES_POG, shoe_end_mode="csm")
    m = simulate(rules, AlwaysPotOfGold(OptimalStrategy()),
                 seed=16_800_000_001, rounds=20_000)
    assert m.pog_rounds == 20_000
    assert sum(m.pog_tokens.values()) == 20_000
    assert all(0 <= k <= 7 for k in m.pog_tokens)
    assert m.pog_stake_total == 20_000
    # Histogram is the sufficient statistic: profit reconstructs from it.
    profit = sum(
        v * settle_pot_of_gold(PAYTABLE_POG_1, k, 1.0)
        for k, v in m.pog_tokens.items()
    )
    assert m.pog_profit_total == pytest.approx(profit)


def test_pog_determinism():
    from ridefree.player_ev import OptimalStrategy

    runs = [
        simulate(RULES_POG, AlwaysPotOfGold(OptimalStrategy()),
                 seed=16_800_000_001, rounds=5_000)
        for _ in range(2)
    ]
    assert runs[0].total_profit == runs[1].total_profit
    assert runs[0].pog_tokens == runs[1].pog_tokens


def test_pog_leaves_the_main_game_untouched():
    """Staking Pot of Gold consumes no cards and changes no decisions: the
    blackjack half of the round must be identical with and without the bet."""
    from ridefree.player_ev import OptimalStrategy

    rules = dataclasses.replace(RULES_POG, shoe_end_mode="csm")
    with_pog = simulate(rules, AlwaysPotOfGold(OptimalStrategy()),
                        seed=16_800_000_002, rounds=20_000)
    plain = simulate(RIDE_FREE_WOO_CSM, OptimalStrategy(),
                     seed=16_800_000_002, rounds=20_000)
    assert with_pog.outcomes == plain.outcomes
    assert with_pog.free_splits == plain.free_splits
    assert with_pog.free_doubles == plain.free_doubles
    assert with_pog.player_naturals == plain.player_naturals
    assert with_pog.dealer_final == plain.dealer_final
    assert with_pog.total_profit - with_pog.pog_profit_total == pytest.approx(
        plain.total_profit
    )


RIDE_FREE_WOO_CSM = dataclasses.replace(RIDE_FREE_WOO, shoe_end_mode="csm")


# --- M10b pogcurve machinery ---------------------------------------------------

def test_pog_curve_totals_identity_and_determinism():
    from ridefree.experiments import merge_pog_curves, run_pog_curve

    rules = dataclasses.replace(RIDE_FREE, side_bet_pot_of_gold=PAYTABLE_POG_1)
    a = run_pog_curve(rules, seed=16_800_000_003, rounds=8_000, rules_name="rf")
    b = run_pog_curve(rules, seed=16_800_000_003, rounds=8_000, rules_name="rf")
    assert a.rounds == 8_000
    # Determinism: identical runs, bin for bin.
    assert a.pog_total == b.pog_total and a.main_total == b.main_total
    assert {k: (v.rounds, v.pog_profit, v.tokens) for k, v in a.bins.items()} == {
        k: (v.rounds, v.pog_profit, v.tokens) for k, v in b.bins.items()
    }
    # Identity: bins partition the rounds; totals reconstruct from bins.
    assert sum(x.rounds for x in a.bins.values()) == a.rounds
    assert sum(x.pog_profit for x in a.bins.values()) == pytest.approx(a.pog_total)
    assert sum(x.main_profit for x in a.bins.values()) == pytest.approx(a.main_total)
    # Merge: pooling a run with itself doubles every additive stat.
    m = merge_pog_curves([a, b])
    assert m.rounds == 16_000
    assert m.pog_total == pytest.approx(2 * a.pog_total)
    assert m.bins[0].rounds == 2 * a.bins[0].rounds


def test_pog_curve_json_round_trip(tmp_path):
    import json

    from ridefree.experiments import (
        load_pog_curve_json,
        pog_curve_to_json,
        run_pog_curve,
    )

    rules = dataclasses.replace(RIDE_FREE, side_bet_pot_of_gold=PAYTABLE_POG_1)
    res = run_pog_curve(rules, seed=16_800_000_003, rounds=4_000, rules_name="rf")
    path = tmp_path / "curve.json"
    with open(path, "w") as f:
        json.dump(pog_curve_to_json(res, 16_800_000_003), f)
    back = load_pog_curve_json(str(path))
    assert back.rounds == res.rounds
    assert back.paytable == res.paytable
    assert back.pog_total == res.pog_total
    assert {k: v.pog_profit for k, v in back.bins.items()} == {
        k: v.pog_profit for k, v in res.bins.items()
    }


def test_csm_always_bet_edge_near_nv_rules_prediction():
    """Smoke gate: 60k csm rounds inside 4 sigma of the NV-rules PT1 edge.
    WoO's published -5.7687% is under their sim's convention; correcting its
    P(0)/P(1) by the exact P(0) transfer (0.004808 of rounds at pay 3 vs -1)
    predicts -5.7687% - 1.923% = -7.69% for the game as actually ruled. Per-
    round sd ~4.1 units -> 4 sigma at 60k ~ +/-6.7%. The full M10a gate runs
    10M rounds per arm in data/m10a_gate.py."""
    from ridefree.player_ev import OptimalStrategy

    rules = dataclasses.replace(RULES_POG, shoe_end_mode="csm")
    m = simulate(rules, AlwaysPotOfGold(OptimalStrategy()),
                 seed=16_700_000_001, rounds=60_000)
    edge = m.pog_profit_total / m.pog_stake_total
    assert abs(edge - (-0.0769)) < 0.067
