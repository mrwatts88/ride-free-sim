# The shelf-guessing theorem — read this first for the card-guessing math thread

> ## ▶ NEXT SESSION — START HERE (updated 2026-07-20)
>
> **CURRENT: E35 + follow-ups A/B + E36 + E37 all DONE; 331 tests green** (routine
> run; the heavy MC/DP gates are `slow`-marked and skipped by default). **E37
> delivered E36's build (a):** `guessing_theorem.exact_e_dp` — Clay's m-shelf
> transition operator made explicit and runnable, computing EXACT E_opt(n,m) past
> the n! wall (first exact deck-scale values: E_opt(52,1)=39 exactly,
> E_opt(52,2)=27.0347). It also SHARPENED E36's cost claim: the operator is
> **Θ(n^{2m})** — polynomial in n for each fixed m (m=1 exactly n²−n+1), exponential
> only in m — because the DFH law caps valleys at m−1; and it PINNED the value
> correction **b(m) = 0, −0.0486, −0.0747 at m=1,2,3** (Follow-up A had only MC
> bounds). **▶ DECIDED (Matt, 2026-07-20): do lead (1) — build (b) — FIRST; lead
> (2) — the proof road — is the deeper parallel thread. BOTH fully specified in §1.**
> **(1) THE NEXT BUILD — build (b), the O(n³) approximate DP** over σ̃ = (t, dir,
> rank, #descents): the LARGE-m complement to E37's exact DP (exact is Θ(n^{2m}),
> dead for m≥5, yet m=5,10 is the real-machine regime). Assumed-density/moment
> closure (E29 doctrine) that collapses the run *composition* to its *count*;
> deliverable = fast E_opt(52, m=5,10) with a MEASURED error bar, gated against
> E37's exact grid + E35 MC. New `guessing_theorem.approx_e_dp` + `data/gt_approx_dp.py`,
> bank as **E38** (§1 has the full plan: state, method, gates, files, seed 24.07e9).
> **(2) THE PROOF ROAD (parallel, hard math not a script)** toward Clay Conjecture 3
> (general m): the operator is now explicit and small for small m, so (i) build it
> as a matrix and compute its SPECTRUM (`data/gt_spectrum.py`; the Tripathi m=1→
> general route, arXiv:2602.07920), and/or (ii) prove the exactly-affine value law
> E37 found (E=c(m)·n+b(m), o(1)<1e-5 by n≈20) — which needs the exact-RATIONAL DP
> (a rational `ShelfPosterior`), also yielding b(m) as exact fractions. §1 item 2.
>
> **▶ HOPE VERDICT — end EVERY session with an updated one (Matt's standing ask,
> 2026-07-20): is hope ALIVE for the big proof** (proving Clay's Conjecture 3 for
> general m ≥ 2)? **ALIVE — and E37 genuinely advanced the equipment** (E36 only
> clarified; E37 *built*). We now hold Clay's open object not just runnable but
> **explicit, sized (Θ(n^{2m}), with the v≤m−1 reason), and PROVEN-exact**, and —
> the new leverage — its OUTPUT is **exactly affine to <1e-5** past a short
> transient, E_opt(n,m) = c(m)·n + b(m) + (vanishing), with b(m) now pinned for
> small m. That converts the proof target from an abstract matrix into two concrete
> hard-math questions you can now stare at directly: (i) find the operator's
> eigenstructure for each fixed m (computable now, the m=1→general-m road Tripathi
> walked), or (ii) prove the affine law + a closed form for b(m). Still hard-math
> hope, not one-more-script — but materially better-founded than before E37, and
> the natural Clay/USC collaboration hook is now a concrete artifact, not a plan.
>
> **TASK 1 IS DONE — the result is now FORMALIZED and banked as experiment E35.**
> The exact grid-wide DFH-`G` optimality (n≤9, m≤10) + the deck-scale value-test
> are written up in `docs/EXPERIMENTS.md` (E35); the helpers are lifted to a
> shared core `src/ridefree/guessing_theorem.py` (`total_prob`, `exact_e` /
> `exact_e_from_perms`, `mc_e` — pure shuffle-math, two-layer rule) that both the
> probes and the tests import; regression anchors live in
> `tests/test_guessing_theorem.py` (`total_prob==1`; `E(n,1)==Fraction(3n,4)` and
> the gap `E_opt==E_G` exact on the n≤7,m≤6 grid; two exact `E(9,m)` values
> MC-validated at ~2 s); the four `data/gt_*.py` core probes carry E35 docstrings
> and were re-run clean; STATUS / ROADMAP (M12d) / memory are updated; **356 tests
> green.** The result below is now the doc's context section, not a to-do.
>
> **STATUS: E35 + BOTH follow-ups are DONE.** Follow-up A — b(m) is a small
> NEGATIVE constant that deepens with m (refines Clay's "≈"). Follow-up B — the
> (52,40) suboptimality lead is REFUTED: DFH's G shows NO measurable suboptimality
> to m=40 at deck scale (the strategy half holds beyond Clay's hedge). Both banked
> in EXPERIMENTS E35.
>
> **▶ E36 DONE (2026-07-20) — the n!-wall scoping probe answered: NO polynomial
> exact algorithm exists via the guessing-state route for m≥2, and we know exactly
> why.** The optimal per-step hit h(prefix) is EXACTLY a function of
> (direction, rank-of-last, ascending-**run-length composition** of the prefix) —
> verified Δhit=0 across n≤8, m∈{2,3,5} — but of NO polynomial coarsening: even the
> exponential ceiling (remaining SET, last, direction) leaves a 0.5 hit gap,
> because a descent in the prefix can only cross a shelf-lane boundary, so the run
> composition (which set+last discards) is load-bearing. The run composition is
> ~2ⁿ states, so this IS why Clay's m-shelf transition matrix is open: its
> transition operator lives on run-compositions, an exponential state space. At
> m=1 the composition collapses and (dir, rank) [O(n²)] is sufficient —
> reproducing Clay's tractable 3n/4. Order-dependence is a weak-mixing effect (the
> set-level gap falls 0.61→0.33→0.04 at m=2/3/5, n=7). Banked: EXPERIMENTS E36,
> shared core `guessing_theorem.walk_prefixes`/`run_lengths`, probe
> `data/gt_sufficiency.py`, 6 pins (328 green).
>
> **▶ THE NEXT CHAPTER — build (a) is DONE (E37); (b) + the proof road remain**
> (framing + specs in "Open questions / next steps" §1 below):
> **(a) the EXACT run-composition DP — DONE, E37** (`guessing_theorem.exact_e_dp`,
> probe `data/gt_exact_dp.py`): Clay's m-shelf operator explicit and runnable,
> exact E_opt to deck scale for small m, cost measured Θ(n^{2m}) (NOT 2ⁿ — poly in
> n per fixed m), b(m) pinned. **(b) the O(n³) APPROXIMATE DP** over
> (dir, rank, #descents) — STILL OPEN, and now the natural next build: it gives fast
> deck-scale values for the LARGE m where (a)'s Θ(n^{2m}) is infeasible (m≥5),
> nearly exact (per-step R²≥0.995, →1 as m grows), bias measurable vs the exact DP
> grid; exact in the strong-mixing limit. **The proof road** (Matt's big-proof
> interest): the operator is now explicit and small for small m — compute its
> spectrum (Tripathi's m=1 route) and/or prove the exactly-affine value law E37
> found. Adjacent, still queued: the polynomial NO-feedback exact number
> (position-matrix column-maxima, RESEARCH_IDEAS 1C); a rational posterior →
> closed-form b(m); the standalone write-up (greenlit); the Clay (USC) hook (now a
> concrete artifact).
>
> **Pre-flight.** PyPy is the accelerator (~4×), NOT on the default PATH; the
> pure-stdlib engine imports fine. Template:
> `PYTHONPATH=/Users/mattwatts/code/ride-free-sim/src /Users/mattwatts/.local/bin/pypy3.11 -u data/<script>.py <args>`
> Exact probes run under `uv run python data/<script>.py`. Seeds: 24.0e9
> (value-test, done); 24.1e9 (Follow-up B); 24.2e9 (Follow-up A); 24.035e9 (E35
> test pins); 24.06e9 (E37 MC cross-check).
>
> (Optional, a larger prose job: fold E35 into the greenlit DFH-verification
> write-up as "exact verification of Conjecture 3's strategy half + the value
> correction" — not required; E35 is self-contained.)
>
> ### FOLLOW-UP A — DONE (2026-07-20): b(m) is a small negative constant
> `data/gt_bm_precision.py`, PyPy 20000-trial (se ~0.008–0.021), seed base 24.2e9.
> The m=1 control measures δ ≡ 0 (estimator unbiased ✓); NO √n/log n growth at 10×
> the value-test precision (E35 O(1)-boundedness holds firmly); and at the
> asymptotic n=104 point δ is small and monotone-NEGATIVE in m —
> δ(104,m) ≈ −0.01 / −0.05 / −0.10 / −0.12 at m=2/3/5/10, decisively nonzero for
> m=5,10 (|z| 5.4, 7.8). So `E = c(m)·n + b(m) + o(1)` with a small negative b(m)
> that deepens with m (sharper than Clay's "≈"). Caveats: b(m) is BOUNDED, not
> pinned (o(1) ≈ b at n≤104 for small m — m=2's δ halves −0.066→−0.015 as n
> doubles); the large-m n=52 points still carry the positive pre-asymptotic
> transient. A precise b(m) / closed form needs larger n (≥208) or a multi-n
> extrapolation. Full table in EXPERIMENTS E35.
>
> ### FOLLOW-UP B — DONE (2026-07-20): the lead is REFUTED, G optimal to ±0.01
> `data/gt_strategy_gap.py`, PyPy 5000-trial CRN, seed base 24.1e9. Measured the
> gap `E_opt−E_G` directly on identical decks (common random numbers), sweeping
> `m=5..40` at n=52,104. EVERY cell is within ~2σ of ZERO, and the only ~2σ blips
> are NEGATIVE (impossible for a true gap — optimal can't lose to G — so noise);
> e.g. (52,40): opt(pred) 4.975 vs G(hit) 5.021, gap −0.008±0.009. So the E35
> (52,40) lead was our value (~4.98) vs DFH's Monte-Carlo SAMPLE (4.7), NOT G
> underperforming. Result: **`G` is optimal to ±0.01 even at m=40, n=52
> (n/2m≈0.65)**, deep inside Clay's hedged regime — the strategy half holds at deck
> scale even more robustly than the n≤9 grid showed. Full table in EXPERIMENTS E35.

**A paradigm-2 Track-A academic spin-off. This is a MATH contribution,
independent of any gambling edge** — it extends the DFH-verification write-up
that was already greenlit (STATUS.md). Opened 2026-07-20 in a research/
brainstorm session (Matt asked for breakthrough ideas beyond gambling; three
research agents produced a menu; Matt picked thread **"1A"**: reuse the exact
shelf-shuffle posterior to attack the OPEN *multi-shelf* card-guessing problem).

This doc is the resume document for the thread: the problem, where it sits in
the literature, what is established, what is running, and the next steps. A cold
session with no context should be able to continue from here.

---

## The problem

Card guessing with **complete feedback** after ONE `m`-shelf DFH shuffle of a
deck of `n` distinct cards. The deck is dealt face up one card at a time; before
each card the player guesses its identity, then sees it (feedback). Maximize the
expected number of correct guesses `E(n, m)`.

- Under a **uniform** shuffle, *any* strategy scores the harmonic number
  `H_n = Σ_{k=1}^n 1/k ≈ 4.5` at `n=52` (`forensics.uniform_guessing_mean`).
- The `m`-shelf machine is NOT uniform, so an input-aware player does better.
  DFH's real casino machine is `m = 10`, one pass; a knowledgeable player scores
  `≈ 9.3 / 52`.
- The **optimal** value is `E(n,m) = E[ Σ_t max_c P(next = c | prefix) ]`
  (greedy Bayes-argmax with feedback is globally optimal — your guesses never
  change the reveals). DFH proposed a simple **`m`-independent** strategy `G`
  ("guess the card following the last shown; once card `n-1` or `n` appears,
  descend") and conjectured it optimal.

## Where this sits in the literature (read from the primary sources, 2026-07-20)

- **DFH 2013** — Diaconis, Fulman, Holmes, *Analysis of casino shelf shuffling
  machines*, Ann. Appl. Prob. 23 (2013), arXiv:1107.2961. Proposed strategy `G`,
  conjectured optimal; reported `≈ 9.3` at `(52, 10)`. (Our repo already
  reproduces DFH's Tables 1–2 exactly — E26.)
- **Clay 2025** — Alexander Clay, *Guessing Strategies for Shelf-Shuffling
  Machines*, arXiv:2507.10294 (USC, ajclay@usc.edu). **Proves ONLY the
  single-shelf `m=1` case**: Thm 1.4 (the optimal strategy is exactly DFH's `G`)
  and Thm 1.5 (**expected reward = `3n/4`**). States **"the transition matrix
  for an arbitrary number of shelves is an open problem."**
  **Conjecture 3** (appendix, p.16), verbatim intent: for an `m`-shelf shuffle
  with `n/m` "not too small," strategy `G` is optimal (high-probability sense)
  and
  ```
  F_G(n, m) ≈ (n / 2m) · H_{2m}        (H_{2m} = the 2m-th harmonic number)
  ```
  Reduces to `3n/4` at `m=1`. Closing line: *"In our future work, we hope to
  make this argument precise."*
- **2026 cluster — all SINGLE-shelf** (so `m≥2` is genuinely unclaimed):
  Tripathi 2602.07920 (confirms Clay's single-shelf eigenvalue conjectures);
  Kuba 2602.12928; asymmetric single-shelf 2606.18047 and Clay–Kuba–Tripathi
  2607.10418. Note: Clay's *no-feedback* appendix conjecture (a different object)
  was later shown non-optimal — the area moves fast; check for new arXiv posts.

**Bottom line:** the multi-shelf (`m ≥ 2`) complete-feedback problem is OPEN, and
Clay's Conjecture 3 sits directly on top of what our exact machinery computes.

## What we have established (exact, gated)

**Method** (`data/gt_exact.py`): exact rational `E_opt(n,m)` from DFH Theorem 3.1
(`forensics.shelf_class_prob` gives `P(perm)` as a function of valley count
alone) + a prefix-trie: `E_opt = Σ over prefixes of (max child probability
mass)`. Fully exact (fractions), no sampling.

**Gates (all pass):** total output probability `= 1`; `E_opt` matches the repo's
*independent* slot-filtering `posterior.PosteriorGuesser` within Monte-Carlo
error; deliberately-suboptimal strategies score **strictly** below `E_opt` while
`G` ties it (`data/gt_robustness.py`) — rules out a "scoring the same thing
twice" bug.

**Results (`n ≤ 9`, `m = 1…10`, exact rationals):**

1. **Reproduces Clay's proven `m=1`:** `E(n,1) = 3n/4` for `n ≥ 2` exactly
   (`3/2, 9/4, 3, …, 27/4`); boundary `E(1,1) = 1`.
2. **DFH strategy `G` is EXACTLY optimal across the whole grid** (gap
   `E_opt − E_G = 0` as exact fractions at all 90 cells) — including cells with
   `n/2m ≈ 0.4`, i.e. **outside Clay's "n/m not too small" hedge**. This is the
   first exact, grid-wide verification of the *strategy* half of Conjecture 3,
   and it appears to hold more broadly than the hedge.
3. **Clay's value formula = the asymptotic slope** `c(m) = H_{2m}/(2m)`
   (`c(1)=3/4`, `c(2)=25/48`, `c(3)=49/120`, `c(5)=7381/25200`,
   `c(10)=11167027/62078016 ≈ 0.1799`). Exact at `m=1`; an approximation for
   `m ≥ 2` (`data/gt_clay_conjecture.py`): our exact values approach it (for
   `m=2` they cross it near `n=7`, within `0.03` by `n=8`); for large `m` at
   small `n` the formula underestimates badly, matching Clay's own
   `(52,20)→6.2` vs `5.56`, `(52,40)→4.7` vs `3.23`.
   **The strategy half and the value half have DIFFERENT regimes** — strategy
   optimality is broad; the value formula is a large-`n/2m` asymptotic. Clay
   bundles them under one hedge; our exact data separates them.

Exact `E_opt(n,m)` grid (regenerate with `data/gt_exact.py 9`):

```
 n\m    1       2       3       5       10
 5    3.7500  2.7188  2.4825  2.3561  2.3016
 6    4.5000  3.1660  2.7850  2.5737  2.4812
 7    5.2500  3.6440  3.0993  2.7828  2.6411
 8    6.0000  4.1415  3.4290  2.9896  2.7875
 9    6.7500  4.6501  3.7745  3.1981  2.9245
```

## The scaled value-test — DONE, banked in E35 (`data/gt_value_mc.py`)

Exact enumeration stops at `n ≈ 9` (`n!`). To test Conjecture 3's **value**
formula in its intended regime (`n/2m` not small) and characterize the
correction `δ(n,m) = E(n,m) − (H_{2m}/2m)·n`, we Monte-Carlo the **low-variance
`predicted` estimator** (`Σ` max-posterior-prob per deck, unbiased for `E(n,m)`,
much tighter than realized hits) via `posterior.ShelfPosterior`.

- Gates: `n=9` MC vs the exact values above; `n=52` MC vs Clay's own table
  (DFH sample `39, 27, 17.6, 9.3, 6.2, 4.7` at `m=1,2,4,10,20,40`).
- Scan `n ∈ {26,52,104,208}`, `m ∈ {1,2,3,5,10}`; report `δ`, `δ/√n`, `δ/ln n`
  to distinguish a constant `b(m)` correction from `√n` / `log n`.
- Seeds: base `24_000_000_000` (fresh; NOT shoe-sim seeds). Exact probes are
  seedless/deterministic.

**RESULTS (2026-07-20, PyPy 3000-trial + CPython 1200-trial, in agreement):**

- **Gates green.** `n=9` MC matches the exact values (`|z| ≤ 1`); `n=52`
  reproduces Clay's own table — `38.99 / 26.98 / 17.51 / 9.29` at `m=1,2,4,10`
  (DFH samples `39 / 27 / 17.6 / 9.3`).
- **Clay's leading term is CONFIRMED as the exact asymptotic slope.** The
  implied slope `[E(n2,m)−E(n1,m)]/(n2−n1)` converges to `c(m)=H_{2m}/(2m)` for
  every `m` (measured `0.750 / 0.519 / 0.408 / 0.293 / 0.179` at
  `m=1/2/3/5/10` vs `c(m)` = `0.750 / 0.521 / 0.408 / 0.293 / 0.180`).
- **The correction `δ(n,m)=E−c(m)·n` is SMALL and BOUNDED — no `√n` or `log n`
  growth; exactly 0 at `m=1`.** Once `n/2m ≳ 2`, `|δ| ≲ 0.1` (MC-noise-limited).
  Control: `m=1` is provably `δ≡0`, yet its low-trial `δ(208,1)=−0.37±0.25`
  fixes the `n=208` noise floor at ~±0.3 — so the other apparent large-`n`
  negatives are noise, not a real correction. Net: `E(n,m)=c(m)·n + O(1)` with a
  small `O(1)` term we can't yet pin below ~0.1.

  ```
  δ(n,m) = E − (H_2m/2m)·n     (PyPy 3000-base; se ~0.01–0.27 growing with n)
   m\n     26      52      104        c(m)=H_2m/2m
    1    -0.011  -0.015  -0.016       0.75000   (provably 0; δ = noise)
    2    -0.041  -0.104  -0.021       0.52083
    3    -0.062  -0.048  -0.037       0.40833
    5    -0.069  -0.128  -0.081       0.29290
   10    +0.422  -0.068  -0.117       0.17989   (n=26 is n/2m=1.3: pre-asymptotic)
  ```
- **Small-`n/2m` transient (Clay's "n/m not too small"):** at `n=26,m=10`
  (`n/2m=1.3`) the value sits well ABOVE the asymptote (`δ=+0.42±0.002`), i.e.
  the slope hasn't set in yet — exactly the regime Clay excluded.
- **Where the formula fails, quantified:** `n=52, m=20/40` → formula `5.56/3.23`
  vs true optimum `6.13/4.98`.
- **LEAD → REFUTED (Follow-up B, 2026-07-20):** at `(52,40)` the optimal value
  `≈4.98` exceeds DFH's *sampled* `4.7`, which hinted `G` might be suboptimal at
  small `n/2m`. Follow-up B measured the gap `E_opt−E_G` directly (CRN), sweeping
  `m=5..40`: every cell within ~2σ of ZERO — DFH's 4.7 was a low Monte-Carlo
  sample, not a real gap. `G` is optimal to ±0.01 even at `(52,40)`; the strategy
  half holds at deck scale, beyond Clay's hedge.
- **Precision caveat:** `n=104/208` used fewer trials (`750/200`, cost-capped),
  se ~0.1–0.27; pinning the exact `O(1)` correction `b(m)` needs a longer PyPy
  run (raise trials, hold `n≤104`). Data: `data/gt_value_mc.py` output.

**Verdict:** the value-test corroborates Conjecture 3's leading term at deck
scale and bounds its correction as small; combined with the exact
strategy-optimality (`n≤9`), this is strong multi-pronged evidence for BOTH
halves of Clay's Conjecture 3, plus the strategy/value regime-split refinement.
A proof still needs the `m`-shelf transition matrix (open).

## Honest bounds (do not overclaim)

- The `m`-invariant optimal *policy* is **Clay's / DFH's conjecture, not our
  discovery** (Conjecture 3 already asserts `G` for all `m`). Our value-add is
  **exact verification** of it across a grid (and beyond the hedge), the
  **strategy/value regime split**, and **exact ground truth** for the value
  correction.
- Exact values are strong *evidence*, not a proof — even now that E37's DP pushes
  them to deck scale for small `m` (n=52 at m=1,2; n≈36 at m=3) and pins b(m). A
  proof of the general-`m` (`m → ∞`) strategy/value still needs the **`m`-shelf
  transition matrix's structure** — E37 makes that matrix explicit and shows it is
  Θ(n^{2m}) with an exactly-affine value law, but *analyzing* it (its spectrum, or
  a proof of the affine law + closed-form b(m)) is real math, not a computation.

## Open questions / next steps

**1. Break the n! wall — build (a) DONE (E37); build (b) + the proof road remain.**
The exact enumeration is O(n·n!) and dies at n≈9. Because the gap is 0 (E35),
`E_opt = E_G = Σ over prefixes of P·h`, aggregable iff the per-step hit
`h(prefix) = max_c P(next=c|prefix)` is a function of a small Markov statistic
`σ(prefix)`. E36 found the minimal sufficient σ = (direction, rank-of-last,
ascending-run-length composition) and PROVED its transition closed (the whole
posterior, not just its max, is a function of σ; max Δposterior/state = 0).

- *(a) The EXACT run-composition DP — DONE (E37), `guessing_theorem.exact_e_dp`.*
  Memoized DFS over σ (representative posterior per state, deduped) + a forward
  mass pass: `E_opt(n,m) = Σ_σ P(σ)·h(σ)`, EXACT. **Gates pass** — reproduces the
  E35 rationals on the whole n≤7×m≤10 grid (worst |Δ| 2e-15) and the deck-scale MC
  within se. **Reshaped E36's cost claim:** the reachable-state count is measured
  **Θ(n^{2m})** — polynomial in n for each fixed m (m=1 EXACTLY n²−n+1, m=2 quartic,
  m=3 sextic; log-log degrees 2.08/4.13/6.09), NOT the flat ~2ⁿ E36 hedged from
  n≤8. Reason: the DFH law caps output valleys at m−1 (`shelf_class_prob` vanishes
  for v>m−1). So E36's "~2ⁿ" was the worst case over all m; the operator is
  tractable in n per fixed m, exponential only in m — the same strategy/value-style
  split, now at complexity. **Wall broken:** exact E_opt(52,1)=39=3·52/4 and
  E_opt(52,2)=27.0347 (first exact m≥2 deck-scale values; m=3 exact to n≈36); and
  the value law is exactly affine past a short transient, pinning **b(m) = 0,
  −0.0486, −0.0747 at m=1,2,3**. (Full result: EXPERIMENTS E37.) *Still open on this
  build:* a rational posterior would make the DP exact-rational → a closed-form
  b(m); and run-composition pruning (drop rare many-descent σ, controlled
  truncation) would push exact-ish values to deck scale for larger m — but build (b)
  does the large-m job more principledly.
- *(b) ▶ **THE NEXT BUILD (DECIDED, Matt 2026-07-20) — do this first.** The O(n³)
  APPROXIMATE DP (assumed-density closure, the E29 doctrine): the large-m complement
  to (a), because exact is Θ(n^{2m}) and dies for m≥5, yet m=5,10 are the DFH-real
  machine regime.* Concrete plan:
  - **State** σ̃ = (t, direction, rank-of-last, #descents) — the E37 exact state with
    the run *composition* collapsed to its *count* (E36 showed #descents alone leaks
    the placement; that leak IS the controlled approximation here). O(n·2·n·n) = O(n⁴)
    cells, but only O(n³) alive per step → a genuine polynomial DP.
  - **Method** — propagate the σ̃ *distribution* forward under an assumed-density
    (moment-closure) transition: at each (t→t+1) the exact posterior would need the
    full run composition, so approximate the per-σ̃ next-card law by the mass-weighted
    average over the compositions folded into σ̃ (project onto the σ̃ family, exactly
    the `AssumedDensityShelfPosterior` pattern). Then Ẽ_opt(n,m) = Σ_σ̃ P(σ̃)·h(σ̃).
  - **Gates (the honest error bar is the whole point)** — E36 measured the per-step
    fit already: (dir, rank, #descents) is R² ≥ 0.995, → 1 as m grows, exact ≤ n=5.
    Gate the AGGREGATE bias against **E37's exact grid** (m=1,2 to n=52; m=3 to n≈36)
    and the E35 MC. Report Ẽ_opt − E_opt as a table; it must → 0 as m grows (the
    strong-mixing limit) and stay small where measurable.
  - **Deliverable** — fast exact-ish E_opt(52, m=5,10) with a MEASURED error bar,
    the values E35 had only as MC and E37 can't reach. Also feeds the b(m) closed
    form (item 3) at larger m.
  - **Files** — `guessing_theorem.approx_e_dp(n, m)` (shared core, two-layer rule)
    + probe `data/gt_approx_dp.py` (bias table vs the E37 exact grid + E35 MC);
    regression pins mirroring E37's. Bank as **E38**. Seeds: next free 24.07e9 (MC
    cross-check only; the DP is seedless).
- *Adjacent stepping stone, still computable NOW.* The NO-feedback multi-shelf
  reward = Σ of column-maxima of the m-shelf position matrix (RESEARCH_IDEAS 1C;
  Tripathi did m=1) — a Poisson-binomial over the slot geometry, genuinely
  polynomial and exact. Produces the exact `m=10, n=52` no-feedback number and
  exercises the position matrix without the feedback complication.

**2. ▶ THE PROOF ROAD — the deeper parallel thread (lead 2) toward Clay's
Conjecture 3 for general m.** This is the big-proof direction (Matt's standing
interest); it is hard research math, NOT a script, but E37 turned the target from
an abstract open matrix into a concrete, explicit, small-for-small-m operator you
can now stare at. Two attacks, pursue in parallel with build (b):
- *(i) The spectrum.* E37's DP transition operator is Clay's m-shelf matrix in
  explicit form. For each fixed m it is Θ(n^{2m}) but small at small n — build it as
  an actual matrix (states × states) and compute its eigenvalues/eigenvectors.
  Tripathi (arXiv:2602.07920) confirmed Clay's *single-shelf* eigenvalue conjectures;
  the road to general m is to find the analogous eigenstructure here. Look for a
  pattern in the spectrum across m (the eigenvalues that govern the n→∞ slope c(m)
  and the correction b(m)). A `data/gt_spectrum.py` that assembles the operator and
  reports its spectrum for m=1,2,3 is the concrete first step.
- *(ii) Prove the affine value law.* E37 found E_opt(n,m) = c(m)·n + b(m) + o(1)
  with the o(1) MEASURED below 1e-5 by n≈20 (m=2), the slope EXACTLY c(m) between
  n=26 and 52. If this is *exactly* affine past some N(m) — not just numerically —
  that is a clean theorem (a fixed intercept b(m) once the transient clears), and
  its proof would come straight from the operator's dominant eigenvalue being
  exactly 1 with a specific eigenvector. Testing exactness needs the exact-RATIONAL
  DP (a rational `ShelfPosterior` — the per-state hit is a ratio of exact shelf-law
  quantities); it also yields b(m) as exact fractions to pattern-match (item 3).
- *The write-up + Clay hook (items 4–5) are the natural outputs of this thread.*
  Clay (USC, ajclay@usc.edu) explicitly flagged general-m as future work; the
  explicit operator + the affine law + pinned b(m) is now a concrete artifact to
  open a collaboration on — much stronger than a cold email.

**3. Pin `b(m)` — largely DONE via E37 for small m.** The exact DP pins b(1,2,3) =
0, −0.0486, −0.0747 (δ flat to <1e-5 past n≈20–36), superseding Follow-up A's MC
bounds. What remains: a CLOSED FORM b(m) = f(m) — needs either the exact-rational
DP (rational posterior, above) for exact b(m) fractions to hunt a pattern, or
larger-m exact points (m≥5 wants build (b) / pruning, since exact is Θ(n^{2m})).

**4. The standalone write-up (greenlit).** Fold E35 + Follow-ups A/B **+ E37** into
"exact verification of Conjecture 3's strategy half (optimal even beyond the hedge,
to m=40 at deck scale) + the value leading-term + the pinned `b(m)` correction +
the strategy/value regime split + the Θ(n^{2m}) complexity of the explicit m-shelf
operator." A self-contained prose job.

**5. Collaboration hook.** Clay (USC, ajclay@usc.edu) explicitly flagged the
general-m case as future work — a natural outreach once build (b) / the proof road
produces something (now a concrete artifact, per item 2).

**DONE this thread:** E35 (banked — `docs/EXPERIMENTS.md`, shared core
`src/ridefree/guessing_theorem.py`, anchors `tests/test_guessing_theorem.py`);
Follow-up A (b(m) small-negative); Follow-up B (G-optimality confirmed to m=40,
the (52,40) lead refuted); **E36** (the n!-wall scoping probe — minimal sufficient
statistic = run-length composition; no poly-exact route uniformly for m≥2; two
constructive builds specified in §1); **E37** (build (a) — the exact
run-composition DP `exact_e_dp`: Clay's m-shelf operator explicit and runnable,
exact E_opt to deck scale for small m, cost measured Θ(n^{2m}) not 2ⁿ, b(1,2,3)
pinned; probe `data/gt_exact_dp.py`, 4 pins, 331 green).

## File map (how to reproduce)

Machinery (existing `src/ridefree/`, gated in `tests/`):
- `shuffle.py` — `ShelfShuffle(shelves=m, passes=1)` (DFH Description 1).
- `forensics.py` — `shelf_class_prob` (DFH Thm 3.1), `ShelfGuesser` (DFH's
  strategy `G`, `m`-independent), `uniform_guessing_mean` (`H_n`),
  `guessing_experiment`.
- `posterior.py` — `ShelfPosterior` (exact next-card law), `PosteriorGuesser`
  (`predicted` = the low-variance value estimator).
- `guessing_theorem.py` — shared core: `total_prob`, `exact_e`/`exact_e_from_perms`
  (O(n·n!) enumeration), `run_lengths`, `walk_prefixes` (E36), **`exact_e_dp` (E37 —
  the run-composition DP, Clay's m-shelf operator explicit; Θ(n^{2m}), deck-scale
  exact for small m)**, `mc_e`.

Probes (`data/`, run `uv run python data/<f>.py [args]`):
- `gt_exact.py [n_max]` — exact `E_opt(n,m)` grid + the exact DFH-optimality gap
  (currently 0 everywhere) + first-difference slopes + `m`-column fractions.
- `gt_exact_dp.py [n_deck] [m1,..] [cap_M]` — E37, the run-composition DP: gates
  (vs enumeration + MC), the Θ(n^{2m}) state-growth law, exact E_opt past the n!
  wall (deck-scale for small m), and the pinned correction δ(n,m)→b(m). **Run
  under PyPy** for the heavy columns (m=3 at deck scale is ~n⁶ states):
  `PYTHONPATH=…/src /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_exact_dp.py 52 1,2,3`
- `gt_robustness.py` — strict-inequality check (suboptimal strategies `<` opt).
- `gt_clay_conjecture.py` — exact `E_opt` vs Clay's `(n/2m)H_{2m}`; confirms
  `c(m)=H_{2m}/(2m)`, `m=1` exact, the regime split.
- `gt_value_mc.py [trials]` — the scaled MC value-test (above). **Run under
  PyPy** (~4× CPython; the sanctioned accelerator, but not on the default
  non-interactive PATH):
  `PYTHONPATH=/Users/mattwatts/code/ride-free-sim/src /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_value_mc.py 3000`
- `gt_sufficiency.py [n_max] [m1,m2,...]` — E36, the n!-wall sufficiency probe:
  bins the optimal per-step hit by a ladder of candidate statistics, reports
  exact-sufficiency (max Δhit) / R² / state-space growth, and prints concrete
  order-dependence witnesses. Uses the shared core
  `guessing_theorem.walk_prefixes` / `run_lengths`.

Primary-source PDF of Clay 2025 was fetched to a tool-results path (ephemeral);
re-fetch from arXiv:2507.10294 if needed. Related memory:
`memory/shuffle-guessing-theorem.md`.
