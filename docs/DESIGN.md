# Design

Deterministic domain model, no UI/DB/threading/ML. **One engine serves every variant**
— standard blackjack and Ride Free are `Rules` presets over identical code. This is a
validation strategy, not just tidiness: the standard-blackjack battery (M2) validates
the same deal/split/double/settlement machinery Ride Free runs on, so its evidence
transfers. Variant-forked code paths would break that transfer and are prohibited
beyond the conditionals the `Rules` object itself drives.

Data flow:

```
Shoe state → hand state → legal actions → resolved payouts
```

## Components

| Component          | Responsibility                                                        |
| ------------------ | --------------------------------------------------------------------- |
| `Rules`            | Immutable ruleset: every game parameter as data (exists)              |
| `Shoe`             | Seeded, shuffled card array; deal; penetration/cut marker (exists)    |
| `Hand`             | Cards + wagers + state; valuation is pure functions (valuation exists)|
| `Round`            | One round: deal, player turns, dealer turn, settlement                |
| `ActionResolver`   | Computes legal actions for a hand under the rules                     |
| `DealerPolicy`     | Dealer drawing rules (H17/S17) driven by `Rules`                      |
| `PlayerStrategy`   | Pluggable: given (hand state, legal actions) → action                 |
| `SettlementLedger` | Per-hand money resolution; every payout explainable                   |
| `Simulator`        | Seeded loop over rounds; owns the shoe lifecycle                      |
| `MetricsCollector` | Frequencies, EV, variance; separate from game logic                   |
| `ValidationSuite`  | Compares collected metrics against published values with CIs          |

## Validation engine

Matching a single house-edge number is weak evidence — an engine with two offsetting
bugs can still land on the right EV. The validation engine compares a *battery* of
metrics from large runs against independently published values, each with a
confidence interval, and reports every metric as pass/fail/no-reference.

Metric battery (standard blackjack; exact reference values looked up at milestone
time, never trusted from memory):

- **EV / house edge** per unit of initial wager.
- **Dealer outcome distribution**: P(final 17), P(18), P(19), P(20), P(21),
  P(blackjack), P(bust) — overall and conditioned on each up-card (Wizard of Odds
  publishes the full up-card table; this is the single most bug-sensitive check).
- **Player blackjack rate** (~4.75% for 6 decks) and dealer blackjack rate.
- **Hand-type frequencies**: pair dealt rate, split rate, resplit rate, double rate
  under basic strategy.
- **Round outcome distribution**: win / lose / push rates.
- **Per-round variance / std dev** of profit (published ≈ 1.15 units for flat-bet
  basic strategy; also needed later to size experiment confidence intervals).
- **Ride Free additions (M4)**: dealer 22 rate, free-split rate, free-double rate,
  frequency of hands carrying both player and free money.

Rules for the suite:
- Every check states its reference source and tolerance; tolerance derives from the
  simulation's own CI (e.g. ±3σ), not a hand-tuned epsilon.
- A metric with no published reference is still collected and reported, but marked
  unvalidated — it documents engine behavior and becomes a regression baseline for
  differential tests (M6).
- The suite is a permanent regression harness, not a one-time gate: it reruns on
  every engine change with fixed seeds.

## Money model

Each hand carries `player_wager` and `free_wager` separately. Settlement resolves them
explicitly:

- **Player wager**: normal blackjack settlement (win pays 1:1 or 3:2, push returns,
  loss forfeits).
- **Free wager**: casino-funded. A win pays the player the winnings (1:1) — the stake
  itself was never the player's. A push or loss pays/costs the player nothing.
- Profit per round = sum over hands of settled amounts; never derived from a single
  "total bet" figure.

This matters because a hand can hold both kinds of money at once (e.g. player-funded
hand, free split, then free double on one branch), and dealer-22 push interacts with
each kind differently.

## Event log

Optional, off by default for speed. When enabled, every deal, action, rule grant
(e.g. "free split granted"), dealer card, and settlement line is recorded. Any failing
or suspicious seed re-runs in verbose mode to produce a full narrative.

## Counting architecture

Counting systems ("accounting systems") are first-class, pluggable, and switchable —
never baked into the engine. A count is an **observer + advisor**:

- **Observes**: every card as it is dealt (the engine already exposes the dealt
  stream; `Shoe.remaining_composition()` gives exact per-rank remaining counts).
- **Advises**: bet size before the deal, and optionally strategy deviations during
  play, given its current state.

Two families share this interface:

1. **Linear EOR counts** (hi-lo, etc.): per-rank tag vector → running count → true
   count. Cheap, human-executable, well-published — used to validate the counting
   machinery itself (roadmap M5).
2. **Composition targeting**: maintain the per-rank frequency distribution of the
   remaining shoe and compute event probabilities directly — e.g.
   P(next hand is a free-splittable pair), P(hard two-card 9/10/11). This is the
   Ride Free attack (roadmap M6): free-bet value depends on *event frequency*, which
   linear high-vs-low counts weren't designed to sense. Note pair probability rises
   when the remaining shoe is *unbalanced* in any rank — a variance-of-composition
   signal, not a high-vs-low signal.

Design consequences:
- The engine must emit dealt cards to observers in a fixed, deterministic order.
- Perfect-information counts (reading true shoe composition) are legal components:
  they establish upper bounds on attainable edge before any practical count is
  designed.
- Bet policy is a separate pluggable piece (flat, ramp-by-true-count,
  ramp-by-probability) so any count composes with any ramp.

## Decision record: Rust later, not now

**Decision (2026-07-17):** Build the Python reference engine first; defer the Rust
simulation core (PyO3 + maturin, Python experiment layer on top) until the experiment
phase (roadmap M6). The Python engine then becomes the differential-test oracle for
the Rust port on seeded shoes.

Rationale:
- Validating a house edge to ±0.02% needs only ~30–40M hands (per-hand std dev ≈ 1.15
  bet units); pure Python does that in minutes. Rust throughput only matters for
  distinguishing tiny (~0.05%) effects across large parameter sweeps — the M5+ phase.
- The rules model churns most in early development; a dual-engine setup doubles every
  churn. Porting a frozen, validated engine against a golden seeded test suite is a
  cheap transcription job.
- PyO3/maturin adds a build step to a repo that currently needs none, and the binding
  API can't be designed well before the experiment layer's needs are known.
