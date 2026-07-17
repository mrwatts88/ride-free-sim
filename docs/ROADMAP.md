# Roadmap

**Current milestone: M1** (M0 scaffold done 2026-07-17).

Each milestone has a validation gate; don't advance until it passes.

## M0 — Scaffold ✅
Docs, conventions, `Rules` dataclass, seeded `Shoe`, hand valuation, tests.

## M1 — Standard blackjack engine
Deal, hit/stand/double/split, dealer play (H17/S17), settlement with the ledger money
model, total-dependent basic strategy for the M2 ruleset.
**Gate:** hand-level unit tests with known outcomes (constructed shoes → exact
expected settlements), including split/resplit/double-after-split edge cases.

## M2 — Validation engine + match published statistics (standard blackjack)
Build the **validation engine** (see "Validation engine" in DESIGN.md): a
`MetricsCollector` + `ValidationSuite` that runs the sim over tens of millions of
hands and compares a full battery of metrics — not just one number — against
published references, each with a confidence interval. It is a permanent regression
harness reused at M4 and M6, not a one-off script.

Canonical ruleset `STANDARD_6D_H17`: 6 decks, dealer hits soft 17, blackjack pays 3:2,
double any two cards, double after split, no surrender, resplit to 4 hands, no resplit
aces, one card to split aces.
**Gate — every metric with a published reference must pass, including:**
- EV within CI of the published Wizard of Odds house edge for this exact ruleset
  (look up the exact figure at milestone time; ~0.6% region for total-dependent
  basic strategy).
- Dealer outcome distribution (17/18/19/20/21/BJ/bust), overall **and per up-card**
  (Wizard of Odds publishes the full table — the most bug-sensitive check we have).
- Player and dealer blackjack rates (~4.75% each, 6 decks).
- Pair / split / double frequencies under basic strategy.
- Win / lose / push distribution and per-round profit std dev (≈ 1.15 units).
- Metrics with no published reference are still collected, reported as unvalidated,
  and frozen as regression baselines.

## M3 — Ride Free rules
Add as pure configuration: free doubles on hard 9/10/11, free splits on all pairs
except tens, dealer 22 pushes all non-blackjack live hands. Free-bet basic strategy.
**Confirmed from Potawatomi's published rules (2026-07-17), encoded in the
`RIDE_FREE` preset:**
- Free splits on any pair except 10-value cards; free resplits up to 4 hands.
- Aces: split once only, one card to each split ace.
- Free doubles on **hard** two-card 9/10/11 only, including after splits; soft hands
  and other totals may double with the player's own money.
- Blackjack pays 3:2; all live hands push against dealer 22.

**Still open (Matt / rack card):** number of decks and H17 vs. S17 — both are `Rules`
toggles (`decks`, `dealer_hits_soft_17`); 6-deck H17 assumed until confirmed.
**Gate:** hand-level tests for every free-money settlement combination (free split ×
free double × dealer 22 × dealer blackjack).

## M4 — Match published Free Bet EV
Extend the M2 validation engine with the Ride Free metric battery.
**Gate:**
- Simulated EV matches the published Free Bet Blackjack house edge for the matching
  ruleset (~1.0% region for 6-deck H17; verify exact figure and ruleset at milestone
  time).
- Dealer 22 rate, free-split rate, and free-double rate match published/derivable
  values; the standard-blackjack battery still passes when run with the
  `STANDARD_6D_H17` preset (regression).

## M5 — Counting infrastructure + hi-lo validation (standard blackjack)
Build the pluggable counting framework (see "Counting architecture" in DESIGN.md):
counts observe every dealt card and feed bet sizing and strategy deviations. Two
families, both switchable and tweakable from day one:

1. **Linear EOR counts** — hi-lo and friends: per-rank tags summed into a running
   count, converted to true count.
2. **Composition targeting** — track the full per-rank frequency distribution of the
   remaining shoe (`Shoe.remaining_composition()` already exists for this) and compute
   event probabilities directly: P(dealt a free-splittable pair), P(hard two-card
   9/10/11), etc.

Then **validate the machinery on known ground**: hi-lo on standard blackjack is the
second validation rung after basic strategy, and published numbers exist for it.
**Gate:**
- True-count frequency distribution matches published tables (Wizard of Odds /
  Schlesinger) for matching penetration.
- EV as a function of true count reproduces published per-true-count edges (~+0.5%
  per true count is the folk number; use exact published tables).
- A standard bet ramp (e.g. 1-8 spread) reproduces the published overall player
  advantage for matching rules/penetration/spread. This gate is demanding — published
  figures are extremely sensitive to exact conditions, so the comparison must pin
  rules, penetration, and ramp to the source's stated conditions.

## M6 — The attack: free-bet targeting on Ride Free
The main event, in deliberate order:

1. **Perfect-information upper bound first.** Use exact composition tracking (the
   sim knows the true remaining shoe) to bet-size on P(free split) and P(free
   double). This bounds the attainable edge: if perfect knowledge of pair/double
   probabilities can't beat the game, no practical count can, and we stop there.
2. **First attack: pair probabilities.** Bet ramp driven by P(free-splittable pair)
   from tracked rank frequencies. Measure edge vs. flat betting.
3. **Double probabilities.** Add P(hard two-card 9/10/11) targeting; combined signal.
4. **Practical counts.** Distill whatever wins into human-trackable systems (side
   counts, simplified tags), and quantify the edge lost at each simplification step.
5. **Hybrid**: EOR-style count for the base game combined with free-bet targeting.

**Gate:** every experiment reproducible from (config, seed); results with confidence
intervals sized from measured per-round variance; a clear verdict per system:
edge, bankroll requirements, and detectability-relevant stats (bet spread used).

## M7 — Rust simulation core
PyO3 + maturin. Port the frozen engine; differential-test against the Python reference
on seeded shoes (exact match required, not statistical). Then large parameter sweeps.
May be pulled earlier if M5/M6 sweeps become throughput-bound.
**Gate:** bit-identical results vs. Python reference across a large seeded corpus;
throughput sufficient for billions of hands.
