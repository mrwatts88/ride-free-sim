"""E24 — the hobby card: minimum bankroll that still clears a $/h target.

Matt's reframe (2026-07-19): the pro question is "max $/h per bankroll"; the
hobby question is "min bankroll subject to >= $15/h at 200 r/h" — a blackjack
hobby that pays for itself without pro-sized capital. No simulation here
(the E4c/E12/E16 pattern): everything is arithmetic over the banked E16
per-TC curves (60M rounds, arms basic/ins/dev) and the banked E17
multi-signal RC curves (48M rounds) — no new seeds.

Two solvers:
1. CONTINUOUS FRONTIER — per arm and leave threshold, the KKT solution of
   min variance s.t. EV >= target with a seated floor bet: raised bins get
   b_k proportional to edge/E[profit^2] (Kelly shape), floor bins stay at 1u.
   Because the constraint is an inequality and the floor toll's variance is
   fixed, the min-bankroll point can sit ABOVE the target hourly — the
   solver keeps raising lambda while bankroll still falls.
2. HUMAN CARDS — exhaustive search over 1- and 2-jump cards on a $5 chip
   grid with leave options, scored on all three arms; the same search runs
   on the Red 7 running-count bins (no division) with its depth-exact pivot.

Run:  uv run python data/e24_hobby.py [target_per_h] [unit] [pace]
      defaults 15 15 200  (the $15-floor weekday hobby spec)

Idealizations on record (inherited, listed in the output notes): ceiling
arm reuses the ins arm's E[profit^2] (deviation variance unmodeled); the
ins arm is composition-exact insurance (E18 measured the human rule at
~73-80% of it); bet-0 bins assume cards keep flowing (sit-out/backcount
semantics); rounds independent (within-shoe TC correlation adds a little
sigma); bankroll is lifetime 5%-RoR with no resizing.
"""

import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ridefree.experiments import (  # noqa: E402
    load_count_curves_json,
    load_tc_curve_json,
    merge_count_curves,
    merge_tc_curves,
)

# --- CONFIG ------------------------------------------------------------------

TARGET_H = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0  # $/h to clear
UNIT = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0  # $ table min (1u)
PACE = float(sys.argv[3]) if len(sys.argv) > 3 else 200.0  # observed rounds/h
RUIN = 0.05
GAME = "h17"
PEN = "p75"
MIN_BIN_ROUNDS = 2_000
TABLE_MAX_U = 1000.0 / UNIT  # cap any bet at $1000 (the felt max)

# chip-real jump sizes for the discrete search: $20..$200 in $5 steps
JUMP_DOLLARS = [d for d in range(20, 205, 5)]
LEAVES = (-99, -2, -1)  # never-leave, walk at tc<=-2, walk at tc<=-1
RUIN_LOG = math.log(1.0 / RUIN)

HERE = os.path.dirname(os.path.abspath(__file__))

# --- data loading (E16 TC curves + dev deltas; E17 RC curves) ----------------


def _load_curve(arm: str, pen: str):
    paths = sorted(glob.glob(os.path.join(HERE, f"e16_{GAME}_{arm}_{pen}_s*.json")))
    if not paths:
        return None
    return merge_tc_curves([load_tc_curve_json(p) for p in paths])


def _load_dev(pen: str):
    bins: dict[int, list] = {}
    for p in sorted(glob.glob(os.path.join(HERE, f"e16_{GAME}_dev_{pen}_s*.json"))):
        with open(p) as f:
            payload = json.load(f)
        for k, (n, d, d2) in payload["by_tc"].items():
            acc = bins.setdefault(int(k), [0, 0.0, 0.0])
            acc[0] += n
            acc[1] += d
            acc[2] += d2
    return bins


basic = _load_curve("basic", PEN)
ins = _load_curve("ins", PEN)
dev_bins = _load_dev(PEN)
if basic is None or ins is None:
    sys.exit("missing banked e16 basic/ins shards for h17 p75")

rc_paths = sorted(glob.glob(os.path.join(HERE, "e17_h17_ins_p75_s*.json")))
rc_data = merge_count_curves([load_count_curves_json(p) for p in rc_paths])


def dev_delta(k: int) -> tuple[float, float]:
    acc = dev_bins.get(k)
    if not acc or acc[0] < 200:
        return 0.0, 0.0
    n, d, d2 = acc
    m = d / n
    var = max(d2 / n - m * m, 0.0)
    return m, math.sqrt(var / n)


def tc_arm_bins(arm: str) -> dict[int, tuple[float, float, float, float, float]]:
    """bin -> (freq, ev/u, E[profit^2]/u^2, mean tc, ev se) for the arm."""
    out = {}
    for k in sorted(set(basic.bins) & set(ins.bins)):
        bi = ins.bins[k]
        if bi.rounds < MIN_BIN_ROUNDS:
            continue
        if arm == "basic":
            bb = basic.bins[k]
            out[k] = (bb.rounds / basic.rounds, bb.ev, bb.profit_sq / bb.rounds,
                      bb.tc_sum / bb.rounds, bb.stderr)
        elif arm == "ins":
            out[k] = (bi.rounds / ins.rounds, bi.ev, bi.profit_sq / bi.rounds,
                      bi.tc_sum / bi.rounds, bi.stderr)
        else:  # ceiling = ins + paired deviation EV delta (variance reused)
            dv, dse = dev_delta(k)
            out[k] = (bi.rounds / ins.rounds, bi.ev + dv,
                      bi.profit_sq / bi.rounds, bi.tc_sum / bi.rounds,
                      math.sqrt(bi.stderr ** 2 + dse ** 2))
    return out


def rc_bins(signal: str) -> dict[int, tuple[float, float, float, float, float]]:
    out = {}
    for k, b in rc_data.by_signal[signal].items():
        if b.rounds < MIN_BIN_ROUNDS:
            continue
        out[k] = (b.rounds / rc_data.rounds, b.ev, b.profit_sq / b.rounds,
                  b.tc_sum / b.rounds, b.stderr)
    return out


# --- pricing core ------------------------------------------------------------


def price_bets(bins, bets):
    """bets: bin -> units. Returns (ev/u, var/u^2, avg_bet, act, corr, se)."""
    ev = e2 = avg_bet = action = se2 = 0.0
    s_t = ss_t = x_bt = ss_b = 0.0
    for k, (f, m, m2, tc, se) in bins.items():
        b = bets.get(k, 0.0)
        ev += f * b * m
        e2 += f * b * b * m2
        se2 += (f * b * se) ** 2
        avg_bet += f * b
        if b > 0:
            action += f
        s_t += f * tc
        ss_t += f * (tc * tc + 1.0 / 12.0)
        x_bt += f * b * tc
        ss_b += f * b * b
    var = max(e2 - ev * ev, 0.0)
    vt = ss_t - s_t * s_t
    vb = ss_b - avg_bet * avg_bet
    corr = (x_bt - avg_bet * s_t) / math.sqrt(vt * vb) if vt > 0 and vb > 0 else 0.0
    return ev, var, avg_bet, action, corr, math.sqrt(se2)


def stats(ev, var, se=0.0):
    """(dollars/h, se $/h, sigma per round $, N0 h, bank $) at the config."""
    dollars_h = ev * UNIT * PACE
    se_h = se * UNIT * PACE
    sd_r = math.sqrt(var) * UNIT
    n0 = (var / (ev * ev)) / PACE if ev > 0 else float("inf")
    bank = (var / (2.0 * ev)) * RUIN_LOG * UNIT if ev > 0 else float("inf")
    return dollars_h, se_h, sd_r, n0, bank


def steps_bets(bins, steps):
    """ledger step convention -> explicit bin->units dict."""
    bets = {}
    for k in bins:
        b = 0.0
        for lo, units in steps:
            if k >= lo:
                b = units
            else:
                break
        bets[k] = b
    return bets


# --- solver 1: continuous KKT frontier ---------------------------------------


def kkt_bets(bins, leave_t, lam):
    bets = {}
    for k, (f, m, m2, tc, se) in bins.items():
        if k <= leave_t:
            bets[k] = 0.0
        elif m <= 0:
            bets[k] = 1.0
        else:
            bets[k] = min(max(1.0, lam * m / (2.0 * m2)), TABLE_MAX_U)
    return bets


def kkt_solve(bins, leave_t, target_per_round_u):
    """Min-bank bets with EV >= target: bisect lambda to the target, then
    keep raising lambda while bankroll still falls (inequality constraint)."""
    lo, hi = 0.0, 1e7
    if price_bets(bins, kkt_bets(bins, leave_t, hi))[0] < target_per_round_u:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if price_bets(bins, kkt_bets(bins, leave_t, mid))[0] < target_per_round_u:
            lo = mid
        else:
            hi = mid
    lam = hi

    def bank_of(lam_):
        ev, var, *_ = price_bets(bins, kkt_bets(bins, leave_t, lam_))
        return (var / (2.0 * ev)) * RUIN_LOG * UNIT if ev > 0 else float("inf")

    step = max(lam, 1.0) * 0.05
    while step > lam * 1e-4 + 1e-9:
        if bank_of(lam + step) < bank_of(lam):
            lam += step
        else:
            step *= 0.5
    return kkt_bets(bins, leave_t, lam)


# --- solver 2: discrete human-card search ------------------------------------


def card_steps(leave_t, jumps):
    base = ((-99, 1.0),) if leave_t == -99 else ((leave_t + 1, 1.0),)
    return base + jumps


def search_cards(bins, leave_t, triggers, n_jumps, target_h):
    """Best (min bank) card with n_jumps rungs; returns (bank, steps, priced)."""
    best = None
    units = [d / UNIT for d in JUMP_DOLLARS]
    if n_jumps == 1:
        combos = [((j, u),) for j in triggers for u in units]
    else:
        combos = [((j1, u1), (j2, u2))
                  for i, j1 in enumerate(triggers) for j2 in triggers[i + 1:]
                  for a, u1 in enumerate(units) for u2 in units[a + 1:]]
    for jumps in combos:
        steps = card_steps(leave_t, jumps)
        priced = price_bets(bins, steps_bets(bins, steps))
        ev, var = priced[0], priced[1]
        if ev * UNIT * PACE < target_h or ev <= 0:
            continue
        bank = (var / (2.0 * ev)) * RUIN_LOG * UNIT
        if best is None or bank < best[0]:
            best = (bank, steps, priced)
    return best


def fmt_steps(steps):
    parts = []
    for lo, u in steps:
        d = u * UNIT
        if lo <= -90:
            parts.append(f"${d:g} floor")
        elif u == 1.0:
            parts.append(f"${d:g} floor from {lo:+d}")
        else:
            parts.append(f"${d:g} at {lo:+d}")
    return ", ".join(parts)


def fmt_row(label, priced):
    ev, var, avg_bet, action, corr, se = priced
    dollars_h, se_h, sd_r, n0, bank = stats(ev, var, se)
    n0_txt = f"{n0:6.0f}h" if math.isfinite(n0) else "     —"
    bank_txt = f"${bank / 1000:5.1f}k" if math.isfinite(bank) else "     —"
    return (f"{label:<58s} {avg_bet * UNIT:6.1f} {100 * action:5.1f}% "
            f"{corr:+5.2f} {dollars_h:+7.2f}±{se_h:4.2f} {sd_r:5.0f} "
            f"{n0_txt} {bank_txt}")


HDR = (f"{'card':<58s} {'avg$':>6s} {'act%':>6s} {'corr':>5s} "
       f"{'$/h ±se':>12s} {'σ/rd':>5s} {'N0':>7s} {'bank':>7s}")

# --- report ------------------------------------------------------------------

print(f"E24 — the hobby card: min bankroll s.t. >= ${TARGET_H:g}/h "
      f"at {PACE:g} r/h, ${UNIT:g} floor, {GAME.upper()} 6d pen {PEN[1:]}%, "
      f"{100 * RUIN:g}% RoR")
print(f"banked: e16 basic/ins 60M rounds + dev pairs; e17 RC curves "
      f"{rc_data.rounds // 10**6}M rounds (arm {rc_data.arm})")
print()

# -- section 1: the continuous frontier --
print("1) CONTINUOUS FRONTIER (KKT bets, seated floor; bank at the target,")
print("   solver may overshoot $/h when that lowers bank):")
target_u = TARGET_H / PACE / UNIT
print(f"   {'arm':<9s} {'leave':<9s} {'$/h':>7s} {'avg$':>6s} "
      f"{'σ/rd':>5s} {'N0':>7s} {'bank':>8s}")
frontier_best = {}
for arm in ("basic", "ins", "ceiling"):
    bins = tc_arm_bins(arm)
    for leave_t in LEAVES:
        sol = kkt_solve(bins, leave_t, target_u)
        if sol is None:
            continue
        ev, var, avg_bet, action, corr, se = price_bets(bins, sol)
        dollars_h, _, sd_r, n0, bank = stats(ev, var)
        leave_txt = "never" if leave_t == -99 else f"tc<={leave_t}"
        print(f"   {arm:<9s} {leave_txt:<9s} {dollars_h:+7.2f} "
              f"{avg_bet * UNIT:6.1f} {sd_r:5.0f} {n0:6.0f}h "
              f"${bank / 1000:6.1f}k")
        if arm not in frontier_best or bank < frontier_best[arm][0]:
            frontier_best[arm] = (bank, leave_t, sol)
print()

# the shape of the ins-arm optimum (what the human card should look like)
bank, leave_t, sol = frontier_best["ins"]
bins = tc_arm_bins("ins")
shape = {k: sol[k] * UNIT for k in sorted(sol) if sol[k] > 0}
print("   ins-arm optimal bet shape ($ by TC bin): "
      + ", ".join(f"{k:+d}:${v:.0f}" for k, v in shape.items()))
print()

# -- section 2: human cards on hi-lo TC --
print(f"2) HUMAN CARDS (hi-lo TC, $5 chips; best min-bank card per shape, "
      f"ins arm; >= ${TARGET_H:g}/h):")
print(HDR)
tc_best_overall = None
for n_jumps in (1, 2):
    for leave_t in LEAVES:
        best = search_cards(tc_arm_bins("ins"), leave_t, (1, 2, 3, 4, 5, 6),
                            n_jumps, TARGET_H)
        if best is None:
            leave_txt = "never" if leave_t == -99 else f"tc<={leave_t}"
            print(f"{n_jumps}-jump, leave {leave_txt}: no card reaches the target")
            continue
        bank, steps, priced = best
        leave_txt = "no leave" if leave_t == -99 else f"leave tc<={leave_t}"
        label = f"{n_jumps}-jump, {leave_txt}: {fmt_steps(steps)}"
        print(fmt_row(label, priced))
        if tc_best_overall is None or bank < tc_best_overall[0]:
            tc_best_overall = (bank, leave_t, steps)
print()

# the winner across arms (what deviations would buy on the SAME card)
bank, leave_t, steps = tc_best_overall
print(f"   THE TC WINNER on all three arms — {fmt_steps(steps)}:")
print(HDR)
for arm in ("basic", "ins", "ceiling"):
    bins = tc_arm_bins(arm)
    print(fmt_row(f"   arm={arm}", price_bets(bins, steps_bets(bins, steps))))
print()

# ceiling-arm search: what the best card looks like IF all indexes are played
print("   ceiling-arm search (all-indexes bound — the deviation-hunt prize):")
print(HDR)
ceil_best = None
for n_jumps in (1, 2):
    for leave_t in LEAVES:
        best = search_cards(tc_arm_bins("ceiling"), leave_t,
                            (1, 2, 3, 4, 5, 6), n_jumps, TARGET_H)
        if best is None:
            continue
        if ceil_best is None or best[0] < ceil_best[0]:
            ceil_best = best + (leave_t, n_jumps)
if ceil_best:
    bank, steps, priced, leave_t, n_jumps = ceil_best
    leave_txt = "no leave" if leave_t == -99 else f"leave tc<={leave_t}"
    print(fmt_row(f"   best: {n_jumps}-jump, {leave_txt}: {fmt_steps(steps)}",
                  priced))
print()

# -- section 3: the no-division version (Red 7 RC, pivot-zeroed IRC -12) --
print("3) NO-DIVISION VERSION (Red 7 RC bins, IRC -12 pivot-zeroed; jump at")
print("   RC>=0 is the depth-exact TC>=+2 test; ins arm, 48M rounds).")
print("   Walk lines must sit BELOW the fresh-shoe IRC -12 to be playable")
print("   (rc<=-12 or higher = instant walk at the shuffle):")
print(HDR)
rc = rc_bins("red7_rc")
rc_best_overall = None
for n_jumps in (1, 2):
    for leave_t in (-99, -18, -16, -14):
        best = search_cards(rc, leave_t, (-2, -1, 0, 1, 2, 3, 4, 6, 8),
                            n_jumps, TARGET_H)
        if best is None:
            continue
        bank, steps, priced = best
        leave_txt = "no leave" if leave_t == -99 else f"leave rc<={leave_t}"
        label = f"{n_jumps}-jump, {leave_txt}: {fmt_steps(steps)} (RC)"
        print(fmt_row(label, priced))
        if rc_best_overall is None or bank < rc_best_overall[0]:
            rc_best_overall = (bank, leave_t, steps)
print()

# -- section 4: conditional shapes (sit-out / backcount semantics) --
print("4) CONDITIONAL SHAPES — bet 0 on a large share of rounds while cards")
print("   keep flowing: needs sit-out-while-others-play or mid-shoe re-entry")
print("   (BOTH open felt items; pace at a peopled table is also < 200 r/h):")
print(HDR)
bins = tc_arm_bins("ins")
for trig in (1, 2):
    best = None
    for d in JUMP_DOLLARS + [15]:
        steps = ((trig, d / UNIT),)
        priced = price_bets(bins, steps_bets(bins, steps))
        if priced[0] * UNIT * PACE < TARGET_H:
            continue
        ev, var = priced[0], priced[1]
        bank = (var / (2.0 * ev)) * RUIN_LOG * UNIT
        if best is None or bank < best[0]:
            best = (bank, steps, priced)
    if best:
        bank, steps, priced = best
        print(fmt_row(f"   wong-in only (TC): {fmt_steps(steps)}", priced))
# seated sit-out versions: floor only at good counts, jumps above
for n_jumps in (1, 2):
    best = search_cards(bins, 0, (1, 2, 3, 4, 5, 6), n_jumps, TARGET_H)
    if best:
        bank, steps, priced = best
        print(fmt_row(f"   TC sit-out below +1, {n_jumps}-jump: "
                      f"{fmt_steps(steps)}", priced))
rc_sit_best = None
for n_jumps in (1, 2):
    for sit_t in (-12, -8, -4):
        best = search_cards(rc, sit_t, (-2, -1, 0, 1, 2, 3, 4, 6, 8),
                            n_jumps, TARGET_H)
        if best is None:
            continue
        bank, steps, priced = best
        label = (f"   RC sit-out below {sit_t + 1:+d}, {n_jumps}-jump: "
                 f"{fmt_steps(steps)} (RC)")
        print(fmt_row(label, priced))
        if rc_sit_best is None or bank < rc_sit_best[0]:
            rc_sit_best = (bank, steps, priced)
print()

# -- section 5: sensitivity --
print("5) SENSITIVITY of the TC winner:")
bank, leave_t, steps = tc_best_overall
for pen in ("p70", "p80"):
    curve = _load_curve("ins", pen)
    if curve is None:
        continue
    pb = {}
    for k, b in curve.bins.items():
        if b.rounds < MIN_BIN_ROUNDS:
            continue
        pb[k] = (b.rounds / curve.rounds, b.ev, b.profit_sq / b.rounds,
                 b.tc_sum / b.rounds, b.stderr)
    print(fmt_row(f"   pen {pen[1:]}% (ins, {curve.rounds // 10**6}M): "
                  f"{fmt_steps(steps)}", price_bets(pb, steps_bets(pb, steps))))
print()

# session expectation-setting for the hobby winner (normal approx)
priced = price_bets(tc_arm_bins("ins"), steps_bets(tc_arm_bins("ins"), steps))
ev, var = priced[0], priced[1]
mean4 = ev * UNIT * PACE * 4
sd4 = math.sqrt(var * PACE * 4) * UNIT
print(f"   4h session on the TC winner: mean {mean4:+.0f}, sd {sd4:,.0f}, "
      f"P10 {mean4 - 1.2816 * sd4:+,.0f}, P5 {mean4 - 1.6449 * sd4:+,.0f}, "
      f"P(lose) {100 * 0.5 * math.erfc(mean4 / (sd4 * math.sqrt(2))):.1f}%")
print()

print("notes: ins arm = chart + composition-exact insurance (human index rule")
print("measured at ~73-80% of it, E18); ceiling = + paired deviation EV with")
print("ins-arm variance REUSED (deviation variance unmodeled — RA-index work")
print("would need new sims); bet-0 rounds assume cards flow (sit-out/walk");
print("semantics; heads-up requires walking — E18b's friction estimate is")
print("per-walk and UNPRICED here (leave rows are zero-friction); rounds")
print("independent; bank = lifetime 5%-RoR, no resizing; floor $" +
      f"{UNIT:g} " + "(recon saw $15 Saturday; weekday $10 unknown).")
print("winner's-curse caveat: cards are argmaxes over ~30k candidates on the")
print("banked stream; printed $/h is selected (se ~0.6-1.5). Any card headed")
print("for the felt gets fresh-seed OOS certification first (E18/E23 pattern).")
