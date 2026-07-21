# Cover email to Alexander Clay (draft)

**To:** ajclay@usc.edu
**Subject:** An exact intercept for your Conjecture 3 (m-shelf card guessing)

---

Dear Professor Clay,

I'm an independent researcher who arrived at shelf-shuffle card guessing sideways — through
a deterministic blackjack/shuffle simulator I'd been building — and your 2025 paper
*Guessing Strategies for Shelf-Shuffling Machines* framed a problem I couldn't put down. I
believe I have a proof of the **value half of your Conjecture 3 for general m**, and I'd
value your read before doing anything further with it.

Briefly: for the m-shelf shuffle with complete feedback, the expected score of the
Diaconis–Fulman–Holmes strategy G is

  F_G(n, m) = (H₂ₘ / 2m)·n + [ 3/2 − 1/(4m) − H₂ₘ⁽²⁾ ] + O((1 − 1/m)ⁿ).

The leading term is your conjectured (n/2m)·H₂ₘ; beyond it I get the **exact constant term**
(limit 3/2 − π²/6 ≈ −0.145) and the **geometric fade rate 1 − 1/m**. The argument is
elementary and probabilistic — it recasts the shuffle as 2m blocks of independent
uniform-label cards, extracts one exchangeability lemma, and sums a per-position hit
probability over the deck. Notably it **never forms the "m-shelf transition matrix" you
identified as the open obstruction.** At m = 1 it reduces to your 3n/4 (Theorem 1.5).

Two things I want to be upfront about:

1. **What I prove is the value of G, not that G is optimal.** I verify E_opt = F_G *exactly*
   for all n ≤ 9, m ≤ 10, and to within 0.01 at deck scale through m = 40, and G is the
   posterior-maximizing guess *conditional on the true block-parse* — but general optimality
   of G stays, as in your paper, a conjecture. The value expansion itself doesn't depend on
   it.

2. **This work was done with substantial AI assistance** (Anthropic's Claude). Every identity
   in the paper is independently machine-verified by exact-arithmetic enumeration. I mention
   it up front because it's unusual and I'd rather be transparent than not.

The 9-page draft is attached. I'd be grateful for any reaction — whether the argument holds,
whether it's worth developing toward publication, and whether the direction is of any
interest to you. Thank you for the paper that started this.

Best regards,
Matt Watts
matt.ryan.watts@gmail.com

---

### Notes for us (not part of the email)
- Attach `main.pdf`.
- Tone: outreach, not submission. Authorship/venue deliberately undecided pending his reply
  (see docs/GUESSING_THEOREM.md §WRITE-UP & OUTREACH PLAN). If he's interested, a Clay
  co-authorship / arXiv endorsement is the best outcome.
- If he asks for the verification code: the probes are `data/gt_*.py` and the test pins in
  `tests/test_guessing_theorem.py` in the simulator repo; we can package a minimal standalone
  script (block-model enumeration + the four-bin decomposition) if useful.
