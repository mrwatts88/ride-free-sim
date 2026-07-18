"""21+3 side bet (M8b): classification, exact combinatorics, engine settlement.

Tier-1 reference: category combination counts enumerated from first principles
over the 6-deck shoe, which must equal Wizard of Odds' published table for the
flat 9-to-1 paytable exactly (fetched 2026-07-17): straight flush 10,368;
three of a kind 26,312; straight 155,520; flush 292,896; total C(312,3) =
5,013,320; house edge 3.2386%.
"""

import dataclasses
from itertools import combinations
from math import comb

from ridefree.engine import play_round
from ridefree.rules import PAYTABLE_21P3_9TO1, RIDE_FREE, STANDARD_6D_H17
from ridefree.side_bets import classify_21p3, settle_21p3
from ridefree.simulator import simulate
from ridefree.strategy import AlwaysSideBet, BasicStrategy

RULES_21P3 = dataclasses.replace(STANDARD_6D_H17, side_bet_21p3=PAYTABLE_21P3_9TO1)


# --- classification ---------------------------------------------------------

def test_classify_basic_categories():
    assert classify_21p3((2, 0), (3, 0), (4, 0)) == "straight_flush"
    assert classify_21p3((2, 0), (3, 1), (4, 0)) == "straight"
    assert classify_21p3((2, 1), (9, 1), (13, 1)) == "flush"
    assert classify_21p3((7, 0), (7, 1), (7, 2)) == "three_of_a_kind"
    assert classify_21p3((2, 0), (9, 1), (13, 2)) is None
    assert classify_21p3((5, 0), (5, 1), (9, 2)) is None  # bare pair loses


def test_classify_ace_high_and_low_straights():
    assert classify_21p3((1, 0), (2, 1), (3, 2)) == "straight"  # A-2-3
    assert classify_21p3((12, 0), (13, 1), (1, 2)) == "straight"  # Q-K-A
    assert classify_21p3((13, 0), (1, 1), (2, 2)) is None  # K-A-2 does not wrap
    assert classify_21p3((1, 3), (13, 3), (12, 3)) == "straight_flush"


def test_classify_multideck_overlaps():
    # Three identical cards (possible with 6 decks) are trips, not a flush.
    assert classify_21p3((8, 2), (8, 2), (8, 2)) == "three_of_a_kind"
    # An identical pair plus a third of the same suit is a flush.
    assert classify_21p3((13, 0), (13, 0), (5, 0)) == "flush"


def test_settle_pays_from_paytable_as_data():
    cards = ((2, 1), (9, 1), (13, 1))  # flush
    assert settle_21p3(PAYTABLE_21P3_9TO1, cards, 2.0) == (18.0, "flush")
    no_flush = tuple(p for p in PAYTABLE_21P3_9TO1 if p[0] != "flush")
    assert settle_21p3(no_flush, cards, 2.0) == (-2.0, "flush")
    loser = ((2, 0), (9, 1), (13, 2))
    assert settle_21p3(PAYTABLE_21P3_9TO1, loser, 1.0) == (-1.0, None)


# --- tier-1: exact 6-deck combinatorics vs the published table --------------

def test_exact_six_deck_combinatorics_match_wizard_of_odds():
    decks = 6
    types = [(rank, suit) for rank in range(1, 14) for suit in range(4)]
    counts = {t: decks for t in types}
    combos = {"straight_flush": 0, "three_of_a_kind": 0, "straight": 0,
              "flush": 0, None: 0}
    # All distinct card types.
    for a, b, c in combinations(types, 3):
        combos[classify_21p3(a, b, c)] += counts[a] * counts[b] * counts[c]
    # Exactly two identical cards + one different type.
    for a in types:
        for b in types:
            if a != b:
                combos[classify_21p3(a, a, b)] += comb(counts[a], 2) * counts[b]
    # Three identical cards.
    for a in types:
        combos[classify_21p3(a, a, a)] += comb(counts[a], 3)

    total = comb(52 * decks, 3)
    assert sum(combos.values()) == total == 5_013_320
    # Wizard of Odds' combination table, flat 9-to-1 paytable, six decks
    # (their flush rows 236,736 + 56,160 = 292,896; suited trips are trips).
    assert combos["straight_flush"] == 10_368
    assert combos["three_of_a_kind"] == 26_312
    assert combos["straight"] == 155_520
    assert combos["flush"] == 292_896
    winners = total - combos[None]
    ev = (9 * winners - combos[None]) / total
    assert abs(ev - (-0.032386)) < 5e-7  # published house edge 3.2386%


# --- engine settlement -------------------------------------------------------

class FakeRawShoe:
    """Deals a scripted raw-card sequence with the Shoe's public interface."""

    def __init__(self, raw):
        self._raw = list(raw)
        self._pos = 0

    def deal(self):
        card = self._raw[self._pos]
        self._pos += 1
        return min(card[0], 10)

    def snapshot(self):
        return self._pos

    def raw_slice(self, start, stop):
        return tuple(self._raw[start:stop])


class NeverBet(BasicStrategy):
    pass


def _round(raw, strategy, rules=RULES_21P3):
    return play_round(rules, FakeRawShoe(raw), strategy, bet=1.0)


def test_engine_settles_flush_win_and_ledger():
    # player 2♠ 7♠, dealer up 9♠ (flush); hole 5♦; player 9 vs dealer draws.
    raw = [(2, 0), (9, 0), (7, 0), (5, 1)] + [(10, s % 4) for s in range(8)]
    result = _round(raw, AlwaysSideBet(BasicStrategy()))
    assert result.sb21p3_stake == 1.0
    assert result.sb21p3_category == "flush"
    assert result.sb21p3_profit == 9.0
    # Round profit = main-hand profit + side-bet profit, ledger-explainable.
    main = sum(h.profit for h in result.hands)
    assert result.profit == main + 9.0


def test_engine_settles_loss():
    raw = [(2, 0), (9, 1), (7, 2), (5, 1)] + [(10, s % 4) for s in range(8)]
    result = _round(raw, AlwaysSideBet(BasicStrategy()))
    assert result.sb21p3_profit == -1.0
    assert result.sb21p3_category is None


def test_side_bet_resolves_even_on_player_blackjack():
    # A♠ K♠ vs up Q♠: straight flush AND a player natural ending the round early.
    raw = [(1, 0), (12, 0), (13, 0), (5, 1)] + [(10, s % 4) for s in range(8)]
    result = _round(raw, AlwaysSideBet(BasicStrategy()))
    assert result.player_natural
    assert result.sb21p3_category == "straight_flush"
    assert result.profit == 1.5 + 9.0


def test_no_hook_and_no_paytable_mean_no_bet():
    raw = [(2, 0), (9, 0), (7, 0), (5, 1)] + [(10, s % 4) for s in range(8)]
    result = _round(raw, NeverBet())  # no bet_21p3 hook
    assert result.sb21p3_stake == 0.0 and result.sb21p3_profit == 0.0
    result = _round(raw, AlwaysSideBet(BasicStrategy()), rules=STANDARD_6D_H17)
    assert result.sb21p3_stake == 0.0  # bet not offered by the rules


def test_wrapper_delegates_to_inner_strategy():
    wrapped = AlwaysSideBet(BasicStrategy())
    assert wrapped.bet_21p3(RULES_21P3) == 1.0
    raw = [(2, 0), (9, 0), (7, 0), (5, 1)] + [(10, s % 4) for s in range(8)]
    assert _round(raw, wrapped).hands  # choose() reached via delegation


# --- statistical smoke + determinism (real Shoe, csm mode) -------------------

def test_csm_always_bet_edge_near_published():
    rules = dataclasses.replace(RULES_21P3, shoe_end_mode="csm")
    m = simulate(rules, AlwaysSideBet(BasicStrategy()), seed=6_400_000_001,
                 rounds=60_000)
    assert m.sb21p3_rounds == 60_000
    edge = m.sb21p3_profit_total / m.sb21p3_stake_total
    # sigma per round ~2.96 units; 4 sigma at 60k rounds ~ +/-4.8%
    assert abs(edge - (-0.032386)) < 0.048


def test_21p3_determinism_and_ridefree_compatibility():
    rules = dataclasses.replace(RIDE_FREE, side_bet_21p3=PAYTABLE_21P3_9TO1)
    from ridefree.player_ev import OptimalStrategy

    runs = [
        simulate(rules, AlwaysSideBet(OptimalStrategy()), seed=6_400_000_002,
                 rounds=5_000)
        for _ in range(2)
    ]
    assert runs[0].total_profit == runs[1].total_profit
    assert runs[0].sb21p3_categories == runs[1].sb21p3_categories
    assert runs[0].sb21p3_rounds == 5_000
