"""M10b verdict: the Silver Stack (Pot of Gold PT1) attack, priced from bins.

    uv run python data/m10b_verdict.py

Inputs: data/m10b_rf_p75_s01..05.json (IN-SAMPLE — threshold search) and
s06..10.json (OUT-OF-SAMPLE — the deep-dive replication discipline: the
threshold is chosen on A and scored blind on B). Bins carry side and main
profit moments separately, so every mode below is arithmetic:

  SEATED: bet $MAIN every round (the Ride Free toll), stake $SIDE on
          Pot of Gold only when the pre-deal hi-lo TC bin <= t.
  WONG:   play only rounds with TC bin <= t (main + side), back-count
          otherwise; the observed-rounds pace discount is the caller's
          problem (quoted per 100 observed rounds like E12/E14).

Threshold convention: bins are round(tc) clamped to +/-12, so "t" means
tc < t + 0.5. Human-card distillation (RC form, live visibility) is a later
step — these are tracker-convention curves (hole card visible at settlement,
the E16/E17 convention).

Variance note: bins do not carry the main-x-side cross moment; seated sd
below sets cov(main, side) = 0 and is flagged approximate. The chosen
operating point gets a live verification run (E16 discipline) which measures
realized combined variance directly.
"""

import math

from ridefree.experiments import load_pog_curve_json, merge_pog_curves

IN_SAMPLE = [f"data/m10b_rf_p75_s{i:02d}.json" for i in range(1, 6)]
OOS = [f"data/m10b_rf_p75_s{i:02d}.json" for i in range(6, 11)]

MAIN_BET = 15.0
SIDE_STAKES = (25.0, 50.0, 100.0)
PACES = (100, 200)  # rounds/h seated (heads-up vs crowded is the caller's map)
CROUCH15_BENCHMARK = 40.0  # $/h, the locked weekday card (E18b), for context


def window(res, t):
    """Pooled stats for bins <= t: (rounds, side profit, side sq, main profit)."""
    n = sp = sq = mp = 0.0
    for k, b in res.bins.items():
        if k <= t:
            n += b.rounds
            sp += b.pog_profit
            sq += b.pog_sq
            mp += b.main_profit
    return n, sp, sq, mp


def side_stats(res, t):
    n, sp, sq, _ = window(res, t)
    if n < 2:
        return 0.0, 0.0, 0.0
    ev = sp / n
    var = max(sq / n - ev * ev, 0.0)
    return n / res.rounds, ev, math.sqrt(var / n)


def main() -> None:
    a = merge_pog_curves([load_pog_curve_json(p) for p in IN_SAMPLE])
    b = merge_pog_curves([load_pog_curve_json(p) for p in OOS])
    both = merge_pog_curves([load_pog_curve_json(p) for p in IN_SAMPLE + OOS])

    main_ev_all = a.main_total / a.rounds  # seated toll rate, in-sample
    print(f"in-sample {a.rounds:,} rounds; OOS {b.rounds:,} rounds; "
          f"pen {a.penetration:.2f}; paytable "
          f"{'/'.join(f'{p:g}' for p in a.paytable)}")
    print(f"always-on numbers (in-sample): pog {100 * a.pog_total / a.rounds:+.4f}%"
          f"   main {100 * main_ev_all:+.4f}%")

    print("\n--- threshold search (IN-SAMPLE): side EV per unit in the window ---")
    print(f"  {'t':>4s} {'freq':>8s} {'side EV':>9s} {'±1se':>8s} "
          f"{'z>0':>6s} {'$/h seated @200r/h, side $100':>30s}")
    candidates = range(-12, 1)
    best_t, best_hourly = None, -1e9
    for t in candidates:
        f, ev, se = side_stats(a, t)
        if f == 0.0:
            continue
        z = ev / se if se else 0.0
        hourly = 200 * (MAIN_BET * main_ev_all + f * 100.0 * ev)
        flag = ""
        if z > 2 and hourly > best_hourly:
            best_t, best_hourly, flag = t, hourly, "  <-- best z>2"
        print(f"  {t:+4d} {100 * f:7.3f}% {100 * ev:+8.3f}% {100 * se:7.3f}% "
              f"{z:+6.2f} {hourly:>+29.2f}{flag}")

    if best_t is None:
        print("\nNO threshold clears z>2 in-sample: the attack fails at this pen.")
        return

    print(f"\n--- OUT-OF-SAMPLE replication at t* = {best_t:+d} ---")
    fa, ea, sa = side_stats(a, best_t)
    fb, eb, sb = side_stats(b, best_t)
    zd = (ea - eb) / math.sqrt(sa * sa + sb * sb)
    print(f"  in-sample : freq {100 * fa:.3f}%  side EV {100 * ea:+.3f}% ± {100 * sa:.3f}%")
    print(f"  OOS       : freq {100 * fb:.3f}%  side EV {100 * eb:+.3f}% ± {100 * sb:.3f}%"
          f"   (A-B z = {zd:+.2f})")
    oos_pass = eb - 2 * sb > 0
    print(f"  OOS side EV > 0 at 2se: {'PASS' if oos_pass else 'FAIL'}")

    print(f"\n--- the ledger (POOLED 20M, t* = {best_t:+d}; "
          f"main ${MAIN_BET:g} every round) ---")
    f, ev, se = side_stats(both, best_t)
    main_ev = both.main_total / both.rounds
    n_win, _, sq_win, mp_win = window(both, best_t)
    main_ev_win = mp_win / n_win
    print(f"  trigger: {100 * f:.3f}% of rounds; side EV {100 * ev:+.3f}% ± "
          f"{100 * se:.3f}%; main EV inside window {100 * main_ev_win:+.3f}% "
          f"(vs {100 * main_ev:+.3f}% overall)")
    ev2_win = sq_win / n_win
    print(f"\n  {'mode':<8s} {'side':>6s} {'pace':>6s} {'toll $/h':>9s} "
          f"{'side $/h':>9s} {'net $/h':>9s} {'sd/round':>9s} {'N0 h':>7s} "
          f"{'bank 5%':>9s}")
    for stake in SIDE_STAKES:
        for pace in PACES:
            toll = pace * MAIN_BET * main_ev
            side = pace * f * stake * ev
            net = toll + side
            # sd per SEATED round, cov(main,side)=0 approximation (the live
            # verification run measures realized combined variance):
            var_main = 1.067 ** 2 * MAIN_BET ** 2
            var_side = f * (stake ** 2) * ev2_win - (f * stake * ev) ** 2
            sd = math.sqrt(var_main + var_side)
            mu_round = net / pace
            n0 = (sd * math.sqrt(pace) / net) ** 2 if net > 0 else float("inf")
            bank = (3.0 * sd * sd / (2 * mu_round)) if net > 0 else float("inf")
            print(f"  {'seated':<8s} {stake:>5.0f} {pace:>5d}r "
                  f"{toll:>+9.2f} {side:>+9.2f} {net:>+9.2f} {sd:>9.1f} "
                  f"{n0:>7.0f} {bank:>9,.0f}")
    print(f"\n  wong-in (play only TC<=t rounds, main+side; cov≈0 sd, "
          f"per TRIGGERED round):")
    for stake in SIDE_STAKES:
        mu_trig = MAIN_BET * main_ev_win + stake * ev
        var_trig = 1.1 ** 2 * MAIN_BET ** 2 + (stake ** 2) * (ev2_win - ev * ev)
        sd_trig = math.sqrt(var_trig)
        bank = 3.0 * var_trig / (2 * mu_trig) if mu_trig > 0 else float("inf")
        net100 = 100 * f * mu_trig
        print(f"    side ${stake:>3.0f}: {net100:+8.2f} per 100 observed "
              f"(200 obs/h heads-up -> {2 * net100:+8.2f}/h)   "
              f"sd {sd_trig:.0f}/trig round, bank 5% ≈ ${bank:,.0f}")
    print(f"\n  context: crouch15-2r weekday benchmark ≈ +${CROUCH15_BENCHMARK:.0f}/h "
          f"(E18b) on the classic tables next door.")


if __name__ == "__main__":
    main()
