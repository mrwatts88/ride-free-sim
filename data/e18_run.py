"""E18 shard: live certification of the locked crouch15-2r card.

Plays the LITERAL card end to end on real shoes — chart play (BasicStrategy),
bet by running count before each round, sit out (bet 0, pointwise convention,
matching the E16/E17 exit pricing) at/below the leave line, and the human
insurance rule "insure iff the visible RC at the decision clears the max-bet
threshold" (decision-time RC: committed cards + the three visible cards of
this round; the hole is NOT counted — unlike the banked arm's composition-
exact oracle, this is the rule a human can actually play, which is the point
of the experiment).

Usage: uv run python data/e18_run.py <base_seed> <rounds> <out.json>
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ridefree.cards import Shoe, shoe_seeds  # noqa: E402
from ridefree.engine import play_round  # noqa: E402
from ridefree.rules import STANDARD_6D_H17  # noqa: E402
from ridefree.strategy import BasicStrategy  # noqa: E402
from ridefree.trainer.card import CROUCH15_2R  # noqa: E402

_MIN_CARDS = 40  # simulator.py's safety floor


class CardPlayer(BasicStrategy):
    """Chart play plus the card's literal insurance rule."""

    def __init__(self, card):
        self.card = card
        self.shoe = None
        self.round_start = 0
        self.rc = 0  # committed RC entering this round

    def take_insurance(self, cards, rules) -> bool:
        visible = self.shoe.raw_slice(self.round_start, self.round_start + 3)
        rc_now = self.rc + sum(self.card.tag(c) for c in visible)
        return rc_now >= self.card.insure_at


def main() -> None:
    base_seed, rounds, out_path = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    rules = STANDARD_6D_H17
    card = CROUCH15_2R
    player = CardPlayer(card)
    seeds = shoe_seeds(base_seed)

    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    rc = card.irc(rules.decks)
    n = 0
    sum_p = sum_p2 = sum_bet = 0.0
    sum_pni = sum_pni2 = 0.0  # profit excluding the insurance overlay
    ins_rounds = 0
    ins_stake = ins_profit = 0.0
    rung_rounds: dict[str, int] = {}
    shoes = 1

    while n < rounds:
        if shoe.needs_shuffle or shoe.cards_remaining < _MIN_CARDS:
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            rc = card.irc(rules.decks)
            shoes += 1
        # None = at/below the leave line: we have no stake, but the cards keep
        # flowing (the pointwise exit convention the E16/E17 pricing used).
        # Chart play is bet-independent, so dealing the sit-out round at a
        # nominal stake consumes the identical card stream; its money simply
        # isn't ours and is excluded from the ledger.
        bet = card.bet_for(rc)
        sit_out = bet is None
        player.shoe = shoe
        player.round_start = shoe.snapshot()
        player.rc = rc
        result = play_round(rules, shoe, player, bet=1.0 if sit_out else bet)
        for raw in shoe.raw_slice(player.round_start, shoe.snapshot()):
            rc += card.tag(raw)
        n += 1
        key = "0" if sit_out else f"{bet:g}"
        rung_rounds[key] = rung_rounds.get(key, 0) + 1
        if sit_out:
            continue
        p = result.profit
        pni = p - result.insurance_profit
        sum_p += p
        sum_p2 += p * p
        sum_pni += pni
        sum_pni2 += pni * pni
        sum_bet += bet
        if result.insurance_stake:
            ins_rounds += 1
            ins_stake += result.insurance_stake
            ins_profit += result.insurance_profit

    with open(out_path, "w") as fh:
        json.dump(
            {
                "experiment": "e18_crouch15_2r_live",
                "card": card.name,
                "seed": base_seed,
                "rounds": n,
                "shoes": shoes,
                "sum_profit": sum_p,
                "sum_profit_sq": sum_p2,
                "sum_profit_no_ins": sum_pni,
                "sum_profit_no_ins_sq": sum_pni2,
                "sum_bet": sum_bet,
                "ins_rounds": ins_rounds,
                "ins_stake": ins_stake,
                "ins_profit": ins_profit,
                "rung_rounds": rung_rounds,
            },
            fh,
        )
    print(f"e18 shard seed {base_seed}: {n:,} rounds, {shoes:,} shoes -> {out_path}")


if __name__ == "__main__":
    main()
