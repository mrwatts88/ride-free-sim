# Deep-dive correctness audit — 2026-07-17

Method: nine specialist review passes (engine rules, money ledger, EV-calculator math,
counting/EOR, experiment statistics, simulator/shoe, validation gates, test suite,
docs-vs-code) produced 41 raw findings, deduplicated to 30. Each finding then faced
adversarial verification by up to two independent reviewers — one required to refute
by *running code*, one by re-deriving the math — with a finding surviving only if no
verifier could kill it. A session usage limit cut off 24 of the verifier votes;
findings that lost both votes are listed as an **unverified backlog** below (a few of
those were subsequently spot-verified by the orchestrating session and are marked so).
All demonstration numbers below were reproduced from committed code/data during the
audit itself.

## Bottom line

**The engine's money math is clean.** No settlement, ledger, dealer-play, or
free-bet-funding defect survived verification, and the audit's own new csm-mode runs
validate the engine *more* strongly than the project ever claimed: off-the-top
`RIDE_FREE_WOO` measures **1.063% ± 0.043% vs the published 1.04%** (+0.5σ) over 6M
fresh rounds. The real defects are concentrated in the **statistics of the experiment
campaign** and in **published claims that outrun the committed evidence**. The single
structural root cause: sequential shoe reseeding (`seed + shuffle_count`) silently
destroyed the independence of every "replication" in E2–E5.

---

## Confirmed — high severity

### 1. `shoe-seed-overlap` — "independent" shards replay 95–98% identical rounds

Every experiment loop derives successive shoe seeds as `base_seed + shuffle_index`
(`simulator.py:126`, `experiments.py:113/247/332`). A 3M-round run spans ~70,600
sequential shoe seeds (~42.5 rounds/shoe), so any two runs whose base seeds differ by
less than that replay byte-identical shoes — and deterministic strategies make the
rounds byte-identical too. Measured pairwise overlap: E3 shards (1111/2222/3333/4444)
95.3–98.4%; E2 (4242) vs E3 up to 99.7%; E4b (5555/6666) 98.4%; E5 (7777/8888) 68.5%;
E1 (31337) vs E2 61.6% — so the pair hypothesis was never tested on data disjoint
from the data that generated it.

Corrected headline statistics (point estimates are nearly unbiased; the *precision
and replication* claims are what fail):

| Published | Corrected |
|---|---|
| E2+E3 pair slope +0.626% ± 0.094% (**+6.6σ**) | ± ~0.21% (**≈ +3.0σ**) |
| E3 "four independent shards agree tightly" | tautological — shard-slope sd 0.034% vs ~0.20% expected under independence (χ²₃ ≈ 0.07, p ≈ 0.005 *against* independence) |
| E4b pair-null −0.079% ± 0.129% | ± ~0.19% (null stands, shard "agreement" near-tautological) |
| E5 deviations +0.119% ± 0.046% (+2.6σ) | ± 0.060% (+2.0σ) |
| E5 wong-in window +0.20% ± 0.13% (+1.5σ) | ± 0.169% (+1.2σ) |

Every "fresh seeds", "independent shards", and "replicated across five independent
seeds" statement in EXPERIMENTS.md (E2–E5), STATUS.md, and ARTICLE.md is unsupported
as written. Demonstration recipe (seconds): replay the grid loop from seed 1111 —
after 47,230 rounds it reaches shoe seed 2222, and its next 5,000
(shoe_seed, signals, profit) tuples equal a fresh seed-2222 run's first 5,000 exactly.

**Fix for future runs:** derive shoe seeds non-sequentially (e.g. a per-run
`random.Random(base_seed)` drawing 64-bit shoe seeds, or `hash((base_seed, k))`), or
enforce base-seed spacing ≥ 10⁸. The 2026-07-17 deep-dive experiments (E6–E9, see
DEEP_DIVE_STRATEGY.md) used spacing ≥ 2×10⁸ throughout.

### 2. `e4c-crossfit-in-sample` — the +1.04% wong-in headline was effectively in-sample

E4c's stated protection ("cross-fitted: thresholds selected on one dataset, profit
evaluated on independent seeds") fails twice: (a) the only rf_ev grids (E4b
5555/6666) share 98.4% of shoes, so selection and evaluation ran on ~98%-identical
data; (b) the standard-game row (+0.23%) had exactly one grid and could not be
cross-fitted at all — EXPERIMENTS.md admits this; ARTICLE.md drops the caveat.
Honest SE for the +1.04% figure is ±0.237% (~200k unique window rounds), before any
threshold-selection optimism. **Fresh-seed re-measurement (21M independent rounds,
this session): wong-in @ rf_ev ≥ +0.0125 = +0.59% ± 0.09%** — the published figure
was roughly 1.8σ optimistic, in the direction selection effects predict.

### 3. `m4-caveat-refuted-by-csm` — the documented explanation of the M4 gate reading is wrong

ROADMAP attributes `RIDE_FREE_WOO` reading 0.99% under cut_card (below published
1.04%, with the cut-card effect "pushing the other way") to argmax-EV play beating
WoO's simplified chart. The csm run the caveat itself prescribes — executed by the
audit — refutes both parts: off the top the engine reads **1.063% ± 0.043%**
(matches published; measured "strategy gain" ĝ = **−0.02% ± 0.04%**, i.e. none), and
the Ride Free cut-card effect measures **−0.06% ± 0.06%** (zero-to-negative — the
standard game's +0.03–0.07% note does not transfer to this variant). The engine is
fine; both documented explanations are wrong, and the gate's cut_card reading remains
genuinely unexplained (plausibly the mode effect and a small strategy effect
partially cancelling — see `gate-shoe-mode-mismatch`).

---

## Confirmed — medium severity

- **`min-cell-estimand-shift`** — `pooled_slope`'s fixed `min_cell=2000` admits
  sparser, more extreme cells as shards are merged, changing the estimand: E3 merged
  reads +0.654% while every shard reads ≤ +0.598% on ~98% the same data. At
  density-matched thresholds the E2+E3 slope is **+0.55%**, not +0.626% (and E4b's
  null becomes −0.17% at matched density). The tails are genuinely steeper (verified
  by bootstrap), but the published shard-vs-merged comparisons mix two estimands
  without disclosure.
- **`wongin-headline-stacking` / `rf-l2-run-unrecorded`** — ARTICLE publishes +0.74%
  (prose) and +1.04% (table) for the same wong-in quantity without reconciliation,
  and stacks the higher one with a +1.5σ deviation bonus measured on a *different*
  (wider) window; no error bar accompanies "+1.2%" anywhere. The head-to-head run IS
  recorded (seed 9999, commit `1106e20` — the finding's "unrecorded" charge was
  corrected), and hi-lo +0.63% / RF-L2 +0.72% regenerate exactly — but the
  **perfect-count +0.74% does not regenerate** (the same run yields ~+0.87–0.90% at
  matched frequency), so "RF-L2 captures essentially all of it" is unsupported; the
  same-shoe RF-L2-to-perfect gap is ~0.2–0.3%, not 0.02%. Note seed 9999 also sits
  inside the contaminated low-seed shoe range.
- **`rounds-changed-mislabel`** — `rounds_changed` counts *profit*-differing rounds;
  the docs publish it as "rounds that change any action". True action-change rate:
  **3.7%** (not 2.1%); gain per action-changed round **≈ +3.2%** (not 5–6%). The
  headline +0.119% deviation value is unaffected.
- **`z-pass-window-too-wide`** — the ±4σ house-edge gate tolerates silent systematics
  of ±0.19% (5M rounds) to ±0.33% (2M CLI default) — 18–53% of the entire house edge.
  z-scores are printed, so "silent" applies to the PASS/FAIL decision only; still,
  the gate cannot support "matching published EVs exactly" phrasing.
- **`gate-shoe-mode-mismatch`** — the one hard external check compares a cut_card
  observation to an off-the-top published reference in the same row. For Ride Free
  this conflates two opposite-sign systematics (mode effect ~+0.02–0.05% on house
  edge by theory, strategy effect unknown), and the HTML report doesn't record which
  shoe mode produced it. A correct engine would deterministically FAIL this gate at
  ~44M+ rounds.

## Plausible (single-vote split)

- **`advisory-checks-as-gate-evidence`** — every published-figure check except house
  edge (dealer-22 vs WoO, std dev) is `advisory=True` and can never fail, yet
  ROADMAP/ARTICLE cite these agreements as validation evidence with equal billing.

## Refuted (claims that did NOT survive — good news)

- **`e4c-ramp-irreproducible`** — REFUTED. All 12 numbers in the E4c ramp table
  regenerate to the published rounding from committed `data/*.json` via the
  procedure stated in the E4c method line (both verifiers reproduced them
  independently). The reproducibility contract holds here.

## Orchestrator-verified additions

- **Insurance is absent and undisclosed** (grep: zero mentions in src/tests/docs).
  It is not a validation error (published edges exclude insurance) but it is a real
  EV omission for the attack phase — quantified at **+0.15%/window round** in
  DEEP_DIVE_STRATEGY.md (E9).
- **`Rules.split_by_value` is dead config** — defined at `rules.py:51`, read nowhere;
  its `False` mode promises a matched-rank-only distinction the 10-collapsed card
  model cannot represent. Delete or implement.
- **Docs drift**: STATUS says "140 tests"; the suite has 149.

## Unverified backlog (verifier votes lost to the session limit)

Ordered by likely importance; none is known-false. `article-csm-overclaim` (ARTICLE
generalizes "off-the-top runs match published figures" beyond the one config tested
at the time — now retroactively supported for ridefree_woo by the audit's own csm
runs); `m3-dealer22-coverage-gap` and `resplit-aces-path-untested` (claimed gate
coverage vs actual test cells); `tracker-hole-card-assumption` (tracker counts the
hole card in the ~20% of rounds the dealer never plays out — fine for ceilings,
optimistic for human-count claims); `game-ev-resplit-blind` (RIDE_FREE and
RIDE_FREE_WOO produce identical calculator EVs since resplit_aces is never read
there); `auto-stand-21-overclaim` (auto-stand at 21 is provably suboptimal for a
casino-funded hand only under `free_double_soft_allowed=True` — latent, not
Potawatomi); `dealer-oracle-not-independent`; `agg-dealer-se-misspecified`;
`published-refs-hardcoded`; `game-ev-no-peek-silent`; `calc-split-ace-double-gap`;
`free-double-signal-hardcoded`; `min-cards-floor-miscalibrated`;
`dealer-final-docstring-wrong`; `e4b-fraction-inconsistency`;
`tracker-invariant-single-point`; `eor-tests-signs-only`.

---

## Recommended corrections (concrete)

1. ✅ APPLIED 2026-07-17 — **EXPERIMENTS.md / STATUS.md / ARTICLE.md**: E2/E3
   restated at ≈ +0.55–0.63% ± 0.21% (≈ +3σ, single effective sample) with
   bracketed audit-correction notes under E3/E4b/E4c/E5; the "five independent
   seeds"/shard-agreement claims corrected inline in ARTICLE.md; E5 restated
   (±0.060, action-change 3.7%, ≈ +3.2%/changed round).
2. ✅ APPLIED 2026-07-17 — wong-in headline replaced with certified numbers in
   ARTICLE.md (marked corrections) and STATUS; the +0.74% figure and "RF-L2 ≈
   perfect" claim corrected (perfect ≈ +0.9% at matched frequency, gap 0.2–0.3%).
3. **Rewrite ROADMAP's M4 "honest caveat"** with the csm result (engine validates
   off-the-top; strategy-gain explanation refuted; RF cut-card effect ≈ 0 to
   negative). — left as-is: M4's section is a historical gate record; the
   correction lives here and in the E-series notes.
4. **Fix shoe-seed derivation** — ✅ APPLIED 2026-07-17: `cards.shoe_seeds()` now
   draws 63-bit shoe seeds from a base-seeded RNG; all four loops + the demo use
   it. Determinism preserved (149 tests pass; same-seed reruns bit-identical);
   base seeds 1111 vs 2222 now share 0 of 100k shoe seeds. Note: reruns of
   pre-fix commands produce statistically equivalent but not bit-identical
   output; the banked `data/*.json` remain valid as data.
5. Mechanical: ✅ `rounds_changed` relabeled AND true action-change counting added;
   ✅ `split_by_value` deleted; ✅ insurance now modeled outright (gate-validated);
   ✅ test count updated (161). Still open: record shoe mode in the HTML
   validation report.
