"""M12b rung-1 gates: the exact shelf posterior.

The load-bearing gate is brute force: enumerate every lane assignment of a
small deck through an INDEPENDENT physical pile simulation (deques, dealt
from the bottom — the machine, not the slot arithmetic), and check the
posterior's conditional next-card law against exact enumeration at every
step of every reachable output. Then: the posterior argmax must be at least
as good a feedback guesser as DFH's conjectured-optimal strategy (paired,
same decks), it must be calibrated (its own claimed hit probabilities match
realized), and the first payoff adapter must realize its predicted edge
within CI (the E17 ramp pattern). Test seeds: 22.7e9 block (rung 1-2),
23.0e9 block (rung 3, the assumed-density filter).
"""

import itertools
import math
import random
from collections import Counter, deque

from ridefree.forensics import ShelfGuesser, guessing_experiment
from ridefree.posterior import (
    AssumedDensityShelfPosterior,
    MultiDeckShelfPosterior,
    PosteriorGuesser,
    ShelfPosterior,
    multideck_proposition_experiment,
    proposition_experiment,
)
from ridefree.shuffle import ShelfShuffle

Z_GATE = 4.5


def physical_shelf_output(stack, shelves, lanes_by_temporal):
    """The machine, simulated with piles — independent of the slot math:
    deal from the bottom of the stack; even lane = on top of the shelf's
    pile, odd lane = under it; unload shelves in order."""
    piles = [deque() for _ in range(shelves)]
    for card, lane in zip(reversed(stack), lanes_by_temporal):
        if lane & 1:
            piles[lane >> 1].append(card)
        else:
            piles[lane >> 1].appendleft(card)
    out = []
    for pile in piles:
        out.extend(pile)
    return tuple(out)


def brute_force_walk(stack, shelves, max_outputs=40):
    """Yield (output, list-of-exact-conditionals) by full enumeration."""
    n = len(stack)
    lanes = 2 * shelves
    by_output = Counter()
    for assignment in itertools.product(range(lanes), repeat=n):
        by_output[physical_shelf_output(stack, shelves, assignment)] += 1
    for output in sorted(by_output)[:max_outputs]:
        conditionals = []
        for t in range(n):
            prefix = output[:t]
            nxt = Counter()
            for out, w in by_output.items():
                if out[:t] == prefix:
                    nxt[out[t]] += w
            total = sum(nxt.values())
            conditionals.append({c: w / total for c, w in nxt.items()})
        yield output, conditionals


def test_posterior_matches_brute_force():
    for stack, shelves in (([1, 2, 3, 4, 5], 2), ([1, 2, 3, 4, 5, 6], 1)):
        for output, conditionals in brute_force_walk(stack, shelves):
            posterior = ShelfPosterior(shelves, stack)
            for t, card in enumerate(output):
                probs = posterior.next_probs()
                assert abs(sum(probs.values()) - 1.0) < 1e-12
                exact = conditionals[t]
                for c in stack:
                    assert abs(probs.get(c, 0.0) - exact.get(c, 0.0)) < 1e-9, (
                        stack,
                        shelves,
                        output,
                        t,
                        c,
                    )
                posterior.observe(card)


def test_posterior_consistent_with_sampler():
    # Every sampled output must be walkable (never "impossible"), across
    # sizes and shelf counts, including a two-pass sample against its
    # Cor 4.2 equivalent single-pass posterior (2 * 4 * 4 = 32 shelves).
    rng = random.Random(22700000001)
    for shelves, passes, eq in ((4, 1, 4), (10, 1, 10), (4, 2, 32)):
        model = ShelfShuffle(shelves=shelves, passes=passes)
        stack = list(range(1, 27))
        for _ in range(60):
            posterior = ShelfPosterior(eq, stack)
            for card in model.permute(stack, rng):
                assert posterior.next_probs()[card] > 0.0
                posterior.observe(card)


def test_impossible_observation_raises():
    # One shelf produces unimodal output only; a valley is unreachable.
    posterior = ShelfPosterior(1, [1, 2, 3, 4, 5])
    for card in (3, 1):  # 3 then 1 then 2 would need a valley
        posterior.observe(card)
    try:
        posterior.observe(2)
        posterior.next_probs()
    except ValueError:
        pass
    else:
        raise AssertionError("expected impossible observation to raise")


def test_posterior_guesser_dominates_conjectured_strategy():
    # Paired on identical decks: the exact-posterior argmax is the true
    # optimal feedback guesser, so it must not lose to DFH's conjectured
    # strategy; the delta measures what the conjecture leaves on the table.
    # Calibration rides along: the posterior's own claimed hit probability
    # must match its realized hits.
    trials, n, m = 400, 52, 10
    rng = random.Random(22700000002)
    stack = list(range(1, n + 1))
    model = ShelfShuffle(shelves=m)
    deltas = []
    post_total = 0
    predicted_total = 0.0
    for _ in range(trials):
        deck = model.permute(stack, rng)
        scores = []
        post = PosteriorGuesser(m, stack)
        shelf = ShelfGuesser(n)
        for guesser in (post, shelf):
            correct = 0
            for card in deck:
                if guesser.guess() == card:
                    correct += 1
                guesser.observe(card)
            scores.append(correct)
        deltas.append(scores[0] - scores[1])
        post_total += scores[0]
        predicted_total += post.predicted
    mean_delta = sum(deltas) / trials
    var_delta = sum((d - mean_delta) ** 2 for d in deltas) / (trials - 1)
    se = math.sqrt(var_delta / trials)
    assert mean_delta > -max(3 * se, 1e-9), (mean_delta, se)
    # calibration: realized correct vs the posterior's own prediction
    z = (post_total - predicted_total) / math.sqrt(predicted_total)
    assert abs(z) < Z_GATE, (post_total, predicted_total)


def test_posterior_guesser_one_shelf_hits_published_39():
    stats = guessing_experiment(
        ShelfShuffle(shelves=1),
        52,
        200,
        22700000003,
        guesser_factory=lambda n: PosteriorGuesser(1, list(range(1, n + 1))),
    )
    assert abs(stats.mean - 39.0) <= 0.6, stats  # DFH Table 2, m=1


def test_proposition_realizes_predicted_edge():
    result = proposition_experiment(
        shelves=10, trials=250, seed=22700000004, threshold=0.02
    )
    assert result.bets > 0
    assert abs(result.z) < Z_GATE, (result.realized, result.predicted, result.z)
    assert result.realized > 0.0, result.realized  # order structure pays


# ---------------------------------------------------------------------------
# Multi-deck (repeated cards): the particle filter vs brute-force truth


def brute_force_value_conditionals(values, shelves, max_outputs=30):
    """Exact next-VALUE conditionals by full enumeration, treating equal
    `values` as indistinguishable — the ground truth the filter approximates."""
    n = len(values)
    lanes = 2 * shelves
    by_output = Counter()
    for assignment in itertools.product(range(lanes), repeat=n):
        positions = physical_shelf_output(list(range(n)), shelves, assignment)
        by_output[tuple(values[p] for p in positions)] += 1
    walks = []
    for output in sorted(by_output)[:max_outputs]:
        conditionals = []
        for t in range(n):
            prefix = output[:t]
            nxt = Counter()
            for out, w in by_output.items():
                if out[:t] == prefix:
                    nxt[out[t]] += w
            total = sum(nxt.values())
            conditionals.append({v: w / total for v, w in nxt.items()})
        walks.append((output, conditionals))
    return walks


def test_multideck_first_step_is_exact():
    # Before any observation all particles are identical, so the filter's
    # first next-value law is exact regardless of particle count.
    values = [0, 0, 1, 1, 2, 2]
    walks = brute_force_value_conditionals(values, shelves=1)
    exact0 = walks[0][1][0]
    filt = MultiDeckShelfPosterior(1, values, particles=8, seed=1)
    got = filt.next_value_probs()
    for v in set(values):
        assert abs(got.get(v, 0.0) - exact0.get(v, 0.0)) < 1e-12, (v, got, exact0)


def test_multideck_matches_brute_force_within_mc():
    # Drive the filter along real sampled outputs; its next-value law must
    # track the exact conditional within particle-count MC error at each step.
    for values, shelves in (([0, 0, 1, 1], 2), ([0, 0, 1, 1, 2, 2], 1)):
        exact = dict(brute_force_value_conditionals(values, shelves))
        model = ShelfShuffle(shelves=shelves)
        rng = random.Random(22700000005)
        checked = 0
        for _ in range(12):
            output = tuple(
                values[p]
                for p in model.permute(list(range(len(values))), rng)
            )
            if output not in exact:
                continue
            checked += 1
            filt = MultiDeckShelfPosterior(
                shelves, values, particles=4000, seed=rng.getrandbits(31)
            )
            for t, v in enumerate(output):
                got = filt.next_value_probs()
                for val in set(values):
                    assert abs(got.get(val, 0.0) - exact[output][t].get(val, 0.0)) < 0.05, (
                        values, shelves, output, t, val, got, exact[output][t]
                    )
                filt.observe(v)
        assert checked >= 6


def test_multideck_distinct_values_is_exact_deterministic():
    # With all-distinct values there are no copies, so every observation pins
    # a unique position: the filter reduces to the rung-1 exact posterior,
    # deterministically (no sampling variance), for any particle count.
    values = [5, 2, 9, 1, 7, 3]
    model = ShelfShuffle(shelves=2)
    output = [
        values[p] for p in model.permute(list(range(len(values))), random.Random(3))
    ]
    filt = MultiDeckShelfPosterior(2, values, particles=3, seed=99)
    exact = ShelfPosterior(2, values)
    for v in output:
        fprobs = filt.next_value_probs()
        eprobs = exact.next_probs()  # keyed by value == position label here
        for val in values:
            assert abs(fprobs.get(val, 0.0) - eprobs.get(val, 0.0)) < 1e-9
        filt.observe(v)
        exact.observe(v)


# ---------------------------------------------------------------------------
# Rung 3: the assumed-density filter — exact where exactness is possible,
# measured bias where it is not (test pins: 23.0e9 block)


def test_adf_distinct_values_reduces_to_exact():
    # With distinct values the water-fill is trivial (one candidate at
    # occupancy 1), the chain is rung 1's chain, no hedge and no
    # contamination apply: the ADF IS the exact posterior, deterministically.
    values = [5, 2, 9, 1, 7, 3, 8, 4]
    model = ShelfShuffle(shelves=2)
    rng = random.Random(23000000001)
    for _ in range(20):
        output = [values[p] for p in model.permute(list(range(len(values))), rng)]
        adf = AssumedDensityShelfPosterior(2, values)
        exact = ShelfPosterior(2, values)
        for v in output:
            aprobs = adf.next_value_probs()
            eprobs = exact.next_probs()
            for val in values:
                assert abs(aprobs.get(val, 0.0) - eprobs.get(val, 0.0)) < 1e-9
            adf.observe(v)
            exact.observe(v)


def test_adf_first_step_is_exact():
    # Before any observation there is no drift for the projection to lose:
    # the first next-value law equals brute-force enumeration exactly, up to
    # the deliberate 1e-9 occupancy hedge on copy classes (the wall guard).
    values = [0, 0, 1, 1, 2, 2]
    walks = brute_force_value_conditionals(values, shelves=1)
    exact0 = walks[0][1][0]
    adf = AssumedDensityShelfPosterior(1, values)
    got = adf.next_value_probs()
    for v in set(values):
        assert abs(got.get(v, 0.0) - exact0.get(v, 0.0)) < 1e-8, (v, got, exact0)


def test_adf_brute_force_bias_envelope():
    # The ADF is NOT exact with copies — mean-field marginals cannot express
    # the hard global order constraints of tiny lane counts, which is the
    # harshest possible regime for it. This gate pins the MEASURED bias
    # envelope (2026-07-19: worst one-step gap 0.52 on a 6-card 1-shelf deck,
    # where the exact law is deterministic and the ADF hedges; means 0.05-0.07)
    # so a regression that widens it gets caught. Real configurations
    # (20+ lanes, 52+ cards) live nowhere near this regime; payoff-level
    # fidelity is gated by test_adf_proposition_realizes_predicted_edge and
    # the E29 battery.
    cases = (
        ([0, 0, 1, 1], 2, 0.20, 0.07),
        ([0, 0, 1, 1, 2, 2], 1, 0.55, 0.09),
        ([0, 0, 0, 1, 1, 2], 1, 0.45, 0.05),
    )
    for values, shelves, worst_gate, mean_gate in cases:
        exact = dict(brute_force_value_conditionals(values, shelves, max_outputs=200))
        worst, total, count = 0.0, 0.0, 0
        for output, conds in exact.items():
            adf = AssumedDensityShelfPosterior(shelves, values)
            for t, v in enumerate(output):
                got = adf.next_value_probs()
                for val in set(values):
                    gap = abs(got.get(val, 0.0) - conds[t].get(val, 0.0))
                    worst = max(worst, gap)
                    total += gap
                    count += 1
                adf.observe(v)
        assert worst < worst_gate, (values, shelves, worst)
        assert total / count < mean_gate, (values, shelves, total / count)


def test_adf_occupancy_bookkeeping_is_exact():
    # The load-bearing structural claim: total occupancy equals n - t and
    # per-class occupancy equals copies - dealt, at every step of a real
    # multi-deck walk. (This is what the capped water-fill buys; without it
    # the leak measurably walls off the slot axis and crashes the law.)
    values = [v for v in range(13) for _ in range(4)]  # 4 copies x 13 classes
    model = ShelfShuffle(shelves=3)
    rng = random.Random(23000000002)
    output = [values[p] for p in model.permute(list(range(len(values))), rng)]
    adf = AssumedDensityShelfPosterior(3, values)
    n = len(values)
    dealt_by: dict = {}
    for t, v in enumerate(output):
        adf.next_value_probs()
        adf.observe(v)
        dealt_by[v] = dealt_by.get(v, 0) + 1
        total = math.fsum(adf._alive)
        assert abs(total - (n - t - 1)) < 1e-6, (t, total)
        for cls, positions in adf._class_positions.items():
            mass = math.fsum(adf._alive[i] for i in positions)
            expect = 4 - dealt_by.get(cls, 0)
            assert abs(mass - expect) < 1e-6, (t, cls, mass, expect)


def test_adf_copy_is_independent():
    # A clone must not share mutable state: advancing the original leaves
    # the clone's law identical to a freshly-walked filter's.
    values = [0, 0, 1, 1, 2, 2, 3, 3]
    model = ShelfShuffle(shelves=2)
    rng = random.Random(23000000003)
    output = [values[p] for p in model.permute(list(range(len(values))), rng)]
    adf = AssumedDensityShelfPosterior(2, values)
    for v in output[:3]:
        adf.next_value_probs()
        adf.observe(v)
    twin = adf.copy()
    before = twin.next_value_probs()
    adf.next_value_probs()
    adf.observe(output[3])
    after = twin.next_value_probs()
    fresh = AssumedDensityShelfPosterior(2, values)
    for v in output[:3]:
        fresh.next_value_probs()
        fresh.observe(v)
    ref = fresh.next_value_probs()
    for v in set(values):
        assert abs(before.get(v, 0.0) - after.get(v, 0.0)) < 1e-12
        assert abs(after.get(v, 0.0) - ref.get(v, 0.0)) < 1e-12


def test_adf_proposition_realizes_predicted_edge():
    # The E17 gate at the payoff level, through the ADF: on 2-deck shoes the
    # composition-fair proposition's realized profit must match the filter's
    # own predicted edge within CI, and the order structure must pay.
    result = multideck_proposition_experiment(
        decks=2, shelves=10, trials=24, seed=23000000004, method="adf"
    )
    assert result.bets > 0
    assert abs(result.z) < Z_GATE, (result.realized, result.predicted, result.z)
    assert result.realized > 0.0, result.realized
