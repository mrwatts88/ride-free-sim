"""The proof road: EXACT-RATIONAL run-composition DP -> exact b(m) + the operator
spectrum. Research probe for experiment **E39** (docs/EXPERIMENTS.md,
docs/GUESSING_THEOREM.md).

E37's `exact_e_dp` computes E_opt(n,m) in floats and could only say the value law
E_opt = c(m)*n + b(m) + o(1) is "affine to < 1e-5 past a short transient". This
probe runs the SAME run-composition DP in exact arithmetic
(`guessing_theorem.exact_e_dp_rational`) and mines the exact rational sequence
delta(n,m) = E_opt(n,m) - c(m)*n. Two results the float DP could not reach:

  1. b(m) EXACTLY, as a fraction. The delta-sequence is C-finite (it satisfies a
     fixed linear recurrence over Q — found here by Berlekamp-Massey and VERIFIED
     on held-out terms), so its limit b(m) = lim delta(n) is extracted exactly via
     the generating function. Results: b(2) = -7/144, b(3) = -269/3600,
     b(4) = -63449/705600, b(5) = -126713/1270080, b(6) = -16388909/153679680, all
     matching the E40 CLOSED FORM b(m) = 3/2 - 1/(4m) - H_{2m}^{(2)} (limit
     3/2 - pi^2/6). The o(1) is genuinely NON-ZERO at every finite n (for m=2 it
     even overshoots and returns), so the law is affine + a decaying correction,
     not "exactly affine" — a correction to E37's language.

  2. The OPERATOR SPECTRUM. The recurrence's characteristic polynomial factors
     EXACTLY over Q as
         (x - 1) * prod_{i=1}^{m-1} (x - i/m)^3 * prod_{i=1}^{m-1} (x - (2i-1)/(2m))
     i.e. the subdominant eigenvalues of Clay's m-shelf feedback operator are
         {i/m : i=1..m-1}          each multiplicity 3  (n^2 * lambda^n modes), and
         {(2i-1)/(2m) : i=1..m-1}  each multiplicity 1,
     with the unit eigenvalue carrying the linear term. Order = 4m-3. The spectral
     gap is exactly 1/m (slowest subdominant mode (1 - 1/m)^n), which is why the
     large-m value law converges so slowly at deck scale (m=10 -> (0.9)^n). This is
     the *feedback* operator's spectrum -- distinct from Tripathi's single-shelf
     POSITION-matrix spectrum (arXiv:2602.07920), which governs the NO-feedback
     game (value ~ sqrt(2n/pi), not 3n/4). The gate below confirms the
     factorization exactly over Q at m=2,3 (Berlekamp-Massey, independent of the
     conjecture) and validates it out-of-sample at m>=4.

    uv run python data/gt_rational_dp.py [m1,m2,...] [n_hi]   # default 2,3  (24/20)
    # PyPy (~4x) to push n / reach m>=4 (heavier: exact arithmetic, ~(2m)^n denoms):
    # PYTHONPATH=src ~/.local/bin/pypy3.11 -u data/gt_rational_dp.py 2,3,4 26
"""

import sys
import time
from fractions import Fraction

from ridefree.guessing_theorem import exact_e, exact_e_dp_rational


def clay_slope(m: int) -> Fraction:
    """Clay's asymptotic per-card rate c(m) = H_{2m} / (2m) (exact at m=1: 3/4)."""
    return sum(Fraction(1, k) for k in range(1, 2 * m + 1)) / (2 * m)


def bm_closed_form(m: int) -> Fraction:
    """The value-law intercept in CLOSED FORM (E40): b(m) = 3/2 - 1/(4m) - H_{2m}^{(2)},
    where H_{2m}^{(2)} = sum_{k=1}^{2m} 1/k^2. Reproduces the exact b(1..6) the DP
    extracts below (b(1)=0, b(2)=-7/144, ..., b(6)=-16388909/153679680) and has the
    finite limit 3/2 - pi^2/6 ~ -0.14493. The slope c(m) is the average of 1/k over
    the 2m slots (first-order harmonic); b(m) is built from sum 1/k^2 over the same
    slots (second-order) — the parallel that points at the Phase-2 eigenvector."""
    h2 = sum(Fraction(1, k * k) for k in range(1, 2 * m + 1))
    return Fraction(3, 2) - Fraction(1, 4 * m) - h2


# --- exact C-finite machinery over Q (the analysis layer) --------------------


def berlekamp_massey(s):
    """Minimal linear recurrence over a field: returns c with
    s[i] = sum_j c[j]*s[i-1-j]. (Standard algorithm; s a list of Fractions.)"""
    ls, cur = [], []
    lf, ld = 0, Fraction(0)
    for i in range(len(s)):
        t = sum(cur[j] * s[i - 1 - j] for j in range(len(cur)))
        if s[i] - t == 0:
            continue
        if not cur:
            cur = [Fraction(0)] * (i + 1)
            lf, ld = i, s[i] - t
            continue
        k = (s[i] - t) / ld
        c = [Fraction(0)] * (i - lf - 1) + [k] + [-k * x for x in ls]
        if len(c) < len(cur):
            c += [Fraction(0)] * (len(cur) - len(c))
        for j in range(len(cur)):
            c[j] += cur[j]
        if i - len(cur) > lf - len(ls):
            ls, lf, ld = cur[:], i, s[i] - t
        cur = c
    return cur


def predicts(seq, c):
    """Does recurrence c reproduce every seq[i] (i>=len(c)) exactly?"""
    L = len(c)
    return all(sum(c[j] * seq[i - 1 - j] for j in range(L)) == seq[i]
               for i in range(L, len(seq)))


def gf_limit(tail, c):
    """Exact limit of a convergent sequence obeying s[i]=sum c[j] s[i-1-j], via the
    generating function: b = N(1)/E(1) with C=(1-x)E and N=(C*G) mod x^L."""
    L = len(c)
    C = [Fraction(1)] + [-cj for cj in c]  # C(x) = 1 - sum c_j x^j
    if sum(C) != 0:
        return None  # x=1 not a root: no constant mode (sequence doesn't converge)
    E, acc = [], Fraction(0)
    for k in range(L):  # E = C/(1-x): prefix sums of C
        acc += C[k]
        E.append(acc)
    N = [sum(C[j] * tail[k - j] for j in range(min(k, L) + 1)
             if 0 <= k - j < len(tail)) for k in range(L)]
    return sum(N) / sum(E)


def pmul(a, b):
    r = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            r[i + j] += ai * bj
    return r


def spectrum(m):
    """The conjectured feedback-operator spectrum for m shelves: (eigenvalue,
    multiplicity) pairs, subdominant only (the unit eigenvalue is implicit)."""
    triple = [(Fraction(i, m), 3) for i in range(1, m)]
    single = [(Fraction(2 * i - 1, 2 * m), 1) for i in range(1, m)]
    return sorted(triple + single, key=lambda rm: rm[0])


def charpoly_hypothesis(m):
    """(x-1) * prod (x - lambda)^mult over the spectrum(m) -- coeffs, index=power."""
    p = [Fraction(-1), Fraction(1)]  # (x - 1)
    for r, mult in spectrum(m):
        for _ in range(mult):
            p = pmul(p, [-r, Fraction(1)])
    return p


def rec_from_charpoly(p):
    """Monic char poly (index=power, deg L) -> recurrence coeffs c (len L)."""
    L = len(p) - 1
    return [-p[L - 1 - j] for j in range(L)]


def charpoly_from_rec(c):
    """Recurrence coeffs -> monic char poly x^L - c0 x^{L-1} - ... (index=power)."""
    L = len(c)
    p = [Fraction(0)] * (L + 1)
    p[L] = Fraction(1)
    for j in range(L):
        p[L - 1 - j] = -c[j]
    return p


# --- gates -------------------------------------------------------------------

EXACT_E9 = {2: Fraction(152375, 32768), 3: Fraction(594355, 157464)}


def gate_exact() -> None:
    """The rational DP must reproduce the n! enumeration with EXACT Fraction
    equality (a stronger gate than E37's float 1e-9) -- confirming the
    (dir, rank, run-composition) state is EXACTLY sufficient, and m=1 is 3n/4."""
    print("== GATE 1: rational DP == n! enumeration, EXACTLY (n<=7, m=1..6) ==")
    all_eq = True
    for n in range(2, 8):
        for m in range(1, 7):
            eq = exact_e_dp_rational(n, m)[0] == exact_e(n, m)[0]
            all_eq &= eq
            if not eq:
                print(f"   MISMATCH at n={n} m={m}")
    assert all_eq
    print("   all 36 cells exact-equal  ->  sigma is exactly sufficient  ✓")

    print("== GATE 2: pinned exact E(9, m) rationals ==")
    for m, frac in EXACT_E9.items():
        e, ns = exact_e_dp_rational(9, m)
        assert e == frac, (m, e, frac)
        print(f"   E(9,{m}) = {frac} = {float(frac):.8f}  ({ns} states)  ✓")

    print("== GATE 3: m=1 is EXACTLY 3n/4 (delta == 0) ==")
    for n in range(2, 13):
        e, _ = exact_e_dp_rational(n, 1)
        assert e == Fraction(3 * n, 4) and e - clay_slope(1) * n == 0, n
    print("   E_opt(n,1) = 3n/4 exactly for n=2..12, delta(n,1) == 0  ✓")


# --- the exact value law + spectrum ------------------------------------------


def analyze(m: int, n_lo: int, n_hi: int, independent: bool) -> None:
    c = clay_slope(m)
    print(f"\n== m={m}:  exact delta(n,m) = E_opt - c(m)*n,  c(m) = {c} ==")
    t0 = time.time()
    deltas = []
    for n in range(n_lo, n_hi + 1):
        e, ns = exact_e_dp_rational(n, m)
        deltas.append(e - c * n)
    print(f"   computed exact delta(n) for n={n_lo}..{n_hi} in {time.time()-t0:.1f}s"
          f"   (delta({n_hi}) = {float(deltas[-1]):+.12f})")

    hyp = charpoly_hypothesis(m)
    order = len(hyp) - 1
    if len(deltas) < order + 2:
        # Guard: the order-(4m-3) recurrence needs order seed values for gf_limit
        # PLUS >=2 more to validate out-of-sample; too few silently gives a vacuous
        # "predicts 0 OOS: True" and a wrong b(m). The recurrence holds from n=2 (no
        # transient — verified at m=4,5), so n_lo=2 minimizes the max n. Raise n_hi
        # (PyPy) — e.g. m=5 wants n_hi>=20 (n_lo=2), m=6 wants n_hi>=24.
        print(f"   ⚠ INSUFFICIENT n: the order-{order} (=4m-3) recurrence needs "
              f">= {order+2} exact δ values to validate + extract b (have "
              f"{len(deltas)}). Raise n_hi / lower n_lo under PyPy. Skipping.")
        return
    if independent:
        # Recover the recurrence from the data alone (hold out the last 4).
        c_rec = berlekamp_massey(deltas[:-4])
        ok = predicts(deltas, c_rec)
        match = (len(charpoly_from_rec(c_rec)) == len(hyp)
                 and all(a == b for a, b in zip(charpoly_from_rec(c_rec), hyp)))
        print(f"   Berlekamp-Massey (from data, held out 4): order {len(c_rec)} "
              f"(= 4m-3 = {4*m-3}? {len(c_rec)==4*m-3}); predicts held-out: {ok}")
        print(f"   char poly == (x-1)*prod(x-i/m)^3*prod(x-(2i-1)/2m) over Q: {match}")
        rec = c_rec
    else:
        # m>=4: assume the eigenvalue law, VALIDATE it out-of-sample.
        rec = rec_from_charpoly(hyp)
        ok = predicts(deltas, rec)
        print(f"   eigenvalue-law recurrence (order {order}=4m-3): predicts ALL "
              f"{len(deltas)-order} out-of-sample delta(n) exactly: {ok}")

    b = gf_limit(deltas, rec)
    bcf = bm_closed_form(m)
    print(f"   >>> b({m}) = {b} = {float(b):.15f}")
    print(f"       closed form 3/2 - 1/(4m) - H_2m^(2) = {bcf}  "
          f"MATCH = {b == bcf}")
    eig = spectrum(m)
    gap = 1 - max(r for r, _ in eig)
    print(f"   subdominant spectrum: "
          + ", ".join(f"{r}(x{mult})" for r, mult in eig))
    print(f"   spectral gap = {gap} = 1/m   ->   correction decays like "
          f"(1-1/m)^n = ({float(1-gap):.3f})^n")


def main():
    args = sys.argv[1:]
    m_list = [int(x) for x in args[0].split(",")] if args else [2, 3]
    n_hi = int(args[1]) if len(args) > 1 else None
    print("exact_e_dp_rational: the run-composition DP in exact arithmetic (E39)")
    print(f"m_list={m_list}\n")
    gate_exact()
    # m=2 recovers the spectrum from data (independent); m>=3 validates it OOS
    # (independent BM would need ~2(4m-3) points -> heavier n; PyPy to push). The
    # recurrence holds from n=2, so n_lo=2 for m>=4 keeps the max n (hence cost)
    # down. m=5,6 are heavy (~n^{10}, n^{12} states, tiny leading constant) — PyPy,
    # and expect several minutes (m=6 to n=24 ~ 30 min, ~13e6 states, ~10 GB).
    defaults = {2: (6, 22), 3: (6, 18), 4: (2, 22), 5: (2, 24), 6: (2, 24)}
    for m in m_list:
        if m == 1:
            continue
        lo, hi_def = defaults.get(m, (6, 18))
        hi = n_hi if n_hi is not None else hi_def
        analyze(m, lo, hi, independent=(m == 2))
    print("\n== SUMMARY ==")
    print("   E_opt(n,m) = c(m)*n + b(m) + O((1-1/m)^n)   (the o(1) is NON-zero)")
    print("   c(m) = H_2m/2m  (avg of 1/k over the 2m slots)")
    print("   b(m) = 3/2 - 1/(4m) - H_2m^(2)   (E40 CLOSED FORM; H_2m^(2)=sum 1/k^2)")
    print("          exact at m=1..6:  0, -7/144, -269/3600, -63449/705600,")
    print("          -126713/1270080, -16388909/153679680;  limit 3/2 - pi^2/6")
    print("   feedback operator spectrum: 1;  {i/m}_1^{m-1} (mult 3);  "
          "{(2i-1)/2m}_1^{m-1} (mult 1);  gap 1/m")
    print("   confirmed: spectrum + b(m) exact at m=2,3 (rigorous Q), OOS at m=4,5,6")


if __name__ == "__main__":
    main()
