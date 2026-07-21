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
from bisect import bisect_left
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


def hit_probability(m: int, ell: int, A: int, B: int) -> Fraction:
    """Exact realized probability that the optimal continuation guess is correct at a
    position whose run's last card is in block ``ell``, with ``A`` undealt cards on the
    CONTINUATION side (above the last card for an ascending run / below for descending,
    counting the guess target w1 itself) and ``B`` on the opposite side — E43, the
    per-position hit law behind the value law's intercept.

    From the E41 label-exchangeability Lemma, the undealt labels are independent-uniform
    (continuation side on ``{ell..2m-1}``, opposite side on ``{ell+1..2m-1}``); the guess
    w1 (smallest undealt above / largest below) is correct iff it has the minimum shuffle
    KEY among undealt cards. Counting those labels gives, with ``r = 2m - ell`` and
    ``d = j - ell`` (``j`` the guess's own block):

        P = (1/r) Σ_{d=0}^{r-1} (1 - (d + (d mod 2))/r)^{A-1} · (1 - (d - (d mod 2))/(r-1))^{B}

    unified for ascending (``ell`` even) and descending (``ell`` odd). The ``d=0`` term is
    1 for all A,B, so in the BULK (A,B → ∞) the hit → ``1/r = 1/(2m-ell)`` (the Lemma's
    bulk rate, which sets the value-law slope); the ``d ≥ 1`` terms are the finite-size
    EXCESS whose deck-sum is the intercept ``b(m)`` (the ``d=1`` term, ``(1/r)(1-2/r)^{A-1}``,
    is the ``H_{2m}^{(2)}`` generator). Gated EXACTLY against brute-force enumeration of the
    physical shuffle (`data/gt_hit_formula.py`, `tests/test_guessing_theorem.py`), and the
    pure-continuation strategy that guesses w1 every step is verified to equal ``E_opt``
    exactly, so ``E_opt(n,m) = Σ_t E[hit_probability(m, ell_t, A_t, B_t)]``.
    """
    r = 2 * m - ell
    total = Fraction(0)
    for d in range(r):  # d = (guess's block) - ell
        p_cont = Fraction(d + (d & 1), r)
        p_opp = Fraction(d - (d & 1), r - 1) if r - 1 else Fraction(0)
        total += (1 - p_cont) ** (A - 1) * (1 - p_opp) ** B
    return total / r


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


class _RationalShelfPosterior:
    """Exact-rational twin of `posterior.ShelfPosterior` — the next-card law as
    exact `Fraction`s, so the run-composition DP can run in exact arithmetic (E39,
    the proof-road instrument). Reuses `ShelfPosterior`'s slot geometry verbatim
    (the shelf shuffle's slot structure is integer; only the probabilities need
    rationalizing).

    Each card independently lands in one of ``2m`` slots (shelf x top/bottom,
    i.i.d. uniform); the output is the cards sorted by slot. The next-card law
    after an observed increasing-slot prefix factorizes into a chain term h_t and
    survival factors F_d(s) = |{d's slots > s}| / (2m), both exact ratios:

        P(next = c) proportional to  sum over c's slots s of  H_t(s^-) *
            product over remaining d != c of F_d(s),

    with H_t(s^-) = P(chain's last slot < s). The chain carries only H_t (survivals
    reapplied at query time) — the exact deferred-survival factorization
    `ShelfPosterior` uses, here in `Fraction`s rather than logs. Interface
    (`next_probs`/`observe`/`copy`) matches `ShelfPosterior` so `exact_e_dp_rational`
    is `exact_e_dp` with the float posterior swapped out.
    """

    def __init__(self, shelves: int, n: int) -> None:
        base = ShelfPosterior(shelves, list(range(1, n + 1)))
        self.n = n
        self.lanes = base.lanes
        self.nslots = base.nslots
        self._slots = base._slots  # per-card sorted integer slot lists
        self._owner = base._owner  # slot index -> owning input position
        self.stack = base.stack  # [1, 2, ..., n]
        self._index = base._index
        self._remaining = [True] * n
        self._n_remaining = n
        # Chain over the last observed card's slot: support (sorted) + normalized
        # cumulative. None means t = 0 (H_0(s^-) == 1 for every s).
        self._h_slots: list[int] | None = None
        self._h_cum: list[Fraction] | None = None

    def _h_before(self, s: int) -> Fraction:
        """H_t(s^-): chain probability that the last observed slot is < s."""
        if self._h_slots is None:
            return Fraction(1)
        return self._h_cum[bisect_left(self._h_slots, s)]

    def _sweep(self):
        """prod[s] = product of F_d(s) over remaining d with F_d(s) > 0;
        zeros[s] = count of remaining d with F_d(s) == 0. One exact pass of the
        global slot axis (the `ShelfPosterior` sweep, in `Fraction`s)."""
        lanes = self.lanes
        owner = self._owner
        remaining = self._remaining
        count = [lanes] * self.n
        cur = Fraction(1)
        cz = 0
        prod = [Fraction(1)] * self.nslots
        zeros = [0] * self.nslots
        for s in range(self.nslots):
            d = owner[s]
            if remaining[d]:
                k = count[d]
                count[d] = k - 1
                cur /= Fraction(k, lanes)  # drop F_d's old factor k/(2m)
                if k == 1:
                    cz += 1  # F_d(s) is now 0 (excluded from the product)
                else:
                    cur *= Fraction(k - 1, lanes)  # new F_d(s) = (k-1)/(2m)
            prod[s] = cur
            zeros[s] = cz
        return prod, zeros

    def next_probs(self) -> dict:
        """P(next dealt card = c | observed prefix), as exact `Fraction`s."""
        lanes = self.lanes
        prod, zeros = self._sweep()
        weights = {}
        total = Fraction(0)
        for i in range(self.n):
            if not self._remaining[i]:
                continue
            acc = Fraction(0)
            for r, s in enumerate(self._slots[i]):
                h = self._h_before(s)
                if h == 0:
                    continue
                kc = lanes - r - 1  # |c's slots > s| = F_c(s) * 2m
                if zeros[s] - (1 if kc == 0 else 0) > 0:
                    continue  # some other remaining d has F_d(s) == 0
                others = prod[s] if kc == 0 else prod[s] / Fraction(kc, lanes)
                acc += h * others
            weights[self.stack[i]] = acc
            total += acc
        if total == 0:
            raise ValueError("observed prefix impossible under this model")
        return {card: w / total for card, w in weights.items()}

    def observe(self, card) -> None:
        """Condition on `card` dealt next; the new chain is proportional to
        H_t(s^-) restricted to `card`'s slots (deferred survivals unchanged)."""
        i = self._index[card]
        slots = self._slots[i]
        hvals = [self._h_before(s) for s in slots]
        total = sum(hvals, Fraction(0))
        if total == 0:
            raise ValueError("observed prefix impossible under this model")
        cum = [Fraction(0)]
        acc = Fraction(0)
        for v in hvals:
            acc += v / total
            cum.append(acc)
        self._h_slots = slots
        self._h_cum = cum
        self._remaining[i] = False
        self._n_remaining -= 1

    def copy(self) -> "_RationalShelfPosterior":
        twin = object.__new__(_RationalShelfPosterior)
        twin.n = self.n
        twin.lanes = self.lanes
        twin.nslots = self.nslots
        twin._slots = self._slots
        twin._owner = self._owner
        twin.stack = self.stack
        twin._index = self._index
        twin._remaining = list(self._remaining)
        twin._n_remaining = self._n_remaining
        twin._h_slots = self._h_slots  # replaced wholesale on observe; safe to share
        twin._h_cum = self._h_cum
        return twin


def exact_e_dp_rational(n: int, m: int) -> tuple[Fraction, int]:
    """EXACT-RATIONAL optimal-guessing value E_opt(n, m) as a `Fraction`, via the
    run-composition DP (E39) — `exact_e_dp` run in exact arithmetic.

    Identical state graph and transition to `exact_e_dp` (E37's explicit form of
    Clay's m-shelf operator), but every posterior / hit / mass is an exact
    `Fraction` (`_RationalShelfPosterior`), so E_opt(n, m) is returned rational.
    This is the proof-road instrument: it lets the value law
    E_opt = c(m)*n + b(m) + o(1) be interrogated EXACTLY — whether the o(1) is
    truly zero past a finite N or (as expected) decays geometrically, and the
    intercept b(m) as an exact fraction to pattern-match a closed form. The
    geometric ratio recovered from the exact delta-sequence is a subdominant
    eigenvalue of the operator (the spectral-proof down-payment).

    The DP dedups states by sigma = (direction, rank-of-last, run-composition), so
    it is correct iff sigma is EXACTLY sufficient (E36); the n!-enumeration
    `exact_e` confirms that with exact `Fraction` equality at every cell it can
    reach (n <= ~8). Returns ``(E_opt as Fraction, number of DP states)``.

    Heavier than the float DP (exact arithmetic, denominators ~ (2m)^n) but the
    state count is modest at moderate n: practical to n ~ 26-30 at m=2 and n ~ 20
    at m=3 (CPython; PyPy for more). Pure shuffle-math (imports the posterior
    layer only — the two-layer rule).
    """
    root = (True, 0, ())  # (direction, rank-of-last, run composition)
    memo: dict[tuple, tuple[Fraction, list]] = {}

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
                if pc == 0:
                    continue
                ascending = j >= rank  # card > last iff its rank >= last's rank
                if not runcomp:
                    child_runcomp = (1,)
                elif ascending:
                    child_runcomp = runcomp[:-1] + (runcomp[-1] + 1,)
                else:
                    child_runcomp = runcomp + (1,)
                child = (ascending, j, child_runcomp)
                edges.append((pc, child))
                if child not in memo:  # dedup: explore each state's subtree once
                    twin = post.copy()
                    twin.observe(card)
                    explore(twin, child)
        memo[state] = (hit, edges)

    explore(_RationalShelfPosterior(m, n), root)

    by_t: dict[int, list] = defaultdict(list)
    for state in memo:
        by_t[sum(state[2])].append(state)
    mass: dict[tuple, Fraction] = defaultdict(lambda: Fraction(0))
    mass[root] = Fraction(1)
    e_opt = Fraction(0)
    for t in range(n):  # levels 0 .. n-1 (t=n-1 leaves contribute the sure card)
        for state in by_t.get(t, ()):
            hit, edges = memo[state]
            m_state = mass[state]
            e_opt += m_state * hit
            for pc, child in edges:
                mass[child] += m_state * pc
    return e_opt, len(memo)


def approx_e_dp(n: int, m: int, max_run: int | None = None) -> tuple[float, int]:
    """Approximate optimal-guessing value Ẽ_opt(n, m) via the run-length-MULTISET
    DP — the polynomial, large-m companion to the exact `exact_e_dp` (E38, the
    build (b) E36/E37 specified). Reaches deck scale where `exact_e_dp` is dead.

    `exact_e_dp`'s state is σ = (dir, rank, ascending-run COMPOSITION), exactly
    sufficient (E36) but Θ(n^{2m}) — dead for m ≥ 5, the DFH-real-machine regime
    (m=10). This DP coarsens the ORDERED composition to its run-length MULTISET
    (how many runs of each length; the order of the runs is discarded), keying
    states by σ̂ = (dir, rank, sorted-run-composition). That is the E38 closure.

    Why the multiset and not just #descents: the run *count* alone (#descents)
    FAILS at deck scale — it is bounded (~2m) while run lengths grow ~n/2m, so it
    discards an ever-larger share of the composition as n grows, and the per-step
    error compounds into a WRONG asymptotic slope (measured: E_opt(52,5) off by
    −4.3, E_opt(52,10) by −2.1 — a near-exact-looking n≤12 gate that collapses by
    n=52). The multiset keeps the run-length *distribution*, which is what the
    posterior actually depends on, and it recovers the deck-scale value: E_opt(52,5)
    to within MC error. It is APPROXIMATELY sufficient (E36's ordered composition
    is exactly sufficient; the multiset's within-bin hit gap is small and SHRINKS
    with m — the strong-mixing limit — but is nonzero for m ≥ 2). So this is a
    genuine approximation whose bias is MEASURED against `exact_e_dp` + the E35 MC
    (`data/gt_approx_dp.py`), EXACT only at m=1 (there the composition is irrelevant
    to the law — reproduces `exact_e_dp` / 3n/4 to float precision). Measured deck
    scale (n=52): exact-grade for m ≤ 5 (bias within MC se — e.g. m=5 z +0.3, and
    m=3 recovers E37's exact b(3)); a small residual bias at m=10 (−0.085, ≈ 0.9%),
    the one place MC still estimates E_opt better.

    Closure (assumed-density / mode): each σ̂ carries ONE representative
    `ShelfPosterior` — the posterior of a real dealt prefix realizing σ̂, reached
    via σ̂'s highest-mass incoming edge (the mode ordered-composition among those
    folded into σ̂, its ordered run-comp carried so the transition is E37's exact
    one). The hit h(σ̂) = max_c P(next=c) and the transition law are read from it;
    folded compositions' masses sum exactly. Ẽ_opt(n,m) = Σ_σ̂ P(σ̂)·h(σ̂).

    Cost: the returned σ̂ count is the reachable (dir, rank, run-multiset) states
    summed over prefix length — run-length PARTITIONS, polynomial in n for each
    fixed m and far below `exact_e_dp`'s ORDERED-composition Θ(n^{2m}) (smaller by
    up to (2m)!), though it still grows with m (partitions into ≤~2m parts) — m=5
    reaches n=52 (~3.6e6 states, ~2.5 min PyPy), m=10 wants ``max_run``. Setting
    ``max_run`` caps run lengths at that value in the state KEY only (the transition
    still uses the true ordered run-comp, so it stays E37-exact — only the bucketing
    coarsens): it merges long runs, shrinking the state space to a NEAR-identical
    value (measured: m=10, n=52 gives the same E to 4 dp for every max_run ≥ 2, at
    ~2.6e5 states for max_run=2) — the tail of the run-length distribution barely
    moves the optimal hit at large m. ``max_run=None`` (default) keeps the full
    multiset. Returns ``(Ẽ_opt, σ̂-state count)``.

    Pure shuffle-math (imports the posterior layer only — the two-layer rule).
    """
    root_post = ShelfPosterior(m, list(range(1, n + 1)))
    # σ̂ = (direction, rank-of-last, run-length multiset) -> (mass, representative
    # posterior, its ORDERED run-composition [carried for the exact transition]).
    level: dict[tuple, tuple[float, ShelfPosterior, tuple]] = {
        (True, 0, ()): (1.0, root_post, ())
    }
    e_opt = 0.0
    n_states = 0
    for _t in range(n):  # levels 0 .. n-1 (t=n-1 leaves add the sure last card)
        n_states += len(level)
        nxt_mass: dict[tuple, float] = defaultdict(float)
        # child σ̂ -> (best incoming edge mass, parent posterior, card, child run-comp)
        nxt_best: dict[tuple, tuple[float, ShelfPosterior, int, tuple]] = {}
        for (_dir, rank, _ms), (mass, post, runcomp) in level.items():
            probs = post.next_probs()
            remaining = sorted(probs)
            vec = [probs[c] for c in remaining]
            e_opt += mass * max(vec)
            if len(remaining) <= 1:
                continue  # leaf: one card left (hit == 1, already counted)
            for j, card in enumerate(remaining):
                pc = vec[j]
                if pc <= 0.0:
                    continue
                ascending = j >= rank  # card > last iff its rank ≥ last's rank
                # E37's exact transition on the ORDERED run-comp: a revealed card
                # extends the last ascending run, or (on a descent) opens a new one.
                if not runcomp:
                    crc = (1,)
                elif ascending:
                    crc = runcomp[:-1] + (runcomp[-1] + 1,)
                else:
                    crc = runcomp + (1,)
                # key by the run-length MULTISET (discard run order — the E38
                # coarsening), run lengths capped at max_run when set (large-m).
                ms = crc if max_run is None else tuple(min(r, max_run) for r in crc)
                child = (ascending, j, tuple(sorted(ms)))
                em = mass * pc
                nxt_mass[child] += em
                best = nxt_best.get(child)
                if best is None or em > best[0]:  # keep the mode-composition path
                    nxt_best[child] = (em, post, card, crc)
        new_level: dict[tuple, tuple[float, ShelfPosterior, tuple]] = {}
        for child, tot in nxt_mass.items():
            _, parent_post, card, crc = nxt_best[child]
            rep = parent_post.copy()
            rep.observe(card)  # materialize the representative once per σ̂
            new_level[child] = (tot, rep, crc)
        level = new_level
    return e_opt, n_states


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
