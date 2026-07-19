"""E22 stage 1: derive POG side-EV EORs, gate them, search the pivot-at-(-2)
level-1 unbalanced family, and answer the dual-card question analytically.

    uv run python data/e22_card.py

Inputs: data/e22_eor_p75_s01..05.json — 5 x 2M fresh-seed farm-arm rounds
(RIDE_FREE + PT1, cut_card pen .75, seeds 17.9e9-18.3e9), each carrying the
additive share-deviation regression stats (experiments.run_pog_eor).

Gates before anything is trusted:
  G1  the same regression's MAIN-profit EORs must reproduce E4a's
      calculator-derived RIDE_FREE_EOR (frequency-weighted correlation) —
      the pipeline validates against an independent derivation.
  G2  per-shard EOR stability (sd across 5 independent shards).

Then: hi-lo's betting correlation vs the side EORs (the E20 baseline,
quantifying "hi-lo is not the optimal lammer count"), the pivot-(-2) search
ranked by side BC with each candidate's main BC alongside (Matt's
all-in-one question, priced analytically; the dollars side of that question
was already bounded by the banked bins: the RF positive end is <= ~$7/h).
Stage 2 (e22_curves) certifies the winners head-to-head in live rounds.
"""

import math

from ridefree.counting import HILO_TAGS, RIDE_FREE_EOR
from ridefree.experiments import (
    load_pog_eor_json,
    merge_pog_eors,
    search_unbalanced_level1_pivot,
    solve_pog_eors,
    unbalanced_bc,
)

SHARDS = [f"data/e22_eor_p75_s{i:02d}.json" for i in range(1, 6)]
TEN = 10
W = {r: (16 if r == TEN else 4) for r in range(1, 11)}


def centered(eors):
    m = sum(W[r] * eors[r] for r in W) / 52.0
    return {r: eors[r] - m for r in W}


def main() -> None:
    parts = [load_pog_eor_json(p) for p in SHARDS]
    pooled = merge_pog_eors(parts)
    eors = solve_pog_eors(pooled)
    side, mainv = eors["side"], eors["main"]
    per_shard = [solve_pog_eors(p) for p in parts]

    print(f"pooled {pooled.rounds:,} rounds ({len(parts)} shards), arm "
          f"{pooled.arm}, pen {pooled.penetration:.2f}\n")
    print("--- per-card-removed EORs (tens pinned 0; sd across shards) ---")
    print(f"  {'rank':>4s} {'side EOR':>9s} {'±sd/√5':>8s} {'main EOR':>9s} "
          f"{'±sd/√5':>8s} {'E4a RF EOR':>10s}")
    rf_rel = {r: RIDE_FREE_EOR[r] - RIDE_FREE_EOR[TEN] for r in W}
    for r in range(1, 11):
        ss = [e["side"][r] for e in per_shard]
        ms = [e["main"][r] for e in per_shard]
        sd_s = math.sqrt(sum((v - side[r]) ** 2 for v in ss) / 4) / math.sqrt(5)
        sd_m = math.sqrt(sum((v - mainv[r]) ** 2 for v in ms) / 4) / math.sqrt(5)
        print(f"  {r:>4d} {100 * side[r]:+8.4f}% {100 * sd_s:7.4f}% "
              f"{100 * mainv[r]:+8.4f}% {100 * sd_m:7.4f}% "
              f"{100 * rf_rel[r]:+9.4f}%")

    corr = unbalanced_bc(mainv, RIDE_FREE_EOR)
    print(f"\nG1 main-EOR cross-check vs E4a calculator: weighted corr = "
          f"{corr:+.4f}  {'PASS' if corr > 0.95 else 'FAIL'}")

    print("\n--- how good is each count as a LAMMER count? (BC vs side EORs) ---")
    hilo_bc = unbalanced_bc({r: float(HILO_TAGS[r]) for r in W}, side)
    red7 = {r: float(HILO_TAGS[r]) for r in W}
    red7[7] = red7[7] + 0.5
    red7_bc = unbalanced_bc(red7, side)
    print(f"  hi-lo (the E20/E21 trigger):      {hilo_bc:+.4f}")
    print(f"  Red 7 (Matt's DRILLED count):     {red7_bc:+.4f}  "
          f"(pivot +2 — the side trigger sits 4 off-pivot; stage 2 prices "
          f"the mush)")
    print(f"  perfect linear count:             +1.0000 (by construction)")

    print("\n--- pivot-at-(-2) level-1 unbalanced search (bet-LOW direction: "
          "most NEGATIVE side BC wins; main BC = the dual-card column; "
          "deduped by effective tags) ---")
    res = search_unbalanced_level1_pivot(
        side, imbalance=-2, top=40, secondary_eors=mainv, direction=-1
    )
    seen, shown = set(), []
    for bc, base, bump, sign, bc2 in res:
        tags = dict(base)
        eff = tuple(tags[r] + (0.5 * sign if r == bump else 0)
                    for r in range(1, 10))
        if eff in seen:
            continue
        seen.add(eff)
        shown.append((bc, base, bump, sign, bc2))
        if len(shown) == 8:
            break
    print(f"  {'side BC':>8s} {'main BC':>8s}  tags A..9 (ten -1), bump")
    for bc, base, bump, sign, bc2 in shown:
        tags = dict(base)
        row = "/".join(f"{tags[r]:+d}" for r in range(1, 10))
        print(f"  {bc:+8.4f} {bc2:+8.4f}  {row}  "
              f"{'red' if sign > 0 else 'anti'}-{bump} ({sign:+d} half)")

    # The naive candidate: hi-lo base with the anti-red-7 bump (pivot -2).
    anti = {r: float(HILO_TAGS[r]) for r in W}
    anti[7] = anti[7] - 0.5
    print(f"\n  anti-red-7 (hi-lo base, red 7s -1): side BC "
          f"{unbalanced_bc(anti, side):+.4f}, main BC "
          f"{unbalanced_bc(anti, mainv):+.4f}")
    print("  (pivot -3 is UNREACHABLE in this family — parity: 4*sum-16±2 "
          "is always even; the matched-$100 t=-3 trigger rides as an "
          "off-pivot rung on the -2 card, priced in stage 2)")

    best = shown[0]
    print(f"\nheadline: best pivot-(-2) count side BC {best[0]:+.4f} vs "
          f"hi-lo (division required) {hilo_bc:+.4f} vs Red 7 (drilled, "
          f"off-pivot) {red7_bc:+.4f} -> stage 2 measures the capture gaps "
          f"in $.")


if __name__ == "__main__":
    main()
