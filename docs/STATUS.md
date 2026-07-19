# STATUS — read this first in a new session

Updated 2026-07-19. This is the resume-here document: current state, key numbers,
and the precisely-specified next step. Doc map at the bottom.

**Current state in one line: all three research questions are ANSWERED and
written up (Ride Free: dominated; 21+3: beatable, grind-scale; Dragon 7 +
Panda 8: beatable, the strongest verdict — `docs/ARTICLE_EZBAC.md`); E16
priced classic blackjack in real dollars; the PLAYING CARD IS LOCKED
(E18, below): crouch15-2r, certified ≈ +$44/h ± 2 on ~$36k, drilled by the
trainer web app; and M10 (below) turned Matt's "Silver Stack" recon find
into the project's best per-bankroll verdict in one day: M10a gated the Pot
of Gold engine and refuted the published table (real PT1 edge 8.25%, not
5.77%); M10b proved the bet BEATABLE — TC ≤ −3 → +7.4%/unit on 11.7% of
rounds, OOS-replicated; the E21 farm arm (split 5s while the side is
out — free by measurement) lifted the window to +11.8%/unit and widened
t\* to −2; E21b priced the side≤main scenarios (raise-on-trigger keeps
70–77%); and E22 DELIVERED THE HUMAN CARD: **"pog2"** — A/T −1, 3/4/6/7
+1, red 2s +1, 5/8/9 nothing, start 24, stake ≤ 12 — a no-division count
that BEATS hi-lo-with-division (106.6% capture, OOS'd): untied $25/$50/
$100 → +$49/+$133/+$300/h on $17k/$24k/$41k; matched 1:1 → +$42/+$108/
+$240/h. Matt's "ultimate card" hypothesis answered by measurement:
fusion, dual-trigger, and Red-7-reuse ALL lose to the specialist. E22b
then certified Matt's simplification **"hi-lo-57"** (hi-lo with the 5
and 7 swapped; start 10, stake ≤ 5) as a statistical TIE with pog2 —
the practicality pick — while his KO variant died (35%). The felt read
LANDED (2026-07-19): $25 side max, TIED (side ≤ main), pen ~.79–.833,
~100 r/h, split rules = the RIDE_FREE preset verbatim — and **E23
certified the literal card live at both pens (both gates pass): the
operating number is ≈ +$26–30/h on ~$16.6k at 5% RoR**
(raise-on-trigger $15→$25). **MATT'S DECISION (same day): the play is
SHELVED** — the $25 tied max caps the hourly too low, and the play
style (side-jamming at trash counts, splitting 5s, nonstop table
commentary at a social game) isn't worth the seat. **The operating game
remains crouch15 blackjack.** Trainer pog2 mode SKIPPED. Final
write-up DONE: `docs/ARTICLE_POG.md` — WoO-ready, carries the P(0)
correction per the parked rule (play dead → correction ships).**
**M11 OPENED (2026-07-19, Matt's hobby reframe): minimum bankroll that
still clears $15/h at 200 r/h on classic blackjack — E24 (below) priced
the whole frontier from banked bins in one pass: never-leave ~$31k,
walk at TC ≤ −1 ~$10k (the walk line is the money decision — and it's
where division earns its keep; no-division walk cards cost $20k+),
sit-out shapes $5–7k (conditional on felt policy), and deviations are
worth a THIRD of the bank (Matt's hunch, priced: $9.7k → $6.4k on the
same card). E25 (same day) built the RA bank (paired SECOND moments per
play — `cli rabank`, 40M rounds, 4 gates green) and answered Matt's
"variance-tuned deviations" question by measurement: honest-variance
deviations cut 35–45% of the bank in every shape (**walk $7.1k at
+$15.4/h; sit-out $3.9k; never-leave $21.4k at +$30.7/h**), the engine
re-derived the classic index card ranked by bankroll impact (16vT = 30%
of play value; top 5 ≈ 60%), insurance-at-jump-bins fell out as the
derived rule — but RA-vs-EV-max itself is ~1–2% of bank (the real RA
content: skip 2,2v3 / 3,3v3 splits, DON'T split T,T v 3 even when +EV).
Awaiting Matt's shape pick, then OOS-certify the literal human card.**

## M11 OPEN — the hobby question; E24 DONE (2026-07-19): the frontier from banked bins

**Matt's reframe:** a 5%-RoR bankroll is honest only if you'd truly lose
all of it — "I'll quit if I drop $5–10k" silently voids the 5%. So the pro
objective (max $/h per bankroll) flips: **min bankroll s.t. ≥ $15/h at
200 r/h** on classic 6d H17, simplest system, non-division preferred,
deviations/index plays reopened (his hunch: that's where low variance
lives, possibly including changed off-the-top strategy).

**E24 answered the frontier without a single new sim**
(`data/e24_hobby.py` over the banked E16 TC curves + E17 RC curves):

| shape (ins arm, $15 floor, pen .75) | $/h | bank @5% RoR |
|---|---|---|
| seated, never leave (best human card) | +$28.12 | $30.8k |
| **walk at TC ≤ −1: floor from 0, $70 at +4** (1-jump pick) | **+$15.96** | **$10.4k** |
| walk at TC ≤ −1: $50 at +4, $90 at +6 (2-jump optimum) | +$15.28 | $9.7k (theory floor $9.4k) |
| same 2-jump card, all-indexes ceiling | +$23.16 | $6.4k |
| sit-out below +1 / wong shapes (TC or RC, division-free) | +$15–16 | $5.1–6.2k |

Structure: the $15 floor toll at negative counts is everything —
never-leave is pro-priced; the walk line at −1 does the work, and it's
the one decision Red 7 RC can't express (RC = d_rem·(TC−2) blurs
off-pivot: best no-division WALK card $20.1k — the pro/hobby inversion:
crouch15's jump was pivot-exact, the hobby's walk needs division).
Deviations cut a third of the bank; insurance alone $2k, all at the jump
bins (E18's human rule transfers). Sensitivities: pen .70 → +$11.6/h
(below target — the deep table decides); pen .80 → +$22/h on $7.7k; $10
weekday floor → $7.2–7.9k walk / $4.7–5.2k sit-out; 140 r/h → $10.7k.
Honesty: N0 425h, 46% of 4h sessions lose (P5 −$975), a full 200h year
is +$3.1k ± $4.4k (~24% chance a correct year loses). Winner's-curse +
zero-friction-walk caveats in EXPERIMENTS E24.

**E25 DONE (same day): the RA bank — see EXPERIMENTS E25.** Machinery:
`cli rabank` (chart moments + per-play paired (d, d², p·d) + exact
insurance overlay, one pass, ~10k r/s) and `data/e25_ra.py` (gates →
per-shape chart/EV-max/RA layer table → the ranked play list). All four
gates green on 40M fresh rounds; deviation second moments are now
MEASURED, retiring E24's reused-variance approximation (walk-shape
honest ceiling $7.1k, was $6.1–6.4k approximate). Headline per shape
(honest variance, $15 floor, ≥$15/h): **walk $7.1k / sit-out $3.9k /
never-leave $21.4k at +$30.7/h**; the distilled card is short (top 5
plays ≈ 60% of play value: 16vT, 15vT, 12v3, 12v2, 14vT; insure ≥ +4 =
"insure when the jump is out", derived); RA-specific selection is worth
only ~1–2% of bank over honest EV-max — measured, no longer a hunch.

**E25b (same day): MATT'S HONEST SPEC — bank ≤ $5k, walk ≤ 10%,
≥ $10/h — is INFEASIBLE seated-and-betting (walk ≤ 6.5% costs $16.3k at
the $15 floor / $10.9k at $10 / ≈$8k at pen .80: the −2..−1 floor toll
is a variance floor 2–3× the budget) but the SIT-OUT card passes all
three with margin: $3.8k at +$10.4/h ($15 floor) or $3.2k at +$10.1/h
($10 floor), 140 r/h, zero walking, betting ~36% of rounds from a kept
seat.** The whole hobby now hangs on one felt question.

**Next chunks (E25b reordered — the felt now gates everything):**
1. **THE decisive recon (Matt, next casino visit):** may a seated
   player sit out hands and rejoin mid-shoe (house policy + dealer
   practice at the $15 tables)? Secondary: weekday $10 tables? weekday
   pace? If sit-out is allowed → the spec-passing card exists; then
   chunk 2. If hostile → the resize-on-drawdown ladder is the one
   honest lever left for a seated card (new machinery, real RoR
   reduction, costs hourly when down).
2. **OOS-certify the sit-out card as the LITERAL human card** (crisp
   TC-threshold indexes from the E25 play list, the E18/E23 pattern;
   closes the composition-vs-crisp gap, the additivity approximation,
   and the play-level winner's curse in one run; next unused block
   22.4e9+).
3. **The walk-pivot count** (only if a walk shape revives): unbalanced
   level-1 with pivot AT the walk line (imbalance −1 → pivot TC −1 →
   the walk depth-EXACT). One new `countcurve` signal run.
4. **PyPy throughput experiment** (Matt's "should we port to Rust?"
   question, 2026-07-19 answer: not yet): the engine is pure stdlib —
   PyPy could buy 5–15× for zero code changes, possibly bit-identical
   (MT19937-compatible random). 30-minute experiment before any Rust
   talk; Rust only if a question demands a scale PyPy can't reach
   (decision record M7 still governs).

## E23 DONE (2026-07-19): the literal pog2 card CERTIFIED LIVE — and priced at the real felt

**Both gates pass on 10M live rounds per pen** (`data/e23_run.py` /
`e23_verdict.py`, seeds 20.4–21.3e9): the literal card (start 24, stake
≤ 12, farm only while the side is out) staked 16.49% of rounds at side
**+10.39% ± 0.39/unit vs the E22 bin prediction +10.13% (z +0.66)**;
unstaked main −0.946% vs the EV_OUT −0.95% approximation (z +0.11).
Realized cov(main, side | staked) = **+0.72 u²** (positive — prior
ledgers slightly understated variance; now measured, approximations
retired). Deep pen pays double: pen .8333 → **18.59% staked at
+11.18%/unit** (frequency AND quality rise; the signal is depth-fed).

**THE OPERATING NUMBER (felt-true: side ≤ main, $25 max, 100 r/h,
raise-on-trigger, pen .8333): +$30.20 ± 1.83/h, N0 367h, ~$16.6k bank
at 5% RoR** (pen .75: +$22.13/h on $20.4k; the observed .79–.833
brackets ≈ +$26–30/h). Flat $15/$15 ≈ +$13.5/h — raising to $25 on
trigger earns its keep. Untied-world numbers (if the tie is ever
lifted): $25 → +$25.67/.75 pen, +$34.33/h/.8333. Realized sd ≈
$56/round; the 7-lammer jackpot landed 7 times in 1.65M staked rounds
(histogram healthy to the top rung). Full entry: EXPERIMENTS E23.

## M10a DONE (2026-07-18, third session): Silver Stack = Pot of Gold, gated; WoO's table refuted on P(0)

Matt's recon find (Silver Stack on the Ride Free tables, 3/10/30/60/100/300/
1000 for 1–7 lammers) is Galaxy Gaming's **Pot of Gold Pay Table 1 verbatim**.
Full story in **EXPERIMENTS E19**; the short version:

- **Engine:** `Rules.side_bet_pot_of_gold` (PT1/PT2/POG-04 presets as data),
  pre-deal `bet_pot_of_gold` hook, settled from the ledger's existing
  `free_splits + free_doubles` — no cards, no RNG, deal sequence untouched
  (brace-tested). `AlwaysPotOfGold`/`SplitFives` wrappers, token histogram in
  Metrics, `cli sim --pog / --split-fives`. 292 tests green (21 new, incl. a
  scripted 7-lammer chain and an exact-P(0) pin).
- **The published table is impossible:** P(0 lammers) is strategy-free
  dealing arithmetic (proved: every repo strategy takes every offered free
  bet) = **0.838228071 exact** (`side_bets.exact_p0_pot_of_gold`); WoO's
  simulated table says 0.833420. Gate battery therefore scores exact-P(0),
  their convention-robust k≥2 shape, and their convention-FREE deltas.
- **Gate (10 × 2M csm rounds, RIDE_FREE_WOO + PT1, seeds 15.7–16.6e9):**
  P(0) z −0.41 ✅; split-fives delta +3.080% vs published +3.019% (z +0.33) ✅
  — validates the whole resplit/token tree; farm main cost −0.173% vs −0.15%
  ✅; main edge −1.027% ± 0.034 re-confirms M4 ✅; k=6/7 rungs match (23
  jackpots in 10M) ✅; k=3 disagrees with their sim by −4% relative (their
  table is unreconstructible under the stated rules — logged, not chased).
- **Operative numbers (NV rules): PT1 −8.246% ± 0.128 (Silver Stack's real
  cost), POG-04 −8.249, PT2 −7.071, split-fives farm −5.166.** Per-round sd
  ≈ 4.1u. Histogram shards banked (`data/m10a_*.json`, pool via
  `data/m10a_verdict.py`) — any paytable variant prices by arithmetic.

**M10b DONE (same session): SILVER STACK IS BEATABLE — the project's best
$/bankroll verdict, conditional on the side max (E20).** 20M cut_card
rounds (pen .75 assumed), 5 in-sample + 5 out-of-sample shards: side EV per
unit runs −4.4% (TC 0) → +7.1% (−3) → +19.5% (−6) → +45% (−12), monotone,
z to +20; **t\* = −3 replicates OOS (+7.10 ± 0.42 vs +7.64 ± 0.45): trigger
11.65% of rounds at +7.37% ± 0.31/unit.** Seated ledger ($15 main every
round — toll charged per-TC, −2.53% inside the window): side $50 →
**+$52/h, N0 487h, ~$38k**; side $100 → **+$138/h, N0 270h, ~$56k**; $25
max → +$9/h (dead). Wong-in stronger still (needs entry policy). New
machinery: `cli pogcurve/pogcombine` (side+main binned separately, ±12
clamp), verdict `data/m10b_verdict.py`, shards `data/m10b_rf_p75_s*.json`.
**Field status: 6-lammer rung felt-confirmed 300:1 → PT1 exactly.**

**E21 DONE (same day): THE FARM ARM — splitting 5s while the side is out
is free money, and it changes the verdict tiers.** 10 × 2M farm-arm rounds
(`pogcurve --split-fives`) on the SAME seeds as the E20 shards (paired
arms = CRN deltas; M10a gate pattern, no fresh seeds consumed): always-on
delta +3.088% ± 0.033 re-validates the gate AND WoO's +3.019; **window
side EV +7.37% → +11.78%/unit (Δ +4.41 ± 0.09, OOS PASS); per-bin
breakeven side stake < $1 → the human rule is unconditional ("side out →
split 5s"); the A/B threshold ceremony re-run under farming picks t\* = −2**
(the −2 bin flips positive: 20.9% of rounds at +7.26%). Farm-mixed seated
ledger ($15 main, 200 r/h): **$25 side → +$34/h (t−3, $17.4k bank) or
+$41/h (t−2, $22.4k); $50 → +$103/+$117/h ($21–29.5k); $100 →
+$240/+$268/h ($35–50.5k)**; breakeven side stake ~$20 → **$11.4–12.5**;
wong-in at −2 ≈ +$62/$137/$289 per 200 observed. **The $25-max scenario no
longer kills the play — it matches crouch15-2r's hourly on half the
bankroll; $50+ dominates everything we own.** t=−3 maximizes $/bankroll,
t=−2 maximizes $/h. Machinery: `arm` tag through curve JSONs (mixed-arm
pooling refused; banked pre-tag dumps load as normal), 295 tests green.
Arithmetic: `data/m10b_farm_verdict.py` over `m10b_farm_p75_s*.json`.

**E21b (same day, Matt's question): the side ≤ main scenario — priced
from banked bins, no new sims (`data/m10b_matched_verdict.py`).** If the
placard ties the side to the main wager, the play becomes
**raise-on-trigger** (main $15 outside, raised to match only in the
window; flat-matching is dominated: +$12–47/h). 1:1 matching keeps
70–77% of the hourly: **$25 → +$32/h on $29.9k; $50 → +$84/h on $43.1k;
$100 → +$188/h on $46.9k (t\* tightens back to −3 at $100)**. The
insurance-style 2:1 hurts: $25 dead, $50 +$51/h, $100 +$127/h on $79k.
Optics bonus on record: raise-on-trigger bumps the main when the count
FALLS — anti-correlated with hi-lo, the opposite of the counter's tell.

**E22 DONE (same day): THE POG2 CARD — the no-division count BEATS
hi-lo-with-division.** Matt's "ultimate card" hypothesis triggered the
full derivation chain, and every reading of it lost to specialization by
measurement: (0) the RF positive end is DEAD (main EV crosses zero at TC
+5; crouch ramp −$0.47/h ON this table; $200@+4 +$7/h vs the side's
$69–300) → portfolio, not fusion; (1) new EOR-by-regression machinery
(`cli pogeor`, additive OLS stats, tens-pinned solve) gate-passed — the
main-profit regression reproduces E4a's calculator EORs at corr +0.9956
— and the side EORs say 2–8 are the fuel (7 as heavy as 3), 5/8/9
sheddable, A/T dead; hi-lo scores −0.931 as a lammer count, Red 7
−0.965, and the pivot-(−2) search winner **"pog2" −0.9726** (odd pivots
parity-unreachable); (2) head-to-head on one card stream (10 × 2M fresh
seeds, A/B): **pog2 at its pivot rung captures 106.6% of hi-lo-with-
division** (16.5% of rounds at +10.13%/unit, B-half +10.22), both
scenario objectives pick the SAME rung (RC ≤ 0 = the pivot), and **Red 7
reuse is refuted — 70%/62% capture** (the 4-point off-pivot mush, priced).
E21 replicated on fresh seeds along the way. **THE CARD: A/T −1, 3/4/6/7
+1, RED 2s +1, 5/8/9 nothing; start each shoe at 24, stake the side (and
split 5s) at 12 or below.** Ledger (pen .75, 200 r/h): untied $25/$50/
$100 → **+$49/+$133/+$300/h on $17.1k/$23.6k/$41.1k**; matched 1:1 →
+$42/+$108/+$240/h on $20.5k/$30.2k/$53.6k. Machinery:
`run_pog_eor`/`solve_pog_eors`, `search_unbalanced_level1_pivot` (E17
wrapper untouched), `run_pog_count_curves` (hilo bins == run_pog_curve,
in-test); 299 tests green. Artifacts: `data/e22_card.py` (stage 1),
`e22_run.py`/`e22_verdict.py` + `e22_eor_p75_s*.json`/`e22_cc_p75_s*.json`.

**E22b (Matt's simplicity question, same session): "hi-lo-57" TIES pog2;
KO is dead.** Matt proposed two simpler counts; measured on 10 × 2M fresh
rounds (19.4–20.3e9), four signals one stream (`data/e22b_run.py` /
`e22b_verdict.py`): his variant A IS the published KO count — pivot +4,
six points off-trigger, **35% capture, $25 stake negative — refuted**
(pivot-offset dose-response now measured: 0/2/4/6 points ≈
100/~100/70/35% capture). His variant B IS pog2 minus the red-2 gadget =
**"hi-lo-57"** (hi-lo with the 5 and 7 swapping tags; balanced): fixed
RC ≤ −5 captures **105% of divided hi-lo / 102% of pog2 — a statistical
tie** → untied +$49/+$134/+$305/h at $25/$50/$100, same as pog2. **The
practicality pick: hi-lo-57, start 10, stake at ≤ 5.** Caveat: its fixed
rung is tuned at pen .75 (pog2's pivot is pen-robust by construction) —
re-price the rung at the true pen after recon. Tag quality is equal
across all three (BC −0.973-ish); the whole game is the pivot.
**Rung-risk BOUNDED (banked-bin flatness, late session): both peaks are
plateaus — ±1 rung ≈ 3–7% of capture, ±2 ≈ 7–14%; a .70↔.80 pen move
shifts hi-lo-57's optimum ~1 rung → worst case ≈ $10–30/h at $50–100.
pog2's optimal rung provably cannot move (the pivot is TC −2 at every
depth; the EV zero-crossing is pen-independent) and it self-corrects for
dealer-to-dealer cut variation, which a fixed rung quietly leaks on.
DECISION PATH (Matt + Claude): drill pog2 as PRIMARY; hi-lo-57 stays the
certified fallback; once the trainer gets a POG mode, drill both and let
measured error rates at pace decide — execution error costs more than
the bounded rung risk.**

**THE OPERATING DOCTRINE (confirmed with Matt, 2026-07-18 late session —
the complete play in one paragraph):** count pog2 (A/T −1; 3/4/6/7 +1;
RED 2s +1, black 2s nothing; 5/8/9 nothing; start each shoe at 24) — or
its E22b-certified equal, **hi-lo-57** (hi-lo but the 5 counts nothing
and the 7 counts +1; start 10, stake ≤ 5; rung re-check at true pen
queued). Main
bet: **table minimum every round** — the main is rent, never a bet; the
RF positive end is dead (E22 step 0), so no count ever justifies raising
it. Play the **Ride Free basic chart** (always take free doubles/splits;
NOT the classic chart), no count deviations, no insurance. **At count ≤
12: stake the side, and while the side is out split 5,5 instead of free-
doubling** (the farm — the one playing deviation, unconditional at any
side stake). The tie is CONFIRMED (2026-07-19: side ≤ main, max $25),
so the play is: **main $15 outside; on trigger, main $25 + side $25;
back to $15 the moment the side comes down.** Side down → 5,5 takes the
free double again. The main game is the toll; the side bet is the
business. Felt-true expectation (E23, pen .8333, 100 r/h): **≈ +$30/h
on ~$16.6k.**

**FELT RECON LANDED (Matt, 2026-07-19):** the Silver Stack **side max is
$25** — the tier question is answered at the bottom rung; **penetration
is DEEP: one shoe cut ~1 deck (pen ≈ .833 = 5/6), the next ~1.25 decks
(≈ .79)** — far better than the .75 assumption, and the signal is
depth-fed; **pace is ~100 hands/h** (the game is slow — extra
procedure), half the 200 r/h the ledgers assumed; **split rule
confirmed: aces split once only to 2 hands, one card each; every other
pair resplits to 4** — this is EXACTLY the `RIDE_FREE` preset
(`resplit_aces=False, hit_split_aces=False, max_hands=4`), and every
attack shard (E20/E21/E22/E22b) already ran on it: nothing re-runs.
**Primary card re-confirmed pog2** on Matt's stated reason — its pivot
rung is pen-independent, while hi-lo-57's fixed rung was tuned at pen
.75 and the felt pen varies dealer to dealer. **Second recon answer
(same day): the side IS TIED — side bet ≤ main bet, 1:1** → the play is
E21b's raise-on-trigger (main $15 outside, main AND side $25 in the
window; flat $15/$15 measures ~+$13.5/h, the raise is worth it, and it
moves the main when the count FALLS — anti-correlated with hi-lo, cover
not tell). Still unknown from the felt: mid-shoe entry policy (wong
mode only). **E23 DONE — see below.**

## E18 DONE (2026-07-18): THE LOCKED CARD — crouch15-2r, certified live

**Matt's practicality critique of the E17 card, measured and answered: the
−14 leave fired in 73% of shoes (3.4 walks/h, median exit round 4 — the
algebra: RC ≈ decks_remaining × (TC − 2), so fixed off-pivot thresholds are
hair-triggers early and dead late), and 74% of the insurance value sits at
the top rung. The card collapsed to 2 rungs and slid +18 so no number a
human holds is ever negative — the walk line IS zero:**

> **Start each shoe at +6. Count hits 0 → walk. $100 at 18. $200 AND
> insurance at 22.** ($15 floor everywhere else; straight basic strategy;
> red sevens +1.)

Certified end-to-end by 12M live rounds of the LITERAL card (E18,
`data/e18_run.py` / `e18_verdict.py`, seeds 14.3–14.8e9): chart-only z =
+0.89 vs the bin prediction, rung occupancy ≤1.3σ everywhere, and the human
insurance rule ("insure iff the max bet is out") measured at **+$4.67/h =
73% of the exact ceiling** — the exact-vs-human insurance gap is now a
number, not an assumption. **Operating numbers: ≈ +$44/h ± 2 at 200 r/h
heads-up, σ ≈ $72/round, N0 ≈ 500h, ~$36k at 5% RoR; 1.7 walks/h (37% of
shoes, median exit round 10).**

**E18b (same day): THE WALK LINE IS ADVISORY.** Matt's weekday-reality call
(walking 37% of shoes to hunt fresh tables is impractical) certified on 12M
more live rounds (`variant=playall`, seeds 15.0–15.5e9): never-leave live
+$46.69 ± 4.19 vs with-leave +$47.83 ± 4.18; the leave's exact same-shoe
value is $5.83/h, walk friction refunds $2.50–6 of it → **never leaving
costs ≈ $0–3.5/h net. Weekday mode: play every round, ≈ +$40/h ± 2 on
~$36–40k, zero walks.** Walk at zero only when a fresh shoe is adjacent
(weekend/busy rooms). Same-day wong measurement (seed 14.9e9): 85% of jump
rounds come 2+ decks deep, 60% of shoes ripen (median entry round 24, then
~12 jump rounds) — the card's top half is also the busy-room back-count
play (~$65/h per 200 observed rounds on $23k; $20–29/h at real crowded
pace). Insurance pooled over 24M rounds: ~80% of ceiling, ≈ +$5/h.
**Trainer default matches the doctrine (`Config.score_leave=False`):
betting through the walk line expects the $15 floor and walking is never
scored; a settings toggle restores strict walk-line scoring for weekend
drilling. No wong mode in the trainer yet — the natural next build if
wonging gets pursued.**

Growth path on record: at a ~$42–52k roll
the 1-rung "$200 at the pivot" card is BOTH simpler and richer (115.9% of
the 3-rung, or 94% with no walking at all); then deviations, then an
insurance side count. Trainer default flipped to this card
(`CROUCH15_2R`); honest E17 correction: the $15-floor toll makes the old
3-rung card $54.70/h, not the ~$60 the ×0.935 shorthand implied.
Session-variance percentiles measured (15.6e9, 2M rounds, never-leave card):
4h sessions run mean +$192 / sd $2,048 — P10 −$2,362, P5 −$3,072, P1
−$4,480, 47.6% of sessions lose, and the MEDIAN session touches −$1,182 at
its low point (P10 low −$3,100). Expectation-setting numbers, in
EXPERIMENTS E18b.
Seed ledger through E18b: 14.9e9 wong depth, 15.0–15.5e9 E18b, 15.6e9
session variance; M10a consumed 15.7–16.6e9 (gate shards) and 16.7/16.8e9
(test pins); M10b consumed 16.9–17.8e9 (E20 curve shards; E21 farm arm
REUSED the same block deliberately — paired CRN arms, not a replication);
E22 consumed 17.9–18.3e9 (EOR shards) and 18.4–19.3e9 (count-curve
shards); E22b consumed 19.4–20.3e9 (simple-count head-to-head); E23
consumed 20.4–21.3e9 (live-card certification, both pens); E25 consumed
21.4–22.3e9 (RA-bank shards; E24 was arithmetic-only, none). **Next
unused seed block: 22.4e9+.**

## TRAINER SHIPPED (2026-07-18, second session): the crouch15 drill room

**`uv run python -m ridefree.trainer` → http://127.0.0.1:8877/** — a
zero-dependency web app (stdlib server, vanilla JS, SQLite) that drills the
chosen play end to end: real rounds from the validated engine on
STANDARD_6D_H17 (pen .75), Matt keeps the Red 7 count and plays the crouch15
card; the app knows ground truth and immediately flags wrong bet size for the
RC, basic-strategy mistakes, insurance mistakes, missed leaves, and count
drift (quiz at every shuffle + random spot checks + on-demand verify + peek).
Session summaries + lifetime stats (accuracy by decision type, most-missed
plays, count-error histogram, bet confusion, per-session history) persist in
`data/trainer.db` (gitignored). Keyboard-first UI for pace.

Design doctrine held: `play_round` and `BasicStrategy` are reused UNTOUCHED —
a replay driver re-runs the round from the shoe snapshot per decision (exact
under determinism), and the only duplicated mechanics (mid-round display
mirror) self-asserts against the engine's RoundResult every round. Decision
record in DESIGN.md; 29 new tests (254 green) incl. a random-play fuzz gate
and an oracle-player-is-error-free gate. Oracle RC excludes the current hole
card until settlement (the live-visibility convention E16/E17 priced).
Sessions replay from their recorded seed. Trainer consumes no experiment
seed blocks (clock-seeded by default, `--seed` to pin).

## E16 DONE (2026-07-18): classic blackjack priced — no-heat play does not pay

Matt's question: real spread, real dollars on his real game (6d H17 DAS
no-surrender, ~pen .75, $25–$2000 shoes at Potawatomi) — and can anything
with REAL cover (flat-looking bets) earn a decent hourly? Can indexes rescue
negative counts (the camouflage holy grail)?

**Answered by measurement (E16, EXPERIMENTS.md; ledger `data/e16_ledger.py`,
all knobs configurable — unit $, pace, ramps, game, pen):**
- **Flat play-all (perfect camo): −$15.58/h** at $25 units, 100 r/h — and
  still **−$11.72/h at the composition-PERFECT ceiling** (deviations +
  insurance). Negative counts are structural: perfect play recovers only
  ~8–9% of the deficit at TC −1..−4. The holy grail is closed by data.
- The only near-invisible positive play — flat bet + exit at TC ≤ −1 —
  makes **+$1.23/h** (ceiling +$3.59) at N0 ≈ 34,000h: breakeven perch.
- Real money needs visible correlation: 1-8 + exits **+$32.73/h** (N0 605h,
  ~$30k, corr(bet,TC)=0.84); backcount 8u at TC ≥ +2 **+$43.54/h** (money
  +1.10%, corr 0.68 but the tell is the entry pattern). Pen dominates: that
  1-8 row is $26.84 / $32.73 / $45.67 per hour at pen .70/.75/.80.
- s17 bracket: everything ~+0.2%; verdicts unchanged. Insurance ≈ +$4/h on
  a 1-8, all at TC ≥ +3.
- **EZ Baccarat remains the project's best game by every column** (E14:
  ~$92–101/h at half the N0, native camouflage, ~2–3× these hourlies).

**Follow-up sizing (same session; E16b in EXPERIMENTS.md): the CHOSEN
OPERATING POINT is the $10–$200 "crouch + leave"** — $10 flat below TC +2
(the +1 rung is breakeven, −0.07%: dollars below +2 are dead weight, the
optimal seated shape is bimodal — Matt's hypothesis, confirmed), jump to
$100/$150/$200 at TC +2/+3/+4, leave at TC ≤ −2. At 200 r/h heads-up:
**+$67.45/h, N0 255h, $25.8k bankroll, corr 0.76** at pen .75; pen
sensitivity **$55.60/$67.45/$92.01 at .70/.75/.80**. Runner-up: $15–$500,
1-16 + exits, +$83.62/h on $31.4k, corr 0.81 (equal bankroll efficiency,
more heat, rarer table). Field intel breaking the tie (Matt, ex-supervisor
at Potawatomi): low-limit tables draw the least surveillance attention.
**Recon (Matt, Saturday 2026-07-18): four $15–$1,000 blackjack tables; pen
≈ .75 as assumed; ONE table cut only a deck (~.83 — the prize seat, and
the condition that wakes the 21+3 overlay); other rules as assumed. No $10
tables seen (Saturday — weekday floor unknown). Adapted card ("crouch15",
ledger row): $15 floor, SAME $100/$150/$200 jumps, leave TC ≤ −2 →
+$63.95/h on $27.7k at pen .75; +$88.97/h on $21.8k at pen .80 (Red 7
version ≈ ×0.935). The $1,000 max is the growth path (double the jumps at
~$55k roll). Remaining unknown, now the model's biggest: weekday pace —
all numbers assume ~200 r/h heads-up.**
**Write-up: `docs/ARTICLE_BLACKJACK.md`** (a summary piece by design).

**E17 DONE (same day): the no-division Red 7 card keeps 93.5%.** New
`cli countcurve` harness (multi-signal RC bins, one pass, raw-suit
tracking) + analytic count search (`search_unbalanced_level1`): Red 7
itself is optimal in the level-1 unbalanced family (BC 0.9755 vs our
EORs) — no better custom exists there. Recommended card: IRC −12; $100
at RC ≥ 0 (the pivot — depth-exact TC≥+2 test), $150 at ≥ +2 (insure from
here), $200 at ≥ +5, leave at RC ≤ −14: **+$59.07/h, N0 307h, $27.2k,
corr 0.81 = 93.5% of the TC card, no division ever.** KO retains 88% but
dominated (bank/corr/no-leave). Ledger `data/e17_unbalanced.py`; E17 in
EXPERIMENTS.md; the Red 7 card is in ARTICLE_BLACKJACK.md. 225 tests.
Seeds 13.4e9–14.1e9 consumed. **Next unused block: 14.2e9+.**

New capability, gate-passed: per-TC curves with variance (`cli curve` /
`curvecombine`), per-TC paired deviation values (`cli deviations --json`),
and the repo's first LIVE betting simulator (`cli ramp`, bet(tc) ramps as
config — closes old STATUS item 4's "hi-lo betting simulator" gap). Ledger
arithmetic verified against three live 10M-round ramp runs (worst |z| =
2.0σ; avg bet / sd / corr match to 3 decimals); E4c's +0.23% and the
"~+1.1% next door" claim both reproduced independently. 222 tests green.
Seeds consumed: 8.9e9–13.3e9 (step 1e8; E17 continued through 14.1e9).

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
8700000001 (E14b verification), 8800000001 (E15 order bounds — quadratic
buys ~4pp on d7, Panda tail high-order; the two-count card is the human
frontier). E16 consumed 8.9e9–13.3e9, E17 13.4e9–14.1e9 (sections above).
**Next unused block: 14.2e9+.**

## NEXT STEPS (M10 closed; M11 — the hobby card — is the active question)

-1. **M11 (ACTIVE, 2026-07-19):** ~~deviation distillation~~ and
   ~~RA-index/variance layer~~ **DONE — E25** (the RA bank; honest
   per-shape numbers: walk $7.1k / sit-out $3.9k / never-leave $21.4k).
   Remaining: Matt picks the operating shape (see the M11 section's
   menu), then OOS-certify the literal human card; optional walk-pivot
   count run; weekday felt recon (floor, pace, sit-out and mid-shoe
   policy); PyPy throughput experiment.

0. ~~THE decisive field check~~ **DONE (Matt, 2026-07-19): side max $25**
   (his prior was right); **pen ≈ .79–.833** (1 to 1.25 decks cut — much
   deeper than the .75 assumption); **pace ≈ 100 hands/h**; **resplit
   rules confirmed = the RIDE_FREE preset** (aces once to 2 hands one
   card each, others to 4 — the farm's resplit assumption holds). Still
   open from the felt: side-tied-to-main (E21b scenarios priced),
   mid-shoe entry policy.
1. **M10 simulation chunks (reordered 2026-07-18 late session; the card
   came first on Matt's call):** ~~the farm arm~~ **DONE — E21**; ~~the
   no-division human card~~ **DONE — E22 (the pog2 card, beats the
   division benchmark)**; ~~live verification~~ **DONE — E23 (both gates
   pass, both pens, approximations retired)**; ~~pen at true pen~~
   **DONE — E23 ran .75 AND .8333**; ~~trainer pog2 mode~~ **SKIPPED
   (Matt shelved the play 2026-07-19)**; ~~optics/heat note~~ **DONE —
   folded into ARTICLE_POG.md's verdict section**. **M10 IS CLOSED.**
   Ledger structure note (E22 card, untied): net =
   ≈ $3.34/h per side $ at 200 r/h minus ≈ $34/h flat toll (outside leg
   −$23.8 + window $15-main leg −$10.6) → breakeven side stake ≈ **$10.3**
   (was $12.45 under hi-lo); the max sets the ceiling on a fixed-cost
   business.
2. **Older field checks (still open, lower stakes now):** the EZ table's
   Dragon/Panda paytables (40:1/25:1 assumed), side-bet maxes, cut-card
   depth; weekday blackjack pace (all crouch15 $/h assume 200 r/h heads-up);
   only if 21+3 is ever played, its pen/CSM/entry policy.
3. ~~PARKED: the WoO correction email~~ **UNPARKED (2026-07-19): the
   rule's condition fired** — the felt ($25 tied max) killed the play and
   Matt shelved it, so the correction ships. It rides along in
   `docs/ARTICLE_POG.md`, which Matt intends to put in front of Wizard of
   Odds. The article carries the full arc: identification, the exact-P(0)
   refutation (0.838228071 vs their 0.833420; real PT1 edge 8.25% not
   5.77%), the countability discovery, pog2, the live certification, and
   the honest shelving verdict.
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
uv run python -m ridefree.cli curve --rules h17 --arm ins --rounds 6000000 \
    --json data/out.json                      # E16 per-TC curve (basic|ins|full)
uv run python -m ridefree.cli curvecombine data/e16_h17_ins_p75_s*.json
uv run python -m ridefree.cli ramp --rules h17 --arm ins \
    --ramp "-0.5:1,0.5:2,1.5:4,2.5:6,3.5:8"   # live bet-ramp simulator
uv run python data/e16_ledger.py h17 p75      # the E16 cover-vs-money menu
uv run python -m ridefree.trainer             # the crouch15 drill room (web app)
uv run python -m ridefree.cli sim --rules ridefree_woo --shoe-mode csm \
    --pog [--split-fives]                     # Pot of Gold always-bet comparator
uv run python -u data/m10a_gate.py normal 15700000001 2000000  # gate shard
uv run python data/m10a_verdict.py            # pool shards, score the battery
uv run python -m ridefree.cli pogcurve --rounds 2000000 --seed S --json out.json
uv run python -m ridefree.cli pogcurve --split-fives --seed S --json out.json
                                              # E21 farm arm (pair seeds!)
uv run python -m ridefree.cli pogcombine data/m10b_rf_p75_s*.json
uv run python data/m10b_verdict.py            # E20: threshold, OOS, ledger
uv run python data/m10b_farm_verdict.py       # E21: paired deltas, farm ledger
uv run python data/m10b_matched_verdict.py    # E21b: side<=main scenarios
uv run python -m ridefree.cli pogeor --split-fives --seed S --json out.json
                                              # E22: EOR regression shard
uv run python data/e22_card.py                # E22 stage 1: EORs, gate, search
uv run python -u data/e22_run.py SEED 2000000 out.json  # E22 stage 2 shard
uv run python data/e22_verdict.py             # E22: head-to-head, THE CARD
uv run python data/e22_positive_end.py        # E22 step 0: RF positive end dead
uv run python -u data/e22b_run.py SEED 2000000 out.json  # E22b shard
uv run python data/e22b_verdict.py            # E22b: hi-lo-57 vs pog2 vs KO
uv run python -u data/e23_run.py SEED 2000000 out.json 0.8333  # E23 live shard
uv run python data/e23_verdict.py             # E23: live card gates + ledger
uv run python data/e24_hobby.py [15 15 200]   # E24: min-bank hobby frontier
uv run python -m ridefree.cli rabank --rounds 4000000 --seed S \
    --json data/e25_ra_p75_sNN.json           # E25: RA-bank shard (~7 min)
uv run python data/e25_ra.py [15 15 200]      # E25: gates + the RA card
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
- `docs/ARTICLE_BLACKJACK.md` — the E16 standard-blackjack summary (the
  cover-vs-money ledger, the crouch, the chosen $10-table operating point).
- `docs/ARTICLE_POG.md` — the Pot of Gold / Silver Stack write-up (M10
  arc: the P(0) refutation, the lammer count, pog2, live certification,
  the shelving verdict; written for a Wizard of Odds audience).
- `src/ridefree/baccarat.py` — the M9 engine (rules, tableau, exact
  enumeration, simulator); gates in `tests/test_baccarat.py`; ledger
  `data/e14_verdict.py`.
- `src/ridefree/trainer/` — the crouch15 drill-room web app (card as data,
  replay driver, session checker, SQLite store, stdlib server + static UI);
  gates in `tests/test_trainer.py` / `test_trainer_server.py`; decision
  record in DESIGN.md.
- `docs/STATUS.md` — this file. Update it at every session checkpoint.
- `data/` — banked grid JSONs (E2, E3 shards; additive bin stats),
  `e12_verdict.py` (the E12 ledger arithmetic), `m10a_gate.py` /
  `m10a_verdict.py` + `m10a_*.json` (the M10a token-histogram gate),
  `m10b_verdict.py` + `m10b_rf_p75_s*.json` (the E20 attack bins — any
  threshold/ramp/side-max reprices by arithmetic over these),
  `m10b_farm_verdict.py` + `m10b_farm_p75_s*.json` (the E21 farm arm,
  seed-paired with the E20 shards), `m10b_matched_verdict.py` (E21b),
  `e22_card.py` + `e22_eor_p75_s*.json` (E22 stage 1: EOR regression +
  search), `e22_run.py`/`e22_verdict.py` + `e22_cc_p75_s*.json` (E22
  stage 2: the pog2 head-to-head and card ledger).
