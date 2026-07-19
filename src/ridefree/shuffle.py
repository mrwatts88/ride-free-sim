"""Shuffle models — physical shuffle procedures as data (M12a, paradigm 2).

Paradigm 1 froze the null hypothesis: `Shoe` deals a uniformly random
permutation (one Fisher–Yates pass under the shoe seed). Track A of paradigm
2 asks what happens when the permutation is NOT uniform: a real procedure (a
shelf machine, N riffles, a hand shuffle) applied to a KNOWN input order
leaves structure an observer can exploit. This module gives the procedure the
same treatment `Rules` gives game variants — an immutable configuration, so
`(seed, stack, shuffle)` reproduces the identical permutation, always.

A shuffle model exposes one method:

    permute(stack, rng) -> list

`stack` is the pre-shuffle order (index 0 = top of the deck), `rng` a seeded
`random.Random` supplying ALL randomness. Models never mutate `stack`, and
each pass draws a content-independent number of variates, so any run replays
exactly from its seed.

Models (validated in tests/test_shuffle.py and data/e26_shelf_gate.py against
Diaconis, Fulman & Holmes, "Analysis of casino shelf shuffling machines",
Ann. Appl. Probab. 23(4) 2013, arXiv:1107.2961 [DFH]; and Bayer & Diaconis,
"Trailing the dovetail shuffle to its lair", Ann. Appl. Probab. 2 1992 [BD]):

- `UniformShuffle` — the paradigm-1 null. `Shoe`'s default path is exactly
  this model (asserted byte-identical in tests).
- `ShelfShuffle` — the casino shelf machine to the published spec: cards
  dealt one at a time FROM THE BOTTOM of the input stack, each onto a
  uniformly chosen shelf, placed on top or under that shelf's pile with
  probability 1/2; piles then unloaded in shelf order. (The machine unloads
  in random order; shelf choices are i.i.d. uniform, so unload order is
  distributionally irrelevant — DFH Description 1 fixes it too.) DFH
  Corollary 4.2: an m1-shelf pass followed by an m2-shelf pass is EXACTLY a
  2*m1*m2-shelf pass, so `passes=2, shelves=10` is the manufacturer's
  adopted fix (a 200-shelf machine).
- `RiffleShuffle` — the Gilbert–Shannon–Reeds a-shuffle: cut into `piles`
  packets multinomially, then interleave uniformly at random (drop chance
  proportional to remaining packet size). `piles=2` is one honest riffle;
  [BD] a-then-b composes to one a*b-shuffle, so `piles`/`passes` together
  are the riffle-quality knob (7 riffles = a 128-shuffle).
- `ComposedShuffle` — apply `stages` left to right; arbitrary procedure
  pipelines (riffle–riffle–strip hand shuffles land here in M12b).
"""

import random
from collections import deque
from dataclasses import dataclass


class Shuffle:
    """A deterministic-under-rng permutation procedure. Subclasses implement
    `permute`; they are immutable configurations in the sense of `Rules`."""

    def permute(self, stack: list, rng: random.Random) -> list:
        raise NotImplementedError


@dataclass(frozen=True)
class UniformShuffle(Shuffle):
    """One Fisher–Yates pass — the uniform null the engine has always used."""

    def permute(self, stack: list, rng: random.Random) -> list:
        out = list(stack)
        rng.shuffle(out)
        return out


@dataclass(frozen=True)
class ShelfShuffle(Shuffle):
    """The DFH shelf machine: uniform shelf, top-or-bottom placement at 1/2.

    One rng draw per card: a lane in [0, 2*shelves) — lane >> 1 is the shelf,
    lane & 1 chooses under-the-pile. This is DFH Description 1's "label each
    card uniformly in 1..2m" directly.
    """

    shelves: int = 10
    passes: int = 1

    def __post_init__(self) -> None:
        if self.shelves < 1:
            raise ValueError("shelves must be >= 1")
        if self.passes < 1:
            raise ValueError("passes must be >= 1")

    def permute(self, stack: list, rng: random.Random) -> list:
        out = list(stack)
        for _ in range(self.passes):
            out = self._one_pass(out, rng)
        return out

    def _one_pass(self, stack: list, rng: random.Random) -> list:
        piles: list[deque] = [deque() for _ in range(self.shelves)]
        lanes = 2 * self.shelves
        for card in reversed(stack):  # the machine deals from the bottom of the deck
            lane = rng.randrange(lanes)
            if lane & 1:
                piles[lane >> 1].append(card)  # under the shelf's pile
            else:
                piles[lane >> 1].appendleft(card)  # on top of the shelf's pile
        out: list = []
        for pile in piles:
            out.extend(pile)
        return out


@dataclass(frozen=True)
class RiffleShuffle(Shuffle):
    """The GSR a-shuffle with a = `piles`: multinomial cut, uniform interleave."""

    piles: int = 2
    passes: int = 1

    def __post_init__(self) -> None:
        if self.piles < 2:
            raise ValueError("piles must be >= 2")
        if self.passes < 1:
            raise ValueError("passes must be >= 1")

    def permute(self, stack: list, rng: random.Random) -> list:
        out = list(stack)
        for _ in range(self.passes):
            out = self._one_pass(out, rng)
        return out

    def _one_pass(self, stack: list, rng: random.Random) -> list:
        a = self.piles
        n = len(stack)
        sizes = [0] * a
        for _ in range(n):  # multinomial cut: packet i is the i-th block from the top
            sizes[rng.randrange(a)] += 1
        heads = [0] * a
        start = 0
        for i, size in enumerate(sizes):
            heads[i] = start
            start += size
        left = list(sizes)
        out: list = []
        remaining = n
        while remaining:
            r = rng.randrange(remaining)  # drop chance proportional to packet size
            for i in range(a):
                if r < left[i]:
                    out.append(stack[heads[i]])
                    heads[i] += 1
                    left[i] -= 1
                    remaining -= 1
                    break
                r -= left[i]
        return out


@dataclass(frozen=True)
class ComposedShuffle(Shuffle):
    """Apply `stages` in order (stages[0] first) with the shared rng."""

    stages: tuple[Shuffle, ...]

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("stages must be non-empty")

    def permute(self, stack: list, rng: random.Random) -> list:
        out = list(stack)
        for stage in self.stages:
            out = stage.permute(out, rng)
        return out
