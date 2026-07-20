# Experiment log

Newest first. Every experiment is reproducible from (git commit, CLI command, seed).

## E29 — M12b rung 3a: the O(slots) assumed-density posterior GATED; the copy tax isolated from the mixing debt; the 8-deck door opened

**Date:** 2026-07-19 · **Question:** the PF's O(particles × slots) cost is
the wall in front of any 8-deck number (E28), and the copy-vs-mixing
confound was left tangled. Build a posterior whose cost is independent of
particle count, measure its bias instead of assuming it, and run the clean
same-n isolation.

**Machinery (new; `posterior.AssumedDensityShelfPosterior`, decision record
in DESIGN.md):** the exact filter's sufficient statistic with copy
ambiguity softened — per-position fractional occupancy + ONE deferred
chain over the last dealt slot. Distinct stacks reduce to the rung-1 exact
posterior deterministically (gated 1e-9); copies bring four structural
rules, each the cure for a measured failure on E28's probe shoes: capped
water-fill subtraction (per-class occupancy is EXACT bookkeeping — without
the cap, leaked mass walls off the slot axis), the 1e-9 occupancy hedge
(no hard survival walls for copy classes), chain-defers-to-occupancy
(strand truncation + in-class certain-dealt repair + last-resort chain
reset, counted in `surprises`), and the ε-contamination output floor `MIX`
(robust-Bayes humility: 6/40 3-deck shoes drifted to a p≈1e-72 claim on a
5% card — one −234-bit step; the floor bounds any step at log2(MIX)).
Deterministic — no filter RNG; O(positions) `copy()`. `mpe` gained
`method="adf"`, `adf_mix`, and `observer="class"|"position"` (the
isolation instrument) with CRN-identical rng consumption across arms.
341 tests green (6 new incl. the bias-envelope pin: worst tiny-lane
one-step gap 0.52 where the true law is deterministic — mean-field cannot
express hard global order constraints; real configs sit nowhere near that
regime).

**Findings (`data/e29_adf.py`, seeds 23.1e9, banked `e29_adf.json`):**

| part | row | u/shoe | bits/shoe | z | ms/shoe |
|---|---|---|---|---|---|
| 1 | d2 pf(120) / adf | +26.1 / +23.0 | 23.7 / 18.3 | +2.00 / +1.62 | 1849 / 29 |
| 1 | d3 pf(120) / adf | +32.2 / +32.9 | 17.1 / 20.0 | +0.50 / +0.45 | 4196 / 55 |
| 2b | d8 adf mix=.40 OOS | **+53.0** | +13.0 | **−1.70** | 373 |
| 3 | d2 position / class | +28.6 / +19.2 | 35.3 / 17.3 | +0.75 / +0.25 | — |
| 3 | d3 position / class | +42.2 / +26.6 | 64.1 / 20.3 | −0.87 / −1.37 | — |
| 3 | d4 position / class | +70.3 / +44.6 | 92.3 / 12.4 | +1.08 / −0.61 | — |
| 4 | d2 2-pass control | −0.4 | −11.0 | −2.37 | 582 |

1. **The throughput wall is down**: 57–76× the PF at equal (d3: better)
   fidelity, 1-deck rows bit-identical to the PF (both exact), and the
   8-deck walk at 0.4 s/shoe.
2. **The first calibrated 8-deck number**: MIX fitted on a fit block
   (rule fixed in advance: smallest mix with bits>0 and |z|<2 → 0.40),
   then OOS on fresh seeds: **+53.0 u/shoe realized at 83 bets/shoe,
   z −1.70 — the gate passes**. E28's do-not-extrapolate flag is resolved
   by measurement: the order channel SURVIVES 8 copies at one pass
   (u/shoe by decks: 8.7 → 23.0 → 32.9 → 53.0). Honesty: realized ≈ 0.83×
   predicted (within CI at 80 shoes, but the sign is consistent —
   claims carry a visible haircut), MIX 0.40 means the output is 40%
   composition, and `surprises` run 52/shoe at 8 decks: the tool is
   CALIBRATED-BY-CONTAMINATION, not clean.
3. **The copy tax and the mixing debt, finally separate** (same-n,
   same-seed pairs): the position-resolution observer's bits GROW with n
   (8.8 → 35.3 → 64.1 → 92.3 at n=52..208 — the fixed 10-shelf machine's
   mixing debt in information units, the ~n^1.5 shortfall made visible),
   while copy-indistinguishability at fixed n costs 51% / 68% / 87% of
   those bits at 2/3/4 decks. Both of E28's "two fights" quantified; the
   surviving units still grow with n (+19 → +27 → +45/shoe). d4-class
   carries an instrument caveat (surprises 6.2/shoe; no PF referee ran
   at d4).
4. **The two-pass fix holds at the REALIZED level** (−0.37 u/shoe ≈ 0)
   but the ADF's 2-pass CLAIMS are junk (6.7 bets/shoe fired, z −2.37,
   bits −11): the filter's projection noise exceeds the ~zero residual.
   Instrument limit on record: the ADF cannot hunt 2-pass machines; only
   its realized-profit readout (or the exact rung-1 machinery) can
   certify a fix.

**Scope:** value-level composition-fair units, NOT game currency (E30 is
the real-paytable conversion); observer premise remains full knowledge of
shoe k. Artifacts: `data/e29_adf.py`, `data/e29_adf.json`.

## E28 — M12b rung 2: the order channel under copy ambiguity (multi-deck) — it survives, but the copy tax and a throughput wall are real

**Date:** 2026-07-19 · **Question:** rung 1 found a huge order channel on a
single distinct-card deck, but a multi-deck shoe hides each rank+suit behind
`decks` indistinguishable copies. Does that copy ambiguity destroy the edge,
and can the posterior even be computed honestly at multi-deck scale?

**Machinery (new; `posterior.MultiDeckShelfPosterior`, decision record in
DESIGN.md):** exact multi-deck filtering is permanent-hard (copies break the
label-sort's per-slot owner), so this is a sequential-importance particle
filter — each particle is a rung-1 `ShelfPosterior` over the distinct input
positions carrying one hypothesis of which copy produced each observed value;
locally-optimal proposal (sample the next position from the exact conditional
restricted to the observed value, weight by that value's marginal), systematic
resampling at ESS < N/2, `ShelfPosterior.copy()` for cloning. Adapter:
`multideck_proposition_experiment` (the composition-fair value bet — perfect
counter = 0 — through the filter). 335 tests green (3 new multi-deck gates).

**Gates (tests/test_posterior.py):** brute force — the filter's next-value law
equals full lane-assignment enumeration through the independent physical pile
sim, within particle MC error, at every step (tol 0.05 at 4000 particles);
first step exact regardless of particle count; **all-distinct values reduce to
the rung-1 exact posterior deterministically** (no variance). All pass.

**The PyPy decision (the parked M7 experiment, run here):**
`data/bench_pypy.py` under PyPy 3.11 vs CPython 3.14 — **bit-identical
checksums, 4.3× on the posterior walk (the M12 hot path), 2.7× on the engine,
full 335-test suite green** (and 2.3× faster). PyPy is the sanctioned
accelerator for the heavy multi-deck/baccarat runs; only friction is
`requires-python >=3.12` vs PyPy's 3.11 ceiling (run via `PYTHONPATH=src uv
run --python pypy@3.11 --no-project`, or relax the pin — Matt's call). Rust
stays unneeded.

**Findings (probe scale under PyPy, 10-shelf machine, composition-fair
baccarat-value-8 proposition; `data/e28_multideck.json`):**

| decks | passes | n | bets/shoe | edge/bet | u/shoe | bits/shoe | z |
|---|---|---|---|---|---|---|---|
| 2 | 1 | 104 | 25.1 | +83.7% | +21.0 | 18.2 | −0.18 |
| 3 | 1 | 156 | 35.7 | +49.3% | +17.6 | 9.3 | −3.07 |
| 2 | 2 | 104 | 0.0 | — | 0.0 | 0.035 | — |

1. **Copy ambiguity does NOT obliterate the channel at 2–3 copies.** A 2-deck
   shoe through one 10-shelf pass leaks +21 u/shoe (18.2 bits), gate-clean
   (z −0.18); 3 decks still +17.6 u/shoe. The observer inverts the shuffle
   through the copy fog.
2. **The bits trend is NON-MONOTONIC — do NOT extrapolate to 8 decks.**
   bits/shoe went **9.0 (1 deck, E27) → 18.2 (2) → 9.3 (3)** — up then down,
   because two forces fight: more cards makes the fixed 10-shelf machine mix
   *worse* (pushes bits up), more copies makes reading a card *harder* (pushes
   bits down). There is no clean line to ride to 8 decks; 8-copy behavior is
   genuinely UNKNOWN and could land anywhere. (Earlier session text that read
   "8 copies don't destroy the edge" was an overstatement — only 2 and 3 were
   measured; corrected here.) Untangling the two forces is exactly step-2
   below.
3. **The copy tax is real** (the down-arm of finding 2): holding the
   confound aside, more copies per card is genuinely harder to invert.
4. **The PF loses fidelity as copies grow.** z slid to −3.07 at 3 decks /
   60 particles (realized below predicted — particle impoverishment at higher
   latent dimension). Inside the 4.5 gate but a clear signal that particle
   count must scale with decks — the tool wobbles *before* the edge dies, so
   an 8-deck number needs both more particles (or the ADF) AND the isolation
   study to be trustworthy.
5. **The two-pass fix collapses the channel at multi-deck too** (0 bets,
   0.035 bits) — the E26/E27 single-deck result holds up the ladder.

**Two honesty flags carried forward:**
- **Confound:** a fixed 10-shelf machine mixes a bigger stack *worse*
  (Diaconis: adequate mixing needs ~n^1.5 shelves), so absolute edge conflates
  the copy penalty with mixing adequacy. The clean isolation is a **same-n
  distinct-vs-duplicated** comparison — queued.
- **Throughput wall:** the PF is O(particles × slots × cards)/shoe and the
  2-pass posterior is +20× (200-shelf slot axis, 16 s/shoe). PyPy makes probe
  scale feasible but an **8-deck production run needs the O(slots)
  assumed-density filter** (posterior cost independent of particle count) or
  far more particles — the immediate next build.

**Scope:** full P/B/Dragon7/Panda8 coup-EV pricing over the M9 engine is the
next rung (needs coup-outcome-under-ordered-posterior machinery). Seeds:
22.9e9 block (probes 22900000001, 22900000050). Artifacts:
`data/e28_multideck.py`, `data/e28_multideck.json`, `data/bench_pypy.py`.

## E27 — M12b rung 1: the exact shelf posterior — DFH's conjecture VERIFIED, the order-only value channel priced

**Date:** 2026-07-19 · **Question:** convert M12a's guessing advantage into
the game-free core M12b needs — the exact next-card posterior for an
input-aware observer — and price the first payoff adapter under the
two-layer rule (posterior core never imports a game; payoffs are thin
adapters).

**Machinery (new; `src/ridefree/posterior.py`):** `ShelfPosterior` — the
EXACT sequential next-card law for an m-shelf pass of a known stack. Key
fact: the shelf shuffle is a label sort (DFH Description 1 — each card
i.i.d. uniform over 2m lanes, output = deterministic sort by slot), so
filtering is exact over the global slot axis: a chain term h_t over the
last observed card's slots plus a per-slot remaining-cards product,
O(slots + remaining·lanes) per dealt card, float-exact. Multi-pass needs
no new code (Cor 4.2: two 10-shelf passes ≡ shelf-200 — the E26-gated
equivalence). `PosteriorGuesser` adapts it to the `forensics` guesser
protocol and self-reports claimed hit probability (calibration for free);
`proposition_experiment` is payoff adapter #1. Scope honesty: stack
entries must be DISTINCT (one physical deck) — multi-deck shoes repeat
cards and need copy-marginalization in the observation model (rung 2);
the forward GSR riffle is not a label sort (its posterior is a separate
easy cut-conditioned construction, deferred until a riffle target needs
pricing). 332 tests green (6 new).

**Gates (tests + `data/e27_posterior_gate.py`, ALL PASS):** brute force —
posterior conditionals equal full lane-assignment enumeration through an
INDEPENDENT physical pile simulation, at every step of every reachable
output, (n=5, m=2) and (n=6, m=1), tol 1e-9; sampler consistency incl.
two-pass output against the Cor-4.2-equivalent posterior; impossible
observations raise; domination, calibration, and prediction-realization
(below).

**Findings (6k decks/arm unless noted, seeds 22.8e9):**
1. **The DFH "conjectured optimal" strategy is VERIFIED (a result the
   paper left open since 2013):** exact-posterior argmax — optimal by
   construction — scores 9.300 (var 4.84); paired-on-identical-decks delta
   vs their strategy **+0.0065 ± 0.0106 (z +0.61)**: statistically zero.
   Their conjecture was right to ±0.01 cards/deck. Calibration z −0.04;
   m=1 sanity 39.081 vs published 39.
2. **The order-only value channel at one pass is LARGE.** Composition-fair
   ten proposition (odds fair vs remaining composition ⇒ a PERFECT COUNTER
   nets exactly zero on every offer; profit = pure order structure): θ=0 →
   **24.2 bets/deck at +22.6%/bet = +5.47 u/deck**; θ=0.05 → 11.7 at
   +38.1%; θ=0.10 → 4.9 at +58.0%. Realized == posterior-predicted within
   z everywhere (worst −1.28) — the adapter's E17-pattern gate.
3. **Information beyond the perfect counter: 8.95 bits/deck** at value
   level; the depth curve of |p−q| on the ten axis rises 0.037 → 0.125
   per card (the last 8 cards are richest) — late-shoe concentrated like
   every paradigm-1 signal, but ON TOP of composition, not instead of it.
4. **The manufacturer's fix closes the channel:** two passes → 0.00
   bets/deck at θ=0.02 and 0.000 bits/deck (600 decks) — consistent with
   E26's +0.021-card identity residual. Weak mixing is the whole game.

**Honesty clauses:** composition-fair odds are a synthetic instrument — no
casino offers them; these units price recoverable order information in
betting currency, NOT a real-game edge (the real conversion — baccarat
coups, insurance-grade spots — is rung 2). The observer premise (full
knowledge of shoe k's order) is the baccarat-like ideal; degraded
observation is a knob for later rungs.

**Seeds:** test pins 22700000001–04; E27 battery 22800000001–04. Next
unused block: **22.9e9+**. Artifacts: `data/e27_posterior_gate.py`,
`data/e27_posterior_gate.json`.

## E26 — M12a: the synthetic shuffle lab reproduces Diaconis/Fulman/Holmes (paradigm 2 opens in code)

**Date:** 2026-07-19 · **Question:** build the M12a lab — shuffle procedures
as data the `Shoe` composes — and gate it hard on the published
shelf-shuffler numbers before any attack work (ROADMAP M12a; the paradigm-2
doctrine's "synthetic ground truth first").

**Machinery (new; decision record in DESIGN.md):** `shuffle.py` —
`UniformShuffle` / `ShelfShuffle(shelves, passes)` / `RiffleShuffle(piles,
passes)` (GSR a-shuffle) / `ComposedShuffle`, immutable dataclasses with
`permute(stack, rng)`, content-independent rng draws → exact replay under
seed; `forensics.py` — exact class laws as `Fraction`s (Warren–Seneta valley
counts, DFH Theorem 3.1, Eulerian counts, the Bayer–Diaconis a-shuffle law,
exact TV/sep/l∞) plus seeded instruments (guessing-with-feedback with DFH's
conjectured-optimal `ShelfGuesser`, pluggable for M12b observers; color
changes; valley/rising-sequence histograms). `Shoe(…, shuffle=, stack=)`
composes any model over any pre-shuffle order (default byte-identical to
the historical uniform path — asserted in tests) and `raw_order()` exposes
the full order as the successor shoe's stack. 326 tests green (19 new).

**Source pinned:** arXiv:1107.2961v2 (Ann. Appl. Probab. 23(4) 2013)
fetched and read in full this session. The "≈9.5/52" the strategy docs
carried was the abstract's rounding — the paper's Table 2 Monte Carlo is
**9.3 / var 4.7**; all gates pin the tables, not the abstract.

**Gates (`data/e26_shelf_gate.py`, 100k trials per instrument, 200k for
histograms; in-test pins 20k at seeds 22.4e9; ALL PASS):**
- **Exact, zero sampling error:** DFH Table 1 reproduced to every printed
  digit — 12 shelf counts × (TV, sep, l∞), incl. l∞ = 45,118 at m=25 (their
  printed "∞" rows compute to 1.7e6–1.4e13, i.e. "effectively infinite" was
  a display choice); BD seven-shuffles TV(52, 2⁷) = 0.3341 vs published
  0.334, full k=1..10 canon reproduced (1 1 1 1 .924 .614 .334 .167 .085
  .043).
- **Guessing (Table 2):** m=1/2/4/10/20/64 → 39.008 / 27.024 / 17.577 /
  **9.290** / 6.126 / 4.714 vs published 39 / 27 / 17.6 / **9.3** / 6.2 /
  4.7 — all pass with their 10k-run MC error included; worst z −3.64 at
  m=20 (Δ 0.074, inside their noise + print rounding; every other |z| ≤
  0.95). Uniform baseline: 4.538 = H₅₂ (z −0.04), var 2.91 = analytic.
- **Color changes (reds-on-top test):** uniform 26.017 ± 3.576 (pub 26 ±
  3.6; 26 is exact by symmetry), one ten-shelf pass **17.196 ± 1.838** (pub
  17 ± 1.83).
- **Sampler ↔ closed form (the load-bearing link):** valley histogram vs
  Theorem 3.1 worst |z| = 1.69; rising-sequence histogram of three composed
  GSR passes vs the exact 8-shuffle law worst |z| = 1.02.
- **The fix, measured (Cor 4.2):** two 10-shelf passes ≡ one 200-shelf pass
  empirically (guessing z +0.56, color z +0.75; two-pass valley histogram
  vs the exact 200-shelf law worst |z| = 2.30 over 12 pooled classes) — and
  the residual of the fix is **+0.021 ± 0.005 cards above chance** (TV
  0.0103): real, resolvable, worthless at a table. The instrument sees
  leaks that small.
- Top-card retention 0.0499 vs the ≥ 1/2m = 0.05 bound (uniform 0.0192).

**Reading for M12b:** one pass of the real machine gives an input-aware
observer **+4.75 correct guesses per 52 cards over chance (2.05×)** — the
paradigm-2 thesis in one number. The advantage decays m=10 → 20 → 64 →
two-pass as 4.75 → 1.59 → 0.18 → 0.02: the exploitable regime is
single-pass / weak mixing, exactly the recalibrated target list (hand
shuffles, weak/old batch machines). Next: convert guessing advantage into
betting edge (M12b, house-game arm first).

**Seeds:** test pins 22400000001–17; E26 22500000001–06 & 101–103
(guessing), 22600000001–04 & 011–014 (color/histograms/top-card). Next
unused block: **22.7e9+**. Artifacts: `data/e26_shelf_gate.py`,
`data/e26_shelf_gate.json`.

## E25 — risk-averse deviations: honest second moments; the RA hypothesis measured (M11)

**Date:** 2026-07-19 · **Question (Matt):** the deviations E24 priced are
EV-maximizing, and its ceiling arm reused the no-deviation variance. Could
we find deviations tweaked in favor of LOWER VARIANCE instead — and what do
honest second moments do to the hobby bankroll? Per the session agreement,
no shape is chosen: everything derives per shape (walk / sit-out /
never-leave) from one shape-independent bank.

**Machinery (new, gate-passed):** `experiments.run_ra_bank` + `cli rabank`
(decision record in DESIGN.md): one paired pass on the chart's canonical
timeline banking, per hi-lo TC bin: chart moments (n, Σp, Σp²); for every
play change the paired (n, Σd, Σd², Σp·d) — so ΔE[p²] = E[2pd + d²] is
exact per play; and the insurance overlay as counts (settle is ±½/+1 per
unit, any TC-threshold rule prices in closed form, hedge term included).
Three sources: candidate cells (every chart DOUBLE/SPLIT replayed with that
one cell suppressed), composition deviations at bins ≥ +2 (the EVCalculator
replay is the cost; attribution to the first diverging decision), insurance
(no replay needed). `data/e25_ra.py` selects per shape: plays grouped by
(chart row, upcard), ONE policy per group (chart / suppress ≥ j / dev ≥ j —
alternatives, never teammates), bet shape re-searched after selection so
the $/h floor binds the card, not each play. 307 tests green (7 new),
including a bit-exact cross-gate: the bank's dev accumulators equal
`run_deviation_value`'s on the same seed.

**Gates (40M rounds, 10 × 4M shards, seeds 21.4–22.3e9, pen .75):** chart
bins vs the banked e16 basic curve (fresh seeds): worst |z| = 2.12,
overall −0.625% vs −0.630% ✅; composition-dev value per bin vs the e16
paired values (independent seeds): worst |z| = 1.65 ✅; aggregate ==
sum-of-attributed-cells: exact ✅; P(dealer BJ | ace up) = 0.3081 ± 0.0003
vs fresh-shoe 96/311 = 0.3087 — 2σ LOW, in the direction the known
cut-card effect predicts (ten-poor residuals deal more rounds) ✅.

**Findings ($15 floor, ≥ $15/h at 200 r/h, 5% RoR, honest variance):**
- **Deviations cut ~35–45% of the bankroll in every shape** — and that
  survives honest second moments: walk chart-only $11.1k → **$7.1k**
  (+$15.40/h, card $15 floor from 0, $35 at +4, $70 at +6, insure ≥ +4);
  sit-out $6.3k → **$3.9k**; never-leave $38.3k → **$21.4k at +$30.7/h**
  (the solver overshoots the hourly because that lowers the bank).
- **The RA hypothesis, measured: mostly a null at hobby stakes.** RA
  selection beats EV-max by only ~1–2% of bank ($7.2k → $7.1k walk). The
  genuine RA content: 2 pure-variance suppressions added (skip split 2,2
  v 3 at ≥ +4; skip 3,3 v 3 at ≥ +1), 3 EV-max plays rejected for
  variance — including **T,T v 3 (don't split tens v 3 even when the
  count makes it +EV; T,T v 5/6 stay, at rungs ≥ +5/+7)** — and 6
  thresholds moved. Real but small: the big money was honest-variance
  EV-max all along, because σ/round DROPS 24 → 19 under deviations (the
  stand-more plays outweigh the extra doubles/splits at these stakes).
- **The engine re-derived the classic index card from raw moments,
  ranked by bankroll impact:** 16vT ($569 of bank, 30% of play value),
  15vT ($233), 12v3 ($149), 12v2 ($99), 14vT ($85), 10vT double ($56),
  16v9, 16v7/8/A, 10vA double, T,T v 5/6, 9v2, 8v6 doubles… Top 5 ≈ 60%
  of play value, top 18 ≈ 88%, the 45-play tail pools to $221. A short
  card captures most of it.
- **Insurance lands at bins ≥ +4 in every shape** — exactly "insure when
  the jump bet is out" (the E18 human rule), now derived rather than
  assumed. The hedging cross term is priced (dealer-natural rounds have
  no play deltas, so the overlay is exact).
- **Honest correction to E24's ceiling:** walk-shape all-indexes was
  $6.1–6.4k with reused variance; the honest number is **$7.1k**.
  Attribution split three ways, on record: real deviation variance,
  TC-threshold insurance vs composition-exact, and the unmodeled
  bins-0/+1 dev EV (~$1–2/h, none of it variance-relevant).

**Caveats on record:** policy effects compose additively in (μ, M2)
(ins × dev cross banked as aggregate, not applied — tiny); selection is an
argmin over ~200 play groups (winner's curse at the play level, min cell
250 rounds; the top plays ride 10⁴–10⁵ samples); dev plays exist only at
bins ≥ +2 (the replay window); the play list is composition-exact per bin —
crisp "at TC ≥ j do X" indexes are its human approximation; pen .75 only.
The chosen card's fresh-seed OOS certification (E18/E23 pattern) runs the
literal human card and closes all four gaps at once.

**E25b addendum (same day): Matt's honest hobby spec, priced.** The real
bar, stated after seeing E25: **bank ≤ $5k at 5% RoR, walk ≤ 10% of the
time, ≥ $10/h.** Added walk-at-−4/−3 shapes (6.5%/11.6% of rounds) and a
walk% column to `e25_ra.py`; everything from the same bank, no new sims.
Verdict: **a stay-seated-and-betting card cannot meet the spec** — with
the full honest play layer and the target relaxed to $10/h, walk ≤ 6.5%
costs $16.3k ($15 floor) / $10.9k ($10 floor) at pen .75; the min-bank
solver overshoots the hourly (+$17–26/h), so earning less buys nothing —
the −2..−1 floor toll sets a variance floor ~2–3× the budget; pen .80
(~×0.75 from E24 evidence) still lands ≈ $8k. **The SIT-OUT shape passes
all three numbers with margin at realistic peopled-table pace (140 r/h,
zero walking — you keep the seat and bet ~36% of rounds): $15 floor →
$3.8k at +$10.4/h; $10 floor → $3.2k at +$10.1/h** (σ/round ~$14: a 4h
session swings ~±$330 — hobby texture). M11 therefore hangs on ONE felt
question: **may a seated player sit out hands and rejoin mid-shoe?**
(plus: do $10 tables exist weekdays?). If the policy is hostile, the one
honest lever left for a seated card is a resize-on-drawdown ladder
(genuine RoR reduction, unbuilt machinery, costs hourly when down).

**E25c (same day): the walk lines' EVENT rates — and the verdict on
Matt's spec.** Matt killed the sit-out card on table-culture grounds
(skipping hands seated = too faux pas), moving the question to walk
lines. `data/e25c_walks.py` (1M played rounds per threshold, seed
22400000001, paired stream, live re-seat semantics): **tc ≤ −1 fires
12.1 walks/h (87% of shoes) — fantasy; ≤ −2: 4.8/h, 67% of shoes;
≤ −3: 2.9/h, 51%; ≤ −4: 1.9/h, 36% of shoes, median exit round 32** —
i.e. the gentlest line we own carries exactly the walking load
(1.7–1.9/h, ~37% of shoes) Matt already shelved as weekday-impractical
in E18b, and still costs $10.9k. **The spec ($5k, low walking, $10/h,
5% RoR) is over-determined at pen .75, and the physics is one line:**
$10/h at 200 r/h on $5k at 5% RoR allows σ ≈ $12.9/round total; a $10
floor played 90+% of rounds contributes ≈ $11.6/round by itself (~80%
of the σ² budget) before a single jump is placed — and the jumps that
must overcome the floor's −$8–12/h toll blow the remainder several
times over. Remaining honest levers, logged in STATUS: the
resize-on-drawdown ladder (the one real candidate — new machinery),
the deep-pen table (~×0.75), or consciously relaxing one of the three
numbers (e.g. the constraint set IS satisfiable near ~20% RoR, or at
~$8–9k, or at ~$6–7/h).

**MATT'S DECISION (2026-07-19) — M11 CLOSED:** resize ladder declined;
the −3 fixed point taken at hobby-honest odds. **Final answer: the −3
walk card ($10 floor from −2, $35 at +3, $85 at +6, insure ≥ +4, E25
index set) → +$14.3/h at 200 r/h on $7.2k at 10% RoR** ("it's a hobby
anyways"; $9.3k at 5%, $5.0k at 20% — the same card at every rung, only
the honesty knob moves; below +$14.3/h no cheaper card exists, the
U-shape floor). Conditions on record: weekday $10 floor unconfirmed
($15 floor → $10.7k at 10%, +$22.5/h); pen .75; 200 r/h; NOT
live-certified — OOS certification is the mandatory gate before felt
play. Write-up: `docs/ARTICLE_HOBBY.md`.

**Seeds:** 21.4–22.3e9 consumed (E25); E25c consumed 22400000001.
Next fresh base: **22.5e9+**.

## E24 — the hobby card: minimum bankroll that still clears $15/h (M11 opened)

**Date:** 2026-07-19 · **Question (Matt):** the pro framing ("max $/h per
bankroll") prices real play out of reach — a 5%-RoR bankroll only means 5%
if you're genuinely willing to lose all of it, and $35k is real money.
Reframe: on the classic blackjack next door (6d H17 DAS, $15 floor), what
is the MINIMUM 5%-RoR bankroll that still clears **$15/h at 200 r/h**, and
what's the simplest system that does it? Non-division preferred; deviations
and index plays are back on the table (Matt's hunch: that's where the low
variance lives — "everything's an index play, even off-the-top strategy").

**Method:** `data/e24_hobby.py` — pure arithmetic over banked bins, no new
sims, no seeds: the E16 per-TC curves (60M rounds, arms basic / ins /
dev-paired ceiling) and the E17 multi-signal RC curves (48M rounds,
`red7_rc`). Two solvers. (1) Continuous KKT frontier: min variance s.t.
EV ≥ target with a seated floor bet — raised bins get bets ∝
edge/E[profit²] (the Kelly shape); the constraint is an inequality, so the
solver keeps raising λ while bankroll still FALLS (the floor toll's
variance is fixed; overshooting the target hourly can be optimal — and is,
at every never-leave row). (2) Exhaustive human cards: 1–2 jumps on a $5
chip grid × walk lines, all three arms; the same search on Red 7 RC bins
with walk-line validity enforced — a "walk" line at or above the
fresh-shoe IRC −12 never sits down (the first pass's rc≤−12/−8 rows were
wong shapes in disguise; caught and relabeled).

**Findings (pen .75, ins arm = chart + exact insurance unless noted):**
- **Seated never-leave is NOT hobby-cheap: ~$31k** (best human card
  +$28.12/h on $30.8k — the solver overshoots because at $15/h sharp the
  bank is even worse). The $15 floor toll at negative counts is the whole
  problem; $15/h with money on every round costs pro-scale capital.
- **The walk line is the money decision.** Walk at TC ≤ −1 and the bank
  collapses to **$9.7k**: floor from 0, **$50 at +4, $90 at +6** →
  +$15.28 ± 0.58/h, σ $22/round, N0 425h. The 1-jump version — **$15
  floor, $70 at +4, walk at TC ≤ −1** — is +$15.96 ± 0.61/h on **$10.4k**
  and is the simplicity pick (crouch15-2r's little sibling: same skeleton,
  softer jump, tighter walk). Continuous frontier says $9.4k — the human
  card captures essentially all of it. Walk at ≤−2 instead: ~$15–16k.
- **Deviations are worth a third of the bankroll (Matt's hunch, priced):**
  the SAME winner card on the all-indexes ceiling arm: $9.7k → **$6.4k**
  (+$23.16/h); best ceiling-searched card $6.1k. Insurance alone is $2k of
  it (basic $11.7k → ins $9.7k), concentrated at the jump bins where the
  E18 human rule ("insure iff the jump bet is out") transfers.
- **No-division walk cards leak ~$10k:** best Red 7 walk card $20.1k. The
  hobby walk line lives at TC ≈ −1, far off Red 7's +2 pivot, and
  RC ≈ d_rem·(TC−2) blurs it across depth. This INVERTS the pro finding:
  crouch15's money decision (the jump) sat at the pivot and was
  depth-exact; the hobby's money decision (the walk) is exactly where
  division earns its keep.
- **Sit-out shapes reach $5.1–5.6k, division-free included** (e.g. RC:
  sit until Red 7 RC > −3, floor, $60 at +6 → +$15.40/h on $5.4k; TC:
  floor from +1, $50 at +4 → $5.6k; wong-in $35 at +2 → $6.2k) — all
  CONDITIONAL on open felt items (sit-out while others play, mid-shoe
  re-entry) and on a peopled table's real pace: re-solved at 140 r/h they
  cost $6.7–7.5k.
- **Sensitivities:** pen .70 → the winner earns **+$11.6/h — below
  target**; pen .80 → +$22.3/h on $7.7k (the deep-cut table is the
  difference between a business and a perch). $10 weekday floor → walk
  card $7.2–7.9k, sit-out $4.7–5.2k, ceiling $4.3k. 140 r/h → the winner
  re-solves to $65 at +4 / $125 at +6 on $10.7k.
- **Hobby honesty:** N0 ≈ 425h ≈ 2 years at 4h/week; 46% of 4h sessions
  lose (P10 −$746, P5 −$975); at 200h/year the year is +$3.1k ± 4.4k —
  roughly a 1-in-4 chance a full YEAR of correct play loses money.

**Caveats on record:** ceiling arm reuses ins-arm variance (deviation
variance unmodeled — the risk-averse-index question needs new machinery);
walk rows are zero-friction (E18b's friction is per-walk, and a TC ≤ −1
line walks most shoes); card $/h are argmaxes over ~30k candidates
(winner's curse, se ~$0.6–1.5/h) — whatever card is picked gets
fresh-seed OOS certification before the felt (E18/E23 pattern).

**Seeds:** none consumed (arithmetic over banked E16/E17 shards). Next
unused block: **21.4e9+**.

## E23 — the literal pog2 card certified LIVE; priced at the real felt ($25 tied max, ~100 r/h, deep pen)

**Date:** 2026-07-19 · **Question:** does the human card as written — pog2
start 24, stake ≤ 12, split 5s only while the side is out, flat main, no
insurance — reproduce the E22 binned prediction when played end to end on
real shoes? And what does it earn at the felt constraints Matt's recon
delivered the same day: **side max $25, side ≤ main (tied 1:1), pace ~100
hands/h, pen ~.79–.833** (1 to 1.25 decks cut — deeper than the .75
assumption)?

**Method:** `data/e23_run.py` (the E18 pattern): a `PogCardPlayer` wraps
`OptimalStrategy` — farms 5,5 and stakes the side ONLY on trigger rounds;
the runner keeps the literal human RC (value tags + red-2 bump, IRC 24,
stake at RC ≤ 12 ≡ the pivot-zeroed RC ≤ 0 rung). Records realized
per-round main/side moments split staked/unstaked INCLUDING the main×side
cross product — retiring the mixed-bin stitch, cov(main,side)=0, and the
EV_OUT constant in one run. 10 × 2M rounds, RIDE_FREE + PT1 cut_card:
pen .75 seeds 20.4–20.8e9, pen .8333 seeds 20.9–21.3e9. Verdict:
`data/e23_verdict.py`.

**Findings (10M rounds per pen):**
- **GATE 1 PASS:** staked 16.49% of rounds (predicted 16.5%), side EV
  **+10.39% ± 0.39/unit vs the E22 bin prediction +10.13% (z +0.66)** —
  the binned pipeline and the literal card agree end to end.
- **GATE 2 PASS:** unstaked main −0.946% ± 0.037 vs the EV_OUT −0.95%
  approximation (z +0.11). Window main (farming) −2.14%.
- **The retired approximation was conservative:** realized
  cov(main, side | staked) = **+0.72 u²** — positive (a farm split
  doubles the main exposure exactly when a lammer lands), so prior
  ledgers slightly UNDERstated variance; realized sd ≈ $53.7–56.5/round
  at $15/$25 stakes. Token histogram healthy out to the 7-lammer jackpot
  (7 in 1.65M staked rounds).
- **Deep pen pays:** pen .8333 → staked **18.59%** of rounds at
  **+11.18% ± 0.36/unit** (the signal is depth-fed: both frequency AND
  quality rise). Rounds/shoe 42.5 → 47.1.
- **THE OPERATIVE LEDGER (side tied ≤ main, max $25, 100 r/h, $15 main
  otherwise — raise-on-trigger):** pen .75 → **+$22.13 ± 1.74/h, bank
  ~$20.4k**; pen .8333 → **+$30.20 ± 1.83/h, N0 367h, bank ~$16.6k (5%
  RoR)**. The observed .79–.833 felt brackets to **≈ +$26–30/h**. Flat
  $15/$15 (never raising) ≈ +$13.5/h — the raise earns its keep. If the
  tie were ever lifted: untied $25 → +$25.67 (.75) / +$34.33/h (.8333).
- Context: half the pace halved the old headline, deep pen bought ~40%
  of it back. ~+$30/h on a $17k bank at $25 stakes is bankroll-efficient
  (compare crouch15-2r: +$40–44/h on ~$36–40k at 200 r/h heads-up — a
  pace assumption weekdays may not deliver either).

**Seeds:** 20.4–21.3e9 consumed. Next unused block: **21.4e9+**.

## E22b — Matt's simple variants: "hi-lo-57" TIES the pog2 card (whole tags, no gadget); KO is dead (35%)

**Date:** 2026-07-18 · **Question (Matt):** can a simpler, more transferable
count hold the EV? Variant A = A/T −1, 2–7 +1, 8/9 0 — **which is exactly
the published KO count** (pivot +4). Variant B = same but 5 stays 0 —
**which is exactly pog2 minus the red-2 gadget** (the gadget's only job is
pinning the pivot at −2; without it the count is BALANCED, pivot 0). Framed
against hi-lo, variant B is one swap: **the 5 and the 7 trade tags** —
"hi-lo-57".

**Method:** `data/e22b_run.py` — 10 × 2M farm-arm rounds, fresh seeds
19.4–20.3e9, FOUR signals on one card stream (hilo_tc / pog2_rc / ko_rc /
simple_rc; whole-tag customs via the sign=0 no-bump path, in-test);
`data/e22b_verdict.py` (A = s01–05 chooses each rung by untied capture,
B = s06–10 scores blind; ledger conventions as E22).

**Findings:**
- **Tag quality (BC vs side EORs): hi-lo-57 −0.9734, KO −0.9774, pog2
  −0.9726** — all three tag sets are essentially equal. The entire game is
  the PIVOT.
- **KO is refuted as a no-division card: 35% capture** (fixed RC ≤ −25,
  4.25%/unit — the 6-point pivot mismatch makes the fixed threshold swing
  from TC −1 early to TC −21 late). $25 stake goes NEGATIVE (−$3/h). The
  dose-response is now measured: pivot offset 0 (pog2) ≈ full capture,
  2 (hi-lo-57) ≈ −0–4%, 4 (Red 7, E22) ≈ −30%, 6 (KO) ≈ −65%.
- **hi-lo-57 at fixed RC ≤ −5: 105.1% of divided hi-lo, 101.9% of pog2
  pooled — a statistical TIE with the certified card** (B-half blind:
  +6.71%/unit at 24.0% of rounds → 1.613/100 vs pog2's 1.554; differences
  ≲1σ on the same stream). Untied nets $25/$50/$100: **+$49/+$134/+$305/h**
  — indistinguishable from pog2's +$48/+$132/+$300.
- **The robustness asymmetry (why pog2 stays the reference):** pog2's
  trigger is the pivot — depth-exact and therefore PEN-ROBUST by
  construction. hi-lo-57's fixed RC ≤ −5 is a depth compromise TUNED AT
  pen .75; a different real pen shifts its optimal rung (re-price at the
  true pen after recon — already queued). Cross-block note: the hilo −2
  window ran +7.26/+7.52/+7.81% across E21/E22/E22b's independent 20M
  blocks (~1.5σ steps — noise, logged).

**Verdict: drill either card; hi-lo-57 is the practicality pick.**

> **hi-lo-57: count exactly like hi-lo but the 5 counts NOTHING and the 7
> counts +1** (A/T −1; 2/3/4/6/7 +1; 5/8/9 nothing). Balanced. **Start
> each shoe at 10; stake the side (and split 5s) at 5 or below** (slide
> +10 of the certified RC ≤ −5). Everything else per the operating
> doctrine.

KO's transferability is real but it cannot run this trigger without
division. Seeds consumed: 19.4–20.3e9. **Next unused block: 20.4e9+.**

## E22 — THE POG2 CARD: a no-division count that BEATS hi-lo-with-division (106.6% capture); Matt's "ultimate card" answered three ways

**Date:** 2026-07-18 · **Questions:** the no-division human card for the
Silver Stack trigger; and Matt's parting hypothesis — is there an ultimate
all-in-one count (raise mains at +TC, stake the side at −TC), or does a
side-specialist win?

**Step 0 — the positive end is DEAD on the Ride Free table (banked-bin
arithmetic, `data/e22_positive_end.py`):** RF main EV doesn't cross zero until TC +5 (the
dealer-22 push blunts ten-rich standing); the crouch-style ramp
($100/$150/$200 at +2/+3/+4) is **−$0.47/h** ON this table; $200-at-+4
top-only makes +$7/h against the side's $69–275/h. **Fusion refuted by
dollars: the comprehensive play is a PORTFOLIO (side card at RF, crouch15-2r
at classic), and the RF card carries no positive rungs.**

**Stage 1 — POG side-EV EORs by regression (new machinery, gate-passed):**
`run_pog_eor` accumulates additive OLS sufficient statistics (intercept +
10 per-rank share deviations of the remaining shoe vs fresh → side profit
AND main profit), solved by `solve_pog_eors` (tens pinned 0 — shares sum
to 1, EORs are identified up to a constant; `unbalanced_bc` centers).
`cli pogeor`; 5 × 2M farm-arm cut_card rounds, fresh seeds 17.9–18.3e9
(`data/e22_eor_p75_s*.json`, solve in `data/e22_card.py`):
- **G1 PASS: the main-profit regression reproduces E4a's calculator EORs
  at weighted corr +0.9956** — the pipeline validates against an
  independent derivation before the side EORs are trusted.
- **Side EORs (per card removed, tens 0):** 2–8 are the fuel — removing
  one costs the side bet −6.8% to −9.2% (the 7 as heavy as the 3: it makes
  the 9/10/11 free-double totals); 9 half-strength (−4.0); A/T dead. Per-
  rank se ≈ 0.1–0.2% (5 shards).
- **As lammer counts (BC vs side EORs): hi-lo −0.9310** (the E20/E21
  trigger; "provably not optimal" now quantified), **Red 7 −0.9652** (!),
  perfect 1.0.
- **Search** (`search_unbalanced_level1_pivot`: the E17 family generalized
  to any per-deck imbalance, both bump signs, bet-LOW direction, secondary-
  EOR column; E17 wrapper unchanged): odd pivots are UNREACHABLE (parity:
  4·sum−16±2 is even), so pivot −2 it is. **Winner "pog2": A −1, RED 2s +1
  (black 2s 0), 3/4/6/7 +1, 5/8/9 nothing, ten −1 → side BC −0.9726**,
  main BC +0.80. The shape is the story: *the 5 — blackjack counting's
  crown jewel — is IRRELEVANT to the lammer count, and the 7 is a full
  point.* Anti-red-7 (hi-lo + red 7s −1) scores −0.876 — worse than raw
  hi-lo; runner-ups within 0.005.

**Stage 2 — head-to-head certification on one card stream**
(`run_pog_count_curves`: side/main pog moments binned by hi-lo TC + custom
pivot-zeroed RCs in one farm-arm pass; hilo_tc bins reproduce
`run_pog_curve` EXACTLY, in-test; runner `data/e22_run.py`, 10 × 2M fresh
seeds 18.4–19.3e9, A=s01–05 chooses / B=s06–10 scores;
`data/e22_verdict.py`):
- **E21 replication gate on fresh seeds: PASS** (hilo ≤ −2 window +7.52%
  @ 20.85% vs E21's +7.26% @ 20.85%; ≈ +2σ with the pairwise se).
- **pog2 captures 106.6% of the division benchmark** — 16.51% of rounds
  at **+10.13% ± 0.27/unit** (B-half blind: +10.22) vs hi-lo's 20.85% at
  +7.52%. Sharper window, more EV per staked dollar. **Both scenario
  objectives (untied AND matched raise-on-trigger) pick the SAME rung —
  the pivot, RC ≤ 0** — and the rung menu peaks exactly there (the A-sweep
  found the pivot blind).
- **Red 7 reuse REFUTED: 70.1% (untied) / 62.4% (matched) capture** at its
  best off-pivot rungs (RC ≤ −13/−16). The 4-point pivot mismatch is
  expensive — the E18 off-pivot-mush algebra, now priced. One-count-both-
  tables costs $70–100/h at $100 side vs the specialist. **All three
  readings of "ultimate card" (fusion count, dual triggering, drilled-count
  reuse) lose to specialization by measurement.**

**THE CARD (slide +12, E18 no-negatives doctrine):**

> **Count: aces and tens −1; 3, 4, 6, 7 +1; RED 2s +1 (black 2s nothing);
> 5s, 8s, 9s nothing. Start each shoe at 24. Stake the side — and split
> 5s while it's out — at 12 or below.** (Same trigger untied or matched.)

**Ledger at the pivot rung (pen .75, 200 r/h seated, $15 main outside):**

| side | untied net | N0 | bank | matched 1:1 net | N0 | bank |
|---|---|---|---|---|---|---|
| $25 | **+$49/h** | 232h | $17.1k | +$42/h | 324h | $20.5k |
| $50 | **+$133/h** | 119h | $23.6k | +$108/h | 186h | $30.2k |
| $100 | **+$300/h** | 91h | $41.1k | +$240/h | 149h | $53.6k |

(vs the hi-lo division card: untied $100 +$268, matched $100 +$240 at
E21b's hi-lo rung — the no-division card nets +12% untied and its matched
rung needs no re-derivation.)

**Caveats:** outside-window toll uses the E21-pool normal-arm EV_OUT
−0.95% (constant approximation); window main is farm-arm (correct for
staked rounds); cov(main, side) = 0 as throughout; non-chosen rungs in the
menu are descriptive, not A/B'd. All retired by the live verification of
the literal card (E18 pattern), which is the next chunk. Trainer has no
POG/pog2 mode yet — natural build alongside it.

Seeds consumed: 17.9–18.3e9 (EOR shards), 18.4–19.3e9 (curve shards),
16.8e9-block pins for tests. **Next unused block: 19.4e9+.**

## E21b — the side ≤ main scenario: the attack survives matching at ~70–77% of the hourly (banked-bin arithmetic, no new sims)

**Date:** 2026-07-18 · **Question (Matt):** E20/E21 stake the side over a
flat $15 main — but what if the placard ties the side bet to the main wager
(side ≤ main, or the insurance-style side ≤ main/2)?

**Method:** `data/m10b_matched_verdict.py`, pure arithmetic over the banked
E20/E21 bins (both arms carry per-bin main AND side moments). The correct
form under the constraint is **raise-on-trigger**: main stays at the $15 min
outside the window and is raised to side/ratio only on trigger rounds
(farming stays on — its main cost is ~40× smaller than its side gain at any
qualifying stake). Per-stake threshold re-chosen under the constraint with
the E20 ceremony (s01–05 choose by seated hourly, B-half scores blind);
variance upgraded to measured per-bin main second moments, window/outside
split, cov(main, side) = 0 as before.

**Findings (seated, 200 r/h; net / N0 / bank at the A-chosen t\*):**

| side | unconstrained (E21) | side ≤ main (1:1) | side ≤ main/2 |
|---|---|---|---|
| $25 | +$41/h, 362h, $22.3k (t −2) | **+$32/h, 630h, $29.9k** (t −2) | +$13/h, 2733h, $53k (t −3) |
| $50 | +$117/h, 168h, $29.5k (t −2) | **+$84/h, 343h, $43.1k** (t −2) | +$51/h, 657h, $50.2k (t −3) |
| $100 | +$268/h, 126h, $50.5k (t −2) | **+$188/h, 166h, $46.9k** (t −3) | +$127/h, 416h, $79.1k (t −3) |

- **1:1 matching keeps 70–77% of the hourly** at ~1.3–1.5× the bankroll
  (mid stakes); at $100 the threshold tightens back to −3 (the −2 bin's
  +1.54% side can't carry a $100 main at −2.3%) and the bankroll actually
  DIPS below unconstrained ($46.9k vs $50.5k — smaller window, less side
  variance). Verdict order vs our other lines is unchanged.
- **2:1 (side ≤ half main) is the damaging version:** $25 effectively dead
  (N0 2,733h), $50 thin, $100 alive but at $79k. Still beats E20-no-farm
  at equal stakes.
- **Flat-matching is dominated and must not be played** (main = side every
  round: +$12/$23/$47/h) — the toll scales with the side. Raise-on-trigger
  only.
- **Wong-in matched (1:1):** +$53/$107/$213 per hour per 200 observed
  rounds at $25/$50/$100 (t −3).
- **Optics bonus, on record:** raise-on-trigger means the main bet goes UP
  when the count goes DOWN — anti-correlated with hi-lo, the opposite of
  the counter's tell surveillance screens for. The cost of the constraint
  buys real camouflage.

**Felt read addition:** the Silver Stack placard/dealer question is now
two-part — the side MAX, and whether the side is TIED to the main bet
(and at what ratio). Consistency checks: the script's unconstrained rows
reproduce the E21 ledger to the dime, and seated window net/round equals
the wong-in figure in every mode. Seeds: none (arithmetic only).

## E21 — the farm arm: split 5s while the side is out → window EV +7.37% → +11.78%; the $25 max un-dies; t\* widens to −2

**Date:** 2026-07-18 · **Question (Matt's catch, queued in E20):** E20's curve
played main-EV-optimal 5,5 (take the free double). With side ≫ main staked,
free-splitting 5s ("farming": the split chain re-splits and free-doubles, each
grant = another lammer) trades pennies of main EV for side EV. M10a priced the
farm always-on (+3.08pp side / −0.17pp main, both matching WoO); how big is it
INSIDE the trigger window, and does it move the verdict?

**Method:** `run_pog_curve(..., farm=True)` = `AlwaysPotOfGold(SplitFives(
OptimalStrategy()))`; curves now carry an `arm` tag ("normal"/"farm") through
JSON and `merge_pog_curves` refuses to pool mixed arms (banked pre-tag dumps
load as normal). 10 × 2M cut_card rounds, `RIDE_FREE` + PT1 pen .75, on **the
same seeds as the E20 normal shards** (16.9e9–17.8e9 step 1e8) — deliberately
paired, the M10a gate pattern: shoes are identical until a 5,5 decision
diverges, so farm−normal deltas are common-random-number measurements (errors
= sd across the 10 paired shard deltas). Not a replication — no fresh seeds
consumed. Shards `data/m10b_farm_p75_s01..10.json`; arithmetic
`data/m10b_farm_verdict.py`.

**Findings:**
- **Validation trio, tightest yet:** always-on paired side delta **+3.088% ±
  0.033** (M10a csm gate +3.080 ± 0.185; WoO +3.019 — pairing cut the error
  bar 5×); main cost **−0.144% ± 0.009** (gate −0.173; WoO −0.15).
- **The farm delta is count-fed too** (5,5 and the chains live in small-card
  shoes): per-bin Δside +2.97pp at TC 0 → +3.86 at −3 → +4.4 at −4 → +5.4 at
  −8, every bin ≥ +30σ paired.
- **Farming is essentially free:** per-bin breakeven side stake (vs $15 main)
  is **< $1 everywhere** — the human rule is unconditional: *side bet out →
  split 5s, always.* Window main EV moves only −2.528% → −2.632% (Δ −0.104 ±
  0.021).
- **Locked window (t\* = −3): side EV +7.369% → +11.775%/unit** (Δ +4.405 ±
  0.089 paired; A/B split +4.344 ± 0.125 vs +4.466 ± 0.135, z −0.66, OOS
  PASS).
- **The threshold widens under farming:** re-run of E20's A-chooses/B-scores
  ceremony picks **t\* = −2** (farm flips the −2 bin −1.884% → +1.541%);
  B-half scores +7.476% on 20.87% of rounds. Seated staking rule is now
  "farm side EV(bin) > 0" = TC ≤ −2.
- **Farm-mixed ledger** (seated $15 main every round, farm iff side out,
  pooled 20M/arm, 200 r/h; normal bins outside window / farm bins inside):

  | side | t=−3 net | N0 | bank | t=−2 net | N0 | bank |
  |---|---|---|---|---|---|---|
  | $25 | **+$34/h** | 336h | $17.4k | **+$41/h** | 362h | $22.4k |
  | $50 | **+$103/h** | 136h | $21.0k | **+$117/h** | 168h | $29.5k |
  | $100 | **+$240/h** | 97h | $35.1k | **+$268/h** | 126h | $50.5k |

  (E20 no-farm: +$9 / +$52 / +$138.) Breakeven side stake drops ~$20 →
  **$11.4–12.5**. Wong-in at −2: +$62/$137/$289 per hour per 200 observed
  rounds. t=−3 maximizes $/bankroll, t=−2 maximizes $/h — both on the menu.
- **Doctrinal shift for the felt read: a $25 side max no longer kills the
  play** — it caps it at ≈ crouch15-2r's hourly (+$34–41 vs +$40) on HALF
  the bankroll ($17–22k vs $36–40k). $50+ dominates every line we own.

**Caveats (inherited + new, all retired by the live-verification chunk):**
mixed ledger stitches farm-arm window bins to normal-arm outside bins (live
play transitions within one shoe — second-order, TC conditioning absorbs most
of it); seated sd still sets cov(main, side) = 0; farming lengthens the payout tail,
so window variance grows with it (seated sd/round 44.7 / 84.9 / 167.6 at
side $25/$50/$100, t=−3 — already inside the table's N0/bank).
Human-card note: the unbalanced-count pivot target is now **−2** (was −3).

Seeds: **none consumed** (paired reuse of 16.9e9–17.8e9 by design). **Next
unused block: 17.9e9+.**

## E20 — Silver Stack IS BEATABLE: hi-lo TC ≤ −3 makes the side bet +7.4%/unit on 11.7% of rounds (OOS-replicated)

**Date:** 2026-07-18 · **Question:** M10b — does shoe composition swing Pot
of Gold PT1 past its 8.25–9.0% base edge, and does anything survive the Ride
Free main-bet toll?

**Method:** new `cli pogcurve` / `pogcombine` (experiments.py: per-hi-lo-TC
bins carrying SIDE profit moments and MAIN profit moments separately, ±12
clamp — the E16 curve pattern; tracker convention as E16/E17: full
RoundResult visible at settlement, i.e. normal live counting). 10 × 2M
cut_card rounds, Potawatomi `RIDE_FREE` + PT1, pen 0.75 (assumed — field
unknown), `AlwaysPotOfGold(OptimalStrategy)`, seeds 16.9e9–17.8e9 step 1e8;
shards s01–05 = in-sample threshold search, s06–10 = untouched
out-of-sample. Verdict arithmetic: `data/m10b_verdict.py` over
`data/m10b_rf_p75_s*.json`.

**Findings (pooled 20M rounds):**
- **The curve is enormous and monotone**: side EV per unit staked runs from
  ≈ −4.4% at TC 0 through **+3.2% at −2, +7.1% at −3, +11.5% at −4,
  +19.5% at −6, +29% at −8, +45% at −12** (per-bin z up to +20). The lammer
  rate roughly doubles (0.10 → 0.32/round) as TC falls, and the paytable's
  convexity (multi-lammer chains need the small-card clusters negative
  shoes are made of) multiplies it. Zero crossing between TC −1 and −2.
- **Out-of-sample replication at t\* = −3 (chosen in-sample): PASS** — A
  +7.10% ± 0.42 vs B +7.64% ± 0.45 (A−B z = −0.88); pooled window: trigger
  **11.65% of rounds, side EV +7.37% ± 0.31**. Main EV inside the window is
  −2.53% (vs −1.13% seated overall) — the toll grows exactly where the
  signal fires and IS charged in every number below.
- **Always-on baselines** (RIDE_FREE cut_card .75): pog −8.99%/unit, main
  −1.15% — the cut-card/no-ace-resplit analogue of E19's csm −8.25%.
- **Ledger (seated: $15 main every round, side staked at TC ≤ −3):**
  side $25 → **+$9/h** on $61k (dead: toll eats it); side $50 → **+$52/h,
  N0 487h, ~$38k** at 200 r/h heads-up; side $100 → **+$138/h, N0 270h,
  ~$56k**. Wong-in (enter only at TC ≤ −3, needs mid-shoe entry):
  +$34/$77/$163 per hour at 200 observed rounds/h for $25/$50/$100 side.
  For scale: crouch15-2r ≈ +$40/h on ~$36–40k; EZ bac ≈ +$92/h on $81k.
  **Per dollar of bankroll this is the project's strongest verdict** — IF
  the side max cooperates.
- Variance caveat: seated sd/bankroll set cov(main, side) = 0 (bins don't
  carry the cross moment); the live verification run measures realized
  combined variance.

**Verdict conditions (order of sensitivity):** (1) **side max** — the whole
result scales with it; $25 max kills it, $50+ beats every blackjack line we
own (READ THE FELT); (2) **penetration** — .75 assumed, unmeasured on the
Ride Free tables; the deep-negative tail is depth-fed (pen sensitivity run
= next arm); (3) mid-shoe side staking freedom (staking the side bet in
round N of a shoe you've sat through is surely fine; wong-IN mid-shoe needs
the entry policy checked); (4) 4-hand resplit cap assumed.

**Not done yet (next chunks):** the no-division human card (RC form of
"TC ≤ −3" — E17's unbalanced-count search machinery points at a pivot-at-−3
count; note hi-lo itself is NOT the optimal lammer count, corr −0.937
leaves ~capture headroom for a POG-specific EOR derivation); pen .70/.80
sensitivity shards; live verification of the literal card (E18 pattern);
optics note (side-jamming at trash counts is novel, unmodeled behavior —
nobody has published this attack).

Seeds consumed: 16.9e9–17.8e9 (+ 16.8e9-block test pins added earlier).
**Next unused block: 17.9e9+.**

## E19 — Silver Stack IS Pot of Gold; the published table is refuted on P(0); the real PT1 edge is 8.25%

**Date:** 2026-07-18 · **Question (Matt, casino recon):** Potawatomi's Ride
Free tables carry a "Silver Stack" side bet — lammers per free bet,
3/10/30/60/100/300/1000 for 1–7. Worth attacking?

**Identification:** the paytable is Galaxy Gaming's Pot of Gold **Pay Table 1
verbatim** (WoO Free Bet page; NV rules-of-play filing "POG 04" differs only
in 6 → 299:1). Published: 5.77% house edge normal / 2.75% splitting 5s
(+0.15% main cost); PT2 4.64%. Nobody has published a composition analysis —
and the WoV thread asking ends in "needs a simulation." Settlement semantics
(NV filing, scanned pages read directly): the lammer is awarded when the
free bet is granted and KEPT win, lose, or push; all PoG wagers lose to a
dealer blackjack.

**Build (M10a, one session):** `Rules.side_bet_pot_of_gold` payout tuple
(PT1/PT2/POG-04 presets), pre-deal `bet_pot_of_gold` hook, settlement =
`settle_pot_of_gold(paytable, free_splits + free_doubles, stake)` — the
engine's existing ledger counters ARE the lammer count; no cards, no RNG, no
new play paths (deal-sequence brace test). `AlwaysPotOfGold` + `SplitFives`
wrappers; token histogram in Metrics; `cli sim --pog / --split-fives`;
21 new tests incl. a scripted 7-lammer resplit chain (292 green).

**Finding 1 — the published table is arithmetically impossible.** P(0
lammers) is strategy-free dealing arithmetic: ≥1 lammer iff the initial two
cards are free-bet eligible (pair A–9, or non-pair hard 9/10/11) and the
dealer has no natural — and enumeration proves every repo strategy takes
every offered free bet (the one divergence family, 5,5 free-double vs
free-split, banks its FIRST lammer either way — the split chain can add
more, which moves mass among k ≥ 1 but never touches P(0); even the A,A
re-pair after splitting aces is taken). Under the lose-to-dealer-BJ rule P(lose) is peek/no-peek
invariant: **exact 6-deck P(0) = 0.838228071**
(`side_bets.exact_p0_pot_of_gold`, exact fractions, rules-driven). WoO
publishes **0.833420** — a "random simulation" with no stated methodology —
irreconcilable at any deck count. Closest reconstruction: their sim let
lammers survive ten-up dealer naturals (ace-peek only). Their k≥2 rungs are
convention-robust; their P(0)/P(1) are not.

**Finding 2 — gate battery (10 × 2M csm rounds, RIDE_FREE_WOO + PT1,
OptimalStrategy; seeds 15.7e9–16.6e9 step 1e8; `data/m10a_gate.py` /
`m10a_verdict.py`):**
- **G1 exact:** P(0) observed 0.838181 vs 0.838228071 → **z = −0.41 ✅** (the
  tier-1 gate: sim == first-principles arithmetic).
- **G3 convention-free published delta:** split-fives PT1 improvement
  **+3.080% ± 0.185 vs WoO +3.019% → z = +0.33 ✅** — this one exercises the
  entire 5,5 resplit/free-double tree, so the multi-token machinery is
  validated against a published number despite Finding 1.
- **G4:** farm's main-game cost −0.173% ± 0.048 vs WoO −0.15% → z −0.48 ✅
  (and the normal arm's main edge −1.027% ± 0.034 re-confirms the M4
  baseline on fresh seeds).
- **G2 shape vs their table:** k=6 −0.9σ, k=7 +0.6σ (23 jackpots in 10M) ✅;
  k=2 +2.8σ, k=3 **−7.8σ** (0.3713% vs 0.3866%, −4% relative), k=4 −2.4σ,
  k=5 −2.0σ — a real shape disagreement beyond the BJ convention.
- **G5 bridge:** measured −8.246% + 4·ΔP0 (+1.923%) = −6.323% vs their
  −5.769%: closes 78%; the −0.55pp residual is exactly the k≥3 shape gap.
  Their absolute table cannot be fully reconstructed under the stated rules;
  our table is pinned by G1 + hand-level chain tests + G3.

**The operative numbers (NV rules, six decks, csm comparator):**
**PT1 −8.246% ± 0.128%** (what Silver Stack actually charges; the advertised
5.77% is an artifact of their convention), POG-04 −8.249%, PT2 −7.071%,
split-fives farm −5.166% ± 0.134%. Per-round sd ≈ 4.1 units. Every paytable
variant prices by arithmetic on the banked token histogram (shards in
`data/m10a_*.json`).

**Consequences for M10b (the attack):** the composition signal must clear
8.25%, not 5.77% — a materially higher bar (quad-Q cleared 3.24% only at
deep pen; but the lammer signal is far stronger: corr(p_free_double,
hilo_tc) = −0.937 with the payoff convex in exactly the events that
negative-count shoes breed). The attack runs on the Potawatomi `RIDE_FREE`
config at real pen with the Ride Free main toll charged at the negative
counts where the side bet fires. Field status: the 6-lammer rung is
felt-confirmed 300:1 (Matt, same day) → Potawatomi's paytable is PT1
exactly; still unknown: side-bet max, resplit cap (assumed 4 hands).

Seeds consumed: 15.7e9–16.6e9 (gate shards), 16.7e9/16.8e9 (test pins).
**Next unused block: 16.9e9+.**

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
14.9e9 (wong depth), 15.0e9–15.5e9 (E18b shards), 15.6e9 (session-variance
percentiles, 2M rounds: 4h sessions P10 −$2,362 / P5 −$3,072 / P1 −$4,480,
47.6% losing, median intra-session low −$1,182 — the "bad day" table in
ARTICLE_BLACKJACK's E18b addendum context). **Next unused block: 15.7e9+.**

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
