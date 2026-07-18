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

# The RF-L2 human count: level-2 quantization of the Ride Free EORs (E4a). Balanced
# (tags x cards/deck sum to 0), betting correlation 0.966 with the exact RF EORs —
# the same quality hi-lo achieves on standard blackjack (0.963). At level 1 the best
# balanced count for Ride Free is hi-lo itself (BC 0.910): +-1 tags cannot express
# the ace/ten asymmetry (ace ~3x the ten), which is exactly what level 2 buys.
RF_L2_TAGS = {1: -2, 2: 1, 3: 1, 4: 1, 5: 2, 6: 1, 7: 0, 8: 0, 9: 0, 10: -1}

# Effects of removal (fraction of EV per card removed from 52), derived analytically
# via eor.effects_of_removal on 2026-07-17 (docs/EXPERIMENTS.md E4a) and regenerated
# by tests/test_eor.py. Standard H17 matches Griffin's published table in sign/order;
# Ride Free differs sharply: tens half as valuable (dealer 22 is made of tens), aces
# ~3x more important than tens, 3/4/5/7 collapse (they feed free doubles), 8 flips
# negative (8,8 free split). Classical hi-lo is mis-tuned for Ride Free.
STANDARD_H17_EOR = {
    1: -0.0052017, 2: 0.0039827, 3: 0.0048520, 4: 0.0065485, 5: 0.0080104,
    6: 0.0048199, 7: 0.0028417, 8: -0.0001621, 9: -0.0022227, 10: -0.0053536,
}
RIDE_FREE_EOR = {
    1: -0.0064175, 2: 0.0040448, 3: 0.0020117, 4: 0.0032373, 5: 0.0052581,
    6: 0.0039695, 7: 0.0009727, 8: -0.0010960, 9: -0.0013008, 10: -0.0022672,
}

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
        return self.linear_true(HILO_TAGS)

    def linear_true(self, tags: dict[int, int]) -> float:
        """True count for any balanced tag vector: running / decks remaining.
        (Running count of dealt cards = -sum over remaining, since a balanced
        count sums to zero over the full shoe.)"""
        decks_left = self.cards_remaining / 52
        if decks_left <= 0:
            return 0.0
        running = -sum(tags[r] * self.counts[r] for r in RANKS)
        return running / decks_left

    def rf_l2_true(self) -> float:
        """True count of the RF-L2 human count."""
        return self.linear_true(RF_L2_TAGS)

    def eor_shift(self, eors: dict[int, float]) -> float:
        """First-order estimated EV shift vs a fresh shoe under an EOR vector —
        the *perfect linear count* for the game the EORs were derived from,
        expressed directly in EV units (0.005 = +0.5%)."""
        from ridefree.eor import eor_ev_shift

        return eor_ev_shift(eors, self.counts, self.cards_remaining)

    def rf_ev_shift(self) -> float:
        """Ride-Free-optimal linear signal (EV units)."""
        return self.eor_shift(RIDE_FREE_EOR)


class RawCompositionTracker:
    """Per-(rank, suit) counts of the remaining shoe, fed with raw dealt cards.

    The suit-aware twin of CompositionTracker (M8c): value-collapsed counts
    cannot express flush richness or distinguish J/Q/K for straights. Fed from
    `Shoe.raw_slice()` by the experiment harness (all dealt cards, hole
    included, per the same visibility doctrine as CompositionTracker)."""

    def __init__(self, decks: int) -> None:
        self.decks = decks
        self.counts: dict[tuple[int, int], int] = {}
        self.cards_remaining = 0
        self.new_shoe()

    def new_shoe(self) -> None:
        self.counts = {
            (rank, suit): self.decks for rank in range(1, 14) for suit in range(4)
        }
        self.cards_remaining = 52 * self.decks

    def observe(self, cards) -> None:
        for card in cards:
            self.counts[card] -= 1
        self.cards_remaining -= len(cards)
