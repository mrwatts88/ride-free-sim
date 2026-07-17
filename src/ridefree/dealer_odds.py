"""Exact dealer outcome probabilities — an independent analytic oracle.

Computed by recursion over the infinite-deck model (each draw is rank r with
probability weight[r]/13, where tens have weight 4). This is a *different* computation
path than the Monte Carlo engine; the validation suite requires the two to agree,
which cross-checks both. Infinite-deck is the standard published reference and differs
from a 6-deck shoe only by small depletion effects.

The dealer's drawing rule is shared with the real engine via `dealer_should_hit`, so
this validates the same H17/S17 logic the simulator uses.

State is fully captured by (best total, soft?) because a blackjack hand holds at most
one ace counted as 11, so memoization on that pair is exact.
"""

from ridefree.cards import ACE, TEN
from ridefree.engine import dealer_should_hit
from ridefree.hand import hand_total, is_soft
from ridefree.rules import Rules

# Infinite-deck rank weights out of 13: A and 2-9 weight 1, ten-values weight 4.
_WEIGHT = {r: (4 if r == TEN else 1) for r in range(1, 11)}
_TOTAL_WEIGHT = 13

OUTCOMES = (17, 18, 19, 20, 21, "bust")


def _distribution(cards: list[int], rules: Rules, memo: dict) -> dict:
    total = hand_total(cards)
    if total > 21:
        return {"bust": 1.0}
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


def dealer_distribution(up_card: int, rules: Rules) -> dict:
    """P(final outcome) for the dealer starting from `up_card`, over all hole cards.

    Naturals (two-card 21 on an ace/ten up) fold into the 21 bucket; the bust rate,
    the headline validation number, is unaffected by that choice.
    """
    memo: dict = {}
    dist: dict = {o: 0.0 for o in OUTCOMES}
    for hole, weight in _WEIGHT.items():
        p = weight / _TOTAL_WEIGHT
        for outcome, prob in _distribution([up_card, hole], rules, memo).items():
            dist[outcome] += p * prob
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
    return dealer_distribution(up_card, rules)["bust"]
