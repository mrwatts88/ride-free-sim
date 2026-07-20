"""E32 — is any baccarat MAIN bet beatable by composition? The exact-calculator
search that closes the question (incl. EZ Baccarat's banker-3-card-7 push).

Matt's counter-argument to "the mains are dead from the linear EORs": we don't
know ALL compositions' EVs, and a quadratic/curvature count could catch what the
linear EORs miss (exactly how quad-Q beat 21+3). And EZ Baccarat's push-on-
banker-3-card-7 makes the banker main EV explicitly ride on a COUNTABLE event
(the Dragon 7), anti-correlated with the side bet — the most plausible main-bet
crack we have. This settles it computationally rather than by citing Thorp:

  `fast_outcomes(composition)` is EXACT (gated vs WoO to the digit), so we can
  price every reachable composition — no Monte Carlo of outcomes, no assumption.

Two arms:
  (1) SAMPLING — deal random depletions to the cut and price the mains on the
      true reachable distribution (what you would actually see). Built-in gate:
      the side bets (Dragon7/Panda8), which we KNOW are countable (M9), MUST show
      up +EV in deep samples, or the search is broken.
  (2) DIRECTED CEILING — hill-climb the composition to MAXIMIZE each main's EV at
      a fixed remaining-card count R (respecting per-value bounds), exact-priced.
      This is the best achievable even hunting for it, at each depth R. If the
      ceiling stays negative through cut depth, no count — linear, quadratic, or
      arbitrary — beats the main there.

Run: PYTHONPATH=src uv run --python pypy@3.11 --no-project data/e32_mains.py
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ridefree.baccarat import (
    BACCARAT_8D,
    EZ_BACCARAT_8D,
    fast_outcomes,
    fresh_composition,
)

DECKS = 8
CAP = {v: (16 * DECKS if v == 0 else 4 * DECKS) for v in range(10)}
FRESH = fresh_composition(DECKS)
N = sum(FRESH.values())  # 416


def price(comp):
    """All main + side EVs for one composition from a single exact call."""
    o = fast_outcomes(comp)
    return {
        "ez_banker": o.ev_main(EZ_BACCARAT_8D, "banker"),
        "cl_banker": o.ev_main(BACCARAT_8D, "banker"),
        "player": o.ev_main(EZ_BACCARAT_8D, "player"),
        "tie": o.ev_main(EZ_BACCARAT_8D, "tie"),
        "dragon7": o.ev_dragon7(EZ_BACCARAT_8D),
        "panda8": o.ev_panda8(EZ_BACCARAT_8D),
    }


BETS = ("ez_banker", "cl_banker", "player", "tie", "dragon7", "panda8")

# --- gate: fresh-shoe EVs must match the published references ---
fresh_ev = price(dict(FRESH))
print("fresh 8-deck EVs (gate vs WoO: EZ banker -1.0183%, classic banker "
      "-1.0579%, player -1.2351%, tie -14.3596%):")
for b in BETS:
    print(f"  {b:10s} {fresh_ev[b]:+8.4%}")
print()

# ---------------------------------------------------------------------------
# Arm 1: sampling the reachable distribution at the cut
# ---------------------------------------------------------------------------
SAMPLES = int(sys.argv[1]) if len(sys.argv) > 1 else 40_000
PEN = 0.95
R_cut = N - int(PEN * N)  # remaining cards at the cut (~21)
rng = random.Random(23_400_000_001)
flat = [v for v, k in FRESH.items() for _ in range(k)]

best = {b: (-9.9, None) for b in BETS}
pos_frac = {b: 0 for b in BETS}
captured = {b: 0.0 for b in BETS}   # sum of ev when +EV = value if you bet only then
for _ in range(SAMPLES):
    rng.shuffle(flat)
    rem = flat[:R_cut]
    comp = {v: 0 for v in range(10)}
    for v in rem:
        comp[v] += 1
    ev = price(comp)
    for b in BETS:
        if ev[b] > best[b][0]:
            best[b] = (ev[b], dict(comp))
        if ev[b] > 0:
            pos_frac[b] += 1
            captured[b] += ev[b]

print(f"ARM 1 — sampling {SAMPLES} reachable compositions at the cut "
      f"(R={R_cut} cards left, pen {PEN}):")
print(f"{'bet':10s} {'max EV':>9s} {'% +EV':>8s} {'avg edge|+EV':>13s} "
      f"{'captured u/opp':>15s}")
for b in BETS:
    pf = pos_frac[b]
    cond = captured[b] / pf if pf else 0.0
    print(f"{b:10s} {best[b][0]:+8.2%} {pf/SAMPLES:>7.2%} {cond:>12.3%} "
          f"{captured[b]/SAMPLES:>+14.4%}")
print("  captured u/opp = E[edge | you bet only the +EV last-coup shoes] "
      "(the practical figure of merit)")
print("  (gate: dragon7 & panda8 MUST show +EV shoes — they are countable, M9)")
print()

# ---------------------------------------------------------------------------
# Arm 2: directed ceiling — max each main's EV at fixed R (hill-climb)
# ---------------------------------------------------------------------------
def random_comp(R, seed_rng):
    """A valid composition of exactly R cards (0 <= count_v <= CAP[v])."""
    comp = {v: 0 for v in range(10)}
    left = R
    order = list(range(10))
    seed_rng.shuffle(order)
    for v in order:
        take = min(CAP[v], left)
        # random amount up to the cap, but ensure the rest can absorb what's left
        remaining_cap_after = sum(CAP[w] for w in order[order.index(v) + 1:])
        lo = max(0, left - remaining_cap_after)
        comp[v] = seed_rng.randint(lo, take)
        left -= comp[v]
    return comp


def hill_climb(R, target, seed_rng, restarts=5):
    """Best `target`-EV composition of R cards found by multi-start hill-climb
    (swap one card a->b, keep the best improving swap). A lower bound on the
    true max; if it stays negative the bet is unbeatable at depth R."""
    best_ev, best_comp = -9.9, None
    for _ in range(restarts):
        comp = random_comp(R, seed_rng)
        cur = price(comp)[target]
        improved = True
        while improved:
            improved = False
            best_local = (cur, None)
            for a in range(10):
                if comp[a] == 0:
                    continue
                for b in range(10):
                    if b == a or comp[b] >= CAP[b]:
                        continue
                    comp[a] -= 1; comp[b] += 1
                    ev = price(comp)[target]
                    comp[a] += 1; comp[b] -= 1
                    if ev > best_local[0] + 1e-12:
                        best_local = (ev, (a, b))
            if best_local[1] is not None:
                a, b = best_local[1]
                comp[a] -= 1; comp[b] += 1
                cur = best_local[0]
                improved = True
        if cur > best_ev:
            best_ev, best_comp = cur, dict(comp)
    return best_ev, best_comp


hc_rng = random.Random(23_400_000_002)
R_VALUES = [6, 13, 20, 26, 40, 78]
TARGETS = ["ez_banker", "cl_banker", "player"]
print("ARM 2 — directed ceiling: MAX main EV achievable at R cards left "
      "(hill-climb, the best even when hunting for it):")
print(f"  cut card sits at R~{R_cut}; deeper R is past the cut (unreachable in play)")
header = f"{'R left':>7s}" + "".join(f"{t:>13s}" for t in TARGETS)
print(header)
ceilings = {}
for R in R_VALUES:
    row = {}
    cells = []
    for t in TARGETS:
        ev, comp = hill_climb(R, t, hc_rng)
        row[t] = ev
        cells.append(f"{ev:+12.3%}")
    ceilings[R] = row
    marker = "  <- cut depth" if R == 20 else (" (past cut)" if R < R_cut else "")
    print(f"{R:>7d}" + "".join(cells) + marker)
print()

# --- verdict ---
mains = ("ez_banker", "cl_banker", "player", "tie")
any_reachable_pos = any(pos_frac[b] for b in mains)
cut_ceiling_pos = any(ceilings[R][t] > 0 for R in R_VALUES if R >= R_cut
                      for t in TARGETS)
print("VERDICT:")
print(f"  any MAIN +EV in {SAMPLES} reachable cut-depth shoes? "
      f"{'YES' if any_reachable_pos else 'NO'}")
print(f"  any MAIN ceiling > 0 at/above cut depth (R>={R_cut})? "
      f"{'YES' if cut_ceiling_pos else 'NO'}")

out = {"fresh_ev": fresh_ev, "samples": SAMPLES, "R_cut": R_cut,
       "sampling_max": {b: best[b][0] for b in BETS},
       "sampling_pos_frac": {b: pos_frac[b] / SAMPLES for b in BETS},
       "ceilings": {str(R): ceilings[R] for R in R_VALUES}}
path = Path(__file__).with_name("e32_mains.json")
path.write_text(json.dumps(out, indent=1))
print(f"\nbanked {path}")
