"""Quantify the insurance overlay for Ride Free wong-in play.

Insurance is not modeled in the engine. This measures, with perfect composition
tracking, the EV a player gains by taking insurance exactly when it is +EV
(3 * P(hole is ten) > 1), overall and conditional on the RF wong-in window.

Knowledge at insurance time: pre-round composition minus the three cards the
player can see (own two cards + dealer up-card). The hole card is part of the
unseen pool of size N-3. Insurance stakes half the bet and pays 2:1, so the
per-round overlay is 0.5 * max(0, 3*p_ten - 1) when the dealer shows an ace.

Seeding note: this script deliberately keeps the pre-fix `SEED + shuffles` shoe
derivation so the banked data/e9_insurance.json (seed 1300000001) reproduces
bit-for-bit. That pattern is only safe with base-seed spacing >= 1e8 (see
docs/DEEP_DIVE_AUDIT.md); new experiments should use cards.shoe_seeds() instead.
"""
import json
import sys

from ridefree.cards import ACE, TEN, Shoe
from ridefree.counting import CompositionTracker
from ridefree.engine import play_round
from ridefree.player_ev import OptimalStrategy
from ridefree.rules import RIDE_FREE
from ridefree.simulator import _needs_reshuffle

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 1300000001
ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
OUT = sys.argv[3] if len(sys.argv) > 3 else None

rules = RIDE_FREE
strat = OptimalStrategy()
shoe = Shoe(rules.decks, rules.penetration, SEED)
tracker = CompositionTracker(rules.decks)
shuffles = 0
rounds_since = 0

THRESHOLDS = {"all": None, "win75": 0.0075, "win125": 0.0125}
acc = {
    k: {"rounds": 0, "ace_up": 0, "ins_taken": 0, "ins_ev": 0.0, "ins_ev_sq": 0.0}
    for k in THRESHOLDS
}

for i in range(ROUNDS):
    if _needs_reshuffle(rules, shoe, rounds_since):
        shuffles += 1
        shoe = Shoe(rules.decks, rules.penetration, SEED + shuffles)
        tracker.new_shoe()
        rounds_since = 0
    rf = tracker.rf_ev_shift()
    pos0 = shoe.snapshot()
    result = play_round(rules, shoe, strat, bet=1.0)
    rounds_since += 1
    # Deal order in play_round: player1, up, player2, hole.
    order = shoe._cards[pos0 : pos0 + 4]
    up = order[1]
    ins = 0.0
    taken = 0
    if up == ACE:
        n = tracker.cards_remaining - 3
        tens = tracker.counts[TEN] - (order[0] == TEN) - (order[2] == TEN)
        p_ten = tens / n
        edge = 3.0 * p_ten - 1.0
        if edge > 0:
            ins = 0.5 * edge
            taken = 1
    for key, thr in THRESHOLDS.items():
        if thr is not None and rf < thr:
            continue
        a = acc[key]
        a["rounds"] += 1
        if up == ACE:
            a["ace_up"] += 1
        a["ins_taken"] += taken
        a["ins_ev"] += ins
        a["ins_ev_sq"] += ins * ins
    tracker.observe_round(result)
    if (i + 1) % 250_000 == 0:
        print(f"{i + 1} rounds...", flush=True)

report = {}
for key, a in acc.items():
    r = a["rounds"]
    mean = a["ins_ev"] / r if r else 0.0
    var = max(a["ins_ev_sq"] / r - mean * mean, 0.0) if r else 0.0
    se = (var / r) ** 0.5 if r else 0.0
    report[key] = {
        "rounds": r,
        "frac_of_all": r / ROUNDS,
        "ace_up_rate": a["ace_up"] / r if r else 0.0,
        "ins_take_rate": a["ins_taken"] / r if r else 0.0,
        "overlay_ev_per_round": mean,
        "overlay_se": se,
    }
    print(
        f"{key:7s} rounds={r:>9,d} ace_up={report[key]['ace_up_rate']:.4f} "
        f"take_rate={report[key]['ins_take_rate']:.4f} "
        f"overlay={mean * 100:+.4f}% ± {se * 100:.4f}%",
        flush=True,
    )
if OUT:
    with open(OUT, "w") as f:
        json.dump({"seed": SEED, "rounds": ROUNDS, "report": report}, f, indent=1)
    print(f"written {OUT}", flush=True)
