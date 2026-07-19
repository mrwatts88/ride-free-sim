"""E22b verdict (Matt's simplicity question): what do the SIMPLE counts
cost vs the certified pog2 card?

    uv run python data/e22b_verdict.py

Inputs: data/e22b_cc_p75_s01..10.json (data/e22b_run.py; 10 x 2M farm-arm
rounds, fresh seeds 19.4-20.3e9) — hilo_tc / pog2_rc / ko_rc / simple_rc
on one card stream — plus the banked E22 EOR shards for the tag-level BCs.

The two candidates:
  ko_rc     = Matt's variant A = the published KO count (transferability!).
              Pivot +4 -> the side trigger sits 6 points off-pivot.
  simple_rc = Matt's variant B = pog2 without the red-2 gadget. BALANCED
              (pivot 0) -> its no-division trigger is a fixed RC, the
              depth compromise.
Discipline: rung chosen on s01..05 (A) by untied capture, scored blind on
s06..10 (B); pooled numbers at the A rung. Ledger conventions as E22
(EV_OUT -0.95% outside toll; farm-arm window main; cov=0).
"""

import math

from ridefree.counting import HILO_TAGS
from ridefree.experiments import (
    load_pog_count_curves_json,
    load_pog_eor_json,
    merge_pog_count_curves,
    merge_pog_eors,
    solve_pog_eors,
    unbalanced_bc,
)

SHARDS = [f"data/e22b_cc_p75_s{i:02d}.json" for i in range(1, 11)]
EOR_SHARDS = [f"data/e22_eor_p75_s{i:02d}.json" for i in range(1, 6)]
MAIN_BET = 15.0
EV_OUT = -0.0095
SIGNALS = ("hilo_tc", "pog2_rc", "ko_rc", "simple_rc")
TAGS = {
    "hilo_tc": {r: float(HILO_TAGS[r]) for r in range(1, 11)},
    "pog2_rc": {1: -1, 2: 0.5, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 0, 9: 0,
                10: -1},
    "ko_rc": {1: -1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 0, 9: 0, 10: -1},
    "simple_rc": {1: -1, 2: 1, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 0, 9: 0,
                  10: -1},
}


def win_stats(res, signal, t):
    n = sp = sq = mp = 0.0
    for k, b in res.by_signal[signal].items():
        if k <= t:
            n += b.rounds
            sp += b.pog_profit
            sq += b.pog_sq
            mp += b.main_profit
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    return n / res.rounds, sp / n, mp / n, sq / n


def sweep_untied(res, signal):
    best_t, best = None, -1e18
    for t in sorted(res.by_signal[signal]):
        f, evs, _, _ = win_stats(res, signal, t)
        if f == 0.0 or f > 0.60:
            continue
        if f * evs > best:
            best_t, best = t, f * evs
    return best_t


def main() -> None:
    eors = solve_pog_eors(merge_pog_eors(
        [load_pog_eor_json(p) for p in EOR_SHARDS]))["side"]
    print("tag-level lammer quality (BC vs the E22 side EORs; more negative "
          "= better bet-low count):")
    for name in SIGNALS:
        print(f"  {name:<10s} {unbalanced_bc(TAGS[name], eors):+.4f}")

    parts = [load_pog_count_curves_json(p) for p in SHARDS]
    a = merge_pog_count_curves(parts[:5])
    b = merge_pog_count_curves(parts[5:])
    pool = merge_pog_count_curves(parts)
    print(f"\npooled {pool.rounds:,} rounds/signal (A {a.rounds:,} chooses, "
          f"B {b.rounds:,} scores), pen {pool.penetration:.2f}, arm "
          f"{pool.arm}")

    print(f"\n--- head-to-head, untied objective (A rung, B blind, pooled) ---")
    print(f"  {'signal':<10s} {'rung':>5s} {'freq':>8s} {'side EV':>9s} "
          f"{'±1se':>7s} {'B side EV':>10s} {'cap/100':>8s} {'vs hilo':>8s} "
          f"{'vs pog2':>8s}")
    caps = {}
    rows = []
    for signal in SIGNALS:
        t = sweep_untied(a, signal)
        fp, evp, evmp, sqp = win_stats(pool, signal, t)
        fb, evb, _, _ = win_stats(b, signal, t)
        se = math.sqrt(max(sqp - evp * evp, 0.0) / (fp * pool.rounds))
        caps[signal] = fp * evp
        rows.append((signal, t, fp, evp, se, evb, evmp, sqp))
    for signal, t, fp, evp, se, evb, evmp, _ in rows:
        print(f"  {signal:<10s} {t:>+5d} {100 * fp:7.3f}% {100 * evp:+8.3f}% "
              f"{100 * se:6.3f}% {100 * evb:+9.3f}% "
              f"{100 * fp * evp:>+8.3f} "
              f"{100 * caps[signal] / caps['hilo_tc']:>7.1f}% "
              f"{100 * caps[signal] / caps['pog2_rc']:>7.1f}%")

    print(f"\n--- the simplicity ledger (untied seated, 200 r/h, $15 main "
          f"outside; net $/h at the A rung) ---")
    print(f"  {'signal':<10s} {'$25':>8s} {'$50':>8s} {'$100':>9s}")
    for signal, t, fp, evp, se, evb, evmp, sqp in rows:
        out_toll = 200 * (1 - fp) * MAIN_BET * EV_OUT
        nets = []
        for stake in (25.0, 50.0, 100.0):
            nets.append(out_toll + 200 * fp * (MAIN_BET * evmp + stake * evp))
        print(f"  {signal:<10s} {nets[0]:>+8.2f} {nets[1]:>+8.2f} "
              f"{nets[2]:>+9.2f}")

    print("\nnotes: simple_rc IS pog2 minus the red-2 gadget — the gadget "
          "only pins the pivot at -2; if you are willing to DIVIDE, "
          "simple/decks-left recovers ~pog2 quality (same tags to within "
          "the half-2), but division is what these cards exist to avoid. "
          "ko_rc is the published KO count: its tags are fine, its pivot "
          "(+4) is six points from the trigger.")


if __name__ == "__main__":
    main()
