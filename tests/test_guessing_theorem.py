"""E35 regression anchors: exact optimal feedback-guessing value E(n, m) for
the DFH m-shelf shuffle, and the verification of Clay 2025's Conjecture 3.

These pin the promoted `data/gt_*.py` result (docs/GUESSING_THEOREM.md,
EXPERIMENTS E35) so a refactor of `forensics.shelf_class_prob`, the posterior,
or `ShelfShuffle` can't silently move it:

  * `total_prob(n, m) == 1`                     — the output law normalizes;
  * `E(n, 1) == 3n/4` exactly (Clay Thm 1.5)    — reproduces the proven m=1 value;
  * `E_opt == E_G` exactly on the n≤7, m≤6 grid — DFH's strategy G is optimal
      (the exact strategy-half of Conjecture 3, gap 0 as a Fraction);
  * two pinned exact E(9, m) spot values, cross-checked by `mc_e(9, m, seed)`
      (the independent float posterior, argmax `predicted` estimator) landing
      within a few se — the enumeration and the sequential posterior agree.

The exact grid is kept to n≤7 for speed (n! enumeration); the pinned n=9 values
are validated by the independent MC rather than re-enumerated (≈9 s each, and
redundant with the n≤7 grid, which already exercises the n-agnostic algorithm).
Both E(9, m) constants are regenerable offline via `exact_e(9, m)`.

Test seeds: the 24.0e9 block (E35; NOT shoe-sim seeds — a separate space).
"""

from bisect import bisect_left
from fractions import Fraction

import pytest

from ridefree.guessing_theorem import (
    approx_e_dp,
    build_perms,
    exact_e,
    exact_e_dp,
    exact_e_dp_rational,
    exact_e_from_perms,
    mc_e,
    run_lengths,
    total_prob,
    walk_prefixes,
)
from ridefree.posterior import ShelfPosterior

# Exact rationals from the enumeration probe (data/gt_exact.py), pinned.
EXACT_E9 = {
    2: Fraction(152375, 32768),   # 4.650116...
    3: Fraction(594355, 157464),  # 3.774545...
}

_SEED_BASE = 24_035_000_000  # E35 test pins, 24.x guessing-theorem seed space


def test_total_prob_normalizes():
    """The m-shelf output law sums to exactly 1 over all n! decks."""
    for n, m in [(2, 1), (4, 1), (5, 2), (6, 3), (7, 6), (8, 10)]:
        assert total_prob(n, m) == 1, (n, m, total_prob(n, m))


def test_m1_closed_form_is_three_n_over_four():
    """Clay 2025 Thm 1.5: single-shelf optimal reward is exactly 3n/4 (n≥2),
    and DFH's strategy G achieves it (Thm 1.4)."""
    for n in range(2, 8):
        e_opt, e_g = exact_e(n, 1)
        assert e_opt == Fraction(3 * n, 4), (n, e_opt)
        assert e_g == e_opt, (n, e_g, e_opt)
    # boundary case Clay's formula excludes
    assert exact_e(1, 1)[0] == Fraction(1)


def test_dfh_strategy_g_optimal_grid():
    """The exact strategy-half of Conjecture 3: DFH's m-independent strategy G
    ties the Bayes-optimal value with ZERO gap (exact Fraction) at every cell of
    the n≤7, m≤6 grid — including cells with small n/2m, beyond Clay's hedge."""
    for n in range(1, 8):
        perms = build_perms(n)
        for m in range(1, 7):
            e_opt, e_g = exact_e_from_perms(n, m, perms)
            assert e_opt == e_g, (n, m, e_opt - e_g)


def test_mc_matches_exact_e9():
    """The two pinned exact E(9, m) spot values, validated by an INDEPENDENT
    construction: the sequential float posterior's low-variance `predicted`
    estimator (mean unbiased for E_opt) agrees with the exact rationals to
    within a few se — enumeration and posterior concur, at n beyond the exact
    grid. (Regenerate the constants offline with `exact_e(9, m)`.)"""
    cases = {2: _SEED_BASE + 102, 3: _SEED_BASE + 203}
    for m, seed in cases.items():
        exact = float(EXACT_E9[m])
        pred, se_pred, hit, _ = mc_e(9, m, 3000, seed)
        assert abs(pred - exact) <= 4 * se_pred, (m, pred, exact, se_pred)
        # the higher-variance realized hits track the same value (loose band)
        assert abs(hit - exact) <= 0.2, (m, hit, exact)


# --- E36: the n!-wall sufficiency probe (data/gt_sufficiency.py) -------------
# Pin the scoping result: the optimal per-step hit max_c P(next=c | prefix) is
# an EXACT function of (direction, rank-of-last, ascending-run composition) —
# but of no polynomial coarsening at m≥2, because the reveal ORDER (which the
# run composition records) is load-bearing. This characterizes why Clay's
# m-shelf transition matrix is open. See docs/GUESSING_THEOREM.md, EXPERIMENTS
# E36. All checks are exact (Δhit = 0 as float) and deterministic (no seeds).


def _remaining(prefix, n):
    return sorted(set(range(1, n + 1)).difference(prefix))


def _dir_up(prefix):
    return len(prefix) < 2 or prefix[-1] > prefix[-2]


def _rank_last(prefix, n):
    last = prefix[-1] if prefix else 0
    return bisect_left(_remaining(prefix, n), last)


def _key_dir_rank(prefix, n):
    return (len(prefix), _dir_up(prefix), _rank_last(prefix, n))


def _key_dir_rank_runcomp(prefix, n):
    return (_dir_up(prefix), _rank_last(prefix, n), run_lengths(prefix))


def _key_set_last_dir(prefix, n):
    last = prefix[-1] if prefix else 0
    return (frozenset(_remaining(prefix, n)), last, _dir_up(prefix))


def _max_hit_range(n, m, keyfn):
    """Largest within-group spread of the optimal per-step hit when prefixes
    are binned by `keyfn`; 0 ⇔ the statistic is exactly sufficient at (n, m)."""
    groups: dict = {}
    for prefix, hit, _ in walk_prefixes(n, m):
        k = keyfn(prefix, n)
        lo, hi = groups.get(k, (2.0, -1.0))
        groups[k] = (hit if hit < lo else lo, hit if hit > hi else hi)
    return max(hi - lo for lo, hi in groups.values())


def test_run_lengths_composition():
    """The ascending-run composition (the descent structure a prefix carries)."""
    assert run_lengths(()) == ()
    assert run_lengths((5,)) == (1,)
    assert run_lengths((1, 2, 5, 3, 4)) == (3, 2)
    assert run_lengths((2, 1)) == (1, 1)  # one descent
    assert run_lengths((1, 2, 3)) == (3,)  # no descent


def test_walk_prefixes_reconstructs_e_opt():
    """Σ over prefixes of P(prefix)·max-posterior-hit == E_opt exactly — ties
    the E36 prefix walk to the E35 permutation enumeration."""
    for n, m in [(6, 1), (6, 2), (6, 3), (5, 5)]:
        recon = sum(pprob * hit for _, hit, pprob in walk_prefixes(n, m))
        assert abs(recon - float(exact_e(n, m)[0])) < 1e-9, (n, m, recon)


def test_runcomp_is_exactly_sufficient():
    """(direction, rank-of-last, run composition) is EXACTLY sufficient for the
    optimal per-step hit at every m — the minimal sufficient statistic."""
    for m in (2, 3, 5):
        assert _max_hit_range(6, m, _key_dir_rank_runcomp) < 1e-9, m


def test_m1_collapses_to_dir_rank_but_m2_does_not():
    """m=1 (Clay's proven, tractable case): the run composition collapses —
    the polynomial (direction, rank) statistic is already exactly sufficient.
    m=2 (open case): it is NOT — the same (direction, rank) bin spans distinct
    hits, so no polynomial coarsening of the sufficient statistic survives."""
    assert _max_hit_range(6, 1, _key_dir_rank) < 1e-9
    assert _max_hit_range(6, 2, _key_dir_rank) > 0.4


def test_set_level_statistic_insufficient_at_m2():
    """The reveal ORDER is load-bearing at m≥2: even the exponential ceiling
    (remaining SET, last card, direction) leaves a 0.5 hit gap — the concrete
    witness is remaining {3,4,6}, last 5, dir up (prefix (1,2,5) → hit 0.5 vs
    (2,1,5) → hit 1.0, split only by the earlier descent 2→1)."""
    rng = _max_hit_range(6, 2, _key_set_last_dir)
    assert 0.49 < rng < 0.51, rng


def test_run_composition_state_transition_is_closed():
    """The whole next-card posterior (indexed by the next card's rank among
    remaining), not just its max, is a function of the (dir, rank, run-comp)
    state — so the state's transition is closed and the O(2ⁿ) exact DP over it
    is valid (E36 build (a)). Checked exactly (max Δposterior per state == 0)."""
    for m in (2, 3):
        seen: dict = {}
        maxdev = 0.0

        def descend(post, prefix):
            nonlocal maxdev
            probs = post.next_probs()
            R = sorted(probs)
            vec = tuple(probs[c] for c in R)  # posterior by remaining-rank
            last = prefix[-1] if prefix else 0
            key = (_dir_up(prefix), bisect_left(R, last), run_lengths(prefix))
            if key not in seen:
                seen[key] = vec
            else:
                maxdev = max(maxdev,
                             max(abs(a - b) for a, b in zip(seen[key], vec)))
            if len(prefix) == 5:
                return
            for c, pc in probs.items():
                if pc > 0.0:
                    child = post.copy()
                    child.observe(c)
                    descend(child, prefix + (c,))

        descend(ShelfPosterior(m, list(range(1, 7))), ())
        assert maxdev < 1e-9, (m, maxdev)


# --- E37: the run-composition DP — exact E_opt past the n! wall ---------------
# Pin build (a): exact_e_dp aggregates the E36 (dir, rank, run-composition) state
# into E_opt(n,m) = Σ_σ P(σ)·h(σ), reproducing the exact enumeration far beyond
# its n≈9 reach. The reachable-state count is Θ(n^{2m}) — polynomial for each
# fixed m (m=1 is exactly n²−n+1), exponential only in m — which is why exact
# deck-scale values exist for small m yet Clay's general-m matrix stays open.
# See docs/GUESSING_THEOREM.md §1, EXPERIMENTS E37. Float-deterministic.

_SEED_BASE_E37 = 24_060_000_000  # E37 deck-scale gate (24.x guessing-theorem space)


def test_exact_e_dp_matches_enumeration():
    """The DP reproduces the O(n·n!) exact enumeration on the n≤7 grid (m=1..4) —
    the end-to-end proof that the (dir, rank, run-composition) transition is
    closed (a closure violation would perturb the aggregate E_opt)."""
    for n in range(1, 8):
        perms = build_perms(n)
        for m in range(1, 5):
            e_ref = float(exact_e_from_perms(n, m, perms)[0])
            e_dp, _ = exact_e_dp(n, m)
            assert abs(e_dp - e_ref) < 1e-9, (n, m, e_dp, e_ref)


def test_exact_e_dp_m1_state_count_is_quadratic():
    """m=1 (Clay's tractable case): the reachable-state count is EXACTLY n²−n+1,
    the polynomial signature the DP inherits from the single-shelf ≤1-valley
    structure — a constructive counterpart to the 3n/4 closed form. m=2 grows
    strictly faster than any cubic (the Θ(n^{2m})=Θ(n⁴) law), so no such collapse
    survives at m≥2."""
    for n in range(2, 13):
        _, ns = exact_e_dp(n, 1)
        assert ns == n * n - n + 1, (n, ns)
    _, ns6 = exact_e_dp(6, 2)
    _, ns12 = exact_e_dp(12, 2)
    assert ns12 / ns6 > 8.0, (ns6, ns12)  # doubling n scales states by >2³


def test_exact_e_dp_m1_deck_scale_is_three_n_over_four():
    """At deck scale the DP returns Clay's proven m=1 value EXACTLY (not MC):
    E_opt(52,1) = 3·52/4 = 39, from only n²−n+1 = 2653 states — the wall broken
    in the one case with a closed form to check against."""
    e, ns = exact_e_dp(52, 1)
    assert abs(e - 39.0) < 1e-9, e
    assert ns == 52 * 52 - 52 + 1


def test_exact_e_dp_deck_scale_m2_matches_mc():
    """The first EXACT E_opt(52, m≥2): the DP's deck-scale m=2 value is pinned
    (float-deterministic) and agrees with the independent MC posterior within se
    — Clay's m-shelf operator evaluated exactly where E35 could only sample. The
    exact correction δ = E_opt − c(2)·52 = −0.0486 pins Follow-up A's b(2).
    (Slow: the Θ(n⁴) state graph is ~5.7e5 states.)"""
    e, ns = exact_e_dp(52, 2)
    assert abs(e - 27.034722) < 1e-4, e  # pinned float-deterministic value
    assert ns == 566203, ns
    pred, se_pred, _, _ = mc_e(52, 2, 1500, _SEED_BASE_E37 + 2)
    assert abs(e - pred) <= 4 * se_pred, (e, pred, se_pred)


# --- E38: the run-length-MULTISET approximate DP — deck-scale E_opt for large m -
# Pin build (b): approx_e_dp coarsens E37's exactly-sufficient ORDERED
# run-composition to keep only the run-length MULTISET (run order discarded). This
# is EXACT at m=1 (the composition is irrelevant to the law) and carries a small
# BOUNDED bias for m≥2 that shrinks with m (strong mixing), recovering the
# deck-scale value where exact_e_dp is Θ(n^{2m})-dead. The literal alternative —
# keeping only the run COUNT (#descents) — instead FAILS at deck scale (its bias
# grows with n into a wrong slope), which is why the multiset is the closure. The
# `max_run` cap merges long runs in the KEY only (transition stays exact),
# shrinking the state space near-losslessly for very large m. See
# docs/GUESSING_THEOREM.md §1, EXPERIMENTS E38. Float-deterministic.

_SEED_BASE_E38 = 24_070_000_000  # E38 deck-scale MC gate (24.x guessing space)


def test_approx_e_dp_m1_is_exact():
    """m=1: the composition is irrelevant to the law, so the multiset closure is
    EXACT — reproduces Clay's 3n/4 from n²−n+1 states, all the way to deck scale
    (the one m with a closed form to check the approximate DP against)."""
    for n in (3, 6, 12, 20, 52):
        e, _ = approx_e_dp(n, 1)
        assert abs(e - 0.75 * n) < 1e-9, (n, e)


def test_approx_e_dp_small_grid_bounded_bias():
    """On the n≤7 grid the multiset DP tracks the exact enumeration to a small
    bounded gap (an approximation for m≥2, not zero-gap), and m=1 is exact — the
    approximate counterpart to the E37 exactness gate."""
    worst_m1 = worst = 0.0
    for n in range(1, 8):
        perms = build_perms(n)
        for m in range(1, 8):
            ref = float(exact_e_from_perms(n, m, perms)[0])
            e, _ = approx_e_dp(n, m)
            worst = max(worst, abs(e - ref))
            if m == 1:
                worst_m1 = max(worst_m1, abs(e - ref))
    assert worst_m1 < 1e-9, worst_m1
    assert worst < 0.05, worst


def test_approx_e_dp_max_run_cap_is_lossless_reduction():
    """`max_run` caps run lengths in the state KEY only (the transition uses the
    true ordered run-comp, so it stays E37-exact), so max_run≥n reproduces the
    full multiset EXACTLY, while a finite cap gives a near-identical value from
    no more states — the large-m feasibility lever, shown not to distort."""
    for n, m in [(16, 3), (20, 5)]:
        full, ns_full = approx_e_dp(n, m)
        big, ns_big = approx_e_dp(n, m, max_run=n)
        cap, ns_cap = approx_e_dp(n, m, max_run=3)
        assert abs(full - big) < 1e-12 and ns_full == ns_big, (n, m)
        assert abs(cap - full) < 1e-3, (n, m, cap - full)
        assert ns_cap <= ns_full, (n, m, ns_cap, ns_full)


def test_approx_e_dp_multiset_beats_run_count_at_deck_scale():
    """The E38 pivot at deck scale (m=3, n=52), where exact_e_dp is dead so MC is
    the referee: keeping the run-length MULTISET tracks the true value to within MC
    error, while keeping only the run COUNT (#descents) falls ~0.7 low — the count
    is bounded ~2m while run lengths grow, so it discards the slope-carrying signal.
    (Slow: the deck-scale DPs + the MC referee.)"""
    pred, se, _, _ = mc_e(52, 3, 2000, _SEED_BASE_E38 + 3)
    multiset, _ = approx_e_dp(52, 3, max_run=2)  # cap is lossless here (see study)
    count = _run_count_e_dp(52, 3)  # the rejected closure: #descents key only
    assert abs(multiset - pred) < 0.1, (multiset, pred, se)
    assert count < pred - 0.4, (count, pred)


def _run_count_e_dp(n: int, m: int) -> float:
    """The REJECTED E38 closure (for the contrast test): E37's transition keyed by
    the run COUNT #descents only, mode representative per (dir, rank, #descents)."""
    from ridefree.posterior import ShelfPosterior

    root = ShelfPosterior(m, list(range(1, n + 1)))
    level = {(True, 0, 0): (1.0, root, ())}
    e_opt = 0.0
    for _t in range(n):
        nm: dict = {}
        nb: dict = {}
        for (_d, rank, _k), (mass, post, rc) in level.items():
            probs = post.next_probs()
            rem = sorted(probs)
            vec = [probs[c] for c in rem]
            e_opt += mass * max(vec)
            if len(rem) <= 1:
                continue
            for j, card in enumerate(rem):
                pc = vec[j]
                if pc <= 0.0:
                    continue
                asc = j >= rank
                crc = (1,) if not rc else (
                    rc[:-1] + (rc[-1] + 1,) if asc else rc + (1,))
                child = (asc, j, len(crc) - 1)
                em = mass * pc
                nm[child] = nm.get(child, 0.0) + em
                b = nb.get(child)
                if b is None or em > b[0]:
                    nb[child] = (em, post, card, crc)
        level = {}
        for child, tot in nm.items():
            _, pp, card, crc = nb[child]
            rep = pp.copy()
            rep.observe(card)
            level[child] = (tot, rep, crc)
    return e_opt


def test_approx_e_dp_deck_scale_m10_matches_mc():
    """The large-m deliverable: E_opt(52,10) — the DFH real machine — where
    exact_e_dp is Θ(n^20)-dead and E35 had only a Monte-Carlo sample. The multiset
    DP (max_run=2, converged) is float-deterministic and lands within ~0.1 of the
    independent MC (and DFH's published 9.3) — the honest small residual bias of
    the closure. (Slow: the state graph + the MC cross-check.)"""
    e, ns = approx_e_dp(52, 10, max_run=2)
    assert abs(e - 9.21440) < 1e-3, e  # pinned float-deterministic value
    assert ns == 264967, ns
    pred, se, _, _ = mc_e(52, 10, 1500, _SEED_BASE_E38 + 810)
    assert abs(e - pred) < 0.15, (e, pred, se)


# --- E39: the EXACT-RATIONAL run-composition DP -> exact b(m) + the spectrum ---
# Pin the proof-road instrument: exact_e_dp_rational runs E37's DP in exact
# Fractions, so E_opt(n,m) is rational and the value law's correction
# delta(n,m) = E_opt - c(m)*n can be studied EXACTLY. Two results the float DP
# could not reach — (1) b(m) as an exact fraction (b(2)=-7/144, b(3)=-269/3600,
# b(4)=-63449/705600), the o(1) being genuinely non-zero; (2) the feedback
# operator's spectrum: delta(n) obeys an order-(4m-3) linear recurrence whose
# char poly is (x-1)*prod(x-i/m)^3*prod(x-(2i-1)/2m), i.e. subdominant eigenvalues
# {i/m} (mult 3) and {(2i-1)/2m} (mult 1), spectral gap 1/m. This is the
# COMPLETE-FEEDBACK operator (Clay's open m-shelf matrix), NOT Tripathi's
# no-feedback POSITION matrix. See docs/GUESSING_THEOREM.md §2, EXPERIMENTS E39.


def test_exact_e_dp_rational_matches_enumeration_exactly():
    """The rational DP reproduces the n! enumeration with EXACT Fraction equality
    (not the float 1e-9 of the E37 gate) across the n<=7, m=1..4 grid — the
    strongest confirmation that the (dir, rank, run-composition) state is EXACTLY
    sufficient (a closure violation would surface as an unequal fraction)."""
    for n in range(2, 8):
        perms = build_perms(n)
        for m in range(1, 5):
            ref = exact_e_from_perms(n, m, perms)[0]
            dp = exact_e_dp_rational(n, m)[0]
            assert isinstance(dp, Fraction) and dp == ref, (n, m, dp, ref)


def test_exact_e_dp_rational_m1_and_pinned_e9():
    """m=1 is EXACTLY 3n/4 (Clay Thm 1.5) as a Fraction, and the two pinned exact
    E(9, m) rationals reproduce — the rational DP agreeing with the enumeration
    at n beyond the exact grid."""
    for n in range(2, 11):
        assert exact_e_dp_rational(n, 1)[0] == Fraction(3 * n, 4), n
    for m, frac in EXACT_E9.items():
        assert exact_e_dp_rational(9, m)[0] == frac, (m, frac)


def _pmul(a, b):
    r = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            r[i + j] += ai * bj
    return r


def _b_and_spectrum_check(m, deltas):
    """Build the eigenvalue-law recurrence for m, assert it reproduces the exact
    delta sequence, and return b(m) = lim delta via the generating function."""
    # char poly (x-1) * prod (x-i/m)^3 * prod (x-(2i-1)/2m)^1  (index = power)
    p = [Fraction(-1), Fraction(1)]
    for r, mult in ([(Fraction(i, m), 3) for i in range(1, m)]
                    + [(Fraction(2 * i - 1, 2 * m), 1) for i in range(1, m)]):
        for _ in range(mult):
            p = _pmul(p, [-r, Fraction(1)])
    L = len(p) - 1
    assert L == 4 * m - 3, (m, L)
    c = [-p[L - 1 - j] for j in range(L)]  # delta[i] = sum c[j] delta[i-1-j]
    assert all(sum(c[j] * deltas[i - 1 - j] for j in range(L)) == deltas[i]
               for i in range(L, len(deltas))), m  # recurrence holds exactly
    # b = N(1)/E(1),  C=(1-x)E,  N=(C*G) mod x^L
    C = [Fraction(1)] + [-cj for cj in c]
    E, acc = [], Fraction(0)
    for k in range(L):
        acc += C[k]
        E.append(acc)
    N = [sum(C[j] * deltas[k - j] for j in range(min(k, L) + 1)
             if 0 <= k - j < len(deltas)) for k in range(L)]
    return sum(N) / sum(E)


@pytest.mark.slow
def test_rational_dp_recovers_b2_closed_form_and_spectrum():
    """End-to-end (slow): from the exact delta(n,2) sequence, the order-5
    eigenvalue-law recurrence — char poly (x-1)(x-1/4)(x-1/2)^3 — holds exactly,
    and its generating-function limit is b(2) = -7/144 EXACTLY. Pins both the
    exact intercept and the operator's subdominant spectrum {1/4, 1/2(x3)}."""
    c = sum(Fraction(1, k) for k in range(1, 5)) / 4  # c(2) = H_4/4 = 25/48
    deltas = [exact_e_dp_rational(n, 2)[0] - c * n for n in range(6, 19)]
    b = _b_and_spectrum_check(2, deltas)
    assert b == Fraction(-7, 144), b
