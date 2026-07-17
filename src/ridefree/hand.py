"""Hand valuation: pure functions over card sequences.

No game flow here — just totals. A hand's total is the highest value <= 21 counting
at most one ace as 11 (counting two aces as 11 always busts), or the minimum total
if every valuation busts.
"""

from collections.abc import Sequence

from ridefree.cards import ACE, TEN


def hand_total(cards: Sequence[int]) -> int:
    """Best total: aces count 11 when that doesn't bust."""
    total = sum(cards)
    if ACE in cards and total + 10 <= 21:
        return total + 10
    return total


def is_soft(cards: Sequence[int]) -> bool:
    """True when an ace is currently counted as 11."""
    return ACE in cards and sum(cards) + 10 <= 21


def is_bust(cards: Sequence[int]) -> bool:
    return hand_total(cards) > 21


def is_blackjack(cards: Sequence[int]) -> bool:
    """A natural: exactly two cards, ace + ten-value. (A split hand that draws to 21
    is not a blackjack; the engine enforces that by never calling this on split
    hands.)"""
    return len(cards) == 2 and sorted(cards) == [ACE, TEN]
