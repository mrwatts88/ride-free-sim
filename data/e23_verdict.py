"""E23 verdict: the literal pog2 card, certified live — and priced at the
2026-07-19 felt constraints ($25 side max, ~100 r/h, deep pen).

    uv run python data/e23_verdict.py

Inputs: data/e23_live_p75_s*.json and data/e23_live_p833_s*.json
(data/e23_run.py: the literal card — pog2 start 24, stake <= 12, farm 5s
while the side is out, flat 1u main, no insurance).

Everything here is realized-moment arithmetic — per-round main/side sums,
squares, and the main*side cross product, split staked/unstaked. No binned
stitch, no cov(main,side)=0, no EV_OUT constant. Gates:

  1. pen .75 staked-round side EV vs the E22 pooled bin prediction
     (+10.13%/unit at 16.5% of rounds, RC <= 0 rung).
  2. pen .75 unstaked main EV vs the EV_OUT ~ -0.95% approximation.

Ledger: $15 main / $25 side (the confirmed max), 100 r/h (the observed
pace), untied AND matched-1:1 raise-on-trigger, at pen .75 and .8333.
"""

import glob
import json
import math

E22_PRED = (0.1013, 0.165)  # side EV/unit, freq at the RC<=0 rung (pen .75)
EV_OUT = -0.0095            # the retired approximation, checked against
ROUNDS_PER_HOUR = 100.0     # Matt's felt read 2026-07-19: the game is slow
MAIN = 15.0


def pool(paths):
    tot = None
    for p in paths:
        with open(p) as fh:
            d = json.load(fh)
        if tot is None:
            tot = {k: (dict(v) if isinstance(v, dict) else v)
                   for k, v in d.items() if k not in ("experiment", "seed")}
            tot["seeds"] = [d["seed"]]
            continue
        assert d["penetration"] == tot["penetration"]
        for k in ("rounds", "shoes", "n_on", "m_off", "m2_off", "m_on",
                  "m2_on", "s_on", "s2_on", "ms_on"):
            tot[k] += d[k]
        for key, c in d["tokens"].items():
            tot["tokens"][key] = tot["tokens"].get(key, 0) + c
        tot["seeds"].append(d["seed"])
    return tot


def ledger_row(t, mode, main_on, side_stake):
    """Exact per-round profit moments for X = main_bet*M + side_stake*S,
    main $15 off-trigger, `main_on` on-trigger (untied: 15; matched: stake).
    All moments realized — cross-covariance included via ms_on."""
    n, n_on = t["rounds"], t["n_on"]
    n_off = n - n_on
    f = n_on / n
    ex = (MAIN * t["m_off"]
          + main_on * t["m_on"] + side_stake * t["s_on"]) / n
    ex2 = (MAIN ** 2 * t["m2_off"]
           + main_on ** 2 * t["m2_on"]
           + side_stake ** 2 * t["s2_on"]
           + 2 * main_on * side_stake * t["ms_on"]) / n
    var = ex2 - ex * ex
    net_h = ROUNDS_PER_HOUR * ex
    sd = math.sqrt(var)
    se_h = ROUNDS_PER_HOUR * sd / math.sqrt(n)
    n0 = var / ex ** 2 / ROUNDS_PER_HOUR if ex > 0 else float("inf")
    bank = 1.5 * var / ex if ex > 0 else float("inf")
    print(f"  {mode:<14s} {side_stake:>5.0f} {net_h:>+9.2f} ±{se_h:4.2f} "
          f"{sd:>7.2f} {n0:>7.0f} {bank:>10,.0f}")
    return f


def report(t, label):
    n, n_on = t["rounds"], t["n_on"]
    n_off = n - n_on
    f = n_on / n
    ev_s = t["s_on"] / n_on
    sd_s = math.sqrt(t["s2_on"] / n_on - ev_s ** 2)
    se_s = sd_s / math.sqrt(n_on)
    ev_m_on = t["m_on"] / n_on
    ev_m_off = t["m_off"] / n_off
    se_m_off = math.sqrt(
        max(t["m2_off"] / n_off - ev_m_off ** 2, 0.0) / n_off)
    cov = t["ms_on"] / n_on - ev_m_on * ev_s
    rpshoe = n / t["shoes"]
    print(f"\n=== {label}: {n:,} rounds, {t['shoes']:,} shoes "
          f"({rpshoe:.1f} r/shoe), seeds {min(t['seeds'])}..{max(t['seeds'])} ===")
    print(f"  staked {100 * f:.3f}% of rounds; side EV {100 * ev_s:+.3f}% "
          f"± {100 * se_s:.3f}/unit (sd {sd_s:.2f}u)")
    print(f"  main EV: staked {100 * ev_m_on:+.3f}%  unstaked "
          f"{100 * ev_m_off:+.3f}% ± {100 * se_m_off:.3f}")
    print(f"  realized cov(main, side | staked) = {cov:+.4f} u^2 "
          f"(the term every prior ledger set to 0)")
    top = {k: v for k, v in sorted(t["tokens"].items()) if int(k) >= 5}
    print(f"  token histogram (staked rounds): "
          f"{ {k: v for k, v in sorted(t['tokens'].items())} }  top rungs {top}")
    print(f"\n  ledger @ {ROUNDS_PER_HOUR:.0f} r/h, $15 main"
          f" — net $/h ± se, sd $/round, N0 h, bank (5% RoR):")
    print(f"  {'mode':<14s} {'side':>5s} {'net $/h':>9s} {'':>5s} "
          f"{'sd/rnd':>7s} {'N0 h':>7s} {'bank 5%':>10s}")
    for stake in (25.0, 50.0, 100.0):
        ledger_row(t, "untied", MAIN, stake)
    for stake in (25.0, 50.0, 100.0):
        ledger_row(t, "matched 1:1", stake, stake)
    return f, ev_s, se_s, ev_m_off, se_m_off


def main() -> None:
    p75 = sorted(glob.glob("data/e23_live_p75_s*.json"))
    p833 = sorted(glob.glob("data/e23_live_p833_s*.json"))
    if p75:
        t = pool(p75)
        f, ev_s, se_s, ev_m_off, se_m_off = report(t, "pen .75 (E22 gate)")
        z_ev = (ev_s - E22_PRED[0]) / se_s
        z_out = (ev_m_off - EV_OUT) / se_m_off
        print(f"\n  GATE 1 (E22 bin prediction): side EV {100 * ev_s:+.3f}% "
              f"vs +10.13% -> z {z_ev:+.2f}  "
              f"{'PASS' if abs(z_ev) < 3 else 'FAIL'}; freq {100 * f:.2f}% "
              f"vs 16.5%")
        print(f"  GATE 2 (EV_OUT approx): unstaked main {100 * ev_m_off:+.3f}%"
              f" vs -0.95% -> z {z_out:+.2f}  "
              f"{'PASS' if abs(z_out) < 3 else 'CHECK'}")
    if p833:
        report(pool(p833), "pen .8333 (the observed 1-deck cut)")


if __name__ == "__main__":
    main()
