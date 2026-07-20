"""Optimal complete-feedback card-guessing value E(n, m) for the DFH m-shelf
shuffle — the shared core behind experiment **E35** (docs/EXPERIMENTS.md, the
`data/gt_*.py` probes, docs/GUESSING_THEOREM.md).

E(n, m) is the expected number of correct guesses under the Bayes-OPTIMAL
complete-feedback strategy after ONE m-shelf pass of a deck of n distinct cards
(guess the next card, see it, repeat). Greedy argmax-with-feedback is globally
optimal because the player's guesses never affect the reveals, so

    E_opt(n, m) = Σ over prefixes q of  max_child  joint-mass[q + (c,)],

with the exact rational output law from DFH Theorem 3.1 (`shelf_class_prob`: the
probability of an output permutation depends only on its valley count). DFH's
m-INDEPENDENT strategy G (`forensics.ShelfGuesser`) is conjectured optimal for
all m (Clay 2025, arXiv:2507.10294, Conjecture 3 — the m ≥ 2 case is open); this
module also returns G's exact expected value E_G so the optimality gap can be
checked as an exact Fraction.

This module is pure shuffle-math: it imports the forensics/posterior/shuffle
layers only, never a game engine (the two-layer rule). See
docs/GUESSING_THEOREM.md for the full write-up and positioning.
"""

from __future__ import annotations

import random
from fractions import Fraction
from itertools import permutations

from ridefree.forensics import (
    ShelfGuesser,
    shelf_class_prob,
    valley_class_counts,
    valleys,
)
from ridefree.posterior import ShelfPosterior
from ridefree.shuffle import ShelfShuffle


def total_prob(n: int, m: int) -> Fraction:
    """Total output probability summed over all n! decks — a normalization gate.

    Sums `shelf_class_prob` over valley classes weighted by class size; must
    equal exactly 1 for a well-formed output law.
    """
    counts = valley_class_counts(n)
    return sum(counts[v] * shelf_class_prob(n, m, v) for v in range(len(counts)))


def _dfh_score(perm) -> int:
    """Realized correct guesses of DFH's strategy G on one fully-revealed deck."""
    g = ShelfGuesser(len(perm))
    correct = 0
    for card in perm:
        if g.guess() == card:
            correct += 1
        g.observe(card)
    return correct


def build_perms(n: int) -> list[tuple[tuple[int, ...], int]]:
    """All n! decks paired with their valley counts (reuse across m columns)."""
    return [(perm, valleys(perm)) for perm in permutations(range(1, n + 1))]


def exact_e_from_perms(n: int, m: int, perms) -> tuple[Fraction, Fraction]:
    """Exact (E_opt, E_G) as rationals, given precomputed ``perms``.

    ``perms`` is a list of ``(perm_tuple, valley_count)`` (see ``build_perms``);
    passing it lets a caller enumerate the n! decks once and sweep m cheaply.

    E_opt: greedy-optimal feedback guessing via the prefix-trie max-child mass.
    E_G:   DFH's strategy G, exact expectation Σ_perm P(perm)·score_G(perm).
    Cost is O(n · n!) — practical to n ≈ 9.
    """
    zero = Fraction(0)
    pcache: dict[int, Fraction] = {}

    def pperm(v: int) -> Fraction:
        p = pcache.get(v)
        if p is None:
            p = shelf_class_prob(n, m, v)
            pcache[v] = p
        return p

    mass: dict[tuple, Fraction] = {}
    e_g = zero
    for perm, v in perms:
        p = pperm(v)
        e_g += p * _dfh_score(perm)
        for t in range(1, n + 1):
            key = perm[:t]
            mass[key] = mass.get(key, zero) + p

    # E_opt = Σ over parent prefixes of the maximum child mass.
    best: dict[tuple, Fraction] = {}
    for key, mval in mass.items():
        parent = key[:-1]
        cur = best.get(parent)
        if cur is None or mval > cur:
            best[parent] = mval
    return sum(best.values(), zero), e_g


def exact_e(n: int, m: int) -> tuple[Fraction, Fraction]:
    """Exact (E_opt, E_G) as rationals for one (n, m) — enumerates the n! decks."""
    return exact_e_from_perms(n, m, build_perms(n))


def mc_e(n: int, m: int, trials: int, seed: int):
    """Monte-Carlo E(n, m) via the low-variance ``predicted`` estimator.

    Returns ``(pred_mean, pred_se, hit_mean, hit_se)``. Along each dealt deck,
    ``predicted`` accumulates the maximum posterior probability at every step
    (`ShelfPosterior.next_probs`); its mean is UNBIASED for E_opt(n, m) and has
    far lower variance than the realized argmax hit count (also returned, as a
    calibration cross-check). Independent of ``exact_e`` — this is the gate that
    the enumeration and the sequential posterior agree.
    """
    rng = random.Random(seed)
    stack = list(range(1, n + 1))
    shuf = ShelfShuffle(shelves=m, passes=1)
    sp = sp2 = sh = sh2 = 0.0
    for _ in range(trials):
        deck = shuf.permute(stack, rng)
        post = ShelfPosterior(m, stack)
        pred = 0.0
        hit = 0
        for card in deck:
            probs = post.next_probs()
            best = max(probs, key=probs.get)
            pred += probs[best]
            if best == card:
                hit += 1
            post.observe(card)
        sp += pred
        sp2 += pred * pred
        sh += hit
        sh2 += hit * hit
    mp = sp / trials
    vp = (sp2 - trials * mp * mp) / (trials - 1)
    mh = sh / trials
    vh = (sh2 - trials * mh * mh) / (trials - 1)
    return mp, (vp / trials) ** 0.5, mh, (vh / trials) ** 0.5
