"""E27 — M12b rung 1: the exact posterior, the DFH conjecture, and the first
payoff adapter.

Four arms (seeds 22.8e9 block; JSON banked next to this file):

  A. Paired guessing, m=10, n=52: exact-posterior argmax vs DFH's
     conjectured-optimal strategy on IDENTICAL decks — the delta is a
     measured verdict on the paper's conjecture (the posterior argmax IS
     the optimal feedback strategy by construction). Calibration (claimed
     hit probability vs realized) rides along.
  B. m=1 sanity: published 39/52.
  C. The composition-fair value proposition (ten-or-not), one walk banking
     per-step (posterior p, composition q, outcome), evaluated on a
     threshold grid (paired across thresholds by construction) plus depth
     curves: mean |p - q| and the log-loss advantage over the PERFECT
     COUNTER baseline. q-fair odds give any composition strategy exactly
     zero edge, so realized profit is pure order structure.
  D. The manufacturer's fix (two passes == 200 shelves, Cor 4.2): the same
     instruments — what does the value channel retain?

Usage: uv run python data/e27_posterior_gate.py [trials]
"""

import json
import math
import random
import sys
from pathlib import Path

from ridefree.cards import RAW_RANKS, SUITS, value
from ridefree.forensics import ShelfGuesser, uniform_guessing_mean
from ridefree.posterior import PosteriorGuesser, ShelfPosterior
from ridefree.shuffle import ShelfShuffle

TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
N = 52
THRESHOLDS = (0.0, 0.01, 0.02, 0.05, 0.10)
DEPTH_BIN = 4

results: dict = {"trials": TRIALS, "seeds": {}}
failures: list[str] = []


def check(name, ok, detail):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def paired_guessing(m, trials, seed):
    rng = random.Random(seed)
    stack = list(range(1, N + 1))
    model = ShelfShuffle(shelves=m)
    deltas, post_scores = [], []
    predicted_total = 0.0
    for _ in range(trials):
        deck = model.permute(stack, rng)
        scores = []
        post = PosteriorGuesser(m, stack)
        for guesser in (post, ShelfGuesser(N)):
            correct = 0
            for card in deck:
                if guesser.guess() == card:
                    correct += 1
                guesser.observe(card)
            scores.append(correct)
        deltas.append(scores[0] - scores[1])
        post_scores.append(scores[0])
        predicted_total += post.predicted
    t = trials
    mean_post = sum(post_scores) / t
    mean_delta = sum(deltas) / t
    var_delta = sum((d - mean_delta) ** 2 for d in deltas) / (t - 1)
    se_delta = math.sqrt(var_delta / t)
    var_post = sum((s - mean_post) ** 2 for s in post_scores) / (t - 1)
    cal_z = (sum(post_scores) - predicted_total) / math.sqrt(predicted_total)
    return mean_post, var_post, mean_delta, se_delta, cal_z


def proposition_walk(shelves, passes, trials, seed):
    """One walk per deck; bank the threshold grid and the depth curves."""
    eq = shelves
    for _ in range(passes - 1):
        eq = 2 * eq * shelves  # DFH Corollary 4.2
    rng = random.Random(seed)
    deck = [(rank, suit) for suit in SUITS for rank in RAW_RANKS]
    model = ShelfShuffle(shelves=shelves, passes=passes)
    bins = N // DEPTH_BIN
    grid = {
        th: {"bets": 0, "pred": 0.0, "real": 0.0, "deltas": []}
        for th in THRESHOLDS
    }
    depth_gap = [0.0] * bins  # sum |p - q| on the ten proposition
    depth_ll = [0.0] * bins  # sum log p_post(actual value) - log q_comp
    depth_steps = [0] * bins
    for _ in range(trials):
        stack = list(deck)
        rng.shuffle(stack)  # shoe k, known to the observer
        dealt = model.permute(stack, rng)
        posterior = ShelfPosterior(eq, stack)
        counts = {}
        for c in stack:
            counts[value(c)] = counts.get(value(c), 0) + 1
        remaining = N
        deck_pred = dict.fromkeys(THRESHOLDS, 0.0)
        deck_real = dict.fromkeys(THRESHOLDS, 0.0)
        for t, card in enumerate(dealt):
            probs = posterior.next_probs()
            value_probs = {}
            for c, pr in probs.items():
                v = value(c)
                value_probs[v] = value_probs.get(v, 0.0) + pr
            actual = value(card)
            b = t // DEPTH_BIN
            depth_ll[b] += math.log(value_probs[actual]) - math.log(
                counts[actual] / remaining
            )
            depth_steps[b] += 1
            tens = counts.get(10, 0)
            if 0 < tens < remaining:
                q = tens / remaining
                p = value_probs.get(10, 0.0)
                depth_gap[b] += abs(p - q)
                hit = actual == 10
                for th in THRESHOLDS:
                    if p - q > th:
                        grid[th]["bets"] += 1
                        deck_pred[th] += (p - q) / q
                        deck_real[th] += (1 - q) / q if hit else -1.0
            posterior.observe(card)
            remaining -= 1
            counts[actual] -= 1
        for th in THRESHOLDS:
            grid[th]["pred"] += deck_pred[th]
            grid[th]["real"] += deck_real[th]
            grid[th]["deltas"].append(deck_real[th] - deck_pred[th])
    for th, g in grid.items():
        d = g.pop("deltas")
        mean = sum(d) / trials
        var = sum((x - mean) ** 2 for x in d) / (trials - 1)
        g["z"] = mean * math.sqrt(trials / var) if var > 0 else 0.0
        g["edge_per_bet"] = g["real"] / g["bets"] if g["bets"] else 0.0
        g["bets_per_deck"] = g["bets"] / trials
        g["units_per_deck"] = g["real"] / trials
    return grid, depth_gap, depth_ll, depth_steps


print("== A. Exact posterior vs the DFH conjectured-optimal strategy (m=10) ==")
seed = results["seeds"]["paired_m10"] = 22_800_000_001
mean_post, var_post, mean_delta, se_delta, cal_z = paired_guessing(10, TRIALS, seed)
results["paired_m10"] = {
    "posterior_mean": mean_post,
    "posterior_var": var_post,
    "delta_mean": mean_delta,
    "delta_se": se_delta,
    "calibration_z": cal_z,
}
check(
    "posterior >= conjectured",
    mean_delta > -3 * se_delta,
    f"posterior {mean_post:.3f} (var {var_post:.2f}), delta "
    f"{mean_delta:+.4f} +- {se_delta:.4f} (z {mean_delta / se_delta:+.2f})",
)
check("posterior calibrated", abs(cal_z) < 4.5, f"claimed-vs-realized z {cal_z:+.2f}")
if abs(mean_delta) < 3 * se_delta:
    print("  [INFO] DFH conjecture verdict: VERIFIED at this precision")
else:
    print(
        f"  [INFO] DFH conjecture verdict: their strategy leaves "
        f"{mean_delta:+.4f} +- {se_delta:.4f} cards per deck on the table"
    )

print("== B. m=1 sanity ==")
seed = results["seeds"]["m1"] = 22_800_000_002
mean1, _, _, _, _ = paired_guessing(1, 800, seed)
results["m1_mean"] = mean1
check("m=1 hits 39", abs(mean1 - 39.0) <= 0.4, f"{mean1:.3f} (pub 39)")

print("== C. Composition-fair ten proposition, one pass m=10 ==")
seed = results["seeds"]["prop_one_pass"] = 22_800_000_003
grid, gap, ll, steps = proposition_walk(10, 1, TRIALS, seed)
results["prop_one_pass"] = grid
results["depth_gap_one_pass"] = [g / s for g, s in zip(gap, steps)]
results["depth_logloss_one_pass"] = [x / s for x, s in zip(ll, steps)]
for th in THRESHOLDS:
    g = grid[th]
    check(
        f"prop theta={th:.2f} realizes prediction",
        abs(g["z"]) < 4.5 and (g["real"] > 0 or g["bets"] == 0),
        f"{g['bets_per_deck']:.1f} bets/deck, edge {g['edge_per_bet']:+.4f}/bet, "
        f"{g['units_per_deck']:+.3f} u/deck (pred z {g['z']:+.2f})",
    )
total_ll = sum(ll) / TRIALS
results["logloss_bits_per_deck_one_pass"] = total_ll / math.log(2)
print(
    f"  [INFO] order info beyond the perfect counter: "
    f"{total_ll / math.log(2):.2f} bits/deck at value level; "
    f"depth |p-q| curve (per {DEPTH_BIN} cards): "
    + " ".join(f"{g / s:.3f}" for g, s in zip(gap, steps))
)

print("== D. The fix: two passes (== 200 shelves) ==")
seed = results["seeds"]["prop_two_pass"] = 22_800_000_004
d_trials = max(600, TRIALS // 10)
grid2, gap2, ll2, steps2 = proposition_walk(10, 2, d_trials, seed)
results["prop_two_pass"] = grid2
results["depth_gap_two_pass"] = [g / s for g, s in zip(gap2, steps2)]
results["logloss_bits_per_deck_two_pass"] = sum(ll2) / d_trials / math.log(2)
g = grid2[0.02]
check(
    "fix closes the value channel",
    abs(g["z"]) < 4.5,
    f"theta=0.02: {g['bets_per_deck']:.2f} bets/deck, "
    f"{g['units_per_deck']:+.4f} u/deck (one pass: "
    f"{grid[0.02]['units_per_deck']:+.3f}); "
    f"{results['logloss_bits_per_deck_two_pass']:.3f} bits/deck "
    f"(one pass {results['logloss_bits_per_deck_one_pass']:.2f})",
)
results["uniform_guessing_mean"] = uniform_guessing_mean(N)

out = Path(__file__).with_name("e27_posterior_gate.json")
out.write_text(json.dumps(results, indent=1))
print(f"\nBanked {out}")
print(f"VERDICT: {'ALL GATES PASS' if not failures else 'FAILURES: ' + ', '.join(failures)}")
