# Two Counts on a Scorecard: the Dragon 7 and Panda 8 at EZ Baccarat

*EZ Baccarat's two side bets — the Dragon 7 (banker wins with a three-card
seven, pays 40:1) and the Panda 8 (player wins with a three-card eight, pays
25:1) — carry house edges of 7.6% and 10.2% off the top. Both have been known
to be countable for over a decade, and both were written off as impractical.
This is the full re-derivation with exact methods: the perfect-play ceiling,
optimal counts derived from first principles, a verified playable two-count
system — with a measured proof that it sits at the human frontier of the
game — and a ledger that lands in a very different place than the prior art
did, because the structure of baccarat quietly removes every practical
objection that made the original verdicts negative.*

---

**A note on how this research was done.** Like the two blackjack studies in
this repository ([ARTICLE.md](ARTICLE.md),
[ARTICLE_21P3.md](ARTICLE_21P3.md)), this was a collaboration between the
author and Claude (Anthropic's AI system), which implemented the baccarat
engine, ran the analyses, and drafted this article. Direction was human: the
choice of target, the insistence on validation gates before attack work, and
the standards of evidence. The final claims are the author's to defend, and
every number is reproducible from the repository.

---

## The bets

EZ Baccarat is ordinary baccarat with the banker commission replaced by a
push: when the banker wins with a three-card total of seven, the banker bet
pushes instead of paying. That "barred" hand is also sold as a side bet — the
**Dragon 7**, paying 40:1 on an event with probability 2.2534% (house edge
**7.611%** at eight decks). Its mirror, the **Panda 8**, pays 25:1 when the
*player* wins with a three-card eight: probability 3.4543%, house edge
**10.188%**.

Why are these countable? Because the banker's third-card decision is governed
by a fixed tableau, and the cards that keep the banker *standing* on 7 — the
8s and 9s — are exactly the cards that prevent a three-card seven from
forming. Deal the 8s and 9s away and the Dragon wakes up; the Panda responds
to 9s and the low-middle cards symmetrically. Unlike the 21+3 study in this
repository, no suit information is involved: both bets are pure rank
composition, which makes them *linear-count-shaped* almost all the way down.

And baccarat brings a structural gift blackjack never offers: **the deepest
standard penetration in the house.** The customary cut places the card
14–16 cards from the end of an eight-deck shoe — 96%+ penetration as the
default table condition, not a favor you hope for.

## First, the credibility check

The repository rule: no exotic claim is trusted until the machinery
reproduces boring published facts. The baccarat engine is new code (the
drawing tableau in the engine, everything else — decks, the EZ push,
paytables, shoe handling — immutable rules data), so it faced a fresh gate
ladder, and ended up cross-validating against the published record three
separate times:

- **Exact combinatorics:** a first-principles enumeration over ordered
  six-card sequences must equal Michael Shackleford's Wizard of Odds
  eight-deck combination table integer-for-integer. It does: banker 2,292,252,566,437,888 / player
  2,230,518,282,592,256 / tie 475,627,426,473,216 of 4,998,398,275,503,360,
  and every published edge — classic banker −1.0579%, player −1.2351%, tie
  −14.3596%, EZ banker −1.0183%, Dragon −7.6113%, Panda −10.1876% —
  reproduces to print precision.
- **End-to-end settlement:** 2 × 2M always-bet rounds off freshly shuffled
  shoes: sixteen frequency and edge checks, worst deviation 1.70σ.
- **The published Dragon count, replayed:** Wizard of Odds' practical count
  (below), scored inside our harness at their cut-card depth, produced
  **0.592 ± 0.004 units/shoe against their published 0.597** — agreement to
  under one percent.
- **The published Panda count, replayed:** their appendix-8 system produced
  **0.241 ± 0.011 units/shoe against their published 0.238**, betting 4.60%
  of hands against their 4.61%.

Two codebases agreeing four times across two decades of publication is about
as much external validation as a simulation study can carry. The published
numbers were all correct. What changes below is what they add up to.

## The exact ceiling

Both bets settle on at most six cards, so the exact conditional EV given the
remaining shoe composition is closed form — an enumeration over the tableau,
restructured (via multiset aggregation) to 2.4ms per evaluation and proven
bit-identical to the reference enumeration. True EV, every round, before the
deal; no effects-of-removal approximation anywhere.

Scanning 600k cut-card rounds and betting exactly when the EV is positive:

| penetration | bet | +EV rounds | mean edge | ceiling /100 rounds |
|---|---|---|---|---|
| 0.966 (cut-14, the norm) | Dragon 7 | 11.1% | +7.6% | **+0.87u** |
| 0.966 | Panda 8 | 5.0% | +7.3% | **+0.37u** |
| 0.966 | **both** | ~14% | — | **+1.24u ≈ +1.0u/shoe** |
| 0.95 | both | — | — | +0.98u |
| 0.90 | both | — | — | +0.65u |

For scale: the 21+3 attack this repository just completed — a genuinely
positive verdict — ceilinged at +0.276u/100 at its best realistic
penetration. The Dragon/Panda pair at baccarat's *default* cut is **4.4×
that**, before the structural advantages are counted.

The depth structure echoes every composition bet we've studied: the Dragon
ignites about six and a half decks out and climbs monotonically — 11% of
rounds +EV at three decks remaining, 22% at a deck and a half, 36–40% inside
the last half-deck at mean edges of +12–19%. The Panda sleeps until about
4.5 decks and follows at half the frequency. The two windows only partially
overlap (correlation of the two EVs ≈ +0.41; both positive on ~2.7% of
rounds): the Panda is not a shadow of the Dragon, which becomes the central
fact of the system design.

## The counts, from first principles

Differentiating the exact EV with respect to each rank's count gives the
removal effects — the provably best linear count for each bet:

| card | A | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | T |
|---|---|---|---|---|---|---|---|---|---|---|
| Dragon (×1000) | +0.5 | −0.9 | −1.1 | −2.7 | −2.6 | −3.2 | −3.6 | **+5.4** | **+4.8** | +0.9 |
| Panda (×1000) | +1.3 | +1.4 | −2.9 | −2.5 | −2.7 | −0.9 | −0.9 | −2.2 | **+4.5** | +1.2 |

The Dragon vector ×10 reproduces Wizard of Odds' published "System 1" optimal
tags digit-for-digit — a satisfying closed loop: their simulation-fitted
optimum is our analytic gradient. The Panda vector reproduces the shape of
their appendix tags. Both published counts were near-optimal *linear* counts
all along; what the published record left unclaimed was the thresholds, the
pair, and the economics.

Scored against the exact ceiling on identical shoes (all thresholds derived
analytically from the first-order model — nothing fit to simulation data):

| system | Dragon capture | Panda capture |
|---|---|---|
| exact EV (computer) | 100% | 100% |
| optimal linear tags, analytic threshold | 92.3% | 83.2% |
| **the playable card (below)** | **89.8%** | **79.1%** |
| WoO practical count @ TC≥4 | 86.9% | — |
| WoO appendix count @ TC≥11 | — | 79.1% |
| Panda triggered by the Dragon count | — | **−147%** |

Three findings. First, the linear family is nearly the whole game here —
unlike 21+3's quadratic suit signal, ~90% of this ceiling is reachable with
running counts (and the next section *proves* the rest is out of reach, not
merely unclaimed). Second, the published Panda count is already at the
integer frontier — our sharpened tags tied it (79.1% vs 78.4%), so the
playable system simply adopts the published set for that leg. Third, and
decisively: **the Panda cannot ride the Dragon count.** Triggering Panda
bets when the Dragon count is high loses 4.7% per bet — the correlation
between the two signals is far too weak. Two counts or no Panda.

## How far could any human system go?

Before settling for ~90%, we asked the question 21+3 taught us to ask: is
there a *higher-order* statistic — the analogue of quad-Q's sum of squared
suit excesses — hiding above the linear counts? This is measurable, not a
matter of taste. Differentiating the exact EV twice gives the full
per-depth quadratic model (level, gradient, and the 10×10 Hessian, all
analytic); scoring "bet when the order-k model is positive" against the
exact ceiling on the same shoes:

| model | Dragon 7 | Panda 8 |
|---|---|---|
| linear class (the counts above) | ~90–92% | ~83% |
| + the exact quadratic | 95.3% | 83.6% |
| exact (computer) | 100% | 100% |

For the Dragon, the *entire second order* is worth three to five points —
about +$3/hour at a $100 unit — and the Hessian is a shapeless smear of
cross-products with none of the symmetry that made quad-Q memorizable. For
the Panda the result is starker: the exact quadratic adds essentially
nothing over the best linear count. The missing ~16% of the Panda ceiling
lives in extreme late-shoe compositions where every low-order model fails
at once (honest methods note: the tangent-linear model actually scores
*below* the static count there — Taylor expansions around the balanced shoe
are the wrong tool exactly where the money is, which is itself the
evidence). That residue is deep combinatorics, reachable only by running
the full enumeration: a phone, not a pencil.

So the two-count card is not a practical compromise short of some better
system — **it is the human frontier of this game**, measured. Everything
above it requires a device, and even a full quadratic tracker (55 running
cross-products) would buy under $5/hour.

That would be a real objection at a blackjack table, where counts live in
your head. At baccarat it costs nothing: **scorekeeping on paper is expected
behavior.** Half the table is charting streaks superstitiously; two running
tallies on the same card are invisible.

## The playable card

One hard-won lesson from building it: integer tags rounded from the optimal
values must stay **balanced** — summing to zero across a full deck. The naive
rounding drifted −4 per deck, which silently poisons the true-count
conversion as the shoe depletes (the first verification run caught the
triggers firing 7× too rarely). Balance is now a build-time assertion.
The verified card:

| card | A | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | T/J/Q/K |
|---|---|---|---|---|---|---|---|---|---|---|
| **DRAGON** | +1 | −1 | −1 | −3 | −3 | −3 | −4 | +5 | +5 | +1 |
| **PANDA** | +1 | +1 | −2 | −2 | −2 | −1 | −1 | −2 | +4 | +1 |

Both counts update from every card dealt (baccarat is face-up). Divide by
decks remaining; **bet the Dragon at true count ≥ 10, the Panda at ≥ 11** —
or pre-print the running-count thresholds:

| decks left | 4 | 3 | 2 | 1.5 | 1 | 0.5 |
|---|---|---|---|---|---|---|
| bet DRAGON at RC ≥ | 40 | 30 | 20 | 15 | 10 | 5 |
| bet PANDA at RC ≥ | 44 | 33 | 22 | 17 | 11 | 6 |

Expect ten to thirteen bets per shoe, nearly all in the back half, at average
edges around +7% (Dragon) and +6.5% (Panda). The card captures ~87% of the
combined exact ceiling: **+1.11 units per 100 observed rounds** per unit of
side stake.

## The verdict: no toll to charge

The 21+3 ledger was dominated by a toll — you cannot play a blackjack side
bet without funding a blackjack hand. Baccarat's ledger has no such line
item, or almost none, and working through the operating modes is where this
game separates from everything else in this repository:

| mode | net /100 rounds | $/h at $100 unit | N0 |
|---|---|---|---|
| crowded table, sit out, bet only triggers | +1.11u | ~$50/h (45 r/h) | ~1,030h |
| **heads-up, $10 main every round** | **+1.01u** | **~$101/h (100 r/h)** | **~560h** |
| heads-up, $25 main every round | +0.85u | ~$85/h | ~780h |
| side ≤ main cap, matched on triggers | +0.88u | ~$88/h | ~750h |
| side ≤ main **and** $25 side max | +0.88u | ~$22/h | ~750h |

The reasoning, briefly. At a crowded table you may simply not bet — normal
baccarat behavior — and pay nothing between windows; but crowded baccarat is
slow. Alone at the table you must wager to be dealt to, but the EZ banker bet
at table minimum is the cheapest toll in the casino: 1.02% of $10 against a
$100 side unit is 9% of the gross edge, and heads-up pace (~100 rounds/hour)
doubles the hourly and halves the calendar time to N0. **Pace dominates;
the toll is noise.** If the house caps the side bet at the main bet, raising
both to the cap on trigger rounds nets ~+5.5–6% of the matched amount —
the cap costs 13%. Even capped at $25 with a matched-main rule, the play
clears +$22/h on a ~$25k bankroll, which matches the *entire uncapped 21+3
operation* at a quarter of the exposure.

Bankroll for 5% risk of ruin at full scale: ~800–1,000 side units (≈
$80–99k at $100 units). The variance is real — a Dragon win is +40 units and
everything else on a bet round is −1 — and it is exactly why the prior art
called this bet impractical. At 2005-era $10 and $25 side caps, it was. At
modern $100 caps, with both legs played and the toll structure understood,
the same math the prior art published cashes out at roughly **4× the hourly
of our fully-optimized 21+3 attack at half the N0.**

One more practical asymmetry: the camouflage runs the right direction. A
player at a baccarat table with a scorecard, flat-betting minimum banker,
pressing to the cap late in shoes and throwing side bets on top "while the
shoe is hot" is the single most ordinary figure in the pit — a progression
bettor. The pattern that surveillance screens blackjack for (bets tracking
the count) has no analogue here that anyone watches baccarat for, though the
bets are published prior art and a shop that cares can recognize late-shoe
side pressing if it looks.

## What this verdict is conditional on

1. **The paytables: Dragon 40:1, Panda 25:1** — the standard EZ Baccarat
   configuration. Anything else (progressive versions exist): re-run the
   pipeline first; it's pure configuration.
2. **A real, deeply cut shoe.** The customary cut-card-14 is what the
   headline numbers assume; at 90% penetration the system keeps ~55% of its
   value. A continuous shuffler or per-hand machine shuffle zeroes
   everything — walk away.
3. **Side-bet maximum.** $/h and bankroll scale linearly with it; the edge
   doesn't care.
4. **Eight decks**, and the idealizations on record: 80–100 rounds/hour
   heads-up (half that crowded), burn cards not modeled (a small rounds-per-
   shoe effect, none on conditional EVs), and dealt-card visibility — which
   in baccarat is not an idealization at all, since every card is exposed.
   A watched-and-unresolved statistical note: across 600k rounds the Dragon's
   realized wins ran 1.9σ under exact prediction while later runs ran above
   it; the predictor is exact by construction and the fluctuation is within
   normal sampling range.

## Reproducibility

Every number regenerates from the repository:

```
uv run pytest -q                                        # 214 tests, incl. gates
uv run python -m ridefree.cli bacexact                  # exact table vs published
uv run python -m ridefree.cli bac --shoe-mode csm --rounds 2000000 \
    --seed 7500000001 --dragon7 1 --panda8 1            # settlement gate
uv run python -m ridefree.cli bacev    --rounds 100000 --seed 7700000001 \
    --penetration 0.966                                 # exact ceiling (E13)
uv run python -m ridefree.cli bactrack --rounds 100000 --seed 8700000001 \
    --penetration 0.966                                 # count systems (E14/E14b)
uv run python -m ridefree.cli bacorder --rounds 100000 --seed 8800000001 \
    --penetration 0.966                                 # order bounds (E15)
uv run python data/e14_verdict.py                       # the ledger
```

The experiment log (`docs/EXPERIMENTS.md`, E13–E15) records every run with
its seed; shoe seeds derive through `cards.shoe_seeds()` so no two runs share
shoes. The tableau is the universal one; everything that varies by casino is
data in `BaccaratRules`.

*For education and analysis. Casinos vary their rules, paytables, and limits —
verify yours before drawing any conclusion from this article.*
