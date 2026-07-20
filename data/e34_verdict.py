"""E34 verdict: the hole-card-play capture curve vs shuffle strength.

Prints, per config, the order player's per-round play edge and what fraction of
the clairvoyant (perfect-hole) ceiling it captures, across shelf counts -- the
"how weak must a shuffle be to be beatable" table.

Usage:  python data/e34_verdict.py
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(config):
    rows = []
    for p in HERE.glob(f"e34_{config}_m*.json"):
        m = re.match(rf"e34_{config}_m(\d+)(p2)?\.json", p.name)
        shelves = int(m.group(1))
        passes = 2 if m.group(2) else 1
        r = json.loads(p.read_text())
        rows.append((shelves, passes, r))
    # order by effective mixing: 1-pass by shelves, then the 2-pass null last
    rows.sort(key=lambda t: (t[1], t[0]))
    return rows


for config in ("sd", "6d"):
    rows = load(config)
    if not rows:
        continue
    label = "single-deck (exact filter)" if config == "sd" else "six-deck (real game)"
    print(f"\n=== E34 hole-card-play capture curve [{config}] : {label} ===")
    print(f"{'shuffle':>10} {'rounds':>7} {'comp EV':>8} {'clair(ceil)':>11} "
          f"{'ORDER edge':>10} {'z':>6} {'capture':>8} {'changed':>8}")
    for shelves, passes, r in rows:
        cap = (100 * r["order_delta_per_round"] / r["clair_delta_per_round"]
               if r["clair_delta_per_round"] else 0.0)
        name = f"{shelves}sh x{passes}" if passes > 1 else f"{shelves} shelf"
        print(f"{name:>10} {r['rounds']:>7} {r['comp_per_round']:>+8.4f} "
              f"{r['clair_delta_per_round']:>+11.4f} "
              f"{r['order_delta_per_round']:>+10.5f} {r['order_z']:>+6.2f} "
              f"{cap:>7.1f}% {r['order_changed_rate']:>8.3f}")
    print("  (ORDER edge = order-minus-composition per-round EV; ceiling = "
          "perfect-hole play; capture = order/ceiling)")
