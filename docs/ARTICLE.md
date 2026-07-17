# Counting Free Bet Blackjack: Deriving the First Count for a Game Nobody Counts

*What 60 million simulated hands taught us about Ride Free — the Free Bet variant —
including its effect-of-removal table, a practical level-2 count, and an honest
answer to whether the game can be beaten.*

---

Free Bet Blackjack — dealt at Potawatomi Casino as **Ride Free** — makes an
irresistible offer: split any pair except tens *for free*, double any hard 9, 10,
or 11 *for free*. The casino puts up the money; you keep the winnings. The catch
funding it all: when the dealer busts with exactly 22, every live hand pushes.

The Wizard of Odds pegs the base house edge around 1.04% (six decks, H17, resplit
aces) — roughly a 6:5 game in cost. But nobody, as far as we could find, has
published an answer to the counter's question: **what happens to this game when the
composition of the shoe changes?** Every card counting system in the literature —
hi-lo, KO, Omega II, all of them — is tuned to *standard* blackjack's effects of
removal. Free Bet changes what cards are worth. So we built an open, seed-
deterministic simulator, validated it against every published number we could find,
and went looking.

This article is the full story, including the blind alleys, because two of them
turned out to be the most instructive parts.

## First, the credibility check

Nobody should trust a simulator's exotic claims until it reproduces boring known
facts. Ours passes this ladder:

- **Standard blackjack house edge:** 0.640% simulated vs ~0.62% published (6-deck
  H17 basic strategy); S17 variant 0.47% vs ~0.40%; off-the-top (CSM-style) runs
  match the published combinatorial figures almost exactly.
- **Dealer outcome tables:** bust probability for every up-card matches an
  independent exact calculator to within noise across 5M hands (e.g. 6-up: 43.93%
  vs 43.95%; ace-up: 13.87% vs 13.89%).
- **Free Bet itself:** simulated house edge 0.99% vs the published 1.04% under the
  Wizard's exact ruleset — and when we toggled resplit-aces off, our edge moved by
  0.081%, reproducing the Wizard's published 0.08% adjustment for that rule almost
  to the digit. The dealer-22 frequency came out 7.354% vs the published 7.3536%.
- **Effects of removal:** our derivation machinery, pointed at standard blackjack,
  reproduces Griffin's classic EOR table (*Theory of Blackjack*, p.44) in sign,
  order, and magnitude.

Rules assumed throughout: six decks, dealer hits soft 17, free split any non-ten
pair with free resplits to four hands, aces split once with one card each, free
double on hard two-card 9/10/11 including after splits, blackjack 3:2, dealer 22
pushes, 75% penetration, cut-card dealing.

## Blind alley #1: "bet more when the free bets are coming"

The intuitive system writes itself: free splits and doubles are where the value
lives, so track how likely they are and bet big when the shoe is rich in them.
Pair probability and hard-9/10/11 probability are both exactly computable from the
remaining composition, so we tested the *perfect-information* version — the upper
bound on what any human count of this type could do.

It fails, decisively — and the reason is the most important number in this game:

> **The correlation between free-double richness and the hi-lo true count is
> −0.94.**

Free doubles are built from small and medium cards. So is a *terrible* blackjack
shoe. The shoes where the free-bet machine fires most are precisely the shoes where
naturals vanish and the dealer stops busting. EV *falls* as free-bet frequency
rises. The free-bet signals are, almost perfectly, upside-down card counters.

## Blind alley #2 (the good one): the pair anomaly

Here's where it gets interesting. When we measured pair-richness *at a fixed hi-lo
true count* — asking what the pair signal adds beyond what a counter already knows
— we found a strong effect: about **+0.63% of EV per +0.01 of pair probability,
6.6 standard errors from zero across 15 million hands**, positive in all thirteen
count bands, and completely absent in a standard-blackjack control (where free
splits don't exist). It replicated across five independent seeds.

A real, novel, count-orthogonal signal? That's what we believed for a few hours.
The resolution is better than the discovery.

## The actual answer: this game needs its own count

The pair anomaly prompted the right question: *is hi-lo even the correct yardstick
here?* Hi-lo's tags are quantized effects of removal — for standard blackjack.
Free Bet's EORs have never been published. So we derived them, with the same
machinery that reproduces Griffin's table:

**Effects of removal, % per card removed from a 52-card deck:**

| Card | Standard (H17) | Free Bet | What changed |
|:---:|:---:|:---:|---|
| A | −0.52 | **−0.64** | more valuable: A-A is a free split, plus naturals |
| 2 | +0.40 | +0.40 | unchanged |
| 3 | +0.49 | **+0.20** | feeds 3-6, 3-7, 3-8 free doubles and 3-3 splits |
| 4 | +0.66 | **+0.32** | halved |
| 5 | +0.80 | **+0.53** | still the biggest, but slashed |
| 6 | +0.48 | +0.40 | mild |
| 7 | +0.28 | **+0.10** | nearly neutral |
| 8 | −0.02 | **−0.11** | *flips negative*: 8-8 is a free split you want available |
| 9 | −0.22 | −0.13 | less negative |
| T | −0.54 | **−0.23** | **halved** — dealer 22 is made of tens, and T-T can't free-split |

Two structural headlines. **The ace is worth nearly three times the ten** in Free
Bet — hi-lo weights them identically. And the small cards hi-lo leans on lose up to
half their value, because in this game they're not just dealer-helpers — they're
the raw material of your free doubles.

When we re-ran the pair analysis conditioned on the *correct* count (the exact
EOR-weighted composition signal), the +6.6σ pair effect collapsed to **−0.6σ —
clean zero.** The pair signal had been carrying linear composition information that
hi-lo mis-weights (mostly ten depletion and the ace/ten asymmetry). Priced
correctly, pairs add nothing. Blind alley — but the one that forced the count into
existence.

## The RF-L2 count: a practical version

The exact count needs a computer. The level-2 quantization doesn't, and it comes
out *naturally balanced*:

> **RF-L2:  A = −2 · 2,3,4,6 = +1 · 5 = +2 · 7,8,9 = 0 · T = −1**

Running count, divided by decks remaining, exactly like hi-lo. Its betting
correlation with the true Free Bet EORs is **0.966** — the same quality hi-lo
achieves against standard blackjack's EORs (0.963). Notably, the best *level-1*
count for Free Bet turns out to be… hi-lo itself (0.910) — ±1 tags simply cannot
express the ace/ten asymmetry, which is exactly what the second level buys you.
Empirically, across three million simulated rounds, the RF-L2 true count turns
positive around **+3**; a back-counter who sits only at **+5 or better** plays
about 6% of rounds at roughly **+0.7% per hand** — within noise of everything the
computer-perfect EOR count earns at the same frequency (+0.74%), versus +0.63% for
hi-lo on the identical shoes. The gain over hi-lo is real but modest; the point is
that two tag changes capture essentially the entire distance to perfect.

## So is the game beatable? The honest ledger

Cross-fitted bet ramps (thresholds chosen on one dataset, profit measured on
independent seeds), 1-to-8 spread, playing every hand:

| System | Edge on money wagered |
|---|:---:|
| Free Bet, hi-lo | −0.51% |
| Free Bet, hi-lo + pair side-signal | −0.40% |
| Free Bet, derived RF count | −0.37% |
| **Standard blackjack, plain hi-lo** | **+0.23%** |

**Seated play does not beat this game.** The ~1.1% cost of every waiting hand,
plus the rarity of good shoes (about 10% bettable, versus 36% for standard
blackjack at TC ≥ +1), swamps the counting gains under every system we could
construct — including perfect-information versions no human could execute.

What *does* work is *wong-in* — back-count and sit only when the count clears
threshold:

| Mode | Frequency | EV per played round |
|---|:---:|:---:|
| Free Bet, RF count ≥ moderate threshold | 14.5% of rounds | +0.48% |
| Free Bet, RF count ≥ strong threshold | 6.6% of rounds | +1.04% |
| Standard, hi-lo TC ≥ +2 | 19.8% of rounds | +1.09% |

Composition-based playing deviations (the Free Bet analogue of the Illustrious 18,
computed with perfect information) add another **+0.12% ± 0.05%** overall — only
about 2% of rounds change their play, but those rounds gain 5–6% each. Stacked
together, the best-known Free Bet system — back-count with RF-L2, sit at strong
threshold, deviate by composition — earns roughly **+1.2% per hand played on the
top ~7% of shoes.**

## Why bother, when regular blackjack pays more?

By raw EV, don't: the standard game next door offers three times the playable
volume at the same quality with a sixty-year-old count. Free Bet's case rests
entirely on what surveillance *can't see*:

- Its bet trigger correlates only weakly with the running count that
  counter-detection software tracks; a mid-shoe wong-in on an RF-count spike reads
  as a hunch player, not a counter.
- Nobody watches for it, because until now there was nothing to watch for.
- The free-bet mechanics also cut per-round variance (~1.07 vs ~1.16 bet units) —
  the casino absorbs your splitting and doubling downside.

Whether that camouflage is worth the EV discount is a professional judgment, not a
math question. Our contribution is the number on each side of the trade.

## Caveats, stated plainly

Rack cards vary: we assume six decks and H17 (both worth re-checking at your
table; S17 improves the player by ~0.31%). The EOR derivation uses the standard
infinite-deck, no-resplit approximations — good enough to reproduce Griffin, but a
resplit-aware refinement could sharpen the RF count slightly. Deviation value is a
perfect-information ceiling; human-executable rules will capture only part of it.
And all results are for the cut-card game at 75% penetration; deeper penetration
helps any count, shallower kills it.

Every number in this article regenerates from a seed-deterministic open simulator —
same seeds, same results, to the digit. The full source, experiment log, and banked
data are at **[github.com/mrwatts88/ride-free-sim](https://github.com/mrwatts88/ride-free-sim)**;
the validation suite, the EOR derivation, and every experiment here are one CLI
command each.

**A note on how this research was done.** This project was a collaboration between
the author and Claude (Anthropic's AI system), which implemented the simulator, ran
the statistical analyses, and drafted much of this article. The direction was
human: I posed the research questions, supplied the hypotheses that drove the two
key turns — that pair frequency might be exploitable, and that hi-lo's tags could
not be assumed valid for this game — demanded the controls and replications, and
judged what survived. The final claims are mine to defend, and the repository
exists so no reader has to take either of us on faith.

---

*This analysis is for education and entertainment. Nothing here is a promise of
profit; casinos change rules, and variance is crueler than any house edge.*