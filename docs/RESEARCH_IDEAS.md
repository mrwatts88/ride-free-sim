# Breakthrough-idea backlog (beyond gambling)

Opened 2026-07-20. Matt asked for a research session to find interesting
problems / possible breakthroughs — "we don't even have to be in the world of
gambling anymore." A 3-agent research pass (fully sourced) produced this menu.
**Matt picked Theme A / thread 1A first** (the shelf-guessing theorem — now
`docs/GUESSING_THEOREM.md`, an active result). This doc parks EVERYTHING ELSE so
we can return to any of it cold.

**The through-line** (Matt's criterion): reuse the project's two real moats —
(i) exact enumeration / exact posteriors, and (ii) synthetic-ground-truth gating
+ dollar/effect-size honesty — pointed at places they haven't been pointed.
"Beating the implementation of randomness" is the recurring thesis.

**Legend:** ✅ pursued · ⏸ parked (ready to resume) · 💤 side-note / low-priority.
Ratings are the research agents' honest calls; VERIFIED/REPORTED/LORE mark claim
confidence. Each idea carries a *cheapest first probe* so a cold session can act.

---

## Theme A — reuse the exact shuffle-posterior machinery for a MATH result

Purest reuse of our most unique, already-gated asset (the exact next-card
posterior + optimal-guessing value + information-channel measurement). We already
verified DFH's conjecture once (E27); this theme is "do it again, bigger."

### 1A — Multi-shelf optimal card-guessing ✅ PURSUED → `docs/GUESSING_THEOREM.md`
The `m≥2` complete-feedback problem; engages Clay 2025 Conjecture 3. Strong
evidence banked. See that doc. (Left here as the anchor of the theme.)

### 1B — Optimal feedback guessing after k≥2 RIFFLE (GSR) shuffles ⏸ [STRONG]
- **Open question:** the optimal complete-feedback strategy + expected reward
  after an *arbitrary* number `k` of GSR riffle shuffles.
- **Known/open:** **Bayer–Diaconis (1992, "Trailing the Dovetail Shuffle to its
  Lair") posed this as an open problem.** **Liu (2019) solved only `k=1`**
  (optimal strategy; reward `n/2 + √(2/π)·√n + O(1)`), arXiv:1908.07718,
  "partially solving an open problem of Bayer and Diaconis." **`k≥2` remains
  open.** Adjacent: moments arXiv:2107.11142; Ottolini–Steinerberger
  arXiv:2211.09094.
- **Our moat:** `k` successive GSR riffles = one `a`-shuffle with `a=2^k`
  (Bayer–Diaconis), closed-form order law → our exact posterior is analytically
  tractable for any `n`, while the optimal `k≥2` strategy is unknown. `forensics.py`
  already has the exact riffle class laws (`riffle_class_prob`, `eulerian_counts`,
  `riffle_distances`); the one missing piece is a **`RifflePosterior`** mirroring
  `ShelfPosterior` (the forward GSR riffle is not a label-sort, but its *inverse*
  is — a known, easy cut-conditioned construction).
- **Cheapest probe:** build `RifflePosterior`; compute exact optimal `E(n,k)` for
  small `n`, `k=2,3` (`a=4,8`); conjecture how Liu's `√n` term generalizes (does
  the `√(2/π)` coefficient scale as `√(a−1)/a`?); check the argmax vs Liu's
  `k=1` zig-zag pattern. (This is the same playbook that worked for 1A.)
- **Rating:** Novelty **High** (30-year-old *named* problem), Difficulty
  **Moderate–High**, Competition **Moderate** (the Clay/Kuba/Tripathi cluster
  could pivot here). VERIFIED open.

### 1C — The guessing-metric mixing cutoff ⏸ [MODERATE, good "second paper"]
- **Open question:** how many passes until the *guessing advantage* (not TV
  distance) vanishes — the operationally-correct "is this shuffle safe?" statistic.
- **Known/open:** the three metrics disagree (52 cards: TV mixing ≈ 7 riffles,
  separation ≈ 11). TV cutoff for the shelf shuffle is now **nailed**
  (`5/4·log_{2m} n`, Ottolini et al. arXiv:2410.17345; asymmetric 2606.18039).
  The **guessing-metric** cutoff (sharp constant/window, esp. multi-shelf +
  feedback) is comparatively under-pinned.
- **Our moat:** we compute the exact guessing curve vs pass count where others use
  bounds. Directly relevant to the (now-closed-for-money) live-dealer QC premise.
- **Cheapest probe:** from the exact posterior, plot exact optimal `E(n, passes)`,
  locate the guessing cutoff/window, compare to `5/4·log_{2m} n`.
- **Adjacent freebie:** no-feedback multi-shelf reward = sum of column-maxima of
  the `m`-shelf position matrix; Tripathi did `m=1` (arXiv:2602.07920) — we can
  produce the exact `m=10, n=52` number now.
- **Rating:** Novelty **Moderate**, Difficulty **Low–Moderate**.

### 2 — The Format-Preserving-Encryption bridge 💤 [MODEST — framing transfers, moat doesn't]
Small-domain FPE ciphers ARE card shuffles (Thorp, swap-or-not, Feistel FF1/FF3).
Honest verdict from the research pass: the *mixing-time framing* transfers but our
*label-sort special sauce does NOT* (keyed pseudorandom round functions ≠ a
physically biased mix), and the field is crowded + adaptive-adversary-shaped.
- **2A — exact small-`N` distinguishing advantage of an IDEAL small-domain
  shuffle vs the only-asymptotic proven bounds.** All security proofs are coupling
  UPPER bounds (Hoang–Morris–Rogaway swap-or-not, CRYPTO 2012, arXiv:1208.1176;
  Morris–Rogaway–Stegers Thorp, CRYPTO 2009; Ristenpart–Yilek **Mix-and-Cut**,
  CRYPTO 2013 — *note: "Mix-and-Cut", NOT "Mix&Slice", which is an unrelated
  construction*). An exact small-`N` TV-after-`r`-rounds table is generic
  Markov-chain evolution (feasible to `N≈10–12`), plausibly not done exactly, but
  *any* competent group could do it — our only edge is discipline. Best honest
  use: exact info-theoretic security *ceilings* for the ideal primitive.
- **2B — "guessing under feedback = message-recovery advantage"** — real kinship
  (both are the Bayes-optimal predictor of an unseen value of a non-uniform
  permutation) but routinely overstated; breaks on adversary model (adaptive vs
  fixed reveal), source of non-uniformity (keyed vs physical), objective. Attacks
  for context: Durak–Vaudenay FF3 (eprint 2017/521); Hoang–Tessaro–Trieu "Curse
  of Small Domains" (eprint 2018/556). **Treat as an exposition device, not a
  theorem generator.**

---

## Theme B — renewable structural-EV gambling edges (more on-brand than sports betting)

Reuses our exact-EV enumeration wheelhouse; NO new predictive-modeling machinery.
Honest overall: the *clean arithmetic* fit is known advantage-play territory
(income, not breakthrough); the breakthrough-flavored variants are gated by
capital/logistics or data we don't have. Ranked by fit:

### B1 — Must-hit-by / mystery progressives ⏸ [cleanest wheelhouse fit; renewable income]
- **Mechanism:** a meter with a *known ceiling* must drop before reaching it, so
  per-spin EV rises as the meter climbs — a fresh exact crossover computation per
  machine. Renewable (new titles ship constantly), low capital.
- **Known:** the crossover math is public (Wizard of Odds
  `wizardofodds.com/games/slots/mystery-jackpot`: breakeven `j = m(1−f)/(1−f+r)`
  etc.). **The edge over the crowd:** AGS machines DON'T trigger uniformly (they
  cluster near the ceiling), changing the EV curve — machine-specific trigger
  modeling is where an exact-EV team out-computes casual APs.
- **Cheapest probe:** log each machine's meter / printed ceiling / reset; measure
  rise-rate `r` from meter movement per coin-in; compute crossover. Nearly free.
- **Ceiling:** thin +EV band, competition (outbid/camped at the machine),
  bankroll to play to the ceiling. Legality fine. Novelty **Low** (known AP),
  fit **High**.

### B2 — Roll-down / capped-jackpot parimutuel lotteries (Cash WinFall class) ⏸ [dormant-recurring]
- **Mechanism:** a capped jackpot that "rolls down" into lower parimutuel tiers
  turns tickets +EV *on rolldown draws* — but ONLY when total sales are low vs the
  swollen pool (else self-diluting). The renewable condition to hunt: **rolldown
  pool large relative to the money chasing it.**
- **Known:** Cash WinFall CLOSED (MA IG 2012 — it was *not illegal*; Boston Globe
  2012-07-30; narrative: Fagone, HuffPost Highline "The Lottery Hackers" 2018).
  Class dormant-recurring (UK Lotto "Must Be Won"; some US Cash-5 rolldowns) but
  high liquidity usually kills it (UK rolldown ≈ £1.80 on a £2 ticket).
  Moffitt–Ziemba "trump ticket" analysis: arXiv:1801.02958 & 1801.02959.
- **Split skill:** *discovery* is exact EV (our edge); *harvesting* is
  capital/logistics (buying 100k+ tickets). VERIFIED buying is legal; operators
  redesign/cap when bled.
- **Cheapest probe:** enumerate every game worldwide with **capped jackpot +
  rolldown-to-lower-tiers** (published rules), pull per-draw **sales volume**
  (many states publish it), compute rolldown-draw EV net of dilution — screen for
  the one low-liquidity game that flips positive. A weekend of arithmetic over
  public rule sheets; no capital to *find* it.

### B3 — Guaranteed-jackpot bulk-buy (Texas 2023 "Rook TX") 💤 [capital play, NOT our edge]
- **Mechanism:** when after-tax lump sum > cost of buying every combination, cover
  the whole space. Arithmetic is a **one-line comparison**; the moat is
  capital + terminal throughput + regulatory access. Largely killed by regulation
  (TX SB 3070, 2025; couriers legal only NJ/NY). Flag to Matt as a financier play,
  not an arithmetic edge.

### B4 — Scratch-off printing leaks (Srivastava) 💤 [thesis-aligned but weakest]
- **Mechanism:** *visible* printed numbers leaked the *hidden* result (Ontario
  tic-tac-toe, ~2003; Wired 2011 "Cracking the Scratch Lottery Code"). Canonical
  vector CLOSED; no public method for a *new* game — each is empirical
  reverse-engineering with likely-null payoff. Insider-RNG fraud (Eddie Tipton,
  Hot Lotto) is VERIFIED to recur but needs insider access = cheating.
- **Honest sub-play:** the public **"remaining top prizes" screen** (states
  publish remaining prizes per game; buy only from games with favorable
  remaining-prize-to-remaining-ticket ratio) — pure arithmetic on public data, no
  hidden-info crack.

---

## Theme C — forensic statistics: "is it really random?" pointed at NON-gambling targets

The project's thesis aimed outside gambling. Moat: synthetic-ground-truth gating
+ exact null distributions, in fields full of *contested heuristic debunkings*.
The unifying tool is a **bias-aware replay harness**: plant the null → compute the
EXACT finite-sample expectation of the estimator the authors used → confirm
recovery on a planted effect → report bias-corrected estimate + permutation
p-value, IS/OOS separated.

### C1 — Dunning–Kruger as a statistical artifact ⏸ [BEST OPEN TARGET]
- **Claim:** the unskilled dramatically overestimate ability (the iconic crossing
  "scissors" graph).
- **Suspected artifact:** regression-to-the-mean (imperfect self-assessment) +
  better-than-average + **autocorrelation** (the classic plot regresses
  `perceived − actual` on `actual`) reproduce the scissors from pure noise.
- **Why open:** Nuhfer et al. reproduce the graph from random numbers; Gignac &
  Zajenkowski (2020, *Intelligence*; PDF gwern.net/doc/iq/2020-gignac.pdf) find a
  modest *linear* relation, not the DK shape — but a published Comment (Hiller)
  and Gelman contest the framing. **Nobody has adjudicated HOW MUCH is artifact
  with planted ground truth.** Public data.
- **Cheapest probe (our exact playbook):** simulate individuals with a *known*
  miscalibration function (incl. the zero-DK null), run BOTH the original
  quartile-plot estimator and the Gignac–Zajenkowski linear estimator, report what
  each recovers vs truth. Novelty **High** (famous, non-gambling, legible),
  Difficulty **Low–Moderate**. CONTESTED/OPEN.

### C2 — Miller–Sanjurjo re-sweep of streak / clutch / sequential-decision analyses ⏸
- **Template:** Miller & Sanjurjo (2018, *Econometrica*; arXiv:1902.01265)
  overturned the "hot-hand fallacy" via a subtle finite-sample selection bias.
- **Live sub-targets (public data):** (a) **"clutch hitting doesn't exist"** —
  the debunking may just be *underpowered* (Bill James, "Underestimating the Fog,"
  2004, sabr.org; Cramer 1977); Retrosheet play-by-play is public → plant a known
  clutch-variance component, measure detection power, and M-S-correct streak
  splits. (b) **Penalty-shootout first-kicker advantage** — Apesteguia &
  Palacios-Huerta (AER 2010, ~60.5%) vs Kocher et al. (Mgmt Sci 2012, null) vs
  large recent nulls; a permutation test on the full public database is cheap and
  near-decisive.
- **Study designs most exposed to the M-S bias** (rank-ordered): after-a-run-of-k
  measurements; clutch/high-leverage splits; short-series autocorrelation /
  mean-reversion (also **Stambaugh bias**, JFE 1999); event studies conditioning
  on an extreme then measuring the next window; sequential expert-decision
  "alternation" studies.

### C3 — Distributional forensics for research fraud ⏸ [HIGHEST real-world IMPACT]
- **Idea:** detect fabricated data via distributional tells — the purest "is this
  data actually random/real?" question, dead-center our thesis.
- **Prior art (crude, contested):** Carlisle's baseline-covariate test
  (Anaesthesia 2017; screened 5087 RCTs; caught Yoshitaka Fujii — record 183
  retractions — and Boldt); **GRIM** (Brown & Heathers 2017 — means of integer
  data must be granularity-consistent); **SPRITE**; Benford forensics.
- **Our moat:** these detectors are heuristic and much-debated; bringing **exact
  null distributions + synthetic planted-fabrication power analysis** ("how much
  power does Carlisle's test actually have against a smart fabricator?") is exactly
  our discipline and an open methodological question. Public corpus (published
  papers), renewable, compounding.

### C4 — Auditing institutional / physical randomizations ⏸ [class-6 at civic scale]
- **Idea:** wherever an institution runs a physical/pseudo-random allocation and
  publishes outcomes, audit whether it's actually uniform.
- **Canonical precedent:** the **1969 Vietnam draft lottery** was non-random
  (insufficient mixing by month → later birthdays drafted earlier; Fienberg,
  *Science* 1971) — the textbook "physical randomization failed, statistics caught
  it." Live candidates: DV/green-card lottery (a 2011 computer glitch voided
  results — State Dept admitted), H-1B lottery (USCIS found multiple-registration
  fraud), jury-venire randomization (real legal challenges). Renewable, public,
  socially meaningful; moat = the synthetic-gate discipline. Risk: well-run draws
  (UK Premium Bonds/ERNIE) are audited; getting clean current per-draw data.

---

## Documented "reversal" calibration set (Theme C reference — what the genre looks like)

Canonical results overturned/shrunk by a subtle bias (primary cites, for pattern
calibration): hot hand (Miller–Sanjurjo 2018); candidate genes / 5-HTTLPR
(Border et al., AJP 2019 — winner's curse); the finance "factor zoo"
(Harvey–Liu–Zhu, RFS 2016; Hou–Xue–Zhang 2020 — multiple testing); long-horizon
mean-reversion (Stambaugh, JFE 1999 — persistent-regressor small-sample bias);
mutual-fund persistence / survivorship (Carhart 1997; Brown–Goetzmann–Ross 1995);
Berkeley admissions "sex bias" (Bickel et al., *Science* 1975 — Simpson); Will
Rogers / cancer stage migration (Feinstein et al., NEJM 1985); low-birth-weight
"paradox" (Wilcox 2001 — collider); ego depletion (Carter et al. 2015 — small
study bias). Skeptic's note: several *debunkings* here are themselves contested —
treat each as another claim to gate against synthetic ground truth.

---

## How to pick a next one (my read at parking time)

- **Highest breakthrough-per-effort, reuses live code:** Theme A **1B** (the
  standing Bayer–Diaconis riffle problem) — same playbook as 1A, one new
  `RifflePosterior`.
- **Best non-gambling swing, most legible:** Theme C **C1** (Dunning–Kruger).
- **Highest societal impact:** Theme C **C3** (research-fraud forensics).
- **Most likely to actually make money (but low novelty):** Theme B **B1**
  (must-hit progressives) or the **B2** rolldown screen.

Related: `docs/GUESSING_THEOREM.md` (the pursued thread),
`memory/shuffle-guessing-theorem.md`, `docs/PARADIGM2.md` (the taxonomy this all
extends — classes 2/5/6).
