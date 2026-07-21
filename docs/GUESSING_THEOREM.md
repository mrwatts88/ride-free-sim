# The shelf-guessing theorem — read this first for the card-guessing math thread

> ## ▶ NEXT SESSION — START HERE (updated 2026-07-20)
>
> **CURRENT: E35 + follow-ups A/B + E36 + E37 + E38 + E39 + E40 + E41 + E42 + E43 + E44 all
> DONE; tests green** (routine fast run; heavy MC/DP gates are `slow`-marked, skipped by
> default). **▶▶ THE VALUE HALF OF CLAY'S CONJECTURE 3 IS NOW A THEOREM FOR ALL m** — slope
> (E41) + fade rate (E42) + exact intercept (E44), all by the direct block decomposition.
>
> **▶ CORRECTION (2026-07-20, post-review) — the fade REMAINDER carries an n² prefactor; the
> value-law one-liner is imprecise as usually written.** Many places write `E_opt =
> (H₂ₘ/2m)n + b(m) + O((1−1/m)ⁿ)`, but the correct remainder is **`O(n²(1−1/m)ⁿ)`**
> (equivalently `Θ(n²(1−1/m)ⁿ)` for m≥2; exactly 0 at m=1). The `n²` is the Jordan prefactor of
> the **multiplicity-3** subdominant eigenvalue `1−1/m` that E39 ALREADY established (`(x−i/m)³`
> in the char poly) and E42's GATE 3 noted ("m=2 mult-3 n² prefactor") — it was dropped when the
> one-liner was first written (E40) and then propagated through the docs and into the paper's
> first draft. VERIFIED 2026-07-20 (`data/` scratch): for m=2, `R(n)·2ⁿ = (E_opt−c·n−b)·2ⁿ` is an
> exact degree-2 polynomial (2nd finite difference → −1/4, 3rd → 0), so `R(n) ≈ −(1/8)n²(1/2)ⁿ`.
> The exponential **rate `1−1/m` was always correct**; only the polynomial prefactor was missing,
> and this does NOT affect the slope or the intercept `b(m)` (both re-verified correct). The
> paper `docs/paper/main.tex` is FIXED (Prop 6 now `Θ(n²(1−1/m)ⁿ)` with the mult-3 explanation;
> §8 states the multiplicity) and the Clay email is fixed. **When writing the value law, use
> `O(n²(1−1/m)ⁿ)`.** Caught by an independent proof-review agent + Matt — a good catch on a
> self-inconsistency (the one-liner contradicted our own E39 spectrum).
>
> **▶▶ E44 (2026-07-20) — THE PROOF IS COMPLETE: `S_excess(m)` in CLOSED FORM ⟹ the exact
> intercept `b(m) = 3/2 − 1/(4m) − H₂ₘ⁽²⁾` is PROVEN for all m.** E43's remaining sum
> `S_excess = Σ_t E[hit_t − 1/(2m−ℓ_t)]` is derived from the block model to equal
> `5/2 − 3/(4m) − H₂ₘ⁽²⁾` (its E40 target), closing `b(m) = −1 + 1/(2m) + S_excess`.
> **CORRECTION banked (E43's `hit_probability` is PARSE-CONDITIONAL):** the block label ℓ is
> HIDDEN, so a parity/parse strategy is NOT realizable (it scores ABOVE `E_opt` — 3.32 > 3.17
> at m=2,n=6). The optimal, realizable strategy is DFH-G = **continue the last OBSERVED step's
> direction**; `hit_probability(ℓ,A,B)` only applies where DFH-G's direction matches parity.
> **THE DECOMPOSITION:** bin each guess by on-foot/off-foot (does DFH-G's direction match ℓ's
> parity? off-foot = a block-first card entered against its monotone order ⟹ DFH-G guesses the
> wrong side ⟹ a.s. MISS) × Cont/Empty (is the DFH-G side non-empty?). **Only `onC` is O(n)**;
> the other three are O(1) boundary effects. Exact limits (all from label exchangeability):
> `onC = (H₂ₘ−1)/2` (only E43's `d=1` term survives the (A,B)-binomial sum, telescoping to
> `1/(2r)` per block); `offC = 1 − 1/(4m) − H₂ₘ/2` (off-foot-with-live-continuation rate
> `½ − 1/(2m+1−ℓ)`, hit 0); `onE = 2 − 1/(2m) − H₂ₘ⁽²⁾` (peak prob `1/(2m−ℓ)` × flip-hit
> `1/(2m−ℓ−1)`, `Σ_{r=2}^{2m}(1/(r(r−1))−1/r²)`); `offE → 0`. **Sum = `5/2 − 3/(4m) −
> H₂ₘ⁽²⁾` EXACTLY**, matching E40's independently-established `b(m)` for m=1..8 (GATE A). GATE C
> pins the two exchangeability identities EXACTLY by enumeration; GATE B shows the block-model
> bins trending to the limits (slow `(1−1/2m)ⁿ` tail). m=1: `¼ + 0 + ¼ = ½ ⟹ b(1)=0` (Clay
> Thm 1.5). Core `data/gt_s_excess.py`, 2 new pins, 350 green. **▶ THE PROOF ROAD IS DONE** —
> the remaining work is WRITE-UP/outreach (standalone article; Clay/USC hook ajclay@usc.edu),
> not new math. Adjacent open item unchanged from E38: the richer approximate statistic for
> m=10's −0.085 residual (unrelated to the proof).
>
> **▶ CLAIM BOUNDARY — what we can honestly claim (read before drafting the paper / Clay
> email; Matt + I settled this 2026-07-20).** Clay's Conjecture 3 bundles TWO separate claims
> for an m-shelf shuffle (m ≥ 2); he PROVED both only at m=1; DFH first proposed G in 2013.
> - **(VALUE half) — PROVEN by us, exactly, for all m.** The score formula. We derive the value
>   `E_opt(n,m) = (H₂ₘ/2m)·n + [3/2 − 1/(4m) − H₂ₘ⁽²⁾] + O((1−1/m)ⁿ)` — slope (E41) + fade (E42)
>   + exact intercept (E44) — from the block model, sharper than Clay's leading-term-only `≈`.
>   This is the genuinely OPEN, hard part (the "m-shelf transition matrix" obstacle). It is
>   airtight and does **not** depend on the strategy half: we compute the *realizable* DFH-G
>   strategy's value (= Clay's `F_G` object) directly. (Greedy Bayes-with-feedback is provably
>   the true optimum — guesses can't change the reveals — so where we can compute, `V_G ==
>   E_opt` exactly, i.e. the formula is simultaneously G's value and the optimum's.)
> - **(STRATEGY half — G is optimal) — VERIFIED, not closed-form-proven for all m.** We have:
>   exact equality `E_opt == E_G` (gap 0 as fractions) on the whole grid n ≤ 9, m ≤ 10 (E35);
>   deck-scale agreement to ±0.01 out to m = 40 (Follow-up B); and the E41 Lemma showing G is
>   exactly the *parse-conditional* optimum. That is strong, but it is a finite grid + a
>   deck-scale numeric check, NOT a single theorem "G optimal for every (n,m)." Clay didn't have
>   that either (m=1 only). We cannot rule out by proof a sub-0.01 constant-level suboptimality
>   of G beyond our computational reach for large m — we saw zero sign of it anywhere.
> - **The "high-probability G-optimality" wording.** Clay phrases the strategy half as "G optimal
>   in a high-probability sense, for n/m not too small" — a hedged asymptotic. We address it with
>   exact-grid + deck-scale EXPECTED-VALUE checks (arguably stronger where computable), NOT a
>   matching high-probability asymptotic theorem. This is a caveat about matching his exact
>   *wording of the strategy half*; it does NOT touch the value-half result.
> - **How to state it (paper + email):** claim the VALUE formula exactly for all m (with the
>   intercept + fade rate he never stated) as the theorem; present G-optimality as verified
>   exactly on a large grid and numerically to m=40 — a strongly-supported conjecture in full
>   generality, not a closed-form theorem. Do not overstate the second half.
>
> **▶ WRITE-UP & OUTREACH PLAN (Matt, 2026-07-20; tracked as Tasks #1/#2).**
> - **Paper 1 — the focused theorem paper. DRAFTED 2026-07-20 → `docs/paper/`.** `main.tex` →
>   `main.pdf` (9 pp, compiles with `tectonic`, which is now installed via brew; `poppler` too,
>   for PDF rendering). Self-contained: block model + Key Lemma + slope/fade/intercept proof +
>   exact-grid & deck-scale G-optimality verification + the CLAIM BOUNDARY above. Simulator
>   origin = one-line ack. SEPARATE cover email `docs/paper/clay_email.md` (outreach framing,
>   honest AI + claim-boundary disclosure) points at the PDF, does NOT contain the proof.
>   **Matt will send the email to Clay himself.** Author line "Matt Watts (independent)",
>   authorship/venue still open pending Clay's reply.
>   - **⚠ REFEREE-READINESS caveat (banked for later, Matt's ask):** the paper presents the
>     intercept proof (§6) at *preprint* rigor — the arguments are complete and every identity
>     is machine-verified (350 exact gates), but the limit-exchange steps ("vanishes as
>     n→∞ / only d=1 survives" in §6.3; "O(1) distinguished cards, conditioning on all blocks
>     nonempty is exact in the limit" in §6.4–6.6; "offE → 0") are *stated* rather than fully
>     ε-managed. These are standard, but a journal referee will push on them. If the outreach
>     goes toward publication, EXPAND those steps into rigorous limit arguments (dominated
>     convergence / explicit geometric tail bounds tied to the O((1−1/m)ⁿ) fade). Not needed for
>     the Clay outreach draft; needed before formal submission.
> - **Paper 2 — the whole-story write-up. BANKED for a future session (Matt: "probably won't go
>   anywhere, but a bigger one with the whole story because we learned a lot of shit on the
>   way… probably just for us").** The broader informal account: the feedback-operator SPECTRUM
>   (E39), the sufficiency/complexity result (E36) + exact run-composition DP (E37) + run-length
>   -multiset approximate DP (E38), the TWO independent proof routes agreeing (block decomposition
>   vs operator spectrum), the DFH-conjecture verification (E27/E35), and the discover-then-prove
>   workflow. Not needed for the Clay result.
> - **Authorship / venue — DELIBERATELY OPEN, START WITH CLAY OUTREACH (Matt's call).** Matt is
>   not a stats PhD and is unsure how AI-assisted work is received at formal venues, so we do NOT
>   commit to authorship/arXiv/journal up front. Frame Paper 1 as OUTREACH to Clay first — "a
>   result we worked out on your Conjecture 3, would value your read" — disclosing AI assistance
>   honestly (it's a plus, not a liability, and math is checkable regardless of how it was found).
>   Clay (who posed the conjecture, is at USC, posts on arXiv) can sanity-check the proof, advise
>   on publishing, and could co-author / endorse — which would cleanly resolve credentials, arXiv
>   endorsement, and venue. Decide authorship/submission AFTER his response, not before.
>
> **▶▶ E43 (2026-07-20) — the EXACT PER-POSITION HIT LAW → the value law becomes ONE explicit
> sum, and the intercept mechanism is pinned (correcting E42's "transition-sum" framing).**
> At any guess whose run's last card is in block ℓ, with A undealt on the CONTINUATION side
> (incl. the guess target w₁) and B opposite, the E41 Lemma gives P(next=w₁) EXACTLY (GATE 1,
> verified vs enumeration for every (prefix,parse,dir) group, asc+desc): with r=2m−ℓ, d=j−ℓ,
> **P = (1/r)Σ_{d=0}^{r−1}(1−(d+(d mod 2))/r)^(A−1)·(1−(d−(d mod 2))/(r−1))^B** — unified
> asc/desc by d-parity (the naive ℓ→2m−1−ℓ mirror FAILS). The d=0 term is 1 for all A,B ⟹
> bulk limit 1/(2m−ℓ) (the Lemma rate = the slope); d≥1 = the finite-size EXCESS (d=1 =
> (1/r)(1−2/r)^(A−1) = the H₂ₘ⁽²⁾ generator). **THE VALUE LAW IS THIS SUMMED:** the
> pure-continuation strategy (guess w₁ every step, first=1) is OPTIMAL — **V_cont==E_opt
> EXACTLY** at every (n,m) (independent re-confirm of E35), so E_opt=Σ_t E[hit_probability(
> ℓ_t,A_t,B_t)]. **INTERCEPT REDUCED:** bulk reference Σ_p 1/(2m−ℓ(o_{p−1}))→(H₂ₘ/2m)n−1 (last
> card carries no follow-up guess), first guess→1/(2m), so **b(m)=−1+1/(2m)+S_excess(m)** with
> **S_excess(m)=Σ_t E[hit_t−1/(2m−ℓ_t)]=5/2−3/(4m)−H₂ₘ⁽²⁾** (closed-form target from E40; GATE 4
> confirms → 0.70139 at m=2, 0.75861 at m=3). **CORRECTION to E42:** the intercept is NOT the
> 2m−1 transition guesses — it is the finite-size excess hit−1/(2m−ℓ) summed over the WHOLE
> deck (dominated by value-range extremes where A or B is small). **▶ ONE REMAINING STEP:**
> evaluate S_excess in closed form → 5/2−3/(4m)−H₂ₘ⁽²⁾, finishing b(m) and the full value law.
> Core `guessing_theorem.hit_probability`, probe `data/gt_hit_formula.py`, 4 pins, 348 green.
>
> **▶▶ E42 (2026-07-20) — PHASE 2 TAIL: the FADE RATE `O((1−1/m)ⁿ)` is now PROVEN from the
> blocks for ALL m, and the INTERCEPT b(m) is decomposed (two pieces derived).** The FADE:
> for a block-0 ascending contiguous prefix (1..k), conditioning on the last card's true
> block ℓ=L_k, every undealt card survives (key>key(last)) INDEPENDENTLY with prob
> ρ_ℓ=(2m−ℓ)/2m (even ℓ) / (2m−1−ℓ)/2m (odd ℓ), so `P(prefix,L_k=ℓ)=K_ℓ·ρ_ℓ^(n−k)` EXACTLY
> (K_ℓ n-independent — GATE 1, enumeration). The observer's excess over 1/(2m) is carried by
> the competing labels ℓ≠0, whose posterior weight decays like (ρ_ℓ/ρ_0)ⁿ; the DOMINANT is
> ℓ∈{1,2}, both at ρ_ℓ/ρ_0=(2m−2)/2m=**1−1/m** — this is "the factor of 2 in the exponent"
> (a same-direction block SKIP ℓ→ℓ+2, not the intervening-empty (1−1/2m)). So excess is
> Θ((1−1/m)ⁿ) (GATE 2) and δ(n,m)−b(m)=O((1−1/m)ⁿ) (GATE 3): **the dominant subdominant
> eigenvalue is EXACTLY 1−1/m for all m** — a PROOF of what E39 confirmed to m≤6 by
> Berlekamp–Massey, via an independent route (the block survival law, not the operator).
> The INTERCEPT: bin guesses by the true block parse — interior guesses of block ℓ number
> |B_ℓ|−1 and each hit 1/(2m−ℓ) (Lemma), so their sum is (H₂ₘ/2m)n−H₂ₘ ⟹ **interior
> undercount = −H₂ₘ (DERIVED)**; the first guess → **1/(2m) (DERIVED)** (o₁=1 iff L₁=0). The
> rest is one boundary constant B(m)=b(m)+H₂ₘ=3/2−1/(4m)+H₂ₘ−H₂ₘ⁽²⁾ (the 2m−1 transition
> guesses + first + interior parse-mixing excess), MEASURED to match (GATE 4). m=1 warm-up:
> H₂=3/2, no fade, first=1/2 ⟹ b(1)=−3/2+3/2=0 (Clay Thm 1.5, 3n/4). **▶ THE ONE REMAINING
> STEP:** derive the TRANSITION-guess sum (2m−1 peak/valley guesses) in closed form — that
> collapses B(m) and finishes b(m). A single explicit O(1) sum, not "find the eigenvectors."
> Probe `data/gt_fade_intercept.py`; 3 new pins; write-up EXPERIMENTS E42; 344 green.
>
> **▶▶ E41 (2026-07-20) — PHASE 2 BREAKTHROUGH: the SLOPE c(m) = H₂ₘ/(2m) is now PROVEN
> for ALL m — the open, hard half of Clay's Conjecture 3. See §THE SLOPE PROOF below for
> the full argument.** A DIRECT block-decomposition proof that bypasses the "m-shelf
> transition matrix" obstacle Clay flagged as open. Three ingredients, all gated
> (`data/gt_slope_proof.py`): (i) the **2m-block model** — each card draws an i.i.d.
> uniform label ℓ∈{0..2m−1}; output = 2m monotone blocks `B₀↑B₁↓…` concatenated; (ii)
> the **label-exchangeability LEMMA** (exact, verified by enumerating all (2m)ⁿ label
> vectors): conditioned on the prefix's true block-parse, the undealt labels are exactly
> independent-uniform on {ℓ..2m−1} (values > v) / {ℓ+1..2m−1} (values < v), so the
> optimal hit is EXACTLY **1/(2m−ℓ)** and the MAP guess is `v+1` (= DFH's G); (iii) each
> block holds a fraction 1/(2m) of the deck and the non-interior steps are O(1), so
> `E_opt = Σ_ℓ (1/(2m−ℓ))·(n/2m) + O(1) = (H₂ₘ/2m)n + O(1)`. **H₂ₘ demystified: it is
> Σ_ℓ 1/(2m−ℓ), the average over blocks of 1/(#still-live blocks).** With the strategy
> half already in hand (G optimal to m=40), `E_opt = (H₂ₘ/2m)n + O(1)` is a THEOREM.
> **▶ NEXT STEP (the Phase-2 tail — prove the FULL value law; detailed plan in §THE SLOPE
> PROOF → "▶ NEXT STEP"):** finish what we found — prove BOTH the exact intercept
> **b(m) = 3/2 − 1/(4m) − H₂ₘ⁽²⁾** AND the exact fade rate **O((1−1/m)ⁿ)** (E40 confirmed
> both at m≤6; they're our sharpening beyond Clay). Now a bounded boundary computation, not
> "find the eigenvectors." Two verified leads already in hand: **(fade)** the observer's
> per-step hit excess over 1/(2m−ℓ) decays at rate EXACTLY 1−1/m (confirmed m=2,3,4,5 to
> 4 dp) — so the fade IS the block-0 parse-mixing correction and needs only the dominant
> rate, not the full E39 spectrum; **(intercept)** H₂ₘ⁽²⁾ = Σ_ℓ 1/(2m−ℓ)² is the same 2m
> slots squared (second-order block term), the corrections cancel to 0 at m=1 (b(1)=0, the
> warm-up). CAVEAT: per-block intercepts look scrambled (transitions cross boundaries) —
> sum over the whole deck. The E39 spectrum is now a cross-check, not the route.
>
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
> - **✅ PHASE 2 — THE SLOPE IS PROVEN (E41, 2026-07-20).** The value half's leading
>   term c(m) = H_{2m}/(2m) is now a THEOREM for all m, proved NOT via the operator
>   eigenvectors but by a direct **block-decomposition + label-exchangeability lemma**
>   (§THE SLOPE PROOF; `data/gt_slope_proof.py`). The eigenvector route (find the
>   homogenized transfer operator's unit eigenvector, guess-and-verify a harmonic ansatz)
>   turned out to be unnecessary for the slope — the elementary route reached it first,
>   and demystified H_{2m} = Σ_ℓ 1/(2m−ℓ) as the block-average hit. **▶ REMAINING PHASE-2
>   TAIL:** derive the exact intercept b(m) = 3/2 − 1/(4m) − H_{2m}^{(2)} (E40) by summing
>   the O(1) block-boundary/transition/parse-mixing corrections. H_{2m}^{(2)} = Σ_ℓ
>   1/(2m−ℓ)² is the same 2m slots squared (second-order block term); the corrections
>   cancel to exactly 0 at m=1 (b(1)=0). This is a bounded, concrete computation. The
>   eigenvector/spectrum machinery (E39) remains available as a cross-check or an
>   alternative route to the intercept, but is no longer the required path.
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
> general m ≥ 2)? **REALIZED — the value half is PROVEN (E44 closed the last step).** The
> full chain is now a theorem for all m: the strategy half (G optimal, E35 + Follow-up B),
> the slope `c(m) = H_{2m}/(2m)` (E41), the fade rate `O((1−1/m)^n)` (E42), and the exact
> intercept `b(m) = 3/2 − 1/(4m) − H_{2m}^{(2)}` (E44). So
> `E_opt(n,m) = (H_{2m}/2m)·n + [3/2 − 1/(4m) − H_{2m}^{(2)}] + O((1−1/m)^n)` is established
> — Clay's leading term PLUS the exact intercept and fade rate he never claimed — all by the
> direct block decomposition that bypasses the "m-shelf transition matrix" obstacle Clay named.
> E44's step: reduce `S_excess = Σ_t E[hit_t − 1/(2m−ℓ_t)]` (E43) to four boundary bins under
> the *realizable* DFH-G strategy (correcting E43's parse-conditional `hit_probability`, which
> is not a legal strategy — ℓ is hidden — and overscores `E_opt`); only the on-foot continuation
> bin is O(n), the other three are O(1), and they sum to `5/2 − 3/(4m) − H_{2m}^{(2)}` exactly,
> matching E40's independently-pinned `b(m)` for m=1..8. Two independent derivation routes (the
> block decomposition here; E39's operator spectrum) now agree on the whole value law. Honest
> scope: this proves the VALUE half of Conjecture 3; the "high-probability G-optimality" phrasing
> is covered by the exact G==optimal grid + deck-scale Follow-up B, not a probabilistic large-n
> statement (a minor gap if one insists on Clay's exact wording). What remains is NOT math but
> OUTPUT: the standalone article (leads with the full proof) and the Clay/USC hook
> (ajclay@usc.edu) — a complete, exact resolution of the conjecture's value half is a strong
> collaboration artifact.
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

## THE SLOPE PROOF (E41) — Clay's Conjecture 3 leading term, proven for all m

This is the Phase-2 result: a **rigorous proof that `E_opt(n,m) = (H_{2m}/2m)·n + O(1)`
for every m**, i.e. the slope (the open, hard half of Conjecture 3's value claim) is
`c(m) = H_{2m}/(2m)`. The argument is a direct probabilistic one and never touches the
"m-shelf transition matrix" Clay flagged as the open obstacle. Gated in
`data/gt_slope_proof.py`.

### The 2m-block model (exact restatement of the shuffle)

Label the cards by their initial stack position, `c ∈ {1,…,n}` (so "card c" has value
c). The m-shelf shuffle (DFH Description 1, = `ShelfShuffle`, = the slot geometry in
`ShelfPosterior`) is exactly this: each card `c` independently draws a uniform **label**
`L_c ∈ {0,1,…,2m−1}` (shelf × top/bottom), and the output orders the cards by the key

    κ_c = (L_c, +c)  if L_c even,     κ_c = (L_c, −c)  if L_c odd.

Because the key is lexicographic with the label first, the output is the **2m blocks**
`B_ℓ = {c : L_c = ℓ}` written in order `ℓ = 0,1,…,2m−1`, each block internally sorted by
value — **ascending for even ℓ, descending for odd ℓ**:

    output  =  B_0↑  B_1↓  B_2↑  B_3↓  …  B_{2m−1}↓      (concatenation, not a merge).

So the output is `2m` consecutive monotone runs (a "valley" appears only at each
odd→even block junction, giving ≤ m−1 valleys — the DFH class law). The optimal
complete-feedback value is `E_opt = Σ_{t=1}^n E[h_t]` with `h_t = max_c P(o_t = c |
o_1,…,o_{t−1})` (greedy Bayes is optimal because guesses never affect the reveals).

### The Key Lemma (exact label exchangeability)

> **Lemma.** Fix a dealt prefix `o_1,…,o_s` and *condition on its true block-parse*: its
> maximal monotone runs are the nonempty prefixes of `B_0,…,B_ℓ`, the current (say
> ascending, ℓ even) run ends at `o_s = v`, and blocks `0..ℓ−1` are fully dealt. Then the
> labels of the **undealt** cards are **exactly independent**, with
>
>     L_c ~ Uniform{ℓ,   ℓ+1, …, 2m−1}   for undealt c > v     (2m−ℓ   values),
>     L_c ~ Uniform{ℓ+1, …,     2m−1}     for undealt c < v     (2m−ℓ−1 values).

*Proof.* The label prior is a product measure over cards. Under the fixed parse,
conditioning on "the length-s output prefix is `o_1…o_s`" is the intersection of
per-card events: (i) each dealt card's label equals its parsed block index (forced by
the parse); (ii) each undealt card `c` has key `κ_c > κ_v = (ℓ, v)`, i.e. `L_c > ℓ`, or
`L_c = ℓ ∧ c > v`. A product prior intersected with per-card constraints has a product
posterior, uniform on each card's surviving label set: `{ℓ,…,2m−1}` for `c > v` (label
ℓ survives since `c > v`), and `{ℓ+1,…,2m−1}` for `c < v` (label ℓ would have sorted `c`
before `v`). ∎

**Consequence (the exact hit).** Let `w_1 < w_2 < …` be the undealt values above `v`.
The next output card is the minimum-key undealt card; a card `w_j` is next iff
`L_{w_j} = ℓ` and `L_{w_1},…,L_{w_{j−1}} > ℓ`, so

    P(o_{s+1} = w_j)  =  (1/(2m−ℓ)) · (1 − 1/(2m−ℓ))^{j−1}      (geometric),

maximized at `j = 1`. Hence the **optimal hit is exactly `1/(2m−ℓ)`**, and the MAP guess
is `w_1` = the smallest undealt value above `v` (which is `v+1` whenever `v+1` is
undealt) — *exactly DFH's strategy G*. The descending case is the mirror image (guess
`v−1`, hit `1/(2m−ℓ)`). **GATE 1** in `data/gt_slope_proof.py` verifies the Lemma and the
hit EXACTLY by enumerating all `(2m)ⁿ` label vectors (m=2,n=6: 1382 events; m=3,n=5:
1575), conditioning on each (prefix, parse) and checking independence, uniformity, and
`hit = 1/(2m−ℓ)` as exact fractions.

### Assembling the slope

Call a guess-position *interior* if its prefix has an unambiguous parse and an undealt
value on the continuation side; by the Lemma an interior position in block ℓ has hit
`1/(2m−ℓ)`. The **non-interior** positions are `O(1)` in expectation for fixed m:

- **block transitions** (the first card of each block, a peak or valley): `≤ 2m−1` per
  shuffle;
- **value-range endgame** (an ascending position with nothing undealt above forces `v` =
  the block maximum — a peak, already counted; the descending analogue always has undealt
  values below until the very end and is interior with hit → 1): `O(m)`;
- **parse-ambiguous prefixes** — these require an interior block to be empty (else the
  run structure pins the parse), probability `≤ 2m(1−1/2m)ⁿ` each, so expected count
  `O(n·(1−1/2m)ⁿ) = O(1)`. (This mixing over parses is exactly why the observer's actual
  finite-n hit sits slightly ABOVE `1/(2m−ℓ)`; **GATE 2** shows the excess → 0
  geometrically in exact rationals.)

Each block ℓ therefore supplies `|B_ℓ| − O(1)` interior positions, and `E|B_ℓ| = n/2m`
(uniform labels). Summing:

    E_opt(n,m)  =  Σ_{ℓ=0}^{2m−1} (1/(2m−ℓ)) · (n/2m − O(1))  +  O(1)
                =  (1/2m) Σ_{ℓ=0}^{2m−1} 1/(2m−ℓ) · n  +  O(1)
                =  (H_{2m}/2m) · n  +  O(1).                          ∎

*(Both bounds are rigorous. Lower: the explicit strategy "guess `w_1`" is `w_1`-correct
with probability exactly `1/(2m−ℓ)` per the Lemma, conditional on the true parse, so
`E_opt ≥ E[score] = (H_{2m}/2m)n − O(1)`. Upper: the observer's actual hit
`h_t = max_c Σ_P P(parse=P | prefix)·P(o_t=c | prefix,P) ≤ Σ_P P(P|prefix)·max_c
P(o_t=c|prefix,P) ≤ Σ_P P(P|prefix)·(1/(2m−ℓ_P))`, whose prefix-average collapses by the
tower property to `E[1/(2m−ℓ(t))]` — so parse-mixing, which raises individual hits above
`1/(2m−ℓ)`, cannot raise the SUM above `(H_{2m}/2m)n + O(1)`; the `O(1)` endgame where
`max_c` sits on a below-`v` transition card is bounded separately.)*

**GATE 3** measures the decomposition directly (block-ℓ mean hit → `1/(2m−ℓ)`, occupancy
→ `1/(2m)`, mean hit → `H_{2m}/2m`). At m=1 this is exactly `3n/4` (two blocks, hits
`1/2` and `1` → slope ¾), recovering Clay's proven Thm 1.5 and its "first-descent"
mechanism.

### This proof is COMPLETE-FEEDBACK only (no position-matrix contamination)

Guard against the E39 confusion: this proof uses NOTHING from the no-feedback /
position-matrix world (Tripathi arXiv:2602.07920, `M(i,j)=P(card i→pos j)`, eigenvalues
`{1/4^k}`, single-shelf no-feedback value `√(2n/π)≈5.75`). It rests only on (i) the
2m-block model — the physical shuffle itself, game-agnostic — and (ii) the Key Lemma,
which is *intrinsically* complete-feedback: the hit `1/(#still-live blocks)` exists only
because the observer, having SEEN the revealed prefix, knows which blocks are exhausted.
The decisive check: at m=1 the formula gives `c(1)·52 = 39` = the complete-feedback value
(Clay Thm 1.5, `3n/4`), NOT the no-feedback `√(2·52/π)≈5.75`. A position-matrix leak
would land near 5.75; it lands on 39. Feedback-clean.

### What is proven, and what remains

- **PROVEN (all m):** the slope `c(m) = H_{2m}/(2m)` — the leading term of Conjecture 3,
  open for m ≥ 2, the piece Clay attributed to the open transition matrix. `H_{2m}` is
  literally `Σ_ℓ 1/(2m−ℓ)` = the block-average of `1/(#still-live blocks)`. With the
  strategy half in hand (G optimal to m=40), `E_opt = (H_{2m}/2m)n + O(1)` is a theorem.
- **PROVEN (all m, E42):** the **fade rate** `O((1−1/m)^n)` — the dominant subdominant
  eigenvalue is exactly `1−1/m`, from the block survival law `P(prefix,L_k=ℓ)=K_ℓ·ρ_ℓ^{n−k}`
  (`ρ_ℓ/ρ_0=1−1/m` at the dominant `ℓ∈{1,2}`). Independent of the E39 operator route.
- **EXACT (all m, E43):** the **per-position hit law** `hit_probability(m,ℓ,A,B)` (gated vs
  enumeration), and that the pure-continuation strategy is OPTIMAL — `V_cont = E_opt` exactly
  — so `E_opt(n,m) = Σ_t E[hit_probability(m,ℓ_t,A_t,B_t)]`, one explicit sum. The intercept
  reduces to `b(m) = −1 + 1/(2m) + S_excess(m)`, `S_excess(m) = Σ_t E[hit_t − 1/(2m−ℓ_t)]`,
  closed-form target `5/2 − 3/(4m) − H_{2m}^{(2)}`.
- **PROVEN (all m, E44):** `S_excess(m) = 5/2 − 3/(4m) − H_{2m}^{(2)}`, hence the **exact
  intercept `b(m) = 3/2 − 1/(4m) − H_{2m}^{(2)}`** — the value-law proof is COMPLETE. Under
  the *realizable* DFH-G strategy (`hit_probability` is parse-conditional and NOT a legal
  strategy — ℓ is hidden), the sum splits into four bins: `onC = (H_{2m}−1)/2` (O(n), only the
  `d=1` term survives the (A,B) binomial and telescopes to `1/(2r)` per block), `offC =
  1 − 1/(4m) − H_{2m}/2` (off-foot transition misses), `onE = 2 − 1/(2m) − H_{2m}^{(2)}`
  (peak/valley flips), `offE → 0` — the last three O(1). They sum to the target for all m
  (GATE A, m=1..8); the two exchangeability identities behind `offC`/`onE` are pinned exactly
  by enumeration (GATE C). `data/gt_s_excess.py`. *(E43's "whole-deck finite-size effect"
  framing was right about `onC`; `offC`/`onE` are genuine O(1) boundary effects, so the full
  intercept is `onC's` continuation excess PLUS a finite block-boundary sum.)*

### ▶ NEXT STEP — the value law, remaining piece (fade PROVEN E42; intercept reduced to one explicit sum E43)

Target: prove — from the block picture — that

    E_opt(n,m) = (H_{2m}/2m)·n  +  [ 3/2 − 1/(4m) − H_{2m}^{(2)} ]  +  O((1−1/m)^n),

both the **intercept** and the **fade rate** (E40 confirmed both at m≤6; our sharpening
beyond Clay's leading term). **E42 (2026-07-20) closed the FADE completely and derived two
of the intercept's three pieces:**

- **FADE RATE — PROVEN for all m (E42, `data/gt_fade_intercept.py`).** For a block-0
  ascending *contiguous* prefix `(1..k)`, every undealt card survives (key > key(last))
  INDEPENDENTLY with prob `ρ_ℓ=(2m−ℓ)/2m` (even ℓ) / `(2m−1−ℓ)/2m` (odd ℓ), so
  `P(prefix,L_k=ℓ)=K_ℓ·ρ_ℓ^{n−k}` EXACTLY (K_ℓ n-independent; GATE 1 by enumeration). The
  observer's excess over `1/(2m)` is carried by competing labels `ℓ≠0`, posterior weight
  `∝(ρ_ℓ/ρ_0)^n`; the DOMINANT is `ℓ∈{1,2}`, both at `ρ_ℓ/ρ_0=(2m−2)/2m=1−1/m` — the
  same-direction block SKIP `ℓ→ℓ+2`, **the factor of 2 in the exponent** (not the naive
  `(1−1/2m)`). So excess = `Θ((1−1/m)^n)` and `δ(n,m)−b(m)=O((1−1/m)^n)`: the dominant
  subdominant eigenvalue is EXACTLY `1−1/m` for all m (independent of E39's BM route; E39
  is now a cross-check that matched). **This piece is done.**
- **INTERCEPT — the mechanism is now EXACT (E43); one explicit sum remains.** E42 framed the
  remainder as "derive the `2m−1` transition-guess hits" — that was the **wrong object**. The
  intercept is a **finite-size correction at every position**, not a boundary effect. E43's
  exact per-position hit law (with `r=2m−ℓ`, `d=j−ℓ`)
  ```
  P(next=w₁ | ℓ,A,B) = (1/r) Σ_{d=0}^{r−1} (1−(d+(d mod 2))/r)^{A−1} (1−(d−(d mod 2))/(r−1))^{B}
  ```
  (A = undealt continuation-side supply incl. w₁, B = opposite side) is gated EXACTLY vs
  enumeration for every (prefix,parse,dir) group. Its `d=0` term is 1 (→ bulk `1/(2m−ℓ)` =
  the slope); the `d≥1` terms are the excess. The pure-continuation strategy is optimal
  (`V_cont=E_opt` exactly), so `E_opt = Σ_t E[P(next=w₁)]`, and the intercept splits cleanly:
  ```
  b(m) = −1 + 1/(2m) + S_excess(m),   S_excess(m) = Σ_t E[ hit_t − 1/(2m−ℓ_t) ]
  ```
  (the `−1` = the last card carries no follow-up guess; `1/(2m)` = the first guess). Matching
  E40 gives the closed-form target **`S_excess(m) = 5/2 − 3/(4m) − H_{2m}^{(2)}`**. **▶ THE ONE
  REMAINING STEP: evaluate `S_excess` in closed form** — the `d≥1` excess summed over the deck
  (the `d=1` term `(1/r)(1−2/r)^{A−1}` is the `H_{2m}^{(2)}` generator; it matters only near
  the value-range extremes, where the continuation supply `A` — or `B` — is small). Needs the
  joint law of `(ℓ,A,B)` over guess positions in the block model; a concrete combinatorial sum.
- **WARM-UP — DONE (E42):** m=1: `b(1)=0`, the block decomposition reproduces Clay Thm 1.5.
- The E39 spectrum/eigenvector machinery remains a cross-check (its dominant subdominant
  eigenvalue is exactly the `1−1/m` E42 derives), not the required route.

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
  rational → exact δ(n,m), b(m), and the operator spectrum)**, **`hit_probability(m,ℓ,A,B)`
  (E43 — the exact per-position realized-hit law; bulk → 1/(2m−ℓ), finite-size excess = the
  intercept; `E_opt = Σ_t E[hit_probability]`)**, `mc_e`.

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
- `gt_slope_proof.py [m1,..] [n] [trials]` — E41, the SLOPE PROOF: GATE 1 the Key Lemma by
  enumeration (undealt labels indep-uniform, hit exactly 1/(2m−ℓ)); GATE 2 observer excess
  → 0 geometrically (exact rationals); GATE 3 block-decomposed slope → H_{2m}/2m (MC).
- `gt_fade_intercept.py [m1,..]` — E42, the FADE + INTERCEPT: GATE 1 the survival closed
  form `P(prefix,L_k=ℓ)=K_ℓ·ρ_ℓ^{n−k}` by enumeration (⟹ fade rate 1−1/m at ℓ∈{1,2}); GATE
  2 block-0 excess ratio → 1−1/m (exact-rational posterior); GATE 3 the value-law tail
  δ−b(m) fades at 1−1/m (exact DP); GATE 4 the intercept decomposition b(m)=−H_{2m}+B(m),
  interior undercount −H_{2m} and first guess 1/(2m) derived, boundary B(m) measured (MC,
  seed 24.4e9). **PyPy** for the enumeration + MC:
  `PYTHONPATH=…/src /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_fade_intercept.py 2,3`
- `gt_hit_formula.py [m1,..]` — E43, the EXACT PER-POSITION HIT LAW (core
  `guessing_theorem.hit_probability(m,ℓ,A,B)`): GATE 1 the formula exact vs enumeration for
  every (prefix,parse,dir) group; GATE 2 the bulk limit → 1/(2m−ℓ); GATE 3 the
  pure-continuation strategy is OPTIMAL, `V_cont==E_opt` exactly (⟹ the value law is the
  hit law summed); GATE 4 the intercept reduction `b(m)=−1+1/(2m)+S_excess`,
  `S_excess=5/2−3/(4m)−H_{2m}^{(2)}`. Seedless. **PyPy** for the enumeration:
  `PYTHONPATH=…/src /Users/mattwatts/.local/bin/pypy3.11 -u data/gt_hit_formula.py 2,3`
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
