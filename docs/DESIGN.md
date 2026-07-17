# Design

Deterministic domain model, no UI/DB/threading/ML. Data flow:

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
