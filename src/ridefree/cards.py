"""Cards and the shoe.

Two card representations coexist (DESIGN.md, M8 decision record):

- A **value** is an int 1-10: 1 = ace, 2-9 = pips, 10 = ten/jack/queen/king.
  Blackjack play and payout only ever depend on values, so the engine, hand
  valuation, strategies, and trackers all consume values. One deck holds four
  of each rank 1-9 and sixteen tens.
- A **raw card** is a `(rank, suit)` tuple — rank 1-13 (1 = ace, 11/12/13 =
  J/Q/K), suit 0-3 — needed only by side bets (21+3 flushes/straights) and
  suit-aware trackers. The Shoe shuffles raw cards and collapses to values
  once at shuffle time; `deal()` returns values.
"""

import random
from collections.abc import Iterable, Iterator

ACE = 1
TEN = 10

RANKS = tuple(range(1, 11))

RAW_RANKS = tuple(range(1, 14))
SUITS = (0, 1, 2, 3)

# Count of each rank in a single 52-card deck, indexed by rank.
_PER_DECK = {rank: 16 if rank == TEN else 4 for rank in RANKS}


def value(card: tuple[int, int]) -> int:
    """Blackjack value of a raw (rank, suit) card: min(rank, 10), ace = 1."""
    return min(card[0], 10)


def deck_composition(decks: int) -> dict[int, int]:
    """Rank -> count for a fresh shoe of `decks` decks."""
    return {rank: count * decks for rank, count in _PER_DECK.items()}


def shoe_seeds(base_seed: int) -> Iterator[int]:
    """Deterministic, non-sequential shoe seeds for one run.

    Successive shoes must be independent of each other AND of every other run's
    shoes. The old derivation (base_seed + shuffle_count) made runs with nearby
    base seeds traverse overlapping shoe-seed ranges and replay identical rounds
    (docs/DEEP_DIVE_AUDIT.md, `shoe-seed-overlap`). Drawing 63-bit seeds from a
    base-seeded RNG keeps (rules, seed, strategy) exactly reproducible while
    making cross-run seed collisions vanishingly unlikely.
    """
    rng = random.Random(base_seed)
    while True:
        yield rng.getrandbits(63)


class Shoe:
    """A shuffled multi-deck shoe, deterministic under its seed.

    The full raw-card order is materialized up front from `random.Random(seed)`
    and collapsed to values once, so a (decks, penetration, seed) triple always
    reproduces the identical sequence. `deal()` returns values; the raw twin of
    each dealt card is available via `raw_dealt()`.
    """

    def __init__(self, decks: int, penetration: float, seed: int) -> None:
        if decks < 1:
            raise ValueError("decks must be >= 1")
        if not 0.0 < penetration <= 1.0:
            raise ValueError("penetration must be in (0, 1]")
        self.decks = decks
        self.penetration = penetration
        self.seed = seed
        raw = [(rank, suit) for _ in range(decks) for suit in SUITS for rank in RAW_RANKS]
        random.Random(seed).shuffle(raw)
        self._raw = raw
        self._cards = [min(rank, 10) for rank, _ in raw]
        self._pos = 0
        self._cut = round(len(raw) * penetration)

    def deal(self) -> int:
        if self._pos >= len(self._cards):
            raise IndexError("shoe is empty")
        card = self._cards[self._pos]
        self._pos += 1
        return card

    def snapshot(self) -> int:
        """Current deal position, for paired differential replay."""
        return self._pos

    def restore(self, pos: int) -> None:
        """Rewind (or fast-forward) to a snapshot position. The card order is
        immutable, so replaying from a snapshot deals the identical sequence."""
        self._pos = pos

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
        """Card values dealt so far, in order (for event logs and replay checks)."""
        return tuple(self._cards[: self._pos])

    def raw_dealt(self) -> Iterable[tuple[int, int]]:
        """Raw (rank, suit) cards dealt so far, in order — the raw twin of
        `dealt_cards()`, for side-bet settlement and suit-aware tracking."""
        return tuple(self._raw[: self._pos])

    def raw_slice(self, start: int, stop: int) -> tuple[tuple[int, int], ...]:
        """Raw cards at deal positions [start, stop) — for the engine to read a
        settled deal (e.g. the three 21+3 cards) without copying the whole
        dealt prefix."""
        return tuple(self._raw[start:stop])
