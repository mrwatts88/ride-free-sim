"""The baccarat coup adapter (M12b rung 3b): ordered-posterior coup pricing.

The two-layer rule (STATUS, 2026-07-19): the posterior core never imports a
game — THIS module is the thin adapter over (posterior filter, baccarat EV
calculator). It converts a filter's sequential next-value law into prices for
the five standard coup bets (Player / Banker / Tie / Dragon 7 / Panda 8) and
runs the E30 measurement: a known 8-deck stack goes through a shuffle model,
the observer filters the dealt stream, and every coup is priced BEFORE it is
dealt. The perfect-counter comparator (`fast_outcomes` on the remaining
composition — the M9-validated exact calculator) rides along on the same
shoes: its profit is everything composition can see, so the filter's excess
is pure order structure, the paradigm-2 quantity.

Pricing machinery — coupled control-variate sampling:

  The joint law of the next 4-6 cards under the filter has no closed form
  (the tableau's tree is ~1e5 nodes of O(slots) filter updates — unaffordable
  per coup), so coups are priced by sequential MC: clone the filter, sample a
  value path card by card, resolve it through the VALIDATED engine
  (`play_baccarat_round` on a stub shoe — no duplicated tableau logic). Raw
  MC at affordable sample counts is too noisy for 40:1 paytables, so each
  sampled path is COUPLED to a composition-model path driven by the same
  uniforms, and the estimator is

      p_hat(outcome) = mean[1_filter - 1_composition] + p_exact(outcome),

  with p_exact from `fast_outcomes`. The variance scales with how much the
  filter's law DIFFERS from composition — exactly the small quantity being
  measured — and when the filter degenerates to a card counter the estimate
  is exact with zero samples' worth of noise (gated in tests).

Selection honesty: bets are SELECTED on one sample set (A) and their edge is
PREDICTED by an independent set (B, drawn only when a bet fires). Selecting
and predicting on the same noisy estimate overstates the edge by winner's
curse; with the split, prediction is unbiased conditional on selection, and
the E17 realized-vs-predicted gate stays meaningful.
"""

import math
import random

from ridefree.baccarat import (
    BaccaratRules,
    ExactOutcomes,
    FlatBettor,
    fast_outcomes,
    play_baccarat_round,
    settle_main,
)
from ridefree.cards import RAW_RANKS, SUITS
from ridefree.cards import value as bj_value
from ridefree.posterior import AssumedDensityShelfPosterior
from ridefree.shuffle import ShelfShuffle

BETS = ("banker", "player", "tie", "dragon7", "panda8")

_NO_BETTOR = FlatBettor(main=None)


class _ListShoe:
    """Minimal shoe over a fixed upcoming-card list (1-10 ints); `dealt`
    records what the engine consumed."""

    def __init__(self, cards) -> None:
        self._cards = iter(cards)
        self.dealt: list[int] = []

    def deal(self) -> int:
        card = next(self._cards)
        self.dealt.append(card)
        return card


class _SampledShoe:
    """Shoe that draws each card lazily from `draw(depth)` — the engine's
    tableau decides how many cards a sampled coup consumes."""

    def __init__(self, draw) -> None:
        self._draw = draw
        self._depth = 0

    def deal(self) -> int:
        card = self._draw(self._depth)
        self._depth += 1
        return card


def resolve_coup(rules: BaccaratRules, cards) -> "BaccaratRound":
    """Resolve one coup from upcoming `cards` (1-10 ints) through the
    validated engine; no wagers are staked."""
    return play_baccarat_round(rules, _ListShoe(cards), _NO_BETTOR)


def _outcome_flags(result) -> dict:
    return {
        "banker": result.outcome == "banker",
        "player": result.outcome == "player",
        "tie": result.outcome == "tie",
        "dragon7": result.banker_three_card_7,
        "panda8": result.player_three_card_8,
    }


def _value_cdf_draw(law: dict, u: float):
    """Draw from a {value: prob} law by inverse CDF in fixed 0-9 order.
    Fixed ordering is what makes two laws driven by the same uniform agree
    whenever their CDFs are close — the coupling."""
    acc = 0.0
    last = None
    for v in range(10):
        p = law.get(v, 0.0)
        if p <= 0.0:
            continue
        acc += p
        last = v
        if u <= acc:
            return v
    return last  # float shortfall: the top of the CDF


def sampled_outcome_probs(
    rules: BaccaratRules,
    filt,
    class_bacc: dict,
    vcount: dict,
    exact: ExactOutcomes,
    rng: random.Random,
    samples: int,
) -> ExactOutcomes:
    """Coupled control-variate estimate of the coup-outcome law under `filt`.

    `filt` is any sequential filter over rank+suit classes (copy() /
    next_value_probs() / observe()); `class_bacc` maps its classes to
    baccarat values 0-9; `vcount` is the remaining composition the coupled
    arm and `exact` were built from. Returns an `ExactOutcomes` carrying
    probabilities (total == 1.0), so the M9 EV methods apply verbatim."""
    diff = {b: 0.0 for b in BETS}
    for _ in range(samples):
        us = [rng.random() for _ in range(6)]
        # -- filter arm: sample a class path, resolve values through the engine
        clone = filt.copy()

        def draw_filter(depth):
            probs = clone.next_value_probs()
            law: dict = {}
            for c, p in probs.items():
                v = class_bacc[c]
                law[v] = law.get(v, 0.0) + p
            v = _value_cdf_draw(law, us[depth])
            # choose which class of value v was seen (a joint draw, not an
            # approximation: class | value from the filter's own law)
            r = rng.random() * law[v]
            acc = 0.0
            chosen = None
            for c, p in probs.items():
                if class_bacc[c] == v:
                    chosen = c
                    acc += p
                    if r <= acc:
                        break
            clone.observe(chosen)
            return v if v else 10
        f_result = play_baccarat_round(rules, _SampledShoe(draw_filter), _NO_BETTOR)

        # -- coupled composition arm: same uniforms, draws without replacement
        comp = dict(vcount)
        comp_n = sum(comp.values())

        def draw_comp(depth):
            nonlocal comp_n
            law = {v: k / comp_n for v, k in comp.items() if k > 0}
            v = _value_cdf_draw(law, us[depth])
            comp[v] -= 1
            comp_n -= 1
            return v if v else 10
        c_result = play_baccarat_round(rules, _SampledShoe(draw_comp), _NO_BETTOR)

        ff = _outcome_flags(f_result)
        cf = _outcome_flags(c_result)
        for b in BETS:
            diff[b] += (1.0 if ff[b] else 0.0) - (1.0 if cf[b] else 0.0)

    probs = {
        "banker": exact.p_banker,
        "player": exact.p_player,
        "tie": exact.p_tie,
        "dragon7": exact.p_dragon7,
        "panda8": exact.p_panda8,
    }
    for b in BETS:
        probs[b] += diff[b] / samples
    return ExactOutcomes(
        total=1.0,
        banker=probs["banker"],
        player=probs["player"],
        tie=probs["tie"],
        dragon7=probs["dragon7"],
        panda8=probs["panda8"],
    )


def bet_evs(outcomes: ExactOutcomes, rules: BaccaratRules) -> dict:
    """EV per unit for the five coup bets, from any ExactOutcomes-shaped law."""
    return {
        "banker": outcomes.ev_main(rules, "banker"),
        "player": outcomes.ev_main(rules, "player"),
        "tie": outcomes.ev_main(rules, "tie"),
        "dragon7": outcomes.ev_dragon7(rules),
        "panda8": outcomes.ev_panda8(rules),
    }


def settle_bet(rules: BaccaratRules, bet: str, result) -> float:
    """Realized profit of 1 unit on `bet` for a resolved coup."""
    if bet in ("banker", "player", "tie"):
        return settle_main(rules, bet, 1.0, outcome=result.outcome,
                           banker_three_card_7=result.banker_three_card_7)
    if bet == "dragon7":
        return rules.dragon7_pays if result.banker_three_card_7 else -1.0
    if bet == "panda8":
        return rules.panda8_pays if result.player_three_card_8 else -1.0
    raise ValueError(f"unknown bet: {bet}")


def coup_experiment(
    rules: BaccaratRules,
    shelves: int,
    shoes: int,
    seed: int,
    *,
    passes: int = 1,
    samples: int = 120,
    thresholds: tuple = (0.0, 0.02, 0.05),
    adf_mix: float | None = None,
    decks: int | None = None,
) -> dict:
    """E30: price every coup of shelf-shuffled known shoes, filter vs counter.

    Per shoe: a fresh uniformly-ordered stack (shoe k, fully observed by
    premise) is shelf-shuffled; coups are dealt to the cut card. Before each
    coup, sample set A selects bets (EV_A > threshold), sample set B prices
    the selected bets (split-sample: selection bias cannot inflate the
    prediction), and the perfect counter selects on its exact composition
    EVs. Realized profits settle from the true coup through the validated
    engine. Returns per-threshold ledgers with per-shoe paired deltas (the
    E17 z), per-bet breakdowns, and the counter comparator on the same shoes.
    """
    decks = rules.decks if decks is None else decks
    classes = [(rank, suit) for suit in SUITS for rank in RAW_RANKS]
    class_bacc = {c: bj_value(c) % 10 for c in classes}
    eq_shelves = shelves
    for _ in range(passes - 1):
        eq_shelves = 2 * eq_shelves * shelves
    model = ShelfShuffle(shelves=shelves, passes=passes)
    rng = random.Random(seed)
    stack_proto = [c for _ in range(decks) for c in classes]
    n = len(stack_proto)
    cutoff = int(rules.penetration * n)

    ledgers = {
        t: {"filter": {b: {"bets": 0, "predicted": 0.0, "realized": 0.0}
                       for b in BETS},
            "counter": {b: {"bets": 0, "predicted": 0.0, "realized": 0.0}
                        for b in BETS},
            "shoe_deltas": [],  # filter arm: per-shoe realized - predicted
            "filter_minus_counter": []}  # per-shoe realized profit gap
        for t in thresholds
    }
    coups_total = 0
    surprises = 0

    for _ in range(shoes):
        stack = list(stack_proto)
        rng.shuffle(stack)  # shoe k, known to the observer
        dealt = [stack[p] for p in model.permute(list(range(n)), rng)]
        filt = AssumedDensityShelfPosterior(eq_shelves, stack, mix=adf_mix)
        vcount = {v: 0 for v in range(10)}
        for c in stack:
            vcount[class_bacc[c]] += 1
        pos = 0
        shoe_led = {t: {"f_pred": 0.0, "f_real": 0.0, "c_real": 0.0}
                    for t in thresholds}
        while pos < cutoff and n - pos >= 6:
            comp = {v: k for v, k in vcount.items() if k > 0}
            exact = fast_outcomes(comp)
            counter_evs = bet_evs(exact, rules)
            evs_a = bet_evs(
                sampled_outcome_probs(rules, filt, class_bacc, vcount, exact,
                                      rng, samples), rules)
            fires = {t: [b for b in BETS if evs_a[b] > t] for t in thresholds}
            evs_b = None
            if any(fires.values()):
                evs_b = bet_evs(
                    sampled_outcome_probs(rules, filt, class_bacc, vcount,
                                          exact, rng, samples), rules)
            # resolve the true coup through the engine
            upcoming = [bj_value(c) for c in dealt[pos:pos + 6]]
            result = resolve_coup(rules, upcoming)
            used = len(result.player_cards) + len(result.banker_cards)
            for t in thresholds:
                led = ledgers[t]
                for b in fires[t]:
                    led["filter"][b]["bets"] += 1
                    led["filter"][b]["predicted"] += evs_b[b]
                    profit = settle_bet(rules, b, result)
                    led["filter"][b]["realized"] += profit
                    shoe_led[t]["f_pred"] += evs_b[b]
                    shoe_led[t]["f_real"] += profit
                for b in BETS:
                    if counter_evs[b] > t:
                        led["counter"][b]["bets"] += 1
                        led["counter"][b]["predicted"] += counter_evs[b]
                        profit = settle_bet(rules, b, result)
                        led["counter"][b]["realized"] += profit
                        shoe_led[t]["c_real"] += profit
            # the observer watches the dealt coup (rank+suit, face up)
            for c in dealt[pos:pos + used]:
                filt.observe(c)
                vcount[class_bacc[c]] -= 1
            pos += used
            coups_total += 1
        surprises += filt.surprises
        for t in thresholds:
            ledgers[t]["shoe_deltas"].append(
                shoe_led[t]["f_real"] - shoe_led[t]["f_pred"])
            ledgers[t]["filter_minus_counter"].append(
                shoe_led[t]["f_real"] - shoe_led[t]["c_real"])

    def z_of(deltas):
        m = sum(deltas) / len(deltas)
        if len(deltas) < 2:
            return 0.0
        var = sum((d - m) ** 2 for d in deltas) / (len(deltas) - 1)
        return m * math.sqrt(len(deltas) / var) if var > 0 else 0.0

    out = {"shoes": shoes, "coups": coups_total, "samples": samples,
           "surprises": surprises, "n": n, "thresholds": {}}
    for t in thresholds:
        led = ledgers[t]
        f_bets = sum(led["filter"][b]["bets"] for b in BETS)
        out["thresholds"][t] = {
            "filter": led["filter"],
            "counter": led["counter"],
            "filter_bets": f_bets,
            "filter_realized": sum(led["filter"][b]["realized"] for b in BETS),
            "filter_predicted": sum(led["filter"][b]["predicted"] for b in BETS),
            "counter_realized": sum(led["counter"][b]["realized"] for b in BETS),
            "z": z_of(led["shoe_deltas"]),
            "excess_per_shoe": sum(led["filter_minus_counter"]) / shoes,
        }
    return out
