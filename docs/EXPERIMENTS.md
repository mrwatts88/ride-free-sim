# Experiment log

Newest first. Every experiment is reproducible from (git commit, CLI command, seed).

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
