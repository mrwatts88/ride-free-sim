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

from fractions import Fraction

from ridefree.guessing_theorem import (
    build_perms,
    exact_e,
    exact_e_from_perms,
    mc_e,
    total_prob,
)

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
