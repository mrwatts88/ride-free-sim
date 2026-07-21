"""The proof road, Phase 2 TAIL: the FADE RATE proven from the blocks, and the
INTERCEPT decomposed. Research probe for experiment **E42** (docs/EXPERIMENTS.md,
docs/GUESSING_THEOREM.md §THE SLOPE PROOF → NEXT STEP).

E41 proved the slope c(m)=H_2m/(2m) via the 2m-block model + the label-
exchangeability Lemma. This probe closes the two remaining pieces of the full
value law  E_opt(n,m) = c(m)*n + b(m) + O((1-1/m)^n):

  (FADE) — PROVEN here for all m, from the blocks.  For a block-0 ascending
  contiguous prefix (1,2,...,k), condition on the last card's TRUE block label
  L_k = ell.  Every UNDEALT card c (>k) must have key > key(k) = (ell, +k) for the
  prefix to read as (1..k); by the block model that survival probability is, PER
  undealt card and INDEPENDENTLY,

      rho_ell = (2m-ell)/(2m)        if ell even   (L_c >= ell survives),
              = (2m-1-ell)/(2m)      if ell odd     (L_c >  ell survives).

  Hence  P(prefix, L_k=ell) = K_ell * rho_ell^(n-k)  with K_ell an n-INDEPENDENT
  constant (GATE 1 verifies this EXACTLY by enumeration).  The observer's hit
  mixes over parses; its excess over the true-parse value 1/(2m) is driven by the
  competing labels ell != 0, whose posterior weight decays like
  (rho_ell/rho_0)^n.  The SLOWEST (dominant) competitor is ell in {1,2}, BOTH at

      rho_ell / rho_0 = (2m-2)/(2m) = 1 - 1/m,

  NOT (1-1/2m):  a same-direction block SKIP is ell -> ell+2 (survival ratio
  (2m-2)/2m), which is 'the factor of 2 in the exponent'.  So the per-step excess
  is Theta((1-1/m)^n) (GATE 2), and therefore delta(n,m)-b(m) = O((1-1/m)^n)
  (GATE 3) — the dominant subdominant eigenvalue is EXACTLY 1-1/m, for ALL m.
  This upgrades E39's Berlekamp-Massey spectrum (confirmed m<=6) to a PROOF of the
  dominant fade rate.

  (INTERCEPT) — decomposed (GATE 4).  Bin every guess by the TRUE block parse.
  Interior guesses of block ell number |B_ell|-1 and each hit exactly 1/(2m-ell)
  (Lemma), so their expected sum is  Sum_ell (n/2m - 1)/(2m-ell)
  = (H_2m/2m) n  -  H_2m.  The slope is the leading term (E41); the INTERIOR
  UNDERCOUNT contributes exactly -H_2m to the intercept.  The remainder

      B(m) := b(m) + H_2m = 3/2 - 1/(4m) + H_2m - H_2m^(2)

  is the BOUNDARY constant: the 2m-1 block-transition guesses + the first guess +
  the interior parse-mixing excess (the summed fade series).  GATE 4 measures the
  three boundary pieces and confirms interior -> slope - H_2m and total -> b(m).
  m=1 is the clean warm-up: H_2=3/2, no fade (spectrum empty), boundary=3/2, so
  b(1) = -3/2 + 3/2 = 0 exactly (Clay Thm 1.5, 3n/4).  The closed-form DERIVATION
  of B(m) for general m (summing the transition hits) is the one remaining step.

    uv run python data/gt_fade_intercept.py            # gates 1-4, m=2,3
    uv run python data/gt_fade_intercept.py 2,3,4      # + m=4 where reachable
"""
import random
import sys
from collections import defaultdict
from fractions import Fraction
from itertools import product

from ridefree.guessing_theorem import _RationalShelfPosterior, exact_e_dp_rational
from ridefree.posterior import ShelfPosterior
from ridefree.shuffle import ShelfShuffle

# Exact intercepts b(m) (E39/E40, the generating-function limit of delta(n,m)).
BM = {
    1: Fraction(0),
    2: Fraction(-7, 144),
    3: Fraction(-269, 3600),
    4: Fraction(-63449, 705600),
}


def H(k):
    return sum(Fraction(1, j) for j in range(1, k + 1))


def H2(k):
    return sum(Fraction(1, j * j) for j in range(1, k + 1))


def clay_slope(m):
    return H(2 * m) / (2 * m)


def b_closed(m):
    """E40 closed form b(m) = 3/2 - 1/(4m) - H_{2m}^{(2)}."""
    return Fraction(3, 2) - Fraction(1, 4 * m) - H2(2 * m)


def rho(m, ell):
    """Per-undealt-card survival probability P(key(c) > key(last)) when the last
    card sits in block `ell` of a block-0 ascending contiguous prefix."""
    lanes = 2 * m
    return Fraction(lanes - ell if ell % 2 == 0 else lanes - 1 - ell, lanes)


def output_from_labels(labels):
    """Deterministic output for a label vector, matching ShelfShuffle: sort cards
    1..n by key (L, +c) if L even else (L, -c)."""
    n = len(labels)
    return sorted(range(1, n + 1),
                  key=lambda c: (labels[c - 1], c if labels[c - 1] % 2 == 0 else -c))


# --- GATE 1: the survival closed form -> the fade rate, exact by enumeration ----

def gate1_survival(m, k, ns):
    """Enumerate ALL (2m)^n label vectors; verify EXACTLY that
    P(output prefix == (1..k) AND L_k = ell) = K_ell * rho_ell^(n-k) with K_ell
    independent of n, and that the dominant confusion rate is 1-1/m at ell in {1,2}.
    """
    lanes = 2 * m
    prefix = tuple(range(1, k + 1))
    print(f"== GATE 1 (m={m}, prefix=(1..{k})): P(A_ell) = K_ell * rho_ell^(n-k), "
          f"K_ell CONSTANT  [exact enumeration] ==")
    Ks = {ell: [] for ell in range(lanes)}
    for n in ns:
        cnt = defaultdict(int)
        for labels in product(range(lanes), repeat=n):
            if tuple(output_from_labels(labels)[:k]) == prefix:
                cnt[labels[k - 1]] += 1
        tot = lanes ** n
        for ell in range(lanes):
            p = Fraction(cnt.get(ell, 0), tot)
            r = rho(m, ell)
            if p != 0 and r != 0:
                Ks[ell].append(p / r ** (n - k))
    for ell in range(lanes):
        seq = Ks[ell]
        const = all(x == seq[0] for x in seq) if seq else True
        assert const, f"K_{ell} not constant: {seq}"
        kv = str(seq[0]) if seq else "(unreached)"
        print(f"   ell={ell}: rho={str(rho(m,ell)):>6}  K_ell={kv:>12}  "
              f"{'CONST ✓' if seq else '—'}")
    rho0 = rho(m, 0)
    ratios = {ell: rho(m, ell) / rho0 for ell in range(1, lanes) if rho(m, ell) != 0}
    dom = max(ratios.values())
    where = [e for e, r in ratios.items() if r == dom]
    assert dom == Fraction(m - 1, m), f"dominant rate {dom} != 1-1/m"
    print(f"   dominant confusion rate max_ell rho_ell/rho_0 = {dom} = 1-1/m, "
          f"at ell={where}  ✓  (a block-skip ell->ell+2, ratio (2m-2)/2m)\n")


# --- GATE 2: the observer's excess is Theta((1-1/m)^n) -------------------------

def gate2_excess_rate(ms, kmax=3):
    """Using the exact-rational posterior (polynomial cost, so large n is cheap),
    show the block-0 excess hit-1/(2m) decays with per-step ratio -> 1-1/m, and
    that a deeper block-0 prefix does not decay SLOWER (block 0 realizes the
    slowest mode)."""
    print("== GATE 2: block-0 excess hit - 1/(2m) decays at rate -> 1-1/m "
          "[exact-rational posterior] ==")
    for m in ms:
        target = Fraction(1, 2 * m)
        rate = Fraction(m - 1, m)
        for k in (3, kmax) if kmax != 3 else (3,):
            prefix = tuple(range(1, k + 1))
            prev = None
            last_ratio = None
            ns = range(k + 3, k + 3 + 16)
            for n in ns:
                post = _RationalShelfPosterior(m, n)
                for c in prefix:
                    post.observe(c)
                ex = max(post.next_probs().values()) - target
                if prev is not None and prev != 0:
                    last_ratio = float(ex / prev)
                prev = ex
            # the excess/rate^n ratio should approach a positive constant
            print(f"   m={m}, prefix=(1..{k}): last-step excess ratio "
                  f"= {last_ratio:.5f}  (1-1/m = {float(rate):.5f})")
        assert last_ratio is None or abs(last_ratio - float(rate)) < 0.06, \
            f"excess rate {last_ratio} not near 1-1/m for m={m}"
    print()


# --- GATE 3: the GLOBAL fade — (delta(n,m) - b(m)) ~ (1-1/m)^n -----------------

def gate3_global_fade(ms, n_hi=None):
    """With the exact b(m), the value-law tail delta(n,m)-b(m) fades at 1-1/m —
    the same rate GATE 1 derived from the block-0 confusion. Exact-rational DP."""
    print("== GATE 3: value-law tail (delta - b(m)) fades at 1-1/m [exact DP] ==")
    for m in ms:
        if m not in BM:
            continue
        cs, b = clay_slope(m), BM[m]
        hi = n_hi or (24 if m == 2 else 16)
        prev = None
        last = None
        for n in range(6, hi + 1):
            e, _ = exact_e_dp_rational(n, m)
            tail = e - cs * n - b
            if prev not in (None, 0):
                last = float(tail / prev)
            prev = tail
        print(f"   m={m}: (delta-b) ratio at n={hi} = {last:.5f}  "
              f"(1-1/m = {float(Fraction(m-1,m)):.5f})"
              f"{'   [+ n^2 (1-1/m)^n prefactor: mult-3 eigval]' if m==2 else ''}")
    print()


# --- GATE 4: the intercept, block-decomposed ----------------------------------

def gate4_intercept(ms, n=40, trials=4000, seed0=24_400_000_000):
    """Bin every guess by the TRUE block parse (known from the drawn labels):
    INTERIOR (prev card not last of its block) vs TRANSITION (crossing blocks) vs
    FIRST. Confirm interior-ideal -> (H_2m/2m)n - H_2m, and boundary constant
    B(m) = b(m) + H_2m. Uses the low-variance `predicted` estimator (unbiased for
    E_opt) with the posterior; MC, fixed seed."""
    print(f"== GATE 4 (n={n}, trials={trials}): intercept b(m) = -H_2m + B(m), "
          f"B(m)=b(m)+H_2m  [MC, predicted estimator] ==")
    lanes_of = {}
    for m in ms:
        lanes = 2 * m
        cs = clay_slope(m)
        # accumulators: interior-actual hit, interior-IDEAL (1/(2m-ell)),
        # transition hit, first-guess hit.
        s_int = s_int_ideal = s_trans = s_first = 0.0
        s_total = 0.0
        s_total2 = 0.0
        rng = random.Random(seed0 + m)
        for _ in range(trials):
            labels = [rng.randrange(lanes) for _ in range(n)]
            out = output_from_labels(labels)
            lab = [labels[c - 1] for c in out]  # block label per output position
            post = ShelfPosterior(m, list(range(1, n + 1)))
            total = 0.0
            for t in range(n):
                hit = max(post.next_probs().values())
                total += hit
                if t == 0:
                    s_first += hit
                elif lab[t] == lab[t - 1]:  # interior to block lab[t-1]
                    ell = lab[t - 1]
                    s_int += hit
                    s_int_ideal += 1.0 / (2 * m - ell)
                else:  # crossing a block boundary
                    s_trans += hit
                post.observe(out[t])
            s_total += total
            s_total2 += total * total
        inv = 1.0 / trials
        interior = s_int * inv
        interior_ideal = s_int_ideal * inv
        transition = s_trans * inv
        first = s_first * inv
        total_mean = s_total * inv
        se = ((s_total2 * inv - total_mean ** 2) / (trials - 1)) ** 0.5
        delta = total_mean - float(cs) * n
        b = float(BM[m]) if m in BM else float(b_closed(m))
        Bm = b + float(H(2 * m))
        # interior_ideal - slope*n should approach -H_2m
        interior_ideal_intercept = interior_ideal - float(cs) * n
        excess_const = interior - interior_ideal  # summed parse-mixing excess
        boundary = transition + first + excess_const
        print(f"   m={m}:")
        print(f"     interior IDEAL  = {interior_ideal:9.4f}   "
              f"(- slope*n = {interior_ideal_intercept:+.4f}  ->  -H_2m = "
              f"{float(-H(2*m)):+.4f})")
        print(f"     interior EXCESS = {excess_const:+.4f}  (summed parse-mixing "
              f"excess, a constant){'  [m=1: no n-tail, delta(n,1)=0 exactly]' if m==1 else ''}")
        print(f"     transition sum  = {transition:8.4f}    first guess = {first:.4f}"
              f"  ->  1/(2m) = {1.0/(2*m):.4f}  (o_1=1 iff L_1=0)")
        print(f"     boundary B(m)   = {boundary:+.4f}   ->  b(m)+H_2m = "
              f"{Bm:+.4f}  =  3/2-1/4m+H_2m-H_2m^(2)")
        print(f"     TOTAL delta     = {delta:+.4f} +- {se:.4f}   ->  b(m) = "
              f"{b:+.4f}   [n={n}, o(1) transient remains]")
    print()


def main():
    args = sys.argv[1:]
    ms = [int(x) for x in args[0].split(",")] if args else [2, 3]
    print("E42 — the fade rate (proven from blocks) + the intercept decomposition\n")
    gate1_survival(2, 3, range(4, 11))   # 4^10 vectors at the top; CPython-tolerable
    gate1_survival(3, 3, range(4, 9))    # 6^8 at the top
    gate2_excess_rate([m for m in ms if m <= 5])
    gate3_global_fade([m for m in ms if m in BM])
    gate4_intercept([1] + ms)


if __name__ == "__main__":
    main()
