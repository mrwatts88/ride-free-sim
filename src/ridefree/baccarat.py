"""Baccarat: rules-as-data engine, exact enumeration, and simulator (M9).

Baccarat is a separate game from blackjack — no player decisions, a fixed
drawing tableau — so it gets its own small engine rather than a variant of the
blackjack one (DESIGN.md M9 decision record). It shares the repo doctrine and
plumbing: the deterministic `cards.Shoe` / `shoe_seeds` (the 1-10 value
representation is already baccarat-native — all ten-values are the same rank),
rules as immutable data, every settlement explainable in the ledger, and the
M8b two-reference validation pattern (exact first-principles enumeration must
match the published combination table EXACTLY; the simulator must match both
statistically).

The drawing tableau (player draws on 0-5; the banker matrix below) is
universal across casinos and therefore lives in code, not in `BaccaratRules`.
What varies — decks, commission, the EZ push rule, side-bet paytables, shoe
retirement — is data.

Side bets (Dragon 7, Panda 8) follow the insurance/21+3 doctrine: the engine
settles them only when a bettor stakes them, and no built-in bettor does
unless explicitly configured, so published-edge validation is untouched.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

from ridefree.cards import Shoe, shoe_seeds
from ridefree.rules import SHOE_END_MODES

# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BaccaratRules:
    # Shoe. Baccarat is customarily dealt deep — the cut card sits ~14-16 cards
    # from the end of an 8-deck shoe (penetration ~0.96); 0.95 is a
    # conservative default. Shoe-end modes mean the same as in blackjack
    # (rules.py): csm is the published-edge comparator.
    decks: int = 8
    penetration: float = 0.95
    shoe_end_mode: str = "cut_card"
    rounds_per_shoe: int = 60  # fixed_rounds mode; a full 8-deck shoe yields ~84

    # Main-bet settlement. Classic baccarat: banker wins pay 1 minus
    # commission. EZ Baccarat: commission 0, but a banker win with a
    # three-card total of 7 pushes the banker bet (the "barred" hand).
    banker_commission: float = 0.05
    banker_push_on_three_card_7: bool = False
    tie_pays: float = 8.0

    # Side bets (EZ family). Paytables are data; a bet nobody stakes settles
    # nothing. Dragon 7: banker WIN with a three-card total of 7. Panda 8:
    # player WIN with a three-card total of 8.
    dragon7_pays: float = 40.0
    panda8_pays: float = 25.0

    def __post_init__(self) -> None:
        if self.decks < 1:
            raise ValueError("decks must be >= 1")
        if not 0.0 < self.penetration <= 1.0:
            raise ValueError("penetration must be in (0, 1]")
        if self.shoe_end_mode not in SHOE_END_MODES:
            raise ValueError(f"shoe_end_mode must be one of {SHOE_END_MODES}")
        if self.rounds_per_shoe < 1:
            raise ValueError("rounds_per_shoe must be >= 1")
        if not 0.0 <= self.banker_commission < 1.0:
            raise ValueError("banker_commission must be in [0, 1)")


# Published 8-deck references (Wizard of Odds, fetched 2026-07-17): classic
# banker -1.0579%, player -1.2351%, tie 8:1 -14.3596%; EZ banker -1.0183%,
# Dragon 7 (40:1) -7.6113% at p=0.022534, Panda 8 (25:1) -10.1876% at
# p=0.034543. Gates in tests/test_baccarat.py.
BACCARAT_8D = BaccaratRules()
EZ_BACCARAT_8D = BaccaratRules(banker_commission=0.0, banker_push_on_three_card_7=True)


# ---------------------------------------------------------------------------
# Values and the tableau
# ---------------------------------------------------------------------------

MAIN_BETS = ("banker", "player", "tie")


def baccarat_value(card: int) -> int:
    """Baccarat value of a shoe card (1-10 ints): ten-values count 0."""
    return card % 10


def _total(cards: list[int]) -> int:
    return sum(card % 10 for card in cards) % 10


def _banker_draws(banker_total: int, player_third_value: int | None) -> bool:
    """The universal banker drawing matrix.

    `player_third_value` is the baccarat value (0-9) of the player's third
    card, or None if the player stood — in which case the banker plays like
    the player: draw on 0-5, stand on 6-7.
    """
    if player_third_value is None:
        return banker_total <= 5
    d = player_third_value
    if banker_total <= 2:
        return True
    if banker_total == 3:
        return d != 8
    if banker_total == 4:
        return 2 <= d <= 7
    if banker_total == 5:
        return 4 <= d <= 7
    if banker_total == 6:
        return 6 <= d <= 7
    return False  # 7 stands


# ---------------------------------------------------------------------------
# Round result (the ledger) and the engine
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BaccaratRound:
    player_cards: tuple[int, ...]  # shoe values (1-10), deal order
    banker_cards: tuple[int, ...]
    player_total: int
    banker_total: int
    outcome: str  # "banker" | "player" | "tie"
    natural: bool  # either side dealt an 8/9 two-card total
    banker_three_card_7: bool  # banker WON with a three-card 7 (Dragon 7)
    player_three_card_8: bool  # player WON with a three-card 8 (Panda 8)
    main_side: str | None
    main_stake: float
    main_profit: float
    dragon7_stake: float
    dragon7_profit: float
    panda8_stake: float
    panda8_profit: float

    @property
    def profit(self) -> float:
        return self.main_profit + self.dragon7_profit + self.panda8_profit


def settle_main(rules: BaccaratRules, side: str, stake: float, *,
                outcome: str, banker_three_card_7: bool) -> float:
    """Profit on a main bet. Banker/player push on a tie; the EZ rule turns a
    banker three-card-7 win into a push of the banker bet."""
    if side == "tie":
        return stake * rules.tie_pays if outcome == "tie" else -stake
    if outcome == "tie":
        return 0.0
    if side == "banker":
        if outcome != "banker":
            return -stake
        if rules.banker_push_on_three_card_7 and banker_three_card_7:
            return 0.0
        return stake * (1.0 - rules.banker_commission)
    if side == "player":
        return stake if outcome == "player" else -stake
    raise ValueError(f"unknown main bet side: {side}")


def play_baccarat_round(rules: BaccaratRules, shoe: Shoe, bettor) -> BaccaratRound:
    """Deal and settle one round. All wagers are staked before the deal."""
    main = bettor.main_bet(rules)
    main_side, main_stake = main if main is not None else (None, 0.0)
    d7_stake = bettor.bet_dragon7(rules)
    p8_stake = bettor.bet_panda8(rules)

    # Standard alternating deal: player, banker, player, banker.
    p1, b1, p2, b2 = shoe.deal(), shoe.deal(), shoe.deal(), shoe.deal()
    player = [p1, p2]
    banker = [b1, b2]
    p_total, b_total = _total(player), _total(banker)
    natural = p_total >= 8 or b_total >= 8

    if not natural:
        third_value: int | None = None
        if p_total <= 5:
            player.append(shoe.deal())
            third_value = player[2] % 10
            p_total = _total(player)
        if _banker_draws(b_total, third_value):
            banker.append(shoe.deal())
            b_total = _total(banker)

    if p_total > b_total:
        outcome = "player"
    elif b_total > p_total:
        outcome = "banker"
    else:
        outcome = "tie"
    d7 = outcome == "banker" and len(banker) == 3 and b_total == 7
    p8 = outcome == "player" and len(player) == 3 and p_total == 8

    main_profit = 0.0
    if main_side is not None and main_stake:
        main_profit = settle_main(rules, main_side, main_stake,
                                  outcome=outcome, banker_three_card_7=d7)
    d7_profit = (rules.dragon7_pays * d7_stake if d7 else -d7_stake) if d7_stake else 0.0
    p8_profit = (rules.panda8_pays * p8_stake if p8 else -p8_stake) if p8_stake else 0.0

    return BaccaratRound(
        player_cards=tuple(player),
        banker_cards=tuple(banker),
        player_total=p_total,
        banker_total=b_total,
        outcome=outcome,
        natural=natural,
        banker_three_card_7=d7,
        player_three_card_8=p8,
        main_side=main_side,
        main_stake=main_stake if main_side is not None else 0.0,
        main_profit=main_profit,
        dragon7_stake=d7_stake,
        dragon7_profit=d7_profit,
        panda8_stake=p8_stake,
        panda8_profit=p8_profit,
    )


# ---------------------------------------------------------------------------
# Bettors (the strategy analogue: the engine asks, the bettor answers)
# ---------------------------------------------------------------------------


class FlatBettor:
    """Flat stakes every round — the always-bet validation comparator.

    `main` is a ("banker"|"player"|"tie", stake) tuple or None; dragon7/panda8
    are per-round side stakes (0 = not played).
    """

    def __init__(self, main: tuple[str, float] | None = ("banker", 1.0),
                 dragon7: float = 0.0, panda8: float = 0.0) -> None:
        if main is not None and main[0] not in MAIN_BETS:
            raise ValueError(f"main bet must be one of {MAIN_BETS}")
        self.main = main
        self.dragon7 = dragon7
        self.panda8 = panda8

    def main_bet(self, rules: BaccaratRules) -> tuple[str, float] | None:
        return self.main

    def bet_dragon7(self, rules: BaccaratRules) -> float:
        return self.dragon7

    def bet_panda8(self, rules: BaccaratRules) -> float:
        return self.panda8


# ---------------------------------------------------------------------------
# Metrics and the simulation loop
# ---------------------------------------------------------------------------


@dataclass
class BaccaratMetrics:
    rounds: int = 0
    total_profit: float = 0.0
    _sum_sq: float = 0.0
    outcomes: dict[str, int] = field(default_factory=dict)
    naturals: int = 0
    banker_three_card_7s: int = 0  # all occurrences, staked or not
    player_three_card_8s: int = 0
    main_wager_total: float = 0.0
    main_profit_total: float = 0.0
    dragon7_rounds: int = 0
    dragon7_stake_total: float = 0.0
    dragon7_profit_total: float = 0.0
    panda8_rounds: int = 0
    panda8_stake_total: float = 0.0
    panda8_profit_total: float = 0.0

    def observe(self, result: BaccaratRound) -> None:
        self.rounds += 1
        profit = result.profit
        self.total_profit += profit
        self._sum_sq += profit * profit
        self.outcomes[result.outcome] = self.outcomes.get(result.outcome, 0) + 1
        if result.natural:
            self.naturals += 1
        if result.banker_three_card_7:
            self.banker_three_card_7s += 1
        if result.player_three_card_8:
            self.player_three_card_8s += 1
        self.main_wager_total += result.main_stake
        self.main_profit_total += result.main_profit
        if result.dragon7_stake:
            self.dragon7_rounds += 1
            self.dragon7_stake_total += result.dragon7_stake
            self.dragon7_profit_total += result.dragon7_profit
        if result.panda8_stake:
            self.panda8_rounds += 1
            self.panda8_stake_total += result.panda8_stake
            self.panda8_profit_total += result.panda8_profit

    @property
    def main_edge(self) -> float:
        """Main-bet EV per unit staked (negative = house edge)."""
        if self.main_wager_total == 0:
            return 0.0
        return self.main_profit_total / self.main_wager_total

    @property
    def dragon7_edge(self) -> float:
        if self.dragon7_stake_total == 0:
            return 0.0
        return self.dragon7_profit_total / self.dragon7_stake_total

    @property
    def panda8_edge(self) -> float:
        if self.panda8_stake_total == 0:
            return 0.0
        return self.panda8_profit_total / self.panda8_stake_total

    @property
    def profit_std(self) -> float:
        if self.rounds < 2:
            return 0.0
        mean = self.total_profit / self.rounds
        var = self._sum_sq / self.rounds - mean * mean
        return math.sqrt(max(var, 0.0))


# A round consumes at most 6 cards; reshuffle before one could run dry.
_MIN_CARDS = 8


def _needs_reshuffle(rules: BaccaratRules, shoe: Shoe, rounds_since: int) -> bool:
    if shoe.cards_remaining < _MIN_CARDS:
        return True
    mode = rules.shoe_end_mode
    if mode == "cut_card":
        return shoe.needs_shuffle
    if mode == "fixed_rounds":
        return rounds_since >= rules.rounds_per_shoe
    if mode == "csm":
        return rounds_since >= 1
    return False


def simulate_baccarat(
    rules: BaccaratRules,
    bettor,
    *,
    seed: int,
    rounds: int,
) -> BaccaratMetrics:
    # Same observer hooks as the blackjack simulator: a bettor that tracks the
    # shoe implements observe_round(result) and new_shoe().
    on_round = getattr(bettor, "observe_round", None)
    on_shuffle = getattr(bettor, "new_shoe", None)
    metrics = BaccaratMetrics()
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    rounds_since = 0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            rounds_since = 0
            if on_shuffle is not None:
                on_shuffle()
        result = play_baccarat_round(rules, shoe, bettor)
        rounds_since += 1
        if on_round is not None:
            on_round(result)
        metrics.observe(result)
    return metrics


# ---------------------------------------------------------------------------
# Exact enumeration (the M9a tier-1 reference, and the M9b pre-deal EV core)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExactOutcomes:
    """Exact ordered-6-card-sequence counts for a given remaining composition.

    Every hand is weighted out to 6 dealt cards (a 4-card hand counts
    (N-4)*(N-5) sequences, a 5-card hand (N-5)), so `total` equals the falling
    factorial N*(N-1)*...*(N-5) and the counts are comparable to Wizard of
    Odds' published combination tables. Integer arithmetic throughout.
    """

    total: int
    banker: int
    player: int
    tie: int
    dragon7: int  # banker wins with a three-card 7 (subset of banker)
    panda8: int  # player wins with a three-card 8 (subset of player)

    @property
    def p_banker(self) -> float:
        return self.banker / self.total

    @property
    def p_player(self) -> float:
        return self.player / self.total

    @property
    def p_tie(self) -> float:
        return self.tie / self.total

    @property
    def p_dragon7(self) -> float:
        return self.dragon7 / self.total

    @property
    def p_panda8(self) -> float:
        return self.panda8 / self.total

    def ev_main(self, rules: BaccaratRules, side: str) -> float:
        """Exact EV per unit staked on a main bet under `rules`."""
        if side == "tie":
            return (self.tie * rules.tie_pays - (self.banker + self.player)) / self.total
        if side == "banker":
            win = self.banker - self.dragon7 if rules.banker_push_on_three_card_7 \
                else self.banker
            return (win * (1.0 - rules.banker_commission) - self.player) / self.total
        if side == "player":
            return (self.player - self.banker) / self.total
        raise ValueError(f"unknown main bet side: {side}")

    def ev_dragon7(self, rules: BaccaratRules) -> float:
        return (self.dragon7 * (rules.dragon7_pays + 1.0)) / self.total - 1.0

    def ev_panda8(self, rules: BaccaratRules) -> float:
        return (self.panda8 * (rules.panda8_pays + 1.0)) / self.total - 1.0


def fresh_composition(decks: int) -> dict[int, int]:
    """Baccarat value (0-9) -> count for a fresh shoe."""
    comp = {v: 4 * decks for v in range(1, 10)}
    comp[0] = 16 * decks
    return comp


def composition_from_shoe(remaining: Mapping[int, int]) -> dict[int, int]:
    """Collapse a `Shoe.remaining_composition()` (ranks 1-10) to baccarat
    values 0-9 (rank 10 -> 0)."""
    comp = {v: 0 for v in range(10)}
    for rank, count in remaining.items():
        comp[rank % 10] += count
    return comp


def exact_outcomes(composition: Mapping[int, int]) -> ExactOutcomes:
    """Exact outcome counts by full enumeration of the tableau.

    `composition` maps baccarat values 0-9 to remaining counts. Complexity is
    bounded by 10^6 leaf paths; fresh-shoe evaluation runs in seconds and is
    used by tests and (in M9b) the pre-deal EV calculator.
    """
    n = [composition.get(v, 0) for v in range(10)]
    total_cards = sum(n)
    if total_cards < 6:
        raise ValueError("composition must hold at least 6 cards")

    banker = player = tie = dragon7 = panda8 = 0
    n4 = total_cards - 4
    rem4 = n4 * (n4 - 1)  # ordered fillers weighting a 4-card hand to 6 cards
    rem5 = total_cards - 5  # same for a 5-card hand

    # Deal order within the enumeration is irrelevant (exchangeability); loop
    # player1, player2, banker1, banker2 to keep totals adjacent.
    for v1 in range(10):
        c1 = n[v1]
        if not c1:
            continue
        n[v1] -= 1
        for v2 in range(10):
            c2 = n[v2]
            if not c2:
                continue
            n[v2] -= 1
            p_total = (v1 + v2) % 10
            for v3 in range(10):
                c3 = n[v3]
                if not c3:
                    continue
                n[v3] -= 1
                for v4 in range(10):
                    c4 = n[v4]
                    if not c4:
                        continue
                    b_total = (v3 + v4) % 10
                    w4 = c1 * c2 * c3 * c4
                    natural = p_total >= 8 or b_total >= 8
                    if natural or (p_total >= 6 and b_total >= 6):
                        # No draws: both stand.
                        w = w4 * rem4
                        if p_total > b_total:
                            player += w
                        elif b_total > p_total:
                            banker += w
                        else:
                            tie += w
                        continue
                    n[v4] -= 1
                    if p_total >= 6:
                        # Player stands on 6-7; banker (total <= 5 here) draws.
                        for v6 in range(10):
                            c6 = n[v6]
                            if not c6:
                                continue
                            w = w4 * c6 * rem5
                            bf = (b_total + v6) % 10
                            if p_total > bf:
                                player += w
                            elif bf > p_total:
                                banker += w
                                if bf == 7:
                                    dragon7 += w
                            else:
                                tie += w
                        n[v4] += 1
                        continue
                    # Player (total <= 5) draws.
                    for v5 in range(10):
                        c5 = n[v5]
                        if not c5:
                            continue
                        pf = (p_total + v5) % 10
                        w5 = w4 * c5
                        if not _banker_draws(b_total, v5):
                            w = w5 * rem5
                            if pf > b_total:
                                player += w
                                if pf == 8:
                                    panda8 += w
                            elif b_total > pf:
                                banker += w
                            else:
                                tie += w
                            continue
                        n[v5] -= 1
                        for v6 in range(10):
                            c6 = n[v6]
                            if not c6:
                                continue
                            w = w5 * c6
                            bf = (b_total + v6) % 10
                            if pf > bf:
                                player += w
                                if pf == 8:
                                    panda8 += w
                            elif bf > pf:
                                banker += w
                                if bf == 7:
                                    dragon7 += w
                            else:
                                tie += w
                        n[v5] += 1
                    n[v4] += 1
                n[v3] += 1
            n[v2] += 1
        n[v1] += 1

    total = 1
    for k in range(6):
        total *= total_cards - k
    return ExactOutcomes(total=total, banker=banker, player=player, tie=tie,
                         dragon7=dragon7, panda8=panda8)
