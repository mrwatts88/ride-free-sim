"""M12a gates: shuffle models + forensics vs the published Diaconis numbers.

Published references pinned here (fetched 2026-07-19, arXiv:1107.2961v2 =
Ann. Appl. Probab. 23(4) 2013 [DFH]):

- Table 1 (n=52): exact TV / separation / l-inf distances per shelf count.
- Table 2 (n=52): feedback-guessing mean/variance per shelf count under the
  conjectured-optimal strategy (10k-run Monte Carlo in the paper).
- Section 5.2: color-change test — reds on top, blacks below; uniform mean
  26 sd 3.6, ten-shelf mean 17 sd 1.83.
- Corollary 4.2: m1-shelf pass then m2-shelf pass == one 2*m1*m2-shelf pass.
- Bayer-Diaconis riffle: TV after 7 riffles of 52 cards = 0.334 (the
  "seven shuffles" number; cross-checked against the GSR literature).

Statistical gates use |z| < 4.5; test seeds come from the 22.4e9 block
(ledger in STATUS.md).
"""

import math
import random
from fractions import Fraction

from ridefree.cards import Shoe
from ridefree.forensics import (
    ShelfGuesser,
    color_change_experiment,
    eulerian_counts,
    guessing_experiment,
    riffle_class_prob,
    riffle_distances,
    riffle_rising_law,
    rising_sequence_histogram,
    rising_sequences,
    shelf_class_prob,
    shelf_distances,
    shelf_valley_law,
    uniform_guessing_mean,
    uniform_guessing_var,
    valley_class_counts,
    valley_histogram,
    valleys,
)
from ridefree.shuffle import (
    ComposedShuffle,
    RiffleShuffle,
    ShelfShuffle,
    UniformShuffle,
)

Z_GATE = 4.5


def hist_zs(hist, law, trials):
    """Per-class z-scores of an empirical histogram against an exact law,
    pooling classes with expected count < 10 into their neighbor."""
    groups = []
    pend_obs, pend_p = 0, Fraction(0)
    for cls, p in enumerate(law):
        pend_obs += hist.get(cls, 0)
        pend_p += p
        if pend_p * trials >= 10:
            groups.append((pend_obs, pend_p))
            pend_obs, pend_p = 0, Fraction(0)
    if pend_p:
        if groups:
            obs, p = groups.pop()
            groups.append((obs + pend_obs, p + pend_p))
        else:
            groups.append((pend_obs, pend_p))
    zs = []
    for obs, p in groups:
        pf = float(p)
        exp = trials * pf
        zs.append((obs - exp) / math.sqrt(trials * pf * (1 - pf)))
    return zs


# ---------------------------------------------------------------------------
# The models are deterministic permutations


def test_models_permute_deterministically():
    stack = list(range(1, 53))
    models = [
        UniformShuffle(),
        ShelfShuffle(shelves=10),
        ShelfShuffle(shelves=4, passes=2),
        RiffleShuffle(),
        RiffleShuffle(piles=2, passes=3),
        RiffleShuffle(piles=8),
        ComposedShuffle(stages=(RiffleShuffle(), ShelfShuffle(shelves=3))),
    ]
    for model in models:
        a = model.permute(stack, random.Random(22400000001))
        b = model.permute(stack, random.Random(22400000001))
        c = model.permute(stack, random.Random(22400000002))
        assert a == b
        assert a != c
        assert sorted(a) == stack
        assert stack == list(range(1, 53))  # input never mutated


def test_passes_equal_composition():
    stack = list(range(1, 53))
    riffle3 = RiffleShuffle(piles=2, passes=3)
    composed = ComposedShuffle(stages=(RiffleShuffle(),) * 3)
    assert riffle3.permute(stack, random.Random(7)) == composed.permute(
        stack, random.Random(7)
    )
    shelf2 = ShelfShuffle(shelves=10, passes=2)
    composed = ComposedShuffle(stages=(ShelfShuffle(shelves=10),) * 2)
    assert shelf2.permute(stack, random.Random(7)) == composed.permute(
        stack, random.Random(7)
    )


def test_structural_supports():
    # One shelf pass: piles are unimodal, so at most shelves-1 valleys;
    # one GSR a-shuffle: at most a rising sequences.
    stack = list(range(1, 27))
    rng = random.Random(22400000003)
    for _ in range(300):
        assert valleys(ShelfShuffle(shelves=1).permute(stack, rng)) == 0
        assert valleys(ShelfShuffle(shelves=4).permute(stack, rng)) <= 3
        assert rising_sequences(RiffleShuffle().permute(stack, rng)) <= 2
        assert (
            rising_sequences(RiffleShuffle(piles=2, passes=3).permute(stack, rng))
            <= 8
        )


# ---------------------------------------------------------------------------
# The Shoe composes shuffle models; the default path is untouched


def drain(shoe: Shoe) -> list[int]:
    return [shoe.deal() for _ in range(shoe.cards_remaining)]


def test_shoe_default_is_uniform_shuffle_bit_identical():
    legacy = Shoe(6, 0.75, 22400000004)
    explicit = Shoe(6, 0.75, 22400000004, shuffle=UniformShuffle())
    assert legacy.raw_order() == explicit.raw_order()
    assert drain(legacy) == drain(explicit)


def test_shoe_with_shelf_shuffle_deterministic():
    a = Shoe(6, 0.75, 22400000005, shuffle=ShelfShuffle(shelves=10))
    b = Shoe(6, 0.75, 22400000005, shuffle=ShelfShuffle(shelves=10))
    assert a.raw_order() == b.raw_order()
    assert sorted(a.raw_order()) == sorted(Shoe(6, 0.75, 1).raw_order())
    assert drain(a) == drain(b)


def test_shoe_stack_feeds_successor_shoe():
    first = Shoe(1, 1.0, 22400000006)
    order = first.raw_order()
    # No shuffle: the stack is dealt verbatim, whatever the seed.
    replay = Shoe(1, 1.0, 999, stack=order)
    assert replay.raw_order() == order
    # A shelf pass over the previous shoe's order is deterministic under seed.
    nxt = Shoe(1, 1.0, 22400000007, shuffle=ShelfShuffle(shelves=10), stack=order)
    again = Shoe(1, 1.0, 22400000007, shuffle=ShelfShuffle(shelves=10), stack=order)
    assert nxt.raw_order() == again.raw_order()
    assert sorted(nxt.raw_order()) == sorted(order)
    assert nxt.raw_order() != order


def test_shoe_rejects_wrong_stack():
    order = Shoe(1, 1.0, 3).raw_order()
    try:
        Shoe(2, 1.0, 4, stack=order)  # one deck of cards for a two-deck shoe
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for a mismatched stack")


# ---------------------------------------------------------------------------
# Exact class laws


def test_valley_and_eulerian_counts():
    assert valley_class_counts(3) == (4, 2)
    assert valley_class_counts(4) == (8, 16)
    assert sum(valley_class_counts(8)) == math.factorial(8)
    assert sum(valley_class_counts(52)) == math.factorial(52)
    assert eulerian_counts(3) == (1, 4, 1)
    assert sum(eulerian_counts(8)) == math.factorial(8)
    assert valleys([5, 1, 3, 6, 7, 2, 4]) == 2  # DFH's example w = 5136724
    assert rising_sequences([3, 1, 4, 2]) == 2
    assert rising_sequences(list(range(1, 11))) == 1
    assert rising_sequences(list(range(10, 0, -1))) == 10


def test_exact_laws_total_probability_one():
    for n, m in ((8, 1), (13, 4), (52, 10), (52, 200)):
        counts = valley_class_counts(n)
        total = sum(
            counts[v] * shelf_class_prob(n, m, v) for v in range(len(counts))
        )
        assert total == 1
    for n, a in ((10, 3), (52, 2), (52, 128)):
        counts = eulerian_counts(n)
        total = sum(
            counts[d] * riffle_class_prob(n, a, d + 1) for d in range(len(counts))
        )
        assert total == 1
    # m = 1 shelf: uniform over the 2^(n-1) unimodal permutations (DFH ex.)
    assert shelf_class_prob(8, 1, 0) == Fraction(1, 2**7)
    assert shelf_class_prob(8, 1, 1) == 0


def test_shelf_distances_reproduce_dfh_table1():
    published = {  # m: (TV, sep) — printed to 3 decimals in the paper
        15: (0.943, 1.000),
        20: (0.720, 1.000),
        25: (0.544, 1.000),
        30: (0.391, 1.000),
        35: (0.299, 0.996),
        50: (0.159, 0.910),
        100: (0.041, 0.431),
        150: (0.018, 0.219),
        200: (0.010, 0.130),
        250: (0.007, 0.085),
        300: (0.005, 0.060),
    }
    for m, (tv, sep) in published.items():
        d = shelf_distances(52, m)
        assert round(d.tv, 3) == tv, (m, d.tv)
        assert round(d.sep, 3) == sep, (m, d.sep)
    assert shelf_distances(52, 10).tv > 0.9995  # printed as 1
    assert shelf_distances(52, 25).sep == 1.0  # 25-valley class unreachable
    published_linf = {  # printed precision varies; tolerance = half a digit
        25: (45118, 1),
        30: (3961, 1),
        35: (716, 1),
        50: (39, 0.5),
        100: (1.9, 0.05),
        150: (0.615, 0.0005),
        200: (0.313, 0.0005),
        250: (0.192, 0.0005),
        300: (0.130, 0.0005),
    }
    for m, (linf, tol) in published_linf.items():
        d = shelf_distances(52, m)
        assert abs(d.linf - linf) <= tol, (m, d.linf)


def test_riffle_distances_reproduce_seven_shuffles():
    assert round(riffle_distances(52, 2**7).tv, 3) == 0.334
    tvs = [riffle_distances(52, 2**k).tv for k in range(1, 11)]
    assert all(a >= b for a, b in zip(tvs, tvs[1:]))
    assert tvs[3] > 0.99  # 4 riffles: still nearly maximally far


# ---------------------------------------------------------------------------
# The physical simulation matches the exact laws


def test_shelf_sampler_matches_theorem_31():
    trials = 20000
    hist = valley_histogram(ShelfShuffle(shelves=10), 52, trials, 22400000008)
    zs = hist_zs(hist, shelf_valley_law(52, 10), trials)
    assert max(abs(z) for z in zs) < Z_GATE, zs


def test_two_passes_equal_200_shelves():
    # Corollary 4.2: shelf(10) twice IS shelf(200) once — gate the two-pass
    # sampler against the exact 200-shelf law.
    trials = 15000
    hist = valley_histogram(
        ShelfShuffle(shelves=10, passes=2), 52, trials, 22400000009
    )
    zs = hist_zs(hist, shelf_valley_law(52, 200), trials)
    assert max(abs(z) for z in zs) < Z_GATE, zs


def test_riffle_sampler_matches_bayer_diaconis():
    # Three GSR passes compose to one 8-shuffle (BD); gate the sampler
    # against the exact 8-shuffle rising-sequence law.
    trials = 15000
    hist = rising_sequence_histogram(
        RiffleShuffle(piles=2, passes=3), 52, trials, 22400000010
    )
    law = [Fraction(0)] + list(riffle_rising_law(52, 8))  # class r starts at 1
    zs = hist_zs(hist, law, trials)
    assert max(abs(z) for z in zs) < Z_GATE, zs


# ---------------------------------------------------------------------------
# Guessing with feedback (DFH Section 5.1, Table 2)


def test_shelf_guesser_mechanics():
    guesser = ShelfGuesser(6)
    guesses = []
    for card in (4, 5, 6, 3, 2, 1):
        guesses.append(guesser.guess())
        guesser.observe(card)
    # up from the start, turning down at the observed 6 -> 3 descent; the
    # fallback at the top of the deck guesses the largest remaining card.
    assert guesses == [1, 5, 6, 3, 2, 1]


def test_uniform_guessing_is_harmonic():
    assert abs(uniform_guessing_mean(52) - 4.538) < 5e-4
    stats = guessing_experiment(UniformShuffle(), 52, 20000, 22400000011)
    assert abs(stats.mean - uniform_guessing_mean(52)) < Z_GATE * stats.se_mean
    assert abs(stats.var - uniform_guessing_var(52)) < 0.3


def test_shelf_guessing_reproduces_dfh_table2():
    stats = guessing_experiment(ShelfShuffle(shelves=10), 52, 20000, 22400000012)
    assert abs(stats.mean - 9.3) <= 0.1, stats  # published: 9.3 (10k runs)
    assert abs(stats.var - 4.7) <= 0.5, stats
    stats = guessing_experiment(ShelfShuffle(shelves=1), 52, 8000, 22400000013)
    assert abs(stats.mean - 39.0) <= 0.3, stats  # published: 39
    assert abs(stats.var - 3.2) <= 0.5, stats


def test_two_pass_guessing_near_chance():
    stats = guessing_experiment(
        ShelfShuffle(shelves=10, passes=2), 52, 20000, 22400000014
    )
    assert stats.mean < 5.0, stats  # the manufacturer's fix: ~chance level
    assert stats.mean > uniform_guessing_mean(52) - Z_GATE * stats.se_mean


# ---------------------------------------------------------------------------
# Color changes (DFH Section 5.2)


def test_color_changes_reproduce_dfh():
    stats = color_change_experiment(UniformShuffle(), 52, 20000, 22400000015)
    assert abs(stats.mean - 26.0) < Z_GATE * stats.se_mean  # exactly 26 uniform
    assert abs(stats.sd - 3.6) < 0.15
    stats = color_change_experiment(ShelfShuffle(shelves=10), 52, 20000, 22400000016)
    assert abs(stats.mean - 17.0) <= 0.6, stats  # published: 17 +- 1.83
    assert abs(stats.sd - 1.83) <= 0.12, stats
    stats = color_change_experiment(
        ShelfShuffle(shelves=10, passes=2), 52, 20000, 22400000017
    )
    assert stats.mean > 25.0, stats  # two passes: most of the way to uniform
