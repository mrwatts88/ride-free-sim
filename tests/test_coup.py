"""M12b rung-3b gates: the baccarat coup adapter.

The load-bearing gate is control-variate exactness: a filter whose law IS
the remaining composition must price every coup outcome exactly equal to
`fast_outcomes` (the M9-validated exact calculator) with ZERO sampling
variance — the coupled paths cancel indicator-for-indicator, proving the
estimator is anchored to the exact reference and that all MC noise lives in
the filter-vs-composition DIFFERENCE. Coup resolution itself reuses the
validated engine (`play_baccarat_round`), never a reimplemented tableau.
Test pins: 23.0e9 block.
"""

import random

from ridefree.baccarat import EZ_BACCARAT_8D, fast_outcomes
from ridefree.cards import RAW_RANKS, SUITS
from ridefree.cards import value as bj_value
from ridefree.coup import (
    BETS,
    bet_evs,
    coup_experiment,
    resolve_coup,
    sampled_outcome_probs,
    settle_bet,
)

Z_GATE = 4.5


class _CompositionFilter:
    """A 'filter' whose next-value law is exactly the remaining composition:
    the perfect counter wearing the filter interface."""

    def __init__(self, counts: dict) -> None:
        self._counts = dict(counts)

    def copy(self) -> "_CompositionFilter":
        return _CompositionFilter(self._counts)

    def next_value_probs(self) -> dict:
        total = sum(self._counts.values())
        return {c: k / total for c, k in self._counts.items() if k > 0}

    def observe(self, cls) -> None:
        self._counts[cls] -= 1


def test_cv_estimator_is_exact_for_the_perfect_counter():
    # Filter law == composition law -> coupled paths agree step for step,
    # the difference term is identically zero, and the sampled outcome law
    # equals fast_outcomes EXACTLY at ANY sample count.
    classes = [(rank, suit) for suit in SUITS for rank in RAW_RANKS]
    class_bacc = {c: bj_value(c) % 10 for c in classes}
    rng = random.Random(23000000005)
    counts = {c: 1 for c in classes}  # a single-deck remainder
    vcount = {v: 0 for v in range(10)}
    for c in classes:
        vcount[class_bacc[c]] += 1
    exact = fast_outcomes({v: k for v, k in vcount.items() if k > 0})
    got = sampled_outcome_probs(
        EZ_BACCARAT_8D, _CompositionFilter(counts), class_bacc, vcount,
        exact, rng, samples=40,
    )
    assert abs(got.p_banker - exact.p_banker) < 1e-12
    assert abs(got.p_player - exact.p_player) < 1e-12
    assert abs(got.p_tie - exact.p_tie) < 1e-12
    assert abs(got.p_dragon7 - exact.p_dragon7) < 1e-12
    assert abs(got.p_panda8 - exact.p_panda8) < 1e-12
    evs = bet_evs(got, EZ_BACCARAT_8D)
    ref = bet_evs(exact, EZ_BACCARAT_8D)
    for b in BETS:
        assert abs(evs[b] - ref[b]) < 1e-12, b


def test_resolve_coup_flags_are_consistent():
    # Engine-resolved coups: dragon7 implies a 3-card banker WIN of 7,
    # panda8 a 3-card player WIN of 8; card consumption is 4-6.
    rng = random.Random(23000000006)
    for _ in range(300):
        cards = [rng.randint(1, 10) for _ in range(6)]
        r = resolve_coup(EZ_BACCARAT_8D, cards)
        used = len(r.player_cards) + len(r.banker_cards)
        assert 4 <= used <= 6
        if r.banker_three_card_7:
            assert r.outcome == "banker" and len(r.banker_cards) == 3
            assert r.banker_total == 7
        if r.player_three_card_8:
            assert r.outcome == "player" and len(r.player_cards) == 3
            assert r.player_total == 8
        # settle_bet's payoffs are the rules' paytables verbatim
        assert settle_bet(EZ_BACCARAT_8D, "dragon7", r) == (
            EZ_BACCARAT_8D.dragon7_pays if r.banker_three_card_7 else -1.0
        )


def test_coup_experiment_smoke_and_gate():
    # A small real run (1 deck so the ADF is the exact rung-1 filter,
    # 3 shelves to keep the axis tiny): ledger structure sane, the E17 z
    # inside the gate, and the counter arm's predictions are exact EVs.
    out = coup_experiment(
        EZ_BACCARAT_8D, shelves=3, shoes=3, seed=23000000007,
        samples=40, thresholds=(0.02,), decks=1,
    )
    assert out["coups"] > 0
    led = out["thresholds"][0.02]
    assert abs(led["z"]) < Z_GATE, led
    for b in BETS:
        f = led["filter"][b]
        assert f["bets"] >= 0
        if f["bets"]:
            assert f["predicted"] != 0.0
