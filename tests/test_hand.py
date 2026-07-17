import pytest

from ridefree.hand import hand_total, is_blackjack, is_bust, is_soft

# (cards, total, soft) — 1 = ace, 10 = any ten-value
CASES = [
    ([10, 7], 17, False),
    ([2, 3], 5, False),
    ([1, 10], 21, True),
    ([1, 6], 17, True),
    ([1, 6, 10], 17, False),  # soft 17 hardens after a ten
    ([1, 1], 12, True),  # only one ace counts as 11
    ([1, 1, 9], 21, True),
    ([1, 1, 1], 13, True),
    ([1, 1, 10], 12, False),  # neither ace can be 11 without busting
    ([1, 9, 1], 21, True),
    ([1, 10, 10], 21, False),
    ([10, 10, 2], 22, False),
    ([1, 1, 10, 10], 22, False),  # busts even with both aces as 1
    ([5, 5, 1], 21, True),
    ([9, 1], 20, True),
    ([10, 6, 6], 22, False),
]


@pytest.mark.parametrize("cards,total,soft", CASES)
def test_totals(cards, total, soft):
    assert hand_total(cards) == total
    assert is_soft(cards) == soft
    assert is_bust(cards) == (total > 21)


def test_order_irrelevant():
    assert hand_total([1, 6]) == hand_total([6, 1])
    assert is_soft([10, 1, 5]) == is_soft([5, 1, 10])


@pytest.mark.parametrize(
    "cards,expected",
    [
        ([1, 10], True),
        ([10, 1], True),
        ([1, 9], False),  # 20, not blackjack
        ([10, 10], False),
        ([1, 5, 5], False),  # 21 in three cards is not a natural
        ([10, 5, 6], False),
        ([1], False),
    ],
)
def test_blackjack(cards, expected):
    assert is_blackjack(cards) == expected
