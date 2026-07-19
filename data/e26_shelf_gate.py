"""E26 — the M12a gate battery: the synthetic shuffle lab vs published truth.

Reproduces, at precision, every practical number in Diaconis/Fulman/Holmes,
"Analysis of casino shelf shuffling machines" (Ann. Appl. Probab. 23(4) 2013,
arXiv:1107.2961) [DFH], plus the Bayer-Diaconis riffle pin:

  A. exact arithmetic — DFH Table 1 distances (no sampling error) and the
     BD "seven shuffles" TV table (published pin: 0.334 at k=7, n=52);
  B. guessing-with-feedback sweep — DFH Table 2 (conjectured-optimal
     strategy) across m = 1, 2, 4, 10, 20, 64 shelves;
  C. the manufacturer's fix — two 10-shelf passes vs one 200-shelf pass
     (Corollary 4.2 says they are THE SAME shuffle) and the residual
     guessing advantage of the fix vs the H_52 chance line;
  D. color changes — uniform 26 +- 3.6 vs one ten-shelf pass 17 +- 1.83;
  E. sampler-vs-law histograms — valley classes (Theorem 3.1) and rising
     sequences (BD 8-shuffle via three composed GSR passes);
  F. top-card retention — P(original top card stays on top) >= 1/(2m).

Usage: uv run python data/e26_shelf_gate.py [trials]
Writes data/e26_shelf_gate.json. Seeds: 22.5e9 block (guessing),
22.6e9 block (color/histograms) — ledger in STATUS.md.
"""

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

from ridefree.forensics import (
    ShelfGuesser,
    color_change_experiment,
    guessing_experiment,
    riffle_distances,
    riffle_rising_law,
    rising_sequence_histogram,
    shelf_distances,
    shelf_valley_law,
    uniform_guessing_mean,
    uniform_guessing_var,
    valley_histogram,
)
from ridefree.shuffle import RiffleShuffle, ShelfShuffle, UniformShuffle

TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
HIST_TRIALS = 2 * TRIALS
N = 52

# Published pins (fetched 2026-07-19 from arXiv:1107.2961v2).
TABLE1 = {  # m: (tv, sep, linf or None where the paper prints infinity)
    10: (1.000, 1.000, None),
    15: (0.943, 1.000, None),
    20: (0.720, 1.000, None),
    25: (0.544, 1.000, 45118),
    30: (0.391, 1.000, 3961),
    35: (0.299, 0.996, 716),
    50: (0.159, 0.910, 39),
    100: (0.041, 0.431, 1.9),
    150: (0.018, 0.219, 0.615),
    200: (0.010, 0.130, 0.313),
    250: (0.007, 0.085, 0.192),
    300: (0.005, 0.060, 0.130),
}
TABLE2 = {  # m: (mean, var, mean rounding half-width) — their 10k-run MC
    1: (39.0, 3.2, 0.5),
    2: (27.0, 5.6, 0.5),
    4: (17.6, 6.0, 0.05),
    10: (9.3, 4.7, 0.05),
    20: (6.2, 3.8, 0.05),
    64: (4.7, 3.1, 0.05),
}
COLOR = {"uniform": (26.0, 3.6), "shelf10": (17.0, 1.83)}
BD_SEVEN = 0.334  # TV after 7 riffles of 52 cards (Bayer-Diaconis 1992)
THEIR_TRIALS = 10_000

results: dict = {"trials": TRIALS, "hist_trials": HIST_TRIALS, "seeds": {}}
failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def hist_gate(name, hist, law, trials):
    """Max |z| over classes, pooling expected counts < 10 into a neighbor."""
    groups, pend_obs, pend_p = [], 0, Fraction(0)
    for cls, p in enumerate(law):
        pend_obs += hist.get(cls, 0)
        pend_p += p
        if pend_p * trials >= 10:
            groups.append((pend_obs, pend_p))
            pend_obs, pend_p = 0, Fraction(0)
    if pend_p and groups:
        obs, p = groups.pop()
        groups.append((obs + pend_obs, p + pend_p))
    zs = [
        (obs - trials * float(p)) / math.sqrt(trials * float(p) * (1 - float(p)))
        for obs, p in groups
    ]
    worst = max(abs(z) for z in zs)
    check(name, worst < 4.5, f"{len(zs)} pooled classes, worst |z| = {worst:.2f}")
    return worst


print("== A. Exact arithmetic vs DFH Table 1 and Bayer-Diaconis ==")
table1_out = {}
for m, (tv, sep, linf) in TABLE1.items():
    d = shelf_distances(N, m)
    table1_out[m] = {"tv": d.tv, "sep": d.sep, "linf": d.linf}
    ok = (round(d.tv, 3) == tv or (m == 10 and d.tv > 0.9995)) and (
        round(d.sep, 3) == sep
    )
    if linf is not None:
        ok = ok and abs(d.linf - linf) <= (1 if linf > 100 else 0.05 * linf + 5e-4)
    check(
        f"Table1 m={m}",
        ok,
        f"tv {d.tv:.4f} sep {d.sep:.4f} linf {d.linf:.4g} "
        f"(pub {tv} {sep} {linf if linf is not None else 'inf'})",
    )
results["table1"] = table1_out

riffle_tv = {k: riffle_distances(N, 2**k).tv for k in range(1, 11)}
results["riffle_tv"] = riffle_tv
check(
    "BD seven shuffles",
    round(riffle_tv[7], 3) == BD_SEVEN,
    f"tv(7) = {riffle_tv[7]:.4f} (pub {BD_SEVEN}); "
    f"k=1..10: {' '.join(f'{riffle_tv[k]:.3f}' for k in range(1, 11))}",
)

print("== B. Guessing with feedback vs DFH Table 2 ==")
h52 = uniform_guessing_mean(N)
table2_out = {}
for i, (m, (pub_mean, pub_var, half)) in enumerate(TABLE2.items()):
    seed = 22_500_000_001 + i
    results["seeds"][f"guess_m{m}"] = seed
    stats = guessing_experiment(ShelfShuffle(shelves=m), N, TRIALS, seed)
    se = math.sqrt(stats.se_mean**2 + pub_var / THEIR_TRIALS)
    z = (stats.mean - pub_mean) / se
    table2_out[m] = {"mean": stats.mean, "var": stats.var, "z_mean": z}
    var_se = math.sqrt(2 / (THEIR_TRIALS - 1)) * pub_var
    check(
        f"Table2 m={m}",
        abs(stats.mean - pub_mean) <= 2 * se + half
        and abs(stats.var - pub_var) <= 2 * var_se + 0.05,
        f"mean {stats.mean:.3f} var {stats.var:.2f} "
        f"(pub {pub_mean} / {pub_var}), z_mean {z:+.2f} incl. their MC error",
    )
results["table2"] = table2_out

seed = 22_500_000_101
results["seeds"]["guess_uniform"] = seed
stats = guessing_experiment(UniformShuffle(), N, TRIALS, seed)
results["guess_uniform"] = {"mean": stats.mean, "var": stats.var}
check(
    "uniform baseline",
    abs(stats.mean - h52) < 4.5 * stats.se_mean,
    f"mean {stats.mean:.3f} vs H_52 = {h52:.3f} "
    f"(z {(stats.mean - h52) / stats.se_mean:+.2f}), var {stats.var:.2f} "
    f"vs {uniform_guessing_var(N):.2f}",
)

print("== C. The fix: two 10-shelf passes == one 200-shelf pass (Cor 4.2) ==")
seed = 22_500_000_102
results["seeds"]["guess_two_pass"] = seed
two = guessing_experiment(ShelfShuffle(shelves=10, passes=2), N, TRIALS, seed)
seed = 22_500_000_103
results["seeds"]["guess_shelf200"] = seed
s200 = guessing_experiment(ShelfShuffle(shelves=200), N, TRIALS, seed)
z_eq = (two.mean - s200.mean) / math.sqrt(two.se_mean**2 + s200.se_mean**2)
results["guess_two_pass"] = {"mean": two.mean, "var": two.var}
results["guess_shelf200"] = {"mean": s200.mean, "var": s200.var}
check(
    "two-pass == 200-shelf (guessing)",
    abs(z_eq) < 4.5,
    f"two-pass {two.mean:.3f} vs 200-shelf {s200.mean:.3f}, z {z_eq:+.2f}",
)
residual = two.mean - h52
results["fix_residual_guessing"] = residual
print(
    f"  [INFO] residual of the fix: {residual:+.3f} cards above chance "
    f"(+-{two.se_mean:.3f}) — the instrument resolves what the fix still leaks"
)

print("== D. Color changes (DFH Section 5.2) ==")
color_out = {}
for i, (name, model) in enumerate(
    (
        ("uniform", UniformShuffle()),
        ("shelf10", ShelfShuffle(shelves=10)),
        ("two_pass", ShelfShuffle(shelves=10, passes=2)),
        ("shelf200", ShelfShuffle(shelves=200)),
    )
):
    seed = 22_600_000_001 + i
    results["seeds"][f"color_{name}"] = seed
    stats = color_change_experiment(model, N, TRIALS, seed)
    color_out[name] = {"mean": stats.mean, "sd": stats.sd}
    if name in COLOR:
        pub_mean, pub_sd = COLOR[name]
        half = 0.5 if name == "shelf10" else 0.05
        sd_se = math.sqrt(pub_sd**2 / (2 * THEIR_TRIALS) + stats.sd**2 / (2 * TRIALS))
        check(
            f"color {name}",
            abs(stats.mean - pub_mean)
            <= 2 * math.sqrt(stats.se_mean**2 + pub_sd**2 / THEIR_TRIALS) + half
            and abs(stats.sd - pub_sd) <= 2 * sd_se + 0.005,
            f"{stats.mean:.3f} +- {stats.sd:.3f} (pub {pub_mean} +- {pub_sd})",
        )
    else:
        print(f"  [INFO] color {name}: {stats.mean:.3f} +- {stats.sd:.3f}")
z_eq = (
    color_out["two_pass"]["mean"] - color_out["shelf200"]["mean"]
) / math.sqrt(
    color_out["two_pass"]["sd"] ** 2 / TRIALS
    + color_out["shelf200"]["sd"] ** 2 / TRIALS
)
check(
    "two-pass == 200-shelf (color)",
    abs(z_eq) < 4.5,
    f"{color_out['two_pass']['mean']:.3f} vs "
    f"{color_out['shelf200']['mean']:.3f}, z {z_eq:+.2f}",
)
results["color"] = color_out

print("== E. Sampler vs exact class laws ==")
seed = 22_600_000_011
results["seeds"]["valley_one_pass"] = seed
hist = valley_histogram(ShelfShuffle(shelves=10), N, HIST_TRIALS, seed)
results["valley_hist_one_pass"] = dict(sorted(hist.items()))
results["valley_z_one_pass"] = hist_gate(
    "valleys vs Theorem 3.1 (m=10)", hist, shelf_valley_law(N, 10), HIST_TRIALS
)
seed = 22_600_000_012
results["seeds"]["valley_two_pass"] = seed
hist = valley_histogram(ShelfShuffle(shelves=10, passes=2), N, HIST_TRIALS, seed)
results["valley_hist_two_pass"] = dict(sorted(hist.items()))
results["valley_z_two_pass"] = hist_gate(
    "two-pass valleys vs exact 200-shelf law", hist, shelf_valley_law(N, 200), HIST_TRIALS
)
seed = 22_600_000_013
results["seeds"]["rising"] = seed
hist = rising_sequence_histogram(RiffleShuffle(piles=2, passes=3), N, TRIALS, seed)
results["rising_hist"] = dict(sorted(hist.items()))
law = [Fraction(0)] + list(riffle_rising_law(N, 8))
results["rising_z"] = hist_gate("rising sequences vs BD 8-shuffle law", hist, law, TRIALS)

print("== F. Top-card retention ==")
import random as _random

seed = 22_600_000_014
results["seeds"]["top_card"] = seed
rng = _random.Random(seed)
stack = list(range(1, N + 1))
model = ShelfShuffle(shelves=10)
kept = sum(1 for _ in range(TRIALS) if model.permute(stack, rng)[0] == 1)
freq = kept / TRIALS
results["top_card_retention"] = freq
check(
    "top card stays top >= 1/(2m)",
    freq >= 1 / 20 - 4.5 * math.sqrt(0.05 * 0.95 / TRIALS),
    f"{freq:.4f} (bound 1/20 = 0.05, uniform 1/52 = {1 / 52:.4f})",
)

out = Path(__file__).with_name("e26_shelf_gate.json")
out.write_text(json.dumps(results, indent=1))
print(f"\nBanked {out}")
print(f"VERDICT: {'ALL GATES PASS' if not failures else 'FAILURES: ' + ', '.join(failures)}")
