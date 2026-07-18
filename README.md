# ride-free-sim

A seed-deterministic simulator and analysis toolkit for blackjack variants and
side bets, built to answer one question honestly, twice: *can this game be
counted?*

**Two write-ups:**

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

## What's here

- One rules-driven engine for standard blackjack, Free Bet, and the 21+3 side
  bet (variants and paytables are configuration, never forked code) — validated
  against published house edges, dealer outcome tables, Griffin's EOR table,
  the Wizard of Odds Free Bet figures, and the exact 21+3 combination table
  before any novel claim was trusted.
- An exact player-EV calculator (arbitrary deck composition), effects-of-removal
  derivation, suit-aware composition tracking, a closed-form 21+3 EV calculator
  with exact decomposition, conditional-EV experiment harnesses, and a
  paired-differential deviation measurer.
- The full experiment log ([docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)): every
  result reproducible from (commit, command, seed) — including the blind alleys.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) (Python 3.12+ is fetched automatically).

```bash
uv run pytest -q                                       # 186 tests
uv run python -m ridefree.cli demo --rules ridefree --seed 44 --hands 6
uv run python -m ridefree.cli validate --rules ridefree --rounds 2000000
uv run python -m ridefree.cli signals --rules ridefree --rounds 1000000
uv run python -m ridefree.cli sbev --rounds 1000000    # 21+3 exact-EV ceiling scan
uv run python -m ridefree.cli sbtrack --rounds 1000000 # 21+3 human trackers scored
```

Docs: [STATUS](docs/STATUS.md) · [DESIGN](docs/DESIGN.md) ·
[ROADMAP](docs/ROADMAP.md) · [EXPERIMENTS](docs/EXPERIMENTS.md) ·
[ARTICLE](docs/ARTICLE.md) · [ARTICLE_21P3](docs/ARTICLE_21P3.md)

Built in human–AI collaboration: research direction, hypotheses, and final claims
by Matt Watts; implementation, analysis, and drafting with Claude (Anthropic).
See the notes at the top of [both](docs/ARTICLE.md)
[articles](docs/ARTICLE_21P3.md).

MIT licensed. *For education and analysis. Casinos vary their rules; verify yours.*
