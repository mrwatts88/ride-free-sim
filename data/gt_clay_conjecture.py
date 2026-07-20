"""Test Clay's Conjecture 3 against our EXACT E(n,m) — experiment **E35**.

Conjecture 3 (Clay 2025, arXiv:2507.10294):  F_G(n,m) ~ (n/2m) * H_{2m},
valid "when n/m is not too small"; and DFH's strategy G is optimal
"in a high-probability case".

Exact E_opt(n,m) (= E_G — the gap is 0, re-asserted here) comes from
`ridefree.guessing_theorem`; this probe compares it to Clay's asymptotic slope
to expose (docs/GUESSING_THEOREM.md):
  * Clay's formula is EXACT at m=1 (= 3n/4) and only an asymptotic LEADING term
    for m>=2 (our exact values approach the slope H_{2m}/(2m) from below);
  * the finite-n correction E_opt(n,m) - (n/2m)H_{2m};
  * that the VALUE formula's small-n/2m failure regime is NOT the STRATEGY
    optimality regime — the gap stays 0 even where the value formula is far off,
    so the two halves of Conjecture 3 have different regimes.

    uv run python data/gt_clay_conjecture.py
"""

from fractions import Fraction

from ridefree.guessing_theorem import build_perms, exact_e_from_perms


def H(k: int) -> Fraction:
    return sum(Fraction(1, j) for j in range(1, k + 1))


def main():
    n_max = 8
    m_list = list(range(1, 11))

    # asymptotic slope predicted by Conjecture 3
    print("== Conjecture-3 asymptotic slope  c(m) = H_{2m}/(2m) ==")
    for m in m_list:
        c = H(2 * m) / (2 * m)
        print(f"  m={m:2d}: H_2m/(2m) = {c} = {float(c):.5f}")

    e_table = {}
    print("\n== exact E_opt(n,m)  vs  Clay (n/2m)H_2m  [value = exact | clay | diff] ==")
    for n in range(2, n_max + 1):
        perms = build_perms(n)
        row = []
        for m in m_list:
            e_opt, e_g = exact_e_from_perms(n, m, perms)
            e_table[(n, m)] = e_opt
            assert e_opt == e_g, (n, m, e_opt, e_g)  # strategy G optimal (exact)
            clay = Fraction(n, 2 * m) * H(2 * m)
            diff = float(e_opt - clay)
            row.append(f"{float(e_opt):.3f}|{float(clay):.3f}|{diff:+.3f}")
        print(f"  n={n}: " + "   ".join(f"m{m}:{c}" for m, c in zip(m_list, row)))

    print("\n== m=1: is Clay's formula EXACT?  E_opt(n,1) - 3n/4 ==")
    for n in range(2, n_max + 1):
        e = e_table[(n, 1)]
        print(f"  n={n}: E={e}  3n/4={Fraction(3*n,4)}  diff={e - Fraction(3*n,4)}")

    print("\n== ratio n/2m at the grid edges (Clay's formula needs this 'not small') ==")
    for m in m_list:
        print(f"  m={m:2d}: n/2m at n={n_max} = {n_max/(2*m):.3f}")

    print(
        "\nNOTE: strategy G stays EXACTLY optimal (gap 0, asserted above) at every "
        "(n,m) here, including tiny n/2m — while the VALUE formula (n/2m)H_2m is "
        "only a large-n/2m asymptotic. The two halves of Conjecture 3 have "
        "different regimes."
    )


if __name__ == "__main__":
    main()
