"""M12b rung-1 gates: the exact shelf posterior.

The load-bearing gate is brute force: enumerate every lane assignment of a
small deck through an INDEPENDENT physical pile simulation (deques, dealt
from the bottom — the machine, not the slot arithmetic), and check the
posterior's conditional next-card law against exact enumeration at every
step of every reachable output. Then: the posterior argmax must be at least
as good a feedback guesser as DFH's conjectured-optimal strategy (paired,
same decks), it must be calibrated (its own claimed hit probabilities match
realized), and the first payoff adapter must realize its predicted edge
within CI (the E17 ramp pattern). Test seeds: 22.7e9 block.
"""

import itertools
import math
import random
from collections import Counter, deque

from ridefree.forensics import ShelfGuesser, guessing_experiment
from ridefree.posterior import (
    MultiDeckShelfPosterior,
    PosteriorGuesser,
    ShelfPosterior,
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
