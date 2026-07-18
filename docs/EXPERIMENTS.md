# Experiment log

Newest first. Every experiment is reproducible from (git commit, CLI command, seed).

## E18 — Collapsing the card: the locked crouch15-2r (2 rungs, insure at max bet, walk line at zero)

**Date:** 2026-07-18 · **Question (Matt, after drilling the E17 card):** the
leave triggers absurdly early, and the rungs at RC 0/+2/+5 sit too close
together — how far can the card be collapsed without giving up too much? And
what do these numbers assume about insurance?

**Method (three parts, no new engine code):**

1. **Collapse menu — arithmetic over the banked E17 bins** (48M rounds,
   `data/e17_h17_ins_p75_s*.json`). New wrinkle: the bins' `ins_profit`
   attribution makes insurance separable per RC bin, so "no insurance below
   RC X" is priced by stripping the overlay from bins below the threshold
   (the banked overlay is composition-exact ⇒ these insurance terms are
   ceilings). $15 floor throughout (the honest crouch15 floor toll ≈ −$4/h
   vs the $10-table rows: the "Red 7 ≈ ×0.935" shorthand in E17/STATUS
   overstated the $15-floor hourly by ~$5 — corrected here).
2. **Practicality measurement** — 8,000 real shoes (343,662 engine rounds,
   heads-up BasicStrategy, seed base 14200000001): leave-trigger frequency,
   timing, and rung churn under the absorbing-walk reading.
3. **Live certification of the literal locked card** — `data/e18_run.py`,
   6 × 2M rounds (seed bases 14300000001–14800000001 step 1e8):
   chart play + bet-by-RC + pointwise sit-out at the leave line + the HUMAN
   insurance rule (insure iff decision-time visible RC ≥ threshold; hole not
   counted). This measures what the exact-insurance bins cannot: the realized
   value of the threshold rule. Verdict: `data/e18_verdict.py`.

**Findings:**

- **The algebra behind both complaints:** RC ≈ decks_remaining × (TC − 2)
  (pivot scale). Fixed off-pivot thresholds are depth-blurred: the −14 leave
  = TC −0.4 with 5.5 decks left (hair-trigger) but TC −5 at 1 deck (never).
  Measured: leave −14 fires in **73% of shoes, 3.4 walks/h, median exit
  round 4, 81% of walks within 10 rounds** — impractical, and the ledger's
  preference for shallow leaves prices exits as free (real walks cost 2–5
  dead minutes ≈ $7–17/h at that rate, plus optics). Leave −18: 37% of
  shoes, 1.7 walks/h, median round 10.
- **Insurance concentrates at the top:** of the +$7.67/h exact-insurance
  ceiling on the 3-rung card, +$5.70 sits at RC ≥ +5 and only +$1.48 in
  +2..+4. Tying insurance to the max-bet rung costs ~$2/h ceiling and
  removes a real failure mode (the old "insure at +2" takes theoretically
  bad insurance early-shoe, TC +2.4 < the true +3 index; the max-bet rung
  implies TC ≥ +3 at every depth).
- **The collapse menu** (bins, $15 floor, 200 r/h, pen .75): current 3-rung
  $54.70/h on $29.9k = ref; 2-rung ($100 at pivot, $200+ins at pivot+4)
  94.7% at the same bank; 1-rung $150 81–85%; **1-rung $200 at the pivot
  115.9% but $41.5k bank** (the growth-path card: simplest AND richest once
  the roll clears ~$42–52k; play-all version needs $51.8k and still keeps
  94%). Churn: 20 → 15 → 10 bet changes/hour for 3/2/1 rungs.
- **THE LOCKED CARD (Matt's pick + a cosmetic slide so no number is ever
  negative — the walk line sits AT zero): start each shoe at +6; count ≤ 0
  → walk; $100 at 18 (the depth-exact pivot, TC +2); $200 AND insure at 22.**
  Pivot-scale equivalents: IRC −12, leave ≤ −18, jump 0, max/ins +4.
- **Certification (12M live rounds):** chart-only live +$43.16 ± 4.18 vs bin
  prediction +$39.00 ± 2.08 (**z = +0.89**); rung occupancy matches to
  ≤1.3σ in all four bands (sit-out 7.46% vs 7.47% predicted); avg bet
  $35.39 vs $35.37. **The human insurance rule realizes +$4.67/h = 73% of
  the +$6.40 exact ceiling.** Certified operating numbers: **≈ +$44/h ± 2
  (best estimate: bins chart + measured insurance), σ ≈ $72/round, N0 ≈
  500h, bankroll ≈ $36k at 5% RoR** (live-sample sizing $32.8k; quote $36k
  from the combined estimate). Idealizations unchanged from E16/E17
  (pointwise exits, 200 r/h heads-up, pen .75 assumed, no burn cards).

**E18b addendum — the never-leave variant, certified (Matt's weekday-reality
question: finding a fresh shoe after every walk is a real cost the pointwise
model ignores).** Same runner/verdict with `variant=playall`
(`data/e18b_live_s01..06.json`, 6 × 2M rounds, seeds 15.0e9–15.5e9):
live total **+$46.69 ± 4.19/h** vs with-leave +$47.83 ± 4.18; chart-only
+$41.14 ± 4.20 vs bin prediction +$33.16 ± 2.09 (z = +1.70; second
consecutive live run above prediction — within tolerance, direction noted);
insurance realized +$5.55/h = 87% of ceiling on these seeds (pooled with
E18: ~80%, ≈ +$5/h). **The leave's exact same-shoe paper value is $5.83/h;
walk friction (1.7 walks/h × 2–5 dead min) refunds $2.50–6/h of it — net
cost of never leaving ≈ $0–3.5/h. Verdict: the walk line is ADVISORY** —
weekday mode plays every round (best estimate ≈ +$40/h ± 2, N0 ≈ 550–660h,
~$36–40k at 5% RoR); walk at zero only when a fresh shoe is genuinely
adjacent. Wong-mode context measured the same day (scratchpad, 4k shoes,
seed 14.9e9): 85% of jump rounds come after 2+ decks dealt; 60% of shoes
ever ripen (median first jump bet at round 24, then ~12 jump rounds) — the
card's top half doubles as a busy-room back-count play (~$65/h per 200
observed rounds on $23k; pace-scaled $20–29/h).

**Artifacts:** `data/e18_run.py`, `data/e18_verdict.py` (both take a
`variant` arg), `data/e18_live_s01..06.json`, `data/e18b_live_s01..06.json`;
the card as data in `src/ridefree/trainer/card.py::CROUCH15_2R` (the trainer
default). Seeds consumed: 14.2e9 (timing study), 14.3e9–14.8e9 (E18 shards),
14.9e9 (wong depth), 15.0e9–15.5e9 (E18b shards).
**Next unused block: 15.6e9+.**

## E16 — Classic blackjack next door: the cover-vs-money ledger (real dollars, real ramps)

**Date:** 2026-07-18 · **Question (Matt):** what does MY standard game actually
pay, with a real spread in real dollars — and is there any play with "no heat"
cover (flat-looking bets) and a decent hourly? Sub-question (the holy grail):
can indexes rescue negative counts?

**Method.** Three new harnesses (all `(rules, seed, strategy)`-deterministic):

1. `cli curve` (`experiments.run_tc_curve`): flat-bet pass binning per-round
   profit by pre-deal hi-lo TC (integer bins clamped ±8), banking mean,
   second moment (variance is free), within-bin mean TC, and the insurance
   attribution. Three playing arms — `basic` (OptimalStrategy, no insurance),
   `ins` (+composition-exact insurance), `full` (+composition deviations).
   JSON dumps additive; `cli curvecombine` pools shards.
2. `cli deviations --json` (extended): the E5/E8 paired-differential harness
   now bins each round's paired profit diff by hi-lo TC — per-TC deviation
   value at ~100× the precision of independent arms.
3. `cli ramp` (`experiments.run_ramp`): a LIVE betting simulator — bet(tc)
   chosen pre-deal from the tracked count via a configurable step ramp;
   rounds played at bet=1 and profit scaled (profit is exactly linear in the
   initial bet, so scaling is exact and the card stream is ramp-invariant).
   Bet 0 = sit-out (cards still flow: the table-with-others model). This is
   the "hi-lo betting simulator the repo doesn't have yet" (old STATUS item).

`data/e16_ledger.py` then prices any ramp × arm from the banked bins (EV,
variance, corr(bet,TC), $/h, σ/h, N0, 5%-RoR bankroll — unit $, pace, RoR,
game, pen all configurable) — simulate once, price every betting pattern.

**Data banked** (`data/e16_*.json`): h17 pen .75 — basic 10×6M (seeds
8.9e9–9.8e9 step 1e8), ins 10×6M (9.9e9–10.8e9), paired deviations 8×1M
(10.9e9–11.6e9); s17 pen .75 — basic 4×6M (11.7e9–12.0e9), ins 4×6M
(12.1e9–12.4e9); h17 ins pen .80 2×6M (12.5e9–12.6e9), pen .70 2×6M
(12.8e9–12.9e9). Verification ramps: 13.1e9–13.3e9. **Next unused: 13.4e9+.**

**The curve (h17, pen .75, per-unit EV per round):** baseline −0.63% money
(cut-card mode; validation battery's 0.646% — consistent), slope ~+0.5%/TC,
crossover at TC ≈ +1; bin −2 = −1.49%, +3 = +0.85% (basic). Insurance
attribution is ~all at TC ≥ +3 (+0.056% at +3 → +0.61%/round at +8).

**Negative counts are NOT rescued — the holy-grail question, measured.**
Composition-PERFECT play (better than any index card) recovers, per round:
+0.064% ± 0.025% at TC −1, +0.129% ± 0.043% at −2, +0.244% ± 0.102% at −4 —
i.e. ~8–9% of the deficit, uniformly, growing to only ~22% at TC −8
(+1.39% ± 0.38% against −6.29%). Deviations are tail-heavy on BOTH ends
(+1.8% ± 0.3% at +8) but the negative-count hole is structural: the flat
play-all ceiling (perfect deviations + insurance) is still **−0.47%**.

**The menu** ($25 units, 100 obs rounds/h, h17 pen .75, ins arm unless noted):

| play | corr(bet,TC) | $/h | N0 | bankroll |
|---|---|---|---|---|
| flat play-all (perfect camo) | 0.00 | **−15.58** (ceiling −11.72) | — | — |
| flat + exit TC≤−1 | 0.71 | +1.23 (ceiling +3.59) | 34,082h | $63k |
| 1-2 spread, exit TC≤−2 | 0.84 | +1.82 | 46,629h | $127k |
| 1-8 classic, play-all | 0.78 | +15.92 | 2,687h | $64k |
| 1-8 + exit TC≤−1 | 0.84 | **+32.73** (ceiling +45.31) | 605h | $30k |
| backcount, 8u at TC≥+2 | 0.68 | **+43.54** (money +1.10%) | 543h | $35k |

Pace scales $/h linearly (heads-up ~200 r/h doubles everything). Pen
sensitivity (1-8+exit, ins): pen .70 +$26.84 → .75 +$32.73 → .80 +$45.67/h —
**the cut card is worth more than every index combined.** s17 bracket: whole
curve shifts ~+0.2%; flat play-all still −$10.25/h; verdicts unchanged.

**Verification (live `cli ramp`, 10M rounds each, independent seeds):**
1-8+exit +1.374 ± 0.102 u/100 vs ledger 1.309 (+0.6σ); flat-exit +0.089 ±
0.029 vs 0.049 (+1.3σ); backcount +1.469 ± 0.128 vs 1.742 (−2.0σ, the worst
of three — watched, consistent with sampling); avg bet / per-round sd /
corr(bet,TC) all match to 3 decimals. Cross-validations for free: the 1-8
basic row's money edge +0.223% reproduces E4c's independently-measured
+0.23%; the backcount money edge +1.10% matches the "~+1.1% next door"
STATUS claim.

**Conclusions.**
1. **"No heat AND decent hourly" does not exist at this game.** The
   zero-correlation play loses $15.58/h; the only near-invisible positive
   play (flat + natural-looking exits) makes ~$1–4/h at N0 in the tens of
   thousands of hours. Real money starts at corr(bet,TC) ≥ 0.7 — visible by
   construction — or at back-counting, whose tell is the entry pattern
   rather than the ramp.
2. Indexes/insurance are worth having but don't change the frontier:
   insurance ≈ +$4/h on a 1-8 (all at TC ≥ +3), full deviations ceiling
   ≈ +$12/h more — and NONE of it rescues negative counts (~9% of the
   deficit). E15's lesson repeats: the human frontier is basically the
   simple system; the exotic headroom is small.
3. The best plays here (+$33–44/h, ~$30k bankroll, N0 ~550–600h at 100 r/h)
   are 2–3× E12's 21+3 and half of E14's Dragon+Panda ($92–101/h at HALF
   the N0, with native camouflage) — **the EZ Baccarat verdict stands as
   the project's best game by every column of this ledger.**
4. Idealizations on record: sit-out rounds still consume cards (someone
   else plays); rounds independent for variance (live sd confirms to 3
   decimals); 100 r/h nominal; hi-lo only (E4a: best balanced level-1 count
   for the standard game IS hi-lo).

**E16b addendum — sizing to Potawatomi's actual tables (same day).** Ledger
gained argv overrides (`e16_ledger.py <game> <pen> <unit$> <rounds/h>`) and
wide-spread/bimodal ramp rows. Findings at 200 r/h heads-up (weekday):
- **The TC +1 rung is breakeven** (−0.07%/round, ins arm) — dollars bet
  below TC +2 are dead weight, so the optimal seated shape is BIMODAL:
  min-bet "crouch" + jump straight to a high curve. The crouch (jump 10u at
  TC ≥ +2) beats the graduated 1-20 play-all on every column at once
  (+$57.65 vs +$54.44/h, $30.3k vs $30.6k, N0 351h vs 375h, corr 0.73 vs
  0.78 — while betting LESS total money). Matt's hypothesis, confirmed.
- **Chosen operating point: $10–$200 table, crouch at +2, leave at TC ≤ −2**
  ($10 flat → $100/$150/$200; sheds the worst 21% of rounds):
  **+$67.45/h, N0 255h, $25.8k bankroll, corr 0.76** at pen .75 — pen
  sensitivity **$55.60 / $67.45 / $92.01 per hour at .70/.75/.80**.
  Runner-up: $15–$500 table, 1-16 + exits at $15 units — +$83.62/h, $31.4k,
  N0 251h, corr 0.81 — equal bankroll efficiency, more heat, rarer table.
  Field intel breaking the tie (Matt, ex-supervisor at the property):
  low-limit games draw the least surveillance attention.
- The $500 max only binds at ~$60k+ bankroll (1-33 + exits: +$177.62/h on
  $60.9k); the binding constraint at a ~$30k roll is the roll, not the max.
Write-up: `docs/ARTICLE_BLACKJACK.md` (deliberately a summary, not a
discovery piece).

## E17 — The crouch from an unbalanced running count: Red 7 keeps 93.5%, no division ever

**Date:** 2026-07-18 · **Question (Matt):** can the chosen E16 play keep
most of its EV on an unbalanced count — pure running count, no true-count
division — for lower cognitive load? And is there a better custom count?

**Method.** New harness `cli countcurve` (`experiments.run_count_curves`):
one flat-bet pass bins every round's profit by SEVERAL count signals at
once — hi-lo TC (reference), Red 7 RC, KO RC, half-7 RC (deterministic
7s-at-+0.5, the color-noise-free ideal Red 7) — same card stream, so
retention comparisons carry no cross-run noise. Raw (rank,suit) tracking
feeds the red-seven count (suits {0,1} = red by convention). All running
counts pivot-zeroed: IRC = −s·decks so RC ≈ d_rem·(TC − s) and RC ≥ 0
tests TC ≥ s depth-EXACTLY at the pivot. `search_unbalanced_level1`:
analytic brute force over level-1 unbalanced counts (base tags {−1,0,+1},
ten −1, one red-half-rank bump, imbalance +2/deck ⇒ pivot ≈ TC+2), ranked
by betting correlation against the E4a STANDARD_H17_EOR table. Gates in
`tests/test_e17.py` (incl. differential: multi-pass hi-lo bins ==
run_tc_curve bins exactly; custom==red7 identity). 225 tests green.
Ledger: `data/e17_unbalanced.py` (analytic thresholds at nominal
d_rem = 3.5; sensitivity grids printed, not cherry-picked).

**Data:** 8 × 6M = 48M rounds, ins arm, h17 pen .75, seeds
13.4e9–14.1e9 step 1e8 (`data/e17_*.json`). **Next unused block: 14.2e9+.**

**Findings ($10 units, 200 r/h; hi-lo TC crouch reference on the same pass
= +$63.21/h — E16's independent-seed $67.45 is 1.4σ away, consistent):**
1. **The custom-count search returns Red 7 itself** (hi-lo base, half-bump
   on 7, BC 0.9755): Snyder's count is optimal in the whole level-1
   unbalanced family against our own EORs. No better custom exists there.
2. **The pivot mechanism works as theorized**: jump at RC ≥ 0 is the
   depth-exact TC ≥ +2 test. Color noise (red vs all sevens) costs ~1pp
   (half-7 ideal 90.9% vs red 7 89.8% on the same card).
3. **The recommended no-division card** — IRC −12; $100 at RC ≥ 0, $150 at
   ≥ +2, $200 at ≥ +5; insure when the $150+ bet is out; leave at RC ≤ −14
   (chosen structurally: −16 is the analytic τ=−1.5 point but −14 avoids
   the fresh-shoe IRC −12 collision) — **+$59.07/h, N0 307h, $27.2k
   bankroll, corr 0.81 = 93.5% of the TC card's hourly.** ~$4/h is the
   entire price of never dividing.
4. Sensitivity (pre-registered grids): jump ±1 spans 81–105% (the −2 row
   "beats" the reference only by betting more — bigger bank, worse N0);
   leave −12..−18 spans 87–98% (−12 collides with fresh-shoe IRC — it
   silently converts the card into a wong-in that skips shoe tops).
   Execution tolerance is wide; nothing is knife-edge.
5. **KO play-all retains 88.1%** but with higher bankroll ($37.6k), worse
   corr (0.86), and an unplayable leave threshold (collides with IRC −24):
   pivot placement (TC+4, off the money threshold) costs it, as predicted.
   Red 7 dominates KO for this play.

Caveat on record: the ins arm takes composition-exact insurance in every
system including the reference — retention is arm-consistent (fair) but
all absolute $/h are slightly optimistic vs the human "insure at $150+"
rule. RC-card verification on fresh seeds would need a signal-parameterized
`run_ramp` (parked; bins arithmetic was verified exact in E16).

## E15 — Is there value beyond linear counts? Quadratic buys ~4pp on the Dragon; the Panda tail is high-order (M9 epilogue)

**Date:** 2026-07-18 · **Command:** `uv run python -m ridefree.cli bacorder
--rounds 100000 --seed 8800000001 --penetration 0.966`.

Method: exact per-depth Taylor terms of both side-bet EVs around the
balanced composition (level B, gradient g, full 10×10 Hessian H, by finite
differences of the fractional evaluator `baccarat.frac_probs` — the float
twin of `fast_outcomes`, differentially tested; all analytic, nothing fit).
Score "bet when the order-k tangent model is positive" in TRUE exact EV on
100k cut-14 rounds:

| model | Dragon 7 capture | Panda 8 capture |
|---|---|---|
| order-1 tangent (linear class) | 90.1% | 73.1% |
| order-2 tangent (+ exact quadratic) | 95.3% | 83.6% |
| E14 static-tag rows, for reference | 92.3% / paper 89.8% | 83.2% / 79.1% |
| exact | 100% | 100% |

**Honest caveat, itself a finding:** the tangent model is NOT a strict
supremum over its class — E14's static Panda count (83.2%) beats the
tangent-linear (73.1%), because Panda selection happens at extreme late-shoe
compositions where a Taylor expansion around balanced is far from optimal
while a static count fit to the fluctuation distribution holds up.

**Conclusions:**
- **Dragon 7:** the full exact quadratic reaches 95.3% — at most ~3–5pp
  above the best linear count (~92%). That headroom is ≈ +0.03u/100 ≈
  +$3/h at a $100 unit, and the Hessian has no symmetric human-shaped
  structure (nothing like 21+3's Σ-excess² convexity). Not worth pursuing.
- **Panda 8:** the exact quadratic (83.6%) lands ON the static linear count
  (83.2%) — second order adds ~nothing over the best linear system. The
  missing ~16% of the Panda ceiling is genuinely high-order/combinatorial
  (its value lives in the extreme tail where all low-order models fail):
  **computer-only, definitively.**
- **Bottom line: the two-count card (~87–90% combined) effectively IS the
  human frontier for this game.** Everything beyond it needs a device, and
  even a full quadratic tracker (55 running cross-products — absurd on
  paper) would buy ≤ ~$5/h. The E14b system stands as final.

Seeds consumed: 8800000001. Next unused block: 8.9e9+.

## E14 — The Dragon/Panda verdict: two written counts, ~90% of the ceiling, +$92/h (M9c)

**Date:** 2026-07-17 · **Commands:** `uv run python -m ridefree.cli bactrack
--rounds 100000 --penetration {0.966,0.95} --seed {8300000001, 8400000001,
8500000001}` (300k rounds; all parameters analytic or published, scored in
TRUE exact EV, the E11b doctrine) · ledger: `uv run python data/e14_verdict.py`.

**Prior-art check (fetched 2026-07-17):** Panda 8 DOES have a published
count — WoO appendix 8 (A/2/T +1, 3/4/5/8 −2, 6/7 −1, 9 +4, TC ≥ 11):
0.238u/shoe at cut-14, "the Dragon remains substantially more profitable."
Scored inside our harness, their exact spec gives **0.241 ± 0.011u/shoe, bet
4.60% of rounds at +6.43%/bet vs their published 0.238u / 4.61% / +6.34% —
third independent pipeline cross-validation** (after the M9a combination
table and E13's Dragon count match). Nothing in the published record scores
the PAIR or derives the linear ceiling — that part is ours.

**EOR derivation (analytic, `fast_outcomes` gradients, regeneration-tested):**
our exact D7 removal effects ×10 reproduce WoO's optimal "System 1" tags
digit-for-digit (8 +5.4, 9 +4.8, 7 −3.6, 6 −3.3, 4/5 −2.7, T +0.9…), and the
P8 effects reproduce their appendix tags' shape (9 dominant +4.5; 3/4/5/8
negative; A/2/T mildly positive). Both published counts are near-optimal
LINEAR counts — the open value is threshold quality and the nonlinear tail.

**Capture table (pen 0.966 pooled 2×100k; pen 0.95 in parentheses):**

| row | bet% | u/shoe | capture |
|---|---|---|---|
| d7 linear-EOR tags, analytic threshold | 11.6% | +0.691 | **92.3%** (93.7%) |
| d7 WoO count @ TC≥4 | 9.5% | +0.651 | 86.9% (87.4%) |
| p8 linear-EOR tags, analytic threshold | 5.0% | +0.253 | **83.2%** (87.2%) |
| p8 WoO appendix @ TC≥11 | 4.6% | +0.241 | 79.4% (84.0%) |
| p8 triggered by the d7 count (shared-count) | 11.6% | −0.446 | **−147%** |

- **The two-count pair (Matt's paper-and-pencil point) captures ~90% of the
  combined exact ceiling** (linear pair +1.155u/100 vs ceiling +1.244u/100
  pooled): at a baccarat table a scorecard is expected, so two running counts
  cost nothing socially. The linear-EOR tags are just WoO System-1-style
  scaled integers — written arithmetic, no memory burden.
- **The shared-count row refutes single-count play for the pair:** betting
  Panda on Dragon triggers is firmly −EV (mean −4.7%/bet). The Panda leg
  exists only with its own count — corr(ev_d7, ev_p8) = +0.41 is not enough.
- The last ~10% (ceiling − linear pair ≈ +0.09u/100) is nonlinear
  composition signal — computer territory (or a printed 2-variable lookup;
  not pursued: thin).
- Calibration watch item (E13, d7 pooled −1.89σ): E14's realized columns ran
  ABOVE prediction at pen .966 (+9.9%/+8.6% vs +7.3% predicted windows) —
  opposite direction, consistent with settlement noise. Watch stays open,
  unalarming.

**The ledger (`data/e14_verdict.py`, pen 0.966, no toll — sitting out is
normal baccarat):**

| system | u/100 rounds | $/h @80r/h, $100 unit | N0 @80r/h | bankroll 5% RoR |
|---|---|---|---|---|
| exact (computer) | +1.244 | $100/h | 490h | $73k |
| **linear pair (paper)** | **+1.155** | **+$92/h** | **582h** | **$81k** |
| published pair | +1.092 | +$87/h | 554h | $73k |

Cap sensitivity (linear pair): $50 max → +$46/h on $40k; **$25 max → +$23/h
on $20k — still beats the entire 21+3 operation (E12: +$21/h, $37k, toll,
1,200h N0) at a quarter of the exposure.** Full table (45 r/h) roughly
halves $/h and doubles N0-hours.

**E14b addendum — the playable card (2026-07-17, seeds 8600000001 broken-row
run / 8700000001 verification, 100k rounds pen 0.966):** integer "paper"
tags derived by rounding the exact EORs ×1000 **under a balance constraint**
— the naive rounding summed to −4/deck, the running count drifted with
depth, and the TC triggers never fired (17%/0% capture; the failed run is
seed 8600000001). Lesson recorded: **any rounded tag set must keep
Σ(count × tag) = 0 per deck**; now asserted in code and tested. Verified
playable system: **Dragon tags A+1 / 2−1 / 3−1 / 4−3 / 5−3 / 6−3 / 7−4 /
8+5 / 9+5 / T+1, bet at TC ≥ 10 → 89.8% capture** (vs 91.3% real-valued
ceiling, 85.5% WoO System 2 on the same shoes); **Panda: WoO's appendix
tags at TC ≥ 11 are already at the integer frontier** (79.1% vs our
sharpened set's 78.4% — a tie; use the published set). Paper pair combined
≈ 1.11u/100 ≈ 87% of ceiling ≈ **+$89/h per $100 unit at 80 r/h** — within
$3/h of the real-valued tags; nothing meaningful is lost going to
integers.

**M9c VERDICT: the Dragon 7 + Panda 8 pair at 8-deck EZ Baccarat is the
strongest opportunity this project has found — ~4× the 21+3 hourly at half
the N0, toll-free, at the house's own standard penetration, with native
scorecard camouflage, using two written counts anyone can run. Conditions:
D7/P8 offered at 40:1/25:1, real shoe (no CSM-equivalent), cut ≥ ~0.95,
side maxes ≥ $25. Remaining field items: Potawatomi's EZ table's cut depth,
side maxes, sit-without-betting tolerance.** Idealizations on record: all
dealt cards visible (baccarat deals face-up — weaker assumption than 21+3's
hole card), 80 rounds/h heads-up pace, burn cards not modeled (single-digit
% effect on rounds/shoe, none on conditional EVs).

## E13 — Dragon 7 / Panda 8 exact pre-deal EV: 4.4× the 21+3 ceiling, toll-free (M9b)

**Date:** 2026-07-17 · **Commands:** `uv run python -m ridefree.cli bacev
--rounds 100000 --penetration {0.966,0.95,0.90} --seed <s>` — six shards:
pen 0.966 (cut-card-14, WoO's comparator point) seeds 7700000001 / 7800000001 /
7900000001; pen 0.95 seeds 8000000001 / 8100000001; pen 0.90 seed 8200000001.
600k rounds, ~7,470 shoes. Both side bets staked every round; each round's
EXACT pre-deal EV computed from the remaining composition via
`baccarat.fast_outcomes` (multiset-table restructuring of `exact_outcomes` —
bit-identical integers, differentially tested, 2.4ms/call).

**Ceilings (bet-when-positive, per unit staked, EZ 8-deck flat paytables):**

| pen | bet | P(ev>0) | mean window EV | u/100 rounds | u/shoe |
|---|---|---|---|---|---|
| 0.966 | Dragon 7 | 11.11% | +7.60% | **+0.845** | +0.690 |
| 0.966 | Panda 8 | 5.04% | +7.33% | **+0.370** | +0.303 |
| 0.966 | **both** | — | — | **+1.215** | **+0.993** |
| 0.95 | Dragon 7 | 10.91% | +6.52% | +0.711 | +0.571 |
| 0.95 | both | — | — | +0.980 | +0.787 |
| 0.90 | Dragon 7 | 9.29% | +5.19% | +0.482 | +0.367 |
| 0.90 | both | — | — | +0.654 | +0.498 |

Scale reference: the 21+3 exact ceiling was +0.115u/100 (pen .75) / +0.276u
(pen .85). **The combined Dragon+Panda ceiling at baccarat's normal cut is
+1.215u/100 observed rounds — 4.4× the 21+3 pen-.85 ceiling — and there is no
main-bet toll to subtract** (baccarat sit-out is normal behavior; E12 spent
half its analysis on the toll 21+3 must pay).

**The published-count cross-validation (the load-bearing check):** scoring
WoO's practical Dragon 7 count (4–7 = −1, 8/9 = +2, TC ≥ +4) inside our
harness at cut-14: bet 8.76% of rounds at exact-weighted +8.27% → **+0.592 ±
0.004 u/shoe vs WoO's published 0.597u/shoe** (shards 0.586/0.600/0.591) —
same-harness agreement to half a percent, the E12-Jacobson-style independent
validation of the entire pipeline (engine, depletion, calculator). At pen
0.95 / 0.90 the same count drops to 0.496 / 0.320 u/shoe — penetration
sensitivity matches intuition.

- **The simple count already captures 85.8%** of the D7 exact ceiling
  (corr(ev_d7, tc) ≈ +0.905) — the D7 signal is far more one-dimensional
  than 21+3's suit quadratic (where the best published count got 65%). The
  remaining headroom: ~14% of D7 (+0.10u/shoe) plus ALL of Panda 8
  (+0.30u/shoe; corr(ev_d7, ev_p8) only +0.41, both-windows 2.7% of rounds
  — P8 needs its own signal, published prior art treats it as an
  afterthought). M9c question: cheapest human system for the PAIR of bets.
- **Depth structure:** D7 ignites ~6.5 decks out and grows monotonically —
  P(ev>0) by decks left at pen .966: 2.5% (5) → 11% (3) → 22% (1.5) → 27%
  (1) → 36% (0.5) → 40% (last quarter deck), window mean reaching +12–19%.
  P8 sleeps until ~4.5 decks then follows the same shape at half the
  frequency. Baccarat's cut-14 custom means the game's OWN dealing
  convention delivers the deep tail 21+3 had to pray for.
- **Calibration (pooled binomial on win indicators, 600k rounds):** d7
  all-rounds z = −1.89 (observed 13,291 vs expected 13,508.6; all six shards
  mildly negative), d7 deep-subset z = −2.15, p8 z = +1.57. The predictor is
  exact-by-construction conditional on composition (and `fast_outcomes` ==
  `exact_outcomes` bit-for-bit), so these are WATCHED as sampling
  fluctuation, same doctrine as E10's +2.4σ slope note; M9c's larger samples
  will settle it. Realized window EVs are individually noisy (±6–8%/shard —
  40:1 settlement variance) and consistent with predictions at ~2σ.

**Verdict: proceed to M9c (compression + ledger).** The exact ceiling
clears every bar the project has set: bigger than 21+3 by 4×, toll-free,
at the house's own standard penetration, with the published count as a
strong-but-beatable baseline and Panda 8 as unclaimed value on top.

## E12 — The 21+3 betting verdict: beatable for real, wong-in at deep penetration

**Date:** 2026-07-17 · **Command:** `uv run python data/e12_verdict.py`
(pure ledger arithmetic from E10/E11b measured inputs — no new simulation,
no new seeds; the E4c pattern).

The toll structure decides everything. Playing 21+3 requires a live main
wager, so: **seated** = pay −0.64%/round (h17 basic) on the main bet every
round; **wong-in** = back-count standing behind, enter only on trigger
rounds → the toll shrinks by the trigger rate (~5–7%).

Net EV per 100 observed rounds, in side-stake units (quad-Q system):

| pen | mode | net | notes |
|---|---|---|---|
| 0.75 | seated $15:$100 | **−0.010u** | seated breakeven needs side:main > 7.4:1 — dead at typical limits |
| 0.75 | wong-in | +0.083u | positive but thin |
| 0.85 | seated $15:$100 | +0.115u | viable ONLY at min-main:max-side stakes |
| 0.85 | wong-in | **+0.206u** | the operating point |

$ illustration ($100 side unit, $15 main, 100 observed rounds/h):
**quad-Q @ pen 0.85 wong-in ≈ +$21/h, σ ≈ $716/h, N0 ≈ 1,200 hours**;
seated ≈ +$11.5/h, N0 ≈ 4,100 h; pen 0.75 wong-in ≈ +$8/h, N0 ≈ 4,700 h.
Perfect (computer) play @ 0.85 wong-in: +$26/h, N0 ≈ 950 h. Bankroll for 5%
risk-of-ruin at the operating point ≈ σ²/(2μ)·ln(20) ≈ **$37k**. Grind-scale
— comparable to legitimate hi-lo counting, not a bonanza.

**Interactions:** corr(sb_ev, hilo) ≈ −0.08 ⇒ a hi-lo main game stacks
≈ additively — the strongest configuration is hi-lo main + quad-Q side
(replaces the toll with a positive main leg; both windows rarely collide).

**Side ≤ main cap (added same day; arithmetic in `data/e12_verdict.py`):**
matched bets on a trigger round net ≈ (mean window edge − 0.64%) ≈ +3.2% of
the matched amount, so the common cap does NOT kill the play: wong-in 1:1 =
+0.176u/100 ≈ $17.6/h (85% of uncapped); seated with min main off-trigger
and BOTH bets raised to the cap on triggers ≈ +$8.5/h at pen 0.85 (pen 0.75
capped: +$6.4/h wonging, seated negative). The cap moves the verdict between
"full edge" and "~85% of it"; penetration and paytable remain the kill
conditions.

**Conditions for the verdict to hold (rack-card checklist, in order of
sensitivity):** (1) flat 9-to-1 paytable — tiered "Xtreme" versions have
~13% HE and different category weights, nothing transfers; (2) penetration —
0.75→0.85 is 2.5× the net edge; below ~0.75 wong-in only, marginal;
(3) no CSM (kills everything); (4) mid-shoe entry allowed (else seated mode
needs main-min:side-max ≥ ~1:3); (5) 6 decks (thresholds are 6-deck-derived).
Known idealizations: hole card assumed eventually visible (minor); 100
rounds/h heads-up (a full table cuts $/h roughly proportionally; per-shoe
trigger counts are similar). Surveillance note: max side bets appearing only
late-shoe is a legible pattern — 21+3 suit-counting is published prior art
(Jacobson) and known to surveillance where they care.

**Prior art (fetched 2026-07-17, bjinsider.com newsletter 164, Eliot
Jacobson):** same game (flat 9:1, 6 decks, HE 3.239%), cut card at 260 cards
(pen 0.833 ≈ our 0.85 runs). His perfect-play ceiling: **0.2748u/100 hands —
matching our E10 exact ceiling (+0.269/+0.276u/100) within noise**: strong
independent validation of the whole pipeline. His count is a SPREAD count
(max suit − min suit, true-counted): 0.1777u/100 = 64.7% efficiency, vs
**quad-Q's 0.211u/100 = 78.3% (+19% more value)** — consistent with our E11
finding that one-dimensional shadows of the suit configuration undercapture
the quadratic form. His "minimal vulnerability" verdict rests on era-specific
practicalities (low side-bet caps, device risk), not on different math; at
modern $100 caps his own figure reads ≈ $18/h beside our $21/h. The
widely-quoted "suit count is essentially worthless" line refers to the
single-suit variant (his and our spades-only: ~10% capture).

**M8 FINAL VERDICT: the 21+3 flat-9:1 side bet at 6 decks is genuinely
beatable by suit composition — the first positive verdict of this project.
Best human system: quad-Q (four suit counts + one analytic depth curve),
74–78% of the exact ceiling. Worth playing when: deep penetration (≥0.80),
flat 9:1 paytable, wong-in possible or min-main:max-side stakes, ideally
stacked on hi-lo main play. Expect ~+$20/h per $100 side unit at ~$37k
bankroll — real advantage play, grind-scale.** Unlike Ride Free, this is NOT
dominated by the game next door: it is orthogonal to it and stacks with it.

## E11b — Human trackers scored: quad-Q (4 suit counts) captures 74–78% of the ceiling

**Date:** 2026-07-17 · **Commands:**
`uv run python -m ridefree.cli sbtrack --rounds 2000000 --seed 7100000001` ·
`uv run python -m ridefree.cli sbtrack --rounds 2000000 --seed 7200000001
--penetration 0.85`.

Every rule's parameters are ANALYTIC (threshold curves by bisection on the
closed-form suit-config EV, rank tags by fractional-removal gradient) —
nothing fit to simulation data (the in-sample lesson from the audit). Scored
in TRUE exact EV against the exact rule. Capture (of the E10 ceiling):

| rule | needs | pen 0.75 | pen 0.85 |
|---|---|---|---|
| exact (ceiling) | computer | 100% (+0.116u/100) | 100% (+0.269u/100) |
| additive exact (no interaction) | computer | 99.8% | 99.8% |
| suit4 exact (B+S > 0) | computer-ish | 73.3% | 77.3% |
| **quad-Q: Σ excess² ≥ T_Q(N)** | **4 counts + arithmetic** | **74.2% (+0.086u)** | **78.3% (+0.211u)** |
| suit4 + linear rank count | + a 13-tag count | 80.3% | 81.1% |
| any-suit max-excess ≥ T1(N) | 4 counts | 38.7% | 47.3% |
| … + two-suit pair rule (T2) | 4 counts | 44.4% | 53.7% |
| spades-only specialist | 1 count | 10.1% | 11.2% |

- **The human system is quad-Q**: track the four dealt-per-suit counts;
  remaining excess per suit vs N/4; bet when Σ excess² clears one memorized
  depth curve (T_Q(N) = 4/3·T1(N)², from the analytic single-rich boundary).
  It EQUALS the exact 4-suit family bound (74 vs 73, 78 vs 77 — the shape
  approximation costs nothing; slight dilution near the EV≈0 boundary is
  free). Cross-validates E11a's suit-only bound on independent seeds.
- Max-excess-style rules (the intuitive "one rich suit" heuristic) leave
  ~half the suit value on the table — the two-moderate-suits states matter.
- The best static linear rank count adds ~6pp (80–81% total): the only
  human-shaped path past quad-Q, at the cost of a second (13-tag) running
  count. The last ~19% needs the full quadratic rank term — computer-only.
- Analytic index curve (memorize ~5 points): richest-suit excess to bet
  T1 = 4.0 (26 cards left) / 5.9 (1 deck) / 8.7 (2) / 11.2 (3) / 13.5 (4);
  T_Q = 4/3·T1².

## E11a — What carries the 21+3 signal: suit 71%, rank 19%, interaction ~0.2% (dead)

**Date:** 2026-07-17 · **Commands:**
`uv run python -m ridefree.cli sbdecomp --rounds 2000000 --seed 6900000001` ·
`uv run python -m ridefree.cli sbdecomp --rounds 2000000 --seed 7000000001
--penetration 0.85`.

Exact decomposition, no fitting: the category identities are polynomials, so
they evaluate on fractional smoothed compositions
(`side_bets.category_fracs_21p3`). Per round-state, EV_full = B(depth
baseline, balanced shoe at same N) + S (suit totals, ranks smoothed) + R
(rank totals, suits smoothed) + X (residual interaction) — an identity, each
term exact (`experiments.sb_ev_components`; identities unit-tested to 1e-12).

- **Variance shares of (F − B):** pen 0.75 → S 70.4% / R 20.6% / X 0.16% /
  2·cov(S,R) 9.3%; pen 0.85 → S 72.4% / R 16.6% / X 0.17%. corr(S,R) ≈ +0.13.
- **Selection-rule value (bet when proxy > 0, scored in TRUE ev):**
  | rule | pen 0.75 capture | pen 0.85 capture |
  |---|---|---|
  | exact (ceiling) | 100% (+0.114u/100) | 100% (+0.276u/100) |
  | suit-only (B+S) | **73.0%** | **77.6%** |
  | rank-only (B+R) | 4.3% | 6.2% |
  | additive (B+S+R) | **99.79%** | **99.78%** |
- **The rank×suit interaction is refuted as a signal source** (<0.2% of
  variance; additive rule loses 0.2% of the ceiling). Straight-flush terms
  just don't matter at 9:1 weights.
- **Depth is a first-class variable:** the balanced-shoe baseline B drifts
  −3.24% (fresh) → −8.2% (1.5 decks) → −13.9% (0.5 decks) while sd(S) grows
  0 → 5.5% → 11.9%. A human system needs B(N) as a per-depth threshold
  lookup, not a constant.

**E11b design implications:** four per-suit running counts SUFFICE to compute
B+S exactly (S depends only on suit totals + N) — that family's ceiling is
the suit-only row (73–78%). The remaining ~27% needs rank concentration
(mostly the straight term Σ n_a·n_b·n_c) — full 13-rank tracking is
computer-territory; E11b should quantify cheap R proxies and simplified suit
trackers (max-suit share bins, 2-count compressions) against these bounds.

## E10 — 21+3 exact pre-deal EV: the side bet IS beatable (perfect-info ceiling)

**Date:** 2026-07-17 · **Commands:**
`uv run python -m ridefree.cli sbev --rounds 3000000 --seed 6700000001` (pen 0.75) ·
`uv run python -m ridefree.cli sbev --rounds 3000000 --seed 6800000001
--penetration 0.85`.

First M8c experiment. Each round, the EXACT 21+3 EV (flat 9:1) is computed in
closed form from the remaining (rank,suit) composition
(`side_bets.ev_21p3`, fed by `counting.RawCompositionTracker`) before the
deal; the bet is always staked so realized settlement checks the prediction.

- **Pen 0.75:** ev > 0 on **4.62% of rounds, mean predicted +2.49%**, realized
  +3.81% ± 0.82% (consistent). Ceiling = **+0.115 units per 100 rounds** per
  unit of side stake (bet-when-positive).
- **Pen 0.85:** ev > 0 on **7.10% of rounds, mean +3.88%**, realized +4.27% ±
  0.66%. Ceiling = **+0.276u / 100 rounds** — 2.4× the 0.75 figure; the signal
  lives late (P(ev>0) by depth: 3.6% at 3 decks left → 12.5% at 2 → 18.5% at
  1.5 → 25.1% at 1 → 28.8% at 0.5, mean positive EV there +7.5%).
- **Calibration:** realized-on-predicted slope 1.034 ± 0.071 (pen 0.85 run,
  40 bins spanning −13% to +9%); pen 0.75 run 1.24 ± 0.10 (+2.4σ, watched, not
  alarming). The closed-form calculator prices depleted shoes correctly end
  to end.
- **corr(sb_ev, hilo_tc) ≈ −0.07..−0.09**: essentially orthogonal to the main
  count — side-bet windows don't collide with main-game counting, so a
  combined system stacks rather than competes (E12 must still charge the
  main-bet toll: ~−0.64%/round on the required blackjack bet vs +0.28u/100 per
  unit of side stake at pen 0.85 ⇒ breakeven side:main stake ratio ≈ 2.3:1 on
  bet-selection alone, before any main-game counting).
- Mean predicted EV over all rounds: −3.2464% (0.75) / −3.2369% (0.85) vs the
  fresh-shoe −3.2386% — the small offset is round-frequency weighting (the
  cut-card effect's side-bet analogue), noted, not load-bearing.
- Scale reference: Ride Free's entire bet-selection term was +0.59% on 6.6% of
  rounds ≈ +0.039u/100. The 21+3 ceiling at equal penetration is ~3× that; at
  0.85 pen ~7×. **Verdict: proceed to compression (E11) — this clears the bar
  RF missed.**

Ceiling caveats: perfect information (all dealt cards including dealer hole
assumed visible, same doctrine as CompositionTracker); wong-in of the side bet
only (main hand still played); flat 9:1 paytable as configured — re-confirm
Potawatomi's actual 21+3 paytable on the rack card before believing dollar
figures.

> **2026-07-17 audit note:** the significance figures in E2–E5 below are overstated
> by shoe-seed overlap between shards (corrected σ and details in
> `docs/DEEP_DIVE_AUDIT.md`; the reseeding flaw is fixed in code as of the same
> date). E6–E9 used base seeds spaced ≥ 2×10⁸ and are unaffected — but they ran on
> the pre-fix code, so post-fix reruns of their commands reproduce statistically
> equivalent, not bit-identical, output. The banked `data/` JSONs are canonical.

## E9 — Insurance overlay: +0.15% per wong-in round (perfect information; unmodeled)

**Date:** 2026-07-17 · **Command:** `uv run python data/e9_insurance_overlay.py
1300000001 1000000 data/e9_insurance.json` (1M rounds).

Insurance is not modeled in the engine (see DEEP_DIVE_AUDIT.md); this measures the
overlay from taking it exactly when +EV — p(hole=ten) > 1/3 computed from the
tracked composition minus the three visible cards; stake 0.5, pays 2:1.

- All rounds: **+0.023%**/round (off-window it stays a sucker bet).
- rf_ev ≥ +0.0075 (14.5% of rounds): **+0.099% ± 0.002%** per played round.
- **rf_ev ≥ +0.0125 (6.6%): +0.153% ± 0.004%** per played round. In-window the
  dealer shows an ace 9.2% of rounds (vs 7.7% base) and ~45% of those are +EV.
- Independently replicated at +0.157% (300k rounds, seed 999999937).

Ceiling caveats: perfect-information take rule (human capture via a ten side count
unmeasured — next step); rack card must confirm insurance is offered.

**Engine promotion (same day):** insurance is now first-class — `Rules.insurance_offered`
/ `insurance_pays`, an optional strategy hook `take_insurance(cards, rules)`, explicit
`RoundResult`/`Metrics` ledger fields, and `player_ev.CompositionPlayer` implementing
the E9 composition rule. Gate passed: always-insure on the standard game in csm mode
reproduces the exact 6-deck insurance EV (−23/311 per unit staked, computed reference;
`tests/test_insurance.py`). No built-in reference strategy insures, so all validated
published-edge numbers are untouched. `cli sim` takes insurance (and plays deviations)
by default — `--no-insurance --no-deviations` restores the published-edge comparator;
`validate` always uses the reference strategies.

## E8 — Window-conditional deviation value, properly powered: +0.322% ± 0.063%

**Date:** 2026-07-17 · **Command:** `uv run python data/e8_window_deviations.py
<seed> 1000000 0.0125 <out>` × 4 shards, seeds 1900000001 / 2100000001 /
2300000001 / 2500000001 → `data/e8_wdev_shard*.json`.

Same paired differential design as E5, but the expensive live-composition replay
runs only when rf_ev ≥ threshold (~7× more window rounds per wall-clock; the base
timeline is canonical either way, so the estimand is identical).

- **Deviation value at rf_ev ≥ +0.0125: +0.322% ± 0.063%** (264k paired window
  rounds, 5σ; shards +0.23 / +0.09 / +0.36 / +0.60). 3.4% of window rounds change
  profit. Perfect-information ceiling.
- Supersedes E5's window figure (+0.20% ± 0.13%, which was measured at the wider
  0.0075 threshold and underpowered). E5's *overall* +0.12%/round stands (with the
  corrected σ from the audit).

**Harness promotion (same day):** `run_deviation_value` now takes
`window_threshold` and `window_only` (E8's replay-only-in-window mode, ~7× more
window rounds/sec; window stats proven identical to the full run), counts true
*action* changes alongside profit changes (fixing the E5 mislabel at the source),
and both are exposed on `cli deviations`. Deviations are also playable in straight
sims via `player_ev.CompositionPlayer` (`cli sim`, default on).

## E7 — rf_ev × hilo_tc joint grid: dominance closed, camouflage measured

**Date:** 2026-07-17 · **Command:** `grid --rules ridefree --row rf_ev --col
hilo_tc --rounds 3000000 --json …` × 3 shards, seeds 3400000001 / 3500000001 /
3600000001 → `data/e7_joint_shard*.json` (9M rounds).

- **E4b's open dominance question: CLOSED.** Within-rf_ev hi-lo residual slope
  +0.02%/TC ± 0.04% — null. Hi-lo adds nothing at fixed RF count; the parked
  resplit-aware EOR re-derivation is retired.
- **Camouflage fraction (first measurement): 3.2%** of rf_ev ≥ +0.0125 rounds have
  hilo_tc ≤ +1 (12.4% at ≥ +0.0075) — 96.8% of wong-in entries coincide with
  hi-lo TC ≥ +2, so the ARTICLE's "reads as a hunch player" thesis fails as
  stated. Residual nuance: only 32% of TC ≥ +2 rounds are RF-playable.
- Independent wong-in check @ +0.0125: +0.696% ± 0.138%.

## E6 — rf_ev × p_free_double: subsumed; wong-in EV recertified on clean seeds

**Date:** 2026-07-17 · **Command:** `grid --rules ridefree --row rf_ev --col
p_free_double --rounds 3000000 --json …` × 4 shards, seeds 900000001 /
1100000001 / 1500000001 / 1700000001 → `data/e6_pfd_shard*.json` (12M rounds).

- Pooled within-rf_ev p_free_double slope: **−0.03% ± 0.05%. Null** — with E4b,
  the RF count now subsumes *both* event signals.
- Fresh wong-in @ rf_ev ≥ +0.0125: +0.51% ± 0.12%; **pooled with E7's 9M rounds:
  +0.59% ± 0.09% at 6.6% of rounds** — the certified replacement for E4c's
  in-sample +1.04% (see DEEP_DIVE_AUDIT.md). Fresh threshold frontier and the
  corrected full-system stack (≈ +1.06% ± 0.11%/played round incl. E8+E9
  ceilings) are in DEEP_DIVE_STRATEGY.md.
- RF-count calibration slope on clean data: 0.93–0.97 (E4b's 0.75 was a
  contaminated-data artifact).

## E5 — Value of playing deviations: +0.12% ± 0.05% (perfect-information ceiling)

> **[Audit correction, 2026-07-17]** Shards 7777/8888 shared 68% of their shoes:
> honest overall value **+0.119% ± 0.060% (+2.0σ)**. "2.1% of rounds change any
> action" actually measured *profit*-changed rounds — the true action-change rate
> is **3.7%**, gaining ~+3.2% per changed round. The window figure is superseded
> by E8: **+0.322% ± 0.063%** at the operating threshold (+0.0125).

**Date:** 2026-07-17 · **Command:** `deviations --rules ridefree --rounds 150000`
× 2 shards (seeds 7777/8888), paired differential design (each round played twice
from the same shoe position: fixed OptimalStrategy vs live-composition argmax).

### Result

- **Overall deviation value: +0.119% ± 0.046% per round (+2.6σ).** Shards +0.093 ±
  0.065 and +0.144 ± 0.064 — consistent.
- Only **2.1% of rounds** change any action; those rounds gain ~5–6% EV each.
- Wong-in window (rf_ev ≥ +0.0075): **+0.20% ± 0.13%** (+1.5σ, suggestive).
- This is the *perfect-information ceiling* — human-trackable deviation rules
  capture some fraction of it.

### Impact on the bottom line (updating E4c)

- Seated 1-8 ramp: −0.37% + ~+0.07% (deviations per money wagered) ≈ **−0.30%,
  still losing.** Deviations do not rescue seated play.
- Wong-in at rf_ev ≥ +0.0125: +1.04% + ~0.2% ≈ **~+1.2% per played round on ~6.6%
  of rounds** — the complete best-known Ride Free system: back-count with the RF
  count, sit only above threshold, deviate by composition.
- Standard blackjack still wins on raw EV (more spots at equal quality, plus its
  own deviation set). Ride Free's edge over standard remains camouflage, not money.

**Every EV source in the game is now quantified:** base edge, optimal chart, the
count (game-derived), event signals (subsumed), bet ramps, wong-in, deviations.
M6a's core question — can Ride Free be beaten, how, and by how much — is answered.

## E4c — Which accounting system makes money, and how much (the M6a betting verdict)

> **[Audit correction, 2026-07-17]** The "independent seeds" overlapped ~98%, so
> the cross-fit protection did not exist and the wong-in EVs were
> in-sample-optimistic (honest SE on +1.04% is ±0.24% before selection effects).
> Clean-seed certification (E6/E7, 21M fresh rounds): **≥ +0.0075 → +0.21% ±
> 0.08%; ≥ +0.0125 → +0.59% ± 0.09%.** The standard-game row was single-grid
> (necessarily in-sample), as noted below. The seated-play verdict is unchanged.

**Date:** 2026-07-17 · **Method:** pure arithmetic on banked grids, cross-fitted
(bet thresholds selected on one dataset, profit evaluated on independent seeds).
1-8 spread, min bet 1 every round. Standard-game row is same-data-selected (mild
optimism) — its positive region (TC ≥ +1) is textbook anyway.

| system | units/100 rounds | edge on money | rounds at max bet |
|---|---|---|---|
| Ride Free, hi-lo only | −0.73 | −0.51% | 6.3% |
| Ride Free, hi-lo × pairs (2D) | −0.67 | −0.40% | 9.4% |
| **Ride Free, RF count** | **−0.64** | **−0.37%** | 10.5% |
| **Standard, plain hi-lo** | **+0.79** | **+0.23%** | 35.9% |

**Verdicts:**
1. The RF count is the best Ride Free system — beats hi-lo+pairs while being one
   number instead of two (consistent with E4b: it subsumes the pair signal).
2. **Seated play with realistic spreads does NOT beat Ride Free.** Every system
   loses; the ~1.1% waiting cost and rarity of good shoes (10% bettable vs 36%
   standard) dominate. Standard blackjack next door is beatable with plain hi-lo.
3. **Wong-in is the one profitable Ride Free mode found so far** (back-count, sit
   only when the RF count clears threshold):
   - ≥ +0.0075 predicted shift: 14.5% of rounds, **+0.48% EV**
   - ≥ +0.0125: 6.6% of rounds, **+1.04% EV**
   - Standard comparison: TC ≥ +2 → 19.8% of rounds at +1.09%.
   Standard offers ~3× the playable volume at equal quality; Ride Free wong-in is
   real but second-best — its value would be camouflage (rare, hunch-looking bets)
   rather than raw EV.

**Remaining unquantified EV source:** playing deviations (composition-conditioned
strategy changes). That's E5. Also parked: resplit-aware EOR re-derivation (suspected
to sharpen the RF count somewhat; the E4b dominance question stays open until then).

## E4b — The pair effect is fully explained by the RF count (null at −0.6σ)

> **[Audit correction, 2026-07-17]** Shards 5555/6666 shared 98.4% of their
> shoes; honest SE ±0.19% — the null stands (and E7 later closed the open
> dominance question below: hi-lo is fully subsumed; the calibration slope on
> clean seeds is 0.97, not 0.75).

**Date:** 2026-07-17 · **Command:** `grid --rules ridefree --row rf_ev --col p_pair
--rounds 3000000` × 2 shards (seeds 5555/6666), merged. Raw: `data/e4b_shard*.json`.

### Result

**Pooled within-RF-count pair slope: −0.079% ± 0.129% (−0.6σ). Null.** (Shards:
−0.18 ± 0.19 and −0.16 ± 0.19.) Compare E2/E3: +0.63% ± 0.09% at fixed *hi-lo*.

**Interpretation — the honest revision of the E2/E3 claim:** the pair signal's
predictive power was real *relative to hi-lo*, but it was carrying linear
composition information that hi-lo mis-weights (mostly ten-depletion and the ace/ten
asymmetry — non-ten pair probability rises as tens depart, and the RF count prices
tens/aces correctly where hi-lo can't). Once the count axis is derived from the
game's own EORs, pairs add nothing measurable. The genuinely quadratic
(concentration) component of p_pair carries no material EV. The E2/E3 "discovery"
matures into: **Ride Free needs its own count, and that count subsumes the pair
signal.** Matt's pairs intuition was the thread that exposed hi-lo's inadequacy.

### The RF count itself works

Row marginal is monotone; realized-EV-on-predicted-shift slope ≈ 0.75 (predicted
1.0 — attenuated), EV crossing zero near predicted shift ≈ +0.012 (~3% of rounds
beyond it, reaching +0.7%+).

### Open question for E4c (flagged, unresolved)

Eyeballed conditional-EV spread does not yet show the RF count *dominating* hi-lo as
theory requires of an optimal linear count — suspect the EOR derivation's no-resplit
approximation (free resplits are worth ~0.3% and concentrate in exactly the shoes
the count must price) and binning artifacts. E4c must (1) run the ramp arithmetic
consistently on the banked grids (hi-lo grids: E2/E3; rf_ev grids: E4b) and
(2) if the RF count fails to beat hi-lo, re-derive EORs with resplit value modeled
before concluding anything.

## E4a — Ride Free effects of removal: hi-lo is the wrong count for this game

**Date:** 2026-07-17 · **Method:** `eor.effects_of_removal` — analytic EOR via the
weights-parameterized `EVCalculator` (`game_ev` with one card removed per 52).
Motivated by Matt: classical hi-lo tags are standard-blackjack EORs; Ride Free's
must differ. **Validation first:** our standard-game EORs reproduce Griffin's
published table (Theory of Blackjack p.44) in sign, rank order, and approximate
magnitude (e.g. ours S17: 5 → +0.80 vs Griffin +0.69; A → −0.58 vs −0.61; 8 ≈ 0).

### The derived EORs (% per card removed from 52)

| rank | standard H17 | Ride Free | change |
|---|---|---|---|
| A | −0.52 | **−0.64** | aces MORE valuable (A,A free split + naturals) |
| 2 | +0.40 | +0.40 | unchanged |
| 3 | +0.49 | **+0.20** | collapses (feeds 3-6/3-7/3-8 free doubles, 3,3 split) |
| 4 | +0.66 | **+0.32** | halves |
| 5 | +0.80 | **+0.53** | still max, but slashed (4-5/5-6/5-5 combos) |
| 6 | +0.48 | +0.40 | mild |
| 7 | +0.28 | **+0.10** | nearly neutral |
| 8 | −0.02 | **−0.11** | flips negative (8,8 free split) |
| 9 | −0.22 | −0.13 | less negative |
| T | −0.54 | **−0.23** | HALVED — dealer 22 is made of tens; T,T not free-splittable |

Headline structure: **the Ride Free ace is ~3× as important as the ten** (hi-lo
weights them equally), and the small-card tags hi-lo leans on (3,4,5) lose half or
more of their value. Classical hi-lo is measurably mis-tuned here — consistent with
the blunted EV slope observed in E1 (+0.45%/TC vs +0.6%/TC standard).

### The RF count

`counting.rf_ev_shift()` = first-order EOR expansion, the *perfect linear count*
for Ride Free expressed directly in EV units:
EV(shoe) ≈ EV(fresh) − 51·Σ EOR_r·(n_r/N − c_r/52). Hardcoded EOR vectors carry a
regeneration test. Known level-bias caveat: `game_ev` sits ~0.17%/0.39% below
simulated truth (infinite-deck + no-resplit approximations) — fine for EORs
(derivatives), not for absolute edge claims; the simulator remains the authority
on levels.

### Next: E4b (running)

Grid with rf_ev as the row axis: (1) its EV slope should beat hi-lo's +0.45%/TC
equivalent (calibration: slope of realized EV on predicted shift ≈ 1 would mean the
linear model is well-calibrated); (2) the purified pair claim — pair slope at fixed
RF count.

## E3 — Replication: the pair effect is CONFIRMED (+6.6σ combined)

> **[Audit correction, 2026-07-17]** The four "fresh" shards and E2 shared 95–98%
> of their shoes (the `seed + shuffles` flaw), so this was one large sample, not
> a replication: honest combined evidence ≈ **+0.55–0.63% ± 0.21% (≈ +3σ)** (the
> range reflects a min_cell estimand shift the audit also found), and the tight
> shard agreement below is duplication, not confirmation. Qualitative conclusion
> unchanged — and E4b subsumes the signal regardless.

**Date:** 2026-07-17 · **Command:** `grid --rules ridefree --row hilo_tc --col p_pair
--rounds 3000000` × 4 shards (seeds 1111/2222/3333/4444, fresh — never used in E2),
merged via `combine`. Raw grids: `data/e3_shard*.json`.

### Result

| sample | pooled within-TC pair slope (per +0.01 p_pair) |
|---|---|
| E3 alone (12M fresh rounds) | **+0.654% ± 0.106% (+6.2σ)** |
| E2+E3 combined (15M) | **+0.626% ± 0.094% (+6.6σ)** |
| individual shards | +0.537, +0.598, +0.553, +0.518 (each ±0.221) |

- Positive in **all 13** TC rows of the combined sample.
- The four independent shards agree tightly — this is not seed luck.
- Together with E2's null standard-game control (+0.05% ± 0.24%), the effect is
  attributable to free-split value, not composition confounds.

### What it means

**Pair-richness of the remaining shoe is a real, count-orthogonal EV signal on Ride
Free, worth ≈ +0.6% per 0.01 of pair probability at fixed true count.** Across the
observed signal range (~0.035–0.065) that is up to ~+1.5–2% of EV — pair-rich shoes
at TC +1/+2 reach break-even-or-better territory that a pure counter would ignore,
and the signal is invisible to count-based surveillance (r² with TC ≈ 0.5).

To our knowledge there is no published literature on composition-targeted betting
for Free Bet variants; this appears to be a novel result.

### Next (E4)

Pure arithmetic on the existing grids, no new simulation needed:
1. Derive the optimal (TC × p_pair) bet ramp from the combined grid and compare its
   overall edge/variance to the best TC-only ramp — the first candidate "accounting
   system" verdict.
2. Then: practical distillation (how much of the p_pair signal survives a
   human-trackable approximation, e.g. side-counting a few ranks?).

## E2 — Does pair-richness add EV at fixed true count? (first positive evidence)

**Date:** 2026-07-17 · **Command:** `grid --rules {ridefree,h17} --row hilo_tc
--col p_pair --seed 4242 --rounds 3000000` · Raw grids: `data/e2_*.json`.

### Result

| | pooled within-TC pair slope (per +0.01 p_pair) |
|---|---|
| **Ride Free** | **+0.542% ± 0.221% (+2.4σ)** |
| Standard (control) | +0.047% ± 0.241% (+0.2σ, clean null) |

- The Ride Free slope is positive in **11 of 13** TC rows (sign test p ≈ 0.011).
- The control being null rules out a composition confound: in a game without free
  splits, pair-richness carries no EV information beyond the count. The Ride Free
  effect is therefore attributable to free-split value.
- The Ride Free − control slope difference is +0.50% ± 0.33% (+1.5σ): the contrast
  is *suggestive*, not yet conclusive.

### Interpretation

If the effect is real at this size, it matters: observed p_pair spans ≈ 0.035–0.065,
so riding from average (~0.048) to the pair-rich top is worth roughly **+0.9% EV —
comparable to a full extra true count**. Practically, it would shift the profitable
betting region earlier (e.g. TC +2 pair-rich shoes approaching break-even or better
instead of waiting for TC +4), and it is information hi-lo does not carry (E1:
r² with TC only 0.52).

### Status: SUGGESTIVE, needs replication

2.4σ with one seed is not a discovery, and this project runs many comparisons. Next
(E3): replication at ~4× the sample (seed-sharded 3M-round runs combined via the
JSON dumps — single runs exceed the 10-minute background window at ~7k rounds/s),
targeting ±0.11% precision: a real +0.54% effect would read ~5σ; a null will show
itself honestly. If confirmed, derive the (TC × pair) bet ramp and quantify its edge
over the best TC-only ramp.

## E1 — Conditional EV by pre-deal signal (first attack reconnaissance)

**Date:** 2026-07-17 · **Command:** `signals --rules {h17,ridefree} --seed 31337
--rounds 3000000` · **Signals:** exact P(free-split pair), exact P(free-double hand),
hi-lo true count — all perfect-information from tracked composition.

### Findings

1. **M5 sanity gate: PASSED.** Standard game EV rises monotonically with hi-lo TC,
   ≈ +0.6%/TC through the bulk (−4.8% at TC−6 → +2.1% at TC+5). The signal pipeline
   (tracker → TC → conditional EV) is trustworthy.

2. **The anti-correlation hypothesis is confirmed, strongly.**
   corr(p_free_double, hilo_tc) = **−0.937**; corr(p_pair, hilo_tc) = −0.724.
   Double-rich shoes are small-card shoes are bad shoes.

3. **Naive event-betting is REFUTED for both signals.** On Ride Free, EV *falls* as
   either signal rises: p_free_double runs +1.0% (at 0.07) down to −5.5% (at 0.17);
   p_pair peaks around 0.040–0.045 and declines toward both extremes. Betting more
   when free bets are more likely means betting more into worse shoes. As standalone
   bet triggers, both signals are inverted proxies for the count.

4. **But the free-bet value is real and localized — visible in the (Ride Free −
   standard) difference curves.** By p_pair bin: −2.9% at 0.035 rising monotonically
   to +2.4% at 0.065 — free splits add ~2–3% *relative* EV in pair-rich shoes. By
   p_free_double bin: ~−1.5% at 0.08 rising to ~+1.4% at 0.16. The free-bet features
   pay off exactly where the events are frequent; the base game just deteriorates
   faster in those same shoes.

5. **Hi-lo works on Ride Free.** EV rises ≈ +0.45%/TC, crossing zero around TC +3/+4
   (later than standard because the base edge is higher: −1.11% overall this run).
   A plain counter has a real, if thin, positive-EV region.

6. **Pairs beat doubles on independence — Matt's instinct has support.**
   p_free_double shares r² = 0.88 of its variance with the count: it carries almost
   no information a counter doesn't already have. p_pair shares only r² = 0.52 —
   roughly half its variance is *orthogonal* to the count. If either event signal
   adds value on top of counting, pairs is the better candidate.

### Verdict and next question

The 1D attack is dead; the 2D question is now sharp: **at fixed true count, does
pair-richness still predict EV?** Next experiment: 2D conditional EV binned by
(hilo_tc × p_pair) on Ride Free, plus the analytic ramp evaluation over the hi-lo
curve as the baseline any hybrid must beat.
