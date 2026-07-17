"""M3 gate: hand-level settlement tests for every free-money combination.

Free Bet semantics under test: a free (casino-funded) wager pays its winnings 1:1 on
a win but was never the player's money — it returns nothing on a push and costs the
player nothing on a loss. Player-funded wagers settle normally. Dealer 22 pushes all
live hands.

Deal order: player1, dealer-up, player2, dealer-hole, then draws in play order.
"""

import pytest

from ridefree.engine import Action, free_double_allowed, free_split_allowed, play_round
from ridefree.rules import RIDE_FREE, Rules
from ridefree.strategy import FreeBetStrategy, ScriptedStrategy
from test_engine import StackedShoe


def run(cards, actions, rules=RIDE_FREE, bet=1.0):
    return play_round(rules, StackedShoe(cards), ScriptedStrategy(actions), bet=bet)


# --- free split settlement ------------------------------------------------

def test_free_split_new_hand_is_casino_funded():
    # 8,8 vs 6: free split; h1 8,T=18 stand, h2 8,9=17 stand; dealer 6,T,9 -> 25 bust
    r = run([8, 6, 8, 10, 10, 9, 9], [Action.SPLIT, Action.STAND, Action.STAND])
    h1, h2 = r.hands
    assert (h1.wager, h1.free_wager) == (1.0, 0.0)
    assert (h2.wager, h2.free_wager) == (0.0, 1.0)
    assert r.free_splits == 1
    # both win: own-money hand +1, free hand pays its free winnings +1
    assert r.profit == pytest.approx(2.0)


def test_free_split_hand_loses_nothing():
    # 8,8 vs T (hole 9 -> dealer 19): both hands stand on 18 and lose.
    # Own hand loses 1; the free hand loses only the casino's button -> 0.
    r = run([8, 10, 8, 9, 10, 10], [Action.SPLIT, Action.STAND, Action.STAND])
    h1, h2 = r.hands
    assert h1.profit == pytest.approx(-1.0)
    assert h2.profit == pytest.approx(0.0)
    assert r.profit == pytest.approx(-1.0)


def test_free_split_hand_push_returns_nothing():
    # 9,9 vs 7 (hole T -> 17): free split; h1 9,8=17 push, h2 9,8=17 push.
    r = run([9, 7, 9, 10, 8, 8], [Action.SPLIT, Action.STAND, Action.STAND])
    h1, h2 = r.hands
    assert h1.outcome == "push" and h1.profit == 0.0
    assert h2.outcome == "push" and h2.profit == 0.0
    assert r.profit == 0.0


def test_ten_pair_split_is_paid_not_free():
    # T,T not in free_split_ranks: a (scripted, bad) split costs real money.
    r = run([10, 6, 10, 10, 9, 9, 9], [Action.SPLIT, Action.STAND, Action.STAND])
    h1, h2 = r.hands
    assert (h1.wager, h1.free_wager) == (1.0, 0.0)
    assert (h2.wager, h2.free_wager) == (1.0, 0.0)
    assert r.free_splits == 0


def test_free_resplit_buttons():
    # 2,2 vs 6: split to 4 hands (all free), then stand each.
    class SplitThenStand:
        def choose(self, view, rules):
            if Action.SPLIT in view.legal:
                return Action.SPLIT
            return Action.STAND

    cards = [2, 6, 2, 10] + [2] * 8 + [10, 9, 9]
    r = play_round(RIDE_FREE, StackedShoe(cards), SplitThenStand(), bet=1.0)
    assert len(r.hands) == 4
    assert [h.wager for h in r.hands] == [1.0, 0.0, 0.0, 0.0]
    assert [h.free_wager for h in r.hands] == [0.0, 1.0, 1.0, 1.0]
    assert r.free_splits == 3


def test_free_split_aces_one_card_each():
    # A,A vs 6: free split; one card each (T, 9); dealer 6,T,9 -> 25 bust; both win.
    r = run([1, 6, 1, 10, 10, 9, 9], [Action.SPLIT])
    h1, h2 = r.hands
    assert [len(h.cards) for h in (h1, h2)] == [2, 2]
    assert (h2.wager, h2.free_wager) == (0.0, 1.0)
    assert r.profit == pytest.approx(2.0)  # 21 and 20, no BJ bonus


# --- free double settlement -----------------------------------------------

def test_free_double_win_pays_both_units():
    # 6,5=hard 11 vs 9 (hole 8 -> 17): free double, draw T -> 21. Win +2.
    r = run([6, 9, 5, 8, 10], [Action.DOUBLE])
    h = r.hands[0]
    assert (h.wager, h.free_wager) == (1.0, 1.0)
    assert r.free_doubles == 1
    assert r.profit == pytest.approx(2.0)


def test_free_double_loss_costs_one_unit_only():
    # 6,5=11 vs 9 (hole 8 -> 17): free double, draw 2 -> 13. Lose only own unit.
    r = run([6, 9, 5, 8, 2], [Action.DOUBLE])
    assert r.hands[0].outcome == "lose"
    assert r.profit == pytest.approx(-1.0)  # a paid double would cost -2


def test_free_double_push_returns_own_wager_only():
    # 6,5=11 vs 9 (hole 8 -> 17): free double, draw 6 -> 17. Push -> 0.
    r = run([6, 9, 5, 8, 6], [Action.DOUBLE])
    assert r.hands[0].outcome == "push"
    assert r.profit == 0.0


def test_soft_two_card_nine_not_free_by_default():
    # A,8 is soft 19 (hard count 9): not free-eligible under the default toggle,
    # but hard 4,5=9 is.
    from ridefree.engine import _Hand

    soft = _Hand(cards=[1, 8], wager=1.0)
    hard = _Hand(cards=[4, 5], wager=1.0)
    assert not free_double_allowed(soft, RIDE_FREE)
    assert free_double_allowed(hard, RIDE_FREE)
    soft_ok = Rules(
        dealer_22_pushes=True,
        free_double_totals=frozenset({9, 10, 11}),
        free_double_soft_allowed=True,
    )
    assert free_double_allowed(soft, soft_ok)


def test_paid_double_on_non_eligible_total():
    # 8,4=hard 12 vs 6 is not free-eligible; scripted double costs real money.
    r = run([8, 6, 4, 10, 9, 10], [Action.DOUBLE])
    h = r.hands[0]
    assert (h.wager, h.free_wager) == (2.0, 0.0)
    assert r.free_doubles == 0


# --- stacked free money: free double after free split ---------------------

def test_free_double_after_free_split_wins_two():
    # 8,8 vs 6: free split. h1 draws 3 -> 8,3=11: FREE double, draws T -> 21.
    # h2 draws T -> 18, stands. Dealer 6,T,9 -> 25 bust.
    r = run(
        [8, 6, 8, 10, 3, 10, 10, 9],
        [Action.SPLIT, Action.DOUBLE, Action.STAND],
    )
    h1, h2 = r.hands
    # h1 kept the player's original wager and gained a free double button
    assert (h1.wager, h1.free_wager) == (1.0, 1.0)
    assert (h2.wager, h2.free_wager) == (0.0, 1.0)
    assert r.free_splits == 1 and r.free_doubles == 1
    assert r.profit == pytest.approx(3.0)  # h1 wins 2, h2 wins 1


def test_free_double_on_fully_free_hand_loses_zero():
    # The second (free-split) hand draws to hard 11 and free-doubles: the hand
    # carries no player money at all. It busts/loses -> costs 0.
    # 8,8 vs 7 (hole T -> 17): h1 8,T=18 stand (loses 1... wait dealer 17, 18 wins).
    # Use dealer 7,T=17: h1 8,T=18 stand -> win +1. h2 8,3=11 FREE double draw 4
    # -> 15 lose -> 0. Total +1.
    r = run(
        [8, 7, 8, 10, 10, 3, 4],
        [Action.SPLIT, Action.STAND, Action.DOUBLE],
    )
    h1, h2 = r.hands
    assert (h2.wager, h2.free_wager) == (0.0, 2.0)
    assert h2.outcome == "lose" and h2.profit == 0.0
    assert r.profit == pytest.approx(1.0)


def test_paid_double_on_free_split_hand_costs_one():
    # Free-split hand draws to a non-eligible total and (scripted) pays to double:
    # wager goes 0 -> 1 (+= bet, not *= 2 — the old bug this guards against).
    # 8,8 vs T hole 9 (dealer 19): h1 8,T=18 stand lose -1.
    # h2 8,4=12 paid double, draw 9 -> 21 win: own 1 + free button 1 -> +2.
    r = run(
        [8, 10, 8, 9, 10, 4, 9],
        [Action.SPLIT, Action.STAND, Action.DOUBLE],
    )
    h1, h2 = r.hands
    assert (h2.wager, h2.free_wager) == (1.0, 1.0)
    assert h2.profit == pytest.approx(2.0)
    assert r.profit == pytest.approx(1.0)  # -1 + 2


# --- dealer 22 interactions -----------------------------------------------

def test_dealer_22_pushes_free_double_hand():
    # 6,5=11 vs 6 (hole T=16): free double draw 9 -> 20. Dealer draws 6 -> 22: push.
    r = run([6, 6, 5, 10, 9, 6], [Action.DOUBLE])
    assert r.dealer_22_push
    assert r.hands[0].outcome == "push"
    assert r.profit == 0.0


def test_dealer_22_pushes_free_split_hands():
    # 8,8 vs 6 (hole T=16): free split, both stand 18; dealer draws 6 -> 22.
    r = run([8, 6, 8, 10, 10, 10, 6], [Action.SPLIT, Action.STAND, Action.STAND])
    assert r.dealer_22_push
    assert all(h.outcome == "push" for h in r.hands)
    assert r.profit == 0.0


def test_dealer_22_still_loses_to_nobody_busted():
    # Player busts first; dealer never plays (all dead) -> no 22 push flag.
    # T,6 vs 6: hit T -> 26 bust.
    r = run([10, 6, 6, 10, 10], [Action.HIT])
    assert not r.dealer_22_push
    assert r.profit == pytest.approx(-1.0)


def test_player_bust_loses_even_when_dealer_draws_22():
    # Two hands: h1 busts (loses 1), h2 stands; dealer draws to 22 -> h2 pushes.
    # 8,8 vs 6 (hole T=16): h1 8,T hit T -> 28 bust; h2 8,T=18 stand; dealer +6 -> 22.
    r = run(
        [8, 6, 8, 10, 10, 10, 10, 6],
        [Action.SPLIT, Action.HIT, Action.STAND],
    )
    h1, h2 = r.hands
    assert h1.outcome == "lose" and h1.profit == pytest.approx(-1.0)
    assert h2.outcome == "push" and h2.profit == 0.0
    assert r.dealer_22_push
    assert r.profit == pytest.approx(-1.0)


def test_player_blackjack_paid_before_dealer_can_make_22():
    # Player A,T natural vs dealer 6 up: paid 3:2 immediately; dealer never draws.
    r = run([1, 6, 10, 9], [])
    assert r.hands[0].outcome == "blackjack"
    assert r.profit == pytest.approx(1.5)
    assert not r.dealer_played_out


# --- dealer blackjack interactions ----------------------------------------

def test_dealer_blackjack_takes_only_original_bet():
    # Dealer A,T blackjack found on peek; player 8,8 never gets to free-split.
    r = run([8, 1, 8, 10], [])
    assert len(r.hands) == 1
    assert r.profit == pytest.approx(-1.0)
    assert r.free_splits == 0


# --- eligibility unit checks ----------------------------------------------

def test_free_split_eligibility_matrix():
    from ridefree.engine import _Hand

    for rank in range(1, 10):
        assert free_split_allowed(_Hand(cards=[rank, rank], wager=1.0), RIDE_FREE)
    assert not free_split_allowed(_Hand(cards=[10, 10], wager=1.0), RIDE_FREE)
    # resplits stay free while free_resplits is on
    resplit_hand = _Hand(cards=[8, 8], wager=0.0, free_wager=1.0, is_split=True)
    assert free_split_allowed(resplit_hand, RIDE_FREE)
    no_free_resplit = Rules(
        dealer_22_pushes=True,
        free_split_ranks=frozenset(range(1, 10)),
        free_resplits=False,
    )
    assert not free_split_allowed(resplit_hand, no_free_resplit)


def test_free_double_after_split_toggle():
    from ridefree.engine import _Hand

    split_11 = _Hand(cards=[8, 3], wager=0.0, free_wager=1.0, is_split=True)
    assert free_double_allowed(split_11, RIDE_FREE)
    blocked = Rules(
        dealer_22_pushes=True,
        free_double_totals=frozenset({9, 10, 11}),
        free_double_after_split=False,
    )
    assert not free_double_allowed(split_11, blocked)


# --- provisional strategy takes the free money ----------------------------

def test_free_bet_strategy_takes_free_actions():
    # 8,8 vs 6 under FreeBetStrategy: free split (not the basic-strategy path only),
    # and a free double on a drawn 11.
    cards = [8, 6, 8, 10, 3, 10, 10, 9]
    r = play_round(RIDE_FREE, StackedShoe(cards), FreeBetStrategy(), bet=1.0)
    assert r.free_splits >= 1
    assert r.free_doubles >= 1


def test_free_bet_strategy_never_free_splits_fives():
    # 5,5=hard 10 vs 6: free double, never split.
    r = play_round(
        RIDE_FREE, StackedShoe([5, 6, 5, 10, 10, 9, 9]), FreeBetStrategy(), bet=1.0
    )
    assert len(r.hands) == 1
    assert r.free_splits == 0
    assert r.free_doubles == 1
