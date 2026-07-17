"""Hand-level known-outcome tests — the M1 gate.

Each test stacks an exact card sequence and asserts the precise settlement. Deal
order in the engine is fixed: player1, dealer-up, player2, dealer-hole, then draws
in play order. `A` = 1, tens = 10.
"""

import dataclasses

import pytest

from ridefree.engine import Action, IllegalActionError, play_round
from ridefree.rules import Rules
from ridefree.strategy import ScriptedStrategy

STANDARD = Rules()  # STANDARD_6D_H17 equivalent


class StackedShoe:
    """Deals a predetermined sequence; for constructing exact scenarios."""

    def __init__(self, cards):
        self._cards = list(cards)
        self._pos = 0

    def deal(self):
        card = self._cards[self._pos]
        self._pos += 1
        return card

    @property
    def needs_shuffle(self):
        return False

    @property
    def cards_remaining(self):
        return len(self._cards) - self._pos


def run(cards, actions, rules=STANDARD, bet=1.0):
    return play_round(rules, StackedShoe(cards), ScriptedStrategy(actions), bet=bet)


# --- naturals -------------------------------------------------------------

def test_player_blackjack_pays_3to2():
    r = run([1, 9, 10, 6], [])  # player A,T=BJ; dealer up 9, hole 6
    assert r.hands[0].outcome == "blackjack"
    assert r.profit == pytest.approx(1.5)


def test_both_blackjack_pushes():
    r = run([1, 10, 10, 1], [])  # player A,T; dealer T,A
    assert r.hands[0].outcome == "push"
    assert r.profit == 0.0


def test_dealer_blackjack_beats_nonblackjack():
    r = run([10, 1, 9, 10], [])  # player T,9=19; dealer A,T=BJ
    assert r.hands[0].outcome == "lose"
    assert r.profit == pytest.approx(-1.0)


def test_six_five_blackjack_payout_config():
    r = run([1, 9, 10, 6], [], rules=Rules(blackjack_payout=1.2))
    assert r.profit == pytest.approx(1.2)


# --- basic settlements ----------------------------------------------------

def test_player_bust_loses_even_when_dealer_busts():
    # player T,6 hits T -> 26 bust; dealer T,6 draws T -> 26 bust
    r = run([10, 10, 6, 6, 10, 10], [Action.HIT])
    assert r.hands[0].outcome == "lose"
    assert r.profit == pytest.approx(-1.0)


def test_higher_total_wins():
    # player T,9=19 stand; dealer 7,9=16 draws 2 -> 18
    r = run([10, 7, 9, 9, 2], [Action.STAND])
    assert r.hands[0].outcome == "win"
    assert r.profit == pytest.approx(1.0)


def test_push_on_equal_total():
    r = run([10, 10, 9, 9], [Action.STAND])  # both 19
    assert r.hands[0].outcome == "push"
    assert r.profit == 0.0


# --- doubling -------------------------------------------------------------

def test_double_doubles_wager_and_draws_one():
    # player 5,6=11 double -> T = 21; dealer 9,8=17
    r = run([5, 9, 6, 8, 10], [Action.DOUBLE])
    assert r.hands[0].wager == pytest.approx(2.0)
    assert r.hands[0].outcome == "win"
    assert r.profit == pytest.approx(2.0)


def test_double_loss_costs_two_units():
    # player 5,6=11 double -> 4 = 15; dealer 9,8=17
    r = run([5, 9, 6, 8, 4], [Action.DOUBLE])
    assert r.hands[0].outcome == "lose"
    assert r.profit == pytest.approx(-2.0)


# --- splitting ------------------------------------------------------------

def test_split_creates_two_independent_hands():
    # player 8,8 split; hand1 8,3 stand, hand2 8,5 stand; dealer 6,T draws 9 -> bust
    r = run([8, 6, 8, 10, 3, 5, 9], [Action.SPLIT, Action.STAND, Action.STAND])
    assert len(r.hands) == 2
    assert all(h.outcome == "win" for h in r.hands)
    assert r.profit == pytest.approx(2.0)


def test_split_aces_get_one_card_each():
    # player A,A split; each ace gets exactly one card; dealer 6,T draws 9 -> bust
    r = run([1, 6, 1, 10, 9, 10, 9], [Action.SPLIT])
    assert len(r.hands) == 2
    assert [len(h.cards) for h in r.hands] == [2, 2]
    # A,T after a split is 21 but NOT a natural blackjack
    assert all(h.outcome == "win" for h in r.hands)
    assert not any(h.outcome == "blackjack" for h in r.hands)
    assert r.profit == pytest.approx(2.0)


def test_resplit_aces_blocked_by_default():
    # player A,A split -> hand1 gets another A; resplit must be illegal (one card only)
    r = run([1, 6, 1, 10, 1, 10, 9], [Action.SPLIT])
    # engine never offers a decision on split aces, so no IllegalAction; each keeps 2
    assert [len(h.cards) for h in r.hands] == [2, 2]


# --- dealer drawing rules -------------------------------------------------

def test_h17_dealer_hits_soft_17():
    # dealer A,6=soft17 must hit under H17: draws 4 -> 21, beats player 19
    r = run([10, 1, 9, 6, 4], [Action.STAND], rules=Rules(dealer_hits_soft_17=True))
    assert r.hands[0].outcome == "lose"


def test_s17_dealer_stands_soft_17():
    # same cards, S17: dealer stands on soft 17, player 19 wins
    r = run([10, 1, 9, 6, 4], [Action.STAND], rules=Rules(dealer_hits_soft_17=False))
    assert r.hands[0].outcome == "win"


# --- dealer 22 (the Free Bet mechanic, standalone) ------------------------

def test_standard_dealer_22_is_a_bust_win():
    # dealer T,5 draws 7 -> 22; standard rules: bust, player 19 wins
    r = run([10, 10, 9, 5, 7], [Action.STAND], rules=Rules(dealer_22_pushes=False))
    assert r.hands[0].outcome == "win"


def test_dealer_22_pushes_when_configured():
    r = run([10, 10, 9, 5, 7], [Action.STAND], rules=Rules(dealer_22_pushes=True))
    assert r.hands[0].outcome == "push"
    assert r.profit == 0.0


# --- guards ---------------------------------------------------------------

def test_illegal_action_raises():
    # player 5,6=11; splitting is not legal (not a pair)
    with pytest.raises(IllegalActionError):
        run([5, 9, 6, 8, 10], [Action.SPLIT])


def test_surrender_still_unsupported():
    with pytest.raises(NotImplementedError):
        run([10, 7, 9, 9], [Action.STAND], rules=Rules(late_surrender=True))


def test_free_bet_rules_now_play():
    # Free rules no longer raise (M3); a plain stand-off settles normally.
    r = run([10, 7, 9, 9, 2], [Action.STAND], rules=Rules(free_resplits=True))
    assert r.hands[0].outcome == "win"
