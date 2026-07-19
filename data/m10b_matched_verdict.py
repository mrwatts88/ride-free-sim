"""E21b: what if the Silver Stack stake must be <= the main bet? (Matt's
question, 2026-07-18.) Priced entirely from the banked E20/E21 bins — no new
simulation.

    uv run python data/m10b_matched_verdict.py

Scenario: the placard ties the side bet to the main wager (side <= main, or
side <= main/2 — both priced). The play changes form: main stays at the $15
table min outside the window; on trigger rounds you RAISE the main to
side/ratio and farm. Note the optics: the main bet goes UP when the count
goes DOWN — anti-correlated with hi-lo, the opposite of a counter's tell.

Per-stake threshold is re-chosen under the constraint with the E20 ceremony
(s01..05 choose by seated hourly, s06..10 score blind), because the marginal
bin now pays S*side_EV + main_win*main_EV - $15*main_EV_normal and the
boundary moves with S and the ratio.

Variance here uses the MEASURED per-bin main second moments (main_sq), split
window/outside — slightly better than E21's flat 1.067u main sd — with
cov(main, side) = 0 inside the window as before (live verification retires
it). Farming stays on in the window under every ratio: its main cost is
~40x smaller than its side gain at any stake that clears the constraint.
"""

import math

from ridefree.experiments import load_pog_curve_json, merge_pog_curves

NORMAL = [f"data/m10b_rf_p75_s{i:02d}.json" for i in range(1, 11)]
FARM = [f"data/m10b_farm_p75_s{i:02d}.json" for i in range(1, 11)]

MAIN_MIN = 15.0
SIDE_STAKES = (25.0, 50.0, 100.0)
RATIOS = (None, 1.0, 0.5)  # None = unconstrained (the E21 world), else side<=ratio*main
PACE = 200  # r/h heads-up; $/h scales linearly, N0 hours inversely, bank unchanged


def win_out(norm, farm, t):
    """Window moments from the FARM pool, outside moments from the NORMAL
    pool (that is what the mixed strategy plays), all per unit staked."""
    nw = sp = sq = mp = mq = 0.0
    for k, b in farm.bins.items():
        if k <= t:
            nw += b.rounds
            sp += b.pog_profit
            sq += b.pog_sq
            mp += b.main_profit
            mq += b.main_sq
    no = op = oq = 0.0
    for k, b in norm.bins.items():
        if k > t:
            no += b.rounds
            op += b.main_profit
            oq += b.main_sq
    return nw, sp / nw, sq / nw, mp / nw, mq / nw, no, op / no, oq / no


def seated(norm, farm, t, side, main_win):
    """Per-round mean/variance in dollars: $15 main outside, main_win + side
    (farmed) inside the window."""
    nw, evs, es2, evm, em2, no, evo, eo2 = win_out(norm, farm, t)
    pw = nw / (nw + no)
    po = 1.0 - pw
    mu = po * MAIN_MIN * evo + pw * (main_win * evm + side * evs)
    ex2 = (po * MAIN_MIN ** 2 * eo2
           + pw * (main_win ** 2 * em2 + side ** 2 * es2
                   + 2 * main_win * side * evm * evs))
    return mu, ex2 - mu * mu, pw


def row(norm, farm, t, side, main_win):
    mu, var, pw = seated(norm, farm, t, side, main_win)
    net = PACE * mu
    n0 = var / (mu * mu) / PACE if mu > 0 else float("inf")
    bank = 3.0 * var / (2 * mu) if mu > 0 else float("inf")
    return net, math.sqrt(var), n0, bank, pw


def main() -> None:
    norms = [load_pog_curve_json(p) for p in NORMAL]
    farms = [load_pog_curve_json(p) for p in FARM]
    npool, fpool = merge_pog_curves(norms), merge_pog_curves(farms)
    a_n, a_f = merge_pog_curves(norms[:5]), merge_pog_curves(farms[:5])
    b_n, b_f = merge_pog_curves(norms[5:]), merge_pog_curves(farms[5:])

    print(f"E21b — the side<=main scenario, from banked bins "
          f"({npool.rounds:,} rounds/arm, pen {npool.penetration:.2f}, "
          f"{PACE} r/h seated, farm always on in window)")
    print(f"  ratio: side <= ratio * main; main raised to side/ratio ONLY on "
          f"trigger rounds (${MAIN_MIN:g} min otherwise)\n")

    print(f"  {'ratio':>7s} {'side':>5s} {'main@win':>8s} {'t*':>4s} "
          f"{'B $/h':>8s} {'net $/h':>8s} {'sd/rnd':>7s} {'N0 h':>6s} "
          f"{'bank 5%':>9s}   note")
    for ratio in RATIOS:
        for side in SIDE_STAKES:
            main_win = MAIN_MIN if ratio is None else max(MAIN_MIN, side / ratio)
            best_t, best = None, -1e9
            for t in range(-12, 1):
                mu, _, _ = seated(a_n, a_f, t, side, main_win)
                if PACE * mu > best:
                    best_t, best = t, PACE * mu
            b_net = row(b_n, b_f, best_t, side, main_win)[0]
            net, sd, n0, bank, _ = row(npool, fpool, best_t, side, main_win)
            label = "unconstrained (E21)" if ratio is None else f"{ratio:g}:1"
            note = "" if net > 0 else "  DEAD"
            print(f"  {label:>7s} {side:>5.0f} {main_win:>8.0f} {best_t:>+4d} "
                  f"{b_net:>+8.2f} {net:>+8.2f} {sd:>7.1f} {n0:>6.0f} "
                  f"{bank:>9,.0f}{note}")
        print()

    print("  flat-matched comparison (main = side EVERY round, side in window"
          " — the naive reading, dominated):")
    for side in SIDE_STAKES:
        # main = side all rounds: outside toll scales with side too.
        nw, evs, _, evm, _, no, evo, _ = win_out(npool, fpool, -3)
        pw = nw / (nw + no)
        mu = (1 - pw) * side * evo + pw * side * (evm + evs)
        print(f"    side ${side:>3.0f}: {PACE * mu:>+8.2f}/h at t=-3")

    print("\n  wong-in under the constraint (play only trigger rounds, "
          "main = side/ratio, farm; per 100 observed):")
    for ratio in (1.0, 0.5):
        for side in SIDE_STAKES:
            main_win = max(MAIN_MIN, side / ratio)
            best_t, best = None, -1e9
            for t in range(-12, 1):
                nw, evs, _, evm, _, no, _, _ = win_out(a_n, a_f, t)
                v = (nw / (nw + no)) * (main_win * evm + side * evs)
                if v > best:
                    best_t, best = t, v
            nw, evs, _, evm, _, no, _, _ = win_out(npool, fpool, best_t)
            f = nw / (nw + no)
            net100 = 100 * f * (main_win * evm + side * evs)
            print(f"    {ratio:g}:1 side ${side:>3.0f} (main ${main_win:>3.0f}"
                  f" @win, t={best_t:+d}): {net100:>+8.2f}/100 obs "
                  f"({2 * net100:>+8.2f}/h at 200 obs)")


if __name__ == "__main__":
    main()
