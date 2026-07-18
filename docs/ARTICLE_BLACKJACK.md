# Pricing the Game Next Door: a Cover-vs-Money Ledger for Standard Blackjack

*Research direction, hypotheses, and field knowledge: Matt Watts. Implementation,
measurement, and drafting: Claude (Anthropic). 2026-07-18. Experiment E16 in
[EXPERIMENTS.md](EXPERIMENTS.md); reproduce any number from (commit, command,
seed).*

**What this is:** a working summary, not a discovery. Everything here is
classical card-counting theory — hi-lo, spreads, wonging, insurance — applied
to one specific game with one discipline: every claim is a measurement from
our validated engine, denominated in dollars per hour at named table limits,
with variance, bankroll, and a surveillance statistic attached. The other
write-ups in this repo each found something new. This one just answers,
carefully, a question every counter eventually asks: *what is the game next
door actually worth to me, and what does the camouflage cost?*

## The question

Three projects in, the portfolio looked like this: Ride Free (dominated,
retired), 21+3 (beatable, grind-scale), Dragon 7 + Panda 8 (beatable, the
strongest verdict). The obvious missing row was plain blackjack — the game
the whole repo had been using as its validation reference. Two questions:

1. **The camouflage holy grail:** can playing skill — indexes, composition
   play, anything — beat or substantially rescue *negative counts*? A counter
   who could survive bad shoes could flat-bet, and flat-betting is invisible.
2. **The practical one:** on the actual tables available (6-deck H17, DAS,
   no surrender, shoes not CSMs, limits $10–$200 / $15–$500 / $25–$2,000),
   what do real betting patterns pay in real dollars — and which patterns are
   quiet enough to not be worth a second look?

## Method, in one paragraph

One 120M-round pass banked per-true-count bins (frequency, mean EV, second
moment, insurance attribution) for two playing arms — chart play, and chart
play plus composition-exact insurance — plus an 8M-round paired-differential
run that prices composition-perfect playing deviations *per TC bin* at ~100×
the resolution of independent runs. Because blackjack profit is exactly
linear in the initial bet, any betting pattern can then be priced by
arithmetic over the banked bins; a live betting simulator (`cli ramp`, new in
this session) replayed three chosen patterns over 10M fresh rounds each and
matched the arithmetic (worst gap 2.0σ; average bet, per-round σ, and
corr(bet, TC) to three decimals). The harness also reproduced two numbers
measured by completely different code paths earlier in the project (the 1-8
spread's +0.23% on money from E4c; the ~+1.1% wong-in edge from E4/E7).
Details and idealizations: EXPERIMENTS.md E16.

## Answer 1: negative counts are structurally lost

Composition-perfect play — an oracle strictly better than any index card —
recovers, per round: **+0.06% at TC −1, +0.13% at −2, +0.24% at −4**, against
deficits of −1.1%, −1.5%, −2.7%. That is 8–9% of the hole, uniformly, rising
to only ~22% at TC −8. Every player asymmetry (3:2 naturals, doubles, splits,
the right to stand) is a ten/ace asymmetry, and small-card shoes shrink the
option value itself; perfect knowledge of a bad shoe mostly tells you
precisely how bad it is. Consequently the perfect-camouflage play — flat bet,
every round, forever — **loses $15.58/h at $25 units even played with
composition-perfect skill it loses $11.72/h.** There is no skill route out of
negative counts; there is only not having money on the table when they
happen. The holy grail is closed, by measurement, on our own game.

## Answer 2: the price list

At $25 units, 100 observed rounds/h, chart + count insurance (the realistic
skill level; full menu and all knobs in `data/e16_ledger.py`):

| pattern | corr(bet,TC) | $/h | N0 | bankroll (5% RoR) |
|---|---|---|---|---|
| flat play-all (invisible) | 0.00 | −15.58 | — | — |
| flat + exit at TC ≤ −1 | 0.71 | +1.23 | 34,082h | $63k |
| 1-8 spread, play-all | 0.78 | +15.92 | 2,687h | $64k |
| 1-8 + exits | 0.84 | +32.73 | 605h | $30k |
| backcount, 8u at TC ≥ +2 | 0.68 | +43.54 | 543h | $35k |

The shape of the frontier: **camouflage and income trade almost linearly**,
and the exit (not playing bad shoes) is worth more than the spread itself.
corr(bet, TC) ≥ ~0.7 is intrinsic to every pattern that pays — the money IS
the correlation. What varies is where the tell lives: in the bet ramp
(seated spreads) or in the entry pattern (back-counting).

## Answer 3: the operating point (the part that's ours)

Table limits change the answer more than theory does. Two useful facts from
this session's sizing runs (heads-up weekday pace, 200 rounds/h):

**The TC +1 rung is free.** Its EV is −0.07%/round — breakeven to the noise.
So the graduated middle of a classical ramp ($40, $80 at low counts) buys
nothing: dollars bet below TC +2 are dead weight. The optimal seated shape is
**bimodal** — table minimum everywhere, then jump straight onto a curve that
starts high. Matt named it the *crouch*, and it beats the graduated play-all
1-20 on every column at once (+$57.65 vs +$54.44/h, smaller bankroll, lower
N0, corr 0.73 vs 0.78) while putting *less* total money on the felt.

**The chosen play — crouch + leave.** $10–$200 table, $10 flat at all counts
below +2, jump to $100/$150/$200 at TC +2/+3/+4, color up and wander at
TC ≤ −2 (sheds the worst 21% of rounds; infrequent enough to read as
restlessness, not as a system):

| pen | $/h | N0 | bankroll | corr |
|---|---|---|---|---|
| .70 | +$55.60 | 341h | $28.4k | 0.76 |
| **.75 (assumed)** | **+$67.45** | **255h** | **$25.8k** | **0.76** |
| .80 | +$92.01 | 151h | $20.8k | 0.76 |

### The card, explicitly

**Count:** plain hi-lo — 2, 3, 4, 5, 6 count **+1**; 7, 8, 9 count **0**;
tens, faces, aces count **−1**. True count = running count ÷ decks remaining
(half-deck estimation is fine). E4a showed hi-lo is the best balanced
level-1 count for this game, so the tags are not a compromise.

**Bet ramp, $10–$200 table** (thresholds are half-integers because the
priced bins are rounded TCs — "TC rounds to +2" means TC ≥ +1.5):

| true count | bet / action |
|---|---|
| TC ≤ −1.5 (rounds to −2 or worse) | **leave** — color up, wander, come back on a fresh shoe |
| −1.5 < TC < +1.5 | **$10** (the crouch) |
| +1.5 ≤ TC < +2.5 (rounds to +2) | **$100** |
| +2.5 ≤ TC < +3.5 (rounds to +3) | **$150** |
| TC ≥ +3.5 (rounds to +4+) | **$200** (table max) |

**Insurance:** take it at TC ≥ +3, never below. (The priced arm uses
composition-exact insurance, worth ≈ +$6/h of the total; the TC +3 index is
the standard human approximation and captures most of it.)

**Playing decisions:** straight basic strategy for 6-deck H17 DAS, every
hand, at every count. No playing indexes — their value was priced
separately (the `ceiling` rows) and deliberately left off this card.

Runner-up card, for reference ($15–$500 table, 1-16 + exits): $15 below
+1.5, then $45 / $120 / $180 / $240 at TC rounding to +1 / +2 / +3 / +4+,
leave at TC ≤ −0.5 — +$83.62/h on $31.4k, corr 0.81.

Runner-up: $15–$500 table, 1-16 spread + exits — +$83.62/h on $31.4k at pen
.75 — more money, but corr 0.81, twice the walking, and a rarer table. The
crouch matches its N0 (255h vs 251h) and its bankroll efficiency ($2.6/h per
$k for both) on the softest table in the house. Field judgment (Matt,
ex-floor supervisor at this property): low-limit games draw the least
surveillance attention — a $200 bet on a $10 game doesn't get watched; the
quarter tables do. That intel, not the model, is what breaks the tie.

**Penetration is the whole ballgame.** One row of cut-card depth (.70 → .80)
moves the chosen play from $56 to $92/h — more than insurance, deviations,
and ramp engineering combined. The pre-play recon list is therefore short:
cut depth, H17/S17 confirm, and whether the room deals $10–$200 heads-up for
hours on a weekday.

## Where it sits in the portfolio

| play | $/h | bankroll | N0 | camouflage |
|---|---|---|---|---|
| 21+3 quad-Q wong-in (E12) | ~$21 per $100 unit | $37k | 1,200h | side bet, odd but quiet |
| **BJ crouch+leave (E16)** | **~$67** | **$26k** | **255h** | good, perishable |
| EZ bac two-count (E14) | ~$92–101 per $100 unit | $81k | 582h | native, durable |

Blackjack earns the best dollars per bankroll-dollar and converges fastest —
on a ~$30k roll it is simply the biggest number. Its weakness is that the
income is *perishable*: one backoff ends it at that property, and the pattern
it wears is the one thing every pit is trained to see. The baccarat play is
the opposite — indistinguishable from ritual, scales to $100 units, needs
~$81k. The sequencing writes itself: **blackjack is the sprint, baccarat is
the annuity** — play the crouch while the room is asleep and the roll is
small, bank toward the baccarat stake, shift weight if sweat ever appears.

## Honesty section (assumptions that could move the numbers)

- **H17 6d DAS no-surrender, pen .75 are assumed, not confirmed** — the rack
  card item from M3 is still open. s17 shifts every EV +0.2% (verdicts
  unchanged); pen is priced above.
- Exits modeled as "cards keep flowing" (someone else plays the shoe).
  Heads-up that's wrong in the player's favor — walking to a fresh shoe
  beats idling at bet zero — minus table-hopping dead time.
- Rounds treated as independent for variance (live runs matched σ to three
  decimals, so this is fine at these spreads); 5% risk-of-ruin bankrolls,
  fixed stakes, no resizing.
- The tracker sees every dealt card including the dealer's hole card (the
  repo's perfect-information convention). For betting decisions this is
  nearly moot — hole cards are revealed at settlement before the next bet —
  but a visible-cards-only realism pass remains parked.
- Backoff/longevity risk is not modeled anywhere. It is the entire
  difference between this play and the baccarat play, and it is real.

## Provenance

Engine validated against published house edges before any of this (0.646%
measured vs 0.62% published, cut-card mode, H17; four batteries). E16 data:
148M banked rounds, seeds 8.9e9–13.3e9 step 1e8, `data/e16_*.json`; harness
gates in `tests/test_e16.py` (222 tests green); ledger
`data/e16_ledger.py <game> <pen> <unit$> <rounds/h>`; live verification runs
seeds 13.1–13.3e9. Commits `cadca88` → this one.
