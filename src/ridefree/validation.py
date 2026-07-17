"""Validation engine: a battery of metrics checked against references with CIs.

Matching one house-edge number is weak evidence — an engine with two offsetting bugs
can still land on it. This runs a battery and reports each metric pass/fail/no-ref.

Reference sources, in order of trust:
1. The exact dealer-odds calculator (`dealer_odds.py`), an independent computation
   path. The dealer distribution from the real engine (Monte Carlo) must agree with
   it cell by cell — the most bug-sensitive check we have.
2. Computed constants (e.g. the fresh-shoe natural rate from deck composition).
3. Published figures (Wizard of Odds) for the headline house edge and variance.
"""

import math
from dataclasses import dataclass

from ridefree import dealer_odds
from ridefree.cards import ACE, TEN, deck_composition
from ridefree.engine import play_dealer
from ridefree.rules import Rules
from ridefree.simulator import Metrics, simulate
from ridefree.strategy import BasicStrategy

Z_PASS = 4.0  # |observed - reference| within this many standard errors → pass


@dataclass
class Check:
    name: str
    observed: float
    reference: float | None
    stderr: float
    source: str
    is_percent: bool = True  # False for absolute quantities like the std dev
    advisory: bool = False  # informational: shown with delta, never gates a run

    @property
    def z(self) -> float | None:
        if self.reference is None or self.stderr == 0:
            return None
        return (self.observed - self.reference) / self.stderr

    @property
    def status(self) -> str:
        if self.reference is None:
            return "BASELINE"
        if self.advisory:
            return "ADVISORY"
        z = self.z
        if z is None:
            return "BASELINE"
        return "PASS" if abs(z) <= Z_PASS else "FAIL"

    def _fmt(self, value: float) -> str:
        return f"{value * 100:8.4f}%" if self.is_percent else f"{value:8.4f} "

    def format(self) -> str:
        obs = self._fmt(self.observed)
        if self.reference is None:
            return f"[{self.status:8s}] {self.name:34s} {obs}            ({self.source})"
        ref = self._fmt(self.reference)
        z = self.z
        zs = f"{z:+.2f}σ" if z is not None else "  n/a"
        return f"[{self.status:8s}] {self.name:34s} {obs} vs {ref}  {zs:>8s}  ({self.source})"


def _binom_stderr(p: float, n: int) -> float:
    if n == 0:
        return 0.0
    return math.sqrt(max(p * (1 - p), 1e-12) / n)


class InfiniteDeckShoe:
    """Draws ranks with infinite-deck weights so the Monte Carlo matches the exact
    calculator's model. Deterministic under its seed."""

    _RANKS = tuple(range(1, 11))
    _WEIGHTS = tuple(4 if r == TEN else 1 for r in range(1, 11))

    def __init__(self, seed: int) -> None:
        import random

        self._rng = random.Random(seed)

    def deal(self) -> int:
        return self._rng.choices(self._RANKS, weights=self._WEIGHTS, k=1)[0]


def dealer_monte_carlo(rules: Rules, seed: int, trials: int) -> dict[int, dict[int, int]]:
    """Play out the REAL dealer state machine from each up-card, infinite deck.

    Returns {up_card: {final_total(22=bust): count}}. Uses `play_dealer` so we test
    the engine's logic, not a reimplementation.
    """
    from ridefree.hand import hand_total

    shoe = InfiniteDeckShoe(seed)
    by_up: dict[int, dict[int, int]] = {up: {} for up in range(1, 11)}
    counts: dict[int, int] = {up: 0 for up in range(1, 11)}
    per_up = trials // 10
    for up in range(1, 11):
        for _ in range(per_up):
            hole = shoe.deal()
            cards = play_dealer([up, hole], shoe, rules)
            total = hand_total(cards)
            key = 22 if total > 21 else total
            by_up[up][key] = by_up[up].get(key, 0) + 1
            counts[up] += 1
    return by_up


_UP_WEIGHT = {r: (4 if r == TEN else 1) for r in range(1, 11)}


def _dealer_checks(rules: Rules, seed: int, trials: int) -> list[Check]:
    """Dealer bust rate — real-engine Monte Carlo vs exact calculator.

    The per-up-card Monte Carlo plays out every hole card (no peek), matching the
    exact calculator's unconditional model, so the aggregate built from it is
    apples-to-apples with the exact aggregate.
    """
    mc = dealer_monte_carlo(rules, seed, trials)
    checks: list[Check] = []
    for up in range(1, 11):
        n = sum(mc[up].values())
        obs = mc[up].get(22, 0) / n if n else 0.0
        ref = dealer_odds.bust_probability(up, rules)
        label = "A" if up == ACE else str(up)
        checks.append(
            Check(f"dealer bust vs up-card {label}", obs, ref,
                  _binom_stderr(ref, n), "exact calc")
        )
    # Aggregate over up-cards weighted by fresh-deck frequency (unconditional).
    total_w = sum(_UP_WEIGHT.values())
    agg_obs = sum(
        _UP_WEIGHT[up] / total_w * (mc[up].get(22, 0) / max(sum(mc[up].values()), 1))
        for up in range(1, 11)
    )
    agg_n = sum(sum(mc[up].values()) for up in range(1, 11))
    agg_ref = dealer_odds.aggregate_distribution(rules)["bust"]
    checks.append(
        Check("dealer bust (aggregate)", agg_obs, agg_ref,
              _binom_stderr(agg_ref, agg_n), "exact calc (∞-deck)")
    )
    return checks


def _fresh_shoe_natural_rate(rules: Rules) -> float:
    comp = deck_composition(rules.decks)
    n = sum(comp.values())
    return 2 * (comp[ACE] / n) * (comp[TEN] / (n - 1))


def run_suite(
    rules: Rules,
    *,
    seed: int = 1,
    game_rounds: int = 2_000_000,
    dealer_trials: int = 2_000_000,
    published_edge: float | None = -0.0062,
    published_std: float | None = 1.15,
) -> tuple[list[Check], Metrics]:
    """Run the battery. Returns (checks, full-game metrics).

    `published_edge` is the player EV (negative = house edge) for the exact ruleset;
    default is the Wizard of Odds ~0.62% house edge for 6-deck H17 basic strategy.
    Override / re-verify at call time — don't trust a hardcoded figure blindly.
    """
    m = simulate(rules, BasicStrategy(), seed=seed, rounds=game_rounds, bet=1.0)
    checks: list[Check] = []

    # 1. Dealer distribution: real engine vs exact calculator, per up-card + aggregate.
    checks.extend(_dealer_checks(rules, seed + 1, dealer_trials))

    # 3. Player natural rate vs the exact fresh-shoe value.
    nat_ref = _fresh_shoe_natural_rate(rules)
    nat_obs = m.player_naturals / m.rounds if m.rounds else 0.0
    checks.append(
        Check("player natural rate", nat_obs, nat_ref,
              _binom_stderr(nat_ref, m.rounds), "fresh-shoe exact")
    )

    # 4. House edge vs published figure.
    checks.append(
        Check("house edge", -m.edge, (-published_edge if published_edge is not None else None),
              m.edge_stderr, "Wizard of Odds")
    )

    # 5. Per-round std dev vs published ~1.15. The reference is a rounded folk figure,
    #    so this is advisory (shown with delta) rather than a hard gate.
    std_stderr = m.profit_std / math.sqrt(2 * max(m.rounds - 1, 1))  # approx SE of std
    checks.append(
        Check("per-round std dev (abs)", m.profit_std, published_std,
              std_stderr, "Wizard/Schlesinger ~1.15", is_percent=False, advisory=True)
    )

    # 6. Frequencies with no strict published reference — baselines / regression anchors.
    for name, count in (
        ("pair dealt rate", m.pairs_dealt),
        ("split rate", m.splits),
        ("double rate", m.doubles),
    ):
        checks.append(
            Check(name, count / m.rounds if m.rounds else 0.0, None, 0.0, "baseline")
        )

    return checks, m


_STATUS_META = {
    "PASS": ("#15803d", "#dcfce7", "PASS"),
    "FAIL": ("#b91c1c", "#fee2e2", "FAIL"),
    "ADVISORY": ("#b45309", "#fef3c7", "ADVISORY"),
    "BASELINE": ("#475569", "#e2e8f0", "BASELINE"),
}


def _html_value(c: Check, value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.4f}%" if c.is_percent else f"{value:.4f}"


def to_html(
    checks: list[Check],
    m: Metrics,
    *,
    title: str = "Ride Free — Validation",
    ruleset_name: str = "STANDARD_6D_H17",
    generated_at: str = "",
) -> str:
    n_fail = sum(1 for c in checks if c.status == "FAIL")
    overall_ok = n_fail == 0
    banner_bg, banner_fg = ("#16a34a", "#ffffff") if overall_ok else ("#dc2626", "#ffffff")
    banner_text = "ALL CHECKS PASS" if overall_ok else f"{n_fail} CHECK(S) FAILED"

    rows = []
    for c in checks:
        fg, bg, label = _STATUS_META[c.status]
        z = c.z
        dev = f"{z:+.2f}σ" if z is not None else "—"
        dev_warn = " class='warn'" if (z is not None and abs(z) > 2 and c.status != "FAIL") else ""
        rows.append(
            f"<tr>"
            f"<td class='name'>{c.name}</td>"
            f"<td class='num'>{_html_value(c, c.observed)}</td>"
            f"<td class='num'>{_html_value(c, c.reference)}</td>"
            f"<td class='num'{dev_warn}>{dev}</td>"
            f"<td class='src'>{c.source}</td>"
            f"<td><span class='badge' style='color:{fg};background:{bg}'>{label}</span></td>"
            f"</tr>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0; padding: 2rem 1rem; background: #f8fafc; color: #0f172a; }}
  .wrap {{ max-width: 920px; margin: 0 auto; }}
  h1 {{ font-size: 1.4rem; margin: 0 0 0.25rem; }}
  .meta {{ color: #64748b; font-size: 0.85rem; margin-bottom: 1.25rem; }}
  .meta code {{ background: #e2e8f0; padding: 0.1rem 0.4rem; border-radius: 4px; }}
  .banner {{ font-weight: 700; letter-spacing: 0.04em; padding: 0.7rem 1rem;
    border-radius: 10px; margin-bottom: 1.5rem; background: {banner_bg}; color: {banner_fg}; }}
  .summary {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }}
  .stat {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 0.75rem 1rem; min-width: 120px; }}
  .stat .k {{ color: #64748b; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .stat .v {{ font-size: 1.15rem; font-weight: 650; margin-top: 0.15rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
    border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; }}
  th, td {{ text-align: left; padding: 0.6rem 0.8rem; font-size: 0.9rem;
    border-bottom: 1px solid #eef2f7; }}
  th {{ background: #f1f5f9; color: #475569; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.05em; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  td.name {{ font-weight: 550; }}
  td.src {{ color: #64748b; font-size: 0.8rem; }}
  td.warn {{ color: #b45309; }}
  .badge {{ display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.03em; }}
  tr:last-child td {{ border-bottom: none; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0b1120; color: #e2e8f0; }}
    .meta {{ color: #94a3b8; }} .meta code {{ background: #1e293b; }}
    .stat, table {{ background: #111a2e; border-color: #1e293b; }}
    th {{ background: #172033; color: #94a3b8; }}
    td, th {{ border-bottom-color: #1e293b; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>{title}</h1>
  <div class="meta">ruleset <code>{ruleset_name}</code> &middot; generated {generated_at}</div>
  <div class="banner">{banner_text}</div>
  <div class="summary">
    <div class="stat"><div class="k">Rounds</div><div class="v">{m.rounds:,}</div></div>
    <div class="stat"><div class="k">Hands</div><div class="v">{m.hands:,}</div></div>
    <div class="stat"><div class="k">Dealer completed</div><div class="v">{m.dealer_completed:,}</div></div>
    <div class="stat"><div class="k">House edge</div><div class="v">{-m.edge * 100:.3f}%</div></div>
  </div>
  <table>
    <thead><tr><th>Check</th><th>Observed</th><th>Reference</th><th>Deviation</th><th>Source</th><th>Status</th></tr></thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</div>
</body>
</html>
"""


def format_report(checks: list[Check], m: Metrics) -> str:
    lines = [
        f"rounds: {m.rounds:,}   hands: {m.hands:,}   dealer-completed: {m.dealer_completed:,}",
        "",
    ]
    lines.extend(c.format() for c in checks)
    n_fail = sum(1 for c in checks if c.status == "FAIL")
    lines.append("")
    lines.append(f"{'ALL CHECKS PASS' if n_fail == 0 else f'{n_fail} CHECK(S) FAILED'}")
    return "\n".join(lines)
