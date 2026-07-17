"""One round of blackjack, driven entirely by a Rules object.

The engine owns mechanics and money; it never makes playing decisions. It asks the
strategy "here are the legal actions, choose" and settles every hand through the
ledger model (player-funded wager and casino-funded free wager tracked separately —
free wagers are always 0 until the Free Bet features land in M3, but settlement
already handles both so the same code path serves every variant).
"""

from dataclasses import dataclass
from enum import Enum

from ridefree.cards import ACE, TEN
from ridefree.hand import hand_total, is_blackjack, is_soft
from ridefree.rules import Rules


class Action(Enum):
    HIT = "hit"
    STAND = "stand"
    DOUBLE = "double"
    SPLIT = "split"


class IllegalActionError(Exception):
    pass


@dataclass
class _Hand:
    cards: list[int]
    wager: float
    free_wager: float = 0.0
    is_split: bool = False
    from_split_aces: bool = False
    doubled: bool = False


@dataclass(frozen=True)
class HandView:
    """What a strategy is allowed to see about the hand it must act on."""

    cards: tuple[int, ...]
    total: int
    soft: bool
    pair_rank: int | None  # set when the hand is a splittable-shaped two-card pair
    dealer_up: int
    is_split_hand: bool
    legal: frozenset[Action]


@dataclass(frozen=True)
class HandResult:
    cards: tuple[int, ...]
    wager: float
    free_wager: float
    outcome: str  # "blackjack" | "win" | "lose" | "push"
    profit: float


@dataclass(frozen=True)
class RoundResult:
    profit: float
    hands: tuple[HandResult, ...]
    dealer_cards: tuple[int, ...]
    events: tuple[str, ...]
    dealer_played_out: bool = True  # False when a natural ended it before dealer drew
    player_natural: bool = False  # initial hand was a two-card 21 (before push classing)
    was_pair: bool = False  # initial two cards were a pair
    did_split: bool = False
    did_double: bool = False


def _name(card: int) -> str:
    return "A" if card == ACE else str(card)


def _desc(cards: list[int]) -> str:
    return ",".join(_name(c) for c in cards) + f" ({hand_total(cards)})"


def _check_supported(rules: Rules) -> None:
    if (
        rules.free_double_totals
        or rules.free_split_ranks
        or rules.free_resplits
        or rules.free_double_after_split
    ):
        raise NotImplementedError("Free Bet features arrive in M3")
    if rules.late_surrender:
        raise NotImplementedError("surrender is not implemented")
    if not rules.dealer_peeks_for_blackjack:
        raise NotImplementedError("no-peek (ENHC) play is not implemented")


def legal_actions(hand: _Hand, n_hands: int, rules: Rules) -> frozenset[Action]:
    legal = {Action.HIT, Action.STAND}
    if len(hand.cards) == 2:
        total = hand_total(hand.cards)
        can_double = rules.double_any_two_cards or (
            not is_soft(hand.cards) and total in rules.double_hard_totals
        )
        if hand.is_split and not rules.double_after_split:
            can_double = False
        if hand.from_split_aces:
            can_double = False
        if can_double:
            legal.add(Action.DOUBLE)
        if hand.cards[0] == hand.cards[1] and n_hands < rules.max_hands:
            blocked_ace_resplit = (
                hand.cards[0] == ACE and hand.is_split and not rules.resplit_aces
            )
            if not blocked_ace_resplit:
                legal.add(Action.SPLIT)
    return frozenset(legal)


def dealer_should_hit(cards, rules: Rules) -> bool:
    """The dealer's drawing rule, in one place (H17/S17)."""
    total = hand_total(cards)
    if total < 17:
        return True
    return total == 17 and is_soft(cards) and rules.dealer_hits_soft_17


def play_dealer(cards: list[int], shoe, rules: Rules) -> list[int]:
    """Draw for the dealer until standing. Mutates and returns `cards`.

    Single source of truth for dealer play, shared by play_round and the validation
    harness so the exact odds calculator is checked against the real state machine.
    """
    while dealer_should_hit(cards, rules):
        cards.append(shoe.deal())
    return cards


def play_round(rules: Rules, shoe, strategy, bet: float = 1.0, log: bool = False) -> RoundResult:
    _check_supported(rules)
    events: list[str] = []

    def note(msg: str) -> None:
        if log:
            events.append(msg)

    # Deal order is fixed for replay determinism: player, dealer up, player, hole.
    first = shoe.deal()
    up = shoe.deal()
    second = shoe.deal()
    hole = shoe.deal()
    player = _Hand(cards=[first, second], wager=bet)
    dealer_cards = [up, hole]
    note(f"player dealt {_desc(player.cards)}, dealer shows {_name(up)}")

    player_bj = is_blackjack(player.cards)
    was_pair = player.cards[0] == player.cards[1]
    if (
        rules.dealer_peeks_for_blackjack
        and up in (ACE, TEN)
        and is_blackjack(dealer_cards)
    ):
        note("dealer has blackjack")
        outcome = "push" if player_bj else "lose"
        profit = 0.0 if player_bj else -bet
        note(f"hand 1: {outcome} {profit:+g}")
        hand_result = HandResult(tuple(player.cards), bet, 0.0, outcome, profit)
        return RoundResult(
            profit, (hand_result,), tuple(dealer_cards), tuple(events),
            dealer_played_out=False, player_natural=player_bj, was_pair=was_pair,
        )
    if player_bj:
        profit = bet * rules.blackjack_payout
        note(f"player blackjack {profit:+g}")
        hand_result = HandResult(tuple(player.cards), bet, 0.0, "blackjack", profit)
        return RoundResult(
            profit, (hand_result,), tuple(dealer_cards), tuple(events),
            dealer_played_out=False, player_natural=True, was_pair=was_pair,
        )

    hands = [player]
    i = 0
    while i < len(hands):
        hand = hands[i]
        label = f"hand {i + 1}"
        while True:
            if len(hand.cards) == 1:  # freshly split, awaiting its second card
                hand.cards.append(shoe.deal())
                note(f"{label}: dealt {_name(hand.cards[-1])} -> {_desc(hand.cards)}")
                if hand.from_split_aces and not rules.hit_split_aces:
                    break  # one card to each split ace
            total = hand_total(hand.cards)
            if total > 21:
                note(f"{label}: bust")
                break
            if total == 21:
                break  # nothing rational remains; don't consult the strategy
            legal = legal_actions(hand, len(hands), rules)
            pair_rank = (
                hand.cards[0]
                if len(hand.cards) == 2 and hand.cards[0] == hand.cards[1]
                else None
            )
            view = HandView(
                cards=tuple(hand.cards),
                total=total,
                soft=is_soft(hand.cards),
                pair_rank=pair_rank,
                dealer_up=up,
                is_split_hand=hand.is_split,
                legal=legal,
            )
            action = strategy.choose(view, rules)
            if action not in legal:
                raise IllegalActionError(
                    f"{action} illegal for {_desc(hand.cards)}; "
                    f"legal: {sorted(a.value for a in legal)}"
                )
            if action is Action.STAND:
                note(f"{label}: stand on {total}")
                break
            if action is Action.HIT:
                hand.cards.append(shoe.deal())
                note(f"{label}: hit -> {_desc(hand.cards)}")
                continue
            if action is Action.DOUBLE:
                hand.wager *= 2
                hand.doubled = True
                hand.cards.append(shoe.deal())
                note(f"{label}: double -> {_desc(hand.cards)}")
                break
            # SPLIT: current hand keeps one card and continues; the new hand is
            # played after it and receives its second card when reached.
            rank = hand.cards[0]
            moved = hand.cards.pop()
            hand.is_split = True
            new_hand = _Hand(cards=[moved], wager=bet, is_split=True)
            if rank == ACE:
                hand.from_split_aces = True
                new_hand.from_split_aces = True
            hands.insert(i + 1, new_hand)
            note(f"{label}: split {_name(rank)}s ({len(hands)} hands)")
        i += 1

    any_live = any(hand_total(h.cards) <= 21 for h in hands)
    if any_live:
        note(f"dealer reveals {_name(hole)} -> {_desc(dealer_cards)}")
        before = len(dealer_cards)
        play_dealer(dealer_cards, shoe, rules)
        for card in dealer_cards[before:]:
            note(f"dealer draws {_name(card)} -> {_name(card)}")
        if hand_total(dealer_cards) > 21:
            note("dealer busts")
    dealer_total = hand_total(dealer_cards)

    results = []
    profit = 0.0
    for idx, hand in enumerate(hands, 1):
        total = hand_total(hand.cards)
        if total > 21:
            outcome, delta = "lose", -hand.wager
        elif dealer_total > 21:
            if dealer_total == 22 and rules.dealer_22_pushes:
                outcome, delta = "push", 0.0
            else:
                outcome, delta = "win", hand.wager + hand.free_wager
        elif total > dealer_total:
            outcome, delta = "win", hand.wager + hand.free_wager
        elif total < dealer_total:
            outcome, delta = "lose", -hand.wager
        else:
            outcome, delta = "push", 0.0
        note(f"hand {idx}: {outcome} {delta:+g}")
        results.append(
            HandResult(tuple(hand.cards), hand.wager, hand.free_wager, outcome, delta)
        )
        profit += delta
    note(f"round profit {profit:+g}")
    return RoundResult(
        profit, tuple(results), tuple(dealer_cards), tuple(events),
        dealer_played_out=any_live, player_natural=False, was_pair=was_pair,
        did_split=len(hands) > 1, did_double=any(h.doubled for h in hands),
    )
