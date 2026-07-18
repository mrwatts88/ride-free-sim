"""E16 — classic blackjack next door: the cover-vs-money ledger.

No simulation here (the E4c/E12/E14 pattern): loads the banked per-TC curves
(data/e16_*.json, shards pooled) and prices any betting pattern in real
dollars. Every knob a human would turn is in the CONFIG block. Run:

    uv run python data/e16_ledger.py

Model notes (idealizations on record):
- Per OBSERVED round: a bet of 0 is a sit-out/back-count round — cards still
  flow (someone else plays), time still passes. Hours = observed rounds/pace.
- Profit is exactly linear in the bet, so ledger arithmetic over banked bins
  equals a live simulation of the same ramp (verified via `cli ramp`).
- Rounds treated as independent for variance (within-shoe TC correlation
  makes true session sigma slightly higher; the live ramp run measures it).
- Ramps are keyed on the ROUNDED integer TC bin (bin +2 = tc in [1.5, 2.5));
  the matching live `cli ramp` spec uses thresholds at k-0.5.
- corr(bet, TC) uses within-bin mean TCs (+1/12 bin-width variance): a
  planning-grade detectability index, exact version comes from `cli ramp`.
"""

import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ridefree.experiments import load_tc_curve_json, merge_tc_curves  # noqa: E402

# --- CONFIG ------------------------------------------------------------------

GAME = sys.argv[1] if len(sys.argv) > 1 else "h17"  # h17 (assumed) | s17 (bracket)
PEN = sys.argv[2] if len(sys.argv) > 2 else "p75"  # p75 | p80 | p70 (banked shards)
UNIT = 25.0  # $ per ramp unit ($25-$2000 table; set 10.0 or 15.0 for the others)
ROUNDS_PER_HOUR = 100  # heads-up ~200-250, 2-3 players ~100, full table ~60
RUIN = 0.05  # bankroll sized for this risk of ruin
MIN_BIN_ROUNDS = 2_000  # ignore bins thinner than this (pooled)

# Betting patterns: name -> ((min_bin, units), ...). Bet at TC bin k is the
# units of the highest min_bin <= k; below the lowest step the bet is 0
# (leave / sit out / back-count). Units are multiples of UNIT (1 = table min).
RAMPS = {
    "flat (pure camo)": ((-99, 1),),
    "flat, exit tc<=-1": ((0, 1),),
    "1-2, exit tc<=-2": ((-1, 1), (1, 2)),
    "1-4 mild": ((-99, 1), (1, 2), (2, 3), (3, 4)),
    "1-8 classic": ((-99, 1), (1, 2), (2, 4), (3, 6), (4, 8)),
    "1-8, exit tc<=-1": ((0, 1), (1, 2), (2, 4), (3, 6), (4, 8)),
    "1-12 aggressive": ((-99, 1), (1, 3), (2, 6), (3, 9), (4, 12)),
    "backcount, 8u at tc>=+1": ((1, 8),),
    "backcount, 8u at tc>=+2": ((2, 8),),
}

# Arms: which banked curve carries the playing skill.
#   basic   = chart play only, never insures
#   ins     = + composition-exact insurance (human proxy: insurance index)
#   ceiling = ins + composition-exact deviations (bound for "all the indexes")
ARMS = ("basic", "ins", "ceiling")

# --- data loading ------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_curve(arm: str):
    paths = sorted(glob.glob(os.path.join(HERE, f"e16_{GAME}_{arm}_{PEN}_s*.json")))
    if not paths:
        return None
    return merge_tc_curves([load_tc_curve_json(p) for p in paths]), len(paths)


def _load_dev():
    paths = sorted(glob.glob(os.path.join(HERE, f"e16_{GAME}_dev_{PEN}_s*.json")))
    bins: dict[int, list] = {}
    rounds = 0
    for p in paths:
        with open(p) as f:
            payload = json.load(f)
        rounds += payload["rounds"]
        for k, (n, d, d2) in payload["by_tc"].items():
            acc = bins.setdefault(int(k), [0, 0.0, 0.0])
            acc[0] += n
            acc[1] += d
            acc[2] += d2
    return bins, rounds, len(paths)


basic, n_basic = _load_curve("basic") or (None, 0)
ins, n_ins = _load_curve("ins") or (None, 0)
dev_bins, dev_rounds, n_dev = _load_dev()

if ins is None:
    sys.exit(f"missing banked ins curve for {GAME}/{PEN} — run the E16 shards first")
if basic is None:
    print(f"NOTE: no basic-arm shards banked for {GAME}/{PEN}; "
          "basic rows mirror the ins arm.\n")
    basic, n_basic = ins, 0

KEYS = sorted(set(basic.bins) & set(ins.bins))


def _row(curve, k):
    b = curve.bins[k]
    return b.rounds, b.ev, b.profit_sq / b.rounds, b.tc_sum / b.rounds


def dev_delta(k: int) -> tuple[float, float]:
    """(mean paired deviation value, its se) at TC bin k; 0 if unbanked."""
    acc = dev_bins.get(k)
    if not acc or acc[0] < 200:
        return 0.0, 0.0
    n, d, d2 = acc
    m = d / n
    var = max(d2 / n - m * m, 0.0)
    return m, math.sqrt(var / n)


def arm_bins(arm: str) -> dict[int, tuple[float, float, float, float]]:
    """bin -> (freq, ev/round, E[profit^2], mean tc), per the arm's skill."""
    out = {}
    total = ins.rounds
    for k in KEYS:
        n_i, m_i, e2_i, tc_i = _row(ins, k)
        if n_i < MIN_BIN_ROUNDS:
            continue
        if arm == "basic":
            n_b, m_b, e2_b, tc_b = _row(basic, k)
            out[k] = (n_b / basic.rounds, m_b, e2_b, tc_b)
        elif arm == "ins":
            out[k] = (n_i / total, m_i, e2_i, tc_i)
        else:  # ceiling: ins curve + paired deviation delta
            out[k] = (n_i / total, m_i + dev_delta(k)[0], e2_i, tc_i)
    return out


def ramp_units(steps, k: int) -> float:
    bet = 0.0
    for lo, units in steps:
        if k >= lo:
            bet = units
        else:
            break
    return bet


def price(arm: str, steps):
    bins = arm_bins(arm)
    ev = e2 = avg_bet = action = 0.0
    s_t = ss_t = x_bt = ss_b = 0.0
    lo_bet, hi_bet = None, 0.0
    for k, (f, m, m2, tc) in sorted(bins.items()):
        b = ramp_units(steps, k)
        ev += f * b * m
        e2 += f * b * b * m2
        avg_bet += f * b
        if b > 0:
            action += f
            lo_bet = b if lo_bet is None else min(lo_bet, b)
            hi_bet = max(hi_bet, b)
        s_t += f * tc
        ss_t += f * (tc * tc + 1.0 / 12.0)
        x_bt += f * b * tc
        ss_b += f * b * b
    var = max(e2 - ev * ev, 0.0)
    vt = ss_t - s_t * s_t
    vb = ss_b - avg_bet * avg_bet
    corr = (x_bt - avg_bet * s_t) / math.sqrt(vt * vb) if vt > 0 and vb > 0 else 0.0
    return ev, var, avg_bet, action, corr, (lo_bet or 0.0, hi_bet)


# --- report ------------------------------------------------------------------

print(f"E16 ledger — {GAME.upper()} 6-deck, pen {PEN[1:]}%, DAS, no surrender")
print(f"unit ${UNIT:g} (1u = table min), {ROUNDS_PER_HOUR} rounds/h observed, "
      f"bankroll at {100 * RUIN:g}% RoR")
print(f"banked: basic {basic.rounds:,} rounds ({n_basic} shards), "
      f"ins {ins.rounds:,} ({n_ins}), dev paired {dev_rounds:,} ({n_dev})")
print()

print("the curve (per-unit EV by TC bin; ins arm includes count insurance):")
print(f"  {'tc':>4s} {'freq':>8s} {'basic EV':>9s} {'±se':>7s} {'ins EV':>9s} "
      f"{'ins/rd':>8s} {'dev value':>10s} {'±se':>7s} {'sd':>6s}")
for k in KEYS:
    b, i = basic.bins[k], ins.bins[k]
    if i.rounds < MIN_BIN_ROUNDS:
        continue
    dv, dse = dev_delta(k)
    print(f"  {k:+4d} {100 * i.rounds / ins.rounds:7.3f}% "
          f"{100 * b.ev:+8.3f}% {100 * b.stderr:6.3f}% {100 * i.ev:+8.3f}% "
          f"{100 * i.ins_profit / i.rounds:+7.4f}% "
          f"{100 * dv:+9.4f}% {100 * dse:6.4f}% {math.sqrt(i.var):6.3f}")
print()

hdr = (f"{'ramp':<24s} {'arm':<8s} {'avg$':>6s} {'act%':>6s} {'sprd':>7s} "
       f"{'corr':>6s} {'$/h':>8s} {'σ/h':>8s} {'N0':>8s} {'bank':>7s} "
       f"{'money%':>8s}")
print("the menu (per observed round; $/h and σ/h at the configured pace):")
print(hdr)
for name, steps in RAMPS.items():
    for arm in ARMS:
        ev, var, avg_bet, action, corr, (lo, hi) = price(arm, steps)
        dollars_h = ev * UNIT * ROUNDS_PER_HOUR
        sigma_h = math.sqrt(var * ROUNDS_PER_HOUR) * UNIT
        n0_h = (var / (ev * ev)) / ROUNDS_PER_HOUR if ev > 0 else float("inf")
        bank = (var / (2.0 * ev)) * math.log(1.0 / RUIN) * UNIT if ev > 0 else float("inf")
        money = ev / avg_bet if avg_bet else 0.0
        n0_txt = f"{n0_h:7.0f}h" if math.isfinite(n0_h) else "      —"
        bank_txt = f"${bank / 1000:5.1f}k" if math.isfinite(bank) else "     —"
        spread = f"{lo:g}-{hi:g}" if hi else "—"
        print(f"{name:<24s} {arm:<8s} {avg_bet * UNIT:6.1f} {100 * action:5.1f}% "
              f"{spread:>7s} {corr:+6.2f} {dollars_h:+8.2f} {sigma_h:8.0f} "
              f"{n0_txt} {bank_txt} {100 * money:+7.3f}%")
    print()

print("reading guide: act% = rounds with money down; corr = corr(bet, TC), the")
print("surveillance statistic (flat play-all = 0 by construction); money% = edge")
print("per unit staked (the E4c convention); N0/bank = hours to 1σ=EV and 5%-RoR")
print("bankroll at these stakes. Pace scales $/h linearly, σ/h and N0 by √/1/x.")
