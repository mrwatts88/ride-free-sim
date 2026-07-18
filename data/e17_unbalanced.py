"""E17 — the crouch played from unbalanced RUNNING counts (no division).

Loads the banked multi-signal curves (data/e17_*.json — one pass, every
signal binned on the SAME rounds, so comparisons carry no cross-run noise)
and prices fixed-integer running-count cards against the hi-lo true-count
reference from the same pass. Run:

    uv run python data/e17_unbalanced.py

Threshold derivation (analytic, nothing fit to this data): for a hi-lo-scale
count with per-deck imbalance s and pivot-zeroed IRC = -s*decks, the running
count satisfies RC ~= d_rem * (TC - s). At the pivot (TC = s) a fixed RC
threshold is depth-EXACT; off-pivot thresholds are evaluated at a nominal
d_rem = 3.5 decks and shown with a sensitivity grid (the honest price of
depth blur — especially the leave threshold, far below the pivot, where a
fixed number confounds fresh shoes with bad ones).

Red 7 (s=+2, IRC -12): the pivot IS the crouch's jump threshold, so the
money decision is exact at every depth. KO (s=+4, IRC -24): pivot at TC+4 —
every crouch threshold is off-pivot; its leave threshold collides with the
fresh-shoe IRC and is omitted as unplayable. half7 = deterministic 7s-at-
+0.5 (ideal red-7 without color noise): same card as red 7.

Caveat on record: the banked arm takes composition-exact insurance in every
system including the hi-lo reference — consistent across rows (retention is
fair) but slightly optimistic absolutely; the RC card's human insurance rule
is "insure when the $150 bet is out". corr column is corr(bet, hi-lo TC),
estimated from within-bin mean TCs.
"""

import glob
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ridefree.experiments import (  # noqa: E402
    load_count_curves_json,
    merge_count_curves,
)

UNIT = 10.0  # $ per ramp unit ($10-$200 table, the chosen E16 operating point)
PACE = 200.0  # heads-up weekday
RUIN = 0.05
MIN_BIN_ROUNDS = 2_000

HERE = os.path.dirname(os.path.abspath(__file__))
paths = sorted(glob.glob(os.path.join(HERE, "e17_h17_ins_p75_s*.json")))
if not paths:
    sys.exit("no banked e17 shards found — run the E17 countcurve shards first")
data = merge_count_curves([load_count_curves_json(p) for p in paths])
N = data.rounds

# name -> ((min_bin, units), ...): units of the highest min_bin <= bin, 0 below.
CARDS = {
    # the hi-lo TC reference: E16's chosen card, priced on this pass's bins
    ("hilo_tc", "TC crouch + leave (E16 card)"): ((-1, 1), (2, 10), (3, 15), (4, 20)),
    # Red 7, pivot-zeroed IRC -12: jump at RC>=0 is the depth-exact pivot test
    ("red7_rc", "pivot card, play-all"): ((-99, 1), (0, 10), (2, 15), (5, 20)),
    ("red7_rc", "pivot card + leave RC<=-16"): ((-15, 1), (0, 10), (2, 15), (5, 20)),
    ("half7_rc", "ideal half-7, same card"): ((-15, 1), (0, 10), (2, 15), (5, 20)),
    # KO, IRC -24, pivot TC+4: all crouch thresholds off-pivot (d_rem 3.5)
    ("ko_rc", "play-all (leave unplayable)"): ((-99, 1), (-7, 10), (-5, 15), (-2, 20)),
}

# sensitivity grids printed after the main table
SENS_JUMP = {("red7_rc", j): ((-15, 1), (j, 10), (j + 2, 15), (j + 5, 20))
             for j in (-2, -1, 0, 1)}
SENS_LEAVE = {("red7_rc", lv): ((lv + 1, 1), (0, 10), (2, 15), (5, 20))
              for lv in (-18, -16, -14, -12)}


def bet_at(steps, k: int) -> float:
    bet = 0.0
    for lo, units in steps:
        if k >= lo:
            bet = units
        else:
            break
    return bet


def price(signal: str, steps):
    bins = data.by_signal[signal]
    ev = e2 = avg_bet = action = 0.0
    s_t = ss_t = x_bt = ss_b = 0.0
    for k, b in sorted(bins.items()):
        if b.rounds < MIN_BIN_ROUNDS:
            continue
        f = b.rounds / N
        u = bet_at(steps, k)
        m = b.ev
        ev += f * u * m
        e2 += f * u * u * (b.profit_sq / b.rounds)
        avg_bet += f * u
        if u > 0:
            action += f
        tc = b.tc_sum / b.rounds
        s_t += f * tc
        ss_t += f * (tc * tc + 1.0 / 12.0)
        x_bt += f * u * tc
        ss_b += f * u * u
    var = max(e2 - ev * ev, 0.0)
    vt = ss_t - s_t * s_t
    vb = ss_b - avg_bet * avg_bet
    corr = (x_bt - avg_bet * s_t) / math.sqrt(vt * vb) if vt > 0 and vb > 0 else 0.0
    return ev, var, avg_bet, action, corr


def row(ev, var, avg_bet, action, corr, ref_ev=None):
    dollars = ev * UNIT * PACE
    sigma = math.sqrt(var * PACE) * UNIT
    n0 = (var / (ev * ev)) / PACE if ev > 0 else float("inf")
    bank = (var / (2 * ev)) * math.log(1 / RUIN) * UNIT if ev > 0 else float("inf")
    keep = f"{100 * ev / ref_ev:6.1f}%" if ref_ev else "   ref"
    n0_txt = f"{n0:6.0f}h" if math.isfinite(n0) else "     —"
    bank_txt = f"${bank / 1000:5.1f}k" if math.isfinite(bank) else "     —"
    return (f"{avg_bet * UNIT:6.1f} {100 * action:5.1f}% {corr:+5.2f} "
            f"{dollars:+8.2f} {sigma:7.0f} {n0_txt} {bank_txt} {keep}")


print(f"E17 — unbalanced running-count crouch, H17 6d pen "
      f"{data.penetration:.2f}, ${UNIT:g} units, {PACE:g} r/h, "
      f"{N:,} rounds banked ({len(paths)} shards, arm {data.arm})")
print()
print(f"{'system / card':<38s} {'avg$':>6s} {'act%':>6s} {'corr':>5s} "
      f"{'$/h':>8s} {'σ/h':>7s} {'N0':>7s} {'bank':>7s} {'keep':>7s}")
ref_ev = None
for (signal, label), steps in CARDS.items():
    ev, var, avg_bet, action, corr = price(signal, steps)
    if ref_ev is None:
        ref_ev = ev
    print(f"{signal + ' — ' + label:<38s} "
          f"{row(ev, var, avg_bet, action, corr, None if signal == 'hilo_tc' else ref_ev)}")
print()

print("red 7 jump-threshold sensitivity (leave fixed at RC<=-16; keep vs TC ref):")
for (signal, j), steps in sorted(SENS_JUMP.items(), key=lambda kv: kv[0][1]):
    ev, var, avg_bet, action, corr = price(signal, steps)
    print(f"  jump at RC>={j:+d}: {row(ev, var, avg_bet, action, corr, ref_ev)}")
print()
print("red 7 leave-threshold sensitivity (jump fixed at RC>=0):")
for (signal, lv), steps in sorted(SENS_LEAVE.items(), key=lambda kv: kv[0][1]):
    ev, var, avg_bet, action, corr = price(signal, steps)
    print(f"  leave at RC<={lv:+d}: {row(ev, var, avg_bet, action, corr, ref_ev)}")
print()
print("notes: 'keep' = fraction of the hi-lo TC reference's $/h retained,")
print("same rounds, same arm. Red 7's jump (RC>=0 <=> TC>=+2) is depth-exact;")
print("rungs/leave are the blurred part. half7 vs red7 isolates color noise.")
