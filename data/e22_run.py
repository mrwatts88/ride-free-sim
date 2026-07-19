"""E22 stage 2 shard runner: one farm-arm pass binning POG side/main profit
by three count signals on the same card stream (run_pog_count_curves):

  hilo_tc  — hi-lo true count, E20 ±12 bins (the division benchmark)
  pog2_rc  — THE SPECIALIST from the stage-1 search (side BC -0.9726,
             pivot -2): A -1, red 2s +1 (black 2s 0), 3/4/6/7 +1, 5/8/9 0,
             ten -1. Pivot-zeroed RC: 0 == TC -2 at any depth.
  red7_rc  — Matt's DRILLED Red 7 (side BC -0.9652, pivot +2): the
             one-count-both-tables candidate; its side trigger sits 4 points
             off-pivot and this run prices that mush in dollars.

    uv run python -u data/e22_run.py SEED ROUNDS OUT.json

E22 seeds: 18.4e9-19.3e9 step 1e8 (s01..05 in-sample, s06..10 OOS).
"""

import dataclasses
import json
import sys

from ridefree.experiments import pog_count_curves_to_json, run_pog_count_curves
from ridefree.rules import PAYTABLE_POG_1, RIDE_FREE

POG2 = ({1: -1, 2: 0, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 0, 9: 0, 10: -1}, 2, 1)
RED7 = ({1: -1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 0, 8: 0, 9: 0, 10: -1}, 7, 1)


def main() -> None:
    seed, rounds, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    rules = dataclasses.replace(RIDE_FREE, side_bet_pot_of_gold=PAYTABLE_POG_1)
    res = run_pog_count_curves(
        rules, seed=seed, rounds=rounds, rules_name="RIDE_FREE",
        customs={"pog2_rc": POG2, "red7_rc": RED7},
    )
    with open(path, "w") as f:
        json.dump(pog_count_curves_to_json(res, seed), f)
    print(f"seed {seed}: {res.rounds:,} rounds -> {path}   "
          f"pog {100 * res.pog_total / res.rounds:+.4f}%   "
          f"main {100 * res.main_total / res.rounds:+.4f}%")


if __name__ == "__main__":
    main()
