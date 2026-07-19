"""M10a gate shard: Pot of Gold always-bet on RIDE_FREE_WOO in csm mode.

    uv run python -u data/m10a_gate.py <normal|split5> <seed> <rounds>

Writes data/m10a_<variant>_s<seed>.json with the token histogram (the gate's
sufficient statistic), the Pot of Gold ledger, and the main-game profit.
csm mode deals every round off the top of a full shoe (the combinatorial
comparator); the strategy is the validated OptimalStrategy reference, wrapped
in SplitFives for the split5 arm. (OptimalStrategy and FreeBetStrategy take
every offered free bet — enumeration-verified — so the token distribution is
strategy-convention-free; WoO's published table differs only by their sim's
dealer-blackjack handling, scored as the E19 bridge in m10a_verdict.py.)
"""

import dataclasses
import json
import sys
import time

from ridefree.player_ev import OptimalStrategy
from ridefree.rules import PAYTABLE_POG_1, RIDE_FREE_WOO
from ridefree.simulator import simulate
from ridefree.strategy import AlwaysPotOfGold, SplitFives


def main() -> None:
    variant, seed, rounds = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    assert variant in ("normal", "split5")
    rules = dataclasses.replace(
        RIDE_FREE_WOO, side_bet_pot_of_gold=PAYTABLE_POG_1, shoe_end_mode="csm"
    )
    inner = OptimalStrategy() if variant == "normal" else SplitFives(OptimalStrategy())
    t0 = time.time()
    m = simulate(rules, AlwaysPotOfGold(inner), seed=seed, rounds=rounds)
    elapsed = time.time() - t0
    payload = {
        "variant": variant,
        "seed": seed,
        "rounds": m.rounds,
        "pog_stake": m.pog_stake_total,
        "pog_profit": m.pog_profit_total,
        "tokens": {str(k): v for k, v in sorted(m.pog_tokens.items())},
        "total_profit": m.total_profit,
        "elapsed_s": round(elapsed, 1),
    }
    out = f"data/m10a_{variant}_s{seed}.json"
    with open(out, "w") as f:
        json.dump(payload, f)
    print(f"{out}: {m.rounds:,} rounds in {elapsed:.0f}s "
          f"({m.rounds / elapsed / 1000:.1f}k r/s), "
          f"pog edge {100 * m.pog_profit_total / m.pog_stake_total:+.4f}%")


if __name__ == "__main__":
    main()
