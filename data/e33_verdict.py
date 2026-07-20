"""E33 verdict: pool insurance shards, sweep the contamination mix, and certify
the order-observer's insurance edge over the perfect composition counter with a
fit/certify split (the E29 honesty pattern: choose the mix by CALIBRATION on a
fit block, report the excess and its z on a fresh certify block).

Usage:  python data/e33_verdict.py [config]      config = sd | 6d (default 6d)
Pools data/e33_{config}_s*.json. Run under CPython or PyPy (analysis only).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ridefree.bj_order import summarize_insurance

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "6d"
MIXES = [0.0, 0.05, 0.10, 0.20, 0.40, 1.0]

shards = sorted(Path(__file__).parent.glob(f"e33_{CONFIG}_s*.json"))
if not shards:
    raise SystemExit(f"no shards e33_{CONFIG}_s*.json found")


def pool(paths):
    """Merge shard results into one summarize-shaped dict, re-indexing shoes
    globally so per-shoe deltas stay distinct across shards."""
    spots, base, pays = [], 0, 2.0
    for p in paths:
        r = json.loads(p.read_text())
        pays = r["insurance_pays"]
        for s in r["spots"]:
            spots.append({**s, "shoe": base + s["shoe"]})
        base += r["shoes"]
    return {"spots": spots, "shoes": base, "insurance_pays": pays}


def choose_mix(summ, tol=0.008):
    """Honest mix = the smallest sweep mix at which the observer is not
    over-confident (realized ten-rate >= predicted - tol at its taken spots).
    Falls back to the best-calibrated mix if none clears the bar."""
    best, best_gap = None, 1e9
    for m in MIXES:
        d = summ["mixes"][m]
        if d["filter"]["bets"] < 20:
            continue
        gap = d["cal_predicted_ten"] - d["cal_realized_ten"]  # +ve = overconfident
        if gap <= tol:
            return m
        if gap < best_gap:
            best, best_gap = m, gap
    return best if best is not None else 0.0


data = {p: json.loads(p.read_text()) for p in shards}
half = (len(shards) + 1) // 2
fit_paths, cert_paths = shards[:half], shards[half:]

print(f"=== E33 insurance verdict [{CONFIG}] : {len(shards)} shards "
      f"({sum(data[p]['shoes'] for p in shards)} shoes) ===")

full = summarize_insurance(pool(shards), MIXES)
print(f"pooled: {full['spots']} insurance spots, bits/spot {full['bits_per_spot']:+.4f}")
c = full["counter"]
print(f"perfect counter: bets {c['bets']} realized {c['realized']:+.2f} "
      f"(cal_real {c['taken_ten']/max(c['bets'],1):.3f})\n")
print(f"{'mix':>5} {'bets':>6} {'realEV':>8} {'cal_pred':>9} {'cal_real':>9} "
      f"{'excess_u':>9} {'exc/shoe':>9} {'z':>6}")
for m in MIXES:
    d = full["mixes"][m]
    print(f"{m:5.2f} {d['filter']['bets']:6d} {d['filter']['realized']:+8.2f} "
          f"{d['cal_predicted_ten']:9.3f} {d['cal_realized_ten']:9.3f} "
          f"{d['excess_realized']:+9.2f} {d['excess_per_shoe']:+9.4f} {d['excess_z']:+6.2f}")

if len(shards) >= 2:
    fit = summarize_insurance(pool(fit_paths), MIXES)
    mix = choose_mix(fit)
    cert = summarize_insurance(pool(cert_paths), MIXES)
    cd = cert["mixes"][mix]
    print(f"\nfit block ({len(fit_paths)} shards) -> honest mix = {mix} "
          f"(fit cal pred {fit['mixes'][mix]['cal_predicted_ten']:.3f} / "
          f"real {fit['mixes'][mix]['cal_realized_ten']:.3f})")
    print(f"CERTIFY block ({len(cert_paths)} shards, {cert['spots']} spots) at mix {mix}:")
    print(f"  observer insurance realized {cd['filter']['realized']:+.2f} "
          f"vs counter {cert['counter']['realized']:+.2f}  "
          f"-> excess {cd['excess_realized']:+.2f} u "
          f"({cd['excess_per_shoe']:+.4f}/shoe, z {cd['excess_z']:+.2f})")
    print(f"  calibration: predicted ten-rate {cd['cal_predicted_ten']:.3f} "
          f"vs realized {cd['cal_realized_ten']:.3f}  |  bits/spot "
          f"{cert['bits_per_spot']:+.4f}")
    # dollar translation: excess is in insurance-STAKE units; stake = 0.5 * main
    print(f"  $ per shoe over counter (main $15, stake $7.50): "
          f"${cd['excess_per_shoe']*0.5*15:+.3f}/shoe")
