"""Counting observers and pre-deal signals.

The CompositionTracker maintains perfect-information per-rank counts of the remaining
shoe from observed cards — every card in a round (both dealer cards included) is
exposed at settlement, so a perfect tracker equals the true shoe composition. Both
counting families derive from it:

- Event probabilities, computed exactly from the counts: P(next two cards are a
  free-splittable pair), P(next two cards are a free-double-eligible hard total).
- Linear counts: any balanced tag vector is a dot product with the remaining counts
  (hi-lo running count = -sum(tag[r] * remaining[r]) since the full-shoe sum is 0).

Practical human counts (M6) are approximations of these exact signals; measuring the
exact signals first bounds what any practical count can achieve.
"""

from ridefree.cards import ACE, RANKS, TEN, deck_composition
from ridefree.engine import RoundResult

# Hi-lo tags: 2-6 count +1, 7-9 neutral, ten-values and aces -1.
HILO_TAGS = {r: (1 if 2 <= r <= 6 else (-1 if r in (TEN, ACE) else 0)) for r in RANKS}

# Unordered two-card combos (no aces, no tens) forming each hard total 9/10/11.
FREE_DOUBLE_COMBOS = tuple(
    (a, b)
    for a in range(2, 10)
    for b in range(a, 10)
    if a + b in (9, 10, 11)
)


class CompositionTracker:
    """Perfect-information remaining-shoe composition, fed by observed rounds."""

    def __init__(self, decks: int) -> None:
        self.decks = decks
        self.counts: dict[int, int] = {}
        self.cards_remaining = 0
        self.new_shoe()

    def new_shoe(self) -> None:
        self.counts = deck_composition(self.decks)
        self.cards_remaining = 52 * self.decks

    def observe_card(self, card: int) -> None:
        self.counts[card] -= 1
        self.cards_remaining -= 1

    def observe_round(self, result: RoundResult) -> None:
        for hand in result.hands:
            for card in hand.cards:
                self.observe_card(card)
        for card in result.dealer_cards:
            self.observe_card(card)

    # --- pre-deal signals -------------------------------------------------

    def p_free_split_pair(self, ranks=frozenset(range(1, 10))) -> float:
        """P(next two cards are a matching pair in `ranks`)."""
        n = self.cards_remaining
        if n < 2:
            return 0.0
        num = sum(self.counts[r] * (self.counts[r] - 1) for r in ranks)
        return num / (n * (n - 1))

    def p_free_double_hand(self) -> float:
        """P(next two cards form a hard 9, 10, or 11)."""
        n = self.cards_remaining
        if n < 2:
            return 0.0
        num = 0
        for a, b in FREE_DOUBLE_COMBOS:
            if a == b:
                num += self.counts[a] * (self.counts[a] - 1)
            else:
                num += 2 * self.counts[a] * self.counts[b]
        return num / (n * (n - 1))

    def hilo_running(self) -> int:
        """Hi-lo running count of the cards seen so far."""
        return -sum(HILO_TAGS[r] * self.counts[r] for r in RANKS)

    def hilo_true(self) -> float:
        """Running count per remaining deck (the standard true count)."""
        decks_left = self.cards_remaining / 52
        if decks_left <= 0:
            return 0.0
        return self.hilo_running() / decks_left
