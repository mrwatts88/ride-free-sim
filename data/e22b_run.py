"""E22b shard runner (Matt's simplicity question): score two SIMPLE counts
against the certified pog2 card on the same card stream.

  hilo_tc   — divided hi-lo reference (built-in)
  pog2_rc   — the E22 certified card (pivot -2)
  ko_rc     — Matt's variant A == the published KO count (2-7 +1, 8/9 0,
              A/T -1; whole tags, no red-suit device). Per-deck imbalance
              +4 -> pivot TC +4: the side trigger sits SIX points off-pivot.
              Maximum transferability, priced here.
  simple_rc — Matt's variant B == pog2 WITHOUT the red-2 gadget (all 2s +1,
              5 stays 0). BALANCED (pivot 0), so its no-division trigger is
              a fixed RC — the depth-compromise this run prices.

    uv run python -u data/e22b_run.py SEED ROUNDS OUT.json

E22b seeds: 19.4e9-20.3e9 step 1e8 (s01..05 in-sample, s06..10 OOS).
"""

import dataclasses
import json
import sys

from ridefree.experiments import pog_count_curves_to_json, run_pog_count_curves
from ridefree.rules import PAYTABLE_POG_1, RIDE_FREE

POG2 = ({1: -1, 2: 0, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 0, 9: 0, 10: -1}, 2, 1)
KO = ({1: -1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 0, 9: 0, 10: -1}, 1, 0)
SIMPLE = ({1: -1, 2: 1, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 0, 9: 0, 10: -1},
          1, 0)


def main() -> None:
    seed, rounds, path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    rules = dataclasses.replace(RIDE_FREE, side_bet_pot_of_gold=PAYTABLE_POG_1)
    res = run_pog_count_curves(
        rules, seed=seed, rounds=rounds, rules_name="RIDE_FREE",
        customs={"pog2_rc": POG2, "ko_rc": KO, "simple_rc": SIMPLE},
    )
    with open(path, "w") as f:
        json.dump(pog_count_curves_to_json(res, seed), f)
    print(f"seed {seed}: {res.rounds:,} rounds -> {path}   "
          f"pog {100 * res.pog_total / res.rounds:+.4f}%   "
          f"main {100 * res.main_total / res.rounds:+.4f}%")


if __name__ == "__main__":
    main()
