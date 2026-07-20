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
from collections import defaultdict
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


def run_lengths(prefix) -> tuple[int, ...]:
    """Ascending-run-length composition of a revealed prefix — the descent
    structure. Each descent (prefix[i] > prefix[i+1]) ends a run; under the
    shelf shuffle a descent can only occur across a shelf-lane boundary, so
    the run composition records how the prefix has partitioned the machine's
    lanes. E.g. (1, 2, 5, 3, 4) → (3, 2). Empty prefix → ()."""
    if not prefix:
        return ()
    runs, cur = [], 1
    for a, b in zip(prefix, prefix[1:]):
        if b > a:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    return tuple(runs)


def walk_prefixes(n: int, m: int):
    """Yield ``(prefix, hit, pprob)`` for EVERY reachable dealt prefix of an
    m-shelf pass of the stack 1..n (E36, the n!-wall sufficiency probe).

    ``hit`` is the Bayes-optimal per-step guess success max_c P(next=c|prefix)
    (= DFH strategy G's hit probability, since the gap is 0), and ``pprob`` is
    P(this prefix is dealt). Summing ``pprob * hit`` over the yielded prefixes
    reconstructs E_opt(n, m) exactly (a gate). Cost O(n!) — this is the exact
    enumeration whose aggregation over prefixes is the open problem; the probe
    tests which statistics of ``prefix`` the hit is a function of.

    Implemented as an exact DFS carrying a `ShelfPosterior` (the general-m
    output law in poly time per prefix), branching by `copy()` + `observe()`.
    """

    def rec(post, prefix, pprob):
        probs = post.next_probs()
        yield prefix, max(probs.values()), pprob
        if len(prefix) == n - 1:
            return  # one card left (hit = 1); children are complete decks
        for c, pc in probs.items():
            if pc > 0.0:
                child = post.copy()
                child.observe(c)
                yield from rec(child, prefix + (c,), pprob * pc)

    yield from rec(ShelfPosterior(m, list(range(1, n + 1))), (), 1.0)


def exact_e_dp(n: int, m: int) -> tuple[float, int]:
    """Exact optimal-guessing value E_opt(n, m) via the run-composition DP —
    Clay's m-shelf transition operator made explicit and runnable (E37).

    Breaks the O(n·n!) wall of `exact_e`/`walk_prefixes`. Because DFH's strategy
    G is optimal (E35, gap 0), E_opt(n,m) = Σ over dealt prefixes q of
    P(q)·h(q) with h(q) = max_c P(next=c|q); and E36 verified that the whole
    next-card posterior (hence h) is an EXACT function of the Markov statistic

        σ = (direction, rank-of-last-among-remaining, ascending-run composition)

    and that σ's transition is CLOSED (a revealed card either extends the last
    ascending run or, on a descent, opens a new one). So the sum collapses onto
    states:  E_opt(n, m) = Σ_σ P(σ)·h(σ).  Computed by (1) a memoized DFS that
    builds the state graph once — each state's posterior read from ONE
    representative `ShelfPosterior`, deduped by σ (a state reached by many
    prefixes is explored once) — and (2) a forward mass pass in prefix-length
    order.

    Cost is set by the number of REACHABLE run-compositions, not n!. The DFH law
    gives an m-shelf output AT MOST m−1 valleys (`shelf_class_prob` vanishes for
    v>m−1), so that count is POLYNOMIAL in n for each fixed m — degree growing
    with m — and exponential only in m. That is why this reaches deck scale for
    small m (exact E_opt(52, m) where E35 could only Monte-Carlo) while Clay's
    general-m matrix stays hard. Returns ``(E_opt, number of DP states)``.

    Float arithmetic (the posterior is float): gated to reproduce the exact
    rational `exact_e` for n≤9 to ~1e-9 and the `mc_e` deck-scale values to se.
    The transition operator built here IS Clay's open m-shelf matrix in explicit
    exponential form — the object a proof of Conjecture 3 would work on.
    """
    root = (True, 0, ())  # (direction, rank-of-last, run composition)
    memo: dict[tuple, tuple[float, list]] = {}  # state -> (hit, [(prob, child)])

    def explore(post, state) -> None:
        probs = post.next_probs()
        remaining = sorted(probs)
        vec = [probs[c] for c in remaining]
        hit = max(vec)
        _dir, rank, runcomp = state
        edges: list = []
        if len(remaining) > 1:  # else a leaf: one card left, hit == 1, no branch
            for j, card in enumerate(remaining):
                pc = vec[j]
                if pc <= 0.0:
                    continue
                ascending = j >= rank  # card > last iff its rank ≥ last's rank
                if not runcomp:
                    child_runcomp = (1,)
                elif ascending:
                    child_runcomp = runcomp[:-1] + (runcomp[-1] + 1,)
                else:
                    child_runcomp = runcomp + (1,)
                # new rank-of-last == j: exactly the j remaining cards below the
                # revealed one stay below it after it leaves the remaining set.
                child = (ascending, j, child_runcomp)
                edges.append((pc, child))
                if child not in memo:  # dedup: explore each state's subtree once
                    twin = post.copy()
                    twin.observe(card)
                    explore(twin, child)
        memo[state] = (hit, edges)

    explore(ShelfPosterior(m, list(range(1, n + 1))), root)

    # Forward mass pass over states ordered by prefix length t = sum(runcomp):
    # every edge advances t by exactly 1, so a single sweep is topological.
    by_t: dict[int, list] = defaultdict(list)
    for state in memo:
        by_t[sum(state[2])].append(state)
    mass: dict[tuple, float] = defaultdict(float)
    mass[root] = 1.0
    e_opt = 0.0
    for t in range(n):  # levels 0 .. n-1 (t=n-1 leaves contribute the sure card)
        for state in by_t.get(t, ()):
            hit, edges = memo[state]
            m_state = mass[state]
            e_opt += m_state * hit
            for pc, child in edges:
                mass[child] += m_state * pc
    return e_opt, len(memo)


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
