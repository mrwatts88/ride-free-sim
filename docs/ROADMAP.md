# Roadmap

**Current milestone: M5** (M4 published-EV match done 2026-07-17).

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

## M4 — Match published Free Bet EV ✅
The published WoO strategy charts are images, so instead of transcribing them we
built `player_ev.EVCalculator` — an exact infinite-deck EV recursion over (total,
soft, own_wager, free_wager, upcard) — and `OptimalStrategy` plays its argmax. The
real-money vs free-hand chart distinction falls out of the funding parameterization
(a push is worthless on a (0,1) hand); documented deviations emerged unprompted
(hit 12v4, 13v2; free hands double soft 19–20 v 6; 5,5 free-doubles, not splits).

Published references (fetched from WoO 2026-07-17): house edge 1.04% for 6-deck H17
DAS resplit-to-4 *including aces*; no-resplit-aces costs 0.08% → Potawatomi
(`RIDE_FREE`) target ~1.12%; dealer-22 probability 0.073536.

**Gate — met (5M-round runs, seed 20260717, cut_card mode):**
- `RIDE_FREE_WOO` house edge 0.9895% vs published 1.04% (−1.06σ). ✅
- `RIDE_FREE` (Potawatomi) 1.0706% vs derived 1.12% (−1.04σ). ✅
- The paired difference between the two configs is 0.081% — reproducing WoO's
  published 0.08% resplit-aces adjustment almost exactly (same-seed runs, so most
  noise cancels in the difference). Strong independent confirmation.
- Dealer 22 rate 7.3538% vs WoO's 0.073536 (+0.01σ) and vs our exact calc (−0.25σ). ✅
- Standard H17 battery passes unchanged (regression). ✅
- New baselines frozen: free split 4.93%/5.02% of rounds (Potawatomi/WoO), free
  double 13.62%, dealer-22 push 6.07% of rounds, Ride Free std dev ≈ 1.067.

**Honest caveat:** both edges sit ~0.05% *below* published, in the same direction on
the same seed. Statistically within gate (~1σ), but plausibly a small systematic:
argmax-EV play may beat WoO's simplified published chart by a hair (cut-card effect
pushes the other way). If it matters later, a csm-mode run isolates the strategy
component from the cut-card component.

## M5 — Signal infrastructure + conditional-EV harness (slimmed)
*Restructured 2026-07-17 (Matt + Claude): the attack comes first; full hi-lo
certification against published tables is deferred to M6c, where it belongs — we
only need hi-lo as a sanity-checked control for now.*

Build the signal layer (see "Counting architecture" in DESIGN.md):
- **CompositionTracker**: perfect-information per-rank counts of the remaining shoe,
  maintained from observed cards (every card in a round is exposed at settlement).
  Both counting families derive from it: event probabilities directly (P(free-split
  pair), P(free-double hand)), and any linear count (hi-lo running count is a dot
  product with the tag vector).
- **Conditional-EV harness**: one simulation pass, binning each round's profit by
  each pre-deal signal → EV-vs-signal curves with CIs, plus pairwise signal
  correlations. This is the primary scientific object: any bet ramp's performance is
  then *derivable* from the curve (E[profit] = Σ P(bin)·bet(bin)·EV(bin)) — simulate
  once, evaluate ramps analytically, verify only the winner by simulation.

**Gate (sanity, not certification):**
- Tracker counts exactly equal `shoe.remaining_composition()` at every point.
- Standard-game EV rises with hi-lo true count, roughly the folk +0.5%/TC slope.

## M6a — The attack: pair & double signals, side by side
Matt's first interest is pairs; the doubles signal is ~2.75× more frequent. Rather
than sequencing them, the conditional-EV harness measures both (plus hi-lo TC as
control) in the same pass — the comparison is the deliverable.

**The open question this answers:** free-double abundance comes from small/mid cards
remaining, which is exactly a bad (negative-count) shoe for the base game — the two
effects plausibly fight. Pair abundance (rank concentration) has no obvious base-EV
anti-correlation. Which signal survives contact with the base game is genuinely
unknown; measure corr(signal, hilo_tc) and EV-vs-signal to find out.

Steps: (1) perfect-information conditional-EV curves for both signals — if perfect
knowledge shows no exploitable EV variation, no practical count can work and we stop;
(2) derive optimal ramps from the curves, verify the best by simulation vs flat;
(3) distill winners into human-trackable counts, quantifying edge lost per
simplification; (4) hybrids with a base-game count.

**Playing deviations (Matt, 2026-07-17):** build a deviations layer — a strategy
overlay overriding individual decision cells, eventually count-conditioned. The
foundation exists: `player_ev.EVCalculator` computes exact EVs from rank weights, so
swapping the fixed 4/13 weights for the live composition yields the optimal action
for the actual cards remaining. Motivating case: 5,5 — free-doubling beats
free-splitting by only 0.15% off the top (WoO), because split 5s can catch more free
splits and free doubles; in a small-card-rich shoe that gap could flip.

**Gate:** every experiment reproducible from (config, seed); results with confidence
intervals sized from measured per-round variance; a clear verdict per system:
edge, bankroll requirements, and detectability-relevant stats (bet spread used).

## M6c — Full hi-lo certification (deferred from M5)
When counting results approach publication grade: true-count frequency distribution
and EV-per-TC vs published tables (Wizard of Odds / Schlesinger), and a standard
bet ramp reproducing the published overall advantage for pinned
rules/penetration/spread. Demanding — published figures are extremely sensitive to
exact conditions.

## M7 — Rust simulation core
PyO3 + maturin. Port the frozen engine; differential-test against the Python reference
on seeded shoes (exact match required, not statistical). Then large parameter sweeps.
May be pulled earlier if M5/M6 sweeps become throughput-bound.
**Gate:** bit-identical results vs. Python reference across a large seeded corpus;
throughput sufficient for billions of hands.
