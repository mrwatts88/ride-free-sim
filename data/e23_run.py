"""E23 shard: live verification of the LITERAL pog2 card (the E18 pattern).

Plays the doctrine end to end on real shoes — no bins, no stitching:

  count pog2 (A/T -1; 3/4/6/7 +1; RED 2s +1; 5/8/9 and black 2s nothing),
  start each shoe at 24; at RC <= 12 stake the Pot of Gold side bet AND
  free-split 5s while it is out (the E21 farm); side down -> normal RF
  optimal play (5,5 takes the free double again). Main bet 1 unit every
  round, no insurance, no other deviations.

Measures realized per-round main/side profit moments split by staked /
unstaked, INCLUDING the main-side cross product — this retires the
cov(main,side)=0 assumption, the mixed-bin stitch, and the EV_OUT constant
that every ledger since E20 leaned on. Penetration is a parameter: the
2026-07-19 recon read ~1 deck cut (pen 5/6 = .8333) vs the .75 assumption.

Usage: uv run python -u data/e23_run.py SEED ROUNDS OUT.json PENETRATION

E23 seeds: pen .75 -> 20.4-20.8e9 step 1e8; pen .8333 -> 20.9-21.3e9.
"""

import dataclasses
import json
import sys

from ridefree.cards import Shoe, shoe_seeds, value
from ridefree.engine import Action, play_round
from ridefree.player_ev import OptimalStrategy
from ridefree.rules import PAYTABLE_POG_1, RIDE_FREE

_MIN_CARDS = 40  # simulator.py's safety floor

# The certified card (E22): value tags plus the red-2 bump; human IRC 24,
# stake at RC <= 12 (== the pivot-zeroed RC <= 0 rung both objectives chose).
TAGS = {1: -1, 2: 0, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 0, 9: 0, 10: -1}
RED_SUITS = (0, 1)  # experiments._RED_SUITS convention
IRC = 24
STAKE_AT = 12


def tag(raw) -> int:
    rank, suit = raw
    t = TAGS[value(raw)]
    if rank == 2 and suit in RED_SUITS:
        t += 1
    return t


class PogCardPlayer:
    """RF optimal chart play; farms 5s and stakes the side only on trigger
    rounds (the runner sets `staked` from the card's RC before each round)."""

    def __init__(self) -> None:
        self._inner = OptimalStrategy()
        self.staked = False

    def choose(self, view, rules):
        if self.staked and view.pair_rank == 5 and view.free_split_available:
            return Action.SPLIT
        return self._inner.choose(view, rules)

    def bet_pot_of_gold(self, rules) -> float:
        return 1.0 if self.staked else 0.0

    def __getattr__(self, name):
        return getattr(self._inner, name)


def main() -> None:
    base_seed, rounds, out_path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    pen = float(sys.argv[4])
    rules = dataclasses.replace(
        RIDE_FREE, side_bet_pot_of_gold=PAYTABLE_POG_1, penetration=pen
    )
    player = PogCardPlayer()
    seeds = shoe_seeds(base_seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    rc = IRC
    shoes = 1
    n = n_on = 0
    m_off = m2_off = 0.0
    m_on = m2_on = s_on = s2_on = ms_on = 0.0
    tokens: dict[str, int] = {}

    while n < rounds:
        if shoe.needs_shuffle or shoe.cards_remaining < _MIN_CARDS:
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            rc = IRC
            shoes += 1
        player.staked = rc <= STAKE_AT
        start = shoe.snapshot()
        result = play_round(rules, shoe, player, bet=1.0)
        for raw in shoe.raw_slice(start, shoe.snapshot()):
            rc += tag(raw)
        n += 1
        side = result.pog_profit
        mainp = result.profit - side
        if player.staked:
            n_on += 1
            m_on += mainp
            m2_on += mainp * mainp
            s_on += side
            s2_on += side * side
            ms_on += mainp * side
            key = str(result.pog_tokens)
            tokens[key] = tokens.get(key, 0) + 1
        else:
            m_off += mainp
            m2_off += mainp * mainp

    with open(out_path, "w") as fh:
        json.dump(
            {
                "experiment": "e23_pog2_live",
                "seed": base_seed,
                "penetration": pen,
                "rounds": n,
                "shoes": shoes,
                "n_on": n_on,
                "m_off": m_off,
                "m2_off": m2_off,
                "m_on": m_on,
                "m2_on": m2_on,
                "s_on": s_on,
                "s2_on": s2_on,
                "ms_on": ms_on,
                "tokens": tokens,
            },
            fh,
        )
    print(
        f"e23 shard seed {base_seed} pen {pen:.4f}: {n:,} rounds, "
        f"{shoes:,} shoes, staked {100 * n_on / n:.2f}%, side "
        f"{100 * s_on / n_on:+.3f}%/u -> {out_path}"
    )


if __name__ == "__main__":
    main()
