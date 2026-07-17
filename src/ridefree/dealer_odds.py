"""Exact dealer outcome probabilities — an independent analytic oracle.

Computed by recursion over the infinite-deck model (each draw is rank r with
probability weight[r]/13, where tens have weight 4). This is a *different* computation
path than the Monte Carlo engine; the validation suite requires the two to agree,
which cross-checks both. Infinite-deck is the standard published reference and differs
from a 6-deck shoe only by small depletion effects.

The dealer's drawing rule is shared with the real engine via `dealer_should_hit`, so
this validates the same H17/S17 logic the simulator uses.

Outcome buckets: final totals 17-21, exactly 22 (its own bucket — the Free Bet family
pushes on it), and "bust" meaning 23 or more. A dealer 22 still counts as a bust
statistically; `bust_probability` returns P(22) + P(bust).

State is fully captured by (best total, soft?) because a blackjack hand holds at most
one ace counted as 11, so memoization on that pair is exact.
"""

from ridefree.cards import ACE, TEN
from ridefree.engine import dealer_should_hit
from ridefree.hand import hand_total, is_blackjack, is_soft
from ridefree.rules import Rules

# Infinite-deck rank weights out of 13: A and 2-9 weight 1, ten-values weight 4.
_WEIGHT = {r: (4 if r == TEN else 1) for r in range(1, 11)}
_TOTAL_WEIGHT = 13

OUTCOMES = (17, 18, 19, 20, 21, 22, "bust")  # "bust" = 23+


def _distribution(cards: list[int], rules: Rules, memo: dict) -> dict:
    total = hand_total(cards)
    if total > 21:
        return {22: 1.0} if total == 22 else {"bust": 1.0}
    key = (total, is_soft(cards))
    if key in memo:
        return memo[key]
    if not dealer_should_hit(cards, rules):
        result = {total: 1.0}
        memo[key] = result
        return result
    out: dict = {}
    for rank, weight in _WEIGHT.items():
        p = weight / _TOTAL_WEIGHT
        for outcome, prob in _distribution(cards + [rank], rules, memo).items():
            out[outcome] = out.get(outcome, 0.0) + p * prob
    memo[key] = out
    return out


def dealer_distribution(
    up_card: int, rules: Rules, exclude_natural: bool = False
) -> dict:
    """P(final outcome) for the dealer starting from `up_card`, over all hole cards.

    With `exclude_natural=True`, hole cards completing a two-card 21 are removed and
    the distribution renormalized — the correct conditioning for a peek game, where
    the round only continues when the dealer does NOT have blackjack. Otherwise
    naturals fold into the 21 bucket.
    """
    memo: dict = {}
    dist: dict = {o: 0.0 for o in OUTCOMES}
    kept_weight = 0.0
    for hole, weight in _WEIGHT.items():
        if exclude_natural and is_blackjack([up_card, hole]):
            continue
        kept_weight += weight
        p = weight / _TOTAL_WEIGHT
        for outcome, prob in _distribution([up_card, hole], rules, memo).items():
            dist[outcome] += p * prob
    if exclude_natural and kept_weight:
        scale = _TOTAL_WEIGHT / kept_weight
        dist = {o: p * scale for o, p in dist.items()}
    return dist


def dealer_distribution_by_upcard(rules: Rules) -> dict[int, dict]:
    return {up: dealer_distribution(up, rules) for up in range(1, 11)}


def aggregate_distribution(rules: Rules) -> dict:
    """P(final outcome) with the up-card itself drawn from a fresh infinite deck."""
    dist: dict = {o: 0.0 for o in OUTCOMES}
    for up, weight in _WEIGHT.items():
        p = weight / _TOTAL_WEIGHT
        for outcome, prob in dealer_distribution(up, rules).items():
            dist[outcome] += p * prob
    return dist


def bust_probability(up_card: int, rules: Rules) -> float:
    dist = dealer_distribution(up_card, rules)
    return dist[22] + dist["bust"]


def dealer_22_probability(rules: Rules) -> float:
    """Unconditional P(dealer finishes on exactly 22). WoO publishes 0.073536 for
    six decks H17; this infinite-deck figure differs only by small composition
    effects."""
    return aggregate_distribution(rules)[22]
