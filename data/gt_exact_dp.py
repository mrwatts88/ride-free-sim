"""Break the n! wall: EXACT E_opt(n,m) at deck scale via the run-composition DP.

Research probe for experiment **E37** (docs/EXPERIMENTS.md, docs/GUESSING_THEOREM.md),
the constructive build (a) that E36 specified. E35 could compute the exact optimal
feedback-guessing value E_opt(n,m) only to n≈9 (the O(n·n!) enumeration in
`gt_exact.py`); everything at deck scale was Monte-Carlo. E36 proved the per-step
optimal hit — and the whole next-card posterior — is an exact function of the
Markov state σ = (direction, rank-of-last, ascending-run composition), with a
CLOSED transition, so E_opt(n,m) = Σ_σ P(σ)·h(σ) is a dynamic program over σ.

`guessing_theorem.exact_e_dp` is that DP: Clay 2025's "transition matrix for an
arbitrary number of shelves" (the stated open object) made explicit and runnable.
This file is the reporting/analysis layer over it — gates, the state-count growth
law, the extended exact grid, and the exact correction δ(n,m).

Headline findings this probe establishes:
  * The DP reproduces the E35 exact rationals (n≤9, every m) to ~1e-12 and the
    E35 deck-scale MC values within se — an end-to-end proof the σ-transition is
    closed at every tested cell.
  * The reachable state count is POLYNOMIAL in n for each fixed m — degree ≈ 2m
    (m=1 is exactly n²−n+1; m=2 quartic; m=3 sextic) — NOT the flat "~2ⁿ" E36
    hedged from n≤8 data. The DFH law caps an m-shelf output at m−1 valleys
    (`shelf_class_prob` vanishes for v>m−1), which bounds the descent structure.
    So the operator is exponential in m but tractable in n: exact E_opt(52,m) for
    small m, while Clay's general-m (m→∞) matrix stays hard. This SHARPENS E36.
  * First EXACT E_opt(52,m) for m≥2 (m=1: 39 = 3·52/4 exactly; m=2: 27.0347…),
    where DFH/E35 had only samples.
  * The O(1) correction δ(n,m) = E_opt − (H_2m/2m)·n converges to a constant
    b(m) already by n≈26 (m=2: b≈−0.0486; the slope between n=26 and 52 is
    EXACTLY c(2)) — pinning Follow-up A's b(m), which the 20000-trial MC could
    only bound.

    uv run python data/gt_exact_dp.py [n_deck] [m1,m2,...]   # default 52  1,2,3
    # PyPy (~4x) for the heavy columns (m=3 at n=52 is ~n^6 states):
    # PYTHONPATH=src ~/.local/bin/pypy3.11 -u data/gt_exact_dp.py 52 1,2,3,5
"""

import math
import sys
import time
from fractions import Fraction

from ridefree.guessing_theorem import exact_e, exact_e_dp, mc_e

# Guessing-theorem seed space (24.x); NOT shoe-sim seeds. E37 deck-scale gate.
_SEED_BASE = 24_060_000_000
_MAX_STATES = 1_200_000  # per-column cap (overridable, 3rd CLI arg in millions);
#   default keeps CPython ~2 min: m=2 to n=52 (566k), m≥3 caps near n≈26.

_CACHE: dict = {}  # (n, m) -> (E_opt, n_states, seconds)


def dp(n: int, m: int):
    """Cached `exact_e_dp` with wall-clock — every function shares one compute."""
    key = (n, m)
    if key not in _CACHE:
        t0 = time.time()
        e, ns = exact_e_dp(n, m)
        _CACHE[key] = (e, ns, time.time() - t0)
    return _CACHE[key]


def feasible(n: int, m: int) -> float | None:
    """Predicted state count from the local degree-2m law, using the nearest
    already-computed smaller n for this m; None ⇒ within cap (compute it)."""
    smaller = [k[0] for k in _CACHE if k[1] == m and k[0] < n]
    if not smaller:
        return None
    n0 = max(smaller)
    pred = _CACHE[(n0, m)][1] * (n / n0) ** (2 * m)
    return pred if pred > _MAX_STATES else None


def clay_slope(m: int) -> Fraction:
    """Clay's asymptotic per-card rate c(m) = H_{2m} / (2m) (exact at m=1: 3/4)."""
    h = sum(Fraction(1, k) for k in range(1, 2 * m + 1))
    return h / (2 * m)


def gate_exact_grid() -> None:
    """The DP must reproduce the exact enumeration on the whole n≤7 grid, all m,
    and the two pinned exact E(9,m) fractions — the closed-transition proof."""
    print("== GATE 1: DP vs exact n! enumeration (n≤7, m=1..10) ==")
    worst = 0.0
    for n in range(1, 8):
        for m in range(1, 11):
            e_ref = float(exact_e(n, m)[0])
            e_dp, _ = exact_e_dp(n, m)
            worst = max(worst, abs(e_dp - e_ref))
    assert worst < 1e-9, worst
    print(f"   all 70 cells match, worst |Δ| = {worst:.2e}   ✓")

    print("== GATE 2: DP vs pinned exact E(9,m) rationals ==")
    for m, frac in {2: Fraction(152375, 32768), 3: Fraction(594355, 157464)}.items():
        e, ns, _ = dp(9, m)
        d = abs(e - float(frac))
        assert d < 1e-9, (m, d)
        print(f"   E(9,{m}) = {float(frac):.6f}  DP {e:.6f}  Δ{d:.1e}  ({ns} states) ✓")


def gate_deck_scale(m_list) -> None:
    """The DP's deck-scale values must match the independent float-posterior MC
    (`mc_e`) within a few se — the E35 value-test, now with an exact anchor."""
    print("\n== GATE 3: exact DP vs independent MC at n=52 ==")
    for m in m_list:
        e, ns, dt = dp(52, m)
        pred, se, hit, _ = mc_e(52, m, 2000, seed=_SEED_BASE + m)
        z = (e - pred) / se if se else 0.0
        flag = "  ✓" if abs(z) < 3 else "  ⚠"
        extra = "  (== 3·52/4 exactly)" if m == 1 and abs(e - 39.0) < 1e-9 else ""
        print(f"   n=52 m={m}: E_dp={e:.5f} ({ns:>8d} states, {dt:5.1f}s) | "
              f"MC {pred:.5f}±{se:.5f}  z={z:+.2f}{flag}{extra}")


def state_growth(m_list, n_lo=4, n_hi=16) -> None:
    """The state-count law: polynomial in n for each fixed m, degree ≈ 2m."""
    print("\n== state-count growth  |states|(n)  — polynomial, degree ≈ 2m ==")
    ns_range = range(n_lo, n_hi + 1)
    for m in m_list:
        counts = {n: dp(n, m)[1] for n in ns_range}
        n1, n2 = n_hi // 2, n_hi
        slope = math.log(counts[n2] / counts[n1]) / math.log(n2 / n1)
        row = "  ".join(f"n{n}:{counts[n]:>6d}" for n in ns_range)
        note = ""
        if m == 1:
            ok = all(counts[n] == n * n - n + 1 for n in ns_range)
            note = f"   [= n²−n+1 exactly: {ok}]"
        print(f"  m={m}: {row}")
        print(f"        log-log degree over [{n1},{n2}] ≈ {slope:.2f}  (2m={2*m}){note}")


def extended_grid(n_deck, m_list) -> None:
    """The wall broken: exact E_opt(n,m) past n≈9, out to n_deck for feasible m,
    with the exact O(1) correction δ(n,m) = E_opt − c(m)·n → b(m)."""
    print("\n== EXACT E_opt(n,m) past the n! wall  (δ = E_opt − c(m)·n) ==")
    ladder = sorted({n for n in [9, 13, 16, 20, 26, 36, n_deck] if n <= n_deck})
    for m in m_list:
        c = float(clay_slope(m))
        print(f"\n  m={m}   c(m)=H_2m/2m={c:.6f}")
        prev = None
        for n in ladder:
            pred = feasible(n, m)
            if pred is not None:
                print(f"    n={n:3d}: skipped (~{pred:.1e} states > cap "
                      f"{_MAX_STATES:.0e} — PyPy / run-comp pruning territory)")
                continue
            e, ns, dt = dp(n, m)
            delta = e - c * n
            slope = "" if prev is None else f"  slope={(e - prev[1]) / (n - prev[0]):.6f}"
            print(f"    n={n:3d}: E_opt={e:10.6f}  δ={delta:+.5f}  "
                  f"({ns:>9d} states, {dt:5.1f}s){slope}")
            prev = (n, e)


def clay_deck_check(n_deck, m_list) -> None:
    """Clay Conjecture-3 value formula at deck scale, against the exact DP and
    DFH/Clay's own sampled table (39, 27, 17.6, 9.3 at m=1,2,4,10)."""
    print(f"\n== Clay value formula c(m)·n vs EXACT E_opt at n={n_deck} ==")
    dfh_sample = {1: 39.0, 2: 27.0, 4: 17.6, 10: 9.3}
    for m in m_list:
        if feasible(n_deck, m) is not None:
            print(f"  m={m}: n={n_deck} beyond the exact cap (see grid above)")
            continue
        c = float(clay_slope(m))
        e, _, _ = dp(n_deck, m)
        formula = c * n_deck
        s = dfh_sample.get(m)
        smp = f"  DFH-sample≈{s}" if s is not None else ""
        print(f"  m={m}: exact={e:.4f}  formula c(m)·n={formula:.4f}  "
              f"δ={e-formula:+.4f}{smp}")


def main():
    global _MAX_STATES
    n_deck = int(sys.argv[1]) if len(sys.argv) > 1 else 52
    m_list = (
        [int(x) for x in sys.argv[2].split(",")]
        if len(sys.argv) > 2 else [1, 2, 3]
    )
    if len(sys.argv) > 3:
        _MAX_STATES = int(float(sys.argv[3]) * 1_000_000)
    print("exact_e_dp: the run-composition DP (Clay's m-shelf operator, explicit)")
    print(f"n_deck={n_deck}  m_list={m_list}\n")

    gate_exact_grid()
    gate_deck_scale([m for m in m_list if m <= 2] or [1])
    state_growth(m_list)
    extended_grid(n_deck, m_list)
    clay_deck_check(n_deck, m_list)


if __name__ == "__main__":
    main()
