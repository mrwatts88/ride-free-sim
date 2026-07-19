"""E25c — walk TEXTURE: how often does each walk line actually fire?

The E24/E25 walk rows price "% of rounds not played" from stationary bins,
but Matt's tolerance ("walk at most 10% of the time") is about the hassle
EVENTS: how often you're up and re-tabling. This measures, per threshold,
the live sequential process: play a shoe until the pre-round hi-lo TC bin
drops to the line (bin <= t, i.e. tc < t + 0.5 — the bins convention),
then walk to a fresh table (instant re-seat, fresh shoe). Reports walks/h,
% of shoes abandoned, and median walk depth.

Semantics note (honest): under instant re-seat you PLAY ~every observed
round — walked rounds are replaced by fresh-shoe rounds, which is a
slightly different stream than the bins' "stand around during bad counts"
model. E18b measured the two within ~$1/h of each other at crouch15 scale;
the OOS certification of whatever card Matt picks runs the live semantics
end to end.

Run:  uv run python data/e25c_walks.py   (seed 22.4e9, 1M rounds/threshold)
"""

import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ridefree.cards import Shoe, shoe_seeds  # noqa: E402
from ridefree.counting import CompositionTracker  # noqa: E402
from ridefree.engine import play_round  # noqa: E402
from ridefree.player_ev import OptimalStrategy  # noqa: E402
from ridefree.rules import STANDARD_6D_H17  # noqa: E402
from ridefree.simulator import _needs_reshuffle  # noqa: E402

SEED = 22_400_000_001  # E25c consumes the first seed of the 22.4e9 block
ROUNDS = 1_000_000

rules = STANDARD_6D_H17
print(f"E25c — walk texture, {rules.decks}d pen {rules.penetration:g}, "
      f"{ROUNDS:,} played rounds per threshold, seed {SEED}")
print(f"{'line':>8s} {'walks/1k rounds':>16s} {'walks/h@200':>12s} "
      f"{'walks/h@140':>12s} {'shoes abandoned':>16s} {'median walk round':>18s}")

for t in (-1, -2, -3, -4):
    strategy = OptimalStrategy()
    seeds = shoe_seeds(SEED)  # same stream every threshold: paired comparison
    tracker = CompositionTracker(rules.decks)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    rounds_since = 0
    played = walks = shoes = 0
    walk_rounds = []
    fresh = True
    while played < ROUNDS:
        if fresh or _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            tracker.new_shoe()
            rounds_since = 0
            shoes += 1
            fresh = False
        tc = tracker.hilo_true()
        if round(tc) <= t:  # bin convention: bin <= t <=> tc < t + 0.5
            walks += 1
            walk_rounds.append(rounds_since)
            fresh = True  # abandon the shoe, re-seat at a fresh one
            continue
        result = play_round(rules, shoe, strategy, bet=1.0)
        tracker.observe_round(result)
        rounds_since += 1
        played += 1
    med = statistics.median(walk_rounds) if walk_rounds else float("nan")
    per_1k = 1000.0 * walks / played
    print(f"  tc<={t:+d} {per_1k:16.2f} {per_1k * 0.2:12.2f} "
          f"{per_1k * 0.14:12.2f} {100.0 * walks / shoes:15.1f}% "
          f"{med:18.0f}")

print()
print("walks/h assumes every observed round is played (instant re-seat);")
print("median walk round = rounds into the shoe when the line fires.")
