# Roadmap

**RIDE FREE QUESTION CONCLUDED (2026-07-17).** M6a answered the attack question;
the same-day deep dive (docs/DEEP_DIVE_AUDIT.md, docs/DEEP_DIVE_STRATEGY.md,
E6–E9) audited and re-certified it on clean seeds: wong-in ≈ +1.0%/played round
ceiling on 6.6% of rounds, strictly dominated by standard blackjack, camouflage
thesis refuted by measurement. Insurance and deviations are modeled in-engine and
gate-validated. Human-capture distillation deliberately not pursued. M6b/M6c/M7
parked. The v1 artifact is tagged `ride-free-v1`.

**REOPENED for M8 (2026-07-17): the 21+3 side bet, 9-to-1 paytable.** Same
doctrine, new question: can suit/rank composition beat 21+3? The insurance work
is the template (side bet as Rules data + strategy hook + explicit ledger + hard
gate vs an independently computed/published EV before any attack work).
**M8 ANSWERED (same day): beatable — see M8c.**

**M9 (2026-07-17): the Dragon 7 (EZ Baccarat), with Panda 8 riding along.**
Third target, chosen after scouting: EZ Baccarat is confirmed on Potawatomi's
floor; the Dragon 7 (banker three-card-7 win, 40:1, HE 7.61% at 8 decks) has
published prior art (WoO/Jacobson: countable with a simple 8/9-vs-4-7 count at
~0.6u/shoe) but no published exact-composition ceiling — the same gap the M8
machinery was built to close. Structural appeal over 21+3: no main-bet toll
(sitting out rounds is normal baccarat behavior), the deepest standard
penetration in the house (~14-16 cards from the end of 8 decks), and native
scorecard camouflage. Honest risk: 40:1 variance — the E12-style ledger decides.

## M8a — Suit-aware card model, one engine (the invasive step; gate hard) ✅

21+3 pays on the 3-card poker hand of (player card 1, player card 2, dealer up):
flush / straight / three-of-a-kind / straight flush. Flushes need suits; straights
need J/Q/K distinct — the current `card = int 1..10` collapse cannot express
either. Plan: the Shoe deals full (rank 1–13, suit) cards; a `value()` collapse
feeds the *unchanged* blackjack engine (one engine — the side bet and trackers
see rich cards, the game logic sees values). Accepted consequence: shuffling 52
distinct cards changes every seed's dealt sequence, so pre-M8 runs do not replay
bit-for-bit (banked `data/*.json` stay valid as data; `ride-free-v1` preserves
exact reproducibility of the paper).
**Gate:** full test suite adapted and passing; all four validation batteries
re-pass; determinism under seed re-verified; throughput within ~2× of current.
**PASSED (2026-07-17):** 164 tests green (3 new raw-layer tests, zero
adaptations needed); all four batteries re-pass on the new sequences (h17
+0.31σ, s17 −0.06σ, ridefree −0.54σ, ridefree_woo −0.39σ vs references);
byte-identical replays under seed; reference path ~59k rounds/s (collapse is
shuffle-time, zero per-deal cost). Mechanism in DESIGN.md M8 decision record.

## M8b — 21+3 as configuration, validated before attacked ✅

`Rules` gains the 21+3 paytable as data (the flat 9-to-1 version pays every
winning category 9:1; encode as a category→payout map so the tiered variants are
configurations). The bet is placed BEFORE the deal (unlike insurance) — the
strategy hook is pre-round, which is exactly what a counting bet wants. Explicit
ledger fields per the insurance pattern.
**Gate (two independent references):** (1) exact fresh-shoe combinatorics for
each category probability (computable in closed form — tier-1 reference);
(2) the published Wizard of Odds house edge for the exact paytable and deck
count, looked up at milestone time — never from memory. Always-bet strategy in
csm mode must match both.
**PASSED (2026-07-17):** in-test exhaustive 6-deck enumeration equals WoO's
combination table exactly (SF 10,368 / trips 26,312 / straight 155,520 /
flush 292,896 of 5,013,320; EV −3.2386%); always-bet csm 6M rounds gives
−3.128% ± 0.121% (+0.92σ vs published −3.2386%), all category frequencies
within ±1.3σ; independent 62.4M-triple card-level check within ±1.8σ.
Implementation: `Rules.side_bet_21p3` + `side_bets.py` + `bet_21p3` hook +
`sb21p3_*` ledger fields + `cli sim --21p3`. 176 tests.

## M8c — The attack ✅ (E10–E12, 2026-07-17)

**Answered: yes — the flat-9:1 21+3 is beatable by suit composition.**
E10: exact closed-form pre-deal EV → ceiling +0.116u/100 rounds (pen .75) /
+0.269u (pen .85), late-shoe, orthogonal to hi-lo. E11a: exact decomposition
— suit 71% / rank 19% / interaction dead. E11b: quad-Q human system (four
suit counts, Σ excess² vs one analytic depth curve) captures 74–78% of the
ceiling with zero in-sample fitting. E12: verdict — wong-in at deep pen ≈
+$21/h per $100 side unit (N0 ≈ 1,200 h, ~$37k bankroll @5% RoR); seated
only at min-main:max-side; conditional on rack-card confirmation (paytable /
pen / no-CSM / entry policy). First positive verdict of the project; stacks
with hi-lo main play rather than being dominated by it.

Suit-aware CompositionTracker (per-(rank,suit) counts); exact hypergeometric
P(flush)/P(straight)/P(trips) as pre-deal signals; reuse the conditional-EV and
grid harness verbatim; EOR-style derivation if a linear count is wanted. Known
prior art: 21+3 is regarded as countable mainly via suit imbalance (flush
richness) — side-bet EV swings are large, so this may clear the bar Ride Free
missed. All experiments on fresh seeds (the `shoe_seeds` fix is in place);
per-experiment log discipline unchanged (E10+).

## M9a — Baccarat engine as data, validated before attacked ✅

Baccarat gets its own small engine (`baccarat.py` — decision record in
DESIGN.md): the drawing tableau is universal and lives in code; what varies
(decks, commission, the EZ push rule, Dragon 7 / Panda 8 paytables, shoe
retirement) is `BaccaratRules` data. Reuses `cards.Shoe`/`shoe_seeds` (the
1-10 value collapse is baccarat-native: tens count 0 via `card % 10` — no suit
layer needed, Dragon 7 and Panda 8 are rank-only). Bettor protocol mirrors the
strategy doctrine: the engine asks `main_bet` / `bet_dragon7` / `bet_panda8`;
no built-in bettor stakes a side bet unless configured.
**Gate (the M8b two-reference pattern):** (1) exact first-principles
enumeration (`exact_outcomes`, integer arithmetic over ordered 6-card
sequences, arbitrary composition — deliberately doubling as the M9b pre-deal
EV core) must equal WoO's published 8-deck combination table EXACTLY;
(2) always-bet csm simulation must match enumeration and published edges.
**PASSED (2026-07-17):** enumeration equals WoO exactly (banker
2,292,252,566,437,888 / player 2,230,518,282,592,256 / tie 475,627,426,473,216
of 4,998,398,275,503,360) and reproduces every published figure to print
precision (classic banker −1.0579%, player −1.2351%, tie −14.3596%, EZ banker
−1.0183%, Dragon 7 −7.6113% at p 0.022534, Panda 8 −10.1876% at p 0.034543);
2 × 2M-round always-bet csm shards (seeds 7500000001 / 7600000001) match —
see STATUS for per-shard σ. 208 tests green; determinism under seed verified.

## M9b — Exact pre-deal EV + the ceiling (the E10 analogue)

`exact_outcomes` on the live remaining composition each round → exact Dragon 7
/ Panda 8 / main-bet EV before the bet. Measure: +EV frequency and magnitude by
depth and penetration, the perfect-play ceiling in u/100 rounds, correlation
with the published linear count. Gate: calibration slope of realized on
predicted ≈ 1, published-count comparator reproduces WoO's ~0.6u/shoe within
noise. Performance note: fresh-shoe enumeration is sub-second, and late-shoe
(small-N) compositions enumerate faster still; late-shoe-only evaluation is
the fallback if per-round cost bites.

## M9c — Compression + the betting verdict (the E11/E12 analogue)

What carries the signal (rank decomposition; there is no suit term), how much
a human count captures (published counts as same-harness comparator rows —
the head-to-head E12 could only do cross-harness), then the ledger verdict:
u/100 observed rounds, $/h, N0, bankroll at 5% RoR — with baccarat's toll-free
sit-out structure. Panda 8 as a configuration rider; do the two bets' windows
collide?

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

**Gate (sanity, not certification) — met 2026-07-17:**
- Tracker counts exactly equal `shoe.remaining_composition()` at every point
  (invariant test). ✅
- Standard-game EV rises monotonically with hi-lo true count, ≈ +0.6%/TC (folk
  +0.5%/TC). ✅ See docs/EXPERIMENTS.md E1.

## M6a — The attack ✅ (results in EXPERIMENTS.md E1–E5)
Verdict: seated play loses under every system (best: RF count, −0.37% on money at
1-8 spread); wong-in at RF count ≥ +0.0125 with composition deviations earns ~+1.2%
per played round on ~6.6% of rounds; standard blackjack hi-lo remains the better
raw-EV target. Key artifacts: the RF EOR table, `rf_ev_shift()` (perfect linear
count), and the RF-L2 human count (BC 0.966). Original plan follows for the record.

### (original plan)
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
