# Ride Free Simulator

A deterministic simulator for **Ride Free** blackjack (Potawatomi Casino's Free Bet
variant: free splits, free doubles, dealer 22 pushes). Goal: first reproduce published
house edges exactly, then search for betting/counting systems that beat the game.

**Start every session by reading `docs/STATUS.md`** — current state, key measured
numbers, the specified next step, and operational notes (throughput limits, sharding
pattern, seed hygiene). Update it at every checkpoint. Architecture is in
`docs/DESIGN.md`, milestones/gates in `docs/ROADMAP.md`, the experiment log in
`docs/EXPERIMENTS.md`.

## Working rules (non-negotiable)

1. **Rules are data — one engine for all variants.** Every game parameter — decks,
   H17/S17, blackjack payout, dealer-22 behavior, free-double totals, free-split
   pairs, resplit/split-ace rules, max hands — lives in the immutable `Rules` object
   (`src/ridefree/rules.py`). Variants are configurations. Never scatter rule
   conditionals through game logic, and **never fork variant-specific code paths**:
   the entire reason standard blackjack is in this repo is that validating the shared
   engine against its published numbers is what makes the Ride Free results
   trustworthy. Code that only runs for one variant gets no validation transfer, so
   keep it to the minimum the `Rules` object genuinely requires.

2. **The engine asks, strategy answers.** Playing decisions come from pluggable
   strategy objects given the hand state and the legal actions. Never bake a playing
   decision into the engine.

3. **Deterministic under seed.** `(rules, seed, strategy)` must reproduce exact shoes
   and results, always. No hidden RNG, no `random` module calls outside seeded
   `random.Random` instances. Any bug found in a long run must be replayable from its
   seed.

4. **Money is a ledger.** Every hand tracks player-funded wager and casino-funded
   ("free") wager separately, and every settlement is explainable. Never collapse to a
   single "bet size" — free wagers pay winnings only and vanish on push/loss.

5. **Correctness before speed.** This Python engine is the slow, obvious, trusted
   reference. No performance work until it is frozen and validated against published
   EVs (see roadmap). Event logging is optional and off by default; failing seeds
   re-run verbose.

6. **Iterate small.** One milestone-sized chunk per session. Don't start the next
   rung of the validation ladder until the current one's gate passes.

7. **Validation ladder.** Hand-level known-outcome tests → exhaustive decision/payout
   tests → statistical frequencies (blackjack rate, dealer bust/22 rate, free-double
   rate) → published house edge match → (later) differential tests vs. the fast engine.

## Practical notes

- Python 3.12+, managed with `uv`. Run tests: `uv run pytest`.
- Cards are ints: `1` = ace, `2`–`9` pips, `10` = ten/jack/queen/king (suits and
  face distinctions never matter in blackjack).
- Don't trust remembered house-edge numbers for validation gates — look up the exact
  published figure (Wizard of Odds) for the exact ruleset at milestone time.
