# ride-free-sim

A seed-deterministic simulator and analysis toolkit for casino card games and
side bets, built to answer one question honestly, four times over: *can this
game be counted?*

**Four write-ups:**

- **[docs/ARTICLE.md](docs/ARTICLE.md)** — Free Bet Blackjack ("Ride Free"):
  the first published effect-of-removal table for the game and the **RF-L2**
  count (A −2 · 5 +2 · 2/3/4/6 +1 · T −1). Verdict: beatable only at the
  margin, and dominated by standard blackjack next door.
- **[docs/ARTICLE_21P3.md](docs/ARTICLE_21P3.md)** — the **21+3 side bet**
  (flat 9:1): exact closed-form pre-deal EV, an exact suit/rank/interaction
  decomposition, and **quad-Q** — a four-suit-count human system with analytic
  thresholds capturing 78% of the perfect-play ceiling. Verdict: genuinely
  beatable at deep penetration, wonging in — and it stacks with hi-lo instead
  of losing to it.
- **[docs/ARTICLE_EZBAC.md](docs/ARTICLE_EZBAC.md)** — the **Dragon 7 and
  Panda 8** at EZ Baccarat: exact enumeration ceiling, optimal counts derived
  from first principles (reproducing the published tags digit-for-digit), and
  a verified two-count scorecard system capturing ~87% of it. Verdict: the
  strongest in this repository — ~4× the 21+3 hourly at half the N0, toll-free
  by the structure of baccarat, at the house's own standard penetration.
- **[docs/ARTICLE_BLACKJACK.md](docs/ARTICLE_BLACKJACK.md)** — **standard
  blackjack**, deliberately a summary rather than a discovery: a per-true-count
  EV/variance curve, proof-by-measurement that playing skill cannot rescue
  negative counts (~9% of the deficit at best), and a cover-vs-money ledger
  pricing real betting patterns in $/h, N0, bankroll, and corr(bet, TC) —
  including the *crouch*, a bimodal min-bet-then-jump shape that beats
  graduated ramps on every column because the TC +1 rung is breakeven.

## What's here

- One rules-driven blackjack engine for standard blackjack, Free Bet, and the
  21+3 side bet, plus a small rules-driven baccarat engine (variants and
  paytables are configuration, never forked code) — validated against
  published house edges, dealer outcome tables, Griffin's EOR table, the
  Wizard of Odds Free Bet figures, and the exact 21+3 and baccarat
  combination tables before any novel claim was trusted.
- An exact player-EV calculator (arbitrary deck composition), effects-of-removal
  derivation, suit-aware composition tracking, closed-form 21+3 and
  Dragon 7 / Panda 8 EV calculators with exact decomposition, conditional-EV
  experiment harnesses, a paired-differential deviation measurer, per-TC
  curve banking with variance, and a live bet-ramp simulator with a
  dollar-denominated cover-vs-money ledger (`data/e16_ledger.py`).
- The full experiment log ([docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)): every
  result reproducible from (commit, command, seed) — including the blind alleys.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) (Python 3.12+ is fetched automatically).

```bash
uv run pytest -q                                       # 222 tests
uv run python -m ridefree.cli demo --rules ridefree --seed 44 --hands 6
uv run python -m ridefree.cli validate --rules ridefree --rounds 2000000
uv run python -m ridefree.cli sbev --rounds 1000000    # 21+3 exact-EV ceiling scan
uv run python -m ridefree.cli sbtrack --rounds 1000000 # 21+3 human trackers scored
uv run python -m ridefree.cli bacexact                 # exact baccarat table
uv run python -m ridefree.cli bacev --rounds 100000 --penetration 0.966
uv run python -m ridefree.cli bactrack --rounds 100000 --penetration 0.966
uv run python -m ridefree.cli curve --rules h17 --arm ins --rounds 1000000
uv run python -m ridefree.cli ramp --rules h17 --arm ins \
    --ramp "-0.5:1,1.5:10,2.5:15,3.5:20"               # live bet-ramp simulator
uv run python data/e16_ledger.py h17 p75 10 200        # the cover-vs-money menu
```

Docs: [STATUS](docs/STATUS.md) · [DESIGN](docs/DESIGN.md) ·
[ROADMAP](docs/ROADMAP.md) · [EXPERIMENTS](docs/EXPERIMENTS.md) ·
[ARTICLE](docs/ARTICLE.md) · [ARTICLE_21P3](docs/ARTICLE_21P3.md) ·
[ARTICLE_EZBAC](docs/ARTICLE_EZBAC.md) ·
[ARTICLE_BLACKJACK](docs/ARTICLE_BLACKJACK.md)

Built in human–AI collaboration: research direction, hypotheses, and final claims
by Matt Watts; implementation, analysis, and drafting with Claude (Anthropic).
See the notes at the top of each article.

MIT licensed. *For education and analysis. Casinos vary their rules; verify yours.*
