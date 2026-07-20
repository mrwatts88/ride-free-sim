"""Exact optimal feedback-guessing value E(n,m) for the DFH m-shelf shuffle.

Research probe for experiment **E35** (docs/EXPERIMENTS.md, docs/GUESSING_THEOREM.md):
is DFH's conjectured-optimal strategy G actually optimal for m>1, and what is the
exact expected reward? (Clay 2025 proved only the single-shelf m=1 case: 3n/4.)

Prints the exact rational E_opt(n,m) grid, the DFH strategy-G optimality gap
(E_opt - E_G, exactly 0 at every cell measured), the m=1 closed form
E(n,1)=3n/4, per-column fractions, and the first-difference slopes in n — the
exact evidence banked in E35.

The exact machinery (DFH Thm 3.1 class law + prefix-trie max-child mass) and the
independent Monte-Carlo cross-check (the float ShelfPosterior) both live in
`ridefree.guessing_theorem`; this file is the reporting/analysis layer over them.

    uv run python data/gt_exact.py [n_max]      # default n_max=9
"""

import sys

from ridefree.forensics import uniform_guessing_mean
from ridefree.guessing_theorem import (
    build_perms,
    exact_e_from_perms,
    mc_e,
    total_prob,
)


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    m_list = list(range(1, 11))

    # sanity: probabilities sum to 1
    print("== sanity: total output probability (must be 1) ==")
    for (n, m) in [(4, 1), (6, 3), (8, 10)]:
        print(f"  n={n} m={m}: sum P = {total_prob(n, m)}")

    print("\n== independent MC cross-check of exact E_opt (float ShelfPosterior) ==")
    for (n, m) in [(6, 3), (7, 5)]:
        e_opt, _ = exact_e_from_perms(n, m, build_perms(n))
        mp, sep, mh, seh = mc_e(n, m, 200_000, seed=42)
        print(
            f"  n={n} m={m}: exact E_opt={float(e_opt):.5f} | "
            f"MC predicted={mp:.5f}±{sep:.5f}  hit={mh:.5f}"
        )

    print("\n== exact E_opt(n,m) and the DFH optimality gap ==")
    print("rows = n, cols = m ; each cell: E_opt (gap = E_opt - E_DFH)")
    header = "  n |" + "".join(f"   m={m:<2d}        " for m in m_list)
    print(header)
    e_table = {}
    gap_table = {}
    for n in range(1, n_max + 1):
        perms = build_perms(n)
        cells = []
        for m in m_list:
            e_opt, e_dfh = exact_e_from_perms(n, m, perms)
            e_table[(n, m)] = e_opt
            gap = e_opt - e_dfh
            gap_table[(n, m)] = gap
            gflag = "0" if gap == 0 else f"+{float(gap):.4g}"
            cells.append(f"{float(e_opt):7.4f}({gflag:>6})")
        print(f"  {n:2d}|" + " ".join(cells))

    # reference curves
    print("\n== references ==")
    for n in range(1, n_max + 1):
        hn = uniform_guessing_mean(n)
        print(
            f"  n={n:2d}: H_n={hn:.4f}  3n/4={3*n/4:.4f}  (3n+1)/4={(3*n+1)/4:.4f}"
        )

    # m=1 exact fractions (Clay's proven case) — the exact closed form 3n/4
    print("\n== m=1 exact fractions (Clay proved reward 3n/4) ==")
    for n in range(1, n_max + 1):
        e = e_table[(n, 1)]
        print(
            f"  n={n:2d}: E_opt(n,1)={e}  = {float(e):.5f}   "
            f"4*E={4*e}   4*E-3n={4*e - 3*n}"
        )

    # exact fractions for a few columns — hunt a closed form in n
    for mcol in (2, 3, 4):
        print(f"\n== m={mcol} exact fractions E_opt(n,{mcol}) ==")
        for n in range(1, n_max + 1):
            e = e_table[(n, mcol)]
            print(f"  n={n:2d}: {e}  = {float(e):.6f}")

    # asymptotic per-card guessing rate estimate c(m) ~ E/n and tail slope
    print("\n== per-card rate E_opt(n,m)/n  and  tail slope (last diff) ==")
    for m in m_list:
        rate = float(e_table[(n_max, m)]) / n_max
        tail = float(e_table[(n_max, m)] - e_table[(n_max - 1, m)])
        print(f"  m={m:2d}: E/n(n={n_max})={rate:.4f}   last slope={tail:.4f}")

    # per-m: is E_opt(n,m) affine in n?  print first differences
    print("\n== first differences E_opt(n,m) - E_opt(n-1,m) (slope in n) ==")
    for m in m_list:
        diffs = [
            float(e_table[(n, m)] - e_table[(n - 1, m)])
            for n in range(2, n_max + 1)
        ]
        ds = " ".join(f"{d:6.4f}" for d in diffs)
        print(f"  m={m:2d}: {ds}")

    # whole gap summary
    any_gap = any(g != 0 for g in gap_table.values())
    print(f"\n== DFH optimality: any exact gap (E_opt > E_DFH) anywhere? {any_gap} ==")
    if any_gap:
        for (n, m), g in sorted(gap_table.items()):
            if g != 0:
                print(f"   GAP at n={n} m={m}: {g} = {float(g):.6f}")


if __name__ == "__main__":
    main()
