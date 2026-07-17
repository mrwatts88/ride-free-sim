"""Cards and the shoe.

A card is an int rank value: 1 = ace, 2-9 = pips, 10 = ten/jack/queen/king.
Suits and face distinctions never affect blackjack play or payout, so they are not
modeled. One deck therefore holds four of each rank 1-9 and sixteen tens.
"""

import random
from collections.abc import Iterable

ACE = 1
TEN = 10

RANKS = tuple(range(1, 11))

# Count of each rank in a single 52-card deck, indexed by rank.
_PER_DECK = {rank: 16 if rank == TEN else 4 for rank in RANKS}


def deck_composition(decks: int) -> dict[int, int]:
    """Rank -> count for a fresh shoe of `decks` decks."""
    return {rank: count * decks for rank, count in _PER_DECK.items()}


class Shoe:
    """A shuffled multi-deck shoe, deterministic under its seed.

    The full card order is materialized up front from `random.Random(seed)`, so a
    (decks, penetration, seed) triple always reproduces the identical sequence.
    """

    def __init__(self, decks: int, penetration: float, seed: int) -> None:
        if decks < 1:
            raise ValueError("decks must be >= 1")
        if not 0.0 < penetration <= 1.0:
            raise ValueError("penetration must be in (0, 1]")
        self.decks = decks
        self.penetration = penetration
        self.seed = seed
        cards = [rank for rank in RANKS for _ in range(_PER_DECK[rank] * decks)]
        random.Random(seed).shuffle(cards)
        self._cards = cards
        self._pos = 0
        self._cut = round(len(cards) * penetration)

    def deal(self) -> int:
        if self._pos >= len(self._cards):
            raise IndexError("shoe is empty")
        card = self._cards[self._pos]
        self._pos += 1
        return card

    @property
    def cards_dealt(self) -> int:
        return self._pos

    @property
    def cards_remaining(self) -> int:
        return len(self._cards) - self._pos

    @property
    def needs_shuffle(self) -> bool:
        """True once the cut card has been reached; finish the round, then reshoe."""
        return self._pos >= self._cut

    def remaining_composition(self) -> dict[int, int]:
        """Rank -> count of undealt cards (for counting-system work later)."""
        counts = dict.fromkeys(RANKS, 0)
        for card in self._cards[self._pos:]:
            counts[card] += 1
        return counts

    def dealt_cards(self) -> Iterable[int]:
        """Cards dealt so far, in order (for event logs and replay checks)."""
        return tuple(self._cards[: self._pos])
