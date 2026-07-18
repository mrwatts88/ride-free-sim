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

## Shoe-end modes (the cut card)

The cut card is configured by `Rules.shoe_end_mode` (with `penetration` and
`rounds_per_shoe` as the associated knobs):

- **`cut_card`** — realistic fixed-depth cut card at `penetration`. The round in which
  the cut card appears is finished, then the shoe reshuffles. Rounds-per-shoe varies
  with composition, so this **includes the cut-card effect**: a fixed-depth cut biases
  the dealt-round composition slightly and raises the house edge by ~0.01–0.03% versus
  a combinatorial figure. This is the mode for real-game and counting analysis.
- **`fixed_rounds`** — reshuffle after exactly `rounds_per_shoe` rounds. Fixed
  rounds-per-shoe removes the cut-card effect while keeping intra-shoe depletion;
  matches fixed-round combinatorial analyses.
- **`csm`** — reshuffle a full shoe before every round, so each round is dealt off the
  top of a complete shoe. No depletion at all: the direct match to a published
  off-the-top house edge, and the "counting does nothing" baseline (approximates a
  continuous shuffle machine).

Why this matters: published house edges are combinatorial (no cut card), so `csm`
should match them tightest; `cut_card` sits slightly above by the cut-card effect. For
the counting/targeting phase, `penetration` is the single most important lever (deeper
penetration → more counter advantage), so the cut card is a first-class, sweepable
config, not a fixed default. The simulator's reshuffle decision lives in one place
(`simulator._needs_reshuffle`).

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

## Decision record: suit-aware cards for M8 (21+3), engine unchanged

**Decision (2026-07-17):** to model the 21+3 side bet (flush/straight/trips need
suits and distinct J/Q/K), the Shoe will deal full (rank, suit) cards and a
`value()` collapse will feed the existing engine — game logic keeps consuming
blackjack values only, preserving the one-engine validation transfer. Side bets
settle in the engine from the raw dealt cards, following the insurance pattern
(Rules data + optional strategy hook + explicit ledger fields + hard validation
gate before any attack work). The 21+3 bet is placed pre-deal, so its strategy
hook is pre-round — the natural shape for a counting bet. Accepted cost: dealt
sequences change for every seed (v1 exactly reproducible at tag `ride-free-v1`).

**Mechanism (M8a, 2026-07-17):**

- A raw card is a `(rank, suit)` tuple: rank 1–13 (1 = ace, 11/12/13 = J/Q/K),
  suit 0–3. `cards.value(card)` collapses to the blackjack value
  (`min(rank, 10)`).
- The collapse happens **once, at shuffle time**: `Shoe` shuffles the
  52·decks distinct raw cards, keeps that sequence in `_raw`, and precomputes
  the parallel values list that `deal()` reads — so `deal()` still returns
  plain value ints, at zero per-deal cost, and the engine, hand valuation,
  trackers, and every strategy are untouched. `remaining_composition()` and
  `dealt_cards()` stay value-keyed (RF signals unchanged); suit-aware
  composition queries are M8c.
- Raw cards surface via `Shoe.raw_dealt()` (the raw twin of `dealt_cards()`).
  In M8b the engine snapshots the deal position before the initial deal; the
  21+3 hand is raw positions `pos` (player card 1), `pos+1` (dealer up),
  `pos+2` (player card 2). `RoundResult` will carry those three raw cards and
  the side bet settles inside the engine, insurance-style.
- `validation.InfiniteDeckShoe` (dealer state-machine Monte Carlo only) stays
  value-based — it never feeds a side bet.

## Decision record: baccarat as its own small engine (M9), shared plumbing

**Decision (2026-07-17):** the Dragon 7 / Panda 8 attack (M9) gets a separate
engine in `baccarat.py` rather than a variant of the blackjack engine. The
one-engine doctrine exists to buy validation transfer between variants that
share game logic; baccarat shares none of it — no player decisions, a fixed
drawing tableau, mod-10 totals — so forcing it through `engine.py` would add
rule conditionals with zero transfer, the exact thing working rule 1 forbids.
What IS shared is the trusted plumbing and doctrine: the deterministic
`cards.Shoe` + `shoe_seeds` (an 8-deck baccarat shoe is the same 416 physical
cards; ten-values collapse to 0 via `card % 10`, so the repo's 1-10 value
representation is already baccarat-native and the M8a suit layer is not
needed — both side bets are rank-only), rules-as-data (`BaccaratRules`:
decks, commission, the EZ three-card-7 push, side-bet paytables, shoe-end
modes with the same csm-as-published-comparator semantics), the
engine-asks/bettor-answers protocol with observer hooks, explicit ledger
fields per wager, and the M8b two-reference validation gate.

- The **tableau lives in code**, not in Rules: the player/banker drawing
  matrix is universal across casinos (what varies is settlement and
  paytables, and that is data).
- `exact_outcomes(composition)` is the single exact reference: integer
  enumeration over ordered 6-card sequences (4- and 5-card hands weighted by
  falling-factorial fillers, matching WoO's published combination-table
  convention exactly). It deliberately takes an arbitrary composition so the
  M9a fresh-shoe gate and the M9b live pre-deal EV calculator are the same
  audited function — no second implementation to trust.
- Side bets follow the insurance/21+3 doctrine: settled by the engine only
  when a bettor stakes them; no built-in bettor stakes them unless
  configured, so published-edge validation is never contaminated.

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

## Decision record: the trainer reuses the engine via replay (2026-07-18)

**What:** `ridefree.trainer` — a localhost web app (stdlib `http.server`,
vanilla JS, SQLite, zero dependencies) that drills the chosen live play
(docs/ARTICLE_BLACKJACK.md: crouch15 Red 7 card on STANDARD_6D_H17, pen .75)
and flags every human error: bet-vs-card, basic-strategy play, insurance,
the leave threshold, and the running count itself (quiz at shuffle + random
spot checks + on-demand). Sessions and every scored decision persist to
`data/trainer.db` for lifetime accuracy views.

**How the human gets inside `play_round` without touching it:** the engine is
synchronous, so `trainer/driver.py` replays the round from the shoe's
round-start snapshot on every decision — a scripted strategy feeds the answers
recorded so far and raises `NeedDecision` at the first unanswered ask; the
immutable shoe order makes each replay re-deal the identical round. Cost is
O(decisions²) engine runs per round — nothing at human pace. The alternatives
(threaded engine, forked interactive engine) were rejected: the first adds
lifecycle/cleanup complexity to a stdlib server, the second forks validated
code (CLAUDE.md rule 1).

**Oracles are the validated objects themselves:** the play check is
`strategy.BasicStrategy.choose()` on the engine's own `HandView`; the game is
`STANDARD_6D_H17` unmodified; shoes come from `cards.shoe_seeds`, so a session
is replayable from its recorded seed. The card (tags incl. red sevens, IRC,
rungs, insure/leave thresholds) is data (`trainer/card.py`), like `Rules`.

**The one piece of duplicated mechanics, and its gate:** mid-round table
display (which raw card sits in which split hand) — the engine only reports
final `RoundResult`s. `driver._mirror` reconstructs it from the raw deal
sequence plus the decision trace, and asserts itself card-for-card against
the engine's result every finished round (and against the engine's `HandView`
at every pending ask), so drift raises `MirrorError` instead of mis-training.
Fuzzed in `tests/test_trainer.py` over thousands of random-play rounds.

**Count visibility convention:** the oracle RC excludes the current round's
hole card until settlement, then counts it — exactly what a live counter sees,
and the convention the E16/E17 pricing assumed (hole revealed before the next
bet decision).
