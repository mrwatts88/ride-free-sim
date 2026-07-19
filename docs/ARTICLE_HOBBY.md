# The Hobby Card: What Minimum-Bankroll Blackjack Actually Costs

*Research direction, hypotheses, and the honesty standard: Matt Watts.
Implementation, measurement, and drafting: Claude (Anthropic). 2026-07-19.
Experiments E24–E25c in [EXPERIMENTS.md](EXPERIMENTS.md); reproduce any
number from (commit, command, seed).*

**What this is:** a working summary for ourselves, like the E16 blackjack
piece — no new theory. Risk-averse indices, resizing, walk lines, and the
gain-from-perfect-play literature all exist. What's ours is the discipline:
one validated engine, every claim a measurement, and one framing rule that
drove the whole milestone — **a risk-of-ruin bankroll is only honest if you
would actually lose all of it.** "I'll try it and quit if I drop $5k" is not
a $35k bankroll at 5% RoR; it is a much smaller bankroll at a much larger
RoR that was never computed. M11 asked what the game costs when you refuse
to lie to yourself about that.

## The question, and how it moved

The pro question this repo had always answered is *max $/h per bankroll*.
The hobby question inverts it: **minimum bankroll that still clears an
hourly floor** — a blackjack habit that pays for itself without pro-scale
capital. The spec sharpened twice as the numbers arrived:

1. Opening spec: ≥ $15/h at 200 rounds/h, minimum 5%-RoR bankroll (E24).
2. Honest spec, after seeing the frontier: **≤ $5k bankroll, walking at
   most ~10% of the time, ≥ $10/h** (E25b/c).

The second spec turned out to be over-determined — provably, not
rhetorically — and the final answer is the closest honest point to it.

## Method, in one paragraph

E24 priced the whole frontier without a single new simulation: a KKT
solver (bet ∝ edge/E[profit²] per true-count bin, floored at table
minimum) plus an exhaustive 1–2-jump card search, all arithmetic over the
banked E16/E17 bins. E25 then built what no prior experiment had — the
**RA bank**: 40M fresh rounds (10 shards, seeds 21.4–22.3e9) recording,
per TC bin, paired *second* moments for every playing change (chart-cell
suppressions, composition deviations attributed to their first diverging
decision, and the insurance overlay in closed form, hedge term included).
Four gates passed: chart bins reproduce the E16 curve on fresh seeds
(worst |z| 2.12), deviation values replicate the E16 paired estimand
(worst 1.65), attribution sums exactly, and P(dealer BJ | ace up) sits 2σ
below 96/311 precisely as the cut-card effect predicts. E25c measured
walk-line *event rates* live (1M played rounds per line). Selection is
argmin-bankroll with the bet shape re-searched after each pass, so the
hourly constraint binds the card, never the individual play.

## Answer 1: the floor toll owns the problem

Every seated round below TC +2 is a table-minimum bet with negative or
negligible EV. That toll is not mainly an EV problem — it is a **variance
budget** problem. The arithmetic that closed the $5k spec in one line:
$10/h at 200 r/h on $5k at 5% RoR allows σ ≈ $12.9/round *total*; a $10
floor bet played 90+% of rounds contributes ≈ $11.6/round — about 80% of
the entire σ² budget — before a single jump is placed. The jumps that must
then overcome the floor's −$8–12/h drag blow the remainder several times
over. No count, no index set, no ramp engineering escapes this; the only
lever that ever moved the bankroll class was **not having money on the
table at bad counts** — and every way of doing that has a price tag
measured in this milestone: walking (event rates below), sitting out
(vetoed on table culture: a seated player skipping hands reads as exactly
what it is), or paying $21k+ to never leave.

A second structural finding (E24): **the walk line is where division earns
its keep.** The pro card's money decision (the jump) sits on Red 7's pivot
and is depth-exact without division; the hobby's money decision (the walk)
sits far off-pivot, where a fixed running count confuses fresh shoes with
bad ones — the best no-division walk card costs about double. The hobby
card is therefore a hi-lo-with-division card (a walk-pivot count with
imbalance −1 is designed but unbuilt, parked).

## Answer 2: deviations are worth a third of the bankroll — and the RA hunt came back nearly empty

With honest second moments, the full playing layer (indexes + insurance)
cuts the required bankroll 35–45% in every shape — and σ/round *drops*
(24 → 19 at the walk card): the stand-more plays outweigh the extra
doubles and splits. That was Matt's "deviations are where the low variance
lives" hunch, confirmed in direction and priced in dollars.

The stronger version of the hunch — re-tune the indexes themselves for
variance instead of EV — was measured and came back **nearly null: ~1–2%
of bankroll**. EV-max deviations were already variance-friendly, so there
is little left to trade. The genuine risk-averse residue, for the record:
skip splitting 2,2 v 3 and 3,3 v 3 at high counts, and **don't split
T,T v 3 even when the count makes it +EV** (T,T v 6 and v 5 stay, at
bins +5 and +7). Everything else the RA machinery selected is the classic
index card, *re-derived from raw paired moments and ranked by bankroll
impact*: 16vT carries 30% of the play value alone; 16vT, 15vT, 12v3,
12v2, 14vT together carry ~60%; the 45-play tail pools to $221 of
bankroll. And the insurance rule fell out of the optimizer rather than
being assumed: **insure at bins ≥ +4 — exactly "insure when the jump bet
is out,"** the human rule E18 measured at 73–80% capture.

## Answer 3: what walking actually costs (E25c)

Walk lines are priced in % of rounds skipped, but they are *lived* in
events per hour. Measured live (instant re-seat semantics):

| walk line | rounds skipped | walks/hour | shoes abandoned | median exit round |
|---|---|---|---|---|
| TC ≤ −1 | 37.8% | 12.1 | 87% | 5 |
| TC ≤ −2 | 20.8% | 4.8 | 67% | 19 |
| **TC ≤ −3** | **11.6%** | **2.9** | **51%** | **28** |
| TC ≤ −4 | 6.5% | 1.9 | 36% | 32 |

The ≤ −1 line every bankroll-minimizer loves is a fantasy — twelve walks
an hour. Even ≤ −4 carries the walking load (1.9/h, 36% of shoes) that
E18b already shelved as weekday-impractical for the pro card. The hobby
verdict settled on −3: a walk every ~20 minutes, half of shoes played to
the shuffle, and the best bankroll any tolerable line buys.

## The final answer (Matt's call, 2026-07-19)

There is a floor under this shape that no earnings target escapes: drop
the target and the optimizer converges to the same card — below
+$14.3/h, EV shrinks faster than variance and the required bankroll
*rises*. $9.3k at 5% RoR is the entry ticket at −3, and it happens to pay
more than the hobby asked for. Matt took it at hobby-honest odds:

> **THE HOBBY CARD ($10 floor, 6d H17 DAS, pen .75):** count hi-lo, true
> count by decks remaining. **Walk when the TC rounds to −3 or worse**
> (every ~20 minutes; half your shoes). Bet **$10** at every count below
> +2.5, **$35** when the TC rounds to +3, **$85** at +6 and above.
> **Insure at +4 and up** (when a jump bet is out). Basic strategy plus
> the short index set, in bankroll order: stand 16vT, 15vT, 12v3, 12v2,
> 14vT; double 10vT, 10vA, 9v2, 8v6; stand 16 v 7/8/9/A deep; split
> T,T v 6 at +5 and v 5 at +7 — **never v 3**; skip 2,2 v 3 and 3,3 v 3.
>
> **+$14.3/h at 200 rounds/h. Bankroll $7.2k at 10% risk of ruin** —
> "it's a hobby anyways" — or $9.3k at 5%, or $5.0k at 20%, same card,
> pick your honesty. N0 ≈ 433h. σ ≈ $21/round: a 4-hour session swings
> roughly ±$600, ~46% of sessions lose, and a 200-hour year runs
> +$2,900 ± $4,200 — about a 1-in-4 chance a full year of correct play
> loses money. Those are the numbers a hobbyist signs up for, known in
> advance.

The spec scorecard, honestly: $10/h ✔ (half again over). Walking ✖ as
originally wished (2.9/h, not "10% of the time"), accepted with eyes
open. $5k ✖ → $7.2k at a consciously chosen 10% RoR. The game does not
sell the product Matt wanted; this is the closest thing on the shelf.

## Where it sits in the portfolio

| play | $/h | bankroll | note |
|---|---|---|---|
| **hobby card (M11)** | **~$14** | **$7.2k @ 10%** | the low-capital rung; walks every 20 min |
| BJ crouch15-2r (E18) | ~$40–44 | ~$36–40k @ 5% | the certified pro card, trainer-drilled |
| EZ bac two-count (E14) | ~$92–101 per $100u | ~$81k | the annuity, native camouflage |

The hobby card is not a smaller pro card — it is a different product:
half the hourly of crouch15-2r per hour of effort, a fifth the capital,
and the same table heat physics (corr(bet, TC) ≈ 0.8 is intrinsic; low
limits draw low attention — Matt's field intel, unchanged).

## Honesty section (what could move these numbers)

- **The $10 weekday floor is UNCONFIRMED** — Saturday recon saw only $15
  tables. At a $15 floor the same shape costs $10.7k at 10% RoR (pays
  +$22.5/h). This is the card's single biggest condition.
- **Pen .75 assumed;** the one deep-cut table (~.83) is worth roughly
  ×0.75 on bankroll. **Pace 200 r/h heads-up assumed;** weekday pace is
  still the model's oldest unknown — at 140 r/h the hourly scales to ~$10.
- **Not live-certified.** The card is a searched argmax over banked bins
  (winner's curse at both card and play level), its play effects compose
  additively in (μ, M2), the dev window starts at bin +2, and the crisp
  TC indexes approximate composition-exact plays. The E18/E23-pattern OOS
  certification — the literal human card on fresh seeds — is the
  mandatory gate **if this card ever heads to the felt.** M11 closed
  without it by choice; the number is bin-arithmetic-grade, not
  felt-certified-grade.
- Walk rows price "cards keep flowing" semantics; live re-seating differs
  slightly (E18b measured the gap at ~$1/h at pro scale). Rounds
  independent for variance; fixed stakes, no resizing (the resize ladder
  was considered and declined — "not a lot of dropping down you can do"
  from a $10 floor).

## Provenance

E24: arithmetic only, zero seeds (`data/e24_hobby.py` over the E16/E17
banks). E25: `cli rabank`, 40M rounds, seeds 21.4–22.3e9, four gates
green, 307 tests (`data/e25_ra.py`, `tests/test_ra_bank.py`); machinery
decision record in DESIGN.md. E25c: `data/e25c_walks.py`, seed
22400000001. Engine provenance unchanged: validated against published
house edges (Wizard of Odds) before any attack work; every number above
reproduces from (commit, command, seed).
