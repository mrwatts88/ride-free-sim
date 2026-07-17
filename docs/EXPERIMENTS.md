# Experiment log

Newest first. Every experiment is reproducible from (git commit, CLI command, seed).

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
