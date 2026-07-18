# STATUS — read this first in a new session

Updated 2026-07-17. This is the resume-here document: current state, key numbers,
and the precisely-specified next step. Doc map at the bottom.

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

Seeds consumed: 6.4e9 block (gate + tests), 6500000001, 6600000001–2.
Next unused block: **6.7e9+**.

## NEXT STEP (start here): M8c — the 21+3 attack

Per ROADMAP.md M8c: suit-aware CompositionTracker (per-(rank,suit) counts of
the remaining shoe); exact hypergeometric P(flush)/P(straight)/P(trips) as
pre-deal signals; reuse the conditional-EV and grid harness verbatim;
EOR-style derivation if a linear count is wanted. Prior art expects the edge
to swing mainly on suit imbalance (flush richness). Experiments are E10+ on
fresh seeds (6.7e9+ block), per-experiment log discipline in EXPERIMENTS.md.

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
