# Experiment log

Newest first. Every experiment is reproducible from (git commit, CLI command, seed).

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
