"""E25 — risk-averse deviations: honest second moments, the RA card per shape.

E24's ceiling arm priced deviations by EV delta with the no-deviation arm's
variance REUSED. This script retires that: it loads the banked RA moments
(data/e25_ra_p75_s*.json — chart bins, per-play paired (d, d^2, p*d) for
composition deviations and chart-cell suppressions, and the exact insurance
overlay) and, per operating shape, selects the play set that MINIMIZES the
5%-RoR bankroll subject to the hourly target — Matt's question "can we find
deviations tweaked in favor of lower variance?" answered by arithmetic.

Selection is human-shaped and double-count-safe:
- plays are grouped by (chart row, upcard); each group picks ONE policy —
  chart as-is, "suppress this chart double/split at TC bins >= j", or "play
  the composition deviation at bins >= j" (never both: a dev cell and its
  suppression touch the same rounds);
- insurance is its own group: "insure at bins >= j" (the overlay is exact,
  hedging cross term included);
- the bet shape is re-searched after each selection pass (E24's 1-2 jump
  grid), so EV lost to variance-saving suppressions is re-earned by the
  ramp and the >= $/h constraint binds the CARD, not each play;
- policies are additive in (mu, M2) space to first order; the certified
  final card gets a live OOS run (E18/E23 pattern) which plays the real
  combined policy.

Gates (printed first): chart bins vs the banked E16 basic curve (fresh
seeds); the dev aggregate per bin vs the E16 paired dev values (the same
estimand, independent seeds); aggregate == sum-of-cells identity (exact by
construction); insurance P(BJ | ace up) vs first principles.

Run:  uv run python data/e25_ra.py [target_per_h] [unit] [pace]
      defaults 15 15 200 (the M11 hobby spec)
"""

import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ridefree.experiments import (  # noqa: E402
    load_ra_bank_json,
    load_tc_curve_json,
    merge_ra_banks,
    merge_tc_curves,
)

TARGET_H = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
UNIT = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
PACE = float(sys.argv[3]) if len(sys.argv) > 3 else 200.0
RUIN_LOG = math.log(1.0 / 0.05)
MIN_BIN_ROUNDS = 2_000
MIN_CELL_ROUNDS = 250  # per (play, bin): below this a delta is noise, skip
JUMP_DOLLARS = list(range(20, 205, 5))

HERE = os.path.dirname(os.path.abspath(__file__))

# --- load the bank -----------------------------------------------------------

paths = sorted(glob.glob(os.path.join(HERE, "e25_ra_p75_s*.json")))
if not paths:
    sys.exit("no banked e25 shards — run `cli rabank` shards first")
bank = merge_ra_banks([load_ra_bank_json(p) for p in paths])
N = bank.rounds

BINS = {}  # k -> dict of per-round rates the pricing needs
for k, b in bank.bins.items():
    if b.rounds < MIN_BIN_ROUNDS:
        continue
    n = b.rounds
    BINS[k] = {
        "f": n / N, "n": n,
        "m": b.p_sum / n, "m2": b.p_sq / n, "tc": b.tc_sum / n,
        # insurance overlay per unit main bet, rates per bin round
        "ins_dm": (1.0 * b.ins_bj - 0.5 * (b.ins_rounds - b.ins_bj)) / n,
        "ins_dm2": (2.0 * (1.5 * b.ins_p_bj_sum - 0.5 * b.ins_p_sum)
                    + (1.0 * b.ins_bj + 0.25 * (b.ins_rounds - b.ins_bj))) / n,
        "dev_n": b.dev_rounds,
        "dev_dm": (b.dev_d_sum / n) if b.dev_rounds else 0.0,
        "dev_dm2": ((2.0 * b.dev_pd_sum + b.dev_d_sq) / n) if b.dev_rounds else 0.0,
        "dev_ins_x": (-1.0 * b.dev_ins_d_sum / n) if b.dev_rounds else 0.0,
    }
KEYS = sorted(BINS)
DEV_MIN = bank.dev_tc_min

# --- play groups: (row, up) -> policy options --------------------------------


def _parse_key(key: str):
    """'noD:h10v6' -> ('sup', 'h10', '6'); 'dev:h12v3:H>S' -> ('dev','h12','3')."""
    if key.startswith("no"):
        body = key.split(":", 1)[1]
        row, up = body.rsplit("v", 1)
        return "sup", row, up, key[2]
    _, body, swap = key.split(":")
    row, up = body.rsplit("v", 1)
    return "dev", row, up, swap


GROUPS: dict[tuple[str, str], dict] = {}
for key, by_bin in bank.cells.items():
    kind, row, up, tag = _parse_key(key)
    g = GROUPS.setdefault((row, up), {"sup": {}, "dev": {}, "tags": set()})
    g["tags"].add(f"{kind}:{tag}")
    dst = g[kind]
    for k, c in by_bin.items():
        if k not in BINS:
            continue
        acc = dst.setdefault(k, [0, 0.0, 0.0, 0.0])
        acc[0] += c.rounds
        acc[1] += c.d_sum
        acc[2] += c.d_sq
        acc[3] += c.pd_sum


def _policy_deltas(cells: dict, j: int):
    """Per-bin (dm, dm2) of playing this group's change at bins >= j."""
    out = {}
    for k, (cn, d, d2, pd) in cells.items():
        if k < j or cn < MIN_CELL_ROUNDS:
            continue
        n = BINS[k]["n"]
        out[k] = (d / n, (2.0 * pd + d2) / n)
    return out


# --- pricing -----------------------------------------------------------------


def price(bets: dict, adj: dict, ins_j: int | None):
    """(mu, M2) in units for a bets dict + selection adjustments + insurance."""
    mu = m2 = 0.0
    for k in KEYS:
        b = bets.get(k, 0.0)
        if b == 0.0:
            continue
        r = BINS[k]
        dm, dm2 = adj.get(k, (0.0, 0.0))
        ins_on = ins_j is not None and k >= ins_j
        # dev x insurance cross term (dev_ins_x) is banked but NOT applied:
        # it corresponds to the full dev set, not a selected subset — tiny
        # either way (two rare events), and the OOS run plays the real policy.
        i_dm = r["ins_dm"] if ins_on else 0.0
        i_dm2 = r["ins_dm2"] if ins_on else 0.0
        mu += r["f"] * b * (r["m"] + dm + i_dm)
        m2 += r["f"] * b * b * (r["m2"] + dm2 + i_dm2)
    return mu, m2


def bank_of(mu: float, m2: float) -> float:
    var = max(m2 - mu * mu, 0.0)
    return (var / (2.0 * mu)) * RUIN_LOG * UNIT if mu > 0 else float("inf")


def stats_row(label, mu, m2):
    var = max(m2 - mu * mu, 0.0)
    dollars = mu * UNIT * PACE
    sd_r = math.sqrt(var) * UNIT
    n0 = (var / (mu * mu)) / PACE if mu > 0 else float("inf")
    bk = bank_of(mu, m2)
    return (f"{label:<46s} {dollars:+8.2f} {sd_r:5.0f} "
            f"{n0:6.0f}h ${bk / 1000:5.1f}k")


# --- card search (E24 pattern, self-contained on this bank) ------------------


def steps_bets(steps):
    bets = {}
    for k in KEYS:
        v = 0.0
        for lo, u in steps:
            if k >= lo:
                v = u
            else:
                break
        bets[k] = v
    return bets


def search_card(leave_t, adj, ins_j, n_jumps=2):
    """Min-bank 1-2 jump card, >= TARGET_H, with the selection active."""
    best = None
    units = [d / UNIT for d in JUMP_DOLLARS]
    triggers = (1, 2, 3, 4, 5, 6)
    base = ((-99, 1.0),) if leave_t == -99 else ((leave_t + 1, 1.0),)
    combos = [((j, u),) for j in triggers for u in units]
    if n_jumps == 2:
        combos += [((j1, u1), (j2, u2))
                   for i, j1 in enumerate(triggers) for j2 in triggers[i + 1:]
                   for a, u1 in enumerate(units) for u2 in units[a + 1:]]
    for jumps in combos:
        bets = steps_bets(base + jumps)
        mu, m2 = price(bets, adj, ins_j)
        if mu * UNIT * PACE < TARGET_H:
            continue
        bk = bank_of(mu, m2)
        if best is None or bk < best[0]:
            best = (bk, base + jumps, bets)
    return best


# --- selection ---------------------------------------------------------------


def select(bets, *, ra: bool):
    """Greedy per-group policy choice on a fixed card. ra=False -> EV-max
    (adopt any policy with mu gain, thresholds by EV; insurance at its +EV
    bins) — the honest-variance version of E24's ceiling. ra=True -> adopt
    whatever minimizes bank. Returns (adj, ins_j, chosen)."""
    chosen: dict = {}
    ins_j: int | None = None
    for _ in range(8):
        changed = False
        # insurance group
        best_j, best_score = None, None
        for j in KEYS:
            adj = _combine(chosen)
            mu, m2 = price(bets, adj, j)
            score = -mu if ra is False else bank_of(mu, m2)
            if best_score is None or score < best_score:
                best_score, best_j = score, j
        adj = _combine(chosen)
        mu0, m20 = price(bets, adj, None)
        base_score = -mu0 if ra is False else bank_of(mu0, m20)
        new_ins = best_j if best_score < base_score - 1e-12 else None
        if new_ins != ins_j:
            ins_j, changed = new_ins, True
        # play groups (incremental: combine everyone-else once per group)
        for gk, g in GROUPS.items():
            options = [("chart", None, {})]
            for kind in ("sup", "dev"):
                cells = g[kind]
                if not cells:
                    continue
                for j in sorted(set(cells)):
                    deltas = _policy_deltas(cells, j)
                    if deltas:
                        options.append((kind, j, deltas))
            others = dict(chosen)
            others.pop(gk, None)
            base_adj = _combine(others)
            best_opt, best_score = None, None
            for name, j, deltas in options:
                adj = base_adj if not deltas else {
                    k: (base_adj.get(k, (0.0, 0.0))[0] + dm,
                        base_adj.get(k, (0.0, 0.0))[1] + dm2)
                    for k in set(base_adj) | set(deltas)
                    for dm, dm2 in (deltas.get(k, (0.0, 0.0)),)
                }
                mu, m2 = price(bets, adj, ins_j)
                score = -mu if ra is False else bank_of(mu, m2)
                if best_score is None or score < best_score:
                    best_score, best_opt = score, (name, j, deltas)
            name, j, deltas = best_opt
            cur = chosen.get(gk)
            new = None if name == "chart" else (name, j, deltas)
            if (cur is None) != (new is None) or (cur and new and cur[:2] != new[:2]):
                if new is None:
                    chosen.pop(gk, None)
                else:
                    chosen[gk] = new
                changed = True
        if not changed:
            break
    return _combine(chosen), ins_j, chosen


def _combine(chosen: dict) -> dict:
    adj: dict = {}
    for name, j, deltas in chosen.values():
        for k, (dm, dm2) in deltas.items():
            a = adj.get(k, (0.0, 0.0))
            adj[k] = (a[0] + dm, a[1] + dm2)
    return adj


def pipeline(leave_t, *, ra: bool, label: str):
    """search card -> select plays -> re-search -> re-select (two passes)."""
    sel_adj, ins_j, chosen = {}, None, {}
    card = search_card(leave_t, sel_adj, ins_j)
    for _ in range(2):
        if card is None:
            return None
        sel_adj, ins_j, chosen = select(card[2], ra=ra)
        card = search_card(leave_t, sel_adj, ins_j)
    if card is None:
        return None
    bk, steps, bets = card
    mu, m2 = price(bets, sel_adj, ins_j)
    return {"label": label, "steps": steps, "bets": bets, "mu": mu, "m2": m2,
            "ins_j": ins_j, "chosen": chosen}


def fmt_steps(steps):
    parts = []
    for lo, u in steps:
        d = u * UNIT
        if u == 1.0:
            parts.append(f"${d:g} floor" + ("" if lo <= -90 else f" from {lo:+d}"))
        else:
            parts.append(f"${d:g} at {lo:+d}")
    return ", ".join(parts)


# --- report ------------------------------------------------------------------

print(f"E25 — the RA card: honest second moments, min bank >= ${TARGET_H:g}/h "
      f"at {PACE:g} r/h, ${UNIT:g} floor")
print(f"bank: {N:,} rounds, {len(paths)} shards, pen {bank.penetration:g}, "
      f"dev replay at bins >= {DEV_MIN:+d}, {len(bank.cells)} raw cells, "
      f"{len(GROUPS)} play groups")
print()

# -- gates --
print("GATES")
e16_paths = sorted(glob.glob(os.path.join(HERE, "e16_h17_basic_p75_s*.json")))
e16 = merge_tc_curves([load_tc_curve_json(p) for p in e16_paths])
worst = (0.0, None)
for k in KEYS:
    if k not in e16.bins or e16.bins[k].rounds < MIN_BIN_ROUNDS:
        continue
    r, eb = BINS[k], e16.bins[k]
    se = math.sqrt((r["m2"] - r["m"] ** 2) / r["n"] + eb.stderr ** 2)
    z = (r["m"] - eb.ev) / se
    if abs(z) > abs(worst[0]):
        worst = (z, k)
mu_all = sum(r["f"] * r["m"] for r in BINS.values())
print(f"  1. chart bins vs banked e16 basic (60M, fresh seeds): worst |z| = "
      f"{abs(worst[0]):.2f} at bin {worst[1]:+d}; overall EV {100 * mu_all:+.3f}% "
      f"vs e16 {100 * e16.overall_ev:+.3f}%"
      f"   {'PASS' if abs(worst[0]) < 3.0 else 'FAIL'}")

dev_bins_e16: dict[int, list] = {}
for p in sorted(glob.glob(os.path.join(HERE, "e16_h17_dev_p75_s*.json"))):
    with open(p) as f:
        payload = json.load(f)
    for k, (n, d, d2) in payload["by_tc"].items():
        acc = dev_bins_e16.setdefault(int(k), [0, 0.0, 0.0])
        acc[0] += n
        acc[1] += d
        acc[2] += d2
worst_dev = (0.0, None)
for k in KEYS:
    r = BINS[k]
    if k < DEV_MIN or r["dev_n"] < 50_000 or k not in dev_bins_e16:
        continue
    n16, d16, d216 = dev_bins_e16[k]
    m16 = d16 / n16
    v16 = max(d216 / n16 - m16 * m16, 0.0)
    m25 = bank.bins[k].dev_d_sum / r["dev_n"]
    v25 = max(bank.bins[k].dev_d_sq / r["dev_n"] - m25 * m25, 0.0)
    z = (m25 - m16) / math.sqrt(v25 / r["dev_n"] + v16 / n16)
    if abs(z) > abs(worst_dev[0]):
        worst_dev = (z, k)
if worst_dev[1] is None:
    print("  2. composition-dev value vs e16 paired: too few dev rounds per "
          "bin to score (need 50k)")
else:
    print(f"  2. composition-dev value per bin vs e16 paired (independent "
          f"seeds): worst |z| = {abs(worst_dev[0]):.2f} at bin "
          f"{worst_dev[1]:+d}   {'PASS' if abs(worst_dev[0]) < 3.0 else 'FAIL'}")

agg_err = 0.0
for k in KEYS:
    if k < DEV_MIN:
        continue
    cells_sum = sum(
        c.d_sum for key, by_bin in bank.cells.items() if key.startswith("dev:")
        for kk, c in by_bin.items() if kk == k
    )
    agg_err = max(agg_err, abs(cells_sum - bank.bins[k].dev_d_sum))
print(f"  3. dev aggregate == sum of attributed cells: max |err| = "
      f"{agg_err:.2e}   {'PASS' if agg_err < 1e-6 else 'FAIL'}")

n_a = sum(b.ins_rounds for b in bank.bins.values())
n_bj = sum(b.ins_bj for b in bank.bins.values())
p_bj = n_bj / n_a
se_bj = math.sqrt(p_bj * (1 - p_bj) / n_a)
print(f"  4. insurance: P(dealer BJ | ace up) = {p_bj:.4f} ± {se_bj:.4f} "
      f"(fresh-shoe first principles 96/311 = {96 / 311:.4f}; depth blends it)")
print()

# -- the shape table --
SHAPES = (
    ("walk at tc<=-1 (floor from 0)", 0 - 1),
    ("sit-out below +1 (floor from +1)", 0),
    ("never leave", -99),
)
HDR = f"{'layer':<46s} {'$/h':>8s} {'σ/rd':>5s} {'N0':>7s} {'bank':>7s}"

results = {}
for shape_label, leave_t in SHAPES:
    print(f"SHAPE: {shape_label}")
    print(HDR)
    card = search_card(leave_t, {}, None)
    if card is None:
        print("  no chart-only card reaches the target")
    else:
        mu, m2 = price(card[2], {}, None)
        print(stats_row(f"  chart only: {fmt_steps(card[1])}", mu, m2))
    ev = pipeline(leave_t, ra=False, label="EV-max")
    if ev:
        print(stats_row(
            f"  EV-max plays (honest var): {fmt_steps(ev['steps'])}"
            + (f", ins>={ev['ins_j']:+d}" if ev["ins_j"] is not None else ""),
            ev["mu"], ev["m2"]))
    ra = pipeline(leave_t, ra=True, label="RA")
    if ra:
        print(stats_row(
            f"  RA plays (min bank):  {fmt_steps(ra['steps'])}"
            + (f", ins>={ra['ins_j']:+d}" if ra["ins_j"] is not None else ""),
            ra["mu"], ra["m2"]))
        results[shape_label] = (ev, ra)
    print()

# -- the distilled RA play list for the primary shape (walk) --
primary = results.get(SHAPES[0][0])
if primary:
    ev, ra = primary
    print(f"THE RA PLAY LIST — {SHAPES[0][0]}, card {fmt_steps(ra['steps'])}"
          + (f", insure at bins >= {ra['ins_j']:+d}" if ra["ins_j"] is not None
             else ", no insurance"))
    rows = []
    base_mu, base_m2 = ra["mu"], ra["m2"]
    base_bank = bank_of(base_mu, base_m2)
    for gk, (name, j, deltas) in ra["chosen"].items():
        trial = dict(ra["chosen"])
        trial.pop(gk)
        mu, m2 = price(ra["bets"], _combine(trial), ra["ins_j"])
        rows.append((bank_of(mu, m2) - base_bank,
                     (mu - base_mu) * UNIT * PACE, gk, name, j))
    rows.sort(reverse=True)  # most bank-valuable plays first
    print(f"  {'play':<34s} {'policy':<12s} {'Δbank if dropped':>17s} {'Δ$/h':>7s}")
    for dbank, dmoney, (row, up), name, j in rows[:18]:
        pol = f"{'skip' if name == 'sup' else 'dev'} at >={j:+d}"
        print(f"  {row + ' v ' + up:<34s} {pol:<12s} {dbank:+15,.0f}$ {-dmoney:+7.2f}")
    if len(rows) > 18:
        rest = sum(r[0] for r in rows[18:])
        print(f"  ... {len(rows) - 18} more plays, {rest:+,.0f}$ pooled")
    # what did RA reject that EV-max keeps?
    ev_set = {gk: v[:2] for gk, v in ev["chosen"].items()}
    ra_set = {gk: v[:2] for gk, v in ra["chosen"].items()}
    dropped = {gk: v for gk, v in ev_set.items() if gk not in ra_set}
    flipped = {gk: (v, ra_set[gk]) for gk, v in ev_set.items()
               if gk in ra_set and ra_set[gk] != v}
    added = {gk: v for gk, v in ra_set.items() if gk not in ev_set}
    print(f"\n  RA vs EV-max: {len(dropped)} EV-max plays rejected for variance, "
          f"{len(flipped)} thresholds moved, {len(added)} pure-variance plays "
          f"added (EV-negative, bank-positive)")
    for gk, v in list(added.items())[:8]:
        print(f"    added: {gk[0]} v {gk[1]} -> {v[0]} at >={v[1]:+d}")
    for gk in list(dropped)[:8]:
        print(f"    rejected: {gk[0]} v {gk[1]} ({ev_set[gk][0]} at "
              f">={ev_set[gk][1]:+d})")
print()
print("notes: policies additive in (mu, M2) to first order (ins x dev cross")
print("terms banked as aggregate, not applied — tiny; suppression x dev")
print("interactions live only through global mu/var); selection is an argmin —")
print("winner's curse applies at the play level (min cell rounds "
      f"{MIN_CELL_ROUNDS}); the")
print("chosen card gets fresh-seed OOS certification before the felt. Dev")
print(f"plays exist only at bins >= {DEV_MIN:+d} (the replay window); e16 dev "
      "pairs say")
print("bins 0/+1 carry ~+0.06-0.07%/round of EV-max value at floor bets —")
print("unmodeled here, worth ~$1-2/h, none of it variance-relevant.")
