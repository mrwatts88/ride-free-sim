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


# --- closed-form pre-deal EV (E10 core) --------------------------------------

def _enumerate_combos(counts):
    """Brute-force category counts by enumerating card-type triples —
    independent arithmetic to check the closed-form identities against."""
    from ridefree.side_bets import category_combos_21p3  # noqa: F401 (contrast)

    types = [t for t, c in counts.items() if c > 0]
    combos = {"straight_flush": 0, "three_of_a_kind": 0, "straight": 0,
              "flush": 0, None: 0}
    for a, b, c in combinations(types, 3):
        combos[classify_21p3(a, b, c)] += counts[a] * counts[b] * counts[c]
    for a in types:
        for b in types:
            if a != b and counts[a] >= 2:
                combos[classify_21p3(a, a, b)] += comb(counts[a], 2) * counts[b]
        if counts[a] >= 3:
            combos[classify_21p3(a, a, a)] += comb(counts[a], 3)
    return combos


def test_closed_form_matches_fresh_shoe_exactly():
    from ridefree.side_bets import category_combos_21p3, ev_21p3

    counts = {(r, s): 6 for r in range(1, 14) for s in range(4)}
    combos, total = category_combos_21p3(counts)
    assert total == 5_013_320
    assert combos == {"straight_flush": 10_368, "three_of_a_kind": 26_312,
                      "straight": 155_520, "flush": 292_896}
    assert abs(ev_21p3(counts, PAYTABLE_21P3_9TO1) - (-162_360 / 5_013_320)) < 1e-15


def test_closed_form_matches_enumeration_on_depleted_shoes():
    import random

    from ridefree.side_bets import category_combos_21p3

    rng = random.Random(987654321)
    types = [(r, s) for r in range(1, 14) for s in range(4)]
    for depth in (60, 150, 240, 280):
        counts = {t: 6 for t in types}
        deck = [t for t in types for _ in range(6)]
        rng.shuffle(deck)
        for card in deck[:depth]:
            counts[card] -= 1
        combos, total = category_combos_21p3(counts)
        brute = _enumerate_combos(counts)
        assert total == comb(312 - depth, 3)
        for cat in ("straight_flush", "three_of_a_kind", "straight", "flush"):
            assert combos[cat] == brute[cat], (depth, cat)


def test_ev_positive_when_one_suit_dominates():
    from ridefree.side_bets import ev_21p3

    # Remaining shoe: all six copies of every spade, one copy of everything else.
    counts = {(r, s): (6 if s == 0 else 1) for r in range(1, 14) for s in range(4)}
    assert ev_21p3(counts, PAYTABLE_21P3_9TO1) > 0.5


def test_raw_tracker_mirrors_shoe():
    from collections import Counter

    from ridefree.cards import Shoe
    from ridefree.counting import RawCompositionTracker
    from ridefree.side_bets import ev_21p3

    shoe = Shoe(decks=6, penetration=1.0, seed=31415)
    tracker = RawCompositionTracker(6)
    for _ in range(217):
        shoe.deal()
    tracker.observe(shoe.raw_dealt())
    remaining = Counter()
    for card in shoe.raw_dealt():
        remaining[card] += 1
    expect = {(r, s): 6 - remaining[(r, s)] for r in range(1, 14) for s in range(4)}
    assert tracker.counts == expect
    assert tracker.cards_remaining == shoe.cards_remaining
    # EV from tracker counts is finite and sane at depth.
    ev = ev_21p3(tracker.counts, PAYTABLE_21P3_9TO1)
    assert -0.5 < ev < 0.5


# --- E11a decomposition -------------------------------------------------------

def test_float_fracs_equal_int_combos():
    import random

    from ridefree.side_bets import category_combos_21p3, category_fracs_21p3

    rng = random.Random(24680)
    types = [(r, s) for r in range(1, 14) for s in range(4)]
    for depth in (0, 130, 250):
        counts = {t: 6 for t in types}
        deck = [t for t in types for _ in range(6)]
        rng.shuffle(deck)
        for card in deck[:depth]:
            counts[card] -= 1
        ints, total_i = category_combos_21p3(counts)
        floats, total_f = category_fracs_21p3(counts)
        assert total_f == total_i
        for cat, v in ints.items():
            assert floats[cat] == v, (depth, cat)


def test_decomposition_identities():
    from ridefree.experiments import sb_ev_components

    types = [(r, s) for r in range(1, 14) for s in range(4)]
    # Pure suit skew (ranks uniform within each suit): R and X must vanish.
    counts = {(r, s): (9, 5, 4, 2)[s] for r, s in types}
    f, b, s_term, r_term, x = sb_ev_components(counts, PAYTABLE_21P3_9TO1)
    assert abs(f - (b + s_term + r_term + x)) < 1e-12
    assert abs(r_term) < 1e-12 and abs(x) < 1e-12
    assert s_term > 0  # suit concentration always helps flushes (convexity)
    # Pure rank skew (suits uniform within each rank): S and X must vanish.
    skew = {r: 2 + (r % 3) for r in range(1, 14)}
    counts = {(r, s): skew[r] for r, s in types}
    f, b, s_term, r_term, x = sb_ev_components(counts, PAYTABLE_21P3_9TO1)
    assert abs(s_term) < 1e-12 and abs(x) < 1e-12
    # Fresh shoe: everything vanishes and F = B = published EV.
    counts = {t: 6 for t in types}
    f, b, s_term, r_term, x = sb_ev_components(counts, PAYTABLE_21P3_9TO1)
    assert abs(s_term) < 1e-12 and abs(r_term) < 1e-12 and abs(x) < 1e-12
    assert abs(f - (-162_360 / 5_013_320)) < 1e-12 and abs(f - b) < 1e-12


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


def test_side_bet_invariant_to_playing_strategy():
    """Differential brace: the side bet settles pre-play, so in csm mode
    (fresh shoe per round, same seed stream) its outcomes must be EXACTLY
    identical regardless of how the blackjack hands are played. Any strategy
    leakage into the side-bet path breaks this."""
    from ridefree.player_ev import OptimalStrategy
    from ridefree.strategy import FreeBetStrategy

    rules = dataclasses.replace(
        RIDE_FREE, side_bet_21p3=PAYTABLE_21P3_9TO1, shoe_end_mode="csm"
    )
    results = [
        simulate(rules, AlwaysSideBet(inner), seed=6_700_000_001, rounds=20_000)
        for inner in (BasicStrategy(), FreeBetStrategy(), OptimalStrategy())
    ]
    ref = results[0]
    for m in results[1:]:
        assert m.sb21p3_profit_total == ref.sb21p3_profit_total
        assert m.sb21p3_categories == ref.sb21p3_categories
    # ...while the blackjack profits DO differ (the strategies really diverge).
    main = [m.total_profit - m.sb21p3_profit_total for m in results]
    assert len(set(main)) > 1


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
