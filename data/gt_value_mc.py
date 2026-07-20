"""Scaled test of Clay's Conjecture 3 VALUE formula F_G(n,m) ~ (n/2m) H_{2m} — E35.

Research probe for experiment **E35** (docs/EXPERIMENTS.md, docs/GUESSING_THEOREM.md).
Low-variance estimator (`ridefree.guessing_theorem.mc_e`):
E(n,m) = E[ sum_t max_c P(next=c | prefix) ] via the float ShelfPosterior (the
`predicted` accumulator). Realized hits (DFH-optimal guesser) are tracked too as
a higher-variance cross-check / calibration.

Gates:
  (G1) n=9 vs the exact rational values from the enumeration probe.
  (G2) n=52 vs Clay's own table (DFH sample: 39, 27, 17.6, 9.3, 6.2, 4.7 at
       m = 1,2,4,10,20,40) and his formula (39, 27.08, 17.67, 9.35, 5.56, 3.23).

Then scan n to characterize the correction  delta(n,m) = E(n,m) - (H_2m/2m) n
(constant? sqrt(n)? log n?).
"""

import math
import sys
import time

from ridefree.guessing_theorem import mc_e


def H(k: int) -> float:
    return math.fsum(1.0 / j for j in range(1, k + 1))


def cslope(m: int) -> float:
    return H(2 * m) / (2 * m)


# exact E(9,m) from the enumeration probe (gt_exact.py rationals -> float), m=1..10
EXACT_N9 = {
    1: 6.750000, 2: 4.650116, 3: 3.774545, 4: 3.391120, 5: 3.198116,
    6: 3.088931, 7: 3.021580, 8: 2.977247, 9: 2.946568, 10: 2.924480,
}


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    base = 24_000_000_000

    print(f"trials={trials}\n")
    print("== G1: n=9 MC vs EXACT (predicted should match to within se) ==")
    for m in (1, 2, 3, 5, 10):
        t0 = time.time()
        mp, sep, mh, seh = mc_e(9, m, trials, base + 900 + m)
        z = (mp - EXACT_N9[m]) / sep
        print(
            f"  m={m:2d}: pred={mp:.4f}±{sep:.4f} exact={EXACT_N9[m]:.4f} "
            f"z={z:+.2f} | hits={mh:.4f}±{seh:.4f}  ({time.time()-t0:.1f}s)"
        )

    print("\n== G2: n=52 vs Clay's table  (DFH sample / formula) ==")
    clay_sample = {1: 39, 2: 27, 4: 17.6, 10: 9.3, 20: 6.2, 40: 4.7}
    for m in (1, 2, 4, 10, 20, 40):
        t0 = time.time()
        mp, sep, mh, seh = mc_e(52, m, trials, base + 5200 + m)
        formula = cslope(m) * 52
        print(
            f"  m={m:2d}: pred={mp:.3f}±{sep:.3f}  DFHsample={clay_sample[m]}  "
            f"formula(n/2m)H2m={formula:.3f}  delta={mp-formula:+.3f}  "
            f"hits={mh:.3f} ({time.time()-t0:.1f}s)"
        )

    print("\n== correction scan: delta(n,m)=E-(H2m/2m)n ; is it const / sqrt(n) / log n? ==")
    ns = [26, 52, 104, 208]
    for m in (1, 2, 3, 5, 10):
        print(f"  m={m}  c(m)=H2m/2m={cslope(m):.5f}")
        prev = None
        for n in ns:
            tr = max(200, int(trials * (52.0 / n) ** 2))  # ~constant compute/cell
            t0 = time.time()
            mp, sep, mh, seh = mc_e(n, m, tr, base + n * 100 + m)
            c = cslope(m)
            delta = mp - c * n
            impl = "" if prev is None else f" implied-slope={ (mp-prev[1])/(n-prev[0]):.4f}"
            print(
                f"    n={n:3d}: E={mp:.3f}±{sep:.3f} delta={delta:+.3f} "
                f"d/sqrt(n)={delta/math.sqrt(n):+.4f} d/ln(n)={delta/math.log(n):+.4f}"
                f"{impl}  ({tr}tr {time.time()-t0:.1f}s)"
            )
            prev = (n, mp)


if __name__ == "__main__":
    main()
