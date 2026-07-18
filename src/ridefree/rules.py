"""Game rules as immutable data.

Every parameter that affects gameplay or payout lives here. Variants (standard
blackjack, Ride Free / Free Bet) are configurations of this one object; game logic
must never hard-code a rule.
"""

import dataclasses
from dataclasses import dataclass


# How a shoe is retired and reshuffled:
#   "cut_card"     realistic fixed-depth cut card at `penetration`; finish the round
#                  in which the cut card appears, then reshuffle. Number of rounds per
#                  shoe varies with composition, so this INCLUDES the cut-card effect.
#   "fixed_rounds" reshuffle after exactly `rounds_per_shoe` rounds regardless of
#                  depth. Removes the cut-card effect (fixed rounds/shoe) but keeps
#                  intra-shoe depletion. Matches fixed-round combinatorial analyses.
#   "csm"          reshuffle a full shoe before every round, so every round is dealt
#                  off the top of a complete shoe. No depletion at all — the direct
#                  match to a published off-the-top house edge and the "counting does
#                  nothing" baseline. Approximates a continuous shuffle machine.
SHOE_END_MODES = ("cut_card", "fixed_rounds", "csm")


@dataclass(frozen=True, slots=True)
class Rules:
    # Shoe
    decks: int = 6
    penetration: float = 0.75  # fraction of shoe dealt before reshuffle (cut_card mode)
    shoe_end_mode: str = "cut_card"
    rounds_per_shoe: int = 40  # used by fixed_rounds mode (~75% pen equiv for 6 decks)

    # Dealer
    dealer_hits_soft_17: bool = True
    dealer_22_pushes: bool = False  # Free Bet family: dealer 22 pushes live hands
    dealer_peeks_for_blackjack: bool = True

    # Payouts
    blackjack_payout: float = 1.5  # per unit wagered (3:2); 1.2 would be 6:5

    # Doubling
    double_any_two_cards: bool = True
    double_hard_totals: frozenset[int] = frozenset()  # used when not double_any_two_cards
    double_after_split: bool = True

    # Splitting
    max_hands: int = 4  # total hands after all splits
    resplit_aces: bool = False
    hit_split_aces: bool = False  # False = one card only to each split ace
    # (split_by_value removed 2026-07-17: it was never read, and the 10-collapsed
    # card model cannot represent a matched-rank-only distinction anyway.)

    # Surrender
    late_surrender: bool = False

    # Insurance: side bet offered when the dealer shows an ace, staking half the
    # main bet, resolved at the peek. The engine only asks a strategy that
    # implements `take_insurance(cards, rules)`; no built-in strategy takes it
    # (infinite-deck insurance is -EV), so published-edge validation is
    # unaffected. It is a real EV source for count-based play (~+0.15%/round in
    # the RF wong-in window; docs/EXPERIMENTS.md E9). Gate validated 2026-07-17
    # against the exact 6-deck EV (tests/test_insurance.py).
    insurance_offered: bool = True
    insurance_pays: float = 2.0  # 2:1

    # Free Bet features (all empty/False = standard blackjack)
    free_double_totals: frozenset[int] = frozenset()  # two-card totals, e.g. {9, 10, 11}
    free_double_soft_allowed: bool = False  # if True, soft totals also qualify (unconfirmed at Potawatomi; standard Free Bet is hard-only)
    free_split_ranks: frozenset[int] = frozenset()  # ranks eligible; 1=A, 10=T/J/Q/K
    free_resplits: bool = False
    free_double_after_split: bool = False

    def __post_init__(self) -> None:
        if self.decks < 1:
            raise ValueError("decks must be >= 1")
        if not 0.0 < self.penetration <= 1.0:
            raise ValueError("penetration must be in (0, 1]")
        if self.max_hands < 1:
            raise ValueError("max_hands must be >= 1")
        if self.shoe_end_mode not in SHOE_END_MODES:
            raise ValueError(f"shoe_end_mode must be one of {SHOE_END_MODES}")
        if self.rounds_per_shoe < 1:
            raise ValueError("rounds_per_shoe must be >= 1")
        bad = {r for r in self.free_split_ranks if r not in range(1, 11)}
        if bad:
            raise ValueError(f"free_split_ranks contains invalid ranks: {sorted(bad)}")


# M2 validation targets: look up the exact Wizard of Odds house edge for precisely
# these rulesets at milestone time (see docs/ROADMAP.md).
STANDARD_6D_H17 = Rules()
STANDARD_6D_S17 = Rules(dealer_hits_soft_17=False)  # ~0.40% house edge published

# Potawatomi Ride Free, per the published rules: free splits on non-ten pairs with
# free resplits to 4 hands; aces split once only, one card each; free double on hard
# two-card 9/10/11 only (soft/other totals may double with own money), including
# after splits; BJ 3:2; dealer 22 pushes. Still unconfirmed: decks and H17/S17
# (dealer_hits_soft_17) — 6-deck H17 assumed. See docs/ROADMAP.md M3.
RIDE_FREE = Rules(
    dealer_22_pushes=True,
    max_hands=4,
    resplit_aces=False,
    hit_split_aces=False,
    free_double_totals=frozenset({9, 10, 11}),
    free_double_soft_allowed=False,
    free_split_ranks=frozenset(range(1, 10)),  # all pairs except ten-value
    free_resplits=True,
    free_double_after_split=True,
)

# The exact Wizard of Odds Free Bet configuration behind their published 1.04% house
# edge (fetched 2026-07-17): identical to RIDE_FREE except aces may be re-split (to
# 4 hands). Per WoO's rule-variation table, no-resplit-aces costs the player 0.08%,
# so the Potawatomi RIDE_FREE preset's derived target is ~1.12%.
RIDE_FREE_WOO = dataclasses.replace(RIDE_FREE, resplit_aces=True)
