# Four Suit Counts and One Curve: Beating the 21+3 Blackjack Side Bet

*The 21+3 side bet resolves a three-card poker hand — your two cards plus the
dealer's up card — and the flat 9-to-1 version carries a 3.24% house edge off
the top. It is also, at deep penetration, one of the most countable bets on a
blackjack table. This is the full derivation: the exact ceiling, an exact
decomposition of where the edge lives, a four-count human system that captures
78% of it, and an honest verdict — including how it compares to the one prior
published attack.*

---

**A note on how this research was done.** Like the Free Bet study in this
repository ([ARTICLE.md](ARTICLE.md)), this was a collaboration between the
author and Claude (Anthropic's AI system), which implemented the simulator
extensions, ran the analyses, and drafted this article. Direction was human:
the research question, the insistence on validation gates before attack work,
and the standards of evidence. The final claims are the author's to defend,
and every number is reproducible from the repository.

---

## The bet

21+3 is offered beside the main wager on ordinary blackjack tables: before the
deal you may stake a side bet that pays on the three-card poker hand formed by
your first two cards and the dealer's up card. The original paytable — the one
analyzed here — pays a flat **9 to 1** for a flush, straight, three of a kind,
or straight flush, and takes everything else.

Off a fresh six-deck shoe the arithmetic is fully knowable: of the
C(312,3) = 5,013,320 possible triples, 10,368 are straight flushes, 26,312 are
trips, 155,520 are straights, and 292,896 are flushes. Total win probability
9.676%, expected value **−3.2386%** — a figure published by Michael
Shackleford (Wizard of Odds) that our engine had to reproduce, twice over,
before any attack work began (more below).

Why should this be countable at all? Because 60% of the winning mass is
flushes, and flush probability is *convex* in the suit composition: a shoe
with 30 spades and 10 clubs left makes more flushes than a balanced one,
because C(n,3) grows faster than linearly. Convexity means imbalance — any
imbalance — helps. No standard rank-based counting system can see this: by
symmetry, the four suits' effects of removal are identical, so every linear
rank count carries exactly zero suit information. The signal, if it exists,
lives in a place hi-lo is structurally blind to.

## First, the credibility check

This project's rule is that no exotic claim is trusted until the machinery
reproduces boring published facts. The blackjack engine behind this study
already passed the Free Bet project's validation ladder (standard house edges,
dealer outcome tables, Griffin's EOR table — see ARTICLE.md). For 21+3 two new
gates were added, each with two independent references:

- **Exact combinatorics:** an in-test exhaustive enumeration of all six-deck
  triples must equal the Wizard of Odds combination table integer-for-integer
  (it does: 10,368 / 26,312 / 155,520 / 292,896 of 5,013,320).
- **End-to-end settlement:** 6 million always-bet rounds dealt off freshly
  shuffled shoes returned −3.128% ± 0.121% against the published −3.2386%
  (+0.92σ), with every category frequency within ±1.3σ.
- **The live predictor:** during the attack runs, realized results were
  regressed on the exact pre-deal EV across 40 bins spanning −13% to +9%:
  slope 1.034 ± 0.071. The calculator prices depleted shoes correctly.
- **The cards themselves:** the suit-aware shoe still passes all four of the
  original validation batteries, byte-identical replay under seed included.

## The exact ceiling: what perfect play is worth

For a bet that settles on three cards, the exact conditional EV given the
remaining shoe composition is closed form — a few hundred integer operations
over the per-(rank, suit) counts. No effects-of-removal approximation, no
model: the true EV, every round, before the deal.

Scanning millions of cut-card rounds and betting exactly when that EV is
positive (the perfect-information ceiling):

| penetration | +EV rounds | mean edge when betting | ceiling per 100 rounds |
|---|---|---|---|
| 75% | 4.6% | +2.5% | **+0.116 units** per unit staked |
| 85% | 7.1% | +3.9% | **+0.276 units** |

The signal is violently late-shoe: at 75% penetration nothing is bettable
until about four decks remain, and the +EV fraction climbs from 3.6% of rounds
at three decks to 18% at a deck and a half. Cut one more half-deck of
penetration and the ceiling more than doubles — at one deck remaining, a
quarter of all rounds are +EV at a mean of +5.6%. Penetration is the single
biggest lever in this game.

Two more facts that shape everything downstream. First, the signal is
essentially orthogonal to hi-lo (correlation ≈ −0.08): side-bet windows and
main-game counting windows rarely collide. Second, for scale: the entire
bet-selection value of the Free Bet game this repository was built to study
was +0.039u per 100 rounds. This bet offers three to seven times that.

## Anatomy: where the edge lives

The EV formula is a polynomial in the 52 composition counts — which means it
evaluates cleanly on *fractional* compositions. That allows an exact
decomposition with no model fitting anywhere. For every shoe state, compute
the EV of three smoothed twins: same suit totals with ranks flattened, same
rank totals with suits flattened, and fully balanced at the same depth. Then

> EV = B(depth) + S(suit configuration) + R(rank configuration) + X(residual)

is an identity, and each term is exact. Measured over millions of round
states:

- **The suit term S carries 70–72% of the variance.** The rank term R carries
  17–21% (mostly the straight term Σ nₐ·n_b·n_c, some trips).
- **The interaction X is dead: ~0.2%.** A selection rule using S and R
  additively, ignoring X entirely, captures 99.8% of the exact ceiling.
  Rank-within-suit structure (straight-flush effects) is priced at 9:1 like
  everything else and simply doesn't matter.
- **The depth baseline B is a headwind, and it's steep**: a *balanced* shoe's
  21+3 EV worsens from −3.24% fresh to −8.2% at a deck and a half, to −13.9%
  at half a deck. Every +EV round is a composition fluctuation strong enough
  to overcome a deteriorating baseline. Practical consequence: any human
  system needs depth-indexed thresholds, not a single trigger number.
- Rank-only selection is nearly worthless on its own (4–6% of the ceiling) —
  the structural prediction confirmed: this game is about suits.

## The human system: quad-Q

A player can realistically keep four running counts — one per suit, +1 per
card seen. From those and the cards-remaining total, each suit's *excess* over
its fair share (N/4) is a subtraction. The question is what statistic of the
four excesses to compare against what threshold.

The discipline here matters: an earlier audit of this repository's Free Bet
work found an in-sample bias in a betting verdict, and the lesson stuck.
**Every threshold below is derived analytically from the closed-form EV —
bisecting the exact suit-configuration formula — before any simulation ran.**
The simulations only score the rules; nothing is tuned to them.

Scored on 2M fresh-seeded rounds per penetration, in *true* exact EV:

| rule | tracks | pen 75% | pen 85% |
|---|---|---|---|
| exact EV (computer) | everything | 100% | 100% |
| suit + rank, additive (computer) | everything | 99.8% | 99.8% |
| exact four-suit table (bound) | 4 counts | 73.3% | 77.3% |
| **quad-Q: Σ excess² ≥ T_Q(N)** | **4 counts** | **74.2%** | **78.3%** |
| + best static linear rank count | + a 13-tag count | 80.3% | 81.1% |
| "one rich suit" max-excess rule | 4 counts | 38.7% | 47.3% |
| single-suit specialist | 1 count | 10.1% | 11.2% |

**Quad-Q is the finding.** Bet when the sum of squared suit excesses clears
one memorized depth curve. It matches the exact four-suit bound — the
quadratic form *is* the right shape, because the flush convexity it exploits
is itself a symmetric quadratic. In units per 100 observed rounds it banks
+0.086 (75% pen) and +0.211 (85% pen) per unit of side stake.

The index curve, derived once from the closed form (minimum excess of one
rich suit to bet; the quad-Q threshold is T_Q = 4/3 · T1²):

| decks remaining | 0.5 | 0.75 | 1 | 1.5 | 2 | 2.5 | 3 | 4 |
|---|---|---|---|---|---|---|---|---|
| T1 (excess cards) | 4.0 | 5.0 | 5.9 | 7.4 | 8.7 | 10.0 | 11.2 | 13.5 |

Two negative results worth as much as the positive one. The intuitive rule —
"bet when one suit is very rich" — captures barely half the suit value,
because shoes with *two* moderately rich suits carry real EV that a maximum
can't see (and a *poor* suit concentrates the remainder just as profitably).
And the last ~19% of the ceiling, the quadratic rank term, appears genuinely
out of human reach: the best static linear rank count recovers only six
points of it.

## The verdict: charging the toll

You cannot bet 21+3 without a live main wager, so the honest ledger charges
the blackjack you're forced to play — 0.64% per round on the main bet (6-deck
H17 basic strategy). How often you pay it depends on the mode:

| pen | mode | net, side units /100 rounds |
|---|---|---|
| 75% | seated, $15 main : $100 side | −0.010 (dead) |
| 75% | wong-in on triggers | +0.083 |
| 85% | seated, $15 main : $100 side | +0.115 |
| 85% | **wong-in on triggers** | **+0.206** |

Seated play breaks even only above a 3:1 side:main ratio at 85% penetration
(7.4:1 at 75% — hopeless). The back-counter who stands behind the table,
keeps the four counts, and steps in only on trigger rounds pays the toll on
just ~5–7% of rounds and keeps nearly the whole side edge.

Dollarized at a $100 side unit, $15 main, 100 observed rounds/hour:
**wong-in at 85% penetration ≈ +$21/hour**, σ ≈ $716/hour, N0 ≈ 1,200 hours,
bankroll for 5% risk of ruin ≈ $37k. Seated at min-main/max-side: ≈ +$11.5/hr,
N0 ≈ 4,100 hours. This is grind-scale — the same order as legitimate hi-lo
counting — not a bonanza. But unlike the Free Bet game, it is **not dominated
by the game next door**: the signal is orthogonal to hi-lo, so the strongest
configuration is a counted main game *plus* quad-Q on the side, the two legs
stacking almost additively.

### What if the side bet is capped at the main bet?

Many houses rule that the side wager may not exceed the main wager, which
looks fatal for a system whose edge lives on the side. It isn't — because on
a trigger round the *pair* of bets is jointly profitable: matched at $B, the
side earns +3.83%·B against the main's −0.64%·B, so every matched dollar
nets **≈ +3.2% per trigger round**. Concretely (pen 85%, $100 units):

- **Wong-in, main = side on triggers only:** +0.176 units/100 observed
  rounds ≈ **+$17.6/hour** — the cap costs about 15% of the uncapped edge.
- **Seated:** table-minimum main off-trigger, then raise *both* bets to the
  cap when quad-Q fires: ≈ **+$8.5/hour** (vs +$11.5 uncapped). The
  trigger-round main raise even reads to surveillance like an ordinary bet
  spread — except it is uncorrelated with the running count, which is not
  the pattern counter-catchers screen for. (Fine print: trigger windows lean
  faintly low-count — corr ≈ −0.08 — so the main hand plays a hair worse
  than −0.64% there; it shaves the margin without changing the sign.)

At 75% penetration the capped numbers are +$6.4/h wonging and negative
seated — but that game was marginal before the cap. The cap moves the answer
between "full edge" and "~85% of it"; penetration and the paytable remain
the kill conditions.

## The prior art, and an unplanned replication

After deriving all of this, we checked it against the one published attack we
could find: Eliot Jacobson's analysis (BJ Insider newsletter 164) of the same
flat 9:1, six-deck bet with the cut card at 260 cards — penetration 83%,
almost exactly our deep runs.

His perfect-play ceiling: **0.2748 units per 100 hands**. Ours: **0.269–0.276**
across independent measurements. Two codebases, a decade apart, agreeing to
the third decimal — as strong an external validation as a simulation study
can hope for.

His counting system is different: a *spread* count (most abundant suit minus
least abundant, true-counted), reaching 64.7% efficiency against his ceiling.
Quad-Q reaches 78.3% on the same game at the same depth — about 19% more
value — consistent with our decomposition: a one-dimensional shadow of the
suit configuration undercaptures a quadratic signal. (Honesty requires the
caveat that this comparison crosses harnesses — his thresholds on his
simulation, ours on ours; identical game and depth, but not a same-seed
head-to-head.) His famous "the suit count is essentially worthless" line
refers to the *single-suit* variant — which our scoring confirms at ~10%
capture. His overall verdict of "minimal vulnerability" rested on the
practical constraints of his era, chiefly low side-bet caps; at modern $100
caps, his own numbers land within a few dollars an hour of ours.

## What this verdict is conditional on

In order of sensitivity, verified against the actual table before believing
any dollar figure:

1. **The paytable.** Everything here is the flat 9-to-1 original. The tiered
   "Xtreme" versions carry ~13% house edges and different category weights —
   no threshold in this article transfers (though the entire pipeline reruns
   on any paytable as pure configuration).
2. **Penetration.** 75% → 85% multiplies the net wong-in edge by 2.5×. Below
   ~75% this game is not meaningfully playable.
3. **No CSM.** A continuous shuffler zeroes everything.
4. **Entry policy and limits.** Wong-in mode needs mid-shoe entry; where it's
   banned, seated mode needs either main-min:side-max of roughly 1:3 or
   better, or the raise-both-on-trigger play above. A side-≤-main cap costs
   ~15% (wonging) and does not by itself flip any verdict.
5. **Six decks**, and the idealizations on record: all dealt cards including
   the dealer's hole card assumed eventually visible (standard tracking
   doctrine; the effect of the exceptions is small), heads-up pace for the
   hourly figures, and no burn-card modeling.

And one non-mathematical condition: a maximum side bet that appears only in
the last two decks of a shoe is a *legible pattern*. Suit-counting 21+3 is
published prior art; surveillance that cares already knows what it looks
like.

## Reproducibility

Every number above regenerates from the repository (tag the current HEAD;
`ride-free-v1` preserves the original Free Bet study):

```
uv run pytest -q                                        # 186 tests, incl. gates
uv run python -m ridefree.cli sim  --rules h17 --shoe-mode csm --21p3 \
    --no-insurance --no-deviations --rounds 3000000 --seed 6400000003
uv run python -m ridefree.cli sbev     --rounds 3000000 --seed 6700000001
uv run python -m ridefree.cli sbev     --rounds 3000000 --seed 6800000001 --penetration 0.85
uv run python -m ridefree.cli sbdecomp --rounds 2000000 --seed 6900000001
uv run python -m ridefree.cli sbdecomp --rounds 2000000 --seed 7000000001 --penetration 0.85
uv run python -m ridefree.cli sbtrack  --rounds 2000000 --seed 7100000001
uv run python -m ridefree.cli sbtrack  --rounds 2000000 --seed 7200000001 --penetration 0.85
uv run python data/e12_verdict.py                       # the ledger
```

The experiment log (`docs/EXPERIMENTS.md`, E10–E12) records every run with
its seed; shoe seeds derive through `cards.shoe_seeds()` so no two runs share
shoes. The engine deals full (rank, suit) cards and collapses to blackjack
values once at shuffle time, so the blackjack logic that passed the published-
edge gates is bit-for-bit the logic underneath every claim here.

*For education and analysis. Casinos vary their rules and paytables — verify
yours before drawing any conclusion from this article.*
