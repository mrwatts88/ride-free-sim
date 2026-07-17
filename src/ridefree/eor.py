"""Effects of removal (EOR), derived from the exact EV calculator.

EOR_r = game EV with one card of rank r removed from a 52-card deck's frequencies,
minus baseline game EV — the classic Griffin quantity, computed analytically under
the i.i.d.-frequency model (no simulation noise). Classical hi-lo tags are standard
blackjack's EORs quantized; Ride Free's EORs differ (free doubles are built from
small/mid cards, dealer 22 is built from tens), so its optimal linear count must be
derived from its own EORs — Matt's insight, 2026-07-17.

First-order composition estimate (frequency-gradient expansion; see eor_ev_shift):
EV(remaining) ≈ EV(fresh) − 51 · Σ_r EOR_r · (n_r/N − c_r/52),
which turns a full EOR vector into an O(ranks) per-round signal — the *perfect
linear count* for the game, expressed directly in EV units.
"""

from ridefree.cards import RANKS, TEN
from ridefree.player_ev import game_ev
from ridefree.rules import Rules

PER_DECK = {r: (16 if r == TEN else 4) for r in RANKS}


def effects_of_removal(rules: Rules) -> tuple[float, dict[int, float]]:
    """(baseline full-deck EV, {rank: EOR for removing one card from 52})."""
    base = game_ev(rules, dict(PER_DECK))
    eors = {}
    for rank in RANKS:
        weights = dict(PER_DECK)
        weights[rank] -= 1
        eors[rank] = game_ev(rules, weights) - base
    return base, eors


def eor_ev_shift(eors: dict[int, float], counts: dict[int, int], n: int) -> float:
    """First-order estimated EV shift vs a fresh shoe for remaining composition
    `counts` (total `n` cards). Positive = better-than-fresh shoe."""
    if n <= 0:
        return 0.0
    return -51.0 * sum(
        eors[r] * (counts[r] / n - PER_DECK[r] / 52) for r in RANKS
    )
