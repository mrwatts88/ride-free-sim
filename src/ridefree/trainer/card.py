"""The play card as data: count tags, bet rungs, insurance and leave thresholds.

This encodes the chosen operating point from docs/ARTICLE_BLACKJACK.md — the
"crouch15" Red 7 card (E16b sizing, E17 count): hi-lo tags plus red sevens +1,
IRC −12 per 6-deck shoe, $15 crouch, jump to $100/$150/$200 at RC 0/+2/+5,
insure at RC ≥ +2, leave at RC ≤ −14. Other cards (the hi-lo TC variant, a
doubled-jump growth card) are configurations of the same dataclass.

Suit convention matches experiments.py: suits (0, 1) are red.
"""

from dataclasses import dataclass

RED_SUITS = (0, 1)


@dataclass(frozen=True)
class PlayCard:
    name: str
    irc_per_deck: int  # Red 7 imbalance: −2/deck before the display shift
    red7: bool  # count red sevens +1 on top of hi-lo tags
    floor_bet: float  # the crouch
    jumps: tuple[tuple[int, float], ...]  # (rc_threshold, bet), ascending
    insure_at: int  # take insurance at RC >= this
    leave_at: int  # leave (fresh shoe elsewhere) at RC <= this
    table_max: float = 1000.0  # the $15-$1,000 tables confirmed on recon
    # Cosmetic scale slide (Matt, 2026-07-18): add a constant so the numbers a
    # human holds are never negative — the leave line sits AT zero ("hit zero,
    # walk"). Pure relabeling: every threshold above is in the slid scale, and
    # slid RC = pivot-scale RC + shift (E17's pivot RC 0 = TC +2 is `shift`).
    shift: int = 0

    def irc(self, decks: int) -> int:
        return self.irc_per_deck * decks + self.shift

    def tag(self, raw_card: tuple[int, int]) -> int:
        """Count tag of a raw (rank, suit) card. Rank 1=A, 11/12/13=J/Q/K."""
        rank, suit = raw_card
        if 2 <= rank <= 6:
            return 1
        if rank == 7 and self.red7 and suit in RED_SUITS:
            return 1
        if 7 <= rank <= 9:
            return 0
        return -1  # ace, ten, J, Q, K

    def bet_for(self, rc: int) -> float | None:
        """Card bet at running count `rc`; None means the card says leave."""
        if rc <= self.leave_at:
            return None
        bet = self.floor_bet
        for threshold, amount in self.jumps:
            if rc >= threshold:
                bet = amount
        return bet

    def insures(self, rc: int) -> bool:
        return rc >= self.insure_at


# THE LOCKED CARD (Matt, 2026-07-18, E18): the 2-rung collapse in the slid
# scale. Start each shoe at +6; count hits 0 -> walk; $100 at 18 (the
# depth-exact pivot, TC +2); $200 AND insurance at 22. Bin-priced +$45.39/h
# on $34.4k at pen .75, 200 r/h ($15 floor); certification run in E18.
# Pivot-scale equivalents (the E17 ledger/bins): IRC -12, leave <= -18,
# $100 at >= 0, $200+ins at >= +4.
CROUCH15_2R = PlayCard(
    name="crouch15-2r",
    irc_per_deck=-2,
    red7=True,
    floor_bet=15.0,
    jumps=((18, 100.0), (22, 200.0)),
    insure_at=22,
    leave_at=0,
    shift=18,
)

# The E17 3-rung card it superseded (kept for comparison drills).
CROUCH15_RED7 = PlayCard(
    name="crouch15-red7",
    irc_per_deck=-2,
    red7=True,
    floor_bet=15.0,
    jumps=((0, 100.0), (2, 150.0), (5, 200.0)),
    insure_at=2,
    leave_at=-14,
)

DEFAULT_CARD = CROUCH15_2R
CARDS = {CROUCH15_2R.name: CROUCH15_2R, CROUCH15_RED7.name: CROUCH15_RED7}
