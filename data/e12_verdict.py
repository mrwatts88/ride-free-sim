"""E12 — the 21+3 betting verdict: ledger arithmetic from measured inputs.

No simulation here (the E4c pattern): every constant below is a measured or
validated number with its source. Run: uv run python data/e12_verdict.py
"""

import math

# --- measured inputs (sources in comments) -----------------------------------

# E11b (2M rounds each, seeds 7100000001 / 7200000001), scored in TRUE exact EV.
# side_u100: EV units per 100 OBSERVED rounds per unit of side stake;
# p_bet: fraction of rounds the rule fires; mu_bet: mean exact EV when betting.
SYSTEMS = {
    #  system            pen    side_u100  p_bet     mu_bet
    ("exact", 0.75): (0.116, 0.04666, 0.02480),
    ("exact", 0.85): (0.269, 0.07019, 0.03833),
    ("quad-Q", 0.75): (0.086, 0.03515, 0.02441),
    ("quad-Q", 0.85): (0.211, 0.05494, 0.03834),
}

TOLL = 0.0064  # h17 6d basic-strategy house edge/round (M2-validated vs 0.62%)
SIGMA_MAIN = 1.15  # main-hand per-round std dev in main-bet units (M1: 1.16)
ROUNDS_PER_HOUR = 100  # heads-up assumption; illustration only


def sigma_side(mu: float) -> float:
    """Exact per-staked-round std dev for the flat 9:1 bet at window edge mu:
    X = +9 w.p. p, -1 otherwise, with p = (1 + mu) / 10."""
    p = (1.0 + mu) / 10.0
    var = 81.0 * p + (1.0 - p) - mu * mu
    return math.sqrt(var)


def ledger(name, pen, main_per_side):
    """Per 100 observed rounds, in units of the side stake."""
    side_u100, p_bet, mu_bet = SYSTEMS[(name, pen)]
    toll_seated = 100.0 * TOLL * main_per_side
    toll_wong = 100.0 * TOLL * main_per_side * p_bet
    return side_u100 - toll_seated, side_u100 - toll_wong


print("E12 ledger — net EV per 100 observed rounds, in SIDE-STAKE units")
print("(side leg from E11b; toll = 0.64%/round on the required main bet)")
print()
print(f"{'system':>8s} {'pen':>5s} {'main:side':>10s} "
      f"{'seated':>9s} {'wong-in':>9s}")
for name in ("quad-Q", "exact"):
    for pen in (0.75, 0.85):
        for ratio, label in ((1.0, "1:1"), (0.5, "1:2"), (1 / 3, "1:3"),
                             (0.2, "1:5"), (0.15, "$15:$100")):
            seated, wong = ledger(name, pen, ratio)
            print(f"{name:>8s} {pen:5.2f} {label:>10s} "
                  f"{seated:+8.3f}u {wong:+8.3f}u")
        side_u100, p_bet, _ = SYSTEMS[(name, pen)]
        breakeven = side_u100 / (100.0 * TOLL)
        print(f"{'':>8s} {'':>5s} {'breakeven':>10s} "
              f"side:main > {1 / breakeven:.2f}:1 seated "
              f"(wong-in breakeven {p_bet / breakeven:.3f}:1)")
    print()

print("$ illustration (side $100, main $15, 100 rounds/h observed):")
print(f"{'system':>8s} {'pen':>5s} {'mode':>8s} {'$/h':>8s} "
      f"{'sigma/h':>9s} {'N0 hours':>9s}")
for name in ("quad-Q", "exact"):
    for pen in (0.75, 0.85):
        side_u100, p_bet, mu_bet = SYSTEMS[(name, pen)]
        s_side = sigma_side(mu_bet) * 100.0  # $ per staked round
        bets_per_h = ROUNDS_PER_HOUR * p_bet
        for mode in ("seated", "wong-in"):
            if mode == "seated":
                ev_h = side_u100 - 100.0 * TOLL * 0.15
                var_h = bets_per_h * s_side**2 + ROUNDS_PER_HOUR * (SIGMA_MAIN * 15) ** 2
            else:
                ev_h = side_u100 - 100.0 * TOLL * 0.15 * p_bet
                var_h = bets_per_h * (s_side**2 + (SIGMA_MAIN * 15) ** 2)
            # ev_h is in side-stake units per 100 rounds; 1 unit = $100 and
            # 100 rounds = 1 hour, so dollars/hour = ev_h * $100.
            ev_h_usd = ev_h * 100.0
            sd_h = math.sqrt(var_h)
            n0 = (sd_h / ev_h_usd) ** 2 if ev_h_usd > 0 else float("inf")
            print(f"{name:>8s} {pen:5.2f} {mode:>8s} {ev_h_usd:+8.2f} "
                  f"{sd_h:9.0f} {n0:9.0f}")
print()
print("Notes: u/100 rounds at $100 side stake == $/hour at 100 rounds/h.")
print("Seated variance includes the every-round main hand; wong-in only the")
print("trigger rounds' main hands. N0 = hours to 1-sigma = EV.")

print()
print("side <= main cap (common rule) — quad-Q, $ per 100 observed rounds:")
print("wong-in: bet main = side = $100 on trigger rounds only;")
print("seated:  table-min $15 main off-trigger, raise BOTH to $100 on triggers.")
print(f"{'pen':>5s} {'wong-in 1:1':>12s} {'seated raise-both':>18s}")
for pen in (0.75, 0.85):
    side_u100, p_bet, mu_bet = SYSTEMS[("quad-Q", pen)]
    wong = (side_u100 - 100.0 * TOLL * p_bet) * 100.0  # main=side, $100 units
    toll_seated = ((100.0 - 100.0 * p_bet) * TOLL * 15.0
                   + 100.0 * p_bet * TOLL * 100.0)
    seated = side_u100 * 100.0 - toll_seated
    print(f"{pen:5.2f} {wong:+11.2f} {seated:+17.2f}")
print("(the trigger-round pair nets ~(mu_bet - 0.64%) of the matched amount;")
print(" the cap costs ~15% in wong-in mode and does not flip any verdict —")
print(" penetration and paytable remain the kill conditions)")
