"""M10a gate verdict: pool m10a_*.json shards and score the five-part battery.

    uv run python data/m10a_verdict.py

The published reference (WoO Free Bet page, fetched 2026-07-18) is a "random
simulation" whose P(0)/P(1) are irreconcilable with the stated rules: exact
dealing arithmetic gives P(0) = 0.838228071 (side_bets.exact_p0_pot_of_gold,
strategy-independent, peek/no-peek equivalent under the lose-to-dealer-BJ
rule), while WoO publishes 0.833420. Their k>=2 rungs are convention-robust
and their split-fives DELTAS are convention-free, so the battery is:

  G1  sim P(0) vs the exact enumeration                 (tier-1, ours)
  G2  token rungs k=2..7 vs WoO probabilities           (published shape)
  G3  split-fives PT1 edge delta vs WoO +3.0187pp       (convention-free)
  G4  split-fives main-game cost vs WoO -0.15pp         (convention-free, ~SE)
  G5  reconciliation bridge: our edge + 4*(P0_exact - P0_WoO) vs WoO -5.7687%
      (their surplus 1-token mass rides at pay 3 vs lose -1)
"""

import glob
import json
import math
from collections import defaultdict

from ridefree.rules import RIDE_FREE_WOO
from ridefree.side_bets import exact_p0_pot_of_gold

PAYS_PT1 = (3.0, 10.0, 30.0, 60.0, 100.0, 300.0, 1000.0)
PAYS_PT2 = (3.0, 12.0, 30.0, 50.0, 100.0, 100.0, 100.0)
PAYS_POG04 = (3.0, 10.0, 30.0, 60.0, 100.0, 299.0, 1000.0)

# WoO probabilities backed out of their PT1 return column (more precision
# than the printed probability column).
WOO_P = {
    0: 0.833420,
    1: 0.444466 / 3,
    2: 0.134884 / 10,
    3: 0.115973 / 30,
    4: 0.050799 / 60,
    5: 0.019445 / 100,
    6: 0.008140 / 300,
    7: 0.002026 / 1000,
}
WOO_EDGE_PT1 = -0.057687
WOO_EDGE_PT1_SPLIT5 = -0.0275
WOO_SPLIT5_MAIN_COST = -0.0015
P0_EXACT = exact_p0_pot_of_gold(RIDE_FREE_WOO)
MAIN_SIGMA = 1.07  # measured Ride Free per-round profit sd (STATUS key numbers)


def pay(paytable, k):
    return -1.0 if k == 0 else paytable[min(k, len(paytable)) - 1]


def edge_from_hist(hist, paytable):
    n = sum(hist.values())
    ev = sum(c * pay(paytable, k) for k, c in hist.items()) / n
    var = sum(c * pay(paytable, k) ** 2 for k, c in hist.items()) / n - ev * ev
    return ev, math.sqrt(var / n)


def load(variant):
    hist: dict[int, int] = defaultdict(int)
    rounds = 0
    pog_profit = 0.0
    main_profit = 0.0
    shards = sorted(glob.glob(f"data/m10a_{variant}_s*.json"))
    for path in shards:
        with open(path) as f:
            d = json.load(f)
        assert d["variant"] == variant
        rounds += d["rounds"]
        pog_profit += d["pog_profit"]
        main_profit += d["total_profit"] - d["pog_profit"]
        for k, v in d["tokens"].items():
            hist[int(k)] += v
    return shards, rounds, hist, pog_profit, main_profit


def report(variant):
    shards, rounds, hist, pog_profit, main_profit = load(variant)
    if not rounds:
        print(f"[{variant}] no shards found")
        return None
    print(f"\n=== {variant}: {len(shards)} shard(s), {rounds:,} rounds ===")
    ev, se = edge_from_hist(hist, PAYS_PT1)
    print(f"PT1 edge (NV rules): {100 * ev:+.4f}% ± {100 * se:.4f}%")
    assert abs(pog_profit / rounds - ev) < 1e-9  # ledger == histogram arithmetic

    if variant == "normal":
        p0 = hist.get(0, 0) / rounds
        se0 = math.sqrt(P0_EXACT * (1 - P0_EXACT) / rounds)
        z0 = (p0 - P0_EXACT) / se0
        print(f"\nG1  P(0) = {p0:.6f}   exact {P0_EXACT:.6f}   z = {z0:+.2f}")
        print(f"\nG2  {'tokens':>7s} {'observed':>12s} {'obs %':>10s} "
              f"{'WoO %':>10s} {'z':>7s}")
        for k in sorted(set(hist) | set(WOO_P)):
            obs = hist.get(k, 0)
            p = WOO_P.get(k)
            if p is None:
                print(f"    {k:>7d} {obs:>12,d}  (beyond the published table)")
                continue
            sigma = math.sqrt(rounds * p * (1 - p))
            zk = (obs - rounds * p) / sigma
            tag = "" if k >= 2 else "  (convention-affected, not gated)"
            note = "  (Poisson regime)" if rounds * p < 50 else ""
            print(f"    {k:>7d} {obs:>12,d} {100 * obs / rounds:>10.4f} "
                  f"{100 * p:>10.4f} {zk:>+7.2f}{note}{tag}")
        bridge = ev + 4.0 * (P0_EXACT - WOO_P[0])
        zb = (bridge - WOO_EDGE_PT1) / se
        print(f"\nG5  bridge: measured {100 * ev:+.4f}% + 4·ΔP0 "
              f"{100 * 4 * (P0_EXACT - WOO_P[0]):+.4f}% = {100 * bridge:+.4f}%"
              f"   WoO {100 * WOO_EDGE_PT1:+.4f}%   z = {zb:+.2f}")
        ev2, se2 = edge_from_hist(hist, PAYS_PT2)
        bridge2 = ev2 + 4.0 * (P0_EXACT - WOO_P[0])  # PT2 also pays 3 at k=1
        print(f"\nPT2 edge (NV rules, same histogram): {100 * ev2:+.4f}% ± "
              f"{100 * se2:.4f}%   bridge {100 * bridge2:+.4f}% vs WoO -4.64% "
              f"(z = {(bridge2 + 0.0464) / se2:+.2f})")
        ev4, _ = edge_from_hist(hist, PAYS_POG04)
        print(f"POG-04 edge (NV variant, 6 pays 299):  {100 * ev4:+.4f}%")

    main_edge = main_profit / rounds
    main_se = MAIN_SIGMA / math.sqrt(rounds)
    print(f"main-game edge: {100 * main_edge:+.4f}% ± {100 * main_se:.4f}% "
          f"(approx SE)")
    return {"edge": ev, "se": se, "main": main_edge, "main_se": main_se}


def main() -> None:
    normal = report("normal")
    split5 = report("split5")
    if normal and split5:
        delta = split5["edge"] - normal["edge"]
        se = math.sqrt(normal["se"] ** 2 + split5["se"] ** 2)
        woo_delta = WOO_EDGE_PT1_SPLIT5 - WOO_EDGE_PT1
        print(f"\nG3  split-fives PT1 delta: {100 * delta:+.4f}% ± "
              f"{100 * se:.4f}%   WoO {100 * woo_delta:+.4f}%   "
              f"z = {(delta - woo_delta) / se:+.2f}")
        mdelta = split5["main"] - normal["main"]
        mse = math.sqrt(normal["main_se"] ** 2 + split5["main_se"] ** 2)
        print(f"G4  split-fives main cost: {100 * mdelta:+.4f}% ± "
              f"{100 * mse:.4f}% (approx)   WoO {100 * WOO_SPLIT5_MAIN_COST:+.4f}%"
              f"   z = {(mdelta - WOO_SPLIT5_MAIN_COST) / mse:+.2f}")


if __name__ == "__main__":
    main()
