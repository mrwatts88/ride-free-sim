"""Seeded simulation loop and metrics collection.

The simulator owns the shoe lifecycle (reshuffle at the cut card) and is deterministic
under its seed: (rules, strategy, seed, rounds, bet) reproduces exactly. Metrics are
collected separately from game logic — the collector only sees RoundResults.
"""

import math
from dataclasses import dataclass, field

from ridefree.cards import Shoe
from ridefree.engine import RoundResult, play_round
from ridefree.rules import Rules


@dataclass
class Metrics:
    rounds: int = 0
    hands: int = 0
    total_profit: float = 0.0
    _sum_sq: float = 0.0  # sum of per-round profit^2, for variance
    outcomes: dict[str, int] = field(default_factory=dict)
    player_naturals: int = 0  # true count, even when both-BJ makes it a push
    pairs_dealt: int = 0
    splits: int = 0
    doubles: int = 0
    # Dealer final total counted ONLY over hands the dealer actually played out
    # (excludes naturals and all-player-bust rounds), so it matches published tables.
    dealer_final: dict[int, int] = field(default_factory=dict)  # total (22=bust) -> n
    dealer_completed: int = 0
    total_initial_wager: float = 0.0

    def observe(self, result: RoundResult, bet: float) -> None:
        self.rounds += 1
        self.total_profit += result.profit
        self._sum_sq += result.profit * result.profit
        self.total_initial_wager += bet
        if result.player_natural:
            self.player_naturals += 1
        if result.was_pair:
            self.pairs_dealt += 1
        if result.did_split:
            self.splits += 1
        if result.did_double:
            self.doubles += 1
        for h in result.hands:
            self.hands += 1
            self.outcomes[h.outcome] = self.outcomes.get(h.outcome, 0) + 1
        if result.dealer_played_out:
            dealer_total = _dealer_total(result.dealer_cards)
            key = 22 if dealer_total > 21 else dealer_total
            self.dealer_final[key] = self.dealer_final.get(key, 0) + 1
            self.dealer_completed += 1

    @property
    def edge(self) -> float:
        """Player EV per unit of initial wager (negative = house edge)."""
        if self.total_initial_wager == 0:
            return 0.0
        return self.total_profit / self.total_initial_wager

    @property
    def profit_std(self) -> float:
        """Std dev of per-round profit (in bet units when flat-betting 1)."""
        if self.rounds < 2:
            return 0.0
        mean = self.total_profit / self.rounds
        var = self._sum_sq / self.rounds - mean * mean
        return math.sqrt(max(var, 0.0))

    @property
    def edge_stderr(self) -> float:
        """Standard error of the edge estimate (per unit initial wager)."""
        if self.rounds == 0 or self.total_initial_wager == 0:
            return 0.0
        avg_bet = self.total_initial_wager / self.rounds
        return self.profit_std / math.sqrt(self.rounds) / avg_bet


def _dealer_total(cards) -> int:
    from ridefree.hand import hand_total

    return hand_total(list(cards))


def simulate(
    rules: Rules,
    strategy,
    *,
    seed: int,
    rounds: int,
    bet: float = 1.0,
) -> Metrics:
    metrics = Metrics()
    shoe = Shoe(rules.decks, rules.penetration, seed)
    shuffles = 0
    for _ in range(rounds):
        if shoe.needs_shuffle or shoe.cards_remaining < 20:
            shuffles += 1
            shoe = Shoe(rules.decks, rules.penetration, seed + shuffles)
        result = play_round(rules, shoe, strategy, bet=bet)
        metrics.observe(result, bet)
    return metrics
