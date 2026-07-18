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
to only ~22% at TC −8. (This is our measured, shoe-game echo of Peter
Griffin's classic "gain from perfect play" analysis in *The Theory of
Blackjack* — the same book whose EOR table our E4a derivation had to
reproduce before any of this was trusted.) Every player asymmetry (3:2
naturals, doubles, splits, the right to stand) is a ten/ace asymmetry, and
small-card shoes shrink the option value itself; perfect knowledge of a bad
shoe mostly tells you precisely how bad it is. Consequently the
perfect-camouflage play — flat bet, every round, forever — **loses $15.58/h
at $25 units, and even played with composition-perfect skill it loses
$11.72/h.** There is no skill route out of negative counts; there is only
not having money on the table when they happen. The holy grail is closed, by
measurement, on our own game.

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

### The no-division variant: the Red 7 card (E17)

For lower cognitive load the whole play runs on a raw running count — no
true count, no deck estimation, no division, ever. Count **Red 7**: hi-lo
tags plus **red sevens +1** (black sevens stay 0). The +2-per-deck imbalance
puts the count's *pivot* exactly on the crouch's jump threshold, so the one
decision carrying the money is depth-exact with a fixed number. E17 priced
it on 48M rounds against the hi-lo card on the same card stream:

| running count (start at **−12** each shoe) | bet / action |
|---|---|
| RC ≤ −14 | **leave** — fresh shoe elsewhere |
| −14 < RC < 0 | **$10** |
| RC ≥ 0 | **$100** |
| RC ≥ +2 | **$150** — and take insurance from here up |
| RC ≥ +5 | **$200** |

**+$59.07/h, N0 307h, $27.2k bankroll — 93.5% of the hi-lo card's hourly.**
About $4/h is the entire price of never dividing. Two supporting facts from
the same experiment: an exhaustive analytic search over the level-1
unbalanced family (our own EOR table, betting-correlation objective)
returns Red 7 *itself* as the optimum — Snyder's 1983 count is the ceiling
of its class, so there is no better custom to chase — and KO, the popular
alternative, retains 88% but with a higher bankroll, worse correlation, and
no workable leave threshold (its pivot sits at TC +4, off the money
decision). Threshold tolerance is wide (±1 point moves retention only a few
points); nothing about the card is knife-edge.

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

### Post-recon addendum (same day)

Floor recon (a Saturday) found four **$15–$1,000** tables at pen ≈ .75 —
one cut a full deck deeper (~.83) — and no $10 games that day. The card
adapts without redesign: keep the SAME $100/$150/$200 jump curve on a $15
floor ("crouch15" in the ledger) — the floor toll is +$3.50/h, the jump
bankroll is unchanged. Priced from the banked bins: **+$63.95/h on $27.7k
at pen .75; +$88.97/h on $21.8k at pen .80** (hi-lo; Red 7 ≈ ×0.935). The
$1,000 max is the growth path — double the jumps at a ~$55k roll. The
deep-cut table is the prize seat (and the condition that would wake a 21+3
overlay, worth ~$17–42/h more depending on cut — E12 numbers, side-max and
cognitive load pending). Last big unknown: weekday pace — every $/h here
assumes ~200 rounds/h heads-up; a crowded table pays a third.

### The locked card (E18 addendum, same day): two rungs, and zero is the exit

Drilling the Red 7 card in the trainer surfaced two practicality problems the
$/h tables don't show, and both trace to one identity: **RC ≈ decks-remaining
× (TC − 2)**. Off-pivot thresholds are depth-blurred — the −14 leave meant
TC −0.4 early in the shoe (measured: abandoning 73% of shoes, 3.4 walks an
hour, median exit round four — conduct no $15 player can sustain), while the
rungs crowd together as the shoe depletes. Pricing the collapse from the
banked bins settled it: 74% of the insurance value lives at the top rung
(and "insure at +2" takes theoretically bad insurance early-shoe, TC +2.4
against the true +3 index), the middle bet rung buys ~5% of the hourly, and
the leave can deepen to a once-every-35-minutes walk for ~$3/h — less than
the walking friction the ledger never charges.

The locked card, with the whole scale slid +18 so no number is ever
negative — zero is simply the eject line:

> **Start each shoe at +6. If the count ever hits 0, color up and walk.
> $100 at 18. $200 — and take insurance — at 22.** $15 floor everywhere
> else; straight basic strategy; red sevens +1; never divide anything.

(In the old pivot scale: IRC −12, leave ≤ −18, jump at 0, max and insure at
+4. The jump threshold, 18, is the depth-exact pivot = TC +2.)

E18 then certified the *literal* card — 12M live rounds of chart play, bet
by running count, sit-out at the line, and the human insurance rule —
against the bin arithmetic: chart-only agreement z = +0.89, rung occupancy
matching to a tenth of a percent, and the first *measured* value of the
"insure when the max bet is out" rule: **+$4.67/h, 73% of the
composition-exact ceiling**. Operating numbers: **≈ +$44/h ± 2 at 200
rounds/h heads-up, N0 ≈ 500h, ~$36k bankroll at 5% RoR, 1.7 walks/h.**
About $10/h of the 3-rung card's paper value buys: one fewer bet rung, one
fewer memorized number, insurance welded to the max bet, a third the
walking, and a count that never goes negative. Human error is the biggest
edge-killer this model doesn't price; the card was collapsed accordingly.

The growth path got cleaner too: at a ~$42–52k roll the right card is
*simpler still* — $200 flat at the pivot (one number), worth 116% of the
3-rung card with walks, or 94% with no walking at all. After that:
playing deviations, then an insurance side count — in that order, only
once the drill-room error rates say the current card is clean.

**E18b, the last word on walking:** a second 12M-round certification of the
same card with *no leave at all* settled the weekday question. The leave's
exact same-shoe value is $5.83/h; the walking it takes to collect it
refunds $2.50–6/h in dead time first. So the walk line is **advisory**:
weekday mode plays every round (**≈ +$40/h ± 2 on ~$36–40k, zero walks,
one less thing to execute**); walk at zero only when a fresh shoe is
genuinely adjacent. The same measurement run mapped the card's second
life: 85% of jump rounds arrive 2+ decks deep and 60% of shoes ripen
(median entry round 24, then ~12 hot rounds), so the card's top half —
sit when a watched shoe hits 18, play $100/$200, leave at the shuffle —
doubles as a busy-room back-counting play (~$65/h per 200 observed rounds
on a $23k roll; $20–29/h at real crowded-table pace, wearing the wong
entry pattern). One count, one card, three modes.

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
measured vs 0.62% published — Michael Shackleford's Wizard of Odds figures,
as everywhere in this repo — cut-card mode, H17; four batteries). E16 data:
148M banked rounds, seeds 8.9e9–13.3e9 step 1e8, `data/e16_*.json`; harness
gates in `tests/test_e16.py` (222 tests green); ledger
`data/e16_ledger.py <game> <pen> <unit$> <rounds/h>`; live verification runs
seeds 13.1–13.3e9. Commits `cadca88` → this one.
