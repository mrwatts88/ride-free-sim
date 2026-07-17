"""Tests for the exact player EV calculator and the argmax OptimalStrategy.

The strongest correctness anchor: for standard rules, the derived play must agree
with our sim-validated BasicStrategy on famously non-borderline cells. For Free Bet,
we assert the deviations documented in fetched sources (hit 12v4, hit 13v2) and the
structural invariants of free money (a fully-free hand can never have negative EV).
"""

import pytest

from ridefree.engine import Action, HandView
from ridefree.player_ev import EVCalculator, OptimalStrategy, _draw
from ridefree.rules import RIDE_FREE, STANDARD_6D_H17

ALL = frozenset({Action.HIT, Action.STAND, Action.DOUBLE})


def view(cards, dealer_up, legal=ALL, own=1.0, free=0.0, is_split=False):
    from ridefree.hand import hand_total, is_soft

    return HandView(
        cards=tuple(cards),
        total=hand_total(list(cards)),
        soft=is_soft(list(cards)),
        pair_rank=cards[0] if len(cards) == 2 and cards[0] == cards[1] else None,
        dealer_up=dealer_up,
        is_split_hand=is_split,
        legal=legal,
        own_wager=own,
        free_wager=free,
    )


# --- _draw state arithmetic ------------------------------------------------

def test_draw_arithmetic():
    assert _draw(0, False, 1) == (11, True)  # lone ace
    assert _draw(11, True, 1) == (12, True)  # A,A = soft 12
    assert _draw(17, True, 10) == (17, False)  # soft 17 + T hardens to 17
    assert _draw(15, False, 1) == (16, False)  # ace as 1 on hard 15
    assert _draw(18, True, 5) == (13, False)  # soft 18 + 5 demotes


# --- EV sanity -------------------------------------------------------------

def test_stand_ev_ordering():
    calc = EVCalculator(STANDARD_6D_H17)
    evs = [calc.ev_final(t, 1.0, 0.0, 10) for t in (17, 18, 19, 20, 21)]
    assert evs == sorted(evs)  # higher standing total is never worse
    assert calc.ev_final(21, 1.0, 0.0, 10) > 0.5
    assert calc.ev_final(16, 1.0, 0.0, 10) < 0  # standing a stiff vs T is bad


def test_free_hand_ev_never_negative():
    # A hand carrying only casino money cannot lose player money: EV >= 0 always.
    calc = EVCalculator(RIDE_FREE)
    for total in (12, 14, 16, 18, 20):
        for up in (2, 6, 10, 1):
            assert calc.ev_final(total, 0.0, 1.0, up) >= 0
            assert calc.ev_play_on(total, False, 0.0, 1.0, up) >= 0


def test_dealer_22_push_lowers_standing_ev():
    # The same stand under push-22 rules is worth less: some dealer busts
    # become pushes.
    std = EVCalculator(STANDARD_6D_H17)
    rf = EVCalculator(RIDE_FREE)
    assert rf.ev_final(18, 1.0, 0.0, 6) < std.ev_final(18, 1.0, 0.0, 6)


# --- derived standard-game chart agrees with validated BasicStrategy -------

@pytest.mark.parametrize(
    "cards,up,expected",
    [
        ([10, 6], 10, Action.HIT),  # 16 v T
        ([10, 3], 2, Action.STAND),  # 13 v 2
        ([10, 2], 4, Action.STAND),  # 12 v 4
        ([10, 2], 2, Action.HIT),  # 12 v 2
        ([6, 5], 1, Action.DOUBLE),  # 11 v A under H17
        ([5, 4], 3, Action.DOUBLE),  # 9 v 3
        ([1, 7], 9, Action.HIT),  # A7 v 9
        ([1, 8], 6, Action.DOUBLE),  # A8 v 6 under H17
        ([10, 10], 6, Action.STAND),  # 20 v 6
    ],
)
def test_standard_cells_match_basic_strategy(cards, up, expected):
    strat = OptimalStrategy()
    assert strat.choose(view(cards, up), STANDARD_6D_H17) is expected


def test_standard_pair_cells():
    strat = OptimalStrategy()
    legal = frozenset(ALL | {Action.SPLIT})
    assert strat.choose(view([8, 8], 6, legal), STANDARD_6D_H17) is Action.SPLIT
    assert strat.choose(view([1, 1], 10, legal), STANDARD_6D_H17) is Action.SPLIT
    assert strat.choose(view([10, 10], 6, legal), STANDARD_6D_H17) is Action.STAND
    assert strat.choose(view([5, 5], 6, legal), STANDARD_6D_H17) is Action.DOUBLE


# --- Free Bet deviations and free-money play -------------------------------

def test_free_bet_hits_more_against_small_cards():
    # Documented Free Bet deviations vs standard play: dealer-22-push devalues
    # standing, so hit 12v4 and 13v2 (both stands in the standard game).
    strat = OptimalStrategy()
    assert strat.choose(view([10, 2], 4, ALL), RIDE_FREE) is Action.HIT
    assert strat.choose(view([10, 3], 2, ALL), RIDE_FREE) is Action.HIT
    # 12v5 and 12v6 still stand even in Free Bet.
    assert strat.choose(view([10, 2], 5, ALL), RIDE_FREE) is Action.STAND
    assert strat.choose(view([10, 2], 6, ALL), RIDE_FREE) is Action.STAND


def test_takes_free_double_and_split():
    strat = OptimalStrategy()
    legal = frozenset(ALL | {Action.SPLIT})
    assert strat.choose(view([6, 5], 10, ALL), RIDE_FREE) is Action.DOUBLE  # free 11
    assert strat.choose(view([4, 4], 10, legal, is_split=False), RIDE_FREE) is Action.SPLIT
    assert strat.choose(view([8, 8], 10, legal), RIDE_FREE) is Action.SPLIT
    # 5,5 free-doubles rather than free-splits (WoO: splitting fives costs 0.15%).
    assert strat.choose(view([5, 5], 6, legal), RIDE_FREE) is Action.DOUBLE


def test_free_hand_plays_more_aggressively():
    # Documented free-hand behavior (fetched source): free hands double soft 18-20
    # against certain upcards, which own-money hands never do. On a free hand a push
    # is as worthless as a loss, so upgrading the win payout is worth risking real
    # money on the double.
    strat = OptimalStrategy()
    own_view = view([1, 9], 6, ALL, own=1.0, free=0.0, is_split=True)
    free_view = view([1, 9], 6, ALL, own=0.0, free=1.0, is_split=True)
    assert strat.choose(own_view, RIDE_FREE) is Action.STAND
    assert strat.choose(free_view, RIDE_FREE) is Action.DOUBLE
    # ...but only vs certain upcards: soft 20 vs 5 still stands even on free money.
    assert strat.choose(view([1, 9], 5, ALL, own=0.0, free=1.0, is_split=True),
                        RIDE_FREE) is Action.STAND


def test_resplit_aces_decision():
    # A re-paired ace on a one-card split-ace hand: free resplit is chosen.
    strat = OptimalStrategy()
    v = HandView(
        cards=(1, 1), total=12, soft=True, pair_rank=1, dealer_up=10,
        is_split_hand=True, legal=frozenset({Action.STAND, Action.SPLIT}),
        free_split_available=True, own_wager=0.0, free_wager=1.0,
    )
    from ridefree.rules import RIDE_FREE_WOO

    assert strat.choose(v, RIDE_FREE_WOO) is Action.SPLIT
