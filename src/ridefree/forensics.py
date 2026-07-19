"""Shuffle forensics — the measurement layer for Track A (M12a).

Two kinds of instrument, matching the paradigm-2 doctrine (synthetic ground
truth first):

**Exact arithmetic** (fractions, no sampling error), from the published
closed forms:

- Shelf shuffler [DFH = Diaconis/Fulman/Holmes 2013, arXiv:1107.2961]:
  Theorem 3.1 — the chance of a permutation after an m-shelf pass depends
  only on its number of valleys; `shelf_class_prob` is that chance,
  `valley_class_counts` the Warren–Seneta count of permutations per valley
  class, `shelf_distances` the exact total-variation / separation / l-inf
  distances (DFH Table 1).
- GSR riffle [BD = Bayer/Diaconis 1992]: the chance after an a-shuffle
  depends only on the number of rising sequences; `riffle_class_prob`,
  `eulerian_counts`, `riffle_distances` (the "seven shuffles" table).

**Monte Carlo instruments** (deterministic under seed) scoring an actual
`Shuffle` model, for the DFH Section 5 practical tests:

- `guessing_experiment` — card guessing with feedback. `ShelfGuesser` is
  DFH's conjectured-optimal strategy verbatim: guess the nearest unseen
  card beyond the last card shown, upward until a descent is observed,
  downward until an ascent, starting upward from the top of the original
  order. Under a uniform shuffle ANY strategy scores H_n on average
  (`uniform_guessing_mean`); the gap above H_n is the recoverable
  structure, and this is the guessing-advantage instrument M12b's
  input-aware observers plug into (any object with guess()/observe()).
- `color_change_experiment` — DFH's second test: reds on top, blacks on
  the bottom, count color changes through the shuffled deck.
- `valley_histogram` / `rising_sequence_histogram` — empirical class
  occupancies to set against the exact class laws above (the load-bearing
  link between the physical simulation and the closed forms).

Cards in all instruments are the input-stack positions 1..n (1 = original
top of the deck), so "guess card 1" means "guess the card that started on
top".
"""

import math
import random
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache

from ridefree.shuffle import Shuffle

# ---------------------------------------------------------------------------
# Permutation statistics


def valleys(perm) -> int:
    """Number of positions i (interior) with perm[i-1] > perm[i] < perm[i+1]."""
    return sum(
        1
        for i in range(1, len(perm) - 1)
        if perm[i - 1] > perm[i] < perm[i + 1]
    )


def rising_sequences(perm) -> int:
    """Number of maximal rising sequences (consecutive values in increasing
    positions). Equals descents of the inverse permutation plus one."""
    position = {card: i for i, card in enumerate(perm)}
    cards = sorted(position)
    return 1 + sum(
        1 for a, b in zip(cards, cards[1:]) if position[b] < position[a]
    )


def color_changes(colors) -> int:
    """Number of adjacent unequal pairs in a sequence of colors."""
    return sum(1 for a, b in zip(colors, colors[1:]) if a != b)


# ---------------------------------------------------------------------------
# Exact class laws


@lru_cache(maxsize=None)
def valley_class_counts(n: int) -> tuple[int, ...]:
    """v(n, k): permutations of n with k valleys, k = 0..(n-1)//2.

    Warren & Seneta (1996) recurrence, as quoted in DFH Section 3.2:
    v(1, 0) = 1, v(n, k) = (2k + 2) v(n-1, k) + (n - 2k) v(n-1, k-1).
    """
    counts = [1]
    for size in range(2, n + 1):
        prev = counts
        counts = []
        for k in range((size - 1) // 2 + 1):
            total = (2 * k + 2) * (prev[k] if k < len(prev) else 0)
            if k >= 1:
                total += (size - 2 * k) * prev[k - 1]
            counts.append(total)
    return tuple(counts)


@lru_cache(maxsize=None)
def eulerian_counts(n: int) -> tuple[int, ...]:
    """A(n, d): permutations of n with d descents, d = 0..n-1."""
    counts = [1]
    for size in range(2, n + 1):
        prev = counts
        counts = []
        for d in range(size):
            total = (d + 1) * (prev[d] if d < len(prev) else 0)
            if 1 <= d <= len(prev):
                total += (size - d) * prev[d - 1]
            counts.append(total)
    return tuple(counts)


def _comb0(n: int, k: int) -> int:
    """C(n, k) with the combinatorial convention: 0 outside 0 <= k <= n."""
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def shelf_class_prob(n: int, m: int, v: int) -> Fraction:
    """DFH Theorem 3.1: the exact chance an m-shelf pass of n cards produces
    ONE GIVEN permutation with v valleys (all such are equally likely):

        4^(v+1) / (2 (2m)^n) * sum_a C(n+m-a-1, n) C(n-1-2v, a-v),

    the sum over a = 0..n-1 (the paper's remark extends it past m-1; terms
    with a > m-1 vanish through the first binomial)."""
    total = sum(
        math.comb(n + m - a - 1, n) * _comb0(n - 1 - 2 * v, a - v)
        for a in range(n)
    )
    return Fraction(4 ** (v + 1) * total, 2 * (2 * m) ** n)


def riffle_class_prob(n: int, a: int, r: int) -> Fraction:
    """BD: the exact chance an a-shuffle of n cards produces ONE GIVEN
    permutation with r rising sequences: C(a + n - r, n) / a^n."""
    return Fraction(_comb0(a + n - r, n), a**n)


@dataclass(frozen=True)
class Distances:
    """Distances to uniformity, computed exactly then floated."""

    tv: float
    sep: float
    linf: float


def _distances(class_counts, class_prob) -> Distances:
    n_total = sum(class_counts)
    u = Fraction(1, n_total)
    tv = Fraction(0)
    sep = Fraction(0)
    linf = Fraction(0)
    for count, p in zip(class_counts, class_prob):
        tv += count * abs(p - u)
        sep = max(sep, 1 - p / u)
        linf = max(linf, abs(1 - p / u))
    return Distances(tv=float(tv / 2), sep=float(sep), linf=float(linf))


def shelf_distances(n: int, m: int) -> Distances:
    """Exact distances to uniformity after one m-shelf pass (DFH Table 1)."""
    counts = valley_class_counts(n)
    probs = [shelf_class_prob(n, m, v) for v in range(len(counts))]
    return _distances(counts, probs)


def riffle_distances(n: int, a: int) -> Distances:
    """Exact distances to uniformity after one a-shuffle (BD; a = 2^k is k
    riffles — the "seven shuffles" table)."""
    counts = eulerian_counts(n)
    probs = [riffle_class_prob(n, a, d + 1) for d in range(len(counts))]
    return _distances(counts, probs)


def shelf_valley_law(n: int, m: int) -> tuple[Fraction, ...]:
    """P(valley count = v) after one m-shelf pass, exact, v = 0..(n-1)//2."""
    counts = valley_class_counts(n)
    return tuple(
        counts[v] * shelf_class_prob(n, m, v) for v in range(len(counts))
    )


def riffle_rising_law(n: int, a: int) -> tuple[Fraction, ...]:
    """P(rising sequences = r) after one a-shuffle, exact, r = 1..n."""
    counts = eulerian_counts(n)
    return tuple(
        counts[d] * riffle_class_prob(n, a, d + 1) for d in range(len(counts))
    )


# ---------------------------------------------------------------------------
# Guessing with feedback (DFH Section 5.1)


def uniform_guessing_mean(n: int) -> float:
    """E[correct guesses] for ANY feedback strategy on a uniform deck: H_n."""
    return sum(1 / k for k in range(1, n + 1))


def uniform_guessing_var(n: int) -> float:
    """var[correct guesses] on a uniform deck: sum (1/k)(1 - 1/k)."""
    return sum((1 / k) * (1 - 1 / k) for k in range(1, n + 1))


class ShelfGuesser:
    """DFH's conjectured-optimal feedback strategy (Section 5.1), verbatim.

    Guess the nearest unseen card beyond the last shown card in the current
    direction; the direction starts upward ("to begin, guess card 1") and
    flips on each observed descent/ascent. When no unseen card remains in
    the current direction, the run must turn, so guess the nearest unseen
    card on the other side (for the shelf machine's unimodal piles that is
    the extreme remaining card, which is where the reversed run resumes).
    """

    def __init__(self, n: int) -> None:
        self._available = list(range(1, n + 1))  # kept sorted
        self._prev = 0  # sentinel below every card: first guess is card 1
        self._up = True

    def guess(self) -> int:
        avail = self._available
        i = self._bisect_gt(self._prev)
        if self._up:
            return avail[i] if i < len(avail) else avail[-1]
        return avail[i - 1] if i > 0 else avail[0]

    def observe(self, card: int) -> None:
        avail = self._available
        i = self._bisect_gt(card) - 1
        if 0 <= i < len(avail) and avail[i] == card:
            avail.pop(i)
        if self._prev:  # direction only updates from the second card on
            self._up = card > self._prev
        self._prev = card

    def _bisect_gt(self, value: int) -> int:
        """Index of the first available card strictly greater than value."""
        avail = self._available
        lo, hi = 0, len(avail)
        while lo < hi:
            mid = (lo + hi) // 2
            if avail[mid] <= value:
                lo = mid + 1
            else:
                hi = mid
        return lo


@dataclass(frozen=True)
class SampleStats:
    """Mean/variance of a per-trial statistic over `trials` runs."""

    trials: int
    mean: float
    var: float

    @property
    def sd(self) -> float:
        return math.sqrt(self.var)

    @property
    def se_mean(self) -> float:
        return math.sqrt(self.var / self.trials)


def _run_stat(model: Shuffle, n: int, trials: int, seed: int, stat) -> SampleStats:
    rng = random.Random(seed)
    stack = list(range(1, n + 1))
    total = 0.0
    total_sq = 0.0
    for _ in range(trials):
        x = stat(model.permute(stack, rng))
        total += x
        total_sq += x * x
    mean = total / trials
    var = (total_sq - trials * mean * mean) / (trials - 1)
    return SampleStats(trials=trials, mean=mean, var=var)


def guessing_experiment(
    model: Shuffle,
    n: int,
    trials: int,
    seed: int,
    guesser_factory=ShelfGuesser,
) -> SampleStats:
    """Deal `trials` shuffled decks face-up; score a feedback guesser on each."""

    def correct_guesses(deck) -> int:
        guesser = guesser_factory(n)
        correct = 0
        for card in deck:
            if guesser.guess() == card:
                correct += 1
            guesser.observe(card)
        return correct

    return _run_stat(model, n, trials, seed, correct_guesses)


def color_change_experiment(
    model: Shuffle, n: int, trials: int, seed: int
) -> SampleStats:
    """DFH Section 5.2: start with the n//2 reds on top, blacks below; count
    color changes through the shuffled deck."""
    half = n // 2

    def changes(deck) -> int:
        return color_changes([card <= half for card in deck])

    return _run_stat(model, n, trials, seed, changes)


def valley_histogram(model: Shuffle, n: int, trials: int, seed: int) -> Counter:
    """Empirical valley-count occupancies over `trials` shuffled decks."""
    rng = random.Random(seed)
    stack = list(range(1, n + 1))
    hist: Counter = Counter()
    for _ in range(trials):
        hist[valleys(model.permute(stack, rng))] += 1
    return hist


def rising_sequence_histogram(
    model: Shuffle, n: int, trials: int, seed: int
) -> Counter:
    """Empirical rising-sequence occupancies over `trials` shuffled decks."""
    rng = random.Random(seed)
    stack = list(range(1, n + 1))
    hist: Counter = Counter()
    for _ in range(trials):
        hist[rising_sequences(model.permute(stack, rng))] += 1
    return hist
