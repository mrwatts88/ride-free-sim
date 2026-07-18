"""Replay driver: a human plays one engine round, one decision at a time.

The engine (`play_round`) is synchronous — it asks its strategy for every
decision inline. Instead of forking an interactive engine, this driver replays
the round from the shoe's round-start snapshot each time a new decision is
needed: a scripted strategy feeds the answers recorded so far and raises
`NeedDecision` at the first unanswered ask. The shoe's card order is immutable
and `restore()` rewinds exactly, so every replay re-deals the identical round
(CLAUDE.md rule 3). The engine stays byte-for-byte the validated one; a round
costs O(decisions^2) replays, trivial at human pace.

Display is the one thing the engine does not expose mid-round (it returns only
the final RoundResult), so `_mirror` reconstructs the table — which raw card
went to which hand — from the round's raw deal sequence plus the decision
trace. The mirror is presentation-only (no money, no legality); every finished
round it is asserted card-for-card against the engine's RoundResult, and the
pending hand against the engine's own HandView, so any drift raises
immediately instead of mis-training.
"""

from dataclasses import dataclass

from ridefree.cards import ACE, value
from ridefree.engine import Action, HandView, RoundResult, play_round
from ridefree.hand import hand_total
from ridefree.rules import Rules

# Script/decision kinds
INSURANCE = "insurance"
ACTION = "action"


class NeedDecision(Exception):
    """Raised inside play_round when the script has no answer for this ask."""

    def __init__(self, kind: str, view: HandView | None, cards: tuple[int, ...]):
        self.kind = kind  # INSURANCE or ACTION
        self.view = view  # the engine's HandView (ACTION only)
        self.cards = cards  # player cards at the ask
        super().__init__(kind)


class MirrorError(AssertionError):
    """Display mirror disagreed with the engine — a driver bug, never playable."""


class _ReplayStrategy:
    """Feeds recorded answers to the engine; raises at the first unanswered ask."""

    def __init__(self, script: list[tuple[str, object]]) -> None:
        self._queue = list(script)
        self.trace: list[tuple[str, tuple[int, ...], object]] = []

    def take_insurance(self, cards: tuple[int, ...], rules: Rules) -> bool:
        if not self._queue:
            raise NeedDecision(INSURANCE, None, cards)
        kind, answer = self._queue.pop(0)
        if kind != INSURANCE:
            raise RuntimeError(f"script misaligned: engine asked insurance, script has {kind}")
        self.trace.append((INSURANCE, cards, answer))
        return bool(answer)

    def choose(self, view: HandView, rules: Rules) -> Action:
        if not self._queue:
            raise NeedDecision(ACTION, view, view.cards)
        kind, answer = self._queue.pop(0)
        if kind != ACTION:
            raise RuntimeError(f"script misaligned: engine asked action, script has {kind}")
        self.trace.append((ACTION, view.cards, answer))
        return answer


@dataclass
class MirrorHand:
    cards: list[tuple[int, int]]  # raw (rank, suit)
    doubled: bool = False
    from_split_aces: bool = False

    @property
    def values(self) -> tuple[int, ...]:
        return tuple(value(c) for c in self.cards)


@dataclass
class Table:
    hands: list[MirrorHand]
    dealer: list[tuple[int, int]]  # raw; dealer[1] is the hole card
    hole_hidden: bool
    active: int | None  # hand index awaiting a decision; None when settled


@dataclass
class RoundState:
    """Either a pending decision (result None) or a finished round."""

    pending: NeedDecision | None
    result: RoundResult | None
    table: Table
    deals: tuple[tuple[int, int], ...]  # raw cards this round, deal order


def drive(
    rules: Rules,
    shoe,
    start_pos: int,
    script: list[tuple[str, object]],
    bet: float,
) -> RoundState:
    """(Re)play one round from `start_pos` with the answers in `script`."""
    shoe.restore(start_pos)
    strategy = _ReplayStrategy(script)
    pending: NeedDecision | None = None
    result: RoundResult | None = None
    try:
        result = play_round(rules, shoe, strategy, bet=bet)
    except NeedDecision as need:
        pending = need
    deals = shoe.raw_slice(start_pos, shoe.snapshot())
    if pending is not None:
        shoe.restore(start_pos)  # next drive re-deals the identical round
    table = _mirror(rules, deals, strategy.trace, pending, result)
    return RoundState(pending=pending, result=result, table=table, deals=deals)


def _mirror(
    rules: Rules,
    deals: tuple[tuple[int, int], ...],
    trace: list[tuple[str, tuple[int, ...], object]],
    pending: NeedDecision | None,
    result: RoundResult | None,
) -> Table:
    actions = [(cards, act) for kind, cards, act in trace if kind == ACTION]
    hands = [MirrorHand(cards=[deals[0], deals[2]])]
    dealer = [deals[1], deals[3]]
    idx = 4  # next undealt position in `deals`
    ai = 0  # next unconsumed traced action
    active: int | None = None

    i = 0
    while i < len(hands) and active is None:
        hand = hands[i]
        while True:
            if len(hand.cards) == 1:  # freshly split, second card on arrival
                if idx >= len(deals):
                    active = i  # pending mid-split (engine stopped before dealing)
                    break
                hand.cards.append(deals[idx])
                idx += 1
            total = hand_total(list(hand.values))
            if total >= 21:
                break  # engine never asks at 21/bust
            if _ace_blocked(hand, len(hands), rules):
                break  # one card to each split ace, no resplit available
            if ai < len(actions) and actions[ai][0] == hand.values:
                _, act = actions[ai]
                ai += 1
                if act is Action.STAND:
                    break
                if act is Action.HIT:
                    hand.cards.append(deals[idx])
                    idx += 1
                    continue
                if act is Action.DOUBLE:
                    hand.doubled = True
                    hand.cards.append(deals[idx])
                    idx += 1
                    break
                # SPLIT: keep the first card; the new hand waits after this one
                moved = hand.cards.pop()
                new_hand = MirrorHand(cards=[moved])
                if value(moved) == ACE:
                    hand.from_split_aces = True
                    new_hand.from_split_aces = True
                hands.insert(i + 1, new_hand)
                continue
            if pending is not None and ai == len(actions) and hand.values == pending.cards:
                active = i  # the engine's unanswered ask is on this hand
                break
            break  # engine auto-completed this hand
        i += 1

    if pending is not None and pending.kind == INSURANCE:
        active = 0

    hole_hidden = pending is not None
    if not hole_hidden and result is not None and result.dealer_played_out:
        dealer.extend(deals[idx:])  # everything after the player phase is the dealer's

    table = Table(hands=hands, dealer=dealer, hole_hidden=hole_hidden, active=active)
    _assert_mirror(table, pending, result)
    return table


def _ace_blocked(hand: MirrorHand, n_hands: int, rules: Rules) -> bool:
    """Mirror of the engine's split-ace auto-stand (engine.legal_actions)."""
    if not hand.from_split_aces or rules.hit_split_aces:
        return False
    can_resplit = (
        len(hand.cards) == 2
        and hand.values == (ACE, ACE)
        and rules.resplit_aces
        and n_hands < rules.max_hands
    )
    return not can_resplit


def _assert_mirror(table: Table, pending: NeedDecision | None, result: RoundResult | None) -> None:
    if result is not None:
        got = tuple(h.values for h in table.hands)
        want = tuple(h.cards for h in result.hands)
        if got != want:
            raise MirrorError(f"mirror hands {got} != engine {want}")
        dealer = tuple(value(c) for c in table.dealer)
        if dealer != result.dealer_cards:
            raise MirrorError(f"mirror dealer {dealer} != engine {result.dealer_cards}")
    elif pending is not None:
        if table.active is None:
            raise MirrorError("pending decision but no active mirror hand")
        if pending.kind == ACTION and table.hands[table.active].values != pending.cards:
            raise MirrorError(
                f"active mirror hand {table.hands[table.active].values} "
                f"!= engine ask {pending.cards}"
            )
