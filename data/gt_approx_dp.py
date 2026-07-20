"""The polynomial APPROXIMATE guessing-value DP — fast deck-scale E_opt for LARGE m
via the run-length MULTISET closure (E38, build b).

Research probe for experiment **E38** (docs/EXPERIMENTS.md, docs/GUESSING_THEOREM.md).
E37's `exact_e_dp` is exact but Θ(n^{2m}) — dead for m ≥ 5, exactly the DFH
real-machine regime (m=10). Build (b) coarsens E37's exact state σ = (dir, rank,
ordered run-COMPOSITION) to keep only the run-length MULTISET (order of the runs
discarded): σ̂ = (dir, rank, sorted-run-comp). `guessing_theorem.approx_e_dp` is
that DP, and this file MEASURES its bias — the whole point — against E37's exact
grid and the E35 Monte-Carlo.

The pivot this probe records (the E38 finding): the run *count* alone (#descents,
the literal reading of "collapse the composition to its count") FAILS at deck
scale — it is bounded ~2m while run lengths grow ~n/2m, so its per-step error
compounds into a WRONG asymptotic slope (E_opt(52,5) off by −4.3; a near-exact
n≤12 gate that collapses by n=52). The run-length *distribution* (the multiset) is
what the posterior depends on; keeping it recovers the deck-scale value.

Headline findings:
  * #descents (run count) DP: catastrophic at deck scale (§ contrast) — the
    cautionary result that motivates the multiset.
  * MULTISET DP: EXACT at m=1; small BOUNDED bias for m ≥ 2 that is NON-MONOTONE
    in n (rises then falls) and SHRINKS with m (strong mixing). Deck scale:
    E_opt(52,5) within ~2 MC-se, E_opt(52,10) within ~0.08 (0.8%) — vs #descents'
    −2 to −4. Fast + deterministic where `exact_e_dp` is Θ(n^{2m})-dead.
  * The multiset is APPROXIMATELY (not exactly) sufficient — E36's ORDERED
    composition is exactly sufficient; the multiset's within-bin hit gap is small
    and shrinks with m. So this is an honest approximation with a measured error.
  * `max_run` caps run lengths in the key for very large m (m=10 needs it): the
    value is unchanged to 4 dp from max_run=2 upward — the long-run tail barely
    moves the optimal hit — while the state count drops to ~9k (n=52, m=10).

    uv run python data/gt_approx_dp.py [n_deck] [m1,m2,...]   # default 52  1,2,3,5,10
    # PyPy (~4x); the exact-reference + m=5 full-multiset columns are the heavy part:
    # PYTHONPATH=src ~/.local/bin/pypy3.11 -u data/gt_approx_dp.py 52 1,2,3,5,10
"""

import math
import sys
import time
from collections import defaultdict
from fractions import Fraction

from ridefree.guessing_theorem import approx_e_dp, exact_e, exact_e_dp, mc_e
from ridefree.posterior import ShelfPosterior

# Guessing-theorem seed space (24.x); NOT shoe-sim seeds. E38 deck-scale MC gate.
_SEED_BASE = 24_070_000_000
_MAX_STATES = 1_200_000  # exact-reference per-column cap (3rd CLI arg, in millions)

_ADP: dict = {}  # (n, m) -> (E_approx, n_states, seconds)
_EDP: dict = {}  # (n, m) -> (E_exact,  n_states, seconds)  [feasible cells only]


def _cap(m: int) -> int | None:
    """Run-length cap for the approx DP: full multiset for m ≤ 5 (feasible to
    n=52), capped at 3 for larger m (converged — see the max_run study)."""
    return None if m <= 5 else 3


def adp(n: int, m: int):
    """Cached `approx_e_dp` (with the per-m run-length cap) and wall-clock."""
    key = (n, m)
    if key not in _ADP:
        t0 = time.time()
        e, ns = approx_e_dp(n, m, max_run=_cap(m))
        _ADP[key] = (e, ns, time.time() - t0)
    return _ADP[key]


def edp(n: int, m: int):
    """Cached exact `exact_e_dp`, or None if predicted beyond the state cap."""
    key = (n, m)
    if key in _EDP:
        return _EDP[key]
    smaller = [k[0] for k in _EDP if k[1] == m and k[0] < n and _EDP[k] is not None]
    if smaller:
        n0 = max(smaller)
        if _EDP[(n0, m)][1] * (n / n0) ** (2 * m) > _MAX_STATES:
            _EDP[key] = None
            return None
    t0 = time.time()
    e, ns = exact_e_dp(n, m)
    _EDP[key] = (e, ns, time.time() - t0)
    return _EDP[key]


def ndesc_e_dp(n: int, m: int) -> float:
    """The REJECTED closure, for the contrast: E37's transition but keyed by the
    run COUNT (#descents) only — the literal 'collapse composition to its count'.
    Mode representative per (dir, rank, #descents). Fast (~O(n³) states)."""
    root = ShelfPosterior(m, list(range(1, n + 1)))
    level = {(True, 0, 0): (1.0, root, ())}
    e_opt = 0.0
    for _t in range(n):
        nm: dict = defaultdict(float)
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
                child = (asc, j, len(crc) - 1)  # key by #descents ONLY
                em = mass * pc
                nm[child] += em
                b = nb.get(child)
                if b is None or em > b[0]:
                    nb[child] = (em, post, card, crc)
        nl = {}
        for child, tot in nm.items():
            _, pp, card, crc = nb[child]
            rep = pp.copy()
            rep.observe(card)
            nl[child] = (tot, rep, crc)
        level = nl
    return e_opt


def clay_slope(m: int) -> Fraction:
    """Clay's asymptotic per-card rate c(m) = H_{2m} / (2m) (exact at m=1: 3/4)."""
    h = sum(Fraction(1, k) for k in range(1, 2 * m + 1))
    return h / (2 * m)


def gate_small_grid() -> None:
    """vs the O(n·n!) enumeration on n≤7: m=1 EXACT (composition irrelevant to the
    law), and the multiset columns stay small (a bound, not a zero-gap claim)."""
    print("== GATE 1: multiset DP vs exact n! enumeration (n≤7) ==")
    worst_m1 = worst_any = 0.0
    for n in range(1, 8):
        for m in range(1, 11):
            e_ref = float(exact_e(n, m)[0])
            e_apx, _, _ = adp(n, m)
            d = abs(e_apx - e_ref)
            worst_any = max(worst_any, d)
            if m == 1:
                worst_m1 = max(worst_m1, d)
    assert worst_m1 < 1e-9, worst_m1
    assert worst_any < 0.05, worst_any
    print(f"   m=1 EXACT (worst |Δ| = {worst_m1:.2e}); "
          f"worst |Δ| over all m ≤ 10 = {worst_any:.4f}   ✓")


def contrast_ndesc_vs_multiset(m_list) -> None:
    """The E38 pivot, at deck scale: the run-COUNT closure fails; the run-length
    MULTISET closure works. Both keyed variants, same transition, vs MC."""
    print("\n== CONTRAST: #descents (count) DP vs multiset DP at n=52 ==")
    print("   (both = E37's transition; differ only in the dedup key)")
    for m in [m for m in m_list if m >= 3]:
        e_count = ndesc_e_dp(52, m)
        e_multi, ns, _ = adp(52, m)
        pred, se, _, _ = mc_e(52, m, 1500, seed=_SEED_BASE + 900 + m)
        print(f"   m={m:2d}: #descents={e_count:7.4f} (bias {e_count-pred:+.3f}) | "
              f"MULTISET={e_multi:7.4f} (bias {e_multi-pred:+.3f}, {ns} st) | "
              f"MC {pred:.4f}±{se:.4f}")


def gate_deck_scale_mc(m_list, trials) -> None:
    """The deck-scale ERROR BAR: multiset DP vs the independent low-variance MC
    (`mc_e`, unbiased for E_opt) at n=52 — the calibration where no exact value
    exists (m ≥ 3)."""
    print(f"\n== GATE 2: multiset DP vs independent MC at n=52  ({trials} trials) ==")
    for m in m_list:
        e, ns, dt = adp(52, m)
        pred, se, _, _ = mc_e(52, m, trials, seed=_SEED_BASE + m)
        z = (e - pred) / se if se else 0.0
        cap = _cap(m)
        tag = "" if cap is None else f", max_run={cap}"
        extra = "  (== 3·52/4 exactly)" if m == 1 and abs(e - 39.0) < 1e-9 else ""
        print(f"   n=52 m={m:2d}: E_apx={e:9.5f} ({ns:>6d} st{tag}, {dt:5.1f}s) | "
              f"MC {pred:.4f}±{se:.4f}  bias={e-pred:+.4f} (z={z:+.1f}){extra}")


def bias_grid(n_deck, m_list) -> None:
    """The deliverable table: multiset bias δ̃ = Ẽ_opt − E_opt vs the EXACT DP,
    across n, wherever the exact reference is feasible. Shows m=1 exact, the small
    bounded NON-MONOTONE-in-n bias for m ≥ 2, and its shrink with m."""
    print("\n== multiset bias  δ̃(n,m) = Ẽ_opt − E_opt  (vs exact_e_dp) ==")
    ladder = sorted({n for n in [7, 9, 12, 16, 20, 26, 36, n_deck] if n <= n_deck})
    for m in m_list:
        print(f"\n  m={m}:")
        for n in ladder:
            e_apx, ns_a, _ = adp(n, m)
            ref = edp(n, m)
            if ref is None:
                print(f"    n={n:3d}: Ẽ_opt={e_apx:9.5f} ({ns_a:>6d} st)   "
                      f"exact beyond cap — see MC gate")
                continue
            e_ex, ns_e, _ = ref
            print(f"    n={n:3d}: Ẽ_opt={e_apx:9.5f} ({ns_a:>6d} st)  "
                  f"E_opt={e_ex:9.5f} ({ns_e:>8d} st)  δ̃={e_apx-e_ex:+.5f}")


def deliverable(n_deck, m_list) -> None:
    """The fast deck-scale values with their measured error bars, and the Clay
    c(m)·n comparison — the numbers E35 had only as MC and E37 (exact) cannot
    reach for large m."""
    print(f"\n== DELIVERABLE: fast E_opt(n={n_deck}, m) with error bar ==")
    for m in m_list:
        e, ns, dt = adp(n_deck, m)
        c = float(clay_slope(m))
        ref = edp(n_deck, m)
        if ref is not None:
            bar = f"exact δ̃={e-ref[0]:+.4f} (E_opt={ref[0]:.4f})"
        else:
            bar = "large-m: MC-calibrated (Gate 2)"
        print(f"  m={m:2d}: Ẽ_opt={e:9.5f}  ({ns:>6d} st, {dt:5.1f}s)  "
              f"c(m)·n={c*n_deck:8.4f}  δ=Ẽ−c·n={e-c*n_deck:+.4f}  [{bar}]")


def main():
    global _MAX_STATES
    n_deck = int(sys.argv[1]) if len(sys.argv) > 1 else 52
    m_list = (
        [int(x) for x in sys.argv[2].split(",")]
        if len(sys.argv) > 2 else [1, 2, 3, 5, 10]
    )
    if len(sys.argv) > 3:
        _MAX_STATES = int(float(sys.argv[3]) * 1_000_000)
    trials = 2000
    print("approx_e_dp: the run-length-MULTISET coarsened DP (E38, build b)")
    print(f"n_deck={n_deck}  m_list={m_list}\n")

    gate_small_grid()
    contrast_ndesc_vs_multiset(m_list)
    gate_deck_scale_mc([m for m in m_list if m in (1, 5, 10)] or [10], trials)
    bias_grid(n_deck, m_list)
    deliverable(n_deck, m_list)


if __name__ == "__main__":
    main()
