# STATUS — read this first in a new session

Updated 2026-07-18. This is the resume-here document: current state, key numbers,
and the precisely-specified next step. Doc map at the bottom.

**Current state in one line: all three research questions are ANSWERED and
written up (Ride Free: dominated; 21+3: beatable, grind-scale; Dragon 7 +
Panda 8: beatable, the strongest verdict — `docs/ARTICLE_EZBAC.md`). No next
step is scheduled; remaining items are field checks on the felt and parked
options below.**

## ⚠ Deep-dive checkpoint (2026-07-17, late session) — read before trusting the numbers below

A full correctness audit + strategy hunt ran after this file's last update. Key
corrections (details: `docs/DEEP_DIVE_AUDIT.md`, new results: `docs/DEEP_DIVE_STRATEGY.md`):

- **Shoe reseeding flaw — FIXED in code**: `seed + shuffles` made "independent"
  shards replay 95–98% identical shoes (E3's +6.6σ is really ≈ +3σ; all
  shard-agreement claims tautological). `cards.shoe_seeds()` now derives
  non-sequential shoe seeds everywhere; 149 tests pass, determinism preserved.
  Pre-fix commands no longer reproduce bit-identical output (banked JSONs stay
  valid as data).
- **Wong-in headline corrected**: fresh 21M rounds give **+0.59% ± 0.09%** at
  rf_ev ≥ +0.0125 (published +1.04% was in-sample-selected). Engine itself is
  clean — new csm runs match published off-the-top EV (+0.5σ).
- **New certified system** (per played round, 6.6% of rounds): +0.59% bet
  selection + **+0.32% ± 0.06% deviations** (E8, repowered) + **+0.15% insurance**
  (E9 — insurance was never modeled!) ≈ **+1.06% ± 0.11%** (two ceiling terms).
- **E4b dominance question CLOSED** (hi-lo null at fixed rf_ev, 9M fresh rounds);
  free-double signal also subsumed (E6); **camouflage thesis refuted by
  measurement** (96.8% of wong-in rounds coincide with hi-lo TC ≥ +2).
- **Sit-out wonging**: seated toll shrinks −0.44% → −0.05% (breakeven perch, not
  profit). New data: `data/e6_*`, `e7_*`, `e8_*`, `e9_*`. Post-audit re-run of
  all four validation batteries: ALL PASS, tightest readings yet (RF 1.108% vs
  1.12 derived, −0.16σ; WoO 1.026% vs 1.04, −0.19σ). **Project concluded — see
  the section below.**
- **Insurance + deviations are now first-class** (same day): `Rules.insurance_offered`,
  strategy hook `take_insurance`, `CompositionPlayer` (tracker-fed, both features
  toggleable), simulator observer hooks; `cli sim` defaults BOTH ON
  (`--no-insurance --no-deviations` = published-edge comparator; `validate`
  always uses reference strategies). Insurance gate passed vs exact 6-deck EV.
  `cli deviations` gained `--window-threshold` / `--window-only` and true
  action-change counting. 161 tests pass.

## Where the project stands

Goal (Matt's framing): simulate Potawatomi's **Ride Free** blackjack (Free Bet
variant), first matching published EVs exactly, then beating the game with
"accounting systems" — count/composition-based betting. Milestones M0–M6 (the
Ride Free question) are ✅ done and CONCLUDED — see the verdict section below.
**M8 (the 21+3 side bet attack) is also ✅ complete as of 2026-07-17**: M8a
suit-aware cards, M8b the bet as validated configuration, M8c the attack
(E10–E12) — final verdict at the top of this file; write-up in
`docs/ARTICLE_21P3.md`. **Field intel (Matt, in person, 2026-07-17): the flat
9:1 21+3 IS on Potawatomi's floor** (alongside a separate 21+3 progressive and
"Top 3") — the verdict's most sensitive condition is confirmed; still to check:
pen/cut depth, CSM, entry policy, side max, decks, H17/S17.
**M9 IS ✅ COMPLETE (2026-07-17): the Dragon 7 + Panda 8 attack — the
project's strongest verdict.** M9a engine gate-passed (enumeration == WoO's
combination table to the integer); M9b exact ceiling (E13): combined D7+P8
**+1.24u/100 rounds at cut-card-14, ~4.4× the 21+3 ceiling, toll-free**;
M9c verdict (E14): **two written counts capture ~90% → +$92/h per $100 unit
heads-up, N0 ≈ 582h, ~$81k bankroll (at $25 caps: +$23/h on $20k, still
beating all of 21+3)**. Three independent published cross-validations along
the way (combination table; WoO Dragon count 0.592 vs 0.597 u/shoe; WoO
Panda count 0.241 vs 0.238). Remaining: EZ-table field items on the rack
card below; optional write-up.

## Where the attack stands (E1–E4c, see EXPERIMENTS.md)

The arc so far: naive event-betting refuted (E1) → pair-richness beyond hi-lo
confirmed at +6.6σ (E2/E3) → **hi-lo shown to be the wrong count for this game;
game-specific EORs derived and validated against Griffin (E4a)** → the pair effect
is fully subsumed by the derived RF count (E4b, null at −0.6σ) → betting verdict
(E4c): **RF count is the best system but seated play still loses (−0.37% on money
at 1-8 spread); standard blackjack hi-lo next door wins (+0.23%). The only
profitable Ride Free mode found: wong-in at RF count ≥ +0.0125 → 6.6% of rounds at
+1.04% EV** (standard offers ~3× the volume at equal quality — RF's residual value
is camouflage, not raw EV).

Key artifacts: `counting.rf_ev_shift()` — the first game-specific linear count for
Free Bet blackjack, denominated directly in predicted EV (RF EORs vs standard:
tens halved, ace ≈ 3× the ten, 3/4/5/7 collapse, 8 flips negative) — and
**RF-L2**, the human-playable level-2 count (A −2, 5 +2, 2/3/4/6 +1, T −1;
balanced; BC 0.966). Head-to-head at ~6% wong-in frequency (same seed): hi-lo
+0.63%, RF-L2 +0.72%, perfect count +0.74% per played round — the human count
captures essentially all of it. Best balanced level-1 for this game is hi-lo
itself (BC 0.910). Publishable write-up: `docs/ARTICLE.md`.

## Key numbers (all measured, seeds in EXPERIMENTS.md / git log)

| Quantity | Value |
|---|---|
| Standard 6d H17 house edge (validated vs published 0.62%) | 0.64% |
| Standard 6d S17 (vs published ~0.40%) | 0.47% |
| RIDE_FREE (Potawatomi, no resplit aces) house edge, OptimalStrategy | 1.07% (target 1.12% derived; gate passed) |
| RIDE_FREE_WOO (resplit aces) vs published 1.04% | 0.99% (passed) |
| Resplit-aces config difference (vs WoO's published 0.08%) | 0.081% |
| Dealer 22 rate (vs WoO 0.073536) | 7.354% |
| Ride Free per-round std dev | ~1.067 |
| Free doubles / free splits / dealer-22 pushes (% of rounds) | 13.6% / 4.9% / 6.1% |
| Hi-lo EV slope: standard vs Ride Free | ~+0.6%/TC vs ~+0.45%/TC |
| corr(p_free_double, hilo_tc) / corr(p_pair, hilo_tc) | −0.937 / −0.724 |
| Naive event-frequency betting (E1) | REFUTED — both signals invert |
| Within-TC pair slope, Ride Free (E2+E3) | **+0.626% ± 0.094% / 0.01 p_pair** |
| Same, standard-game control | +0.05% ± 0.24% (null) |

## M6a is answered (E5 done): the final Ride Free verdict

**Best-known system:** back-count with the RF count, wong-in at rf_ev ≥ +0.0125,
deviate by composition → **~+1.2% per played round on ~6.6% of rounds.** Seated
play with realistic spreads loses (−0.30% even with deviations). Deviations are
worth +0.12% ± 0.05% overall (perfect-information ceiling; 2.1% of rounds change).
Standard blackjack hi-lo still beats it on raw EV (~3× the playable volume at equal
quality); Ride Free's differentiator is camouflage.

## M8a DONE (2026-07-17): suit-aware card model, gate passed

The project is REOPENED for a new question: **can the 21+3 side bet (9-to-1
paytable) be beaten by suit/rank composition?** Full ladder in ROADMAP.md M8a–c.

**M8a is complete.** Implementation (mechanism recorded in DESIGN.md M8
decision record): raw card = `(rank 1–13, suit 0–3)` tuple; `cards.value()`
collapses to blackjack value; `Shoe` shuffles the 52·decks distinct raw cards
and collapses **once at shuffle time**, so `deal()` still returns value ints —
engine, hand valuation, strategies, trackers all untouched. Raw cards surface
via `Shoe.raw_dealt()` (raw twin of `dealt_cards()`); in M8b the engine reads
raw positions pos/pos+1/pos+2 (player c1, dealer up, player c2) from the
pre-deal snapshot. `validation.InfiniteDeckShoe` stays value-only.

**Gate results (all passed):**
- 164 tests green (161 prior — none needed adaptation, no test hardcoded a
  shuffled sequence — plus 3 new raw-layer tests in `test_shoe.py`).
- All four `validate` batteries re-pass on the new dealt sequences: h17
  0.646% vs 0.62 (+0.31σ), s17 0.395% vs 0.40 (−0.06σ), ridefree 1.079% vs
  1.12 (−0.54σ), ridefree_woo 1.010% vs 1.04 (−0.39σ); every dealer-bust /
  22-rate / natural check within ±1.9σ.
- Determinism: same (rules, seed, strategy) → byte-identical sim output.
- Throughput: reference path 500k rounds in ~8.5s (~59k rounds/s) — the
  shuffle-time collapse costs nothing per deal; well inside the ~2× budget.

Seeds 6300000001–6300000003 consumed for gate checks (from the 6.3e9+ block).

## M8b DONE (2026-07-17): 21+3 as configuration, gate passed on both references

Implementation (insurance pattern throughout): `Rules.side_bet_21p3` is a
category→payout tuple (`PAYTABLE_21P3_9TO1` = flat 9:1; tiered variants are
configurations); the bet is staked PRE-deal via the strategy hook
`bet_21p3(rules)` (no built-in strategy stakes it, so published-edge
validation is untouched); the engine settles from the three raw cards
(pre-deal snapshot positions pos/pos+1/pos+2) in `side_bets.py`
(`classify_21p3`, precedence SF > trips > straight > flush; suited trips are
trips, matching WoO; ace high AND low). Ledger: `RoundResult.sb21p3_stake /
sb21p3_profit / sb21p3_category`; Metrics tracks per-category counts.
`strategy.AlwaysSideBet` wraps any strategy for the always-bet comparator;
`cli sim --21p3` enables it. 176 tests green (12 new in `tests/test_21p3.py`).

**Gate (two independent references, both matched):**
1. **Tier-1 closed form:** exhaustive 6-deck enumeration (in-test, first
   principles) equals WoO's combination table EXACTLY — SF 10,368; trips
   26,312 (incl. suited trips); straight 155,520; flush 292,896 (their
   236,736 + 56,160 rows); total C(312,3) = 5,013,320; EV −3.2386%.
2. **Published edge (WoO, fetched 2026-07-17, flat 9:1 six decks: −3.2386%):**
   always-bet csm, 2 × 3M rounds (seeds 6400000003, 6500000001) combined:
   **−3.128% ± 0.121% (+0.92σ)**; combined categories vs closed form: SF
   +0.02σ, trips +0.68σ, straight +1.21σ, flush +0.05σ. Cross-check at the
   card layer: 62.4M disjoint shuffled-shoe triples (exchangeability ⇒ exact
   top-3 marginal; empirical shoe-level σ) — every category within ±1.8σ.

Seeds consumed: 6.4e9 block (gate + tests), 6500000001, 6600000001–2 (M8b);
6700000001, 6800000001 (E10); 6900000001, 7000000001 (E11a); 7100000001,
7200000001 (E11b). Next unused block: **7.3e9+**.

## M8c IN PROGRESS: E10 done — 21+3 IS beatable at the ceiling

**E10 (2026-07-17, EXPERIMENTS.md):** exact closed-form pre-deal EV
(`side_bets.ev_21p3` + `counting.RawCompositionTracker`, `cli sbev`) says the
flat-9:1 21+3 clears the bar Ride Free missed:
**pen 0.75 → +EV on 4.6% of rounds (mean +2.5%) = +0.115u/100 rounds;
pen 0.85 → 7.1% of rounds (mean +3.9%) = +0.276u/100** per unit of side
stake. Signal is late-shoe (25% of rounds +EV at 1 deck left) and essentially
orthogonal to hi-lo (corr ≈ −0.08). Calibration slope 1.03 ± 0.07 (deep run):
the calculator prices depleted shoes correctly end to end.

**E11a DONE (2026-07-17, EXPERIMENTS.md):** exact decomposition
EV = B(depth) + S(suit) + R(rank) + X(interaction), each term closed-form
(`sb_ev_components`, `cli sbdecomp`). Verdict: **suit 70–72% of variance,
rank 17–21%, interaction ~0.2% (dead — additive rule captures 99.8% of the
ceiling)**. Suit-only selection captures 73% (pen .75) / 78% (pen .85) of
ceiling value; rank-only alone is worthless (4–6%). Depth is first-class:
B drifts −3.24% → −13.9% (0.5 decks) while sd(S) grows to 11.9% — per-depth
thresholds required. Four per-suit counts compute B+S EXACTLY, so the
suit-only row is that family's ceiling; the last ~27% needs rank
concentration (mostly the straight term).

**E11b DONE (2026-07-17, EXPERIMENTS.md):** human trackers scored with fully
analytic parameters (`cli sbtrack`). **Winner: quad-Q — four dealt-per-suit
counts, bet when Σ(remaining excess)² clears one memorized depth curve —
captures 74% (pen .75, +0.086u/100) / 78% (pen .85, +0.211u/100) of the
exact ceiling, equal to the exact 4-suit-family bound** (shape approximation
free). Adding the best static linear rank count (13-tag second count) → 81%;
the last ~19% is the quadratic rank term, computer-only. Intuitive
max-excess rules capture only ~half the suit value (two-moderate-suit states
matter). Index curve: T1 = 4.0 / 5.9 / 8.7 / 11.2 / 13.5 excess cards at
0.5 / 1 / 2 / 3 / 4 decks left; T_Q = 4/3·T1².

## M8 FINAL VERDICT (E12 done, 2026-07-17): 21+3 is beatable — first positive verdict

**The 21+3 flat-9:1 side bet (6 decks) is genuinely beatable by suit
composition.** Ledger arithmetic in `data/e12_verdict.py` (E12,
EXPERIMENTS.md). Operating point: **quad-Q wong-in at pen 0.85 ≈ +0.206
side-units per 100 observed rounds ≈ +$21/h per $100 side unit (σ ≈ $716/h,
N0 ≈ 1,200 h, ~$37k bankroll for 5% RoR)**. Seated play viable only at
min-main:max-side stakes AND deep pen (+$11.5/h at $15:$100, pen 0.85);
pen 0.75 is thin (wong-in +$8/h, seated dead — breakeven 7.4:1). Unlike Ride
Free, this does NOT lose to the game next door: it is orthogonal to hi-lo
(corr −0.08) and stacks with a counted main game.

**Verdict conditions (rack-card checklist, by sensitivity):** flat 9:1
paytable (Xtreme tiers → nothing transfers); penetration ≥ ~0.80; no CSM;
mid-shoe entry allowed (or ≥1:3 main:side stakes); 6 decks. Idealizations on
record: hole card eventually visible; 100 rounds/h heads-up.

## M9a DONE (2026-07-17): baccarat engine as data, gate passed on both references

Target rationale (scouting session, same day): the Dragon 7 (banker
three-card-7 win, 40:1, 8-deck HE 7.611%) has published prior art — WoO's
simple count (8/9 = +2, 4–7 = −1, bet at TC ≥ +4) makes 0.597u/shoe ≈
0.73u/100 hands at cut-card-14 penetration, ~3.5× quad-Q's 0.211u/100 — but
NO published exact-composition ceiling: the same gap M8 closed for 21+3.
Structural edge over 21+3: **no main-bet toll** (sitting out rounds is normal
baccarat), **deepest standard penetration in the house** (~14–16 cards from
the end ≈ 0.96), native scorecard camouflage, rank-only signal (no suit
layer). Honest risk: 40:1 variance — E12-style ledger will decide. Panda 8
(player three-card-8 win, 25:1, HE 10.188%) is a free configuration rider.

Implementation (`baccarat.py`, decision record in DESIGN.md): separate small
engine — the universal drawing tableau in code, everything that varies
(`BaccaratRules`: decks, commission, EZ three-card-7 push, paytables,
shoe-end modes with the same csm-comparator semantics) as data; reuses
`cards.Shoe`/`shoe_seeds` (ten-values collapse to 0 via `card % 10` — the 1-10
value model is baccarat-native); engine-asks/bettor-answers protocol
(`main_bet`/`bet_dragon7`/`bet_panda8` + observer hooks); per-wager ledger.
`exact_outcomes(composition)` — integer enumeration over ordered 6-card
sequences, arbitrary composition — is BOTH the gate reference and the future
M9b pre-deal EV calculator (one audited function, no second implementation).
CLI: `cli bac` (sim + self-check vs enumeration), `cli bacexact`.

**Gate (two references, both matched, 2026-07-17):**
1. **Exact enumeration == WoO's published 8-deck combination table to the
   integer**: banker 2,292,252,566,437,888 / player 2,230,518,282,592,256 /
   tie 475,627,426,473,216 of 4,998,398,275,503,360; every published figure
   reproduced to print precision (classic banker −1.0579%, player −1.2351%,
   tie 8:1 −14.3596%, EZ banker −1.0183%, Dragon 7 −7.6113% @ p 0.022534,
   Panda 8 −10.1876% @ p 0.034543). Fresh-shoe enumeration runs sub-second.
2. **Simulator vs enumeration + published edges**: always-bet
   (banker + D7 + P8) csm, 2 × 2M rounds (seeds 7500000001 / 7600000001) —
   16 checks (5 frequencies + 3 edges per shard), worst |z| = 1.70σ (tie
   freq, shard 2); Dragon 7: freq −0.00σ / +0.36σ, edge −7.6127% / −7.4548%
   vs exact −7.6113%. 208 tests green (22 new in `tests/test_baccarat.py`,
   incl. tableau-matrix unit deals and EZ/classic settlement); determinism
   under seed verified.

## M9b DONE (2026-07-17): the ceiling is 4.4× the 21+3 one, and toll-free (E13)

**E13 (EXPERIMENTS.md):** exact pre-deal D7/P8 EV every round
(`baccarat.fast_outcomes` — multiset-table restructuring of `exact_outcomes`,
bit-identical integers differentially tested, 2.4ms/call; `cli bacev`), 600k
rounds across pens 0.966/0.95/0.90. Headlines:
- **Combined Dragon+Panda exact ceiling at cut-card-14 (pen 0.966, the
  baccarat norm): +1.215u/100 observed rounds ≈ +0.99u/shoe** (D7 +0.845,
  P8 +0.370) — 4.4× the 21+3 pen-.85 ceiling, with no main-bet toll.
- **Pipeline cross-validated against WoO independently**: their practical
  count scored in our harness gives +0.592 ± 0.004 u/shoe vs their published
  0.597. The simple count captures 85.8% of the D7 ceiling (corr +0.905) —
  headroom is ~14% of D7 plus ALL of P8 (corr(d7,p8) +0.41).
- Depth: D7 ignites ~6.5 decks out; last half-deck P(+EV) ≈ 36–40% at mean
  +12–19%. Pen 0.95 → combined +0.980u/100; pen 0.90 → +0.654u/100.
- Calibration: pooled binomial z over 600k rounds — d7 −1.89, p8 +1.57
  (watched; predictor is exact-by-construction, M9c samples will settle it).

Seeds consumed: 7300000001–6 (tests + calibration), 7400000001 (M9a
calibration), 7500000001 / 7600000001 (M9a gate), 7700000001–8200000001
step 1e8 (E13 shards). **Next unused block: 8.3e9+.**

## M9c DONE (2026-07-17): the verdict — two written counts, ~90% of ceiling, +$92/h (E14)

**E14 (EXPERIMENTS.md):** Panda 8 prior art checked — WoO appendix 8 has a
count (0.238u/shoe); scored same-harness we get 0.241 ± 0.011 (third
independent pipeline cross-validation). Our exact D7 EORs ×10 reproduce
WoO's optimal System 1 digit-for-digit; P8 EORs reproduce their appendix
tags' shape. Capture at cut-14 (analytic thresholds, zero fitting): **d7
linear-EOR 92.3% / p8 83.2% → the two-count pair captures ~90% of the
+1.244u/100 combined ceiling = +1.155u/100.** Single-count play refuted:
Panda on Dragon triggers = −4.7%/bet (−147% capture). Ledger
(`data/e14_verdict.py`, toll-free): **+$92/h per $100 unit at 80 rounds/h,
N0 ≈ 582h, ~$81k bankroll at 5% RoR; $25 cap → +$23/h on $20k — still
beats all of 21+3 (E12: $21/h, $37k, toll, 1,200h).** ~4× the 21+3 hourly
at half the N0. Baccarat deals face-up (no hole-card idealization); pace
and burn-card idealizations on record in E14.

**M9 IS COMPLETE. The Dragon 7 + Panda 8 pair is the project's strongest
verdict.** Conditions: 40:1/25:1 paytables, real shoe, cut ≥ ~0.95, side
maxes ≥ $25, two written counts (scorecards are normal at baccarat).

**E14b addendum (playable card + operating modes, 2026-07-17/18):** integer
"paper" tags must be BALANCED (naive rounding drifted −4/deck and killed the
TC triggers — lesson asserted in code). Verified card: Dragon tags
A+1/2−1/3−1/4−3/5−3/6−3/7−4/8+5/9+5/T+1 @ TC≥10 → 89.8% capture; Panda =
WoO appendix tags @ TC≥11 (already at the integer frontier, 79.1%). Paper
pair ≈ +1.11u/100 ≈ 87% of ceiling. **Operating modes (ledger):** heads-up
with $10 min main every round (required when alone; Matt confirmed sitting
out is fine at Potawatomi when others play) → toll is 9% of gross, pace
doubles: **~$101/h at 100 r/h vs ~$50/h crowded**. Side ≤ main cap (matched
on triggers): −13% → $88/h; capped $25 side max: $22/h on ~$25k — still
matches all of 21+3. Only a flat matched main all shoe kills it (never
required). Full write-up: **`docs/ARTICLE_EZBAC.md`** (done 2026-07-18).

Seeds consumed (M9c): 7300000007 (test), 8300000001 / 8400000001 (pen .966),
8500000001 (pen .95), 8600000001 (E14b broken-row run, discarded),
8700000001 (E14b verification). **Next unused block: 8.8e9+.**

## NEXT STEPS (M8 research complete; field + polish items remain)

1. **Field checks (Matt, at the felt — no rack-card homework left):** 21+3
   flat 9:1 CONFIRMED on the floor (2026-07-17; progressive and "Top 3" also
   present); sit-without-betting at baccarat CONFIRMED fine (2026-07-17).
   Remaining, readable off the felt in a minute: the EZ table's Dragon/Panda
   paytables (40:1/25:1 assumed), side-bet maxes, cut-card depth — and, only
   if 21+3 is ever played, its pen/CSM/entry policy and H17/S17.
2. Optional realism passes if the field checks pass: visible-cards-only
   tracker (drop hole-card assumption — expect ~nil), full-table
   cards-per-round model, tiered-paytable re-derivation (pure configuration:
   rerun sbev/sbdecomp/sbtrack with the actual paytable).
3. ~~Optional write-up~~ **DONE**: `docs/ARTICLE_21P3.md` (the full M8 arc:
   engine → gates → ceiling → decomposition → quad-Q → verdict → Jacobson
   comparison). Open editorial item if ever wanted: a same-harness head-to-head
   of Jacobson's spread count inside `sbtrack` (currently a cross-harness
   comparison, flagged honestly in the article).
4. Combined-play measurement (parked; would upgrade the E12 "stacks with
   hi-lo" claim from arithmetic to measurement): simulate hi-lo-spread main +
   quad-Q side in one run; needs a hi-lo betting simulator class the repo
   doesn't have yet. E12's seated toll assumed flat-bet basic strategy
   (−0.64%/round) — with a counted main game the toll flips to a profit leg
   (E4c: +0.23% on money at 1–8 spread, standard game).

Parked/refuted (ChatGPT list disposition): rank×suit interaction models
**refuted by E11a** (<0.2% of variance); rank-adjacency beyond the straight
term subsumed in R; "strange regime" hunts unnecessary (exact EV prices all
regimes); dealer-upcard effects empty (third exchangeable card). Realism
variants for later: visible-cards-only tracker (drop the hole-card
assumption), burn cards, paytable variants (Xtreme tiers) as configurations.

Known consequences, accepted in advance: pre-M8 seeds do not replay
bit-for-bit (52-card shuffle ≠ collapsed shuffle) — the exact v1 artifact is
preserved at git tag **`ride-free-v1`**; banked `data/*.json` remain valid as
data. Seed hygiene: `cards.shoe_seeds()` everywhere; fresh base seeds spaced
≥ 1e8.

## RIDE FREE QUESTION CONCLUDED (Matt, 2026-07-17)

The research question is answered and re-certified on clean seeds: **Ride Free is
beatable only by wong-in at rf_ev ≥ +0.0125 (~6.6% of rounds) for ≈ +1.0% ± 0.11%
per played round at the perfect-information ceiling (bet +0.59 / deviations +0.32
/ insurance +0.15) — and that is strictly dominated by standard blackjack next
door (~3× the volume at ~+1.1% with plain hi-lo), with the camouflage
differentiator refuted by measurement (97% of RF entries coincide with hi-lo
TC ≥ +2).** Human-capture distillation deliberately not pursued: no reason to
optimize execution of the second-best game.

Formerly-candidate items, now all parked with no successor scheduled: practical
distillation / RF deviation index, bankroll & hourly analysis, resplit-aware EOR
re-derivation (retired — E7 closed the dominance question), hi-lo certification
(M6c), Rust core (M7). Still outstanding if ever revisited: apply the
DEEP_DIVE_AUDIT.md prose corrections to EXPERIMENTS/ARTICLE (editorial), and the
audit's unverified test-coverage backlog.

## Superseded plan notes (E4, done)

Matt's insight driving it: **classical hi-lo tags are standard-blackjack EORs; Ride
Free's effects of removal must differ** (5s/6s feed free doubles; dealer-22 push is
made of tens and devalues ten-rich standing — the blunted +0.45%/TC slope is the
symptom). Plan:

- **E4a — derive EORs from the calculator.** Parameterize `player_ev.EVCalculator`'s
  rank weights (currently hardcoded infinite-deck `_W = 4/13 tens`). Compute
  full-game EV(weights) = Σ over (c1, c2, up) deal probabilities × best-action EV
  (naturals and dealer-natural terms included). EOR_r = EV(one card of rank r
  removed per deck) − EV(baseline). **Validate on the standard game first** — the
  derived standard EORs must reproduce published (Griffin) values, looked up at run
  time, before trusting the Ride Free ones. Normalize RF EORs into tags → the first
  Ride-Free-specific linear count ("RF count").
- **E4b — purify the pair claim.** Add the RF count to `experiments.SIGNALS`; rerun
  the (RF-count × p_pair) grid. Expect: RF count beats +0.45%/TC; pair slope
  conditional on RF count shrinks somewhat but stays significant (it is a quadratic
  concentration signal no linear count can express — but a better linear count may
  claim part of what hi-lo missed).
- **E4c — ramp arithmetic, no new sims.** From banked grids (`data/*.json`):
  optimal (count × pair) bet ramp vs count-only vs classical hi-lo;
  E[profit] = Σ P(bin)·bet(bin)·EV(bin). Deliver: edge, variance, bankroll, spread
  per system — the first full "accounting system" verdict.

## Operational notes (hard-won, do not relearn)

- **Throughput:** Ride Free + OptimalStrategy ≈ 7k rounds/s; standard + BasicStrategy
  ≈ 10–12k rounds/s. Background Bash commands are killed at 10 minutes and buffered
  stdout is lost (use `python -u`; expect nothing from a killed run).
- **Sharding pattern:** cap runs at ~3M rounds (Ride Free) per background task; for
  bigger samples run parallel shards with distinct seeds and `--json` dumps, then
  `ridefree.cli combine data/*.json`. Bin stats are additive.
- **Seed hygiene:** used so far: 20260717 (validation), 31337 (E1), 4242 (E2),
  1111/2222/3333/4444 (E3). Replications must use fresh seeds.
- **Cut-card effect:** cut_card mode reads ~+0.03–0.07% above published
  (combinatorial) figures; csm mode matches published almost exactly. Gates were run
  in cut_card mode; csm is the clean comparator for published numbers.
- **Rust trigger (M7):** fires when sweeps need >(few×10M) rounds routinely; Python
  reference is the differential-test oracle.

## Commands cheat sheet

```
uv run pytest -q                                   # 161 tests
uv run python -m ridefree.cli demo --rules ridefree --seed 44 --hands 6
uv run python -m ridefree.cli sim --rules ridefree --rounds 2000000
uv run python -m ridefree.cli validate --rules {h17,s17,ridefree,ridefree_woo}
uv run python -m ridefree.cli signals --rules ridefree --rounds 3000000
uv run python -m ridefree.cli grid --rules ridefree --row hilo_tc --col p_pair \
    --rounds 3000000 --json data/out.json
uv run python -m ridefree.cli combine data/e2_ridefree_grid.json data/e3_shard*.json
uv run python -m ridefree.cli sim --rules h17 --shoe-mode csm --21p3 \
    --no-insurance --no-deviations           # 21+3 published-edge comparator
uv run python -m ridefree.cli sbev --rounds 2000000 [--penetration 0.85]
uv run python -m ridefree.cli sbdecomp --rounds 2000000   # EV = B+S+R+X shares
uv run python -m ridefree.cli sbtrack --rounds 2000000    # human trackers scored
uv run python data/e12_verdict.py                         # the E12 ledger
uv run python -m ridefree.cli bacexact                    # exact baccarat table
uv run python -m ridefree.cli bac --shoe-mode csm --rounds 2000000 \
    --dragon7 1 --panda8 1                    # M9a gate: sim vs exact + published
```

## Open items

- Rack card (Matt): confirm decks and H17/S17 at Potawatomi (assumed 6d H17); also
  whether free doubles are hard-only (assumed; `free_double_soft_allowed` toggle).
- Playing deviations layer (M6a step, after E4): EVCalculator with live-composition
  weights; motivating case 5,5 split-vs-double flip in small-card-rich shoes.
- Cut-card effect precise measurement via common random numbers (parked).
- Full hi-lo published-table certification (M6c, parked).

## Doc map

- `CLAUDE.md` — working doctrine (rules-as-data, one engine, determinism, ledger).
- `docs/DESIGN.md` — architecture, money model, shoe-end modes, counting design,
  suit-aware card / M8 decision records, Rust decision record.
- `docs/ROADMAP.md` — milestones M0–M8 with gates and results.
- `docs/EXPERIMENTS.md` — experiment log E1–E12 (newest first), reproducible.
- `docs/ARTICLE.md` — the Free Bet (Ride Free) write-up.
- `docs/ARTICLE_21P3.md` — the 21+3 side bet write-up (M8 arc, quad-Q, verdict).
- `docs/ARTICLE_EZBAC.md` — the Dragon 7 / Panda 8 write-up (M9 arc, the
  two-count card, the toll-free ledger, verdict).
- `src/ridefree/baccarat.py` — the M9 engine (rules, tableau, exact
  enumeration, simulator); gates in `tests/test_baccarat.py`; ledger
  `data/e14_verdict.py`.
- `docs/STATUS.md` — this file. Update it at every session checkpoint.
- `data/` — banked grid JSONs (E2, E3 shards; additive bin stats) and
  `e12_verdict.py` (the E12 ledger arithmetic).
