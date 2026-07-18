"""Trainer gates: the card's numbers, the replay driver vs the engine, the
session's oracle checks, and the store.

The heavyweight check is the fuzz test: thousands of engine rounds driven
decision-by-decision through the replay driver with random legal actions — the
driver's internal mirror assertion compares every finished round card-for-card
against the engine's RoundResult, so any display/replay drift fails loudly.
The session gate is an oracle player: a bot that always answers exactly what
the card and BasicStrategy prescribe must be scored error-free.
"""

import dataclasses
import random

import pytest

from ridefree.cards import Shoe
from ridefree.engine import Action
from ridefree.rules import STANDARD_6D_H17
from ridefree.trainer import driver
from ridefree.trainer.card import CROUCH15_2R, CROUCH15_RED7, DEFAULT_CARD
from ridefree.trainer.driver import ACTION, INSURANCE, drive
from ridefree.trainer.session import Config, SessionError, TrainerSession
from ridefree.trainer.store import Store

CARD = CROUCH15_RED7
RULES = STANDARD_6D_H17


class RawStackedShoe:
    """Raw-card twin of test_engine.StackedShoe, with the snapshot/restore and
    raw_slice surface the replay driver needs."""

    def __init__(self, raw_cards):
        self._raw = [tuple(c) for c in raw_cards]
        self._cards = [min(r, 10) for r, _ in self._raw]
        self._pos = 0

    def deal(self):
        card = self._cards[self._pos]
        self._pos += 1
        return card

    def snapshot(self):
        return self._pos

    def restore(self, pos):
        self._pos = pos

    def raw_slice(self, start, stop):
        return tuple(self._raw[start:stop])

    @property
    def needs_shuffle(self):
        return False

    @property
    def cards_dealt(self):
        return self._pos

    @property
    def cards_remaining(self):
        return len(self._cards) - self._pos


# --- the card -------------------------------------------------------------


def test_tags_hilo_plus_red_sevens():
    assert all(CARD.tag((rank, 2)) == 1 for rank in range(2, 7))
    assert CARD.tag((7, 0)) == 1 and CARD.tag((7, 1)) == 1  # red sevens
    assert CARD.tag((7, 2)) == 0 and CARD.tag((7, 3)) == 0  # black sevens
    assert CARD.tag((8, 0)) == 0 and CARD.tag((9, 1)) == 0
    assert all(CARD.tag((rank, 1)) == -1 for rank in (1, 10, 11, 12, 13))


def test_irc_is_minus_12_for_six_decks():
    assert CARD.irc(RULES.decks) == -12


@pytest.mark.parametrize(
    "rc,bet",
    [
        (-15, None), (-14, None),  # leave
        (-13, 15.0), (-1, 15.0),  # the crouch
        (0, 100.0), (1, 100.0),
        (2, 150.0), (4, 150.0),
        (5, 200.0), (30, 200.0),
    ],
)
def test_bet_rungs(rc, bet):
    assert CARD.bet_for(rc) == bet


def test_insurance_threshold():
    assert not CARD.insures(1)
    assert CARD.insures(2)


# --- the locked E18 card (crouch15-2r, slid scale: walk line AT zero) ------


def test_locked_card_is_the_default():
    assert DEFAULT_CARD is CROUCH15_2R


def test_locked_card_starts_at_plus_6():
    # shift +18 over the pivot scale's IRC -12
    assert CROUCH15_2R.irc(RULES.decks) == 6


@pytest.mark.parametrize(
    "rc,bet",
    [
        (-3, None), (0, None),  # the walk line IS zero
        (1, 15.0), (17, 15.0),  # the crouch
        (18, 100.0), (21, 100.0),  # the pivot rung (TC +2, depth-exact)
        (22, 200.0), (40, 200.0),  # max bet
    ],
)
def test_locked_card_rungs(rc, bet):
    assert CROUCH15_2R.bet_for(rc) == bet


def test_locked_card_insures_only_at_max_bet():
    assert not CROUCH15_2R.insures(21)
    assert CROUCH15_2R.insures(22)


def test_locked_card_tags_unchanged_by_the_slide():
    for rank in range(1, 14):
        for suit in range(4):
            assert CROUCH15_2R.tag((rank, suit)) == CROUCH15_RED7.tag((rank, suit))


def test_session_on_locked_card_scores_leave_at_zero():
    session = TrainerSession(RULES, CROUCH15_2R, seed=31, config=quiet_config())
    assert session.rc_committed() == 6
    session._rc_committed = 0
    feedback = session.leave_table()
    assert feedback[0].kind == "leave" and feedback[0].correct is True
    assert session.rc_committed() == 6  # fresh shoe restarts at +6
    feedback = session.leave_table()  # +6 is comfortably above the walk line
    assert feedback[0].correct is False and feedback[0].expected == "stay"


# --- the replay driver ----------------------------------------------------


def test_pending_then_stand():
    shoe = RawStackedShoe([(13, 2), (7, 3), (9, 2), (5, 3), (5, 0)])
    state = drive(RULES, shoe, 0, [], bet=10.0)
    assert state.pending is not None and state.pending.kind == ACTION
    assert state.pending.view.cards == (10, 9)
    assert state.table.hole_hidden and state.table.active == 0
    assert state.table.hands[0].cards == [(13, 2), (9, 2)]
    assert shoe.snapshot() == 0  # rewound, ready to replay

    state = drive(RULES, shoe, 0, [(ACTION, Action.STAND)], bet=10.0)
    assert state.pending is None
    # dealer 7 + 5 = 12 draws the 5 -> 17; player 19 wins
    assert state.result.profit == 10.0
    assert state.table.dealer == [(7, 3), (5, 3), (5, 0)]
    assert not state.table.hole_hidden


def test_insurance_asked_then_dealer_blackjack():
    shoe = RawStackedShoe([(5, 2), (1, 0), (9, 2), (12, 1)])
    state = drive(RULES, shoe, 0, [], bet=10.0)
    assert state.pending.kind == INSURANCE
    assert state.table.active == 0 and state.table.hole_hidden

    state = drive(RULES, shoe, 0, [(INSURANCE, False)], bet=10.0)
    assert state.result is not None
    assert state.result.profit == -10.0  # dealer natural, no insurance
    assert state.table.dealer == [(1, 0), (12, 1)]


def test_split_mirror_places_raw_cards():
    shoe = RawStackedShoe(
        [(8, 0), (6, 1), (8, 2), (10, 3), (10, 0), (3, 1), (10, 1), (9, 0)]
    )
    script = []
    expected_asks = [(8, 8), (8, 10), (8, 3)]
    answers = [Action.SPLIT, Action.STAND, Action.DOUBLE]
    for want, answer in zip(expected_asks, answers):
        state = drive(RULES, shoe, 0, script, bet=10.0)
        assert state.pending.view.cards == want
        script.append((ACTION, answer))
    state = drive(RULES, shoe, 0, script, bet=10.0)
    assert state.result is not None
    assert state.table.hands[0].cards == [(8, 0), (10, 0)]
    assert state.table.hands[1].cards == [(8, 2), (3, 1), (10, 1)]
    assert state.table.hands[1].doubled
    # dealer 6 + 10 = 16 draws 9 -> 25 bust; both hands win, double pays 2x
    assert state.table.dealer == [(6, 1), (10, 3), (9, 0)]
    assert state.result.profit == 30.0


def test_split_aces_one_card_each():
    shoe = RawStackedShoe(
        [(1, 0), (6, 1), (1, 2), (9, 3), (5, 0), (7, 1), (10, 2)]
    )
    state = drive(RULES, shoe, 0, [], bet=10.0)
    assert state.pending.view.cards == (1, 1)
    state = drive(RULES, shoe, 0, [(ACTION, Action.SPLIT)], bet=10.0)
    assert state.result is not None  # no further asks: one card per split ace
    assert state.table.hands[0].cards == [(1, 0), (5, 0)]
    assert state.table.hands[1].cards == [(1, 2), (7, 1)]
    # dealer 6+9=15 draws 10 -> 25 bust: soft 16 and soft 18 both win
    assert state.result.profit == 20.0


def test_replay_is_deterministic():
    shoe = RawStackedShoe([(13, 2), (7, 3), (9, 2), (5, 3), (5, 0)])
    first = drive(RULES, shoe, 0, [], bet=10.0)
    second = drive(RULES, shoe, 0, [], bet=10.0)
    assert first.pending.view == second.pending.view
    assert first.table.hands[0].cards == second.table.hands[0].cards


def test_fuzz_mirror_matches_engine_over_random_play():
    """Random legal decisions over full shoes; the driver's internal assertion
    compares every finished round against the engine's RoundResult."""
    rng = random.Random(20260718)
    rounds = 0
    for _ in range(40):
        shoe = Shoe(RULES.decks, RULES.penetration, rng.getrandbits(40))
        while not shoe.needs_shuffle and shoe.cards_remaining >= 40:
            start = shoe.snapshot()
            script = []
            while True:
                state = drive(RULES, shoe, start, script, bet=10.0)
                if state.pending is None:
                    break
                if state.pending.kind == INSURANCE:
                    script.append((INSURANCE, rng.random() < 0.5))
                    continue
                legal = sorted(state.pending.view.legal, key=lambda a: a.value)
                if Action.SPLIT in legal and rng.random() < 0.5:
                    choice = Action.SPLIT  # bias toward the mirror's hardest path
                else:
                    choice = rng.choice(legal)
                script.append((ACTION, choice))
            rounds += 1
    assert rounds > 1000


# --- the session ----------------------------------------------------------


def quiet_config():
    return Config(quiz_on_shuffle=False, random_quiz_mean_rounds=0)


@pytest.mark.parametrize("card", [CROUCH15_RED7, CROUCH15_2R], ids=lambda c: c.name)
def test_oracle_player_is_error_free(card):
    """A bot that answers exactly what the card and BasicStrategy prescribe
    must be scored 100% correct — the checker checked against itself."""
    session = TrainerSession(RULES, card, seed=414243, config=quiet_config())
    for _ in range(300):
        if session.phase == "bet":
            expected = card.bet_for(session.rc_committed())
            if expected is None:
                session.leave_table()
            else:
                session.place_bet(expected)
        elif session.phase == "insurance":
            session.answer_insurance(card.insures(session.rc_visible()))
        elif session.phase == "action":
            view = session._state.pending.view
            session.answer_action(session.oracle.choose(view, RULES))
    for kind, (attempts, errors) in session.tally.items():
        assert errors == 0, f"{kind}: {errors}/{attempts} scored wrong"
    assert session.tally["bet"][0] > 0 and session.tally["play"][0] > 0


def test_rc_visibility_excludes_hole_until_settlement():
    session = TrainerSession(RULES, CARD, seed=1, config=quiet_config())
    # pad with tag-0 cards so the safety-floor reshuffle doesn't fire
    session.shoe = RawStackedShoe([(5, 2), (1, 0), (9, 2), (12, 1)] + [(8, 2)] * 40)
    session._rc_committed = CARD.irc(RULES.decks)
    session.place_bet(15.0)
    assert session.phase == "insurance"
    # visible: 5 (+1), A (-1), 9 (0); the hole queen is NOT counted yet
    assert session.rc_visible() == -12
    session.answer_insurance(False)  # dealer had it: round over, hole revealed
    assert session.phase == "bet"
    assert session.rc_committed() == -13


def test_wrong_bet_and_wrong_play_are_flagged():
    session = TrainerSession(RULES, CARD, seed=99, config=quiet_config())
    session.shoe = RawStackedShoe(
        [(13, 2), (7, 3), (6, 2), (5, 3), (9, 0), (13, 0), (10, 1)]
    )
    session._rc_committed = 0  # card says $100
    feedback = session.place_bet(15.0)
    assert feedback[0].kind == "bet" and feedback[0].correct is False
    assert feedback[0].expected == "$100"
    # hard 16 v 7: basic strategy hits; stand must be flagged
    feedback = session.answer_action(Action.STAND)
    assert feedback[0].kind == "play" and feedback[0].correct is False
    assert feedback[0].expected == "hit"
    assert feedback[0].context["situation"] == "hard 16 v 7"


def test_leave_scoring_both_ways():
    session = TrainerSession(RULES, CARD, seed=7, config=quiet_config())
    session._rc_committed = -14
    feedback = session.leave_table()
    assert feedback[0].kind == "leave" and feedback[0].correct is True
    assert session.shoe_no == 2
    assert session.rc_committed() == -12  # fresh shoe, IRC restored

    feedback = session.leave_table()  # RC -12 > leave threshold: wrong to go
    assert feedback[0].correct is False and feedback[0].expected == "stay"


def test_betting_into_a_leave_count_is_flagged():
    session = TrainerSession(RULES, CARD, seed=8, config=quiet_config())
    session._rc_committed = -15
    feedback = session.place_bet(15.0)
    assert feedback[0].kind == "leave" and feedback[0].correct is False
    assert feedback[0].expected == "leave"


def test_shuffle_quiz_blocks_betting_and_resets_count():
    rules = dataclasses.replace(RULES, penetration=0.02)  # cut after ~6 cards
    session = TrainerSession(rules, CARD, seed=5, config=Config(random_quiz_mean_rounds=0))
    bet = CARD.bet_for(session.rc_committed()) or 15.0
    session.place_bet(bet)
    while session.phase == "action":
        view = session._state.pending.view
        session.answer_action(session.oracle.choose(view, rules))
    if session.phase == "insurance":
        session.answer_insurance(False)
        while session.phase == "action":
            view = session._state.pending.view
            session.answer_action(session.oracle.choose(view, rules))
    assert session.pending_quiz == "shuffle"
    with pytest.raises(SessionError):
        session.place_bet(15.0)
    truth = session.rc_visible()
    feedback = session.check_count(truth + 2)
    assert feedback[0].correct is False and feedback[0].context["delta"] == 2
    assert session.pending_quiz is None
    assert session.shoe_no == 2
    assert session.rc_committed() == CARD.irc(rules.decks)


def test_summary_shape():
    session = TrainerSession(RULES, CARD, seed=17, config=quiet_config())
    session.place_bet(CARD.bet_for(session.rc_committed()))
    while session.phase != "bet":
        if session.phase == "insurance":
            session.answer_insurance(CARD.insures(session.rc_visible()))
        else:
            view = session._state.pending.view
            session.answer_action(session.oracle.choose(view, RULES))
    summary = session.end()
    assert summary["rounds"] == 1 and summary["seed"] == 17
    assert "bet" in summary["by_kind"]
    assert summary["by_kind"]["bet"]["errors"] == 0


# --- the store ------------------------------------------------------------


def test_store_roundtrip_and_lifetime(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    session = TrainerSession(RULES, CARD, seed=21, config=quiet_config())
    sid = store.start_session(session.seed, session.card.name, session.started_at)
    session.on_event = lambda event: store.log_event(sid, event)

    session.shoe = RawStackedShoe(
        [(13, 2), (7, 3), (6, 2), (5, 3), (9, 0), (13, 0), (10, 1)]
    )
    session._rc_committed = 0
    session.place_bet(15.0)  # wrong: card says $100
    session.answer_action(Action.STAND)  # wrong: hits 16 v 7
    store.update_session(sid, session, ended=True)

    stats = store.lifetime()
    assert stats["sessions"] == 1 and stats["rounds"] == 1
    kinds = {row["kind"]: row for row in stats["by_kind"]}
    assert kinds["bet"]["errors"] == 1 and kinds["play"]["errors"] == 1
    assert stats["play_mistakes"][0]["situation"] == "hard 16 v 7"
    assert stats["play_mistakes"][0]["expected"] == "hit"
    assert stats["bet_mistakes"][0] == {"expected": "$100", "got": "$15", "n": 1}
    assert stats["recent_sessions"][0]["errors"] == 2
    store.close()
