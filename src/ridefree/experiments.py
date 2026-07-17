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
    # Ride-Free-optimal linear count (E4a EORs), in EV units; bins of 0.25%.
    "rf_ev": (lambda t: t.rf_ev_shift(), _bin_p(0.0025)),
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


@dataclass
class RowSummary:
    row: object
    rounds: int
    ev: float
    slope: float | None  # EV change per +0.01 of the column signal, at fixed row
    slope_se: float | None


@dataclass
class GridResult:
    rounds: int
    total_profit: float
    row_name: str
    col_name: str
    grid: dict = field(default_factory=dict)  # row_bin -> {col_bin -> BinStat}

    @property
    def overall_ev(self) -> float:
        return self.total_profit / self.rounds if self.rounds else 0.0

    def row_marginals(self) -> dict:
        out = {}
        for row, cols in self.grid.items():
            stat = BinStat()
            for cell in cols.values():
                stat.rounds += cell.rounds
                stat.profit += cell.profit
                stat.profit_sq += cell.profit_sq
            out[row] = stat
        return out

    def row_summaries(self, min_cell: int = 2000) -> list[RowSummary]:
        summaries = []
        for row in sorted(self.grid):
            cols = {c: s for c, s in self.grid[row].items() if s.rounds >= min_cell}
            marginal = BinStat()
            for cell in self.grid[row].values():
                marginal.rounds += cell.rounds
                marginal.profit += cell.profit
                marginal.profit_sq += cell.profit_sq
            slope, slope_se = _weighted_slope(cols)
            summaries.append(
                RowSummary(row, marginal.rounds, marginal.ev, slope, slope_se)
            )
        return summaries

    def pooled_slope(self, min_cell: int = 2000) -> tuple[float, float] | None:
        """Inverse-variance weighted mean of within-row slopes: the column
        signal's EV effect at fixed row signal."""
        num = den = 0.0
        for s in self.row_summaries(min_cell):
            if s.slope is None or not s.slope_se:
                continue
            w = 1.0 / (s.slope_se**2)
            num += w * s.slope
            den += w
        if den == 0:
            return None
        return num / den, math.sqrt(1.0 / den)


def _weighted_slope(cols: dict, scale: float = 0.01):
    """Rounds-weighted least-squares slope of EV on the column bin value, scaled to
    EV-per-+`scale` of signal. Returns (slope, se) or (None, None)."""
    if len(cols) < 2:
        return None, None
    total = sum(s.rounds for s in cols.values())
    xbar = sum(c * s.rounds for c, s in cols.items()) / total
    denom = sum(s.rounds * (c - xbar) ** 2 for c, s in cols.items())
    if denom <= 0:
        return None, None
    slope = sum(s.rounds * (c - xbar) * s.ev for c, s in cols.items()) / denom
    var = sum(
        (s.rounds * (c - xbar) / denom) ** 2 * s.stderr**2 for c, s in cols.items()
    )
    return slope * scale, math.sqrt(var) * scale


def run_conditional_ev_grid(
    rules: Rules,
    strategy,
    *,
    seed: int,
    rounds: int,
    row_signal: str = "hilo_tc",
    col_signal: str = "p_pair",
    bet: float = 1.0,
) -> GridResult:
    """One pass, binning each round's profit by (row signal, column signal)."""
    row_extract, row_bin = SIGNALS[row_signal]
    col_extract, col_bin = SIGNALS[col_signal]
    grid: dict = {}
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
        row = row_bin(row_extract(tracker))
        col = col_bin(col_extract(tracker))
        result = play_round(rules, shoe, strategy, bet=bet)
        rounds_since += 1
        tracker.observe_round(result)
        total_profit += result.profit
        grid.setdefault(row, {}).setdefault(col, BinStat()).add(result.profit)
    return GridResult(
        rounds=rounds,
        total_profit=total_profit,
        row_name=row_signal,
        col_name=col_signal,
        grid=grid,
    )


@dataclass
class DeviationResult:
    rounds: int
    base_profit: float
    diff_sum: float
    diff_sq: float
    rounds_changed: int  # rounds where the two strategies' profits differ
    window_rounds: int = 0  # rounds inside the wong-in window (rf_ev >= threshold)
    window_diff: float = 0.0
    window_diff_sq: float = 0.0

    @property
    def deviation_value(self) -> float:
        """Mean EV gained per round by composition-conditioned play."""
        return self.diff_sum / self.rounds if self.rounds else 0.0

    @property
    def deviation_se(self) -> float:
        if self.rounds < 2:
            return 0.0
        m = self.deviation_value
        var = max(self.diff_sq / self.rounds - m * m, 0.0)
        return math.sqrt(var / self.rounds)

    @property
    def window_value(self) -> float:
        return self.window_diff / self.window_rounds if self.window_rounds else 0.0

    @property
    def window_se(self) -> float:
        if self.window_rounds < 2:
            return 0.0
        m = self.window_value
        var = max(self.window_diff_sq / self.window_rounds - m * m, 0.0)
        return math.sqrt(var / self.window_rounds)


def run_deviation_value(
    rules: Rules,
    *,
    seed: int,
    rounds: int,
    bet: float = 1.0,
    window_threshold: float = 0.0075,
) -> DeviationResult:
    """Paired differential simulation of composition-conditioned play.

    Each round is played twice from the same shoe position — once with the fixed
    OptimalStrategy, once with CompositionStrategy (live-composition argmax) — and
    the profit difference recorded. The fixed strategy's timeline is canonical
    (its cards advance the shoe and feed the tracker). Most rounds the strategies
    agree, so the difference is exactly 0 and its variance is tiny — resolving
    deviation values far below what independent runs could.
    """
    from ridefree.player_ev import CompositionStrategy, OptimalStrategy

    base = OptimalStrategy()
    dev = CompositionStrategy()
    shoe = Shoe(rules.decks, rules.penetration, seed)
    tracker = CompositionTracker(rules.decks)
    shuffles = 0
    rounds_since = 0
    result = DeviationResult(0, 0.0, 0.0, 0.0, 0)
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shuffles += 1
            shoe = Shoe(rules.decks, rules.penetration, seed + shuffles)
            tracker.new_shoe()
            rounds_since = 0
        in_window = tracker.rf_ev_shift() >= window_threshold
        start = shoe.snapshot()
        r_base = play_round(rules, shoe, base, bet=bet)
        end = shoe.snapshot()
        shoe.restore(start)
        dev.set_composition(rules, tracker.counts)
        r_dev = play_round(rules, shoe, dev, bet=bet)
        shoe.restore(end)  # canonical timeline: the fixed strategy's cards
        tracker.observe_round(r_base)
        rounds_since += 1
        d = r_dev.profit - r_base.profit
        result.rounds += 1
        result.base_profit += r_base.profit
        result.diff_sum += d
        result.diff_sq += d * d
        if d != 0.0:
            result.rounds_changed += 1
        if in_window:
            result.window_rounds += 1
            result.window_diff += d
            result.window_diff_sq += d * d
    return result


def _parse_bin(text: str):
    try:
        return int(text)
    except ValueError:
        return float(text)


def load_grid_json(path: str) -> GridResult:
    import json

    with open(path) as f:
        payload = json.load(f)
    grid: dict = {}
    total_rounds = 0
    total_profit = 0.0
    for row_text, cols in payload["grid"].items():
        row = _parse_bin(row_text)
        for col_text, (rounds, profit, profit_sq) in cols.items():
            col = _parse_bin(col_text)
            stat = grid.setdefault(row, {}).setdefault(col, BinStat())
            stat.rounds += rounds
            stat.profit += profit
            stat.profit_sq += profit_sq
            total_rounds += rounds
            total_profit += profit
    return GridResult(
        rounds=total_rounds,
        total_profit=total_profit,
        row_name=payload["row"],
        col_name=payload["col"],
        grid=grid,
    )


def merge_grids(results: list[GridResult]) -> GridResult:
    """Pool independently-seeded grid runs (bin stats are additive)."""
    assert results
    first = results[0]
    merged = GridResult(
        rounds=0, total_profit=0.0, row_name=first.row_name, col_name=first.col_name
    )
    for r in results:
        assert (r.row_name, r.col_name) == (first.row_name, first.col_name)
        merged.rounds += r.rounds
        merged.total_profit += r.total_profit
        for row, cols in r.grid.items():
            for col, stat in cols.items():
                target = merged.grid.setdefault(row, {}).setdefault(col, BinStat())
                target.rounds += stat.rounds
                target.profit += stat.profit
                target.profit_sq += stat.profit_sq
    return merged


def format_grid(result: GridResult, min_cell: int = 2000) -> str:
    lines = [
        f"rounds: {result.rounds:,}   overall EV: {result.overall_ev * 100:+.3f}%",
        f"rows: {result.row_name}   cols: {result.col_name}   "
        f"(slope = EV change per +0.01 of {result.col_name}, within the row)",
        "",
        f"  {'row':>5s} {'rounds':>10s} {'EV':>9s} {'slope/0.01':>11s} {'±1se':>8s}",
    ]
    for s in result.row_summaries(min_cell):
        label = f"{s.row:+d}" if isinstance(s.row, int) else f"{s.row:.3f}"
        if s.slope is None:
            slope_txt, se_txt = "n/a", ""
        else:
            slope_txt = f"{s.slope * 100:+10.3f}%"
            se_txt = f"{(s.slope_se or 0) * 100:7.3f}%"
        lines.append(
            f"  {label:>5s} {s.rounds:>10,d} {s.ev * 100:+8.3f}% {slope_txt:>11s} {se_txt:>8s}"
        )
    pooled = result.pooled_slope(min_cell)
    lines.append("")
    if pooled:
        slope, se = pooled
        z = slope / se if se else 0.0
        lines.append(
            f"pooled within-row slope: {slope * 100:+.4f}% ± {se * 100:.4f}% "
            f"per +0.01 {result.col_name}  ({z:+.1f}σ)"
        )
    return "\n".join(lines)


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
