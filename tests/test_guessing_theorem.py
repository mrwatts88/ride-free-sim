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
    _RationalShelfPosterior,
    approx_e_dp,
    build_perms,
    exact_e,
    exact_e_dp,
    exact_e_dp_rational,
    exact_e_from_perms,
    hit_probability,
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
    assert b == _bm_closed_form(2)  # end-to-end: the DP's b matches the E40 form


# --- E40: the closed form for the intercept b(m) + the m=5 spectrum ------------
# Phase 1 of the proof road. The eigenvalue law is CONFIRMED at m=5 (the critical
# checkpoint) and m=6 (extending E39's m=2,3 rigorous / m=4 OOS), and the intercept
# has a CLOSED FORM (E39's OPEN item, resolved):
#     b(m) = 3/2 - 1/(4m) - H_{2m}^{(2)},   H_{2m}^{(2)} = sum_{k=1}^{2m} 1/k^2
# reproducing b(1..6) exactly, limit 3/2 - pi^2/6. So the full value law is
#     E_opt(n,m) = (H_2m/2m)*n + [3/2 - 1/(4m) - H_2m^(2)] + O((1-1/m)^n).
# See docs/GUESSING_THEOREM.md §2-3, EXPERIMENTS E40. Exact/deterministic.


def _H2(k):
    return sum((Fraction(1, i * i) for i in range(1, k + 1)), Fraction(0))


def _bm_closed_form(m):
    """The E40 closed form for the value-law intercept b(m) = lim_n E_opt - c(m)*n."""
    return Fraction(3, 2) - Fraction(1, 4 * m) - _H2(2 * m)


# The exact intercepts, pinned. b(2),(3) are rigorous over Q (E39 independent
# Berlekamp-Massey); b(4),(5),(6) are the GF limit of the eigenvalue-law recurrence
# validated out-of-sample. Regenerable via data/gt_rational_dp.py.
_BM_EXACT = {
    1: Fraction(0),
    2: Fraction(-7, 144),
    3: Fraction(-269, 3600),
    4: Fraction(-63449, 705600),
    5: Fraction(-126713, 1270080),
    6: Fraction(-16388909, 153679680),
}


def test_bm_closed_form_reproduces_exact_intercepts():
    """b(m) = 3/2 - 1/(4m) - H_{2m}^{(2)} equals every known exact intercept
    (m=1..6) — a 3-parameter form matching six exact rationals (the unique <=3
    feature fit). At m=1 it is 0, so the value law is exactly 3n/4 (Clay Thm 1.5)
    with no correction; the m->inf limit is finite, 3/2 - pi^2/6."""
    for m, exact in _BM_EXACT.items():
        assert _bm_closed_form(m) == exact, (m, _bm_closed_form(m), exact)
    assert abs(float(_bm_closed_form(50)) - (1.5 - 1.6449340668482264)) < 1e-2


def test_bm_closed_form_matches_spectrum_recurrence_from_pinned_deltas():
    """The m=5 CRITICAL-CHECKPOINT result, pinned from the exact delta(n,5) sequence
    (values from data/gt_rational_dp.py, so no expensive DP recompute here): the
    conjectured order-17 eigenvalue-law recurrence — char poly
    (x-1)*prod(x-i/5)^3*prod(x-(2i-1)/10) — holds EXACTLY out-of-sample on the real
    m=5 data (a closure/spectrum error would break it), and its generating-function
    limit is b(5) = -126713/1270080 = the E40 closed form. Confirms the eigenvalue
    law is not a small-m accident and links it to the closed form. The delta values
    are regenerable via exact_e_dp_rational(n, 5) (PyPy)."""
    # exact delta(n,5) = E_opt(n,5) - c(5)*n as Fractions, n=6..24, regenerable via
    # exact_e_dp_rational(n, 5) (reported by data/gt_rational_dp.py, PyPy).
    delta5 = {
        6: Fraction(428557, 525000), 7: Fraction(8240371, 11250000),
        8: Fraction(50905181, 78750000), 9: Fraction(24589429, 43750000),
        10: Fraction(3794319097, 7875000000),
        11: Fraction(10021245751, 24609375000),
        12: Fraction(88994101759, 262500000000),
        13: Fraction(2732413087889, 9843750000000),
        14: Fraction(12535922131387, 56250000000000),
        15: Fraction(716261399201, 4101562500000),
        16: Fraction(1043427117922069, 7875000000000000),
        17: Fraction(9448107053718463, 98437500000000000),
        18: Fraction(28240508386963373, 437500000000000000),
        19: Fraction(185382252440452531, 4921875000000000000),
        20: Fraction(1165240950922632173, 78750000000000000000),
        21: Fraction(-213655476760719823, 46875000000000000000),
        22: Fraction(-821570714658063217651, 39375000000000000000000),
        23: Fraction(-170046750938669693653, 4921875000000000000000),
        24: Fraction(-96577741626494762717, 2100000000000000000000),
    }
    deltas = [delta5[n] for n in range(6, 25)]  # 19 terms, n=6..24
    b = _b_and_spectrum_check(5, deltas)  # order-17 recurrence must hold OOS
    assert b == Fraction(-126713, 1270080), b
    assert b == _bm_closed_form(5)


# --- E41: the SLOPE PROOF — c(m) = H_2m/2m for all m, via block decomposition ---
# Pin the Phase-2 proof (data/gt_slope_proof.py, docs/GUESSING_THEOREM.md §THE SLOPE
# PROOF): the m-shelf output is 2m monotone blocks B_ell (label ell = card's uniform
# lane), and the KEY LEMMA — conditioned on the prefix's true block-parse, the undealt
# labels are exactly independent-uniform ({ell..2m-1} for values > v, {ell+1..2m-1}
# for < v) — makes the optimal hit EXACTLY 1/(2m-ell). Each block holds 1/(2m) of the
# deck, so the mean hit -> (1/2m) sum 1/(2m-ell) = H_2m/2m. This PROVES the open leading
# term of Clay's Conjecture 3. Exact/deterministic (the Lemma is enumeration; the
# convergence is exact rationals).


def _output_from_labels(labels):
    """Deterministic shuffle output for label vector labels[c-1]=L_c: sort cards
    1..n by key (L, +c) even / (L, -c) odd — matching ShelfShuffle's slot order."""
    n = len(labels)
    return sorted(range(1, n + 1),
                  key=lambda c: (labels[c - 1],
                                 c if labels[c - 1] % 2 == 0 else -c))


def test_slope_proof_label_lemma_exact_by_enumeration():
    """THE LINCHPIN, exact: enumerate every (2m)^n label vector; for each dealt
    prefix at an ascending interior position, condition on the prefix AND its true
    block-parse (dealt cards' labels) and verify the undealt labels are EXACTLY
    independent-uniform on the Lemma's sets, and the optimal hit is EXACTLY
    1/(2m-ell). A single counterexample would break the slope proof."""
    from collections import defaultdict
    from itertools import product

    for m, n in [(2, 5), (3, 4)]:
        lanes = 2 * m
        joint: dict = defaultdict(lambda: defaultdict(int))
        for labels in product(range(lanes), repeat=n):
            out = _output_from_labels(labels)
            for s in range(1, n):
                prefix = tuple(out[:s])
                v = out[s - 1]
                ell = labels[v - 1]
                if ell % 2 != 0:  # test ascending runs (descending is the mirror)
                    continue
                undealt = tuple(c for c in range(1, n + 1) if c not in prefix)
                if not any(c > v for c in undealt):
                    continue
                parse = tuple(labels[c - 1] for c in prefix)
                key = (prefix, parse, v, ell)
                joint[key][tuple(labels[c - 1] for c in undealt)] += 1
        checked = 0
        for (prefix, parse, v, ell), dist in joint.items():
            undealt = [c for c in range(1, n + 1) if c not in prefix]
            supports = [list(range(ell if c > v else ell + 1, lanes))
                        for c in undealt]
            total = sum(dist.values())
            # every combination in the product support occurs exactly once (=>
            # undealt labels independent + uniform), and nothing outside it occurs
            prod_size = 1
            for sup in supports:
                prod_size *= len(sup)
            assert len(dist) == prod_size and total == prod_size, (
                m, prefix, len(dist), prod_size)
            for combo in product(*supports):
                assert dist.get(combo, 0) == 1, (m, prefix, combo)
            # optimal hit = P(next = w_1) = 1/(2m-ell), w_1 = min undealt > v
            w1 = min(c for c in undealt if c > v)
            wi = undealt.index(w1)
            hit = Fraction(sum(cnt for lab, cnt in dist.items() if lab[wi] == ell),
                           total)
            assert hit == Fraction(1, lanes - ell), (m, prefix, hit)
            checked += 1
        assert checked > 50, (m, checked)  # the enumeration actually exercised it


def test_slope_proof_hit_converges_to_block_rate():
    """The observer's true finite-n hit at a fixed block-0 interior prefix (1,2,3)
    is slightly ABOVE 1/(2m) (it mixes over parse hypotheses — an interior block
    could be empty), and that excess decays MONOTONICALLY to 0 as n grows, in exact
    rationals — so the optimal hit -> 1/(2m-ell)=1/(2m) at block 0, the block-rate
    the slope proof sums. (This is why the O(1) intercept is a boundary/mixing term.)"""
    for m in (2, 3):
        target = Fraction(1, 2 * m)
        prev_excess = None
        for n in (10, 14, 18, 22):
            post = _RationalShelfPosterior(m, n)
            for c in (1, 2, 3):
                post.observe(c)
            excess = max(post.next_probs().values()) - target
            assert excess > 0, (m, n, excess)  # observer is never below block rate
            if prev_excess is not None:
                assert excess < prev_excess / 3, (m, n, excess, prev_excess)
            prev_excess = excess
        assert prev_excess < Fraction(1, 1000), (m, prev_excess)  # -> 0


def test_slope_proof_block_hit_law_exact_rational():
    """The block-hit law 1/(2m-ell), pinned on hand-built DEEP interior prefixes via
    the exact-rational posterior: an ascending run near the bottom of the value range
    with an empty odd block skipped is far from all boundaries, so the optimal hit is
    within the geometric tail of 1/(2m-ell). Constructs prefixes that walk into blocks
    0,1,2 (via a peak then a valley) and checks each block's rate."""
    m, n = 2, 40  # 2m=4 blocks; large n so the parse-mixing excess is tiny
    # block 0 (ascending): prefix 1,2,3 -> hit ~ 1/4
    p0 = _RationalShelfPosterior(m, n)
    for c in (1, 2, 3):
        p0.observe(c)
    assert abs(float(max(p0.next_probs().values())) - 1 / 4) < 1e-3
    # into block 1 (descending) via a peak at the top, then descend: 1,2,3,40,39,38
    p1 = _RationalShelfPosterior(m, n)
    for c in (1, 2, 3, 40, 39, 38):
        p1.observe(c)
    assert abs(float(max(p1.next_probs().values())) - 1 / 3) < 1e-2  # 1/(4-1)
    # into block 2 (ascending) via a valley: ...,38,4,5,6 (descend then ascend low)
    p2 = _RationalShelfPosterior(m, n)
    for c in (1, 2, 3, 40, 39, 38, 4, 5, 6):
        p2.observe(c)
    assert abs(float(max(p2.next_probs().values())) - 1 / 2) < 1e-2  # 1/(4-2)


# --- E42: the FADE RATE proven from blocks + the INTERCEPT decomposition --------
# Pin the Phase-2 tail (data/gt_fade_intercept.py, docs/GUESSING_THEOREM.md §THE
# SLOPE PROOF -> NEXT STEP; EXPERIMENTS E42). For a block-0 ascending contiguous
# prefix (1..k), conditioning on the last card's true block L_k=ell, every undealt
# card survives (key > key(last)) INDEPENDENTLY with probability rho_ell, so
#     P(prefix, L_k=ell) = K_ell * rho_ell^(n-k),   rho_ell = (2m-ell)/2m  (even)
#                                                          = (2m-1-ell)/2m (odd),
# with K_ell n-independent. The dominant competitor to the true parse (ell=0) is
# ell in {1,2}, both at rho/rho_0 = (2m-2)/2m = 1-1/m — so the fade is O((1-1/m)^n)
# for ALL m (upgrading E39's m<=6 Berlekamp-Massey spectrum to a PROVEN dominant
# rate). The intercept splits as b(m) = -H_2m (interior undercount, DERIVED) + B(m)
# with B(m) = b(m)+H_2m = 3/2 - 1/(4m) + H_2m - H_2m^(2) (the boundary constant).


def _rho(m, ell):
    """Per-undealt-card survival probability P(key(c) > key(last)) at a block-0
    ascending prefix whose last card is in block ell."""
    lanes = 2 * m
    return Fraction(lanes - ell if ell % 2 == 0 else lanes - 1 - ell, lanes)


def test_fade_survival_law_is_exactly_geometric_by_enumeration():
    """THE FADE-RATE CORE, exact: P(output prefix==(1..k) AND L_k=ell) is EXACTLY
    K_ell * rho_ell^(n-k). Enumerate every (2m)^n label vector and verify the joint
    probability scales by exactly rho_ell when n grows by 1 (so K_ell is constant),
    which is what makes the observer's block-confusion — and hence the value-law
    fade — geometric at rate rho_ell/rho_0."""
    from collections import defaultdict
    from itertools import product

    for m, k in [(2, 3), (3, 3)]:
        lanes = 2 * m
        prefix = tuple(range(1, k + 1))
        prev = None  # P(A_ell) at the previous n
        for n in range(k + 1, k + 5):
            cnt = defaultdict(int)
            for labels in product(range(lanes), repeat=n):
                if tuple(_output_from_labels(labels)[:k]) == prefix:
                    cnt[labels[k - 1]] += 1
            tot = lanes ** n
            cur = {ell: Fraction(c, tot) for ell, c in cnt.items()}
            if prev is not None:
                for ell, p in cur.items():
                    if prev.get(ell, 0) != 0:  # exact geometric step by rho_ell
                        assert p == prev[ell] * _rho(m, ell), (m, n, ell)
            prev = cur


def test_fade_dominant_rate_is_one_minus_one_over_m():
    """The dominant block-confusion rate (the largest subdominant eigenvalue of the
    value law) is EXACTLY 1-1/m, realized by ell in {1,2} — a same-direction block
    SKIP ell->ell+2 (ratio (2m-2)/2m), NOT the intervening-empty-block (1-1/2m).
    This is 'the factor of 2 in the exponent'. Pure arithmetic, all m."""
    for m in range(2, 8):
        rho0 = _rho(m, 0)
        assert rho0 == 1
        ratios = {ell: _rho(m, ell) / rho0 for ell in range(1, 2 * m)
                  if _rho(m, ell) != 0}
        dominant = max(ratios.values())
        assert dominant == Fraction(m - 1, m), (m, dominant)
        winners = {ell for ell, r in ratios.items() if r == dominant}
        assert {1, 2} <= winners, (m, winners)


def test_intercept_interior_undercount_and_boundary_identity():
    """The intercept b(m) = -H_2m + B(m): interior guesses of block ell number
    |B_ell|-1 and each hit exactly 1/(2m-ell), contributing (H_2m/2m)*n - H_2m — so
    the interior undercount is exactly -H_2m. The boundary constant B(m) := b(m)+H_2m
    equals the E40 closed-form rearrangement 3/2 - 1/(4m) + H_2m - H_2m^(2). Pins the
    decomposition identity against the exact b(m) (E39/E40)."""
    for m, b in _BM_EXACT.items():
        h2m = sum((Fraction(1, j) for j in range(1, 2 * m + 1)), Fraction(0))
        boundary = b + h2m
        assert boundary == Fraction(3, 2) - Fraction(1, 4 * m) + h2m - _H2(2 * m)
        # and b = -H_2m + B(m) is a tautology check on the split
        assert b == -h2m + boundary


# --- E43: the EXACT per-position hit law -> the value law as one explicit sum ----
# Pin the intercept mechanism (data/gt_hit_formula.py, EXPERIMENTS E43). The realized
# hit at a position whose run's last card is in block ell, with A undealt on the
# continuation side and B on the opposite side, is `hit_probability(m,ell,A,B)` — exact
# vs enumeration, bulk-limit 1/(2m-ell). The pure-continuation strategy (guess w1 every
# step) equals E_opt exactly, so E_opt = sum_t E[hit], and the intercept reduces to
# b(m) = -1 + 1/(2m) + S_excess(m), S_excess(m) = 5/2 - 3/(4m) - H_2m^(2).


def test_hit_probability_exact_by_enumeration():
    """The per-position hit law equals the brute-force shuffle probability for EVERY
    (prefix, parse, direction) group — ascending AND descending. A single mismatch
    would break the value-law reduction."""
    from collections import defaultdict
    from itertools import product

    for m, n in [(2, 6), (3, 5)]:
        lanes = 2 * m
        grp = defaultdict(lambda: [0, 0])
        meta = {}
        for labels in product(range(lanes), repeat=n):
            out = _output_from_labels(labels)
            pos = {c: i for i, c in enumerate(out)}
            for t in range(1, n):
                v = out[t - 1]; ell = labels[v - 1]
                undealt = [c for c in range(1, n + 1) if pos[c] >= t]
                above = [c for c in undealt if c > v]
                below = [c for c in undealt if c < v]
                if ell % 2 == 0:
                    if not above:
                        continue
                    w1, A, B, dirn = min(above), len(above), len(below), 0
                else:
                    if not below:
                        continue
                    w1, A, B, dirn = max(below), len(below), len(above), 1
                key = (tuple(out[:t]), tuple(labels[c - 1] for c in out[:t]), dirn)
                grp[key][0] += 1
                grp[key][1] += 1 if out[t] == w1 else 0
                meta[key] = (ell, A, B)
        for key, (c, h) in grp.items():
            ell, A, B = meta[key]
            assert Fraction(h, c) == hit_probability(m, ell, A, B), (m, key)
        assert len(grp) > 100, (m, len(grp))


def test_hit_probability_bulk_limit_is_block_rate():
    """The d=0 term is exactly 1 for all A,B, so hit_probability -> 1/(2m-ell) as the
    undealt supply grows — the E41 Lemma bulk rate that sets the value-law slope."""
    for m in (2, 3, 4):
        for ell in range(2 * m - 1):
            assert hit_probability(m, ell, 200, 200) - Fraction(1, 2 * m - ell) < Fraction(1, 10**6)
            # and it is >= the bulk rate at finite supply (finite-size EXCESS >= 0)
            assert hit_probability(m, ell, 5, 5) >= Fraction(1, 2 * m - ell)


def test_continuation_strategy_equals_e_opt_exactly():
    """The pure-continuation strategy (guess w1 = smallest undealt above v on an
    ascending run / largest below on descending; first guess = value 1) is OPTIMAL: its
    exact realized-hit expectation equals E_opt at every (n,m) — so the value law is
    exactly the per-position hit law summed. (An independent re-confirmation of E35.)"""
    from itertools import product

    for m, n in [(2, 5), (3, 4)]:
        lanes = 2 * m
        hits = 0
        for labels in product(range(lanes), repeat=n):
            out = _output_from_labels(labels)
            remaining = set(range(1, n + 1))
            for t in range(n):
                if t == 0:
                    guess = 1
                else:
                    v = out[t - 1]
                    asc = (t == 1) or (out[t - 1] > out[t - 2])
                    above = [c for c in remaining if c > v]
                    below = [c for c in remaining if c < v]
                    if asc:
                        guess = min(above) if above else (max(below) if below else v)
                    else:
                        guess = max(below) if below else (min(above) if above else v)
                if guess == out[t]:
                    hits += 1
                remaining.discard(out[t])
        v_cont = Fraction(hits, lanes ** n)
        e_opt, _ = exact_e_dp_rational(n, m)
        assert v_cont == e_opt, (m, n, v_cont, e_opt)


def test_intercept_reduction_to_s_excess():
    """The clean intercept split b(m) = -1 + 1/(2m) + S_excess(m), with the last mile in
    closed form S_excess(m) = 5/2 - 3/(4m) - H_2m^(2) (matching E40's b(m))."""
    for m, b in _BM_EXACT.items():
        s_excess = Fraction(5, 2) - Fraction(3, 4 * m) - _H2(2 * m)
        assert b == -1 + Fraction(1, 2 * m) + s_excess
        assert b == Fraction(3, 2) - Fraction(1, 4 * m) - _H2(2 * m)
