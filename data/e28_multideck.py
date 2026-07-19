"""E28 — M12b rung 2: the order channel under copy ambiguity (multi-deck).

The load-bearing question for hand-shuffled multi-deck baccarat: rung 1 showed
a huge order channel on a single distinct-card deck, but an 8-deck shoe hides
each rank+suit behind 8 indistinguishable copies. Does that ambiguity destroy
the edge? This sweeps the composition-fair value proposition (perfect counter
nets exactly zero by construction) through the multi-deck particle-filter
posterior across deck counts and shuffle passes, so the decay of the channel
with copies (decks) and with mixing (passes) is measured, not assumed.

Every number is realized profit that a perfect card counter could NOT earn —
pure order structure surviving the honest observation model (observer knows
shoe k at rank+suit resolution, cannot tell copies apart). The E17 gate rides
along: realized == posterior-predicted within CI (`z`).

Usage: uv run python data/e28_multideck.py [particles] [scale]
Seeds: 22.9e9 block. Banks data/e28_multideck.json.
"""

import json
import math
import sys
import time
from pathlib import Path

from ridefree.posterior import multideck_proposition_experiment as mpe

PARTICLES = int(sys.argv[1]) if len(sys.argv) > 1 else 120
SCALE = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

# (decks, passes, base_trials) — trials shrink as n grows (cost ~ n * particles).
CONFIGS = [
    (1, 1, 600),
    (2, 1, 300),
    (3, 1, 160),
    (4, 1, 100),
    (2, 2, 300),  # the manufacturer's fix at 2 decks
]

results = {"particles": PARTICLES, "scale": SCALE, "target_value": 8, "rows": []}
print("decks passes   n  trials  ms/shoe  bets/shoe  edge/bet   u/shoe   bits/shoe    z")
for i, (decks, passes, base) in enumerate(CONFIGS):
    trials = max(20, int(base * SCALE))
    seed = 22_900_000_001 + i
    t0 = time.perf_counter()
    r = mpe(
        decks=decks,
        shelves=10,
        trials=trials,
        seed=seed,
        passes=passes,
        particles=PARTICLES,
        target_value=8,
    )
    dt = time.perf_counter() - t0
    row = {
        "decks": decks,
        "passes": passes,
        "n": r.info["n"],
        "trials": trials,
        "seed": seed,
        "ms_per_shoe": dt / trials * 1000,
        "bets_per_shoe": r.bets / trials,
        "edge_per_bet": r.edge_per_bet,
        "units_per_shoe": r.realized / trials,
        "bits_per_shoe": r.bits_per_shoe,
        "z": r.z,
    }
    results["rows"].append(row)
    print(
        f"{decks:5d} {passes:6d} {r.info['n']:4d} {trials:6d} "
        f"{row['ms_per_shoe']:8.0f} {row['bets_per_shoe']:9.2f} "
        f"{row['edge_per_bet']:+9.4f} {row['units_per_shoe']:+8.3f} "
        f"{row['bits_per_shoe']:+10.3f} {row['z']:+6.2f}"
    )

out = Path(__file__).with_name("e28_multideck.json")
out.write_text(json.dumps(results, indent=1))
worst_z = max(abs(row["z"]) for row in results["rows"])
print(f"\nBanked {out}")
print(f"worst |z| (predicted-vs-realized gate) = {worst_z:.2f}")
