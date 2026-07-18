# Deep-dive strategy hunt — 2026-07-17

Question: is there a way to beat Ride Free (or materially improve the best-known
system) that E1–E5 never explored? Method: six independent idea-generation lenses
(AP practice, composition-signal math, rule-structure exploits, count engineering,
methodology re-examination, bankroll/operations) produced 44 candidates; a
three-judge panel scored them; the top cluster was executed the same session with
**fresh seeds spaced ≥ 2×10⁸ apart** (immune to the shoe-seed-overlap flaw — see
DEEP_DIVE_AUDIT.md). Everything below regenerates from committed data in `data/`
plus the two measurement scripts banked there.

## New measured results (E6–E9)

### E6 — Free-double signal: subsumed. Wong-in EV: certified lower.

`grid --rules ridefree --row rf_ev --col p_free_double --rounds 3000000` × 4 shards,
seeds 900000001 / 1100000001 / 1500000001 / 1700000001 → `data/e6_pfd_shard*.json`.

- **Pooled within-rf_ev p_free_double slope: −0.03% ± 0.05% per +0.01. Null.**
  Together with E4b (pairs), the RF count now provably subsumes *both* event
  signals — the composition-targeting idea that started the project is fully
  priced by the game's own linear count.
- **Fresh wong-in @ rf_ev ≥ +0.0125: +0.51% ± 0.12%** (12M rounds; the four shards
  scatter +0.19…+0.79%, consistent with independent noise). The published +1.04%
  reproduces exactly from the old contaminated shards — the pipeline was right,
  the data was not.
- RF-count calibration slope (realized EV per unit predicted shift): **0.93–0.97**
  — essentially perfectly calibrated; E4b's 0.75 was a contaminated-data artifact.

### E7 — Joint (rf_ev × hilo_tc): dominance closed; camouflage thesis measured and refuted

`grid --rules ridefree --row rf_ev --col hilo_tc --rounds 3000000` × 3 shards, seeds
3400000001 / 3500000001 / 3600000001 → `data/e7_joint_shard*.json` (9M rounds).

- **Dominance (E4b's open question): CLOSED.** Within-rf_ev hi-lo residual slope =
  +0.02%/TC ± 0.04% — null. Hi-lo adds nothing at fixed RF count; the suspected
  resplit-EOR sharpening is unnecessary, and the parked re-derivation can be
  retired.
- **Camouflage fraction, measured for the first time: the thesis dies.** Only
  **3.2%** of wong-in rounds (@ +0.0125) occur at hi-lo TC ≤ +1: 96.8% of RF
  entries happen exactly when standard count-surveillance already sees a hot shoe.
  (At the looser +0.0075 threshold: 12.4%.) ARTICLE's "bet trigger correlates only
  weakly with the running count… reads as a hunch player" is refuted by
  measurement. Residual nuance: the RF player's *threshold* differs from a hi-lo
  player's (only 32% of TC ≥ +2 rounds are RF-playable), so entries look like a
  conservative counter, not a non-counter.
- Independent frontier check: wong-in @ +0.0125 = +0.70% ± 0.14% on this dataset.
- **Certified wong-in EV, pooling E6+E7 (21M fresh rounds): +0.59% ± 0.09% at
  6.6% of rounds.** Threshold frontier (fresh): +0.21% @ 14.5% · +0.51→0.70% @
  6.6% · +0.78% @ 4.4% · +0.99% @ 2.9% · +1.41% @ 1.9%.

### E8 — Window-conditional deviation value, properly powered: +0.32%

Paired differential replay run *only inside the window* (~7× cheaper per window
round; script `data/e8_window_deviations.py`), 4 × 1M rounds, seeds 1900000001 /
2100000001 / 2300000001 / 2500000001 → `data/e8_wdev_shard*.json`.

- **Deviation value @ rf_ev ≥ +0.0125: +0.322% ± 0.063%** (264k paired window
  rounds, 5σ). Larger than E5's underpowered +0.20% ± 0.13% (measured at the wrong
  threshold, 0.0075) — deviations are worth more where compositions are extreme.
  Perfect-information ceiling; 3.4% of window rounds change profit.

### E9 — Insurance: a real, unmodeled EV source worth +0.15%/window round

Insurance appears nowhere in the engine or docs, yet Free Bet tables offer it and
the wong-in window is selected for exactly the ace/ten-rich shoes where it pays.
Perfect-tracking overlay (take iff p(hole=ten) > 1/3, stake 0.5, pays 2:1; script
`data/e9_insurance_overlay.py`), 1M rounds, seed 1300000001 → `data/e9_insurance.json`;
independently replicated by a workflow probe (300k rounds, seed 999999937, +0.157%).

- All rounds: +0.023%/round (negligible — insurance stays a sucker bet off-window).
- **@ rf_ev ≥ +0.0125: +0.153% ± 0.004% per played round.** In-window the dealer
  shows an ace 9.2% of rounds (vs 7.7% base) and ~45% of those are +EV insurance.
- Perfect-information ceiling; the classic ten side count captures most of it
  (capture fraction unmeasured — top of the next-session list). Rack-card check
  needed: confirm insurance is offered at Potawatomi's Ride Free table.

### Sit-out wonging — seated verdict softens to breakeven, does not flip

Pre-registered policy (1-8 rf_ev ramp; bet 0 below a floor) from the banked-grid
arithmetic, evaluated on 12M fresh rounds (E6 marginals):

| Policy | units/100 rounds | edge on money | plays |
|---|---|---|---|
| Bet every round (E4c-style) | −0.90 | −0.44% | 100% |
| Sit out below rf_ev 0 | **−0.08** | **−0.05%** | 50% |

The contaminated banked grids had promised +0.17 u/100; clean data says **breakeven,
not profit**. Honest reframe: sitting out kills ~90% of the seated toll, making the
seat a **free camouflage perch between wong-in windows** — but not a profit center.

## The corrected best-known system

Per played round at rf_ev ≥ +0.0125 (~6.6% of rounds), all components fresh-seed:

| Component | Old claim | Certified 2026-07-17 |
|---|---|---|
| Bet selection (wong-in) | +1.04% | **+0.51…0.70% (pooled +0.59% ± 0.09%)** |
| Composition deviations (ceiling) | ~+0.2% | **+0.32% ± 0.06%** |
| Insurance overlay (ceiling, new) | — | **+0.15%** |
| **Stack** | **"~+1.2%"** (no error bar) | **≈ +1.06% ± 0.11%** |

The total lands near the old headline *by coincidence*: the wong-in haircut is
offset by a bigger deviations term and the new insurance term. But the composition
changes what to work on — half the edge now comes from play-time information
(deviations + insurance), both of which are perfect-information ceilings whose
human-capture fractions are unmeasured. And the two verdict-level facts move
against Ride Free: the camouflage differentiator is measured-and-mostly-dead, and
standard blackjack next door still offers ~3× the playable volume at comparable
per-round EV.

## Ranked go-forward plan (post-results update of the judged synthesis)

> **Closed without pursuit (Matt, 2026-07-17):** with the verdict certified —
> Ride Free beatable at ≈ +1.0%/played round on 6.6% of rounds but strictly
> dominated by standard blackjack — the human-capture and economics items below
> are deliberately not being executed. The list is preserved as the roadmap if
> the project is ever reopened (e.g., rack card reveals a Push-22 side bet or
> unusually deep penetration).

1. **Insurance human-capture + engine promotion.** Extend E9: realized-settlement
   track, capture fraction for three human rules (hi-lo TC ≥ +3, RF-L2 ≥ +3, ten
   side count), covariance with round profit. Adopt into the headline if a human
   rule captures ≥ 50%. Then (only if adopted) add insurance to the engine as
   `Rules` data, validated against the published 6-deck off-the-top insurance EV
   first. *(small-code; ~15 min of runs)*
2. **RF "Illustrious 18" distillation.** E8 proves +0.32% exists; mine the paired
   logs for which decision cells carry it, derive RF-L2 index numbers from the
   calculator, certify a rule-list strategy vs OptimalStrategy (target ≥ 60%
   capture). The deliverable is the first published Free Bet deviation index.
   *(small-code scratch harness; ~30 min of runs)*
3. **Bankroll economics on banked variance (arithmetic only).** Kelly quality
   re-rank (preliminary: RF window EV/variance may beat standard's per played
   round — the "equal quality, 3× volume" framing was never variance-adjusted),
   growth-optimal threshold (likely below +0.0125), $/hr with back-count dead
   time, two-table RF+standard portfolio using E7's joint distribution (overlap
   is now measured, not assumed). *(zero simulation; uses `profit_sq` already
   banked in every BinStat)*
4. **Sit-out realism FSM.** Certify the breakeven perch under entry/exit
   hysteresis, capped consecutive sit-outs, and a hole-card-masked tracker (the
   tracker currently sees the hole card in ~20% of rounds a human wouldn't).
5. **Retired by today's results:** resplit-aware EOR re-derivation and the
   empirical-EOR regression (E7 dominance null closes E4b's question); the
   rf_ev × p_free_double cell (E6 null); quadratic/second-order composition
   signals (power analysis says ~50M rounds per test — post-Rust).
6. **Parked on physical ground truth (Matt's rack-card visit):** Push-22 side bet
   counting (potentially large, entirely gated on whether it's offered and its
   paytable), penetration sweep (needs the actual cut depth), S17/soft-double
   rule-sensitivity, multi-spot play (needs engine surgery + its own validation
   gate).

## Seed registry addendum (all consumed 2026-07-17, deep-dive session)

E6: 900000001, 1100000001, 1500000001, 1700000001 · E7: 3400000001, 3500000001,
3600000001 · E8: 1900000001, 2100000001, 2300000001, 2500000001 · E9: 1300000001
(+ workflow probe 999999937) · audit csm/cut-card runs: 987654321, 123456789,
31415926, 24680 (+ seed-9999 reconstructions, which — note — sit inside the
contaminated low-seed range). Future runs: use hash-derived shoe seeds or keep
base-seed spacing ≥ 10⁸.
