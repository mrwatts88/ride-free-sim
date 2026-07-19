# The Lammer Count: Beating Pot of Gold at Free Bet Blackjack

*Pot of Gold (sold on some floors as "Silver Stack") is a side bet on Free
Bet blackjack that pays by the number of free splits and free doubles a
player collects in one round. This study makes three claims, in ascending
order of interest. First, the published house-edge table for the bet is
arithmetically impossible: the probability of collecting zero free bets is
strategy-free dealing arithmetic with an exact closed-form answer, and the
published figure disagrees with it; the bet's real cost is about 8.2%, not
the advertised 5.77%. Second, the bet is genuinely countable — the first
composition analysis of it we are aware of — and the count is unlike any
blackjack count in print: it fires at* negative *true counts, the 5 (the
crown jewel of blackjack counting) is irrelevant to it, and the 7 is a full
point. Third, a no-division unbalanced count derived from first principles
("pog2") beats hi-lo-with-division at the trigger, was certified end to end
by 20 million live simulated rounds, and still ended up shelved — because
the felt sets the ceiling on a fixed-cost business, and this felt's answer
was a $25 tied maximum at 100 slow hands an hour. The mathematics is a
clean win; the ledger is a grind. Both halves are reported here with equal
care.*

---

**A note on how this research was done.** Like the other studies in this
repository ([ARTICLE.md](ARTICLE.md), [ARTICLE_21P3.md](ARTICLE_21P3.md),
[ARTICLE_EZBAC.md](ARTICLE_EZBAC.md),
[ARTICLE_BLACKJACK.md](ARTICLE_BLACKJACK.md)), this was a collaboration
between the author and Claude (Anthropic's AI system), which implemented
the engine, ran the analyses, and drafted this article. Direction was
human: the target came from floor reconnaissance, the farm arm and the
simplified counts were the author's hypotheses, and the standards of
evidence — validation gates before attack work, out-of-sample ceremony for
every fitted threshold, live certification of the literal card before any
number is trusted — are the repository's working rules. The final claims
are the author's to defend, and every number is reproducible from the
repository.

---

## The bet

Free Bet blackjack (played as "Ride Free" at the casino that prompted this
study) is Geoff Hall's variant in which the house funds your splits and
doubles: split any pair except tens for free, double hard 9/10/11 for
free, and in exchange a dealer 22 pushes all live hands. Each free split
or free double is granted as a physical button — a *lammer* — placed by
your bet. Pot of Gold is a side bet on how many lammers you end the round
with, kept win, lose, or push:

| lammers | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| pays | 3 | 10 | 30 | 60 | 100 | 300 | 1000 |

That is Galaxy Gaming's Pay Table 1, confirmed on the felt down to the
300:1 six-lammer rung. Zero lammers loses the stake — and zero is the
overwhelmingly common outcome, because a round earns its first lammer only
if the starting two cards are free-bet eligible and the dealer has no
blackjack. Seven lammers (three free splits plus a free double on every
resulting hand) is the 1000:1 jackpot. Under the Nevada rules of play, all
Pot of Gold wagers lose to a dealer natural.

The published analysis (Wizard of Odds, Free Bet page) prices Pay Table 1
at a 5.77% house edge under normal play, improving to 2.75% if the player
free-splits 5s instead of taking the free double — a detail that becomes
important later. No composition analysis of the bet has been published
anywhere we could find; a Wizard of Vegas forum thread asking whether it
is countable ends, unanswered, with "needs a simulation."

This is that simulation.

## First, the credibility check

The repository rule: no exotic claim is trusted until the machinery
reproduces boring published facts. The Free Bet engine behind this study
had already passed its published-edge gates (main-game house edge 0.99%
measured against Wizard of Odds' 1.04% for the exact ruleset, dealer-22
frequency 7.354% against their 7.3536%, and the resplit-aces rule
variation reproduced to 0.081% against their 0.08%). The Pot of Gold layer
added no cards and no randomness — the engine's existing ledger already
counted free splits and free doubles separately, so settlement is
arithmetic on numbers the validated engine was already producing.

The new layer then faced its own gate battery: ten independent shards of
two million rounds each, scored against every external number available.
The split-fives improvement — a published, convention-independent delta
that exercises the entire resplit and multi-lammer tree — measured
**+3.080% ± 0.185 against the published +3.019%** (z = +0.33). The farm's
main-game cost measured −0.173% ± 0.048 against the published −0.15%. The
six- and seven-lammer tail matched the published table within a fraction
of a standard deviation (23 jackpots in 10 million rounds). The machinery
agrees with the published record everywhere the published record is
internally consistent.

Everywhere, that is, except one place.

## The published table is impossible on P(0)

The probability of ending a round with *zero* lammers does not depend on
strategy at all. A round earns at least one lammer if and only if the
initial two cards are free-bet eligible — any pair ace through nine, or a
non-pair hard 9, 10, or 11 — and the dealer does not have blackjack. Every
sensible strategy takes every offered free bet (we proved this holds for
every strategy in the repository by enumeration; the one genuine choice —
a pair of 5s, which may either free-double or free-split — banks its
first lammer immediately under either action, so the divergence moves
probability among the paying rungs but never in or out of zero). P(0) is therefore pure dealing arithmetic over the
six-deck composition, computable in exact rational fractions:

> **P(0 lammers) = 0.838228071…** (exact, six decks, lose-to-dealer-
> blackjack settlement — and invariant to peek convention under that rule)

The published table says **0.833420**, sourced to a "random simulation"
with no stated methodology. The two are irreconcilable at any deck count —
the gap is 24 standard deviations of our ten-shard battery, against an
exact number. Our simulator, run blind on fresh seeds, landed on the exact
figure at z = −0.41.

The likeliest reconstruction: the published simulation let lammers survive
a dealer ten-up blackjack (an ace-peek-only convention), which is both
contrary to the Nevada rules-of-play filing and, on some floors, contrary
to how the bet is actually dealt. Their k ≥ 2 rungs are robust to that
convention and mostly match; their P(0), P(1) — and therefore the house
edge built on them — are not. There is also a residual shape disagreement
at three lammers (−4% relative, beyond any convention we could construct)
that we log but cannot explain; their table cannot be fully reconstructed
under the stated rules.

The correction that matters to a player reading the rack card:

> **Pot of Gold Pay Table 1 costs 8.25% (± 0.13), not 5.77%.** The
> split-fives farm improves it to 5.17%, not 2.75%. (Pay Table 2: 7.07%.)

We publish this with some confidence because the same machinery reproduces
the published *deltas* — the numbers that don't depend on the disputed
convention — to a third of a standard deviation.

## Why the bet is countable, and why the count is upside down

Everything about the lammer distribution is fed by small cards. Free
doubles need hard 9/10/11 in two cards — 4+5, 5+6, 3+6, and their
neighbors. Free splits need pairs below ten. The long chains that reach
the paytable's convex upper rungs need *clusters* of small cards: a 5,5
split into re-pairs and free doubles consumes half a suit of low
denominations in one round. Ten-rich shoes, the shoes every blackjack
counter waits for, are exactly the shoes in which the side bet starves.

So the signal is anti-correlated with hi-lo — corr(free-double
probability, hi-lo true count) = **−0.937** — and the bet comes alive at
counts a blackjack player considers garbage. Binning twenty million
cut-card rounds by the pre-deal hi-lo true count:

| hi-lo TC | 0 | −2 | −3 | −4 | −6 | −8 | −12 |
|---|---|---|---|---|---|---|---|
| side EV per unit | −4.4% | +3.2% | +7.1% | +11.5% | +19.5% | +29% | +45% |

Monotone, enormous, and statistically overwhelming (per-bin z up to +20).
The lammer rate roughly triples across that range while the paytable's
convexity multiplies it. The zero crossing sits between TC −1 and −2. At
the threshold chosen in-sample and replicated out-of-sample (TC ≤ −3, no
farming yet), the side bet is **+7.37% ± 0.31 per unit staked on 11.65% of
rounds**.

Nothing else in this repository — not the 21+3 suit attack, not the
Dragon 7 — has a window one third this rich. The structural reason is that
an 8.25% base edge is simply not much armor against a signal this strong:
the paytable pays 1000:1 into events manufactured almost entirely out of
small-card concentration.

## The farm: split your 5s while the side bet is out

The published 2.75%-edge row already hints at it: free-splitting 5s
(instead of taking the free double on 10) manufactures lammers at a tiny
main-game cost. As a full-time strategy it is a curiosity. As a
*conditional* strategy — farm only while your side bet is out — it is
close to free money, and it is count-fed exactly like the bet itself.

Measured with paired seeds (identical shoes, the two arms diverge only at
a 5,5 decision), farming lifts the trigger window from +7.37% to
**+11.78% ± 0.09 per unit**, and the per-bin breakeven side stake against
a $15 main is *under one dollar everywhere* — meaning the human rule needs
no qualification: **side bet out → split 5s. Side bet down → the free
double takes over again.** Farming also widens the profitable window one
full true-count point (the TC −2 bin flips positive under it).

One honest cost is measured rather than assumed: a farm split doubles the
main-bet exposure in exactly the rounds where a lammer lands, so main and
side profits are positively correlated (+0.72 units², measured in the live
certification below) — the variance is slightly worse than independent
accounting suggests, and every bankroll figure in this article carries the
measured value.

## The count, from first principles

Hi-lo captures most of this — but hi-lo is a *main-game* count conscripted
into pricing a lammer distribution, and there was no reason to expect it
to be optimal. Regressing side-bet profit on the per-rank composition of
the remaining shoe (with the same machinery cross-validated against the
repository's independently derived main-game removal effects, agreement
+0.9956) gives the bet's own effects of removal, and they are strange by
blackjack standards:

- **The fuel is 2 through 8.** Removing any one costs the side bet
  6.8–9.2% of a unit — and the **7 is as heavy as the 3**, because 7s
  make the hard 9/10/11 free-double totals (2+7, 4+7, 3+6…). The 9 is
  half-strength; the aces and tens are dead.
- **The best human count sheds the 5 entirely.** Under the constraint of
  whole ±1 tags, the search keeps 3/4/6/7 and drops 5, 8, and 9 — so the
  5, blackjack counting's most valuable card, carries no tag at all in
  the optimal lammer count. No count in the blackjack literature looks
  like this.

Scored against these removal effects as lammer counts: hi-lo −0.931,
Red 7 −0.965. A search over the full family of unbalanced level-1 counts,
constrained to put its *pivot* — the running-count value that is
depth-invariant — exactly at the trigger, lands on:

> **pog2: aces and tens −1; 3, 4, 6, 7 +1; red 2s +1 (black 2s nothing);
> 5s, 8s, 9s nothing. Start each shoe at 24. Stake the side bet — and
> split 5s while it's out — at 12 or below.**

(The red-2 device pins the pivot at the right parity, the same trick as
the Red 7 count; correlation with the exact removal effects −0.9726.)

Head-to-head on identical card streams — so differences are pure capture,
with no shoe noise — pog2's no-division trigger takes **106.6% of what
hi-lo with true-count division takes**: a sharper window (16.5% of rounds
at +10.13% ± 0.27 per unit) versus hi-lo's wider, thinner one. The rung
search, run blind in-sample, chose the pivot itself; the out-of-sample
half confirmed it (+10.22%). A running count with no division beating the
divided benchmark is the same free lunch the repository found for the
main game's Red 7 card, for the same structural reason: a pivot placed
*at* the decision threshold is depth-exact precisely where it matters,
and penetration-robust by construction — the pivot is TC −2 at every
depth, so dealer-to-dealer variation in cut depth cannot move the rung.

Two postscripts from the author's simplification instinct, both measured:

- **"hi-lo-57"** — ordinary hi-lo with the 5 and the 7 trading tags
  (balanced; start 10, stake at ≤ 5) — statistically **ties** pog2. For a
  player who already keeps hi-lo, one swapped pair of tags converts the
  drilled count. Its fixed rung, however, is tuned to one penetration,
  where pog2's pivot is not — which decided the primary.
- **KO's tags are refuted for this job**: the pivot sits six points from
  the trigger, and the fixed-rung capture collapses to 35%. The
  dose-response is now a measured curve — 0, 2, 4, 6 points of pivot
  offset keep roughly 100%, ~100%, 70%, 35% of the value. The pivot is
  the entire game.

## Certified live

Binned curves involve stitching approximations (window bins from one arm,
outside bins from another, zero main-side covariance). So the literal
card — start 24, stake at 12 or below, farm while out, flat main,
straight Free Bet basic strategy, no insurance — was played end to end on
ten million fresh rounds per penetration, exactly as a human would play
it. Both gates passed:

- Staked **16.49%** of rounds (the binned prediction: 16.5%) at side EV
  **+10.39% ± 0.39** per unit (predicted +10.13%; z = +0.66).
- Unstaked main EV −0.946% against the ledger's −0.95% assumption
  (z = +0.11).

And the felt turned out to deal *deeper* than the study had assumed: the
cut card observed on the live tables sits 1 to 1.25 decks from the end
(penetration ~0.79–0.83 against the assumed 0.75). Depth feeds this
signal twice over — at the observed one-deck cut the card stakes **18.6%
of rounds at +11.18% ± 0.36 per unit**. The seven-lammer jackpot landed
seven times in 1.65 million staked rounds, right on the arithmetic.

## The ledger, at the real felt

Then the felt answered the three questions that price any fixed-cost
business, and each answer took a tier off the top:

1. **The side bet maximum is $25.** The attack's income scales with the
   stake; its toll (the main bet's negative expectation, charged every
   round) does not. At $100 stakes this play makes several hundred
   dollars an hour; at $25 it cannot.
2. **The side bet is tied: side ≤ main.** Staking $25 requires a $25 main
   bet, so the play becomes *raise-on-trigger* — $15 main outside the
   window, $25 main + $25 side inside it — which keeps most of the value
   and, as a bonus, raises the main bet when the count *falls*:
   anti-correlated with hi-lo, the mirror image of the tell surveillance
   screens for.
3. **The game is slow.** Free Bet's extra procedure (lammers out, lammers
   paid, free hands resolved) runs about 100 hands an hour, half the pace
   of the blackjack ledgers next door.

The certified bottom line, with all constraints applied and every
approximation replaced by a measured value:

| penetration | net per hour | sd per round | N0 | bankroll (5% RoR) |
|---|---|---|---|---|
| 0.75 | +$22.13 ± 1.74 | $54.90 | 615h | $20.4k |
| 0.833 (the observed cut) | **+$30.20 ± 1.83** | $57.83 | 367h | **$16.6k** |

About $26–30 an hour on a $17k bankroll at the observed penetration. Per
bankroll dollar that is actually the best line the repository owns —
roughly three quarters of the locked blackjack card's hourly on less
than half its bankroll. As an hourly it is
a grind, and it is earned with the most conspicuous play style this
repository has produced: jamming a side bet at visibly terrible counts,
splitting 5s against every instinct at the table, playing a count that
ignores 5s entirely. Free Bet tables run social — the basic strategy is
obscure enough that ordinary play already draws commentary — and this
play is a running invitation to it. None of that changes the arithmetic;
all of it changes whether the seat is worth occupying.

**The verdict on record: the bet is beatable, the count is real and
certified, and the play is shelved.** The felt's constraints — a $25 tied
maximum at 100 hands an hour — cap it below the author's alternatives,
and the standard blackjack card next door earns more per hour of
attention with none of the theater. If a floor ever posts this bet at a
$100 untied maximum with a deep cut, the certified numbers in this study
say +$150 to +$190 an hour on a $36–40k bankroll. That felt, we would
play.

## What this verdict is conditional on

- **Pay Table 1** (3/10/30/60/100/300/1000), felt-confirmed including the
  300:1 rung. Other paytables reprice by arithmetic on the banked token
  histograms; none we know of changes the countability conclusion.
- **Six decks, dealer hits soft 17, dealer 22 pushes, free splits to four
  hands (aces once, one card each), free re-splits, free double on hard
  9/10/11 after splits** — the standard Free Bet configuration, validated
  against its published main-game edge. The four-hand resplit cap is
  confirmed on the felt; the farm leans on it.
- **All Pot of Gold wagers lose to a dealer blackjack** (the Nevada
  rules-of-play settlement). A floor that pays lammers through a ten-up
  natural is playing the convention the published table appears to
  assume; it would *improve* the player's side of every number here.
- **Cut-card shoes, no CSM.** A continuous shuffler kills this attack
  completely, as it kills all of them.
- Pace, penetration, and the tie ratio as observed on one floor in July
  2026; the ledger table above shows the sensitivity.

## Reproducibility

Everything in this article regenerates from the repository:
`side_bets.exact_p0_pot_of_gold` (the exact fraction), `data/m10a_*.py`
(the gate battery), `cli pogcurve` / `data/m10b_verdict.py` (the curve),
`data/m10b_farm_verdict.py` (the farm), `cli pogeor` / `data/e22_card.py`
(removal effects and the count search), `data/e22_run.py` /
`e22_verdict.py` (the head-to-head), `data/e22b_verdict.py` (hi-lo-57 and
KO), and `data/e23_run.py` / `e23_verdict.py` (the live certification and
the felt-true ledger). Seeds and shard files are logged in
`docs/EXPERIMENTS.md` (E19–E23); every run is deterministic under its
seed. The engine's validation ladder — hand-level known outcomes,
exhaustive decision tests, statistical frequencies, published-edge
matches — is in the test suite, 300 tests at time of writing.
