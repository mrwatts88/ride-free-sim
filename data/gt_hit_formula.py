"""The proof road, Phase 2 tail (continued): the EXACT per-position hit law, which
turns the value law into one explicit sum and pins the intercept mechanism. Research
probe for experiment **E43** (docs/EXPERIMENTS.md, docs/GUESSING_THEOREM.md).

E42 proved the fade rate and derived two intercept pieces, but framed the remainder as
a "transition-guess sum". That framing was WRONG: the intercept is not a boundary
effect, it is a finite-size correction living at EVERY position. E43 gets the exact
correction.

THE PER-POSITION HIT LAW (gated exact vs enumeration, GATE 1).  Consider any guess made
from a run whose last card v is in block ell, with A undealt cards on the CONTINUATION
side (above v for an ascending run / below for descending, INCLUDING the guess target
w1) and B on the opposite side.  The E41 Lemma gives the undealt-label distribution;
the guess w1 (smallest undealt above / largest below) is correct iff w1 has the minimum
KEY among undealt, i.e. no other undealt card's block/value beats it.  Counting the
independent-uniform labels gives, with r = 2m - ell and d = j - ell (j = w1's block):

    P(next = w1 | ell, A, B) = (1/r) sum_{d=0}^{r-1}
            (1 - (d + (d mod 2))/r)^{A-1} * (1 - (d - (d mod 2))/(r-1))^{B}.

The d=0 term is 1 for all A,B, so in the BULK (A,B -> inf) only it survives and the hit
-> 1/r = 1/(2m-ell) — the E41 Lemma value (GATE 2).  The d>=1 terms are the finite-size
EXCESS.  The d=1 term is (1/r)(1-2/r)^{A-1}: it decays in A (the continuation supply),
so it matters only near the value-range extreme — and it is the H_{2m}^{(2)} generator.

THE VALUE LAW IS THIS FORMULA SUMMED (gated exact, GATE 3).  The pure-continuation
strategy (guess w1 every step; first guess = value 1) is OPTIMAL — its value equals
E_opt EXACTLY at every (n,m) (an independent re-confirmation of E35's G-optimality) —
so E_opt(n,m) = sum_t E[ P(next = w1_t) ] with the per-step term the formula above.

THE INTERCEPT, CLEANLY (GATE 4).  The bulk reference sum_{p} 1/(2m - ell(o_{p-1}))
-> (H_2m/2m) n - 1 (every card but the LAST is some guess's predecessor; the last
card's 1/(2m-(2m-1))=1 is missing).  The first guess -> 1/(2m) (o_1 = 1 iff L_1 = 0).
So

    b(m) = -1 + 1/(2m) + S_excess(m),   S_excess(m) = sum_t E[ hit_t - 1/(2m-ell_t) ],

and matching E40's b(m) = 3/2 - 1/(4m) - H_{2m}^{(2)} gives the last mile in closed
form: **S_excess(m) = 5/2 - 3/(4m) - H_{2m}^{(2)}**, an explicit sum of the formula's
d>=1 excess over the deck.  Deriving that sum in closed form finishes b(m) — now a
concrete summation, not "find the transition guesses".

    uv run python data/gt_hit_formula.py         # gates, m=2,3
"""
import sys
from fractions import Fraction
from itertools import product

from ridefree.guessing_theorem import exact_e_dp_rational, hit_probability as p_hit

BM = {1: Fraction(0), 2: Fraction(-7, 144), 3: Fraction(-269, 3600)}


def H(k):  return sum(Fraction(1, j) for j in range(1, k + 1))
def H2(k): return sum(Fraction(1, j * j) for j in range(1, k + 1))
def clay_slope(m): return H(2 * m) / (2 * m)


def output_from_labels(labels):
    n = len(labels)
    return sorted(range(1, n + 1),
                  key=lambda c: (labels[c - 1], c if labels[c - 1] % 2 == 0 else -c))


# --- GATE 1: the per-position hit law, exact vs enumeration -------------------

def gate1_formula(m, n):
    """Enumerate all (2m)^n label vectors; group by (prefix, parse, direction) and
    verify P(next=w1) matches p_hit(ell, A, B) EXACTLY for every group (ascending AND
    descending)."""
    from collections import defaultdict
    lanes = 2 * m
    grp = defaultdict(lambda: [0, 0])
    meta = {}
    for labels in product(range(lanes), repeat=n):
        out = output_from_labels(labels)
        pos = {c: i for i, c in enumerate(out)}
        for t in range(1, n):
            v = out[t - 1]; ell = labels[v - 1]
            undealt = [c for c in range(1, n + 1) if pos[c] >= t]
            above = [c for c in undealt if c > v]
            below = [c for c in undealt if c < v]
            if ell % 2 == 0:
                if not above:
                    continue
                w1, A, B, dirn = min(above), len(above), len(below), "asc"
            else:
                if not below:
                    continue
                w1, A, B, dirn = max(below), len(below), len(above), "desc"
            key = (tuple(out[:t]), tuple(labels[c - 1] for c in out[:t]), dirn)
            grp[key][0] += 1
            grp[key][1] += 1 if out[t] == w1 else 0
            meta[key] = (ell, A, B)
    bad = 0
    for key, (c, h) in grp.items():
        ell, A, B = meta[key]
        if Fraction(h, c) != p_hit(m, ell, A, B):
            bad += 1
    assert bad == 0, (m, n, bad)
    print(f"   m={m}, n={n}: {len(grp)} (prefix,parse,dir) groups, formula EXACT ✓")


# --- GATE 2: bulk limit -> 1/(2m-ell) ----------------------------------------

def gate2_bulk(ms):
    print("== GATE 2: p_hit -> 1/(2m-ell) as A,B grow (d=0 term = 1; rest -> 0) ==")
    for m in ms:
        for ell in range(2 * m - 1):
            vals = [float(p_hit(m, ell, A, A)) for A in (4, 12, 40, 120)]
            assert abs(vals[-1] - 1.0 / (2 * m - ell)) < 1e-3
            print(f"   m={m} ell={ell}: p_hit(A=A=4,12,40,120) = "
                  f"{', '.join(f'{v:.4f}' for v in vals)}  -> 1/(2m-ell)="
                  f"{1.0/(2*m-ell):.4f}")
    print()


# --- GATE 3: the value law IS the formula summed (continuation optimal) -------

def v_cont(m, n):
    """Exact E[realized hits] of the pure-continuation strategy (guess w1; first = 1)."""
    lanes = 2 * m
    hits = 0
    for labels in product(range(lanes), repeat=n):
        out = output_from_labels(labels)
        remaining = set(range(1, n + 1))
        for t in range(n):
            if t == 0:
                guess = 1
            else:
                v = out[t - 1]
                asc = (t == 1) or (out[t - 1] > out[t - 2])
                above = [c for c in remaining if c > v]
                below = [c for c in remaining if c < v]
                if asc:
                    guess = min(above) if above else (max(below) if below else v)
                else:
                    guess = max(below) if below else (min(above) if above else v)
            if guess == out[t]:
                hits += 1
            remaining.discard(out[t])
    return Fraction(hits, lanes ** n)


def gate3_value(ms, ns):
    print("== GATE 3: continuation strategy is OPTIMAL — V_cont == E_opt exactly ==")
    for m in ms:
        for n in ns:
            vc = v_cont(m, n)
            eo, _ = exact_e_dp_rational(n, m)
            assert vc == eo, (m, n, vc, eo)
        print(f"   m={m}: V_cont == E_opt for n in {list(ns)}  ✓")
    print()


# --- GATE 4: the intercept, reduced to S_excess ------------------------------

def gate4_intercept(ms, ns):
    print("== GATE 4: b(m) = -1 + 1/(2m) + S_excess(m),  "
          "S_excess(m) = 5/2 - 3/(4m) - H_2m^(2) ==")
    for m in ms:
        cs = clay_slope(m)
        target_S = Fraction(5, 2) - Fraction(3, 4 * m) - H2(2 * m)
        # closed-form identity check
        assert BM[m] == -1 + Fraction(1, 2 * m) + target_S
        assert BM[m] == Fraction(3, 2) - Fraction(1, 4 * m) - H2(2 * m)
        print(f"   m={m}: b(m) = {BM[m]} ;  S_excess target 5/2-3/4m-H_2m^(2) = "
              f"{target_S} = {float(target_S):.5f}")
        # numerical S_excess from the exact value: S = E_opt - slope*n + 1 - first,
        # first = P(o_1 = 1) -> 1/(2m); shown converging (fade O((1-1/m)^n)).
        for n in ns:
            eo, _ = exact_e_dp_rational(n, m)
            # first-guess hit for this n (exact): value 1 is o_1 iff it has min key;
            # approximate by 1/(2m) (its n->inf limit) for the display of convergence.
            S_n = eo - cs * n + 1 - Fraction(1, 2 * m)
            print(f"      n={n:2d}: E_opt - slope*n + 1 - 1/2m = {float(S_n):+.5f}"
                  f"   (-> {float(target_S):.5f})")
    print()


def main():
    ms = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [2, 3]
    print("E43 — the exact per-position hit law; the value law as one explicit sum\n")
    print("== GATE 1: per-position hit law exact vs enumeration ==")
    gate1_formula(2, 6)
    gate1_formula(2, 7)
    gate1_formula(3, 5)
    gate1_formula(3, 6)
    print()
    gate2_bulk(ms)
    gate3_value(ms, range(4, 8))
    gate4_intercept(ms, [8, 12, 16, 20])


if __name__ == "__main__":
    main()
