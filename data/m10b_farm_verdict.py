"""E21 verdict: the farm arm — split 5s while the Silver Stack window is open.

    uv run python data/m10b_farm_verdict.py

Inputs: data/m10b_rf_p75_s01..10.json (E20 normal arm, banked: main-EV-optimal
5,5, i.e. take the free double) and data/m10b_farm_p75_s01..10.json (farm arm:
SplitFives — free-split 5s and re-splits — run on the SAME seed shard for
shard). Paired arms share shoes until a 5,5 decision diverges, so the
farm-minus-normal delta is a common-random-numbers measurement: errors on
deltas below are the sd across the 10 paired shard deltas, not the pooled
per-round sd. E20's threshold t* = -3 is LOCKED (chosen in-sample there,
OOS-replicated); this script prices the farm INSIDE that window and re-checks
the threshold under farming with the same A/B discipline (s01..05 choose,
s06..10 score).

The stake-aware rule being priced: the side stake is out only when TC <= t;
while it is out, splitting 5s converts one free double (1 lammer) into a
split chain (>= 1 lammer, expected ~2+), trading main-bet EV for side-bet EV.
Farm in bin k iff SIDE * d_side(k) + MAIN * d_main(k) > 0. Outside the window
no side is staked, so farming is never right there and the mixed ledger uses
normal bins outside / farm bins inside.

Convention notes: bins are round(tc) clamped to +/-12 ("t" means tc < t+0.5);
tracker sees the full RoundResult at settlement (E16/E17). Cross-round
contamination (farm history shifting later same-shoe bins beyond what TC
conditioning absorbs) is second-order and inherited from E20's convention;
the live verification run retires it. Seated sd sets cov(main, side) = 0 as
in E20.
"""

import json
import math

from ridefree.experiments import load_pog_curve_json, merge_pog_curves

NORMAL = [f"data/m10b_rf_p75_s{i:02d}.json" for i in range(1, 11)]
FARM = [f"data/m10b_farm_p75_s{i:02d}.json" for i in range(1, 11)]

T_STAR = -3  # E20's locked threshold
MAIN_BET = 15.0
SIDE_STAKES = (25.0, 50.0, 100.0)
PACES = (100, 200)
E20_NET = {  # $/h at 200 r/h seated, the pre-farm E20 ledger, for the delta row
    25.0: 9.0, 50.0: 52.0, 100.0: 138.0,
}


def seed_of(path):
    with open(path) as f:
        return json.load(f)["seed"]


def window(res, t):
    """Pooled stats for bins <= t: rounds, side profit, side sq, main profit."""
    n = sp = sq = mp = 0.0
    for k, b in res.bins.items():
        if k <= t:
            n += b.rounds
            sp += b.pog_profit
            sq += b.pog_sq
            mp += b.main_profit
    return n, sp, sq, mp


def win_evs(res, t):
    n, sp, sq, mp = window(res, t)
    return (sp / n if n else 0.0), (mp / n if n else 0.0), n


def paired(norms, farms, stat):
    """Mean +/- se of stat(farm_i) - stat(normal_i) across paired shards."""
    ds = [stat(f) - stat(a) for a, f in zip(norms, farms)]
    m = sum(ds) / len(ds)
    var = sum((d - m) ** 2 for d in ds) / (len(ds) - 1)
    return m, math.sqrt(var / len(ds))


def mixed_ledger(norm_pool, farm_pool, t, farming: bool):
    """Seated economics: main every round (normal bins outside the window,
    farm bins inside when `farming`), side staked only in the window."""
    src = farm_pool if farming else norm_pool
    n_win, sp_win, sq_win, mp_win = window(src, t)
    f = n_win / src.rounds
    ev_side = sp_win / n_win
    ev2_side = sq_win / n_win
    # Mixed main: normal pool outside + chosen arm inside.
    n_win_n, _, _, mp_win_n = window(norm_pool, t)
    out_profit = norm_pool.main_total - mp_win_n
    out_rounds = norm_pool.rounds - n_win_n
    main_ev = (out_profit + mp_win) / (out_rounds + n_win)
    return f, ev_side, ev2_side, main_ev


def main() -> None:
    for a, b in zip(NORMAL, FARM):
        assert seed_of(a) == seed_of(b), f"unpaired shards: {a} vs {b}"
    norms = [load_pog_curve_json(p) for p in NORMAL]
    farms = [load_pog_curve_json(p) for p in FARM]
    norm_pool = merge_pog_curves(norms)
    farm_pool = merge_pog_curves(farms)
    assert norm_pool.arm == "normal" and farm_pool.arm == "farm"
    assert norm_pool.penetration == farm_pool.penetration

    print(f"paired shards: {len(norms)} x {norms[0].rounds:,} rounds/arm; "
          f"pen {norm_pool.penetration:.2f}; paytable "
          f"{'/'.join(f'{p:g}' for p in norm_pool.paytable)}")
    d_all, se_all = paired(norms, farms, lambda r: r.pog_total / r.rounds)
    dm_all, sem_all = paired(norms, farms, lambda r: r.main_total / r.rounds)
    print(f"always-on (all rounds): side delta {100 * d_all:+.3f}% ± "
          f"{100 * se_all:.3f}% (M10a csm gate: +3.080 ± 0.185; WoO +3.019)   "
          f"main delta {100 * dm_all:+.3f}% ± {100 * sem_all:.3f}% "
          f"(gate -0.173; WoO -0.15)")

    print("\n--- per-bin farm-minus-normal deltas (paired se; negative bins) ---")
    print(f"  {'tc':>4s} {'rounds':>11s} {'normal EV':>10s} {'farm EV':>10s} "
          f"{'d side':>8s} {'±1se':>7s} {'d main':>8s} {'±1se':>7s} "
          f"{'side* $':>8s}")
    for k in sorted(norm_pool.bins):
        if k > 0 or norm_pool.bins[k].rounds < 50_000:
            continue
        nb, fb = norm_pool.bins[k], farm_pool.bins[k]
        ds, ses = paired(norms, farms, lambda r, k=k: r.bins[k].pog_ev)
        dm, sem = paired(norms, farms, lambda r, k=k: r.bins[k].main_ev)
        breakeven = MAIN_BET * -dm / ds if ds > 0 else float("inf")
        print(f"  {k:+4d} {nb.rounds:>11,d} {100 * nb.pog_ev:+9.3f}% "
              f"{100 * fb.pog_ev:+9.3f}% {100 * ds:+7.3f}% {100 * ses:6.3f}% "
              f"{100 * dm:+7.3f}% {100 * sem:6.3f}% {breakeven:>8.2f}")
    print("  (side* = side stake above which farming beats the free double "
          "in that bin, at $15 main)")

    print(f"\n--- the window (t* = {T_STAR:+d}, LOCKED from E20) ---")
    ds_win, ses_win = paired(norms, farms, lambda r: win_evs(r, T_STAR)[0])
    dm_win, sem_win = paired(norms, farms, lambda r: win_evs(r, T_STAR)[1])
    ev_n, evm_n, n_win_n = win_evs(norm_pool, T_STAR)
    ev_f, evm_f, n_win_f = win_evs(farm_pool, T_STAR)
    print(f"  side EV : normal {100 * ev_n:+.3f}%  farm {100 * ev_f:+.3f}%  "
          f"delta {100 * ds_win:+.3f}% ± {100 * ses_win:.3f}% (paired)")
    print(f"  main EV : normal {100 * evm_n:+.3f}%  farm {100 * evm_f:+.3f}%  "
          f"delta {100 * dm_win:+.3f}% ± {100 * sem_win:.3f}% (paired)")
    for stake in SIDE_STAKES:
        net = stake * ds_win + MAIN_BET * dm_win
        print(f"    side ${stake:>3.0f}: farm nets {100 * net:+7.2f}% of $1 "
              f"per window round -> {'FARM' if net > 0 else 'do not farm'}")

    print("\n--- A/B discipline on the farm delta (chosen on physics, "
          "scored anyway) ---")
    da, sea = paired(norms[:5], farms[:5], lambda r: win_evs(r, T_STAR)[0])
    db, seb = paired(norms[5:], farms[5:], lambda r: win_evs(r, T_STAR)[0])
    zd = (da - db) / math.sqrt(sea * sea + seb * seb)
    print(f"  in-sample delta {100 * da:+.3f}% ± {100 * sea:.3f}%   "
          f"OOS {100 * db:+.3f}% ± {100 * seb:.3f}%   (A-B z = {zd:+.2f}; "
          f"OOS > 0 at 2se: {'PASS' if db - 2 * seb > 0 else 'FAIL'})")

    print("\n--- threshold re-check under farming (A chooses, B scores; "
          "$100 side @200 r/h) ---")
    a_norm, a_farm = merge_pog_curves(norms[:5]), merge_pog_curves(farms[:5])
    b_norm, b_farm = merge_pog_curves(norms[5:]), merge_pog_curves(farms[5:])
    best_t, best_hourly = None, -1e9
    for t in range(-12, 1):
        f, ev, _, mev = mixed_ledger(a_norm, a_farm, t, farming=True)
        if f == 0.0:
            continue
        n, sp, sq, _ = window(a_farm, t)
        se = math.sqrt(max(sq / n - (sp / n) ** 2, 0.0) / n)
        hourly = 200 * (MAIN_BET * mev + f * 100.0 * ev)
        if ev / se > 2 and hourly > best_hourly:
            best_t, best_hourly = t, hourly
    f_b, ev_b, _, mev_b = mixed_ledger(b_norm, b_farm, best_t, farming=True)
    print(f"  A picks t = {best_t:+d} (${best_hourly:+.2f}/h); B at that t: "
          f"side {100 * ev_b:+.3f}%, freq {100 * f_b:.3f}%, "
          f"${200 * (MAIN_BET * mev_b + f_b * 100.0 * ev_b):+.2f}/h"
          f"{'   (same t* as E20)' if best_t == T_STAR else '   <-- MOVED'}")

    for t in dict.fromkeys((T_STAR, best_t)):  # print each threshold once
        print_ledger(norm_pool, farm_pool, t,
                     e20_net=E20_NET if t == T_STAR else None)


def print_ledger(norm_pool, farm_pool, t, e20_net=None) -> None:
    tag = "LOCKED E20 t*" if e20_net else "farm-era t* (A/B above)"
    print(f"\n--- the farm-mixed ledger (POOLED 20M/arm, t = {t:+d} [{tag}]; "
          f"main ${MAIN_BET:g} every round, farm iff side out) ---")
    f, ev, ev2, main_ev = mixed_ledger(norm_pool, farm_pool, t, True)
    print(f"  trigger {100 * f:.3f}% of rounds; window side EV {100 * ev:+.3f}%; "
          f"mixed main EV {100 * main_ev:+.4f}% "
          f"(E20 no-farm: {100 * norm_pool.main_total / norm_pool.rounds:+.4f}%)")
    print(f"\n  {'side':>6s} {'pace':>6s} {'toll $/h':>9s} {'side $/h':>9s} "
          f"{'net $/h':>9s} {'E20 net':>8s} {'sd/round':>9s} {'N0 h':>7s} "
          f"{'bank 5%':>9s}")
    for stake in SIDE_STAKES:
        for pace in PACES:
            toll = pace * MAIN_BET * main_ev
            side = pace * f * stake * ev
            net = toll + side
            var_main = 1.067 ** 2 * MAIN_BET ** 2
            var_side = f * (stake ** 2) * ev2 - (f * stake * ev) ** 2
            sd = math.sqrt(var_main + var_side)
            mu_round = net / pace
            n0 = (sd * math.sqrt(pace) / net) ** 2 if net > 0 else float("inf")
            bank = (3.0 * sd * sd / (2 * mu_round)) if net > 0 else float("inf")
            e20 = (f"{e20_net[stake]:+8.0f}" if e20_net and pace == 200
                   else f"{'':>8s}")
            print(f"  {stake:>5.0f} {pace:>5d}r {toll:>+9.2f} {side:>+9.2f} "
                  f"{net:>+9.2f} {e20} {sd:>9.1f} {n0:>7.0f} {bank:>9,.0f}")
    breakeven = -(MAIN_BET * main_ev) / (f * ev)
    print(f"\n  breakeven side stake (seated, any pace): ${breakeven:.2f} "
          f"(pre-farm E20 note said ~$20)")
    print(f"  wong-in (play only TC<={t} rounds, farm always) per 100 "
          f"observed rounds:")
    n_win, _, _, mp_win = window(farm_pool, t)
    evm_win = mp_win / n_win
    for stake in SIDE_STAKES:
        mu_trig = MAIN_BET * evm_win + stake * ev
        net100 = 100 * f * mu_trig
        print(f"    side ${stake:>3.0f}: {net100:+8.2f} per 100 observed "
              f"(200 obs/h heads-up -> {2 * net100:+8.2f}/h)")


if __name__ == "__main__":
    main()
