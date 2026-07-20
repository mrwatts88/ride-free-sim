"""E30 — M12b rung 3b: real-paytable baccarat coup pricing from a known
8-deck stack through the shelf machine (the first game-currency number of
paradigm 2's Track A).

Per shoe: the observer knows shoe k's full order (the baccarat-like ideal,
as E27/E28); the house shelf-shuffles it; every coup to the cut card is
priced BEFORE dealing by the assumed-density filter (E29-gated) via coupled
control-variate sampling, split-sample selected/predicted (winner's curse
excluded by construction), and settled through the validated M9 engine at
EZ Baccarat paytables. The perfect counter (exact composition EVs) rides the
same shoes: the filter's excess over it is pure order structure, priced in
REAL bet units for the first time.

Shardable: python data/e30_coup.py [shard] [shoes] [samples] [mix] [passes]
Banks data/e30_coup_s{shard:02d}.json (passes=2 banks with a p2 suffix).
Pool with data/e30_verdict.py. Seeds: 23.2e9 block (shard-strided).
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ridefree.baccarat import EZ_BACCARAT_8D
from ridefree.coup import coup_experiment

SHARD = int(sys.argv[1]) if len(sys.argv) > 1 else 1
SHOES = int(sys.argv[2]) if len(sys.argv) > 2 else 8
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 120
MIX = float(sys.argv[4]) if len(sys.argv) > 4 else None
PASSES = int(sys.argv[5]) if len(sys.argv) > 5 else 1

if MIX is None:
    e29 = Path(__file__).with_name("e29_adf.json")
    MIX = json.loads(e29.read_text())["mix_chosen"] if e29.exists() else 0.25

seed = 23_200_000_000 + SHARD * 1000 + (0 if PASSES == 1 else 500)
t0 = time.perf_counter()
out = coup_experiment(
    EZ_BACCARAT_8D,
    shelves=10,
    shoes=SHOES,
    seed=seed,
    passes=PASSES,
    samples=SAMPLES,
    thresholds=(0.02, 0.05, 0.10),
    adf_mix=MIX,
)
dt = time.perf_counter() - t0
out.update({"shard": SHARD, "seed": seed, "mix": MIX, "passes": PASSES,
            "rules": "EZ_BACCARAT_8D", "shelves": 10,
            "seconds": dt, "s_per_shoe": dt / SHOES})

suffix = "" if PASSES == 1 else "_p2"
path = Path(__file__).with_name(f"e30_coup{suffix}_s{SHARD:02d}.json")
path.write_text(json.dumps(out, indent=1))
print(f"shard {SHARD} (passes={PASSES}): {out['coups']} coups / {SHOES} shoes "
      f"in {dt:.0f}s ({out['s_per_shoe']:.0f}s/shoe), mix {MIX}")
for t, led in out["thresholds"].items():
    print(f"  t={t}: filter bets {led['filter_bets']:5d} "
          f"realized {led['filter_realized']:+9.2f} predicted {led['filter_predicted']:+9.2f} "
          f"z {led['z']:+6.2f}  counter {led['counter_realized']:+8.2f}  "
          f"excess/shoe {led['excess_per_shoe']:+7.3f}")
print(f"banked {path}")
