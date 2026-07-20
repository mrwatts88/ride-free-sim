"""Follow-up B (E35): where does DFH's strategy G stop being optimal?

Our exact enumeration showed gap E_opt - E_G = 0 for ALL n<=9, m<=10. Clay's
Conjecture 3 only claims G optimal when "n/m is not too small". LEAD from the
value-test: at (52,40) the optimal value ~4.98 exceeds DFH's sampled 4.7, hinting
G is suboptimal in the small-n/2m regime.

Measure the gap DIRECTLY via common random numbers (both guessers see the SAME
shuffled decks, so the per-deck difference is low-variance). A gap significantly
> 0 locates where G first loses optimality -- making Clay's hedge precise.

Run under PyPy:
  PYTHONPATH=/Users/mattwatts/code/ride-free-sim/src \
  /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_strategy_gap.py 5000
"""

import math
import random
import sys

from ridefree.forensics import ShelfGuesser
from ridefree.posterior import PosteriorGuesser
from ridefree.shuffle import ShelfShuffle


def gap(n: int, m: int, trials: int, seed: int):
    rng = random.Random(seed)
    stack = list(range(1, n + 1))
    shuf = ShelfShuffle(shelves=m, passes=1)
    sopt_pred = sopt_hit = sg_hit = 0.0
    sdiff = sdiff2 = 0.0
    for _ in range(trials):
        deck = shuf.permute(stack, rng)  # CRN: both strategies see this deck
        pg = PosteriorGuesser(m, stack)  # Bayes-optimal (argmax of exact posterior)
        ho = 0
        for c in deck:
            if pg.guess() == c:
                ho += 1
            pg.observe(c)
        gg = ShelfGuesser(n)  # DFH's strategy G (m-independent)
        hg = 0
        for c in deck:
            if gg.guess() == c:
                hg += 1
            gg.observe(c)
        sopt_pred += pg.predicted
        sopt_hit += ho
        sg_hit += hg
        d = ho - hg
        sdiff += d
        sdiff2 += d * d
    mo_pred = sopt_pred / trials
    md = sdiff / trials
    vd = (sdiff2 - trials * md * md) / (trials - 1)
    return mo_pred, sopt_hit / trials, sg_hit / trials, md, math.sqrt(vd / trials)


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    base = 24_100_000_000  # reserved seed block for Follow-up B
    print(f"trials={trials}  gap = E_opt - E_G (CRN; se on the realized diff)")
    for n in (52, 104):
        print(f"\n n={n}")
        print(f"  {'m':>3} {'opt(pred)':>10} {'opt(hit)':>9} {'G(hit)':>8} "
              f"{'gap':>8} {'se':>7} {'z':>6}")
        for m in (5, 10, 13, 20, 26, 40):
            mo_pred, mo, mg, md, sed = gap(n, m, trials, base + n * 1000 + m)
            z = md / sed if sed > 0 else 0.0
            print(f"  {m:>3} {mo_pred:>10.3f} {mo:>9.3f} {mg:>8.3f} "
                  f"{md:>+8.3f} {sed:>7.3f} {z:>+6.1f}")


if __name__ == "__main__":
    main()
