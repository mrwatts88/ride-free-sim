"""E31 verdict: the contamination-mix sweep, D7/P8 focus.

Pools each mix's shards -- e31_mix{tag}_s*.json for the de-shrunk runs, plus the
existing E30 mix-0.40 shards (e30_coup_s*.json) as the calibrated-instrument
baseline -- and tables, per threshold, the filter's Dragon-7 / Panda-8:
  - bets fired, realized %/unit, CLAIMED %/unit  (mechanism: claim -> realized
    as mix -> 0), and
  - the counter's D7/P8 (mix-independent baseline) and the realized
    filter-minus-counter D7/P8 excess per shoe (selection read; high variance).

Usage: python data/e31_verdict.py
"""

import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
D7P8 = ("dragon7", "panda8")


def load(pattern):
    return [json.loads(Path(p).read_text()) for p in sorted(glob.glob(str(HERE / pattern)))]


# (mix, shards) sources, low mix first
sources = []
for tag, mix in [("000", 0.0), ("005", 0.05)]:
    shards = load(f"e31_mix{tag}_s*.json")
    if shards:
        sources.append((mix, shards))
e30 = load("e30_coup_s*.json")
if e30:
    sources.append((0.40, e30))
sources.sort(key=lambda s: s[0])

if not sources:
    raise SystemExit("no shards found (run e31_launch.py first)")

thresholds = list(sources[0][1][0]["thresholds"])


def agg_bet(shards, t, arm, bet):
    bets = real = pred = 0.0
    for s in shards:
        led = s["thresholds"][t][arm][bet]
        bets += led["bets"]; real += led["realized"]; pred += led["predicted"]
    return bets, real, pred


def pct(x, n):
    return f"{x / n:+7.1%}" if n else "    n/a"


for t in thresholds:
    print(f"\n============ threshold {t} ============")
    print(f"{'mix':>5} {'shoes':>5} | {'arm':>7} {'bet':>7} {'bets':>6} "
          f"{'realiz/u':>9} {'claim/u':>9}")
    for mix, shards in sources:
        shoes = sum(s["shoes"] for s in shards)
        # filter D7/P8
        for bet in D7P8:
            b, r, p = agg_bet(shards, t, "filter", bet)
            print(f"{mix:>5} {shoes:>5} | {'filter':>7} {bet:>7} {int(b):>6} "
                  f"{pct(r, b):>9} {pct(p, b):>9}")
        # combined filter and counter, per shoe excess
        fb = fr = fp = 0.0
        cb = cr = 0.0
        for bet in D7P8:
            b, r, p = agg_bet(shards, t, "filter", bet)
            fb += b; fr += r; fp += p
            b2, r2, _ = agg_bet(shards, t, "counter", bet)
            cb += b2; cr += r2
        print(f"{'':>5} {'':>5} |   D7+P8 filter {int(fb):>6} {pct(fr, fb):>9} "
              f"{pct(fp, fb):>9}   ->  {fr/shoes:+6.2f} u/shoe")
        print(f"{'':>5} {'':>5} |   D7+P8 counter {int(cb):>5} {pct(cr, cb):>9} "
              f"{'(exact)':>9}   ->  {cr/shoes:+6.2f} u/shoe   "
              f"EXCESS {(fr-cr)/shoes:+6.2f} u/shoe")
    print()

print("\nMechanism: watch filter D7/P8 CLAIM/u rise toward its REALIZED/u as mix")
print("falls (the joint claim de-shrinks). Selection/excess is high-variance at")
print("this scale -- a first read, not the certified number (that is item 3).")
