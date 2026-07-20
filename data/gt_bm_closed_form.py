"""The proof road, Phase 1(1b): the CLOSED FORM for the value-law intercept b(m).
Research probe for experiment **E40** (docs/EXPERIMENTS.md, docs/GUESSING_THEOREM.md).

E39 pinned b(2),b(3),b(4) as exact fractions but found no closed form (the numerators
-7, -269, -63449 were opaque). With the exact b(5), b(6) added (from `exact_e_dp_rational`
via `data/gt_rational_dp.py`; the eigenvalue law is CONFIRMED at m=5 — the critical
checkpoint — and m=6), an exact-rational subset fit over a harmonic/rational library of
m finds a UNIQUE <=3-feature form reproducing all six exact intercepts b(1..6):

    b(m) = 3/2 - 1/(4m) - H_{2m}^{(2)},     H_{2m}^{(2)} = sum_{k=1}^{2m} 1/k^2

with the finite limit b(inf) = 3/2 - pi^2/6 ~ -0.14493. Combined with the slope
c(m) = H_{2m}/(2m), the full value law for Clay 2025's open multi-shelf complete-feedback
problem is (up to an exponentially small tail set by the spectral gap 1/m):

    E_opt(n,m) = (H_{2m}/2m)*n + [3/2 - 1/(4m) - H_{2m}^{(2)}] + O((1-1/m)^n)

The slope is the average of 1/k over the 2m slots (first-order harmonic); the intercept
is built from sum 1/k^2 over the same slots (second-order) — the structural parallel
that points at the Phase-2 eigenvector. At m=1 it is exactly 3n/4 (Clay's proven Thm
1.5) with no correction, since b(1)=0 and the tail (1-1)^n vanishes.

    uv run python data/gt_bm_closed_form.py
"""

from fractions import Fraction as F
from itertools import combinations


def H(k):
    return sum((F(1, i) for i in range(1, k + 1)), F(0))


def H2(k):
    return sum((F(1, i * i) for i in range(1, k + 1)), F(0))


def bm_closed_form(m):
    """b(m) = 3/2 - 1/(4m) - H_{2m}^{(2)}  (E40)."""
    return F(3, 2) - F(1, 4 * m) - H2(2 * m)


# The exact intercepts b(m) = lim_n (E_opt(n,m) - c(m)*n), from the exact-rational DP
# (data/gt_rational_dp.py; b(2),(3) rigorous over Q, b(4),(5),(6) OOS-validated).
BM_EXACT = {
    1: F(0),
    2: F(-7, 144),
    3: F(-269, 3600),
    4: F(-63449, 705600),
    5: F(-126713, 1270080),
    6: F(-16388909, 153679680),
}


def features(m):
    """Labeled library of candidate basis functions g_j(m), exact Fractions."""
    h2m, h2m2 = H(2 * m), H2(2 * m)
    return {
        "1": F(1), "1/m": F(1, m), "1/m^2": F(1, m * m),
        "1/(2m-1)": F(1, 2 * m - 1), "1/(2m-1)^2": F(1, (2 * m - 1) ** 2),
        "1/(2m)^2": F(1, (2 * m) ** 2), "H2m": h2m, "H2m/m": h2m / m,
        "c=H2m/2m": h2m / (2 * m), "H2m/m^2": h2m / (m * m), "H2m^(2)": h2m2,
        "m*H2m^(2)": m * h2m2, "H2m^(2)/m": h2m2 / m, "Hm": H(m), "Hm/m": H(m) / m,
        "Hm^(2)": H2(m), "H2m^2": h2m * h2m,
    }


def solve_exact(rows, rhs):
    """Exact consistency solve of a Q-system; particular solution or None."""
    ncol = len(rows[0])
    A = [row[:] + [rhs[i]] for i, row in enumerate(rows)]
    piv, r = [], 0
    for c in range(ncol):
        p = next((i for i in range(r, len(A)) if A[i][c] != 0), None)
        if p is None:
            continue
        A[r], A[p] = A[p], A[r]
        A[r] = [x / A[r][c] for x in A[r]]
        for i in range(len(A)):
            if i != r and A[i][c] != 0:
                f = A[i][c]
                A[i] = [a - f * b for a, b in zip(A[i], A[r])]
        piv.append(c)
        r += 1
        if r == len(A):
            break
    for i in range(len(A)):
        if all(A[i][c] == 0 for c in range(ncol)) and A[i][ncol] != 0:
            return None
    sol = [F(0)] * ncol
    for i, c in enumerate(piv):
        sol[c] = A[i][ncol]
    return sol


def search(max_k=3):
    """Every exact <=max_k-feature fit reproducing ALL of BM_EXACT (a fit that
    reproduces points beyond those it is solved on is a real hit, not freedom)."""
    ms = sorted(BM_EXACT)
    labels = list(features(ms[0]))
    fb = {m: features(m) for m in ms}
    hits = []
    for k in range(1, max_k + 1):
        for combo in combinations(labels, k):
            rows = [[fb[m][lab] for lab in combo] for m in ms]
            sol = solve_exact(rows, [BM_EXACT[m] for m in ms])
            if sol is None:
                continue
            if all(sum(fb[m][lab] * s for lab, s in zip(combo, sol)) == BM_EXACT[m]
                   for m in ms):
                hits.append(" + ".join(f"({s})*{lab}"
                                       for lab, s in zip(combo, sol) if s != 0))
    return hits


def main():
    print("== the closed form vs the exact intercepts ==")
    for m, exact in BM_EXACT.items():
        cf = bm_closed_form(m)
        print(f"  m={m}: 3/2 - 1/(4m) - H_2m^(2) = {str(cf):>22}  exact {str(exact):>22}"
              f"  MATCH={cf == exact}")
    print(f"  limit b(inf) = 3/2 - pi^2/6 = {float(F(3,2)) - 3.141592653589793**2/6:.10f}")

    print(f"\n== exact-rational subset search over a {len(features(2))}-feature "
          f"library, all 6 points (m=1..6) ==")
    hits = search(3)
    print(f"  {len(hits)} exact fit(s) with <=3 features:")
    for h in hits:
        print(f"    b(m) = {h}")
    assert hits == ["(3/2)*1 + (-1/4)*1/m + (-1)*H2m^(2)"], hits
    print("  -> UNIQUE; the closed form is the only low-complexity fit.")

    print("\n== the full value law (up to the O((1-1/m)^n) spectral tail) ==")
    print("  E_opt(n,m) = (H_2m/2m)*n + [3/2 - 1/(4m) - H_2m^(2)] + O((1-1/m)^n)")


if __name__ == "__main__":
    main()
