# Paradigm 2 — beating the implementation of randomness

Opened 2026-07-19 (Matt's question: "is there something else we're not thinking
of?"). This document is the strategic map for the project's second life. Read it
the way ROADMAP.md M0 was read in paradigm 1: it defines what we are attacking,
why, what "winning" means, and the honesty rules that keep us from joining the
long tradition of people who fooled themselves in exactly this territory.

## Why a second paradigm

Everything the project has beaten — Ride Free wong-in, 21+3, Dragon 7/Panda 8,
Pot of Gold, crouch15 — is one theorem instantiated five times: **a shoe is a
state machine with visible state decay; condition the bet on the state.** Within
this class every quantity is enumerable, the true EV is computable by us, the
casino, and every AP with a laptop, and consequently every edge is (a) small,
(b) published or publishable, and (c) defended by design (cut cards, CSMs,
side-bet maxes, backoffs). The project's own history states the ceiling: our
best verdicts are tens of dollars an hour on five-figure bankrolls, and the
best games got shelved on operational texture, not math.

The organizing principle for what comes next:

> **An edge is a gap between the true price and the price the counterparty
> acts on.** In an enumerable game the counterparty acts on the true price, so
> edges exist only via state visibility (paradigm 1) or arithmetic mistakes
> (the M10a P(0) refutation — we found one). In a non-enumerable game NOBODY
> holds the true price — the counterparty acts on an estimate, and the edge is
> the superiority of your estimate. Such edges are **renewable** (they cannot
> be published as *the* answer and burned out the way hi-lo was) and they
> **compound** (more data and better models widen the gap monotonically).

The money agrees with the theory: the largest verified gambling results in
history — Benter's pari-mutuel modeling, the lottery syndicates, top poker —
are all in non-enumerable games. The enumerable hall of fame tops out around
Don Johnson's $15M, which was a *contract* edge, not a card edge.

## The taxonomy (where an edge can live at all)

Recorded in full so future sessions don't re-derive it. Six structurally
distinct asymmetries; paradigm 1 was class 1.

| # | Class | Edge mechanism | Status for us |
|---|---|---|---|
| 1 | State/memory games (shoes, meters, persistent machines) | re-price mid-process on visible state | **Paradigm 1 — mined, written up, largely shelved on texture** |
| 2 | Physical implementation of "random" (shuffles, wheels, dice) | the uniformity assumption is false; infer the residual structure | **CHOSEN — Track A (shuffle forensics)** |
| 3 | Human implementation (hole-card flashes, tells, dealer error) | information leaks at the interface | parked — priceable later via the "value-of-information atlas" idea |
| 4 | Negotiable payoff functions (loss rebates, promos, comps) | the contract mispriced vs. an optimizer (Don Johnson) | parked — natural reuse of E24/E25 stopping machinery if a promo appears |
| 5 | Pari-mutuel / peer pools (racing, lotto rollovers, poker) | beat the crowd's estimate, not the house | parked — different domain, biggest historical prizes, heaviest ops |
| 6 | Data-scale observation (live-dealer broadcast outcomes) | operators publish enough data to audit their own physics | **CHOSEN — Track B (live-dealer QC)** |

Matt's selection criterion, on record: he loves **beating the randomness
itself** — classes 2 and 6, which are really one idea at two ranges: class 2 is
inference on a physical mixing process you observe in person; class 6 is the
same inference run at internet scale on processes the operators broadcast.

## The "too hard a fight?" question, answered

The worry: shuffling machines (Shuffle Master / Light & Wonder) already
"understand this problem," and nobody shuffles by hand. Three answers, held
with the confidence the research pass below supports:

1. **The premise is historically false.** The one time a first-rank
   mathematician was allowed inside a flagship machine (Diaconis/Fulman/
   Holmes, *Analysis of Casino Shelf Shuffling Machines*, ~2013), one pass was
   NOT random: a feedback guessing strategy roughly **doubled** correct
   next-card guesses vs. chance. The manufacturer's in-house engineers had
   believed it was fine ("we are not pleased with your conclusions"). A decade
   later IOActive tore open the Deck Mate 2 at DEF CON 2023. Every rigorous
   look at casino randomization infrastructure has found something; the
   scarce input is rigorous people looking, not exploitable structure.
2. **Machines standardize the leak.** A hand shuffle is a new stochastic
   process every dealer; an automatic shuffler runs the same physical program
   in thousands of pits. Characterize one model once, apply everywhere.
   Machines make forensics MORE tractable, not less.
3. **We are the auditor, not the competitor.** They must make every machine
   sufficiently random under speed/cost/jam-rate pressure (casinos buy
   shufflers for hands-per-hour — the economics push toward minimum
   acceptable mixing). We need ONE model, one firmware era, one lazy
   procedure with detectable structure. Auditing is cheap; engineering is
   expensive.

## Track A — shuffle forensics (M12)

**Hypothesis:** real shuffle procedures (machine and hand) leave measurable
mutual information between the observed order of shoe *k* and the dealt order
of shoe *k+1*, and some of it converts to betting edge under honest human
constraints (memory only, no devices).

**Why our toolkit is the right lab:** the deterministic engine gives synthetic
ground truth. We implement the physical shuffle as a stochastic process,
deal shoes through it, and measure — with exact knowledge of what structure
went in — what any inference scheme can recover. That is **non-enumerable
room with an enumerable gate**: the inference target is messy reality, but
every method is validated against a known-truth simulator before a single
real-world assumption enters. No other class offers that bridge.

**The ladder is M12 in ROADMAP.md.** The first rung is pure desk work: model
the Diaconis shelf shuffler, reproduce the published guessing numbers as the
gate, then convert guessing advantage into blackjack/baccarat betting edge —
a number nobody has published.

**Legal line (bright, on record):** memorized precomputed strategy and
observation are legal everywhere we care about; any device used at the table
to track or predict is a felony in Nevada (NRS 465.075) and equivalent
elsewhere. All Track A output must be executable by an unaided human, or it
is a paper result only. Machine tampering (the DEF CON path) is cheating —
we cite that work as evidence about engineering quality, never as a method.

### The poker dual-attack (Track A × class 5) — Matt, 2026-07-19

Matt's interjection, recorded because it is the strongest single idea in
this document: **poker's shuffler is literally in the table, and the game is
class 5 (peer pool), so shuffle forensics has a second, richer payoff
function.** The casino poker room deals from a single-deck automatic
shuffler in the table well (the Light & Wonder Deck Mate / Deck Mate 2 line
— the exact unit IOActive opened at DEF CON 2023). Why the fusion is worth
more than shuffle-tracking a house game:

1. **The house doesn't care who wins.** Poker's house takes a fixed rake and
   is structurally indifferent to the outcome. There is no house edge to
   shave and — critically — no pit boss backing you off *for winning*. The
   adversary is the other players, who are betting as if the deck were
   uniform. Any residual shuffle structure is private information used
   against them, and in a zero-sum betting game private information
   **compounds through the betting**, rather than nudging a fixed edge the
   way it does in blackjack.
2. **Single deck, high observation bandwidth.** 52 cards, not a 6–8 deck
   shoe — a single riffle/shelf pass leaves proportionally more recoverable
   structure, and it is the simplest possible shuffle model to build first.
   And the reshuffle input is partly *observed*: cards land in the muck and
   the collected pile in hand-correlated clumps (the classic clump-tracking
   substrate), and stud variants expose many upcards. The information going
   INTO the next shuffle is partly visible, which is exactly what a
   forensic prior needs.
3. **It is the natural place class 2 and class 5 meet.** The taxonomy listed
   class 5 as parked "different domain, heavy ops." This is the bridge: the
   physics work (Track A / M12) produces the deck prior; the peer-pool
   payoff (class 5) is what makes even a weak prior pay. No horse-racing
   database or lottery-pool logistics required — the venue is the same
   casino floor we already know.

**Honest flags carried with the idea (do not let its appeal skip the gates):**
- **Legality is grayer here and does NOT inherit the blackjack answer.**
  Observation + memory is still device-free, but poker rooms police
  advantage play and (far more seriously) collusion; "predicting the
  shuffle" may violate house rules even where it isn't a crime, and the
  optics of a lone player exploiting deck order at a table of humans differ
  from beating a house game. This needs its own legality pass before any
  play framing — treat it as a research question, not a settled line.
- **The observation is partial.** In hold'em most opponents' cards muck face
  down, so the inference input is incomplete — a real modeling constraint
  the synthetic gate must respect (don't let the simulator "see" cards a
  live player couldn't). Stud exposes more; the variant matters.
- **The Deck Mate claims casino-grade mixing.** Whether one of its passes
  actually leaves exploitable single-deck structure is precisely the M12
  question — now with a poker payoff attached. If M12 finds the machine
  mixes well, the dual-attack dies with the rest of Track A on that model.

**Muck structure enriches the forensic input (Matt, 2026-07-19) — and it
repairs the "partial observation" caveat above.** Two poker-specific facts
make the pre-shuffle stack unusually *known*, not unusually hidden:

- **Pre-flop folds are a strategically sorted sample.** Players fold low /
  disconnected / unsuited cards and play high cards, pairs, and suited
  connectors, so the pre-flop muck is systematically ten-poor and
  low-card-rich — NOT a random handful. The faces are hidden but the
  *distribution* is nearly known: a pre-flop fold is a near-determined
  object. This directly repairs the earlier flag ("cards muck face down, so
  input is partial") — the input is partial in identity but constrained in
  distribution.
- **Later-street discards are anti-correlated with the board.** People fold
  hands that missed. Conditioned on the (fully observed, face-up) community
  cards plus the betting action, the muck at each street has an estimable
  distribution that AVOIDS the board's ranks/suits, while cards surviving to
  showdown ECHO them. "Unknown folded cards" becomes "cards drawn from a
  board-conditioned distribution we can write down."

**The mechanical crux:** the dealer gathers the deck in hand-structured order
(muck pile → board → hole cards), so cards enter the pre-shuffle stack
clumped by hand-role, and hand-role is correlated with board relationship.
The stack going INTO the shuffler therefore carries both compositional
structure (fold selection) and sequence structure (gather clumping) — and
it is structure the seated player largely observed or can infer.

**The reframe this forces on ALL of Track A (general, logged here because
poker is where it first bites):** shuffle quality is conventionally measured
as distance-from-uniform starting from an *arbitrary* deck. But the edge is
not that — it is I(player's knowledge of the input order ; output order). A
richer, more-known input yields more recoverable information **at the same
machine quality.** Poker hands you an unusually well-known input stack, so a
Deck Mate pass that would look adequate starting from a scrambled deck can
still leave an exploitable posterior starting from poker's structured,
observed stack. The synthetic gate must therefore model I(observation ;
output), never the textbook total-variation-from-uniform.

**New caveat this introduces:** the poker arm's numbers become conditional
on a **player-strategy model** (the fold distribution is behavioral — loose
vs. tight tables, stakes, and street-by-street continuance all move it).
Unlike the blackjack arm (behavior-free), the poker arm models humans — a
genuine "non-enumerable bites here" point. The strategy model is
parameterizable data (fold ranges by position/street), and its assumptions
must be stated with every poker-arm result.

**Where this lands in the plan:** it does not reorder the ladder — M12a still
starts with the Diaconis shelf model and its exact gate, because the physics
must be proven recoverable at all before any payoff function matters. But it
adds a **poker payoff arm to M12b** (convert recovered structure to edge
under BOTH a blackjack/baccarat house-game payoff AND a heads-up/ring poker
equity payoff), and it revives class 5 from "parked" to "live via the poker
bridge." The poker arm's synthetic gate must model (i) a parameterized
player-strategy fold model that makes discards non-random, (ii) the dealer
gather procedure that orders the pre-shuffle stack, and (iii) a seat's
realistic observation set (own cards + board + shown cards + the strategic
prior on unseen cards) — the simulator must never "see" a card a live
player couldn't. The Deck Mate / poker-room shuffler is already in the M12a
research scope (the shuffler-landscape pass covers it).

## Track B — live-dealer data QC (M13)

**Hypothesis:** live-casino studios broadcast physical outcomes (roulette
spins, baccarat cards) continuously; at that volume, statistical QC can
detect wheel bias or shuffle deficiency from a desk, legally, on data the
operator publishes voluntarily.

**The roulette arithmetic that makes it interesting** (why the bar is low):
European straight-up pays 35:1, so the breakeven pocket probability is 1/36
vs. fair 1/37 — a pocket needs only **+2.8% relative frequency to break
even** (+5.6% American). Detection cost (binomial, 3σ, single pocket):
roughly **8k spins for a +20%-relative pocket (EV ≈ +17%), ~32k for +10%
(EV ≈ +7%), ~400k to resolve near-breakeven**. A 24/7 studio wheel does
~800–2,000 spins/day, and wheels are screened in parallel — so strong bias
is a ~one-week detection per wheel, and a fifty-wheel screen is a real
pipeline, vs. months of standing at one physical wheel clocking by hand.
Two honesty clauses built in from paradigm 1 discipline: (a) screening many
wheels and betting the best-looking is the E20 winner's-curse setup —
**screen in-sample, confirm on fresh spins, always**; (b) multiple-testing
control across 37 pockets × N wheels is mandatory arithmetic, not optional.

**Bias survives online; ballistics don't.** Betting closes before/at ball
launch in live studios, so dealer-signature and visual-ballistics play is
physical-casino-only. Static wheel bias doesn't care when bets close.

**Baccarat is the sleeper dataset:** every card dealt is exposed (full
observability, unlike blackjack's hole cards), studios deal thousands of
shoes/day, and full histories may be accessible — the best shuffle-QC
dataset in the world if the data is really there. This is where Track A and
Track B meet: a Track A machine model predicts WHAT structure to test for in
Track B data.

**The gating unknown is data access** — hence M13a (the data-source audit)
is a research gate, not a code gate. Findings from the first research pass
below; the honest kill criterion: if per-wheel histories with timestamps
aren't obtainable at ~10⁴–10⁵ spins/wheel, Track B dies quickly and cheaply.

## Research pass findings (2026-07-19)

Two parallel research agents; every load-bearing claim was fetched from a
primary source (papers, vendor pages, the IOActive report, GLI-29, tracker
pages) and labeled VERIFIED / REPORTED / LORE in the raw dumps. Distilled:

### A. The shuffler landscape (Track A's physics targets)

- **Vendor near-monopoly.** Light & Wonder (ex-Scientific Games / SHFL /
  Shuffle Master) makes essentially every major table shuffler: DeckMate 2
  (single-deck, poker), i-Deal (single-deck, carnival), MD3 / MDX
  (multi-deck, baccarat/blackjack), one2six / ShuffleStar (CSMs). No
  material competitor. **The forensic axis is batch vs. continuous:** batch
  machines shuffle a full stub and behave like a hand shuffle of equal
  penetration (trackable IF the mix is weak/single-pass); CSMs recycle
  discards continuously and give a tracker ~zero penetration (dead by
  design — do not attack).
- **Diaconis is real and exactly quantified** (Ann. Appl. Probab. 23(4),
  2013; arXiv 1107.2961, read in full): a ten-shelf machine, one pass, let
  a feedback player guess **≈ 9.5 of 52 cards vs. ≈ 4.5 by chance**; color
  changes 17 vs. 26 uniform. **Fix: run it twice** (≈ 200-shelf ≈ 8–9
  riffles). Manufacturer president: *"We are not pleased with your
  conclusions, but we believe them."* Still an active math topic (Ottolini
  & Chen 2024 prove a cutoff at (5/4)·log₂₁₀ n). (Precision note from the
  M12a build, 2026-07-19: the "9½" is the intro's rounding — the paper's
  own Table 2 Monte Carlo says **mean 9.3, variance 4.7** under the
  conjectured-optimal strategy, Table 1 gives exact TV/sep/l∞ per shelf
  count, and Corollary 4.2 makes two passes EXACTLY a 200-shelf machine.
  E26 gates on the tables, not the abstract.)
- **THE SOBERING FINDING — the flagships appear to have absorbed the
  lesson.** MD3 does **seven** full riffles, explicitly citing Diaconis.
  IOActive's 2023 teardown ("Shuffle Up and Deal," read in full) found the
  DeckMate 2's *uncompromised* shuffle computes a **full target permutation
  up front from a PRNG** IOActive judged "sufficiently unpredictable" — no
  measured mix bias; their story was a **USB-implant tampering** attack
  (reads the machine's own card-scanning camera), which is cheating and
  strictly off our path. The DeckMate 1 uses a weaker seeded LCG; the flagged
  weakness across the line is **PRNG-seed entropy, not mechanical mix** — and
  seed-prediction is a device/computation attack, not human observation.
- **Certification is permissive.** GLI-29 (read) requires randomness but
  says the lab *"may"* apply named statistical tests to 99% confidence — an
  RNG-quality clause bundled into a heavy functional/security check, **not a
  mandated large-N audit of the physical output permutation.** Cert reports
  are private.
- **The opening, stated honestly.** There is **no public output-distribution
  data on any named modern machine, and no published measured legal edge
  against one.** The live *legal* targets are therefore: (i) **hand
  shuffles** (still prevalent in high-limit blackjack and baccarat — players
  distrust CSMs), and (ii) **weak / old / single-pass batch machines**.
  Which of these sits on a given floor is a **recon question**, exactly like
  paradigm 1's rack-card checks. Snyder (LVA 2022) relays one credible-but-
  unverifiable claim of a European AP who tracks "one specific model" — lore,
  but a proof of concept that the vacuum may hide a real target.

### B. The live-dealer data channel (Track B)

- **In-client history is shallow, trackers are capped, no API exists.**
  Evolution's own client exposes up to **500 past spins** per roulette table
  (~7–12h of one wheel). Third-party trackers (CasinoScores, Tracksino)
  cover only **flagship tables** (Lightning/Immersive/Auto class, not the
  ordinary wheels) with a **1h–72h** ceiling, **no export, no API.** No
  public API, Kaggle, or academic dataset of real live outcomes exists — a
  long per-wheel archive means **collecting it yourself** (~25–75k
  spins/wheel/month, auto-wheels highest).
- **Two hard walls specific to online roulette bias.** (i) **Betting closes
  before/at ball launch everywhere** → only *static wheel bias* is
  exploitable online (ballistics/signature are physical-casino-only —
  confirmed). (ii) The auto-wheels are actively **anti-bias engineered**:
  the Cammegh Slingshot 2 (behind Evolution Auto/Speed) has GLI-approved
  **Random Rotor Speed** randomizing rotor speed every spin, and studios
  **rotate/monitor wheels** (TCS sells "Drop Zone Detection" analytics).
  They are watching for bias from the inside. Only **one thin prior-art
  paper** exists (arXiv 1609.09601, 10,980 spins off a Riga wheel, OU-process
  claim, not peer-reviewed); **no biased online studio wheel has been
  publicly documented.**
- **Access friction.** The best aggregator (casino.org) **bars automated
  access in its ToS §6.d** (exact quote fetched) and several sites in the
  niche return Cloudflare 403 to bots. Watching is free (Evolution's demo
  showcase; embedded tracker streams); *archiving at scale* is the hard part.
- **Baccarat is outcome-level only in public tools.** Trackers expose
  P/B/T/pairs per shoe but **not card-level** data; full card logs would
  require **OCR on the video stream**. Shoe boundaries aren't marked.

### Synthesis — the recalibration and the convergence

**Recalibration (honest):** the bull case in "the too-hard-a-fight question"
survives but narrows. The *flagship* modern machines (MD3 7-riffle, DeckMate
2 computed-permutation) look adequate on the available evidence — the poker
dual-attack's physics premise is weakest exactly against a good DeckMate 2,
because a well-seeded full-permutation shuffle leaves ≈ 0 residual regardless
of how structured the input is (Matt's "richer input → more recoverable MI"
reframe only cashes when the permutation is *imperfect* — an older DeckMate
1, a weak batch pass, or a hand shuffle). So Track A's real targets are hand
shuffles and weak/old batch machines, and the deliverable of M12 is **the
method plus the number** (what edge does an N-pass mix / a given hand
procedure leak, and what does it take to recover it as a human) — with recon
deciding whether a live target exists. This is the paradigm-1 pattern exactly:
build the lab, prove the method, let the floor decide.

**Convergence (the exciting part): live-dealer baccarat is where both tracks
meet.** Evolution deals baccarat from an **8-deck shoe, changed after 7 decks,
MANUALLY shuffled by a dealer's assistant at the table** (VERIFIED). That
single game is simultaneously: a **hand shuffle** (Track A's cleanest legal
physics target, no machine-mixing to defeat), **fully card-observable** (every
card face-up — the richest possible forensic input, unlike blackjack's hole
card or poker's muck), **broadcast 24/7** (Track B's data channel), and
**high-volume** (~20–30 shoes/day/table across dozens of tables). The one
gap is that public tools give outcome-level, not card-level, data — closing
it needs video OCR. **This is the concrete instantiation of the doc's "Track
A model predicts what Track B tests for": build the hand-shuffle forensic
model in the engine (M12), and it tells a baccarat collector exactly which
inter-shoe structure to OCR for (M13).**

## Ordering decision

**M12 (shuffle forensics) first, starting with the fully synthetic rung
M12a.** The research pass makes this clear-cut:

1. **Track B's external dependency is confirmed expensive and gated.** No
   API, 72h/500-spin public caps, ToS/Cloudflare barriers, self-collection
   required, and the online-roulette-bias arm specifically faces engineered
   countermeasures (RRS) and undocumented wheel rotation. It is not dead, but
   its cheapest honest form (baccarat shuffle-QC via OCR) *depends on the
   Track A model to know what to look for* — so it sequences after M12
   regardless.
2. **Track A's first rung has zero external dependency and an exact gate.**
   M12a is desk work: implement the Diaconis shelf model in the engine,
   reproduce ~9.5/52 as the hard gate, then measure what N-pass mixing and
   hand-shuffle procedures leak — synthetic ground truth, engine-native, in
   this repo's exact idiom.
3. **The M13a data audit is effectively already done** by this research pass
   (findings above). Its verdict: no clean public archive; roulette-bias arm
   demoted by RRS + rotation + access friction; the live opening is
   hand-shuffled live baccarat via OCR, which waits on M12's method.

So: **build M12a now.** M13 is reframed around the baccarat convergence and
parked behind M12b (it needs the model first). The roulette-bias arm stays on
the board as a lower-priority, higher-friction option, not the lead.

## Epistemic doctrine for paradigm 2 (non-negotiable)

Paradigm 1's gates checked us against exact answers. Paradigm 2 has no exact
answers — this territory is FULL of unfalsifiable claims (dice setters,
wheel-system sellers, trend bettors) precisely because nothing enumerable
contradicts them. Our moat is that we bring gates anyway:

1. **Synthetic ground truth first.** No inference method touches real data
   until it provably recovers known structure planted by the deterministic
   engine.
2. **In-sample/out-of-sample separation, always.** Screening and confirmation
   never share data (the E20/E22 pattern, now load-bearing).
3. **Multiple-testing arithmetic is part of every claim.** A "biased wheel"
   headline must state the number of wheels and pockets scanned.
4. **Effect sizes in dollars, ledger-style.** A statistically-real bias that
   nets $4/h is a paradigm-1 mistake we don't repeat: texture and ops costs
   go in the verdict (the M10/M11 lesson).
5. **Kill criteria stated in advance** — each milestone's gate says what
   result kills the track, and we honor it (the sit-out-card precedent).

## Doc conventions for paradigm 2

Same machinery as paradigm 1: milestones and gates in ROADMAP.md (M12+),
experiments logged newest-first in EXPERIMENTS.md (E26+), STATUS.md remains
the single resume document, articles when a track reaches a verdict. This
file holds the strategy and taxonomy so STATUS can stay operational.
