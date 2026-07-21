# Cover email to Alexander Clay (draft)

**To:** ajclay@usc.edu
**Subject:** A possible proof of your Conjecture 3 (m-shelf card guessing)

---

Dear Professor Clay,

I should be upfront about who's writing: I'm a software developer, not a mathematician —
statistics isn't my field. I build simulators, and one of them (a deterministic model of
casino shelf shuffles) led me into the card-guessing problem your 2025 paper studies. Working
with an AI system (Anthropic's Claude), I've arrived at what appears to be a proof of the
**value half of your Conjecture 3 for general m**, and I'm bringing it to you because you're
the person who can actually judge whether the mathematics is sound.

Here is the claim, followed by an honest account of what I can and can't personally vouch for.

**The result.** For the m-shelf shuffle with complete feedback, the expected score of the
Diaconis–Fulman–Holmes strategy G is

  F_G(n, m) = (H₂ₘ / 2m)·n + [ 3/2 − 1/(4m) − H₂ₘ⁽²⁾ ] + O((1 − 1/m)ⁿ).

The leading term is your conjectured (n/2m)·H₂ₘ; beyond it there is an **exact constant term**
(limit 3/2 − π²/6 ≈ −0.145) and a remainder that **decays at exponential rate 1 − 1/m** (with
a degree-2 polynomial prefactor, from the multiplicity-3 subdominant eigenvalue). At m = 1 it
reduces to your 3n/4 (Theorem 1.5). The argument recasts the shuffle as 2m blocks of independent
uniform-label cards and sums a per-position hit probability over the deck; notably it **never
forms the "m-shelf transition matrix" you identified as the open obstruction.**

**What I *can* stand behind: the computational verification.** Every identity is checked in
exact rational arithmetic by brute-force enumeration, and the intercept is confirmed two
independent ways — an exact-rational dynamic program pins b(m) as exact fractions for m = 1..6
(0, −7/144, −269/3600, …), and the block-decomposition proof sums to those same fractions.

**What I *can't* personally vouch for: the rigor of the analytic proof itself.** The AI
developed the argument; I understand its shape but I'm not equipped to defend, for example,
the limit-exchange steps to a referee's standard. That is precisely why I'm writing to you
rather than posting it anywhere. Two honest caveats travel with the result:

1. What is proved is the value of G, **not** that G is optimal. G-optimality I only *verify* —
   exactly for all n ≤ 9, m ≤ 10, and to within 0.01 at deck scale through m = 40, and G is
   the posterior-maximizing guess conditional on the true block-parse — but in full generality
   it stays, as in your paper, a conjecture. The value expansion doesn't depend on it.
2. The write-up is at draft/preprint rigor: some limit steps in the intercept proof are stated
   rather than fully managed. A referee would push there.

The 9-page draft is attached. I'd genuinely value your read — whether the argument holds,
whether it's worth developing, and if so, how. If the technical back-and-forth needs more than
I can provide directly, I can turn the AI and the verification code back on it. Thank you for
the paper that started this.

Best regards,
Matt Watts
matt.ryan.watts@gmail.com

---

### Notes for us (not part of the email)
- Attach `main.pdf`.
- Framing (revised 2026-07-20): honest about the division of labor — Matt built the simulator,
  directed the investigation, and owns the computational verification (defensible); the AI
  developed the analytic proof (not personally defensible). Front-loaded, not back-loaded.
- Subject line keeps "AI" out (avoids a reflexive "AI slop" delete); the disclosure is the
  first sentence of the body instead.
- Tone: outreach, not submission. Authorship/venue undecided pending his reply
  (see docs/GUESSING_THEOREM.md §WRITE-UP & OUTREACH PLAN). If he's interested, a Clay
  co-authorship / arXiv endorsement is the best outcome.
- If he asks for the verification code: the probes are `data/gt_*.py` and the test pins in
  `tests/test_guessing_theorem.py`; we can package a minimal standalone script (block-model
  enumeration + the four-bin decomposition) if useful.
