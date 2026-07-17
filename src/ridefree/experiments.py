"""Conditional-EV experiments: EV as a function of pre-deal signals.

One simulation pass bins each round's profit by each signal's pre-deal value. The
resulting EV-vs-signal curves (with CIs) are the primary scientific object of the
attack phase: a bet ramp's overall performance is derivable from a curve
(E[profit] = sum over bins of P(bin) * bet(bin) * EV(bin)), so we simulate once,
evaluate candidate ramps analytically, and only the winning ramp needs its own
verification run.

Also accumulates pairwise Pearson correlations between signals — in particular to
test the hypothesis that free-double abundance anti-correlates with hi-lo true count
(small cards make free doubles AND bad base shoes).
"""

import math
from dataclasses import dataclass, field

from ridefree.cards import Shoe
from ridefree.counting import CompositionTracker
from ridefree.engine import play_round
from ridefree.rules import Rules
from ridefree.simulator import _needs_reshuffle


@dataclass
class BinStat:
    rounds: int = 0
    profit: float = 0.0
    profit_sq: float = 0.0

    def add(self, p: float) -> None:
        self.rounds += 1
        self.profit += p
        self.profit_sq += p * p

    @property
    def ev(self) -> float:
        return self.profit / self.rounds if self.rounds else 0.0

    @property
    def stderr(self) -> float:
        if self.rounds < 2:
            return 0.0
        mean = self.ev
        var = max(self.profit_sq / self.rounds - mean * mean, 0.0)
        return math.sqrt(var / self.rounds)


def _bin_p(width: float):
    def binner(value: float) -> float:
        return round(math.floor(value / width) * width, 6)

    return binner


def _bin_tc(value: float) -> int:
    return max(-6, min(6, int(round(value))))


SIGNALS = {
    # name -> (extract from tracker, binner)
    "p_pair": (lambda t: t.p_free_split_pair(), _bin_p(0.005)),
    "p_free_double": (lambda t: t.p_free_double_hand(), _bin_p(0.01)),
    "hilo_tc": (lambda t: t.hilo_true(), _bin_tc),
}


@dataclass
class ExperimentResult:
    rounds: int
    total_profit: float
    by_signal: dict[str, dict] = field(default_factory=dict)
    correlations: dict[tuple[str, str], float] = field(default_factory=dict)

    @property
    def overall_ev(self) -> float:
        return self.total_profit / self.rounds if self.rounds else 0.0


def run_conditional_ev(
    rules: Rules,
    strategy,
    *,
    seed: int,
    rounds: int,
    bet: float = 1.0,
) -> ExperimentResult:
    """Simulate `rounds` flat-bet rounds, binning profit by each pre-deal signal."""
    names = list(SIGNALS)
    by_signal: dict[str, dict] = {name: {} for name in names}
    # Correlation accumulators: sums, squares, cross-products.
    s = dict.fromkeys(names, 0.0)
    ss = dict.fromkeys(names, 0.0)
    cross = {(a, b): 0.0 for i, a in enumerate(names) for b in names[i + 1:]}

    shoe = Shoe(rules.decks, rules.penetration, seed)
    tracker = CompositionTracker(rules.decks)
    shuffles = 0
    rounds_since = 0
    total_profit = 0.0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shuffles += 1
            shoe = Shoe(rules.decks, rules.penetration, seed + shuffles)
            tracker.new_shoe()
            rounds_since = 0
        values = {name: SIGNALS[name][0](tracker) for name in names}
        result = play_round(rules, shoe, strategy, bet=bet)
        rounds_since += 1
        tracker.observe_round(result)
        total_profit += result.profit
        for name in names:
            key = SIGNALS[name][1](values[name])
            by_signal[name].setdefault(key, BinStat()).add(result.profit)
        for name in names:
            s[name] += values[name]
            ss[name] += values[name] * values[name]
        for (a, b) in cross:
            cross[(a, b)] += values[a] * values[b]

    correlations = {}
    n = rounds
    for (a, b), sab in cross.items():
        var_a = ss[a] / n - (s[a] / n) ** 2
        var_b = ss[b] / n - (s[b] / n) ** 2
        if var_a > 0 and var_b > 0:
            cov = sab / n - (s[a] / n) * (s[b] / n)
            correlations[(a, b)] = cov / math.sqrt(var_a * var_b)
    return ExperimentResult(
        rounds=rounds,
        total_profit=total_profit,
        by_signal=by_signal,
        correlations=correlations,
    )


def format_experiment(result: ExperimentResult, min_rounds: int = 1000) -> str:
    lines = [
        f"rounds: {result.rounds:,}   overall EV: {result.overall_ev * 100:+.3f}%",
        "",
        "signal correlations (Pearson):",
    ]
    for (a, b), r in sorted(result.correlations.items()):
        lines.append(f"  {a} vs {b}: {r:+.3f}")
    for name, bins in result.by_signal.items():
        lines.append("")
        lines.append(f"EV by {name} (bins with >= {min_rounds:,} rounds):")
        lines.append(f"  {'bin':>8s} {'rounds':>10s} {'EV':>9s} {'±1se':>8s}")
        for key in sorted(bins):
            stat = bins[key]
            if stat.rounds < min_rounds:
                continue
            label = f"{key:+d}" if isinstance(key, int) else f"{key:.3f}"
            lines.append(
                f"  {label:>8s} {stat.rounds:>10,d} "
                f"{stat.ev * 100:+8.3f}% {stat.stderr * 100:7.3f}%"
            )
    return "\n".join(lines)
