"""Follow-up A (E35): pin the O(1) correction b(m).

The value-test (gt_value_mc.py) established E(n,m) = (H_2m/2m)*n + [small O(1)],
but delta = E - (H_2m/2m)*n was MC-noise-limited (~0.1) at large n. This runs
MANY trials at fixed n to resolve delta to se ~ 0.02, revealing whether
delta -> a constant b(m) (a refined conjecture E = c(m)*n + b(m) + o(1), sharper
than Clay's "~") or -> 0.

m=1 is the provably-zero control: Clay proved E(n,1) = 3n/4 exactly, so
delta(n,1) must measure to 0 -- it calibrates the noise floor.

Low-variance estimator: predicted = sum_t max_c P(next=c | prefix) (unbiased for
E(n,m)). Run under PyPy:
  PYTHONPATH=/Users/mattwatts/code/ride-free-sim/src \
  /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_bm_precision.py 20000
(~10-15 min at 20000 trials; lower it to 10000 for a quicker se~0.03 pass.)
"""

import math
import random
import sys

from ridefree.posterior import ShelfPosterior
from ridefree.shuffle import ShelfShuffle


def H(k: int) -> float:
    return math.fsum(1.0 / j for j in range(1, k + 1))


def cslope(m: int) -> float:
    return H(2 * m) / (2 * m)


def mc(n: int, m: int, trials: int, seed: int):
    rng = random.Random(seed)
    stack = list(range(1, n + 1))
    shuf = ShelfShuffle(shelves=m, passes=1)
    s = s2 = 0.0
    for _ in range(trials):
        deck = shuf.permute(stack, rng)
        post = ShelfPosterior(m, stack)
        pred = 0.0
        for c in deck:
            probs = post.next_probs()
            pred += max(probs.values())  # optimal per-step hit prob
            post.observe(c)
        s += pred
        s2 += pred * pred
    mp = s / trials
    v = (s2 - trials * mp * mp) / (trials - 1)
    return mp, math.sqrt(v / trials)


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    base = 24_200_000_000  # reserved seed block for Follow-up A
    print(f"trials={trials}   delta(n,m) = E - (H_2m/2m)*n   (want se ~ 0.02)")
    for m in (1, 2, 3, 5, 10):
        c = cslope(m)
        print(f"\n m={m}  c(m)=H_2m/2m={c:.5f}")
        for n in (52, 104):
            mp, se = mc(n, m, trials, base + n * 1000 + m)
            d = mp - c * n
            flag = "  <-- provably 0 (control)" if m == 1 else ""
            print(f"  n={n:3d}: E={mp:.4f}+-{se:.4f}  delta={d:+.4f}+-{se:.4f}{flag}")


if __name__ == "__main__":
    main()
