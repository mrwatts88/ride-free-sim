"""One live training session: shoe lifecycle, oracle count, error checking.

The human plays the crouch15 card end to end — sizes the bet, plays the hand,
answers insurance, decides when to leave — while this class keeps the ground
truth: the exact visible-card running count (the dealer's hole card is excluded
until settlement, matching what a live counter can see; it is revealed and
counted at settlement, the convention the E16/E17 pricing assumed), the card's
prescribed bet/insurance/leave answer, and BasicStrategy's play. Every decision
becomes an event (correct or not) for the store; mistakes come back as
immediate feedback.

Deterministic under seed: shoes come from `cards.shoe_seeds(seed)` and the
random count-quiz schedule from its own seeded RNG, so a session replays
exactly from its recorded seed.
"""

import random
import time
from dataclasses import dataclass, field

from ridefree.cards import ACE, Shoe, shoe_seeds, value
from ridefree.engine import Action, HandView
from ridefree.hand import hand_total, is_soft
from ridefree.rules import Rules
from ridefree.strategy import BasicStrategy
from ridefree.trainer import driver
from ridefree.trainer.card import PlayCard

# Same safety floor as simulator.py: never start a round that could run the shoe dry.
_MIN_CARDS = 40

_HOLE_DEAL_INDEX = 3  # play_round deal order: player, up, player, hole

PHASE_BET = "bet"
PHASE_INSURANCE = "insurance"
PHASE_ACTION = "action"
PHASE_OVER = "over"


@dataclass
class Event:
    kind: str  # bet | play | insurance | leave | count | peek
    correct: bool | None  # None for peeks (informational, not scored)
    expected: str
    got: str
    context: dict
    round_no: int
    shoe_no: int
    ts: float = field(default_factory=time.time)


@dataclass
class Config:
    quiz_on_shuffle: bool = True
    random_quiz_mean_rounds: int = 15  # 0 = off
    reveal_on_error: bool = True  # include the true RC in error feedback
    # E18b: the walk line is ADVISORY (never-leave costs ~$0-3.5/h net after
    # walk friction). Default drills weekday mode: betting through the line
    # expects the floor bet and walking is never scored. Turn on for weekend
    # drilling (walk-at-zero scored as the E18 card wrote it).
    score_leave: bool = False


class TrainerSession:
    def __init__(
        self,
        rules: Rules,
        card: PlayCard,
        seed: int,
        config: Config | None = None,
        on_event=None,  # callable(Event), e.g. the store
    ) -> None:
        self.rules = rules
        self.card = card
        self.seed = seed
        self.config = config or Config()
        self.on_event = on_event
        self.oracle = BasicStrategy()
        self.started_at = time.time()

        self._seeds = shoe_seeds(seed)
        self._quiz_rng = random.Random(seed ^ 0x5EED)
        self.shoe = Shoe(rules.decks, rules.penetration, next(self._seeds))
        self.shoe_no = 1
        self._rc_committed = card.irc(rules.decks)

        self.phase = PHASE_BET
        self.round_no = 0
        self.net = 0.0
        self.profit_sq = 0.0  # sum of per-round profit^2, for lifetime variance
        self.wagered = 0.0
        # Pace: active seconds accumulate per settled round, with idle gaps
        # capped so a walk-away doesn't dilute the rounds/hour number.
        self.active_seconds = 0.0
        self._last_mark = time.time()
        self.pending_quiz: str | None = None  # reason: shuffle | leave | random
        self._shuffle_after_quiz = False

        self._bet = 0.0
        self._start_pos = 0
        self._script: list[tuple[str, object]] = []
        self._state: driver.RoundState | None = None
        self._last_result_state: driver.RoundState | None = None
        self._last_bet = 0.0

        self.events: list[Event] = []
        self.tally: dict[str, list[int]] = {}  # kind -> [attempts, errors]
        self.count_deltas: list[int] = []

    # ---- oracle count -------------------------------------------------------

    def rc_committed(self) -> int:
        """Visible RC between rounds (all settled cards counted, hole included)."""
        return self._rc_committed

    def rc_visible(self) -> int:
        """Visible RC right now — mid-round the current hole card is hidden."""
        rc = self._rc_committed
        if self._state is not None and self._state.pending is not None:
            for i, raw in enumerate(self._state.deals):
                if i != _HOLE_DEAL_INDEX:
                    rc += self.card.tag(raw)
        return rc

    # ---- decisions ----------------------------------------------------------

    def place_bet(self, amount: float) -> list[Event]:
        self._require_phase(PHASE_BET)
        if self.pending_quiz is not None:
            raise SessionError("answer the count check first")
        self.round_no += 1  # the bet opens this round; its events belong to it
        feedback = []
        rc = self._rc_committed
        card_bet = self.card.bet_for(rc)
        if card_bet is None and not self.config.score_leave:
            card_bet = self.card.floor_bet  # advisory walk line: crouch through it
        if card_bet is None:
            feedback.append(
                self._event("leave", False, "leave", f"bet ${amount:g}", {"rc": rc})
            )
        elif amount != card_bet:
            feedback.append(
                self._event("bet", False, f"${card_bet:g}", f"${amount:g}", {"rc": rc})
            )
        else:
            feedback.append(
                self._event("bet", True, f"${card_bet:g}", f"${amount:g}", {"rc": rc})
            )
        self._bet = amount
        self._last_bet = amount
        self._start_pos = self.shoe.snapshot()
        self._script = []
        self._advance()
        return feedback

    def leave_table(self) -> list[Event]:
        self._require_phase(PHASE_BET)
        if self.pending_quiz is not None:
            raise SessionError("answer the count check first")
        feedback: list[Event] = []
        if self.config.score_leave:
            rc = self._rc_committed
            correct = self.card.bet_for(rc) is None
            expected = "leave" if correct else "stay"
            feedback.append(self._event("leave", correct, expected, "leave", {"rc": rc}))
        # advisory mode: walking is always allowed, never scored — it just
        # moves you to a fresh shoe (the mechanical table change)
        self._begin_shuffle(reason="leave")
        return feedback

    def answer_insurance(self, take: bool) -> list[Event]:
        self._require_phase(PHASE_INSURANCE)
        rc = self.rc_visible()
        should = self.card.insures(rc)
        event = self._event(
            "insurance",
            take == should,
            "take" if should else "decline",
            "take" if take else "decline",
            {"rc": rc},
        )
        self._script.append((driver.INSURANCE, take))
        self._advance()
        return [event]

    def answer_action(self, action: Action) -> list[Event]:
        self._require_phase(PHASE_ACTION)
        view: HandView = self._state.pending.view
        if action not in view.legal:
            raise SessionError(f"{action.value} is not legal here")
        expected = self.oracle.choose(view, self.rules)
        event = self._event(
            "play",
            action is expected,
            expected.value,
            action.value,
            {
                "situation": _situation(view),
                "cards": list(view.cards),
                "up": view.dealer_up,
                "rc": self.rc_visible(),
            },
        )
        self._script.append((driver.ACTION, action))
        self._advance()
        return [event]

    def check_count(self, rc_claim: int, on_demand: bool = False) -> list[Event]:
        if self.phase == PHASE_OVER:
            raise SessionError("session is over")
        truth = self.rc_visible()
        delta = rc_claim - truth
        self.count_deltas.append(delta)
        reason = "on_demand" if on_demand else (self.pending_quiz or "on_demand")
        event = self._event(
            "count",
            delta == 0,
            str(truth),
            str(rc_claim),
            {"delta": delta, "reason": reason},
        )
        if not on_demand and self.pending_quiz is not None:
            self._resolve_quiz()
        return [event]

    def skip_quiz(self) -> None:
        if self.pending_quiz is not None:
            self._resolve_quiz()

    def peek(self) -> tuple[int, Event]:
        truth = self.rc_visible()
        event = self._event("peek", None, str(truth), "peek", {})
        return truth, event

    def end(self) -> dict:
        self.phase = PHASE_OVER
        return self.summary()

    # ---- internals ----------------------------------------------------------

    def _advance(self) -> None:
        state = driver.drive(self.rules, self.shoe, self._start_pos, self._script, self._bet)
        self._state = state
        if state.pending is not None:
            self.phase = (
                PHASE_INSURANCE if state.pending.kind == driver.INSURANCE else PHASE_ACTION
            )
            return
        # Round finished: commit the cards to the count, settle the money.
        for raw in state.deals:
            self._rc_committed += self.card.tag(raw)
        self.net += state.result.profit
        self.profit_sq += state.result.profit * state.result.profit
        self.wagered += self._bet
        now = time.time()
        self.active_seconds += min(now - self._last_mark, 60.0)  # cap idle gaps
        self._last_mark = now
        self._last_result_state = state
        self.phase = PHASE_BET
        self._state = None
        if self.shoe.needs_shuffle or self.shoe.cards_remaining < _MIN_CARDS:
            self._begin_shuffle(reason="shuffle")
        elif (
            self.config.random_quiz_mean_rounds
            and self._quiz_rng.random() < 1.0 / self.config.random_quiz_mean_rounds
        ):
            self.pending_quiz = "random"

    def _begin_shuffle(self, reason: str) -> None:
        if self.config.quiz_on_shuffle:
            self.pending_quiz = reason
            self._shuffle_after_quiz = True
        else:
            self._reshuffle()

    def _resolve_quiz(self) -> None:
        self.pending_quiz = None
        if self._shuffle_after_quiz:
            self._shuffle_after_quiz = False
            self._reshuffle()

    def _reshuffle(self) -> None:
        self.shoe = Shoe(self.rules.decks, self.rules.penetration, next(self._seeds))
        self.shoe_no += 1
        self._rc_committed = self.card.irc(self.rules.decks)
        self._last_result_state = None

    def _event(self, kind, correct, expected, got, context) -> Event:
        event = Event(
            kind=kind,
            correct=correct,
            expected=expected,
            got=got,
            context=context,
            round_no=self.round_no,
            shoe_no=self.shoe_no,
        )
        self.events.append(event)
        if correct is not None:
            attempts_errors = self.tally.setdefault(kind, [0, 0])
            attempts_errors[0] += 1
            if not correct:
                attempts_errors[1] += 1
        if self.on_event is not None:
            self.on_event(event)
        return event

    def _require_phase(self, phase: str) -> None:
        if self.phase != phase:
            raise SessionError(f"not in {phase} phase (currently {self.phase})")

    # ---- reporting ----------------------------------------------------------

    def summary(self) -> dict:
        exact = sum(1 for d in self.count_deltas if d == 0)
        return {
            "seed": self.seed,
            "card": self.card.name,
            "started_at": self.started_at,
            "duration_s": time.time() - self.started_at,
            "rounds": self.round_no,
            "shoes": self.shoe_no,
            "net": self.net,
            "wagered": self.wagered,
            "active_seconds": self.active_seconds,
            "pace_rph": (
                self.round_no / self.active_seconds * 3600
                if self.active_seconds > 0
                else None
            ),
            "by_kind": {
                kind: {"attempts": a, "errors": e, "accuracy": (a - e) / a if a else None}
                for kind, (a, e) in sorted(self.tally.items())
            },
            "count_checks": {
                "n": len(self.count_deltas),
                "exact": exact,
                "mean_abs_delta": (
                    sum(abs(d) for d in self.count_deltas) / len(self.count_deltas)
                    if self.count_deltas
                    else None
                ),
            },
            "errors": [
                {
                    "kind": e.kind,
                    "round": e.round_no,
                    "expected": e.expected,
                    "got": e.got,
                    "context": e.context,
                }
                for e in self.events
                if e.correct is False
            ],
        }

    def state_json(self, feedback: list[Event] | None = None) -> dict:
        table = None
        state = self._state or self._last_result_state
        if state is not None:
            table = _table_json(state, self._bet if self._state else self._last_bet)
        pending = None
        if self.phase == PHASE_ACTION:
            view = self._state.pending.view
            pending = {
                "kind": "action",
                "legal": sorted(a.value for a in view.legal),
            }
        elif self.phase == PHASE_INSURANCE:
            pending = {"kind": "insurance"}
        return {
            "phase": self.phase,
            "round_no": self.round_no,
            "shoe_no": self.shoe_no,
            "cards_dealt": self.shoe.cards_dealt,
            "cards_total": self.rules.decks * 52,
            "net": self.net,
            "wagered": self.wagered,
            "pending": pending,
            "pending_quiz": self.pending_quiz,
            "pace_rph": (
                self.round_no / self.active_seconds * 3600
                if self.active_seconds > 30 and self.round_no >= 5
                else None
            ),
            "table": table,
            "session_stats": {
                kind: {"attempts": a, "errors": e} for kind, (a, e) in self.tally.items()
            },
            "card": {
                "name": self.card.name,
                "floor": self.card.floor_bet,
                "jumps": [list(j) for j in self.card.jumps],
                "insure_at": self.card.insure_at,
                "leave_at": self.card.leave_at,
                "irc": self.card.irc(self.rules.decks),
            },
            "config": vars(self.config),
            "feedback": [_event_json(e, self.config.reveal_on_error) for e in feedback or []],
        }


class SessionError(Exception):
    pass


def _situation(view: HandView) -> str:
    up = "A" if view.dealer_up == ACE else str(view.dealer_up)
    if view.pair_rank is not None and Action.SPLIT in view.legal:
        rank = "A" if view.pair_rank == ACE else str(view.pair_rank)
        return f"pair {rank},{rank} v {up}"
    kind = "soft" if view.soft else "hard"
    return f"{kind} {view.total} v {up}"


def _event_json(event: Event, reveal: bool) -> dict:
    data = {
        "kind": event.kind,
        "correct": event.correct,
        "got": event.got,
        "round_no": event.round_no,
    }
    if event.correct is False or event.kind in ("count", "peek"):
        data["expected"] = event.expected
        if reveal and "rc" in event.context:
            data["rc"] = event.context["rc"]
        if "situation" in event.context:
            data["situation"] = event.context["situation"]
        if "delta" in event.context:
            data["delta"] = event.context["delta"]
    return data


def _table_json(state: driver.RoundState, bet: float) -> dict:
    result = state.result
    hands = []
    for i, hand in enumerate(state.table.hands):
        values = list(hand.values)
        entry = {
            "cards": [list(c) for c in hand.cards],
            "total": hand_total(values),
            "soft": is_soft(values),
            "bet": bet * (2 if hand.doubled else 1),
            "active": state.table.active == i,
        }
        if result is not None and i < len(result.hands):
            hand_result = result.hands[i]
            entry["bet"] = hand_result.wager
            entry["outcome"] = hand_result.outcome
            entry["profit"] = hand_result.profit
        hands.append(entry)
    dealer_cards = [list(c) for c in state.table.dealer]
    if state.table.hole_hidden:
        dealer_cards[1] = None  # face down
    data = {
        "dealer": dealer_cards,
        "dealer_total": (
            hand_total([value(c) for c in state.table.dealer])
            if not state.table.hole_hidden
            else None
        ),
        "hole_hidden": state.table.hole_hidden,
        "hands": hands,
    }
    if result is not None:
        data["settled"] = {
            "profit": result.profit,
            "insurance_profit": result.insurance_profit,
            "player_natural": result.player_natural,
        }
    return data
