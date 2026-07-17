# ride-free-sim

A seed-deterministic simulator and analysis toolkit for **Free Bet Blackjack**
("Ride Free"), built to answer one question honestly: *can this game be counted?*

**Read the write-up: [docs/ARTICLE.md](docs/ARTICLE.md)** — including the first
published effect-of-removal table for Free Bet blackjack and the **RF-L2** count
(A −2 · 5 +2 · 2/3/4/6 +1 · T −1) derived from it.

## What's here

- One rules-driven engine for standard blackjack and Free Bet (variants are
  configuration, never forked code) — validated against published house edges,
  dealer outcome tables, Griffin's EOR table, and the Wizard of Odds Free Bet
  figures before any novel claim was trusted.
- An exact player-EV calculator (arbitrary deck composition), effects-of-removal
  derivation, composition tracking, conditional-EV experiment harnesses, and a
  paired-differential deviation measurer.
- The full experiment log ([docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)): every
  result reproducible from (commit, command, seed) — including the blind alleys.

## Quickstart

```bash
uv run pytest -q                                       # 149 tests
uv run python -m ridefree.cli demo --rules ridefree --seed 44 --hands 6
uv run python -m ridefree.cli validate --rules ridefree --rounds 2000000
uv run python -m ridefree.cli signals --rules ridefree --rounds 1000000
```

Docs: [STATUS](docs/STATUS.md) · [DESIGN](docs/DESIGN.md) ·
[ROADMAP](docs/ROADMAP.md) · [EXPERIMENTS](docs/EXPERIMENTS.md) ·
[ARTICLE](docs/ARTICLE.md)

*For education and analysis. Casinos vary their rules; verify yours.*
