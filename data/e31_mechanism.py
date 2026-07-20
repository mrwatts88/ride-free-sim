"""E31 mechanism curve: the compounding-shrink of a JOINT (coup) claim, shown
directly on frozen filter states -- no shoe-level realized noise.

The contamination floor `mix` blends `next_value_probs()` toward composition at
EVERY card (posterior.py). Composition is exactly what the perfect counter sees,
so a coup claim priced at mix=1 equals the counter's EV, and at mix=0 it is the
pure ordered-model read. The question is the SHAPE in between: because the floor
is applied per card and a coup samples 4-6 cards, a joint event like Dragon-7 /
Panda-8 (a 3-card total) shrinks toward composition much faster than mix itself
-- so the calibrated-for-marginals mix=0.40 leaves the joint claim already
~crushed. This freezes several (shoe, depth) states and prices D7/P8 across the
mix axis at high M (CRN uniforms across mixes), tabling claim(mix) against the
counter EV (the mix=1 asymptote) and the pure-model read (mix=0).

Run: PYTHONPATH=src uv run --python pypy@3.11 --no-project data/e31_mechanism.py
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ridefree.baccarat import EZ_BACCARAT_8D, fast_outcomes
from ridefree.cards import RAW_RANKS, SUITS
from ridefree.cards import value as bj_value
from ridefree.coup import bet_evs, sampled_outcome_probs
from ridefree.posterior import AssumedDensityShelfPosterior
from ridefree.shuffle import ShelfShuffle

RULES = EZ_BACCARAT_8D
DECKS = RULES.decks
SHELVES = 10
MIXES = [0.0, 0.05, 0.10, 0.20, 0.40, 0.70, 1.0]
DEPTHS = [40, 160, 300]        # cards observed before the frozen coup
SHOE_SEEDS = [23_310_000_001 + k for k in range(4)]
M = 1500

classes = [(rank, suit) for suit in SUITS for rank in RAW_RANKS]
class_bacc = {c: bj_value(c) % 10 for c in classes}
model = ShelfShuffle(shelves=SHELVES, passes=1)


def frozen_state(shoe_seed, depth):
    """Walk one shelf-shuffled 8-deck shoe `depth` observed cards deep; return
    (filter, remaining-composition) at that frozen point."""
    rng = random.Random(shoe_seed)
    stack = list(classes) * DECKS
    rng.shuffle(stack)
    n = len(stack)
    dealt = [stack[p] for p in model.permute(list(range(n)), rng)]
    filt = AssumedDensityShelfPosterior(SHELVES, stack, mix=0.0)
    vcount = {v: 0 for v in range(10)}
    for c in stack:
        vcount[class_bacc[c]] += 1
    for c in dealt[:depth]:
        filt.observe(c)
        vcount[class_bacc[c]] -= 1
    return filt, vcount


rows = []
for shoe_seed in SHOE_SEEDS:
    for depth in DEPTHS:
        filt, vcount = frozen_state(shoe_seed, depth)
        comp = {v: k for v, k in vcount.items() if k > 0}
        exact = fast_outcomes(comp)
        counter = bet_evs(exact, RULES)
        claims = {}
        for mix in MIXES:
            filt.mix = mix
            rng = random.Random(0xC0FFEE ^ shoe_seed ^ depth)  # CRN across mixes
            evs = bet_evs(
                sampled_outcome_probs(RULES, filt, class_bacc, vcount, exact,
                                      rng, M), RULES)
            claims[mix] = {"dragon7": evs["dragon7"], "panda8": evs["panda8"]}
        rows.append({"shoe_seed": shoe_seed, "depth": depth,
                     "counter": {"dragon7": counter["dragon7"],
                                 "panda8": counter["panda8"]},
                     "claims": claims})

out = {"mixes": MIXES, "depths": DEPTHS, "M": M, "rows": rows}
path = Path(__file__).with_name("e31_mechanism.json")
path.write_text(json.dumps(out, indent=1))

# --- table: claim(mix) for D7 and P8, per (depth) averaged over shoes ---
print(f"claim(mix) for Dragon7 / Panda8, M={M}, averaged over {len(SHOE_SEEDS)} shoes")
print("(counter = composition EV = the mix=1 asymptote; mix=0 = pure ordered model)\n")
for bet in ("dragon7", "panda8"):
    print(f"== {bet} EV/unit ==")
    header = "depth  " + "".join(f"  mix{m:<5}" for m in MIXES) + "   counter"
    print(header)
    for depth in DEPTHS:
        drows = [r for r in rows if r["depth"] == depth]
        cells = []
        for m in MIXES:
            avg = sum(r["claims"][m][bet] for r in drows) / len(drows)
            cells.append(f"{avg:+7.1%}")
        cavg = sum(r["counter"][bet] for r in drows) / len(drows)
        print(f"{depth:>5}  " + "".join(f" {c}" for c in cells) + f"  {cavg:+7.1%}")
    print()
print(f"banked {path}")
