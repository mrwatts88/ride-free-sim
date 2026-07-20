"""E34 — M12b Gate-B arm 2: HOLE-CARD PLAY from the order channel, and how it
depends on shuffle strength.

Insurance (E33) proved order info converts to money, but small. The bigger,
human-relevant PLAY signal is hole-card play: knowing the dealer hole card is
worth ~+10%/round (the clairvoyant ceiling here), and a weak shuffle lets the
order observer PREDICT it. Three players share every shoe and differ ONLY in
the dealer-hole prior (composition / filter posterior / true hole), so
order-minus-composition is the pure order play-edge and clairvoyant-minus-
composition is the ceiling it chases.

The headline is the CAPTURE CURVE vs shelf count: at the well-mixed 10-shelf
machine the order posterior is too weak to flip plays (~0), but as the shuffle
weakens the edge turns on -- the "how weak must a shuffle be to be beatable"
number, in real per-round blackjack EV.

Shardable:  python data/e34_holeplay.py [config] [shelves] [shoes] [passes]
  config = sd (single-deck, exact filter) | 6d (six-deck real game)
Banks data/e34_{config}_m{shelves}[p2].json. Pool with data/e34_verdict.py.
Run under PyPy. Seeds: 23.61e9 (sd) / 23.62e9 (6d), shelf-strided.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ridefree.bj_order import deviation_experiment
from ridefree.rules import STANDARD_6D_H17

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "sd"
SHELVES = int(sys.argv[2]) if len(sys.argv) > 2 else 10
SHOES = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
PASSES = int(sys.argv[4]) if len(sys.argv) > 4 else 1

if CONFIG == "sd":
    DECKS, MIN_TAIL, SEED_BASE = 1, 18, 23_610_000_000
elif CONFIG == "6d":
    DECKS, MIN_TAIL, SEED_BASE = 6, 30, 23_620_000_000
else:
    raise SystemExit(f"unknown config {CONFIG!r} (use sd|6d)")

seed = SEED_BASE + SHELVES * 1000 + (0 if PASSES == 1 else 500)

t0 = time.perf_counter()
r = deviation_experiment(
    STANDARD_6D_H17, shelves=SHELVES, shoes=SHOES, seed=seed,
    passes=PASSES, decks=DECKS, min_tail=MIN_TAIL,
)
dt = time.perf_counter() - t0
r.update({"config": CONFIG, "seed": seed, "seconds": dt})

suffix = "" if PASSES == 1 else "p2"
path = Path(__file__).with_name(f"e34_{CONFIG}_m{SHELVES:02d}{suffix}.json")
path.write_text(json.dumps(r))

cap = (100 * r["order_delta_per_round"] / r["clair_delta_per_round"]
       if r["clair_delta_per_round"] else 0.0)
print(f"[{CONFIG}] shelves={SHELVES} passes={PASSES}: {r['rounds']} rounds "
      f"in {dt:.0f}s, surprises={r['surprises']}")
print(f"  comp EV/round {r['comp_per_round']:+.4f}  "
      f"clair delta {r['clair_delta_per_round']:+.4f} (z {r['clair_z']:+.1f})")
print(f"  ORDER delta/round {r['order_delta_per_round']:+.5f} "
      f"(z {r['order_z']:+.2f}, changed {r['order_changed_rate']:.3f}) "
      f"-> captures {cap:.1f}% of the ceiling")
print(f"banked {path}")
