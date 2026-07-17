# STATUS — read this first in a new session

Updated 2026-07-17. This is the resume-here document: current state, key numbers,
and the precisely-specified next step. Doc map at the bottom.

## Where the project stands

Goal (Matt's framing): simulate Potawatomi's **Ride Free** blackjack (Free Bet
variant), first matching published EVs exactly, then beating the game with
"accounting systems" — count/composition-based betting. Milestones M0–M5 are ✅ done
with validation gates met (see ROADMAP.md). We are in **M6a, the attack phase**, and
have one confirmed discovery.

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

Key artifact: `counting.rf_ev_shift()` — the first game-specific linear count for
Free Bet blackjack, denominated directly in predicted EV. RF EORs vs standard:
tens halved, ace ≈ 3× the ten, 3/4/5/7 collapse, 8 flips negative.

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

## Candidate next steps (Matt to choose)

- **Practical distillation:** human-trackable versions of the RF count and the top
  deviation rules; quantify edge lost per simplification. (The "teach a human"
  step.)
- **Resplit-aware EOR re-derivation:** suspected to sharpen the RF count; also
  settles E4b's open dominance question.
- **Bankroll/risk analysis:** variance, risk-of-ruin, hourly $ for the wong-in
  system at real table conditions (penetration sweep, spread limits).
- **M6c / M7:** full hi-lo certification; Rust core if sweeps grow.

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
uv run pytest -q                                   # 140 tests
uv run python -m ridefree.cli demo --rules ridefree --seed 44 --hands 6
uv run python -m ridefree.cli sim --rules ridefree --rounds 2000000
uv run python -m ridefree.cli validate --rules {h17,s17,ridefree,ridefree_woo}
uv run python -m ridefree.cli signals --rules ridefree --rounds 3000000
uv run python -m ridefree.cli grid --rules ridefree --row hilo_tc --col p_pair \
    --rounds 3000000 --json data/out.json
uv run python -m ridefree.cli combine data/e2_ridefree_grid.json data/e3_shard*.json
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
  Rust decision record.
- `docs/ROADMAP.md` — milestones M0–M7 with gates and results.
- `docs/EXPERIMENTS.md` — experiment log E1–E3 (newest first), reproducible.
- `docs/STATUS.md` — this file. Update it at every session checkpoint.
- `data/` — banked grid JSONs (E2, E3 shards); bin stats are additive.
