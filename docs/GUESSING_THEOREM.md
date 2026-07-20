# The shelf-guessing theorem — read this first for the card-guessing math thread

> ## ▶ NEXT SESSION — START HERE (updated 2026-07-20)
>
> **CURRENT: E35 + follow-ups A/B + E36 + E37 + E38 + E39 + E40 all DONE; 338 tests
> green** (routine fast run; heavy MC/DP gates are `slow`-marked, skipped by default).
> **▶ E40 (2026-07-20) — PHASE 1 of the proof road is DONE, and it landed the headline
> the spectrum was pointing at: a CLOSED FORM for the value-law intercept.**
> - **(1a) The critical checkpoint PASSED.** The E39 eigenvalue law
>   `{i/m}(×3) ∪ {(2i−1)/2m}(×1)`, gap 1/m, order-(4m−3) recurrence, is now CONFIRMED
>   at **m=5** (order-17 recurrence OOS-predicts all 21 exact rationals across every
>   window, ZERO mismatches) and **m=6** — so it holds at m=2,3 (rigorous over ℚ) and
>   m=4,5,6 (OOS-validated). Five m's; not a two-point accident. It did NOT break, so
>   we proceed to Phase 2.
> - **(1b) The CLOSED FORM (resolves E39's OPEN item):**
>   ```
>   b(m) = 3/2 − 1/(4m) − H_{2m}^{(2)},        H_{2m}^{(2)} = Σ_{k=1}^{2m} 1/k²
>   ```
>   the UNIQUE ≤3-feature exact-rational fit reproducing all six exact intercepts
>   b(1..6) = 0, −7/144, −269/3600, −63449/705600, −126713/1270080, −16388909/153679680.
>   Finite limit **b(∞) = 3/2 − π²/6 ≈ −0.14493**. (E39's "denom odd part = ((2m−1)!!)²"
>   was a small-m coincidence; the closed form supersedes it.)
> - **THE FULL VALUE LAW is now explicit** (Clay gave only the leading term):
>   ```
>   E_opt(n,m) = (H_{2m}/2m)·n  +  [3/2 − 1/(4m) − H_{2m}^{(2)}]  +  O((1−1/m)^n)
>   ```
>   **Structural key for Phase 2:** slope = average of 1/k over the 2m slots
>   (first-order harmonic H_{2m}); intercept built from Σ 1/k² over the SAME slots
>   (second-order H_{2m}^{(2)}) — the parallel that should reveal the unit eigenvector.
>   At m=1 it is exactly 3n/4 (b(1)=0, tail vanishes) — Clay's proven Thm 1.5.
>   Full write-up EXPERIMENTS E40; probes `data/gt_bm_closed_form.py` (self-validating)
>   + `data/gt_rational_dp.py` (extended, m=5,6 enabled); 2 fast pins (+1 slow
>   cross-check).
>
> **E39 (step 1, still the basis) — the m-shelf FEEDBACK operator's SPECTRUM.** Running
> E37's run-composition DP in EXACT RATIONALS (`guessing_theorem.exact_e_dp_rational`,
> a `_RationalShelfPosterior` — slot geometry is integer, only probabilities need
> rationalizing) makes `δ(n,m)=E_opt−c(m)·n` exact. It is C-finite over ℚ:
> Berlekamp–Massey recovers its minimal recurrence (order **4m−3**), char poly factors
> EXACTLY as `(x−1)·∏(x−i/m)^3·∏(x−(2i−1)/2m)`, so the subdominant eigenvalues are
> **{i/m}(×3) ∪ {(2i−1)/2m}(×1)**, gap **1/m**, correction **(1−1/m)ⁿ**. σ is EXACTLY
> sufficient (rational DP == n! enumeration as Fractions); "exactly affine" is REFUTED
> (nonzero oscillatory (1−1/m)ⁿ tail). Full write-up EXPERIMENTS E39; probe
> `data/gt_rational_dp.py`.
>
> **⚠ FRAMING CORRECTION banked with E39 — the Tripathi detour was a wrong turn.**
> The earlier note "assemble the operator as a matrix, compute its spectrum, gate
> m=1 against Tripathi's published eigenvalues" conflated TWO matrices. **Tripathi
> (arXiv:2602.07920) diagonalized the single-shelf POSITION matrix**
> `M(i,j)=[C(i−1,j−1)+C(i−1,n−j)]/2^i` (spectrum `{1/4^k}∪{0}`), which governs the
> **NO-feedback** game (single-shelf value ≈ √(2n/π) ≈ 5.75 at n=52). **Clay's
> Conjecture 3 and our E37/E39 operator are the COMPLETE-FEEDBACK problem**
> (single-shelf value = 3n/4 = 39). Different games, different matrices; the
> position matrix is NOT on the Conjecture-3 road, and E37's operator (a leveled
> DAG) is nilpotent — no naive spectrum to assemble. E39 gets the FEEDBACK
> operator's spectrum the right way: read off the exact value sequence, not from an
> assembled matrix. Do not chase Tripathi's eigenvalues for Conjecture 3.
>
> **▶ THE NEXT STEP — the recommended plan, in plain terms (Matt endorsed this
> framing 2026-07-20; §2 has the technical detail).**
>
> **WHAT WE ARE ULTIMATELY DOING, and why the spectrum IS the goal (not a side
> quest).** Clay's Conjecture 3 bundles two claims: (1) the VALUE claim — the score
> formula E_opt ≈ (n/2m)·H₂ₘ (this is the HARD half; Clay flagged "the m-shelf
> transition matrix" as the open obstacle to it), and (2) the STRATEGY claim — that
> DFH's simple rule G is the best possible strategy. **Proving our spectrum
> `{1}∪{i/m}(×3)∪{(2i−1)/2m}` for all m PROVES claim (1) — the hard half — in a
> SHARPER form than Clay stated:** the unit eigenvalue forces the linear growth (and
> its eigenvector pins the slope to exactly c(m)=H₂ₘ/2m), the gap 1/m forces the
> leftover to settle onto a fixed number b(m), so E_opt = c(m)·n + b(m) + O((1−1/m)ⁿ)
> — Clay's formula PLUS the exact intercept and fade-rate he never claimed. Claim (2)
> is SEPARATE and already in hand (our DP computes OPTIMAL play directly — greedy
> Bayes-argmax is provably globally optimal, needs no assumption about G — and G is
> verified == optimal everywhere computed, to m=40 at deck scale, Follow-up B). So
> "prove the spectrum" is the concrete, well-defined form of "prove the open half of
> Conjecture 3."
>
> **THE PLAN, in order:**
> - **PHASE 1 — DONE (E40, 2026-07-20).** (1a) The eigenvalue law is CONFIRMED at m=5
>   (the critical checkpoint — order-17 recurrence OOS-predicts all 21 terms, ZERO
>   mismatches) and m=6; it holds at m=2,3 (rigorous ℚ) + m=4,5,6 (OOS). It did NOT
>   break. (1b) The closed form is found: **b(m) = 3/2 − 1/(4m) − H_{2m}^{(2)}**, the
>   unique ≤3-feature exact fit of b(1..6), limit 3/2 − π²/6. The full value law is now
>   explicit: E_opt(n,m) = (H_{2m}/2m)·n + [3/2 − 1/(4m) − H_{2m}^{(2)}] + O((1−1/m)ⁿ).
>   (Details: EXPERIMENTS E40; §2–3 below; `data/gt_bm_closed_form.py`.)
> - **▶ PHASE 2 — NOW THE ACTIVE STEP: the actual proof (hard math, not a script).**
>   Prove the eigenvalue formula for all m ⟹ the value half of Conjecture 3. Route:
>   find the EIGENVECTORS (the "shapes") of the homogenized transfer operator — the
>   eigenVALUES are known (proven-pattern at m≤6), the eigenVECTORS are the missing
>   half and the key. Identify them from the small-m operators (E39 builds them
>   explicitly), guess the general-m form, then VERIFY it satisfies the operator
>   equation (guess-and-verify — usually a clean algebraic identity). **Phase 1's
>   closed form is the concrete lever:** the unit eigenvector's projection is EXACTLY
>   3/2 − 1/(4m) − H_{2m}^{(2)} and the slope-mode's is H_{2m}/2m — first- vs
>   second-order harmonic sums over the SAME 2m slots. That parallel is almost
>   certainly the eigenvector's signature: look for a unit eigenvector whose entries
>   are built from partial sums of 1/k and 1/k² over the slot geometry, guess-and-verify
>   against E37's explicit small-m operator. A unit eigenvalue with a spectral gap is
>   precisely "the affine value law," so this and proving the value law are one theorem.
>   *(Optional de-risk first: push the eigenvalue-law confirmation to m=7 — cheap
>   relative to a proof, one more data point — but the checkpoint already passed at
>   m=5,6, so this is confidence, not a gate.)*
> - **Adjacent / outputs:** the standalone write-up (greenlit — now folds in E36–E40
>   WITH the spectrum AND the closed-form value law); the Clay/USC hook
>   (ajclay@usc.edu; the explicit operator + its small-m spectrum + the closed-form
>   b(m) + the full value law is a strong concrete collaboration artifact — Clay
>   flagged general-m as future work and gave only the leading term, we now have the
>   exact intercept and fade rate). Still open from E38: a richer approximate statistic
>   to close m=10's −0.085 residual (unrelated to the proof road).
>
> **▶ HOPE VERDICT — end EVERY session with an updated one (Matt's standing ask,
> 2026-07-20): is hope ALIVE for the big proof** (proving Clay's Conjecture 3 for
> general m ≥ 2)? **ALIVE, and RAISED AGAIN by E40 — Phase 1 closed with a bigger
> result than expected.** E39 gave the spectrum as a conjecture at m≤4; E40 (a) passed
> the critical checkpoint (the eigenvalue law holds at m=5 AND m=6 — five m's, not a
> two-point accident, so the universality assumption Phase 2 rests on is well-founded)
> and (b) landed a CLOSED FORM for the intercept, b(m)=3/2−1/(4m)−H_{2m}^{(2)}, giving
> the COMPLETE value law E_opt = (H_{2m}/2m)n + b(m) + O((1−1/m)ⁿ) — Clay's leading
> term PLUS the exact intercept and fade rate he never claimed. Why this raises hope
> concretely: the closed form is not just an answer, it's the strongest available HINT
> for the Phase-2 eigenvector — slope from Σ1/k, intercept from Σ1/k² over the same 2m
> slots screams "the unit eigenvector is built from harmonic partial sums of the slot
> geometry," turning Phase 2 from "find an unknown eigenvector" into "guess-and-verify
> a harmonic ansatz against E37's explicit operator." Still NOT a proof: the general-m
> spectrum theorem + its eigenvectors remain real hard math (an induction on the
> run-composition operator, or the eigenvector combinatorics), not a script. But the
> target is now maximally concrete — a clean eigenvalue formula AND a clean
> eigenvector-projection formula, both verified at m≤6. The Clay/USC collaboration is
> the realistic route to the general-m theorem, now with a genuinely strong artifact:
> the explicit operator + its spectrum + a closed-form value law that sharpens the
> conjecture itself.
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
> **▶ THE NEXT CHAPTER — builds (a) AND (b) are DONE (E37, E38); the proof road
> remains** (framing + specs in "Open questions / next steps" §1 below):
> **(a) the EXACT run-composition DP — DONE, E37** (`guessing_theorem.exact_e_dp`,
> probe `data/gt_exact_dp.py`): Clay's m-shelf operator explicit and runnable,
> exact E_opt to deck scale for small m, cost measured Θ(n^{2m}) (NOT 2ⁿ — poly in
> n per fixed m), b(m) pinned. **(b) the APPROXIMATE DP — DONE, E38, with a PIVOT**
> (`guessing_theorem.approx_e_dp`, probe `data/gt_approx_dp.py`): the spec's
> #descents (run COUNT) closure FAILS at deck scale (compounds to a wrong slope);
> the run-length MULTISET (run distribution) is the working closure — exact-grade
> for m≤5 (m=5 z+0.3 vs MC; recovers b(3)), ~0.9% low at m=10, fast+deterministic
> where (a) is Θ(n^{2m})-dead. The finding: the multiset, not the count, is the
> minimal *aggregating* summary. **The proof road** (Matt's big-proof interest, now
> the primary thread): the operator is explicit and small for small m — compute its
> spectrum (Tripathi's m=1 route) and/or prove the exactly-affine value law E37
> found (via a rational DP). Adjacent, still queued: a richer approximate statistic
> to close m=10's residual; the polynomial NO-feedback exact number (position-matrix
> column-maxima, RESEARCH_IDEAS 1C); a rational posterior → closed-form b(m); the
> standalone write-up (greenlit, folds in E36–E38); the Clay (USC) hook.
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
  Tripathi 2602.07920 (confirms Clay's single-shelf eigenvalue conjectures — but
  those are the eigenvalues of the **POSITION matrix** `M(i,j)=P(card i→pos j)`,
  which governs the **NO-feedback** game, `{1/4^k}∪{0}`, single-shelf value
  ≈√(2n/π); a DIFFERENT object from Clay's complete-feedback transition matrix and
  from our E37/E39 operator — do not conflate them, see E39's framing correction);
  Kuba 2602.12928; asymmetric single-shelf 2606.18047 and Clay–Kuba–Tripathi
  2607.10418. Note: Clay's *no-feedback* appendix conjecture (a different object)
  was later shown non-optimal — the area moves fast; check for new arXiv posts.

**Bottom line:** the multi-shelf (`m ≥ 2`) **complete-feedback** problem is OPEN,
and Clay's Conjecture 3 sits directly on top of what our exact machinery computes.
(E39 has now computed that operator's subdominant SPECTRUM for m≤4:
`{i/m}(×3)∪{(2i−1)/2m}(×1)`, gap 1/m — a concrete general-m conjecture to prove.)

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

**1. Break the n! wall — builds (a) DONE (E37) and (b) DONE (E38); the proof road remains.**
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
- *(b) The APPROXIMATE DP — DONE (E38), `guessing_theorem.approx_e_dp`, WITH A
  PIVOT from the plan below.* The spec was to key by σ̃ = (t, dir, rank, **#descents**)
  — collapse the run composition to its COUNT. Built and measured, that FAILS at
  deck scale: #descents is bounded ~2m while run lengths grow ~n/2m, so its per-step
  error compounds into a WRONG asymptotic slope (E_opt(52,5) off −4.3, E_opt(52,10)
  off −2.1 — a near-exact-looking n≤12 gate that collapses by n=52). Neither a
  mass-weighting beam (bias flat vs beam width — the lumping is intrinsic) nor a
  first/last-run enrichment rescues it. **The fix: key by the run-length MULTISET
  (the *distribution* — how many runs of each length, run ORDER discarded), not the
  count.** Same E37 transition, coarser dedup key, mode representative. Result:
  EXACT-GRADE for m ≤ 5 at deck scale (m=5 bias vs MC +0.014 z+0.3; m=3 δ recovers
  E37's exact b(3)) and ~0.9% low at m=10 (−0.085) — vs #descents' −2 to −4.
  **Deliverable delivered:** fast, deterministic E_opt(52, m) = 39, 27.035, 21.158,
  15.112, 9.214 at m=1,2,3,5,10, where E37's Θ(n^{2m}) is dead. Cost = run-length
  PARTITIONS (≪ ordered Θ(n^{2m}), by up to (2m)!); a `max_run` cap merges the
  long-run tail losslessly for very large m. **The finding:** it is not enough for a
  statistic to predict the per-step hit (E36: #descents is R²≥0.995 per-step yet
  fails in aggregate); the aggregate DP amplifies residual error, so the run-length
  *distribution*, not its *count*, is the minimal *aggregating* summary — sharpening
  E36. Why the multiset suffices approximately: its per-step sufficiency gap shrinks
  with m (0.25/0.068/0.011 at m=2/3/5) — run order matters exactly but washes out as
  mixing improves (the strong-mixing limit made concrete). Full result: EXPERIMENTS
  E38; probe `data/gt_approx_dp.py`; 5 pins. *Still open on this build:* a richer
  approximate statistic (a little run-order info) to close m=10's −0.085 residual.
- *Adjacent stepping stone, still computable NOW.* The NO-feedback multi-shelf
  reward = Σ of column-maxima of the m-shelf position matrix (RESEARCH_IDEAS 1C;
  Tripathi did m=1) — a Poisson-binomial over the slot geometry, genuinely
  polynomial and exact. Produces the exact `m=10, n=52` no-feedback number and
  exercises the position matrix without the feedback complication.

**2. ▶ THE PROOF ROAD — the primary thread (lead 2) toward Clay's Conjecture 3 for
general m. Step 1 DONE (E39): the operator's SPECTRUM, for m≤4.** This is the
big-proof direction (Matt's standing interest); it is hard research math, NOT a
script, but E37 turned the target from an abstract open matrix into a concrete
operator, and E39 read off its eigenvalues.
- *(i) The spectrum — DONE for m≤4 (E39), the RIGHT way.* Note first the FRAMING
  FIX: E37's operator, as one matrix over all states, is a leveled DAG — strictly
  triangular, hence NILPOTENT (all eigenvalues 0), so "assemble it and take its
  spectrum" is vacuous; and Tripathi's `{1/4^k}` are the NO-feedback POSITION
  matrix's eigenvalues, a different object (see the framing correction up top).
  E39 instead reads the spectrum off the exact VALUE sequence: `δ(n,m)` is C-finite
  over ℚ, and its minimal recurrence (Berlekamp–Massey, order 4m−3) has char poly
  `(x−1)·∏_{i=1}^{m−1}(x−i/m)^3·∏_{i=1}^{m−1}(x−(2i−1)/2m)` EXACTLY. So the
  operator's subdominant eigenvalues are **{i/m : i=1..m−1} (mult 3) ∪
  {(2i−1)/2m : i=1..m−1} (simple)**, spectral gap **1/m**, slowest mode
  **(1−1/m)ⁿ** — exact over ℚ at m=2,3 (BM from data alone), OOS-validated at m=4.
  Probe `data/gt_rational_dp.py`. **Extended (E40): CONFIRMED at m=5 (the critical
  checkpoint — order-17 recurrence OOS-predicts all 21 terms) and m=6.** So the law
  holds at m=2,3 (rigorous ℚ) + m=4,5,6 (OOS) — five m's. **The remaining general-m
  step:** PROVE this eigenvalue formula for all m — now a specific structural claim
  about the run-composition operator (an induction on the transition, or the
  eigenvectors' combinatorics), not "analyze an open matrix."
- *(ii) The affine value law — MECHANISM now explicit (E39).* E37 found E_opt =
  c(m)·n + b(m) + o(1); E39's exact DP shows the o(1) is a NONZERO, oscillatory
  (1−1/m)ⁿ tail (NOT "exactly affine past N" — m=2's δ overshoots at n=16 then
  returns to b(2)). The law's structure is exactly the spectrum: the unit
  eigenvalue gives c(m)·n and its eigenvector projection gives b(m); the gap 1/m
  gives convergence. So proving the affine law ⟺ proving eigenvalue 1 is simple and
  dominant with a spectral gap — the same theorem as (i). **b(m) now has a CLOSED
  FORM (E40, item 3):** its unit-eigenvector projection is exactly
  3/2 − 1/(4m) − H_{2m}^{(2)}, so the value law is fully explicit. **Remaining:** the
  general-m proof (as in (i)) — and the closed form is the concrete Phase-2 lever
  (find the unit eigenvector whose projection gives that harmonic form).
- *The write-up + Clay hook (items 4–5) are the natural outputs of this thread.*
  Clay (USC, ajclay@usc.edu) explicitly flagged general-m as future work; the
  explicit operator + its small-m spectrum + the CLOSED-FORM value law
  E_opt = (H_{2m}/2m)n + [3/2 − 1/(4m) − H_{2m}^{(2)}] + O((1−1/m)ⁿ) is now a strong
  concrete artifact to open a collaboration on (sharper than the conjecture Clay stated).

**3. Pin `b(m)` — CLOSED FORM FOUND (E40).** The exact-rational DP + GF limit pins
**b(2)=−7/144, b(3)=−269/3600, b(4)=−63449/705600, b(5)=−126713/1270080,
b(6)=−16388909/153679680**, and the unique ≤3-feature exact-rational fit over a
harmonic/rational library is
```
b(m) = 3/2 − 1/(4m) − H_{2m}^{(2)},     H_{2m}^{(2)} = Σ_{k=1}^{2m} 1/k²,
```
matching all six exact points (b(1)=0 too), with finite limit **3/2 − π²/6 ≈ −0.14493**.
(E39's "denominator odd part = ((2m−1)!!)²" was a small-m coincidence — it breaks at
m=5; the closed form supersedes it.) Probe `data/gt_bm_closed_form.py` (self-validating,
asserts uniqueness). *Still open:* an even simpler / more illuminating derivation
(the Phase-2 eigenvector is the natural route).

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
pinned; probe `data/gt_exact_dp.py`, 4 pins, 331 green); **E38** (build (b) — the
approximate DP `approx_e_dp`, WITH A PIVOT: the spec's #descents/run-COUNT closure
fails at deck scale, so the working closure is the run-length MULTISET; exact-grade
for m≤5 at deck scale, ~0.9% at m=10, fast+deterministic where (a) is Θ(n^{2m})-dead;
the finding — the multiset, not the count, is the minimal aggregating summary;
probe `data/gt_approx_dp.py`, 5 pins, 334 green fast / 371 full); **E39** (the
proof road, step 1 — the exact-rational DP `exact_e_dp_rational`: σ exactly
sufficient (== enumeration as Fractions), the o(1) refuted-as-exactly-affine
(oscillatory (1−1/m)ⁿ tail), **b(2,3,4)=−7/144, −269/3600, −63449/705600 exact**,
and the FEEDBACK operator's subdominant SPECTRUM {i/m}(×3)∪{(2i−1)/2m}(×1), gap
1/m — order-4m−3 recurrence, exact over ℚ at m≤3, OOS at m=4; also the Tripathi
framing correction (position vs feedback matrix); probe `data/gt_rational_dp.py`,
3 pins, 336 green fast); **E40** (PHASE 1 done — the eigenvalue law CONFIRMED at m=5
[the critical checkpoint] and m=6, and the CLOSED FORM for the intercept
**b(m) = 3/2 − 1/(4m) − H_{2m}^{(2)}** [limit 3/2 − π²/6], the unique ≤3-feature fit of
b(1..6); the full value law E_opt = (H_{2m}/2m)n + b(m) + O((1−1/m)ⁿ) now explicit;
probes `data/gt_bm_closed_form.py` + `data/gt_rational_dp.py` [extended], 2 fast pins
+1 slow cross-check, 338 green fast).

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
  exact for small m)**, **`approx_e_dp(n, m, max_run=None)` (E38 — the run-length
  MULTISET DP; polynomial for large m, exact-grade to m≤5 at deck scale, ~1% at
  m=10; `max_run` caps the run-length tail losslessly)**, **`exact_e_dp_rational`
  + `_RationalShelfPosterior` (E39 — the SAME DP in exact `Fraction`s; E_opt(n,m)
  rational → exact δ(n,m), b(m), and the operator spectrum)**, `mc_e`.

Probes (`data/`, run `uv run python data/<f>.py [args]`):
- `gt_exact.py [n_max]` — exact `E_opt(n,m)` grid + the exact DFH-optimality gap
  (currently 0 everywhere) + first-difference slopes + `m`-column fractions.
- `gt_exact_dp.py [n_deck] [m1,..] [cap_M]` — E37, the run-composition DP: gates
  (vs enumeration + MC), the Θ(n^{2m}) state-growth law, exact E_opt past the n!
  wall (deck-scale for small m), and the pinned correction δ(n,m)→b(m). **Run
  under PyPy** for the heavy columns (m=3 at deck scale is ~n⁶ states):
  `PYTHONPATH=…/src /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_exact_dp.py 52 1,2,3`
- `gt_approx_dp.py [n_deck] [m1,..] [cap_M]` — E38, the run-length-MULTISET DP:
  the #descents-vs-multiset contrast (the pivot), the bias grid vs `exact_e_dp`,
  the deck-scale MC gate, and the fast deterministic deck-scale deliverable. **Run
  under PyPy** (the m=5 full multiset at n=52 is ~3.6e6 states, ~2.5 min):
  `PYTHONPATH=…/src /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_approx_dp.py 52 1,2,3,5,10`
- `gt_rational_dp.py [m1,..] [n_hi]` — E39+E40, the exact-RATIONAL DP: gates (rational
  == enumeration EXACTLY), the exact δ(n,m) sequence → Berlekamp–Massey minimal
  recurrence → exact factorization over ℚ (the operator spectrum) → exact b(m) via
  the generating-function limit + a MATCH check against the E40 closed form;
  self-validating (no numpy). m=5,6 enabled (defaults, n_lo=2). **PyPy** to reach m≥4
  (exact arithmetic, ~(2m)ⁿ denominators; m=6 to n=24 ~30 min):
  `PYTHONPATH=…/src /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_rational_dp.py 4,5,6`
- `gt_bm_closed_form.py` — E40, the CLOSED FORM for the intercept: verifies
  b(m)=3/2−1/(4m)−H_{2m}^{(2)} against the exact b(1..6) and runs the exact-rational
  subset search that finds it as the UNIQUE ≤3-feature fit (asserts uniqueness). Fast,
  CPython: `PYTHONPATH=…/src uv run python data/gt_bm_closed_form.py`
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
