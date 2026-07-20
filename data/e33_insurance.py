"""E33 — M12b Gate-B: blackjack insurance from a known stack through the shelf
machine (the FIRST paradigm-2 order channel to convert into real blackjack
money, where the baccarat flat bet could not — E30/E31).

Per shoe: the observer knows shoe k's full order (the baccarat-like ideal of
E27-E29); the house shelf-shuffles it; every ace-up round to the cut card has
its dealer hole card priced BEFORE the reveal by the assumed-density filter
(E29-gated) -- a single marginal `next_value_probs` query, no Monte Carlo. The
perfect composition counter (tens/cards, the validated take-iff-P>1/3 rule)
rides the same spots; the filter's excess over it is pure order structure, in
real insurance dollars. Rounds resolve through the validated engine to advance
the shoe by exactly what a heads-up basic-strategy player consumes.

Banks the RAW per-spot (model_p, counter_p, hole_ten) triples so the verdict
can sweep the contamination mix and split fit/certify post-hoc (the E31
bank-raw-then-analyze pattern).

Shardable:  python data/e33_insurance.py [config] [shard] [shoes]
  config = sd (single-deck, exact filter) | 6d (six-deck real game)
Banks data/e33_{config}_s{shard:02d}.json. Pool with data/e33_verdict.py.
Run under PyPy:  uv run --python pypy@3.11 --no-project data/e33_insurance.py ...
Seeds: 23.51e9 (single-deck), 23.52e9 (six-deck), shard-strided.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ridefree.bj_order import insurance_experiment, summarize_insurance
from ridefree.rules import STANDARD_6D_H17

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "6d"
SHARD = int(sys.argv[2]) if len(sys.argv) > 2 else 1
SHOES = int(sys.argv[3]) if len(sys.argv) > 3 else 500

if CONFIG == "sd":
    DECKS, MIN_TAIL, SEED_BASE = 1, 18, 23_510_000_000
elif CONFIG == "6d":
    DECKS, MIN_TAIL, SEED_BASE = 6, 30, 23_520_000_000
else:
    raise SystemExit(f"unknown config {CONFIG!r} (use sd|6d)")

seed = SEED_BASE + SHARD * 1000
MIXES = [0.0, 0.05, 0.10, 0.20, 0.40, 1.0]

t0 = time.perf_counter()
res = insurance_experiment(
    STANDARD_6D_H17, shelves=10, shoes=SHOES, seed=seed,
    decks=DECKS, min_tail=MIN_TAIL,
)
dt = time.perf_counter() - t0
res.update({"config": CONFIG, "shard": SHARD, "seed": seed,
            "seconds": dt, "s_per_shoe": dt / SHOES})

path = Path(__file__).with_name(f"e33_{CONFIG}_s{SHARD:02d}.json")
path.write_text(json.dumps(res))

summ = summarize_insurance(res, MIXES)
print(f"[{CONFIG}] shard {SHARD}: {summ['spots']} spots / {SHOES} shoes "
      f"({summ['insured_rate_per_shoe']:.2f}/shoe) in {dt:.0f}s "
      f"({res['s_per_shoe']*1000:.0f} ms/shoe), surprises={res['surprises']}, "
      f"bits/spot {summ['bits_per_spot']:+.3f}")
c = summ["counter"]
print(f"  counter: bets {c['bets']:5d} real {c['realized']:+8.2f} "
      f"cal_real {c['taken_ten']/max(c['bets'],1):.3f}")
for m in MIXES:
    d = summ["mixes"][m]
    print(f"  mix {m:4.2f}: bets {d['filter']['bets']:5d} "
          f"real {d['filter']['realized']:+8.2f} "
          f"cal(pred {d['cal_predicted_ten']:.3f}/real {d['cal_realized_ten']:.3f}) "
          f"excess/shoe {d['excess_per_shoe']:+7.4f} z {d['excess_z']:+5.2f}")
print(f"banked {path}")
