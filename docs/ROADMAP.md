# Roadmap

**Current milestone: M4** (M3 Ride Free rules done 2026-07-17).

Each milestone has a validation gate; don't advance until it passes.

## M0 — Scaffold ✅
Docs, conventions, `Rules` dataclass, seeded `Shoe`, hand valuation, tests.

## M1 — Standard blackjack engine ✅
Deal, hit/stand/double/split, dealer play (H17/S17), settlement with the ledger money
model, total-dependent basic strategy (`BasicStrategyH17`), seeded simulator + CLI.
**Gate:** hand-level unit tests with known outcomes (constructed shoes → exact
expected settlements), including split/split-ace/double edge cases — 58 tests pass.
**Early signal:** 4M-hand sim gives house edge 0.629% ± 0.058% (published ≈ 0.62%)
and per-round std dev 1.160 (published ≈ 1.15) — foreshadows the M2 gate.

**Known metrics artifact for M2 to fix:** the CLI's `dealer_final` distribution counts
the dealer's cards even in rounds where the dealer never draws (all player hands bust,
or a natural ended the round). That deflates the observed bust rate (~23.5% vs. the
true ~28% dealer-plays-out figure) and inflates low totals. M2's validation engine must
compute dealer outcome stats over *completed* dealer hands (or simulate the dealer in
isolation per up-card) to compare against published tables.

## M2 — Validation engine + match published statistics (standard blackjack) ✅
Built the validation engine: `dealer_odds.py` (exact analytic dealer-outcome oracle,
memoized infinite-deck recursion sharing the engine's `dealer_should_hit`) +
`validation.py` (`Check`/`run_suite`/`to_html`). The battery runs the sim over
millions of hands and compares each metric to a reference with a confidence interval;
`Check.status` is PASS / FAIL / ADVISORY (imprecise reference, non-gating) / BASELINE
(no reference, frozen as a regression anchor). CLI: `validate` prints the report and
writes a theme-aware HTML file. The dealer state machine is validated by a three-way
agreement: hand-computed micro-cases → exact calc → real-engine Monte Carlo.

Two rulesets are validated so the check isn't a one-off: `STANDARD_6D_H17` and
`STANDARD_6D_S17`. `BasicStrategy` adapts to the soft-17 rule (11 vs A, soft 18 vs 2,
soft 19 vs 6), so the same strategy plays both correctly. Run either via
`validate --rules {h17,s17}`.

**Gate — met (5M-hand runs, seed 20260717):**
- House edge: H17 0.6397% ± 0.052% vs published 0.62% (+0.38σ); S17 0.4710% vs
  published ~0.40% (+1.38σ). Both pass. ✅
- Dealer bust per up-card (all ten) vs exact calc, every cell within noise, under both
  rules; aggregate H17 28.536% vs 28.542% (−0.30σ), S17 28.153% vs 28.159% (−0.30σ). ✅
- Player natural rate 4.751–4.755% vs fresh-shoe exact 4.7489%. ✅
- Per-round std dev ~1.15–1.16 (advisory; published "~1.15" is a rounded figure).
- Pair / split / double frequencies collected as baselines.

Note: the `cut_card` house edges sit slightly *above* the published figures. Adding
the shoe-end modes (see DESIGN.md) let us check why. H17, 8M hands each, seed 20260717:

| shoe mode      | house edge | 1 s.e. |
| -------------- | ---------- | ------ |
| cut_card       | 0.694%     | ±0.041% |
| fixed_rounds   | 0.661%     | ±0.041% |
| csm (off top)  | 0.624%     | ±0.041% |
| published      | ~0.62%     | —      |

`csm` reproduces the published combinatorial figure almost exactly (0.1σ) — a clean
independent validation of the off-the-top EV. The ordering cut_card > fixed_rounds >
csm matches theory (cut-card effect + depletion). **But the gaps (~0.03–0.07%) are
each ~1 s.e. of the pairwise difference at 8M hands, so the cut-card effect is a
visible trend, not yet statistically resolved.** Pinning it down needs ~10× more hands
or common-random-numbers variance reduction (replay identical shoes through each mode
so noise cancels) — a candidate task for the M5+ optimization/experiment work.

**Methodology notes for reuse at M4:**
- The aggregate dealer check uses the *unconditional* dealer Monte Carlo (plays out
  every hole card, no peek) so it is apples-to-apples with the exact ∞-deck aggregate.
  The full-game "completed hands" distribution is peek-conditioned (dealer naturals
  excluded) and is therefore a different quantity — don't compare it to the
  unconditional reference.
- References computed independently (exact calc, fresh-shoe combinatorics) are trusted
  as hard gates; rounded published folk numbers (std dev) are advisory.

## M3 — Ride Free rules ✅
Implemented as pure configuration in the shared engine — no variant-forked code paths.
The engine auto-funds free actions (free strictly dominates paying): a free split puts
the casino's button on the new hand (`wager=0, free_wager=bet`), a free double adds a
free button (`free_wager += bet`). Settlement was already ledger-general from M1: win
pays `wager + free_wager`, loss costs `wager` only, push returns nothing extra. Paid
doubles use `wager += bet` (not `*= 2`) so doubling a free-split hand costs one unit.
`HandView` exposes `free_split_available` / `free_double_available` to strategies.

`FreeBetStrategy` is **provisional**: takes every free double, free-splits all
eligible pairs except 5,5, falls back to standard basic strategy otherwise. It lacks
the published chart's hit/stand deviations (dealer-22-push devalues standing), so its
EV is NOT comparable to published figures — that's M4.

**Gate — met:** hand-level tests for every free-money settlement combination
(free split / free resplit buttons / free double / free-double-after-free-split /
paid-double-on-free-hand / dealer 22 × each / dealer blackjack / player natural /
busts) — 107 tests pass. 2M-round sim: free doubles 13.6% of rounds, free splits
4.9%, dealer 22 = 8.1% of dealer-completed hands, std dev 1.086 — all coherent with
theory. Provisional edge 1.336% ± 0.077% (expected worse than published ~1.04%).
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
The main event, in deliberate order.

**Playing deviations (Matt, 2026-07-17):** build a deviations layer — a strategy
overlay that can override individual decision cells, eventually count-conditioned.
The foundation already exists: `player_ev.EVCalculator` computes exact EVs from rank
weights, so swapping the fixed 4/13 weights for the live shoe composition yields the
optimal action for the actual cards remaining. Motivating case: 5,5 — free-doubling
beats free-splitting by only 0.15% off the top (WoO), because split 5s can catch
more free splits (another 5) and free doubles (draw to 9/10/11). In a small-card-rich
shoe that gap could flip; the deviation layer should answer exactly when.

Steps:

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
