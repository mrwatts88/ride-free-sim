"""E31 — M12b rung 3c (the cheap diagnostic): the contamination-mix sweep
that isolates the Dragon-7 / Panda-8 lead's mechanism.

E30 left one live signal: the filter's D7/P8 bets REALIZE positive (+7-10%/bet)
while their CLAIMED EV is deeply negative (-8 to -10%/bet). The suspected cause
(STATUS, EXPERIMENTS E30): the value-level contamination floor `mix` is applied
to `next_value_probs()` at EVERY sampled card, so a JOINT multi-card claim gets
shrunk ~ (1-mix)^cards toward composition -- at mix 0.40 over 5 cards that is
0.6^5 ~= 0.08, crushing the claim, while realized profit (settled from the true
coup) keeps the full signal.

This driver re-prices the SAME process at several mixes. Two readouts:
  (1) MECHANISM -- does the filter's D7/P8 PREDICTED %/bet rise toward its
      realized %/bet as mix -> 0? (a structural, low-variance effect; unpaired
      shoes across mixes are fine for it -- the aggregate predicted mean is a
      mean over thousands of bets and the mix swing is huge next to shoe noise);
  (2) SELECTION -- does de-shrinking sharpen which coups the filter bets, i.e.
      does the realized filter-minus-counter D7/P8 excess change? (high variance;
      a first read only -- the certified number is item 3's scaled replication).

REALIZED profit is mix-independent for a FIXED fired-bet set; only the filter's
SELECTION shifts with mix, and the counter's selection is fully mix-independent,
so the counter D7/P8 line is a fixed baseline across every mix.

Shardable: python data/e31_mixsweep.py [shard] [shoes] [samples] [mix]
Banks data/e31_mix{mix}_s{shard:02d}.json. Pool with data/e31_verdict.py.
Seeds: 23.3e9 block (shard- and mix-strided so each mix is an independent
sample -- distinct stacks, no accidental cross-mix pairing). Run under PyPy
(E28's sanctioned accelerator): PYTHONPATH=src uv run --python pypy@3.11
--no-project data/e31_mixsweep.py ...
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ridefree.baccarat import EZ_BACCARAT_8D
from ridefree.coup import coup_experiment

SHARD = int(sys.argv[1]) if len(sys.argv) > 1 else 1
SHOES = int(sys.argv[2]) if len(sys.argv) > 2 else 4
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 120
MIX = float(sys.argv[4]) if len(sys.argv) > 4 else 0.40

# Mix- and shard-strided so no two (mix, shard) share a stack sequence: the
# mix occupies the ..._0MMM slot (MIX*1000), the shard the ...SS_000 slot.
seed = 23_300_000_000 + SHARD * 100_000 + int(round(MIX * 1000))
t0 = time.perf_counter()
out = coup_experiment(
    EZ_BACCARAT_8D,
    shelves=10,
    shoes=SHOES,
    seed=seed,
    passes=1,
    samples=SAMPLES,
    thresholds=(0.02, 0.05, 0.10),
    adf_mix=MIX,
)
dt = time.perf_counter() - t0
out.update({"shard": SHARD, "seed": seed, "mix": MIX, "passes": 1,
            "rules": "EZ_BACCARAT_8D", "shelves": 10,
            "seconds": dt, "s_per_shoe": dt / SHOES})

mixtag = f"{MIX:.2f}".replace(".", "")
path = Path(__file__).with_name(f"e31_mix{mixtag}_s{SHARD:02d}.json")
path.write_text(json.dumps(out, indent=1))
print(f"mix {MIX} shard {SHARD}: {out['coups']} coups / {SHOES} shoes "
      f"in {dt:.0f}s ({out['s_per_shoe']:.0f}s/shoe)")
for t, led in out["thresholds"].items():
    fd = led["filter"]["dragon7"]
    fp = led["filter"]["panda8"]
    d7 = f"D7 {fd['bets']}b {fd['realized']/max(fd['bets'],1):+.1%}real {fd['predicted']/max(fd['bets'],1):+.1%}clm"
    p8 = f"P8 {fp['bets']}b {fp['realized']/max(fp['bets'],1):+.1%}real {fp['predicted']/max(fp['bets'],1):+.1%}clm"
    print(f"  t={t}: {d7} | {p8}")
print(f"banked {path}")
