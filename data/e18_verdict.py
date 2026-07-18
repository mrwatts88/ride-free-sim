"""E18 verdict: the locked crouch15-2r card — bin prediction vs live play.

Two independent paths to the same number:
1. PREDICTION — arithmetic over the banked E17 bins (48M rounds), with the
   insurance overlay stripped below the card's threshold. The insurance term
   is composition-EXACT there, so it is a ceiling.
2. LIVE — the data/e18_run.py shards: the literal human card played end to
   end (chart play, bet by RC, sit out at the leave line, always-insure at
   the threshold). This measures what the exact-insurance bins cannot: the
   realized value of the human insurance rule.

The chart-only comparison is the like-for-like gate (both sides play
identical rounds); insurance is reported as realized-vs-ceiling capture.

Card (slid scale, shift +18): start +6, walk at 0, $100 at 18, $200+insure
at 22. Pivot-scale equivalents used against the bins: leave <= -18, $100 at
>= 0, $200+ins at >= +4, floor from -17.

Usage: uv run python data/e18_verdict.py [variant]
  variant: "locked" (default, shards e18_live_s*.json) or "playall"
  (E18b never-leave shards, e18b_live_s*.json).
"""

import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ridefree.experiments import (  # noqa: E402
    load_count_curves_json,
    merge_count_curves,
)

UNIT = 10.0
PACE = 200.0
RUIN = 0.05
MIN_BIN_ROUNDS = 2_000
HERE = os.path.dirname(os.path.abspath(__file__))

# The locked card in pivot scale (bins) — floor $15 = 1.5 units.
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "locked"
if VARIANT == "playall":  # E18b: never leave — the floor extends all the way down
    STEPS = ((-99, 1.5), (0, 10.0), (4, 20.0))
    SHARD_GLOB = "e18b_live_s*.json"
elif VARIANT == "locked":
    STEPS = ((-17, 1.5), (0, 10.0), (4, 20.0))
    SHARD_GLOB = "e18_live_s*.json"
else:
    sys.exit(f"unknown variant {VARIANT!r}")
INS_FLOOR = 4

# ---- prediction from the banked bins --------------------------------------

paths = sorted(glob.glob(os.path.join(HERE, "e17_h17_ins_p75_s*.json")))
data = merge_count_curves([load_count_curves_json(p) for p in paths])
N_BANK = data.rounds
bins = data.by_signal["red7_rc"]


def bet_at(k: int) -> float:
    bet = 0.0
    for lo, units in STEPS:
        if k >= lo:
            bet = units
        else:
            break
    return bet


chart_ev = chart_se2 = ins_ev = avg_bet = 0.0
freq = {"0": 0.0, "15": 0.0, "100": 0.0, "200": 0.0}
e2 = 0.0
for k, b in sorted(bins.items()):
    if b.rounds < MIN_BIN_ROUNDS:
        continue
    f = b.rounds / N_BANK
    u = bet_at(k)
    m_chart = (b.profit - b.ins_profit) / b.rounds
    chart_ev += f * u * m_chart
    chart_se2 += (f * u) ** 2 * b.var / b.rounds
    if k >= INS_FLOOR:
        ins_ev += f * u * (b.ins_profit / b.rounds)
    avg_bet += f * u
    e2 += f * u * u * (b.profit_sq / b.rounds)
    freq[f"{u * UNIT:g}" if u > 0 else "0"] += f
var_total = max(e2 - (chart_ev + ins_ev) ** 2, 0.0)

pred_chart = chart_ev * UNIT * PACE
pred_chart_se = math.sqrt(chart_se2) * UNIT * PACE
pred_ins = ins_ev * UNIT * PACE
pred_total = pred_chart + pred_ins

# ---- live shards -----------------------------------------------------------

shards = sorted(glob.glob(os.path.join(HERE, SHARD_GLOB)))
if not shards:
    sys.exit(f"no {SHARD_GLOB} shards found — run data/e18_run.py first")
n = 0
sum_p = sum_p2 = sum_pni = sum_pni2 = sum_bet = ins_profit = 0.0
rungs: dict[str, int] = {}
seeds = []
for path in shards:
    with open(path) as fh:
        d = json.load(fh)
    seeds.append(d["seed"])
    n += d["rounds"]
    sum_p += d["sum_profit"]
    sum_p2 += d["sum_profit_sq"]
    sum_pni += d["sum_profit_no_ins"]
    sum_pni2 += d["sum_profit_no_ins_sq"]
    sum_bet += d["sum_bet"]
    ins_profit += d["ins_profit"]
    for key, count in d["rung_rounds"].items():
        rungs[key] = rungs.get(key, 0) + count

live_mean = sum_p / n
live_var = sum_p2 / n - live_mean**2
live_total = live_mean * PACE
live_total_se = math.sqrt(live_var / n) * PACE
pni_mean = sum_pni / n
pni_var = sum_pni2 / n - pni_mean**2
live_chart = pni_mean * PACE
live_chart_se = math.sqrt(pni_var / n) * PACE
live_ins = ins_profit / n * PACE

# ---- report ----------------------------------------------------------------

z_chart = (live_chart - pred_chart) / math.sqrt(live_chart_se**2 + pred_chart_se**2)
n0 = (live_var / live_mean**2) / PACE if live_mean > 0 else float("inf")
bank = (live_var / (2 * live_mean)) * math.log(1 / RUIN) if live_mean > 0 else float("inf")

tag = "E18 — crouch15-2r" if VARIANT == "locked" else "E18b — crouch15-2r NEVER-LEAVE"
walk = "walk at 0" if VARIANT == "locked" else "never walk"
print(f"{tag} certification: {n:,} live rounds ({len(shards)} shards, "
      f"seeds {min(seeds)}..{max(seeds)}) vs {N_BANK:,} banked rounds")
print()
print(f"card (slid scale): start +6 | {walk} | $100 at 18 | $200 + insure at 22")
print()
print(f"{'':24s} {'prediction (bins)':>18s} {'live (literal card)':>20s}")
print(f"{'chart-only $/h':24s} {pred_chart:+11.2f} ±{pred_chart_se:4.2f} "
      f"{live_chart:+13.2f} ±{live_chart_se:4.2f}   z = {z_chart:+.2f}")
print(f"{'insurance $/h':24s} {pred_ins:+11.2f} (ceiling) {live_ins:+13.2f} "
      f"(realized, {100 * live_ins / pred_ins:.0f}% capture)")
print(f"{'TOTAL $/h':24s} {pred_total:+11.2f} (ceiling) {live_total:+13.2f} "
      f"±{live_total_se:4.2f}")
print()
print(f"{'rung occupancy':24s} {'bins':>10s} {'live':>10s}")
for key in ("0", "15", "100", "200"):
    lf = rungs.get(key, 0) / n
    se = math.sqrt(lf * (1 - lf) / n)
    z = (lf - freq[key]) / se if se else 0.0
    label = "sit-out" if key == "0" else f"${key}"
    print(f"  {label:22s} {100 * freq[key]:9.2f}% {100 * lf:9.2f}%   z = {z:+.2f}")
print()
print(f"avg bet: bins ${avg_bet * UNIT:.2f}, live ${sum_bet / n:.2f}; "
      f"live per-round sigma ${math.sqrt(live_var):.1f}")
print(f"live-based sizing at {PACE:g} r/h: N0 {n0:,.0f}h, bankroll "
      f"${bank / 1000:.1f}k at {100 * RUIN:g}% RoR")
