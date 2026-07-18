"""Baccarat engine gates (M9a).

Two independent references, the M8b pattern:
1. Exact first-principles enumeration must equal Wizard of Odds' published
   8-deck combination table EXACTLY (integers), and reproduce every published
   probability and house edge (fetched 2026-07-17).
2. The simulator must agree with the enumeration statistically.

Published 8-deck references (WoO):
  total sequences 4,998,398,275,503,360
  banker 2,292,252,566,437,888 / player 2,230,518,282,592,256
  tie 475,627,426,473,216
  P(dragon 7) 0.022534, P(panda 8) 0.034543
  HE: classic banker -1.0579%, player -1.2351%, tie 8:1 -14.3596%,
      EZ banker -1.0183%, dragon 7 (40:1) -7.6113%, panda 8 (25:1) -10.1876%
"""

import functools
import math

import pytest

from ridefree.baccarat import (
    BACCARAT_8D,
    EZ_BACCARAT_8D,
    BaccaratRules,
    FlatBettor,
    composition_from_shoe,
    exact_outcomes,
    fresh_composition,
    play_baccarat_round,
    simulate_baccarat,
)
from ridefree.cards import Shoe


class _ListShoe:
    """Deals a scripted sequence of card values (1-10)."""

    def __init__(self, cards):
        self._cards = list(cards)

    def deal(self):
        return self._cards.pop(0)


_NO_BETS = FlatBettor(main=None)


def _round(cards, rules=EZ_BACCARAT_8D, bettor=_NO_BETS):
    return play_baccarat_round(rules, _ListShoe(cards), bettor)


# ---------------------------------------------------------------------------
# Tableau
# ---------------------------------------------------------------------------

# Deal order is player, banker, player, banker; then player third, banker third.


def test_natural_stops_all_drawing():
    r = _round([4, 2, 5, 3])  # player 4+5=9 natural, banker 2+3=5
    assert r.natural
    assert r.player_cards == (4, 5) and r.banker_cards == (2, 3)
    assert r.outcome == "player" and r.player_total == 9 and r.banker_total == 5


def test_double_natural_tie():
    r = _round([4, 9, 4, 9])  # player 8, banker (9+9)%10=8
    assert r.natural and r.outcome == "tie"


def test_player_stands_67_banker_draws_to_5():
    r = _round([2, 10, 4, 5, 10])  # player 6 stands; banker 5 draws a ten
    assert r.player_cards == (2, 4) and r.banker_cards == (10, 5, 10)
    assert r.outcome == "player" and r.player_total == 6 and r.banker_total == 5


def test_banker_3_stands_on_player_third_8():
    r = _round([2, 10, 2, 3, 8])  # player 4 draws 8 -> 2; banker 3 stands vs d=8
    assert r.player_cards == (2, 2, 8) and r.banker_cards == (10, 3)
    assert r.outcome == "banker" and r.banker_total == 3 and r.player_total == 2


def test_banker_3_draws_on_player_third_9_dragon7():
    # player 4 draws 9 -> 3; banker 3 draws vs d=9, gets 4 -> three-card 7 win
    r = _round([2, 10, 2, 3, 9, 4])
    assert r.banker_cards == (10, 3, 4) and r.banker_total == 7
    assert r.outcome == "banker" and r.banker_three_card_7
    assert not r.player_three_card_8


def test_banker_6_draws_on_player_third_6():
    r = _round([2, 10, 3, 6, 6, 10])  # player 5 draws 6 -> 1; banker 6 draws vs d=6
    assert r.banker_cards == (10, 6, 10) and r.banker_total == 6
    assert r.outcome == "banker"


def test_banker_6_stands_on_player_third_5():
    r = _round([2, 10, 3, 6, 5])  # player 5 draws 5 -> 0; banker 6 stands vs d=5
    assert r.banker_cards == (10, 6)
    assert r.outcome == "banker" and r.banker_total == 6


def test_banker_7_always_stands():
    r = _round([2, 3, 3, 4, 9])  # player 5 draws 9 -> 4; banker 7 stands
    assert r.banker_cards == (3, 4)
    assert r.outcome == "banker" and r.banker_total == 7
    assert not r.banker_three_card_7  # two-card 7 is not a dragon


def test_panda8_player_three_card_8_win():
    r = _round([1, 10, 3, 6, 4])  # player 4 draws 4 -> 8; banker 6 stands vs d=4
    assert r.player_cards == (1, 3, 4) and r.player_total == 8
    assert r.outcome == "player" and r.player_three_card_8


# ---------------------------------------------------------------------------
# Settlement
# ---------------------------------------------------------------------------

_DRAGON_DEAL = [2, 10, 2, 3, 9, 4]  # banker three-card 7 win (test above)


def test_ez_banker_pushes_on_dragon_but_dragon7_pays():
    bettor = FlatBettor(main=("banker", 10.0), dragon7=2.0, panda8=1.0)
    r = _round(_DRAGON_DEAL, EZ_BACCARAT_8D, bettor)
    assert r.main_profit == 0.0  # barred hand pushes the banker bet
    assert r.dragon7_profit == 2.0 * 40.0
    assert r.panda8_profit == -1.0
    assert r.profit == 80.0 - 1.0


def test_classic_banker_wins_with_commission_on_same_deal():
    bettor = FlatBettor(main=("banker", 10.0))
    r = _round(_DRAGON_DEAL, BACCARAT_8D, bettor)
    assert r.main_profit == pytest.approx(10.0 * 0.95)


def test_tie_pushes_main_and_pays_tie_bet():
    deal = [4, 9, 4, 9]  # double natural tie
    r = _round(deal, EZ_BACCARAT_8D, FlatBettor(main=("banker", 5.0), dragon7=1.0))
    assert r.main_profit == 0.0 and r.dragon7_profit == -1.0
    r = _round(deal, EZ_BACCARAT_8D, FlatBettor(main=("tie", 5.0)))
    assert r.main_profit == 5.0 * 8.0


def test_player_bet_pays_even_money():
    r = _round([4, 2, 5, 3], EZ_BACCARAT_8D, FlatBettor(main=("player", 3.0)))
    assert r.main_profit == 3.0


# ---------------------------------------------------------------------------
# Exact enumeration vs the published combination table (tier 1)
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=None)
def _exact_8d():
    return exact_outcomes(fresh_composition(8))


def test_exact_matches_woo_combination_table_exactly():
    out = _exact_8d()
    assert out.total == 4_998_398_275_503_360
    assert out.banker == 2_292_252_566_437_888
    assert out.player == 2_230_518_282_592_256
    assert out.tie == 475_627_426_473_216
    assert out.banker + out.player + out.tie == out.total
    assert 0 < out.dragon7 < out.banker
    assert 0 < out.panda8 < out.player


def test_exact_side_bet_probabilities_match_published():
    out = _exact_8d()
    assert out.p_dragon7 == pytest.approx(0.022534, abs=5e-7)
    assert out.p_panda8 == pytest.approx(0.034543, abs=5e-7)


def test_exact_house_edges_match_published():
    out = _exact_8d()
    assert out.ev_main(BACCARAT_8D, "banker") == pytest.approx(-0.010579, abs=2e-6)
    assert out.ev_main(BACCARAT_8D, "player") == pytest.approx(-0.012351, abs=2e-6)
    assert out.ev_main(BACCARAT_8D, "tie") == pytest.approx(-0.143596, abs=2e-6)
    assert out.ev_main(EZ_BACCARAT_8D, "banker") == pytest.approx(-0.010183, abs=2e-6)
    assert out.ev_dragon7(EZ_BACCARAT_8D) == pytest.approx(-0.076113, abs=2e-6)
    assert out.ev_panda8(EZ_BACCARAT_8D) == pytest.approx(-0.101876, abs=2e-6)


def test_exact_on_depleted_composition_is_consistent():
    # Removing cards must keep the identity banker+player+tie == total; a
    # composition stripped of 8s and 9s (nothing prevents banker draws less
    # often... they *enable* standing) should move the dragon 7 probability up,
    # per the published count's tags (8,9 = +2 when dealt away).
    comp = fresh_composition(8)
    comp[8] -= 20
    comp[9] -= 20
    out = exact_outcomes(comp)
    assert out.banker + out.player + out.tie == out.total
    assert out.p_dragon7 > _exact_8d().p_dragon7


# ---------------------------------------------------------------------------
# Simulator vs enumeration (tier 2, statistical) and determinism
# ---------------------------------------------------------------------------

# Seeds 7300000001-7300000003 consumed for M9a tests (from the 7.3e9 block).


def test_simulator_matches_exact_frequencies():
    out = _exact_8d()
    rounds = 120_000
    m = simulate_baccarat(
        EZ_BACCARAT_8D,
        FlatBettor(main=("banker", 1.0), dragon7=1.0, panda8=1.0),
        seed=7300000001,
        rounds=rounds,
    )
    for observed, p in [
        (m.outcomes.get("banker", 0), out.p_banker),
        (m.outcomes.get("player", 0), out.p_player),
        (m.outcomes.get("tie", 0), out.p_tie),
        (m.banker_three_card_7s, out.p_dragon7),
        (m.player_three_card_8s, out.p_panda8),
    ]:
        sigma = math.sqrt(p * (1 - p) * rounds)
        assert abs(observed - p * rounds) < 4.5 * sigma
    # Ledger identity: staked every round, every settlement explainable.
    assert m.dragon7_rounds == rounds and m.panda8_rounds == rounds
    assert m.main_wager_total == rounds
    assert m.total_profit == pytest.approx(
        m.main_profit_total + m.dragon7_profit_total + m.panda8_profit_total
    )


def test_deterministic_under_seed():
    kwargs = dict(seed=7300000002, rounds=20_000)
    bettor = lambda: FlatBettor(main=("banker", 1.0), dragon7=1.0)  # noqa: E731
    a = simulate_baccarat(EZ_BACCARAT_8D, bettor(), **kwargs)
    b = simulate_baccarat(EZ_BACCARAT_8D, bettor(), **kwargs)
    assert a.total_profit == b.total_profit
    assert a.outcomes == b.outcomes
    assert a.dragon7_profit_total == b.dragon7_profit_total
    c = simulate_baccarat(EZ_BACCARAT_8D, bettor(), seed=7300000003, rounds=20_000)
    assert c.outcomes != a.outcomes


def test_full_penetration_never_exhausts_the_shoe():
    rules = BaccaratRules(penetration=1.0, banker_commission=0.0,
                          banker_push_on_three_card_7=True)
    m = simulate_baccarat(rules, _NO_BETS, seed=7300000003, rounds=5_000)
    assert m.rounds == 5_000


def test_csm_mode_smoke():
    rules = BaccaratRules(shoe_end_mode="csm")
    m = simulate_baccarat(rules, FlatBettor(main=("banker", 1.0)),
                          seed=7300000002, rounds=2_000)
    assert m.rounds == 2_000 and m.main_wager_total == 2_000


def test_composition_from_shoe_collapses_tens():
    shoe = Shoe(8, 1.0, seed=1)
    comp = composition_from_shoe(shoe.remaining_composition())
    assert comp == fresh_composition(8)
    for _ in range(52):
        shoe.deal()
    comp = composition_from_shoe(shoe.remaining_composition())
    assert sum(comp.values()) == shoe.cards_remaining


# ---------------------------------------------------------------------------
# M9b: fast_outcomes, the WoO count, and the EV scan harness
# ---------------------------------------------------------------------------


def test_fast_outcomes_bit_identical_to_exact():
    import random

    from ridefree.baccarat import fast_outcomes

    comps = [fresh_composition(8)]
    c = fresh_composition(8)
    c[8] -= 20
    c[9] -= 20
    comps.append(c)
    rng = random.Random(7300000004)
    c = fresh_composition(8)
    pool = [v for v in range(10) for _ in range(c[v])]
    rng.shuffle(pool)
    for v in pool[:350]:
        c[v] -= 1
    comps.append(c)
    comps.append({0: 10, 2: 3, 4: 1, 5: 2, 7: 1})  # 17 cards, ranks exhausted
    for comp in comps:
        assert fast_outcomes(comp) == exact_outcomes(comp)


def test_dragon7_count_tags_and_true_count():
    from ridefree.baccarat import Dragon7Count

    count = Dragon7Count()
    count.observe_cards([4, 5, 6, 7])  # -4
    assert count.running == -4
    count.observe_cards([8, 9, 8])  # +6
    assert count.running == 2
    count.observe_cards([1, 2, 3, 10, 10])  # aces/2/3/tens are 0
    assert count.running == 2
    assert count.true_count(52) == pytest.approx(2.0)
    assert count.true_count(26) == pytest.approx(4.0)
    count.new_shoe()
    assert count.running == 0


def test_bac_ev_scan_smoke():
    from ridefree.experiments import format_bac_ev_scan, run_bac_ev_scan

    rules = BaccaratRules(penetration=0.95, banker_commission=0.0,
                          banker_push_on_three_card_7=True)
    res = run_bac_ev_scan(rules, seed=7300000005, rounds=3_000)
    assert res.rounds == 3_000 and res.shoes >= 30
    # Bet-when-positive dominates higher thresholds in round count.
    assert res.thresholds_d7[0.0][0] >= res.thresholds_d7[0.02][0]
    # Indicator accounting is consistent.
    assert 0 <= res.cal_d7_all[2] <= res.rounds
    assert res.cal_d7[2] <= res.cal_d7_all[2]
    assert -1.0 <= res.corr_d7_tc <= 1.0
    assert -1.0 <= res.corr_d7_p8 <= 1.0
    # Predicted mean EV should sit near the fresh-shoe -7.61% (cut-card
    # weighting shifts it only slightly).
    assert -0.10 < res.pred_sum_d7 / res.rounds < -0.05
    text = format_bac_ev_scan(res, min_cell=200)
    assert "WoO count comparator" in text and "calibration" in text
