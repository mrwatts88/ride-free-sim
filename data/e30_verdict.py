"""E30 verdict: pool the coup-pricing shards into the rung-3b answer.

Usage: uv run python data/e30_verdict.py [suffix]
Pools data/e30_coup{suffix}_s*.json (default suffix "", i.e. 1-pass shards;
pass "_p2" for the two-pass control pool).
"""

import json
import math
import sys
from pathlib import Path

from ridefree.coup import BETS

suffix = sys.argv[1] if len(sys.argv) > 1 else ""
paths = sorted(Path(__file__).parent.glob(f"e30_coup{suffix}_s*.json"))
if not paths:
    raise SystemExit(f"no shards match e30_coup{suffix}_s*.json")

shards = [json.loads(p.read_text()) for p in paths]
mixes = {s["mix"] for s in shards}
passes = {s["passes"] for s in shards}
assert len(mixes) == 1 and len(passes) == 1, (mixes, passes)
shoes = sum(s["shoes"] for s in shards)
coups = sum(s["coups"] for s in shards)
print(f"{len(shards)} shards, {shoes} shoes, {coups} coups, "
      f"mix {mixes.pop()}, passes {passes.pop()}, "
      f"samples {shards[0]['samples']}, rules {shards[0]['rules']}")

thresholds = list(shards[0]["thresholds"])
for t in thresholds:
    agg = {arm: {b: {"bets": 0, "predicted": 0.0, "realized": 0.0}
                 for b in BETS} for arm in ("filter", "counter")}
    f_real = f_pred = c_real = 0.0
    f_bets = 0
    # per-shoe paired deltas do not pool across shards (not banked per shoe);
    # reconstruct the z from shard-level sums instead: treat each SHARD as a
    # unit (conservative, fewer dof) using its own realized-predicted totals.
    shard_deltas = []
    for s in shards:
        led = s["thresholds"][t]
        for arm in ("filter", "counter"):
            for b in BETS:
                for k in ("bets", "predicted", "realized"):
                    agg[arm][b][k] += led[arm][b][k]
        f_real += led["filter_realized"]
        f_pred += led["filter_predicted"]
        c_real += led["counter_realized"]
        f_bets += led["filter_bets"]
        shard_deltas.append(
            (led["filter_realized"] - led["filter_predicted"]) / s["shoes"])
    m = sum(shard_deltas) / len(shard_deltas)
    if len(shard_deltas) > 1:
        var = sum((d - m) ** 2 for d in shard_deltas) / (len(shard_deltas) - 1)
        z = m * math.sqrt(len(shard_deltas) / var) if var > 0 else 0.0
    else:
        z = float("nan")
    print(f"\n== threshold {t} ==")
    print(f"  filter : {f_bets:5d} bets, realized {f_real:+10.2f} u "
          f"({f_real/shoes:+7.3f}/shoe), predicted {f_pred:+10.2f}, "
          f"shard-z {z:+5.2f}")
    print(f"  counter: realized {c_real:+10.2f} u ({c_real/shoes:+7.3f}/shoe)")
    print(f"  EXCESS (filter - counter): {(f_real-c_real)/shoes:+8.3f} u/shoe")
    for b in BETS:
        f = agg["filter"][b]
        if f["bets"]:
            print(f"    {b:8s}: {f['bets']:5d} bets  "
                  f"realized {f['realized']:+9.2f}  predicted {f['predicted']:+9.2f}  "
                  f"({f['realized']/f['bets']:+7.1%}/bet vs {f['predicted']/f['bets']:+7.1%} claimed)")
