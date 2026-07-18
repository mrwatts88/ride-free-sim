"""Window-conditional deviation value, efficiently.

Same paired differential design as experiments.run_deviation_value (base
OptimalStrategy timeline is canonical), but the expensive live-composition
replay runs ONLY when the pre-deal RF signal clears the wong-in threshold.
Out-of-window rounds cost one cheap base round, so window rounds accumulate
~7x faster per wall-clock second than the all-rounds design.

Seeding note: this script deliberately keeps the pre-fix `SEED + shuffles` shoe
derivation so the banked data/e8_wdev_shard*.json (seeds 1.9e9-2.5e9) reproduce
bit-for-bit. That pattern is only safe with base-seed spacing >= 1e8 (see
docs/DEEP_DIVE_AUDIT.md); new experiments should use cards.shoe_seeds() instead.
"""
import json
import sys

from ridefree.cards import Shoe
from ridefree.counting import CompositionTracker
from ridefree.engine import play_round
from ridefree.player_ev import CompositionStrategy, OptimalStrategy
from ridefree.rules import RIDE_FREE
from ridefree.simulator import _needs_reshuffle

SEED = int(sys.argv[1])
ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
THRESHOLD = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0125
OUT = sys.argv[4] if len(sys.argv) > 4 else None

rules = RIDE_FREE
base = OptimalStrategy()
dev = CompositionStrategy()
shoe = Shoe(rules.decks, rules.penetration, SEED)
tracker = CompositionTracker(rules.decks)
shuffles = 0
rounds_since = 0
win_rounds = 0
win_changed = 0
diff_sum = 0.0
diff_sq = 0.0

for i in range(ROUNDS):
    if _needs_reshuffle(rules, shoe, rounds_since):
        shuffles += 1
        shoe = Shoe(rules.decks, rules.penetration, SEED + shuffles)
        tracker.new_shoe()
        rounds_since = 0
    in_window = tracker.rf_ev_shift() >= THRESHOLD
    if not in_window:
        result = play_round(rules, shoe, base, bet=1.0)
        rounds_since += 1
        tracker.observe_round(result)
        continue
    start = shoe.snapshot()
    r_base = play_round(rules, shoe, base, bet=1.0)
    end = shoe.snapshot()
    shoe.restore(start)
    dev.set_composition(rules, tracker.counts)
    r_dev = play_round(rules, shoe, dev, bet=1.0)
    shoe.restore(end)  # canonical timeline: the fixed strategy's cards
    tracker.observe_round(r_base)
    rounds_since += 1
    d = r_dev.profit - r_base.profit
    win_rounds += 1
    diff_sum += d
    diff_sq += d * d
    if d != 0.0:
        win_changed += 1
    if (i + 1) % 250_000 == 0:
        m = diff_sum / win_rounds if win_rounds else 0.0
        print(f"{i + 1} rounds, {win_rounds} in window, value {100 * m:+.4f}%", flush=True)

mean = diff_sum / win_rounds if win_rounds else 0.0
var = max(diff_sq / win_rounds - mean * mean, 0.0) if win_rounds else 0.0
se = (var / win_rounds) ** 0.5 if win_rounds else 0.0
print(
    f"FINAL seed={SEED} rounds={ROUNDS} thr={THRESHOLD} window_rounds={win_rounds} "
    f"({100 * win_rounds / ROUNDS:.2f}%) deviation_value={100 * mean:+.4f}% "
    f"± {100 * se:.4f}% profit_changed={100 * win_changed / max(win_rounds, 1):.2f}%",
    flush=True,
)
if OUT:
    with open(OUT, "w") as f:
        json.dump(
            {"seed": SEED, "rounds": ROUNDS, "threshold": THRESHOLD,
             "window_rounds": win_rounds, "diff_sum": diff_sum, "diff_sq": diff_sq,
             "changed": win_changed},
            f,
        )
