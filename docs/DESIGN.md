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

## Decision record: Pot of Gold settles from the ledger it already keeps (M10, 2026-07-18)

**What:** `Rules.side_bet_pot_of_gold` — a payout tuple indexed by lammer
count (entry [k-1] pays exactly k lammers; counts past the top rung pay the
top rung; empty = not offered; `PAYTABLE_POG_1/2/POG_04` presets). Staked
strictly pre-deal via the optional hook `bet_pot_of_gold(rules)` (insurance/
21+3 pattern: no built-in strategy stakes it, published-edge validation
untouched); settled in `play_round` at round end as
`settle_pot_of_gold(paytable, free_splits + free_doubles, stake)`.

**Why no new mechanics:** the engine has tracked casino-funded wagers per
hand since M3 (working rule 4) and already counts `free_splits`/`free_doubles`
per round — the lammer count IS that sum. The bet consumes no cards and no
RNG, so the deal sequence and every main-game decision are bit-identical with
and without the stake (brace test in tests/test_pog.py). Settlement semantics
from the NV rules-of-play filing (fetched 2026-07-18): the lammer is kept
whether that hand wins, loses, or pushes; all Pot of Gold wagers lose to a
dealer blackjack — which the peek path realizes automatically (0 lammers can
exist when the round ends at the peek), and the player-natural path likewise.

**Strategy convention, proved not assumed:** token distribution depends only
on free-bet take/decline choices (lammers exist only at two-card decision
points). Enumeration over every free-bet-eligible state
(scratchpad, 2026-07-18) shows `OptimalStrategy` declines NO free bet — the
lone divergence family is 5,5 (and post-split 5,5), where free-DOUBLE beats
free-split by 15–30% of a bet on main-game EV, matching WoO's "normal
strategy doubles fives" convention and their separate split-fives variant
(`strategy.SplitFives` wrapper reproduces it: +3.0pp on the PoG edge for
−0.15pp of main edge).

**The published-table discrepancy (E19):** P(0 lammers) is strategy-free
dealing arithmetic — `side_bets.exact_p0_pot_of_gold` (exact fractions,
rules-driven) gives 0.838228071 for six decks, and is peek/no-peek invariant
BECAUSE of the lose-to-dealer-BJ rule. WoO's simulated table publishes
0.833420, irreconcilable under the stated rules at any deck count; every
k>=2 rung of their table matches our sims. Reconciliation hypothesis with the
arithmetic bridge (their sim appears to let lammers survive ten-up dealer
naturals) is recorded in EXPERIMENTS E19; the M10a gate therefore scores
exact-P(0), the k>=2 shape, the convention-free split-fives deltas, and the
bridge — not blind agreement with a table our own arithmetic refutes. The
real-rules PT1 house edge is ~7.7%, not the advertised 5.77% — the M10b
attack must clear the honest number.

## Decision record: the RA bank prices variance without new strategy code (M11/E25, 2026-07-19)

**What:** `experiments.run_ra_bank` — one paired pass banking, per hi-lo TC
bin, everything needed to price a playing layer's effect on the mean AND the
second moment of round profit: chart-arm moments (n, Σp, Σp²); for every
candidate play change the paired (n, Σd, Σd², Σp·d) where d is the profit
delta against the chart timeline (so ΔE[p²] = E[2pd + d²] exactly); and the
insurance overlay as counts (ace-up rounds, dealer naturals, Σp and Σp over
naturals — the settle is ±½/+1 per unit, so any TC-threshold insurance rule
prices in closed form, hedging cross term included; dealer-natural rounds
have no decisions, so play deltas vanish there by construction).

**Why paired replay, not new arms:** the E24 hobby objective (min bankroll
at an hourly floor) trades EV against variance at an exchange rate set by
the whole card, so play selection must be re-derivable for ANY card — the
bank stores per-play moments and `data/e25_ra.py` selects at arithmetic
time (the E4c/E16/E24 "simulate once, evaluate ramps analytically" doctrine
extended to its second moment). Three sources on one canonical timeline
(the chart's cards, the E5/E8 snapshot-replay pattern): candidate cells =
every chart DOUBLE/SPLIT decision replayed with that one cell suppressed
(`_SuppressCell`, alternative from the same infinite-deck calculator);
composition deviations replayed at bins >= dev_tc_min (default +2 — the
EVCalculator replay is the expensive part and hobby money above the floor
lives there), attributed to the FIRST diverging decision; insurance needs
no replay at all. Selection groups cells by (chart row, upcard) and picks
one policy per group — a dev cell and its suppression touch the same
rounds, so they are alternatives, never teammates.

**Gates:** bit-exact agreement of the dev accumulators with the certified
`run_deviation_value` on the same seed (tests/test_ra_bank.py); the
aggregate-equals-sum-of-cells identity; chart bins vs the banked E16 basic
curve and dev values vs the E16 paired values on fresh seeds; insurance
P(BJ|ace) vs first principles (verdict script). Known blur on record:
later same-round divergences ride along with the first (exactly how a
card of cells is played); policy effects compose additively in (μ, M2);
the chosen card's live OOS certification plays the real combined policy.

## Decision record: shuffle procedures as data the Shoe composes (M12a, 2026-07-19)

**What:** `shuffle.py` — a `Shuffle` model is an immutable dataclass with one
method, `permute(stack, rng) -> list`: `stack` is the pre-shuffle order (top
first), `rng` a seeded `random.Random` supplying ALL randomness, and each
pass draws a content-independent number of variates, so `(seed, stack,
shuffle)` replays exactly (working rule 3 extended to paradigm 2). Models:
`UniformShuffle` (the paradigm-1 null), `ShelfShuffle(shelves, passes)` (the
Diaconis/Fulman/Holmes machine to its published spec: deal from the BOTTOM
of the stack, uniform shelf, top-or-under at 1/2, unload in shelf order —
unload order is distributionally irrelevant because shelf choices are i.i.d.),
`RiffleShuffle(piles, passes)` (GSR a-shuffle: multinomial cut, uniform
interleave; `piles`/`passes` are the quality knobs, a-then-b == ab), and
`ComposedShuffle(stages)`. `Shoe` gained keyword-only `shuffle`/`stack`
(default None/None = the historical Fisher–Yates path, asserted
BYTE-IDENTICAL to explicit `UniformShuffle` in tests — zero validation
transfer lost) and `raw_order()` (the full order, dealt + undealt, i.e. the
successor shoe's pre-shuffle stack for inter-shoe forensics).

**Why models permute abstract stacks, not cards:** the forensic instruments
(guessing, color changes, class histograms) run on position labels 1..n with
zero engine dependency, and the SAME model object drives a 416-card `Shoe`;
one implementation, validated once (working rule 1's "variants are
configurations" applied to physics). Dealer-clumpiness riffles and full hand
procedures (wash/strip/box) are deferred to M12b's hand-procedure modeling —
they compose from these primitives or land beside them as new dataclasses.

**The measurement layer:** `forensics.py` holds exact arithmetic (valley /
Eulerian class counts; DFH Theorem 3.1 and Bayer–Diaconis class
probabilities as `Fraction`s; exact TV/sep/l∞) and seeded Monte Carlo
instruments (`guessing_experiment` with the pluggable guesser protocol —
`ShelfGuesser` is DFH's conjectured-optimal strategy verbatim, and M12b's
input-aware observers plug in as new guessers; `color_change_experiment`;
`valley_histogram` / `rising_sequence_histogram`). The load-bearing link is
sampler-vs-closed-form: empirical class occupancies are z-gated against the
exact laws, so the physical simulation and the arithmetic certify each other
before any attack work (the paradigm-2 doctrine's "synthetic ground truth
first"). Gates in tests/test_shuffle.py; the precision battery is E26
(`data/e26_shelf_gate.py`).

## Decision record: the exact posterior filters over the label-sort slot axis (M12b rung 1, 2026-07-19)

**What:** `posterior.ShelfPosterior` — the exact conditional next-card law
for an m-shelf pass of a known stack, sequential in the dealt prefix.

**Why exact filtering is possible at all:** the shelf shuffle is a *label
sort* (DFH Description 1): each card independently draws one of 2m lanes,
and the output is a deterministic sort by a fixed global key (shelf, side,
±position). So each card occupies one of 2m known SLOTS in a fixed total
order, independently and uniformly, and "the dealt prefix is o_1..o_t" is
exactly "the t smallest realized slots belong to o_1..o_t in order". The
posterior factorizes into (a) a chain term h_t over the last observed
card's slots — h_{t+1}(s) ∝ H_t(s−1) on the new card's slots, where H is
the running sum — and (b) a per-slot product of independent per-card
survival factors F_d(s) = P(slot_d > s) over the remaining cards,
maintained as one log-sweep with a zero-factor count. Cost O(slots +
remaining·lanes) per dealt card; slots = 2m·n. Multi-pass costs nothing
new: Cor 4.2 (E26-gated) says k passes ARE one bigger-shelf pass, so the
two-pass posterior is `ShelfPosterior(shelves=200)`. The forward GSR
riffle is NOT a label sort (its inverse is) — its exact posterior is a
separate cut-conditioned construction (unique merge decomposition given
the cuts), deferred until a riffle target needs pricing.

**The two-layer rule (Matt):** the posterior core never imports a game.
Payoff arms are thin adapters over (posterior, game EV calculator) —
adapter #1 is `proposition_experiment`, a composition-fair value bet whose
odds make every composition-only strategy worth exactly zero, isolating
order structure as profit. Scope: stack entries must be distinct (one
physical deck); multi-deck shoes repeat cards, so the observer can't tell
copies apart — copy-marginalization in the observation model is rung 2's
first piece.

**Gates:** brute force — conditionals equal full lane-assignment
enumeration through an INDEPENDENT physical pile simulation (deques, dealt
from the bottom) at every step of every reachable output, 1e-9; the
posterior argmax must not lose to DFH's conjectured-optimal strategy
paired on identical decks (it ties: the 2013 conjecture is verified);
self-calibration (claimed hit probability vs realized); adapter #1's
realized profit equals its posterior-predicted edge within CI (the E17
pattern). tests/test_posterior.py; battery `data/e27_posterior_gate.py`.

## Decision record: multi-deck copy ambiguity is a particle filter (M12b rung 2, 2026-07-19)

**What:** `posterior.MultiDeckShelfPosterior` — the next-VALUE posterior when
the observer knows the pre-shuffle order but cannot distinguish the copies of
a repeated card (an 8-deck baccarat shoe hides each rank+suit behind 8 equal
copies). This is the honest observation model; using rung 1's distinct-card
posterior on a multi-deck shoe would hand the sim information a live player
can't have (a paradigm-2 rule).

**Why a particle filter, not exact filtering:** rung 1 is exact because a
dealt distinct card pins one input position; with copies the exact next-value
law sums over all copy-assignments consistent with the observed value-prefix
— a permanent-like object, #P-hard at shoe scale (verified no factorization:
the label-sort slot sweep needs a specific owner per slot, which copies
destroy). So it's sequential importance resampling over the latent
copy-history: **each particle IS a rung-1 `ShelfPosterior` over the distinct
input positions**, carrying one hypothesis of which copy produced each
observed value. The proposal is locally optimal — on observing value v a
particle samples the next position from its own EXACT conditional restricted
to value-v positions, and the incremental weight is exactly that value's
marginal probability — so the estimator is unbiased and converges to the
exact law as particles→∞. Systematic resampling at ESS < N/2; `ShelfPosterior.
copy()` shares the immutable precompute and clones only the conditioning
state. Two consequences that make it trustworthy: with all-distinct values it
degenerates to the exact rung-1 posterior deterministically (no variance —
the single candidate has weight 1), and its first step (before any observe)
is exact regardless of particle count. Both are gates.

**Cost and the PyPy decision:** O(particles × slots × cards) per shoe, ~100×
a single rung-1 walk, so shoe-scale multi-deck is the project's first genuine
throughput wall. The parked PyPy experiment (M7 record) was run here
(`data/bench_pypy.py`): **bit-identical results, 4.3× on the posterior walk /
2.7× on the engine, full suite green under PyPy 3.11** — so PyPy is the
sanctioned accelerator for the heavy multi-deck/baccarat runs (the only
friction: `requires-python >=3.12` vs PyPy's 3.11 ceiling — run via
`PYTHONPATH=src uv run --python pypy@3.11 --no-project`, or relax the pin;
Matt's call). Rust stays unneeded (M7 governs).

**The adapter (E28):** `multideck_proposition_experiment` runs adapter #1 (the
composition-fair value bet, perfect counter = 0) through the filter across
deck counts and shuffle passes, so the channel's decay with copies (decks)
and mixing (passes) is measured. The full P/B/Dragon7/Panda8 coup-EV adapter
over the M9 baccarat engine is the next rung — it needs coup-outcome-under-
ordered-posterior machinery of its own and is scoped separately.

**Gates:** brute-force value-conditionals on tiny duplicated decks (filter
tracks exact within MC error at every step; first step exact; distinct-values
reduces to rung-1 exact); E17 predicted-vs-realized on the adapter (`z`).
tests/test_posterior.py; measurement `data/e28_multideck.py`.

## Decision record: the O(slots) assumed-density filter (M12b rung 3a, 2026-07-19)

**What:** `posterior.AssumedDensityShelfPosterior` — a next-VALUE posterior
whose per-step cost is independent of any particle count, built because the
rung-2 particle filter's O(particles × slots) is the throughput wall in
front of every 8-deck number (E28).

**The state is the exact filter's sufficient statistic, softened only where
copy ambiguity forces it:** per-position fractional occupancy `alive[i]`
(rung 1's boolean remaining-set, made soft) plus ONE chain law over the last
dealt slot (rung 1's h_t/H_t, now a mixture over which same-value copy each
observation was). Remaining positions keep their ORIGINAL uniform slot laws
and the chain stores DEFERRED weights exactly as rung 1 does (survival
factors applied at query time, never baked into the chain — baking them
double-counts at the next query). Consequence, gated in tests: **with
distinct values the ADF IS the rung-1 exact posterior, deterministically**
(1e-9 gate); with copies it is the projection of the exact mixture over
copy-assignment histories onto this product family, and its bias is
measured, never assumed.

**Four structural rules, each the cure for a measured disease** (all found
on E28's 2-3-deck probe shoes, all reproduced in tests/comments):
1. **Capped water-fill subtraction.** Per class, sum(alive) == copies −
   dealt is EXACT bookkeeping, so observing a value removes exactly one unit
   of occupancy, projected onto {0 ≤ δᵢ ≤ aliveᵢ, Σδ = 1} proportional to
   full-information responsibilities. Without the cap, evidence outrunning a
   copy's occupancy under-subtracts; the leaked mass walls off the slot axis
   (3-deck crash, sum(alive) 6.0 vs truth 1.0).
2. **The occupancy hedge.** Copy-class positions never carry a HARD
   zero-survival wall (occupancy capped at 1−1e-9 inside survival factors):
   under soft assignment "certainly alive" is itself an estimate, and a
   stale certain copy poisons every legal slot. Distinct classes keep exact
   walls — their identity is pinned — preserving the rung-1 reduction.
3. **Chain defers to occupancy.** A new chain support is truncated where it
   would strand > STRAND_TOL (0.5) of alive mass behind the frontier, and
   `_repair_certain_dealt` then returns genuinely-stranded residue to its
   value class (in-class only, keeping per-class totals exact). Rationale:
   occupancy totals are exact, the chain is wholly a projection. Overshoot
   is the non-self-correcting direction (observations pull an undershot
   chain forward; nothing pulls an overshot one back). Last resort: if the
   frontier strands ALL remaining mass, the chain is provably lost — reset
   to uninformative and re-form (counted in `surprises`).
4. **The contamination floor (MIX).** The output law is (1−MIX)·model +
   MIX·occupancy-composition — robust-Bayes humility applied at the OUTPUT
   only (internal state stays pure-model). Cure: rare shoes drift into
   near-certain wrong claims late (measured: 6/40 3-deck shoes, one step of
   p≈1e-72 on a 5% card = −234 bits, flipping whole-shoe log-loss negative);
   the floor bounds any step at log2(MIX). MIX grows with copy count (0.02
   calibrates at 2-3 decks; 8 decks needs ~0.25) — fitted per configuration
   on probe seeds, certified on fresh ones (E29 part 2), passed via `mix`.

**Measured fidelity (E29; CRN-paired against the PF on identical shoes):**
at 2-3 decks the ADF realizes ~91-98% of the PF's units/shoe with the same
calibration z and comparable bits, at 57-80× the speed (2 decks: 36 vs
2,061 ms/shoe; 3 decks: 60-74 vs ~4,500). The 8-deck single-pass walk runs
~0.5 s/shoe — the deck count the PF could not touch. Deterministic (no
filter RNG): identical observations always give identical prices; `copy()`
is O(positions), which is what the coup adapter's clone-heavy sampling
leans on.

**Not exact, by proof of contradiction:** tiny-lane brute-force cases where
the true conditional is deterministic (a forced next card from the global
pile order) get hedged/mixed answers — mean-field marginals cannot express
hard global order constraints (worst one-step gap 0.52 on a 6-card 1-shelf
deck; envelope pinned in tests so regressions surface). Real configurations
(20+ lanes, 52-416 cards) sit nowhere near that regime; payoff-level honesty
is carried by the E17 predicted-vs-realized gates and the `surprises`
counter, reported with every experiment row.

## Decision record: the baccarat coup adapter prices by coupled CV sampling (M12b rung 3b, 2026-07-19)

**What:** `coup.py` — the first REAL-GAME payoff arm over the posterior
core (the two-layer rule holds: posterior.py never imports a game; coup.py
imports both sides and stays thin). It converts a filter's sequential
next-value law into Player/Banker/Tie/Dragon7/Panda8 prices for the coup
about to be dealt, from a known 8-deck stack through a shuffle model.

**Why sampling, and why the control variate:** the exact joint over the
next 4-6 cards through the tableau is ~1e5 tree nodes of O(slots) filter
updates per coup — unaffordable. Sequential MC (clone the filter, sample a
value path, resolve through the VALIDATED `play_baccarat_round` on a stub
shoe — no duplicated tableau logic) is unbiased but too noisy at 40:1
paytables. So every sampled path is COUPLED to a composition-model path
driven by the same uniforms (inverse-CDF in fixed value order), and the
estimator is p̂ = mean[1_filter − 1_composition] + p_exact, with p_exact
from the M9-validated `fast_outcomes`. Variance scales with the
filter-vs-composition DIFFERENCE — exactly the quantity being measured —
and the estimate is EXACT with zero variance when the filter degenerates to
a card counter (the load-bearing test gate). ExactOutcomes is reused with
probabilities as float "counts" (total=1.0), so the M9 EV methods apply
verbatim.

**Selection honesty:** bets are selected on sample set A and predicted by
an independent set B (drawn only when something fires) — selecting and
predicting on one noisy estimate overstates edge by winner's curse; with
the split, prediction is unbiased conditional on selection and the E17
realized-vs-predicted gate stays meaningful. The perfect-counter comparator
(exact composition EVs, same thresholds, same shoes) makes the filter's
EXCESS the paradigm-2 deliverable: order structure in real bet units.

**Scope honesty (E30):** observer premise is full knowledge of shoe k's
order; the machine is the shelf model (the exactly-invertible one), not a
literal hand shuffle — hand-procedure modeling (riffle posteriors, strip
cuts) is later M12b work. Observation-degradation (partial view of shoe k)
remains the queued knob.
