"""E14 — the Dragon 7 / Panda 8 betting verdict: ledger arithmetic.

No simulation here (the E4c/E12 pattern): every constant below is a measured
number with its source. Run: uv run python data/e14_verdict.py

Structural difference from E12 (21+3): there is NO main-bet toll — sitting at
a baccarat table without betting is normal behavior, so both "wong" and
"seated observer" modes pay nothing between windows. The only ledger items
are the side bets themselves.
"""

import math

# --- measured inputs ---------------------------------------------------------

# Per-system rows at pen 0.966 (cut-card-14, the baccarat norm).
# u100: exact-EV units captured per 100 observed rounds per unit staked;
# p_bet: fraction of rounds staked; mu: mean exact EV when staked.
# Sources: exact = E13 3 shards + E14 2 shards pooled (500k rounds);
# linear pair / published pair = E14, 2 x 100k rounds, seeds 8300000001 /
# 8400000001, capture scored in TRUE exact EV, parameters analytic/published.
SYSTEMS = {
    # name                (u100_d7, p_d7,    mu_d7,  u100_p8, p_p8,    mu_p8)
    "exact (computer)":   (0.8730,  0.1111,  0.0760, 0.3708,  0.0504,  0.0733),
    "linear pair (paper)": (0.8456, 0.11578, 0.0730, 0.3093,  0.04967, 0.0623),
    "published pair":     (0.7966,  0.09546, 0.0835, 0.2951,  0.04597, 0.0642),
}
P_BOTH = 0.027  # both windows on the same round (E13); staked pairs overlap less

ROUNDS_PER_HOUR = (80, 45)  # heads-up-ish midi vs full big table
UNIT = 100.0  # $ per side unit for the illustration
RUIN = 0.05


def var_bet(pays: float, mu: float) -> float:
    """Per-staked-round variance for a flat (pays):1 bet at window edge mu."""
    p = (1.0 + mu) / (pays + 1.0)
    return pays * pays * p + (1.0 - p) - mu * mu


def cov_pair(mu7: float, mu8: float) -> float:
    """Covariance of the two settlements on a round where both are staked:
    the wins are mutually exclusive (banker-7 vs player-8)."""
    p7 = (1.0 + mu7) / 41.0
    p8 = (1.0 + mu8) / 26.0
    exy = -40.0 * p7 - 25.0 * p8 + (1.0 - p7 - p8)
    return exy - mu7 * mu8


print("E14 ledger — Dragon 7 + Panda 8, pen 0.966 (cut-card-14), 8-deck EZ")
print("(no main-bet toll; both bets one unit when their window is open)")
print()
print(f"{'system':>22s} {'u/100':>7s} {'sigma/100':>9s} {'N0':>8s} "
      f"{'80r/h':>13s} {'45r/h':>13s} {'bankroll':>9s}")
for name, (u7, p7, mu7, u8, p8, mu8) in SYSTEMS.items():
    mu100 = u7 + u8
    var100 = (100.0 * p7 * var_bet(40.0, mu7)
              + 100.0 * p8 * var_bet(25.0, mu8)
              + 2.0 * 100.0 * P_BOTH * cov_pair(mu7, mu8))
    sigma100 = math.sqrt(var100)
    n0_rounds = (sigma100 / mu100) ** 2 * 100.0
    bankroll = (var100 / 100.0) / (2.0 * mu100 / 100.0) * math.log(1.0 / RUIN)
    cells = []
    for rph in ROUNDS_PER_HOUR:
        dollars = mu100 * rph / 100.0 * UNIT
        n0_h = n0_rounds / rph
        cells.append(f"${dollars:5.0f}/h {n0_h:4.0f}h")
    print(f"{name:>22s} {mu100:+6.3f}u {sigma100:8.2f}u {n0_rounds:7,.0f}r "
          f"{cells[0]:>13s} {cells[1]:>13s} ${bankroll * UNIT / 1000.0:6.1f}k")

print()
print("side-bet cap sensitivity (linear pair, 80 rounds/h):")
u7, p7, mu7, u8, p8, mu8 = SYSTEMS["linear pair (paper)"]
mu100 = u7 + u8
var100 = (100.0 * p7 * var_bet(40.0, mu7) + 100.0 * p8 * var_bet(25.0, mu8)
          + 2.0 * 100.0 * P_BOTH * cov_pair(mu7, mu8))
for cap in (100.0, 50.0, 25.0):
    scale = cap / 100.0
    dollars = mu100 * 80.0 / 100.0 * UNIT * scale
    bank = (var100 / 100.0) / (2.0 * mu100 / 100.0) * math.log(1.0 / RUIN)
    print(f"  ${cap:5.0f} max: {dollars:+6.1f}$/h   bankroll "
          f"${bank * UNIT * scale / 1000.0:5.1f}k   (N0 unchanged in rounds)")

print()
print("operating modes (paper pair from E14b: +1.108u/100, P(any trigger) ~13.8%;")
print("EZ banker toll 1.02%/round on the main stake; r = main:side stake ratio):")
print(f"{'mode':>44s} {'net u/100':>10s} {'$/h':>7s} {'N0':>7s}")
EZ_TOLL = 0.0102
PAPER_U100 = 1.108
P_ANY = 0.138
VAR100 = 570.0  # paper-pair per-100-rounds settlement variance (E14 scale)
for label, toll_u100, rph in (
    ("crowded, sit out, side-only allowed (45r/h)", 0.0, 45),
    ("crowded, min main on trigger rounds r=0.25", 100 * P_ANY * EZ_TOLL * 0.25, 45),
    ("HEADS-UP, min main every round r=0.10", 100 * EZ_TOLL * 0.10, 100),
    ("HEADS-UP, min main every round r=0.15", 100 * EZ_TOLL * 0.15, 100),
    ("HEADS-UP, min main every round r=0.25", 100 * EZ_TOLL * 0.25, 100),
):
    net = PAPER_U100 - toll_u100
    dollars = net * rph / 100.0 * UNIT
    n0_h = (VAR100 / net ** 2) * 100.0 / rph
    print(f"{label:>44s} {net:+9.3f}u ${dollars:5.0f} {n0_h:6.0f}h")
print()
print("  -> the toll is noise at real stakes ($10-25 main vs $100 side); PACE")
print("     dominates: heads-up ~doubles $/h and halves N0-hours vs a full table.")
print()
print("side <= main cap (if the house requires it), heads-up 100r/h:")
print("(min main off-trigger; raise MAIN to match the side on trigger rounds —")
print(" baccarat players ramp bets constantly, this is native behavior)")
matched_toll = (100 - 100 * P_ANY) * EZ_TOLL * 0.10 + 100 * P_ANY * EZ_TOLL * 1.0
net_matched = PAPER_U100 - matched_toll
var_matched = VAR100 + 100 * P_ANY * 0.88  # matched banker settle variance
for unit, label in ((100.0, "$100 side max"), (25.0, "$25 side max")):
    dollars = net_matched * 1.0 * unit
    n0_h = (var_matched / net_matched ** 2) * 100.0 / 100.0
    bank = (var_matched / 100.0) / (2.0 * net_matched / 100.0) \
        * math.log(1.0 / RUIN) * unit
    print(f"  {label}: net {net_matched:+.3f}u/100 = ${dollars:5.0f}/h   "
          f"N0 {n0_h:4.0f}h   bankroll ${bank / 1000.0:5.1f}k")
print("  (only a FLAT matched main all shoe long would kill it: net "
      f"{PAPER_U100 - 100 * EZ_TOLL:+.3f}u/100 — never required; vary the main)")
print()
print("comparators: 21+3 quad-Q wong-in pen .85 (E12): +$21/h per $100 unit,")
print("  N0 ~1,200h @100r/h, ~$37k bankroll, AND pays a main-bet toll to play;")
print("  standard-BJ hi-lo 1-8 spread (E4c): +0.23% on money, ~36% rounds in action.")
