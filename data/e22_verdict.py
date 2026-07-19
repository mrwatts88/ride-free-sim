"""E22 stage 2 verdict: the no-division Silver Stack card, certified.

    uv run python data/e22_verdict.py

Inputs: data/e22_cc_p75_s01..10.json (data/e22_run.py; 10 x 2M farm-arm
rounds, RIDE_FREE + PT1 cut_card pen .75, fresh seeds 18.4e9-19.3e9).
Every shard bins side/main profit by THREE signals on the same card stream
(differences between signals are pure capture, no shoe noise):

  hilo_tc  — the E20/E21 division benchmark (±12 TC bins)
  pog2_rc  — the stage-1 specialist (pivot -2; RC 0 == TC -2 at any depth)
  red7_rc  — Matt's drilled Red 7 (pivot +2; RC 0 == TC +2; the side
             trigger sits ~4 points off-pivot — this measures the mush)

Discipline: rung chosen on s01..05 (A), scored blind on s06..10 (B), pooled
numbers reported at the A-chosen rung. Scenario objectives:
  untied:   maximize freq * side EV (the side max is its own placard)
  matched:  maximize freq * (S*(side+main) - 15*main) at S=100 (E21b's
            raise-on-trigger world; farm-arm main is the $15 baseline too —
            ~0.1pp approximation, flagged)

Consistency gate: this run's hilo_tc <= -2 window must replicate E21's
pooled +7.26% @ 20.85% (fresh seeds — an OOS replication of E21 itself).
"""

import math

from ridefree.experiments import (
    load_pog_count_curves_json,
    merge_pog_count_curves,
)

SHARDS = [f"data/e22_cc_p75_s{i:02d}.json" for i in range(1, 11)]
E21_WINDOW = (0.07263, 0.20848)  # pooled farm side EV, freq at hilo tc<=-2
MAIN_BET = 15.0
# Normal-arm main EV on NON-staked rounds (you don't farm unstaked): from the
# E21 pools, overall normal -1.1271% with the pog2-window share removed.
EV_OUT = -0.0095


def window(bins, t):
    n = sp = sq = mp = 0.0
    for k, b in bins.items():
        if k <= t:
            n += b.rounds
            sp += b.pog_profit
            sq += b.pog_sq
            mp += b.main_profit
    return n, sp, sq, mp


def win_stats(res, signal, t):
    bins = res.by_signal[signal]
    n, sp, sq, mp = window(bins, t)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    return n / res.rounds, sp / n, mp / n, sq / n


def sweep(res, signal, objective):
    keys = sorted(res.by_signal[signal])
    best_t, best = None, -1e18
    for t in keys:
        f, evs, evm, _ = win_stats(res, signal, t)
        if f == 0.0 or f > 0.60:
            continue
        v = objective(f, evs, evm)
        if v > best:
            best_t, best = t, v
    return best_t, best


def main() -> None:
    parts = [load_pog_count_curves_json(p) for p in SHARDS]
    a = merge_pog_count_curves(parts[:5])
    b = merge_pog_count_curves(parts[5:])
    pool = merge_pog_count_curves(parts)
    print(f"pooled {pool.rounds:,} rounds/signal (A {a.rounds:,} chooses, "
          f"B {b.rounds:,} scores), pen {pool.penetration:.2f}, arm {pool.arm}")

    f, evs, _, _ = win_stats(pool, "hilo_tc", -2)
    ze = (evs - E21_WINDOW[0]) / 0.0009  # ~se of the window EV at 20M
    print(f"\nE21 replication gate (hilo tc<=-2, FRESH seeds): side EV "
          f"{100 * evs:+.3f}% @ {100 * f:.2f}% vs E21 {100 * E21_WINDOW[0]:+.3f}% "
          f"@ {100 * E21_WINDOW[1]:.2f}%  (z ~ {ze:+.1f})  "
          f"{'PASS' if abs(ze) < 3 else 'FAIL'}")

    untied = lambda f, evs, evm: f * evs  # noqa: E731
    # matched raise-on-trigger at S=100: the t-dependent part of net/round is
    # f * (S*(side+main) - $15*ev_out) — window rounds swap a $15 main at the
    # outside EV for S staked at farm window EVs.
    matched = lambda f, evs, evm: f * (100 * (evs + evm) - MAIN_BET * EV_OUT)  # noqa: E731

    print("\n--- head-to-head (rung chosen on A, scored on B, reported pooled) ---")
    print(f"  {'signal':<9s} {'scenario':<8s} {'rung':>5s} {'freq':>8s} "
          f"{'side EV':>9s} {'±1se':>7s} {'B side EV':>10s} "
          f"{'capture/100':>11s} {'vs hi-lo':>8s}")
    reference = {}
    for scen_name, obj in (("untied", untied), ("matched", matched)):
        t_hilo, _ = sweep(a, "hilo_tc", obj)
        fh, evh, _, _ = win_stats(pool, "hilo_tc", t_hilo)
        reference[scen_name] = fh * evh
        for signal in ("hilo_tc", "pog2_rc", "red7_rc"):
            t, _ = sweep(a, signal, obj)
            fp, evp, evmp, sqp = win_stats(pool, signal, t)
            fb, evb, _, _ = win_stats(b, signal, t)
            n_win = fp * pool.rounds
            se = math.sqrt(max(sqp - evp * evp, 0.0) / n_win)
            cap = 100 * fp * evp
            eff = cap / (100 * reference[scen_name])
            print(f"  {signal:<9s} {scen_name:<8s} {t:>+5d} {100 * fp:7.3f}% "
                  f"{100 * evp:+8.3f}% {100 * se:6.3f}% {100 * evb:+9.3f}% "
                  f"{cap:>+11.3f} {100 * eff:>7.1f}%")

    print("\n  capture/100 = side units per 100 observed rounds per unit "
          "stake; vs hi-lo = same-stream efficiency against the division "
          "benchmark's A-chosen window.")

    print("\n--- the winner's rung menu (pooled; pog2_rc unless beaten) ---")
    sig = "pog2_rc"
    bins = pool.by_signal[sig]
    print(f"  {'RC<=':>5s} {'freq':>8s} {'side EV':>9s} {'untied $/h '
          f'$50':>14s} {'$100':>9s} {'matched $/h $100':>17s}")
    for t in range(6, -13, -2):
        fp, evp, evmp, _ = win_stats(pool, sig, t)
        if fp == 0.0:
            continue
        u50 = 200 * fp * 50 * evp
        u100 = 200 * fp * 100 * evp
        m100 = 200 * fp * (100 * (evp + evmp) - MAIN_BET * EV_OUT)
        print(f"  {t:>+5d} {100 * fp:7.3f}% {100 * evp:+8.3f}% "
              f"{u50:>+14.2f} {u100:>+9.2f} {m100:>+17.2f}")
    print("\n  (untied $/h columns are the SIDE INCOME leg only; matched "
          "column is the t-dependent net swing of raise-on-trigger at $100 "
          "— add the flat $15-main toll legs for absolute net, as in the "
          "card ledger below.)")

    print("\n--- THE CARD (pog2_rc, stake at RC <= 0 = the pivot; both "
          "scenarios pick the same rung) ---")
    print("  tags: A -1, ten -1, 3/4/6/7 +1, RED 2s +1 (black 2s 0), "
          "5/8/9 nothing; pivot-zeroed IRC +12 (slide +12 for a "
          "no-negatives card: start 24, stake at <= 12).")
    f0, ev0, evm0, sq0 = win_stats(pool, sig, 0)
    out_toll = 200 * (1 - f0) * MAIN_BET * EV_OUT  # $15 main, normal play
    print(f"  (outside toll {out_toll:+.2f}/h at 200 r/h; window main "
          f"{100 * evm0:+.3f}% farm-arm)")
    print(f"\n  {'mode':<12s} {'side':>5s} {'net $/h':>9s} {'sd/rnd':>7s} "
          f"{'N0 h':>6s} {'bank 5%':>9s}")
    for stake in (25.0, 50.0, 100.0):
        net = out_toll + 200 * f0 * (MAIN_BET * evm0 + stake * ev0)
        var = (1.067 * MAIN_BET) ** 2 + f0 * stake ** 2 * sq0 - (
            f0 * stake * ev0) ** 2
        sd = math.sqrt(var)
        n0 = var / (net / 200) ** 2 / 200 if net > 0 else float("inf")
        bank = 1.5 * var / (net / 200) if net > 0 else float("inf")
        print(f"  {'untied':<12s} {stake:>5.0f} {net:>+9.2f} {sd:>7.1f} "
              f"{n0:>6.0f} {bank:>9,.0f}")
    for stake in (25.0, 50.0, 100.0):
        # matched 1:1 raise-on-trigger: main raised to the stake in-window.
        net = out_toll + 200 * f0 * stake * (ev0 + evm0)
        var = ((1.067 * MAIN_BET) ** 2 * (1 - f0)
               + f0 * ((1.067 * stake) ** 2 + stake ** 2 * (sq0 - ev0 * ev0)))
        sd = math.sqrt(var)
        n0 = var / (net / 200) ** 2 / 200 if net > 0 else float("inf")
        bank = 1.5 * var / (net / 200) if net > 0 else float("inf")
        print(f"  {'matched 1:1':<12s} {stake:>5.0f} {net:>+9.2f} {sd:>7.1f} "
              f"{n0:>6.0f} {bank:>9,.0f}")


if __name__ == "__main__":
    main()
