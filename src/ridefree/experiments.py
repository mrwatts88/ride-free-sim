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

from ridefree.cards import Shoe, shoe_seeds
from ridefree.counting import CompositionTracker, RawCompositionTracker
from ridefree.engine import play_round
from ridefree.rules import Rules
from ridefree.side_bets import _c3, _ev_from, ev_21p3, ev_fracs_21p3
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


def _bin_tc_wide(value: float) -> int:
    # Level-2 true counts run about twice as wide as hi-lo's.
    return max(-10, min(10, int(round(value))))


SIGNALS = {
    # name -> (extract from tracker, binner)
    "p_pair": (lambda t: t.p_free_split_pair(), _bin_p(0.005)),
    "p_free_double": (lambda t: t.p_free_double_hand(), _bin_p(0.01)),
    "hilo_tc": (lambda t: t.hilo_true(), _bin_tc),
    # Ride-Free-optimal linear count (E4a EORs), in EV units; bins of 0.25%.
    "rf_ev": (lambda t: t.rf_ev_shift(), _bin_p(0.0025)),
    # The RF-L2 human count (level-2 quantization of the RF EORs), true count.
    "rf_l2_tc": (lambda t: t.rf_l2_true(), _bin_tc_wide),
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

    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    tracker = CompositionTracker(rules.decks)
    rounds_since = 0
    total_profit = 0.0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
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
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    tracker = CompositionTracker(rules.decks)
    rounds_since = 0
    total_profit = 0.0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
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
    actions_changed: int = 0  # rounds where any chosen action differs (>= rounds_changed)
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


class _ActionRecorder:
    """Transparent strategy wrapper recording the round's action sequence."""

    def __init__(self, inner) -> None:
        self._inner = inner
        self.actions: list = []

    def choose(self, view, rules):
        action = self._inner.choose(view, rules)
        self.actions.append(action)
        return action


def run_deviation_value(
    rules: Rules,
    *,
    seed: int,
    rounds: int,
    bet: float = 1.0,
    window_threshold: float = 0.0075,
    window_only: bool = False,
) -> DeviationResult:
    """Paired differential simulation of composition-conditioned play.

    Each round is played twice from the same shoe position — once with the fixed
    OptimalStrategy, once with CompositionStrategy (live-composition argmax) — and
    the profit difference recorded. The fixed strategy's timeline is canonical
    (its cards advance the shoe and feed the tracker). Most rounds the strategies
    agree, so the difference is exactly 0 and its variance is tiny — resolving
    deviation values far below what independent runs could.

    `window_only` (E8's efficiency mode) skips the paired replay on rounds below
    `window_threshold`, accumulating window rounds ~7x faster per second. In that
    mode only the window_* fields are meaningful — the overall deviation_value /
    rounds_changed / actions_changed cover window rounds alone. The base timeline
    is identical either way, so window stats match the full run exactly.

    Insurance is deliberately excluded on both arms: this harness isolates PLAY
    deviations; the insurance overlay is separable and measured by E9.
    """
    from ridefree.player_ev import CompositionStrategy, OptimalStrategy

    base = _ActionRecorder(OptimalStrategy())
    dev_inner = CompositionStrategy()
    dev = _ActionRecorder(dev_inner)
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    tracker = CompositionTracker(rules.decks)
    rounds_since = 0
    result = DeviationResult(0, 0.0, 0.0, 0.0, 0)
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            tracker.new_shoe()
            rounds_since = 0
        in_window = tracker.rf_ev_shift() >= window_threshold
        if window_only and not in_window:
            r_base = play_round(rules, shoe, base, bet=bet)
            tracker.observe_round(r_base)
            rounds_since += 1
            result.rounds += 1
            result.base_profit += r_base.profit
            continue
        base.actions.clear()
        start = shoe.snapshot()
        r_base = play_round(rules, shoe, base, bet=bet)
        end = shoe.snapshot()
        shoe.restore(start)
        dev_inner.set_composition(rules, tracker.counts)
        dev.actions.clear()
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
        if base.actions != dev.actions:
            result.actions_changed += 1
        if in_window:
            result.window_rounds += 1
            result.window_diff += d
            result.window_diff_sq += d * d
    return result


# --- E10: 21+3 exact pre-deal EV scan (the perfect-information ceiling) -----

SB_EV_THRESHOLDS = (0.0, 0.005, 0.01, 0.02, 0.03)


@dataclass
class SbEvScanResult:
    """One pass of exact 21+3 EV vs realized side-bet profit.

    The ceiling numbers (P(ev > thr), mean predicted EV above threshold) are
    deterministic functions of shoe states — their only error is round
    sampling. Realized profit per bin is the end-to-end consistency check
    (calibration slope ≈ 1)."""

    rounds: int = 0
    penetration: float = 0.0
    realized_profit: float = 0.0
    pred_sum: float = 0.0
    by_ev: dict = field(default_factory=dict)  # ev bin -> BinStat (sb profit)
    bin_pred: dict = field(default_factory=dict)  # ev bin -> sum predicted ev
    by_depth: dict = field(default_factory=dict)  # decks-left bin -> [n, n_pos, sum_pos]
    # thr -> [rounds, pred_sum, profit, profit_sq]
    thresholds: dict = field(default_factory=dict)
    # correlation accumulators: ev vs hilo true count
    s_ev: float = 0.0
    ss_ev: float = 0.0
    s_hilo: float = 0.0
    ss_hilo: float = 0.0
    cross_ev_hilo: float = 0.0

    @property
    def corr_ev_hilo(self) -> float:
        n = self.rounds
        var_e = self.ss_ev / n - (self.s_ev / n) ** 2
        var_h = self.ss_hilo / n - (self.s_hilo / n) ** 2
        if var_e <= 0 or var_h <= 0:
            return 0.0
        cov = self.cross_ev_hilo / n - (self.s_ev / n) * (self.s_hilo / n)
        return cov / math.sqrt(var_e * var_h)

    def calibration_slope(self, min_cell: int = 2000):
        """Rounds-weighted LSQ slope of realized bin EV on mean predicted EV.
        1.0 = the exact calculator prices the shoe correctly end to end."""
        cells = [
            (self.bin_pred[k] / s.rounds, s)
            for k, s in self.by_ev.items()
            if s.rounds >= min_cell
        ]
        if len(cells) < 2:
            return None, None
        total = sum(s.rounds for _, s in cells)
        xbar = sum(x * s.rounds for x, s in cells) / total
        denom = sum(s.rounds * (x - xbar) ** 2 for x, s in cells)
        if denom <= 0:
            return None, None
        slope = sum(s.rounds * (x - xbar) * s.ev for x, s in cells) / denom
        var = sum(
            (s.rounds * (x - xbar) / denom) ** 2 * s.stderr**2 for x, s in cells
        )
        return slope, math.sqrt(var)


def run_sb_ev_scan(
    rules: Rules,
    strategy,
    *,
    seed: int,
    rounds: int,
    bet: float = 1.0,
) -> SbEvScanResult:
    """Simulate with the 21+3 bet always staked, computing the EXACT pre-deal
    EV from the remaining raw composition each round (closed form, no model).
    `rules.side_bet_21p3` must be set and `strategy` must stake every round."""
    if not rules.side_bet_21p3:
        raise ValueError("rules.side_bet_21p3 must be configured for the scan")
    res = SbEvScanResult(penetration=rules.penetration)
    res.thresholds = {t: [0, 0.0, 0.0, 0.0] for t in SB_EV_THRESHOLDS}
    ev_bin = _bin_p(0.005)
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    raw = RawCompositionTracker(rules.decks)
    comp = CompositionTracker(rules.decks)
    rounds_since = 0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            raw.new_shoe()
            comp.new_shoe()
            rounds_since = 0
        ev = ev_21p3(raw.counts, rules.side_bet_21p3)
        hilo = comp.hilo_true()
        depth_bin = round(math.floor(shoe.cards_remaining / 52 / 0.5) * 0.5, 1)
        start = shoe.snapshot()
        result = play_round(rules, shoe, strategy, bet=bet)
        raw.observe(shoe.raw_slice(start, shoe.snapshot()))
        comp.observe_round(result)
        rounds_since += 1
        p = result.sb21p3_profit

        res.rounds += 1
        res.realized_profit += p
        res.pred_sum += ev
        key = ev_bin(ev)
        res.by_ev.setdefault(key, BinStat()).add(p)
        res.bin_pred[key] = res.bin_pred.get(key, 0.0) + ev
        d = res.by_depth.setdefault(depth_bin, [0, 0, 0.0])
        d[0] += 1
        if ev > 0:
            d[1] += 1
            d[2] += ev
        for t, acc in res.thresholds.items():
            if ev > t:
                acc[0] += 1
                acc[1] += ev
                acc[2] += p
                acc[3] += p * p
        res.s_ev += ev
        res.ss_ev += ev * ev
        res.s_hilo += hilo
        res.ss_hilo += hilo * hilo
        res.cross_ev_hilo += ev * hilo
    return res


def format_sb_ev_scan(res: SbEvScanResult, min_cell: int = 2000) -> str:
    n = res.rounds
    lines = [
        f"rounds: {n:,}   penetration: {res.penetration:.2f}",
        f"realized 21+3 EV: {100 * res.realized_profit / n:+.4f}%   "
        f"mean predicted EV: {100 * res.pred_sum / n:+.4f}%",
        f"corr(sb_ev, hilo_tc): {res.corr_ev_hilo:+.3f}",
        "",
        "ceiling by wong-in threshold (bet only when exact EV > thr):",
        f"  {'thr':>6s} {'P(ev>thr)':>10s} {'mean pred':>10s} "
        f"{'realized':>10s} {'±1se':>8s} {'per-100-rounds':>14s}",
    ]
    for t, (cnt, pred, prof, prof_sq) in sorted(res.thresholds.items()):
        if cnt == 0:
            lines.append(f"  {t:6.3f} {'—':>10s}")
            continue
        frac = cnt / n
        mean_pred = pred / cnt
        mean_real = prof / cnt
        var = max(prof_sq / cnt - mean_real * mean_real, 0.0)
        se = math.sqrt(var / cnt)
        per100 = 100 * frac * mean_pred
        lines.append(
            f"  {t:6.3f} {100 * frac:9.4f}% {100 * mean_pred:+9.4f}% "
            f"{100 * mean_real:+9.4f}% {100 * se:7.4f}% {per100:+13.4f}u"
        )
    lines.append("")
    lines.append("P(ev>0) by shoe depth (decks remaining, floor-binned):")
    lines.append(f"  {'decks':>6s} {'rounds':>10s} {'P(ev>0)':>9s} {'mean pos ev':>12s}")
    for k in sorted(res.by_depth, reverse=True):
        cnt, pos, sum_pos = res.by_depth[k]
        mp = 100 * sum_pos / pos if pos else 0.0
        lines.append(
            f"  {k:6.1f} {cnt:>10,d} {100 * pos / cnt:8.4f}% {mp:+11.4f}%"
        )
    slope, se = res.calibration_slope(min_cell)
    lines.append("")
    if slope is not None:
        lines.append(
            f"calibration slope (realized on predicted, weighted): "
            f"{slope:.3f} ± {se:.3f}  (1.0 = exact)"
        )
    lines.append("")
    lines.append(f"realized EV by predicted-EV bin (bins with >= {min_cell:,} rounds):")
    lines.append(f"  {'bin':>8s} {'rounds':>10s} {'mean pred':>10s} "
                 f"{'realized':>10s} {'±1se':>8s}")
    for k in sorted(res.by_ev):
        s = res.by_ev[k]
        if s.rounds < min_cell:
            continue
        mean_pred = res.bin_pred[k] / s.rounds
        lines.append(
            f"  {k:8.3f} {s.rounds:>10,d} {100 * mean_pred:+9.4f}% "
            f"{100 * s.ev:+9.4f}% {100 * s.stderr:7.4f}%"
        )
    return "\n".join(lines)


# --- E11a: what carries the 21+3 signal? (exact decomposition) --------------

_TYPES_52 = tuple((r, s) for r in range(1, 14) for s in range(4))


def sb_ev_components(
    counts: dict, paytable: tuple[tuple[str, float], ...]
) -> tuple[float, float, float, float, float]:
    """Exact decomposition of the pre-deal 21+3 EV for one shoe state.

    The category identities are polynomials, so they evaluate on fractional
    'smoothed' compositions. Define, at the same total N:
      ev_bal  — fully balanced shoe (pure depth effect),
      S = ev(same suit totals, ranks smoothed within suit) − ev_bal,
      R = ev(same rank totals, suits smoothed within rank) − ev_bal,
      X = ev_full − ev_bal − S − R (rank×suit interaction residual).
    Returns (ev_full, ev_bal, S, R, X); ev_full ≡ ev_bal + S + R + X.
    """
    n_rank = [0.0] * 14
    n_suit = [0.0, 0.0, 0.0, 0.0]
    for (rank, suit), c in counts.items():
        n_rank[rank] += c
        n_suit[suit] += c
    n = sum(n_suit)
    ev_full = ev_21p3(counts, paytable)
    suit_smooth = {(r, s): n_suit[s] / 13.0 for r, s in _TYPES_52}
    rank_smooth = {(r, s): n_rank[r] / 4.0 for r, s in _TYPES_52}
    balanced = {t: n / 52.0 for t in _TYPES_52}
    ev_bal = ev_fracs_21p3(balanced, paytable)
    s = ev_fracs_21p3(suit_smooth, paytable) - ev_bal
    r = ev_fracs_21p3(rank_smooth, paytable) - ev_bal
    x = ev_full - ev_bal - s - r
    return ev_full, ev_bal, s, r, x


@dataclass
class _SelStat:
    """One candidate selection rule: bet when its proxy signal > threshold."""

    selected: int = 0
    ev_sum: float = 0.0  # Σ TRUE ev over selected rounds (dilution included)
    true_pos: int = 0  # overlap with the exact rule's selections


@dataclass
class SbDecompResult:
    rounds: int = 0
    penetration: float = 0.0
    threshold: float = 0.0
    # moment accumulators for (S, R, X) and full/baseline
    sums: dict = field(default_factory=dict)
    squares: dict = field(default_factory=dict)
    crosses: dict = field(default_factory=dict)
    rules: dict = field(default_factory=dict)  # name -> _SelStat
    by_depth: dict = field(default_factory=dict)  # bin -> [n, Σbal, ΣS², ΣR²]

    def var(self, k: str) -> float:
        m = self.sums[k] / self.rounds
        return max(self.squares[k] / self.rounds - m * m, 0.0)

    def cov(self, a: str, b: str) -> float:
        key = (a, b) if (a, b) in self.crosses else (b, a)
        return (
            self.crosses[key] / self.rounds
            - (self.sums[a] / self.rounds) * (self.sums[b] / self.rounds)
        )


def run_sb_decomposition(
    rules: Rules,
    strategy,
    *,
    seed: int,
    rounds: int,
    paytable: tuple[tuple[str, float], ...],
    threshold: float = 0.0,
) -> SbDecompResult:
    """E11a: play rounds (no side bet staked — signals are pure functions of
    shoe states) and decompose each round's exact 21+3 EV into depth + suit +
    rank + interaction, scoring proxy selection rules against the exact one."""
    res = SbDecompResult(penetration=rules.penetration, threshold=threshold)
    keys = ("F", "B", "S", "R", "X")
    res.sums = dict.fromkeys(keys, 0.0)
    res.squares = dict.fromkeys(keys, 0.0)
    res.crosses = {(a, b): 0.0 for i, a in enumerate(keys) for b in keys[i + 1:]}
    res.rules = {
        name: _SelStat() for name in ("exact", "suit_only", "rank_only", "additive")
    }
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    raw = RawCompositionTracker(rules.decks)
    rounds_since = 0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            raw.new_shoe()
            rounds_since = 0
        f, b, s, r, x = sb_ev_components(raw.counts, paytable)
        depth_bin = round(math.floor(shoe.cards_remaining / 52 / 0.5) * 0.5, 1)
        start = shoe.snapshot()
        result = play_round(rules, shoe, strategy, bet=1.0)
        raw.observe(shoe.raw_slice(start, shoe.snapshot()))
        rounds_since += 1

        res.rounds += 1
        vals = dict(zip(keys, (f, b, s, r, x)))
        for k, v in vals.items():
            res.sums[k] += v
            res.squares[k] += v * v
        for (a, c) in res.crosses:
            res.crosses[(a, c)] += vals[a] * vals[c]
        exact_bet = f > threshold
        for name, signal in (
            ("exact", f),
            ("suit_only", b + s),
            ("rank_only", b + r),
            ("additive", b + s + r),
        ):
            if signal > threshold:
                stat = res.rules[name]
                stat.selected += 1
                stat.ev_sum += f
                if exact_bet:
                    stat.true_pos += 1
        d = res.by_depth.setdefault(depth_bin, [0, 0.0, 0.0, 0.0])
        d[0] += 1
        d[1] += b
        d[2] += s * s
        d[3] += r * r
    return res


def format_sb_decomposition(res: SbDecompResult) -> str:
    n = res.rounds
    var_dev = res.var("F")  # F = B + S + R + X; report both raw and de-drifted
    lines = [
        f"rounds: {n:,}   penetration: {res.penetration:.2f}   "
        f"threshold: ev > {res.threshold:g}",
        "",
        "variance of exact EV around the depth baseline (F − B = S + R + X):",
    ]
    total = (
        res.var("S") + res.var("R") + res.var("X")
        + 2 * (res.cov("S", "R") + res.cov("S", "X") + res.cov("R", "X"))
    )
    for label, v in (
        ("suit term S", res.var("S")),
        ("rank term R", res.var("R")),
        ("interaction X", res.var("X")),
        ("2·cov(S,R)", 2 * res.cov("S", "R")),
        ("2·cov(S,X)+2·cov(R,X)", 2 * (res.cov("S", "X") + res.cov("R", "X"))),
    ):
        lines.append(f"  {label:22s} {100 * v / total:6.2f}% of Var(F−B)")
    corr = res.cov("S", "R") / math.sqrt(res.var("S") * res.var("R"))
    lines.append(f"  corr(S, R) = {corr:+.3f}   "
                 f"sd(S) = {100 * math.sqrt(res.var('S')):.3f}%   "
                 f"sd(R) = {100 * math.sqrt(res.var('R')):.3f}%   "
                 f"sd(X) = {100 * math.sqrt(res.var('X')):.3f}%   "
                 f"sd(F) = {100 * math.sqrt(var_dev):.3f}%")
    lines.append("")
    lines.append("selection rules (bet when proxy > threshold; value in TRUE ev):")
    lines.append(f"  {'rule':>10s} {'P(bet)':>8s} {'mean ev':>9s} "
                 f"{'u/100':>8s} {'capture':>8s} {'precision':>9s} {'recall':>7s}")
    exact = res.rules["exact"]
    ceiling = exact.ev_sum / n * 100
    for name in ("exact", "suit_only", "rank_only", "additive"):
        st = res.rules[name]
        if st.selected == 0:
            lines.append(f"  {name:>10s}      —")
            continue
        per100 = st.ev_sum / n * 100
        lines.append(
            f"  {name:>10s} {100 * st.selected / n:7.3f}% "
            f"{100 * st.ev_sum / st.selected:+8.3f}% {per100:+7.3f}u "
            f"{100 * per100 / ceiling:7.2f}% "
            f"{100 * st.true_pos / st.selected:8.2f}% "
            f"{100 * st.true_pos / exact.selected:6.2f}%"
        )
    lines.append("")
    lines.append("by depth: baseline drift and term spreads:")
    lines.append(f"  {'decks':>6s} {'rounds':>10s} {'ev_bal':>8s} "
                 f"{'sd(S)':>7s} {'sd(R)':>7s}")
    for k in sorted(res.by_depth, reverse=True):
        cnt, b_sum, s_sq, r_sq = res.by_depth[k]
        lines.append(
            f"  {k:6.1f} {cnt:>10,d} {100 * b_sum / cnt:+7.3f}% "
            f"{100 * math.sqrt(s_sq / cnt):6.3f}% {100 * math.sqrt(r_sq / cnt):6.3f}%"
        )
    return "\n".join(lines)


# --- E11b: human-executable 21+3 trackers vs the E10/E11a bounds ------------


def sb_ev_suit_config(
    suit_totals, paytable: tuple[tuple[str, float], ...]
) -> float:
    """Exact B+S for a shoe with the given remaining suit totals and ranks
    uniform within each suit (E11a's suit-smoothed composition, in closed
    form from the four totals — what a 4-suit counter can know)."""
    n = sum(suit_totals)
    n13 = n / 13.0
    trips = 13.0 * _c3(n13)
    straights_all = 12.0 * n13 * n13 * n13
    sf = 12.0 * sum((ns / 13.0) ** 3 for ns in suit_totals)
    suited_trips = 13.0 * sum(_c3(ns / 13.0) for ns in suit_totals)
    flush = sum(_c3(ns) for ns in suit_totals) - sf - suited_trips
    combos = {
        "straight_flush": sf,
        "three_of_a_kind": trips,
        "straight": straights_all - sf,
        "flush": flush,
    }
    return _ev_from(combos, _c3(n), paytable)


def sb_threshold_curves(
    paytable: tuple[tuple[str, float], ...], max_n: int = 312, min_n: int = 16
) -> tuple[dict[int, float], dict[int, float]]:
    """Analytic wong-in index curves — NO simulation data involved.

    T1[N]: minimum excess x of ONE rich suit (others equal) making the
    suit-family EV positive at N cards remaining; T2[N]: same for TWO equally
    rich suits (each +x). Continuous (bisection): the human's excesses vs N/4
    are fractional whenever N % 4 != 0, so rounding the curve up would give
    away real bets. Absent key = unreachable at that depth."""

    def ev_at(n: float, x: float, rich: int) -> float:
        base = n / 4.0
        totals = [base - rich * x / (4.0 - rich)] * 4
        for i in range(rich):
            totals[i] = base + x
        return sb_ev_suit_config(totals, paytable)

    t1: dict[int, float] = {}
    t2: dict[int, float] = {}
    for n in range(min_n, max_n + 1):
        for table, rich in ((t1, 1), (t2, 2)):
            # feasible x keeps every suit total in [0, n]
            hi_cap = min(3.0 * n / 4.0 / rich, n / 4.0 * (4.0 - rich) / rich)
            lo, hi = 0.0, None
            x = 1.0
            while x <= hi_cap:
                if ev_at(n, x, rich) > 0:
                    hi = x
                    break
                lo = x
                x += 1.0
            if hi is None:
                continue
            for _ in range(30):
                mid = (lo + hi) / 2
                if ev_at(n, mid, rich) > 0:
                    hi = mid
                else:
                    lo = mid
            table[n] = hi
    return t1, t2


def sb_rank_tags(
    paytable: tuple[tuple[str, float], ...], n_ref: int = 156
) -> dict[int, float]:
    """Static per-rank tags: the exact-EV gradient wrt each rank's remaining
    count (suits kept balanced), central-differenced at a balanced mid-shoe.
    The best LINEAR rank count for the side bet; expected to be weak (the
    rank term is mostly quadratic) — measured, not assumed."""
    tags = {}
    types = [(r, s) for r in range(1, 14) for s in range(4)]
    base = n_ref / 52.0
    for rank in range(1, 14):
        up = {t: base + (0.25 if t[0] == rank else 0.0) for t in types}
        dn = {t: base - (0.25 if t[0] == rank else 0.0) for t in types}
        tags[rank] = (
            ev_fracs_21p3(up, paytable) - ev_fracs_21p3(dn, paytable)
        ) / 2.0
    return tags


@dataclass
class SbTrackerResult:
    rounds: int = 0
    penetration: float = 0.0
    rules: dict = field(default_factory=dict)  # name -> _SelStat
    t1: dict = field(default_factory=dict)
    t2: dict = field(default_factory=dict)


def run_sb_trackers(
    rules: Rules,
    strategy,
    *,
    seed: int,
    rounds: int,
    paytable: tuple[tuple[str, float], ...],
) -> SbTrackerResult:
    """E11b: score human-executable selection rules in TRUE exact EV.

    All rules' parameters (threshold curves, rank tags) are derived
    analytically above — nothing is fit to this run's data."""
    t1, t2 = sb_threshold_curves(paytable)
    tags = sb_rank_tags(paytable)
    res = SbTrackerResult(penetration=rules.penetration, t1=t1, t2=t2)
    names = (
        "exact", "additive_exact", "suit4_exact", "any_suit_T1", "pair_rule",
        "quad_Q", "spades_only_T1", "suit4_plus_linrank",
    )
    res.rules = {name: _SelStat() for name in names}
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    raw = RawCompositionTracker(rules.decks)
    rounds_since = 0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            raw.new_shoe()
            rounds_since = 0
        counts = raw.counts
        n_rank = [0.0] * 14
        suit_totals = [0.0, 0.0, 0.0, 0.0]
        for (rank, suit), c in counts.items():
            n_rank[rank] += c
            suit_totals[suit] += c
        n = raw.cards_remaining
        f = ev_21p3(counts, paytable)
        bs = sb_ev_suit_config(suit_totals, paytable)
        lin = sum(tags[r] * (n_rank[r] - n / 13.0) for r in range(1, 14))
        # additive uses the exact rank term R = (B+R) - B; with suits balanced
        # within rank that's ev_fracs of the rank-smoothed comp minus baseline.
        rank_smooth = {t: n_rank[t[0]] / 4.0 for t in _TYPES_52}
        balanced = {t: n / 52.0 for t in _TYPES_52}
        ev_bal = ev_fracs_21p3(balanced, paytable)
        additive = bs + (ev_fracs_21p3(rank_smooth, paytable) - ev_bal)
        excesses = sorted((ns - n / 4.0 for ns in suit_totals), reverse=True)
        thr1 = t1.get(n)
        thr2 = t2.get(n)
        start = shoe.snapshot()
        play_round(rules, shoe, strategy, bet=1.0)
        raw.observe(shoe.raw_slice(start, shoe.snapshot()))
        rounds_since += 1

        res.rounds += 1
        exact_bet = f > 0
        decisions = (
            ("exact", exact_bet),
            ("additive_exact", additive > 0),
            ("suit4_exact", bs > 0),
            ("any_suit_T1", thr1 is not None and excesses[0] >= thr1),
            ("pair_rule",
             (thr1 is not None and excesses[0] >= thr1)
             or (thr2 is not None and excesses[1] >= thr2)),
            # S's quadratic form is symmetric in the suits: threshold on
            # Q = Σ excess², calibrated from the single-rich boundary where
            # Q(x) = x² · 4/3 — still just four counts plus arithmetic.
            ("quad_Q",
             thr1 is not None
             and sum(x * x for x in excesses) >= thr1 * thr1 * 4.0 / 3.0),
            ("spades_only_T1",
             thr1 is not None and (suit_totals[0] - n / 4.0) >= thr1),
            ("suit4_plus_linrank", bs + lin > 0),
        )
        for name, bet in decisions:
            if bet:
                stat = res.rules[name]
                stat.selected += 1
                stat.ev_sum += f
                if exact_bet:
                    stat.true_pos += 1
    return res


def format_sb_trackers(res: SbTrackerResult) -> str:
    n = res.rounds
    exact = res.rules["exact"]
    ceiling = exact.ev_sum / n * 100 if n else 0.0
    lines = [
        f"rounds: {n:,}   penetration: {res.penetration:.2f}",
        "",
        "selection rules (all parameters analytic, none fit to this run; "
        "value in TRUE exact ev):",
        f"  {'rule':>18s} {'P(bet)':>8s} {'mean ev':>9s} "
        f"{'u/100':>8s} {'capture':>8s} {'precision':>9s} {'recall':>7s}",
    ]
    for name, st in res.rules.items():
        if st.selected == 0:
            lines.append(f"  {name:>18s}       —")
            continue
        per100 = st.ev_sum / n * 100
        lines.append(
            f"  {name:>18s} {100 * st.selected / n:7.3f}% "
            f"{100 * st.ev_sum / st.selected:+8.3f}% {per100:+7.3f}u "
            f"{100 * per100 / ceiling:7.2f}% "
            f"{100 * st.true_pos / st.selected:8.2f}% "
            f"{100 * st.true_pos / exact.selected:6.2f}%"
        )
    lines.append("")
    lines.append("human index curve (analytic): min excess of richest suit (T1) / "
                 "each of two rich suits (T2) to bet:")
    lines.append(f"  {'cards left':>10s} {'decks':>6s} {'T1':>6s} {'T2':>6s}")
    for cards in (26, 39, 52, 78, 104, 130, 156, 182, 208):
        d = cards / 52
        t1 = res.t1.get(cards)
        t2 = res.t2.get(cards)
        t1s = f"{t1:.1f}" if t1 is not None else "—"
        t2s = f"{t2:.1f}" if t2 is not None else "—"
        lines.append(f"  {cards:>10d} {d:6.2f} {t1s:>6s} {t2s:>6s}")
    return "\n".join(lines)


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


# --- E13 (M9b): Dragon 7 / Panda 8 exact pre-deal EV scan --------------------

BAC_EV_THRESHOLDS = (0.0, 0.02, 0.04)


@dataclass
class BacEvScanResult:
    """One pass of exact Dragon 7 / Panda 8 pre-deal EV vs realized profit.

    Ceiling numbers (P(ev > thr), mean predicted EV) are deterministic
    functions of shoe states — round sampling is their only error. Realized
    per-bin profit and the pooled indicator z-scores are the end-to-end
    consistency checks; the WoO-count row is the same-harness published
    comparator (0.597u/shoe at cut-card-14)."""

    rounds: int = 0
    shoes: int = 0
    penetration: float = 0.0
    realized_d7: float = 0.0
    realized_p8: float = 0.0
    pred_sum_d7: float = 0.0
    pred_sum_p8: float = 0.0
    # ev bin -> BinStat on the WIN INDICATOR (0/1); bin_pred_* sums predicted
    # win probability, so calibration reads realized frequency on predicted
    # probability (same information as EV at 42x less settlement noise).
    by_p_d7: dict = field(default_factory=dict)
    bin_pred_d7: dict = field(default_factory=dict)
    by_p_p8: dict = field(default_factory=dict)
    bin_pred_p8: dict = field(default_factory=dict)
    # decks-left bin -> [n, n_pos_d7, sum_pos_d7, n_pos_p8, sum_pos_p8]
    by_depth: dict = field(default_factory=dict)
    # thr -> [rounds, pred_sum, profit, profit_sq], per bet
    thresholds_d7: dict = field(default_factory=dict)
    thresholds_p8: dict = field(default_factory=dict)
    # WoO count policy (TC >= trigger): [rounds, exact-ev sum, profit, profit_sq]
    woo: list = field(default_factory=lambda: [0, 0.0, 0.0, 0.0])
    # pooled binomial calibration: sum of predicted p and of p(1-p), hits
    cal_d7: list = field(default_factory=lambda: [0.0, 0.0, 0])  # deep: <= 1.5 decks
    cal_d7_all: list = field(default_factory=lambda: [0.0, 0.0, 0])
    cal_p8_all: list = field(default_factory=lambda: [0.0, 0.0, 0])
    # correlation accumulators
    s_d7: float = 0.0
    ss_d7: float = 0.0
    s_p8: float = 0.0
    ss_p8: float = 0.0
    s_tc: float = 0.0
    ss_tc: float = 0.0
    x_d7_tc: float = 0.0
    x_d7_p8: float = 0.0
    n_pos_d7: int = 0
    n_pos_p8: int = 0
    n_pos_both: int = 0

    def _corr(self, sx, ssx, sy, ssy, sxy) -> float:
        n = self.rounds
        vx = ssx / n - (sx / n) ** 2
        vy = ssy / n - (sy / n) ** 2
        if vx <= 0 or vy <= 0:
            return 0.0
        return (sxy / n - sx * sy / n / n) / math.sqrt(vx * vy)

    @property
    def corr_d7_tc(self) -> float:
        return self._corr(self.s_d7, self.ss_d7, self.s_tc, self.ss_tc,
                          self.x_d7_tc)

    @property
    def corr_d7_p8(self) -> float:
        return self._corr(self.s_d7, self.ss_d7, self.s_p8, self.ss_p8,
                          self.x_d7_p8)


def run_bac_ev_scan(rules, *, seed: int, rounds: int) -> BacEvScanResult:
    """Simulate baccarat with Dragon 7 + Panda 8 staked every round, computing
    both bets' EXACT pre-deal EV from the remaining composition each round
    (closed form via `fast_outcomes` — bit-identical to `exact_outcomes`)."""
    from ridefree.baccarat import (
        Dragon7Count,
        FlatBettor,
        _needs_reshuffle as bac_needs_reshuffle,
        composition_from_shoe,
        fast_outcomes,
        play_baccarat_round,
    )

    res = BacEvScanResult(penetration=rules.penetration)
    res.thresholds_d7 = {t: [0, 0.0, 0.0, 0.0] for t in BAC_EV_THRESHOLDS}
    res.thresholds_p8 = {t: [0, 0.0, 0.0, 0.0] for t in BAC_EV_THRESHOLDS}
    p_bin = _bin_p(0.002)
    bettor = FlatBettor(main=None, dragon7=1.0, panda8=1.0)
    count = Dragon7Count()
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    res.shoes = 1
    rounds_since = 0
    for _ in range(rounds):
        if bac_needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            res.shoes += 1
            count.new_shoe()
            rounds_since = 0
        out = fast_outcomes(composition_from_shoe(shoe.remaining_composition()))
        ev_d7 = out.ev_dragon7(rules)
        ev_p8 = out.ev_panda8(rules)
        p_d7 = out.p_dragon7
        p_p8 = out.p_panda8
        tc = count.true_count(shoe.cards_remaining)
        decks_left = shoe.cards_remaining / 52.0
        depth_bin = round(math.floor(decks_left / 0.5) * 0.5, 1)
        start = shoe.snapshot()
        result = play_baccarat_round(rules, shoe, bettor)
        count.observe_cards(result.player_cards + result.banker_cards)
        rounds_since += 1
        hit_d7 = 1 if result.banker_three_card_7 else 0
        hit_p8 = 1 if result.player_three_card_8 else 0

        res.rounds += 1
        res.realized_d7 += result.dragon7_profit
        res.realized_p8 += result.panda8_profit
        res.pred_sum_d7 += ev_d7
        res.pred_sum_p8 += ev_p8
        k = p_bin(p_d7)
        res.by_p_d7.setdefault(k, BinStat()).add(hit_d7)
        res.bin_pred_d7[k] = res.bin_pred_d7.get(k, 0.0) + p_d7
        k = p_bin(p_p8)
        res.by_p_p8.setdefault(k, BinStat()).add(hit_p8)
        res.bin_pred_p8[k] = res.bin_pred_p8.get(k, 0.0) + p_p8
        d = res.by_depth.setdefault(depth_bin, [0, 0, 0.0, 0, 0.0])
        d[0] += 1
        if ev_d7 > 0:
            d[1] += 1
            d[2] += ev_d7
            res.n_pos_d7 += 1
        if ev_p8 > 0:
            d[3] += 1
            d[4] += ev_p8
            res.n_pos_p8 += 1
        if ev_d7 > 0 and ev_p8 > 0:
            res.n_pos_both += 1
        for t, acc in res.thresholds_d7.items():
            if ev_d7 > t:
                acc[0] += 1
                acc[1] += ev_d7
                acc[2] += result.dragon7_profit
                acc[3] += result.dragon7_profit ** 2
        for t, acc in res.thresholds_p8.items():
            if ev_p8 > t:
                acc[0] += 1
                acc[1] += ev_p8
                acc[2] += result.panda8_profit
                acc[3] += result.panda8_profit ** 2
        if tc >= Dragon7Count.TRIGGER:
            res.woo[0] += 1
            res.woo[1] += ev_d7
            res.woo[2] += result.dragon7_profit
            res.woo[3] += result.dragon7_profit ** 2
        res.cal_d7_all[0] += p_d7
        res.cal_d7_all[1] += p_d7 * (1 - p_d7)
        res.cal_d7_all[2] += hit_d7
        res.cal_p8_all[0] += p_p8
        res.cal_p8_all[1] += p_p8 * (1 - p_p8)
        res.cal_p8_all[2] += hit_p8
        if decks_left <= 1.5:
            res.cal_d7[0] += p_d7
            res.cal_d7[1] += p_d7 * (1 - p_d7)
            res.cal_d7[2] += hit_d7
        res.s_d7 += ev_d7
        res.ss_d7 += ev_d7 * ev_d7
        res.s_p8 += ev_p8
        res.ss_p8 += ev_p8 * ev_p8
        res.s_tc += tc
        res.ss_tc += tc * tc
        res.x_d7_tc += ev_d7 * tc
        res.x_d7_p8 += ev_d7 * ev_p8
    return res


def _cal_z(acc) -> tuple[float, float] | None:
    """Pooled binomial consistency: (observed - expected) / sigma, expected."""
    exp, var, hits = acc
    if var <= 0:
        return None
    return (hits - exp) / math.sqrt(var), exp


def format_bac_ev_scan(res: BacEvScanResult, min_cell: int = 2000) -> str:
    n = res.rounds
    rps = n / res.shoes
    lines = [
        f"rounds: {n:,}   shoes: {res.shoes:,} ({rps:.1f} rounds/shoe)   "
        f"penetration: {res.penetration:.3f}",
        f"dragon 7: realized {100 * res.realized_d7 / n:+.4f}%   "
        f"mean predicted {100 * res.pred_sum_d7 / n:+.4f}%",
        f"panda 8:  realized {100 * res.realized_p8 / n:+.4f}%   "
        f"mean predicted {100 * res.pred_sum_p8 / n:+.4f}%",
        f"corr(ev_d7, woo_tc): {res.corr_d7_tc:+.3f}   "
        f"corr(ev_d7, ev_p8): {res.corr_d7_p8:+.3f}",
        f"+EV windows: d7 {100 * res.n_pos_d7 / n:.3f}%  "
        f"p8 {100 * res.n_pos_p8 / n:.3f}%  "
        f"both {100 * res.n_pos_both / n:.3f}%",
        "",
        "ceiling by threshold (bet when exact EV > thr), per bet:",
        f"  {'bet':>4s} {'thr':>5s} {'P(ev>thr)':>10s} {'mean pred':>10s} "
        f"{'realized':>10s} {'±1se':>8s} {'u/100 rounds':>13s} {'u/shoe':>8s}",
    ]
    for label, thresholds in (("d7", res.thresholds_d7),
                              ("p8", res.thresholds_p8)):
        for t, (cnt, pred, prof, prof_sq) in sorted(thresholds.items()):
            if cnt == 0:
                lines.append(f"  {label:>4s} {t:5.2f} {'—':>10s}")
                continue
            frac = cnt / n
            mean_pred = pred / cnt
            mean_real = prof / cnt
            var = max(prof_sq / cnt - mean_real * mean_real, 0.0)
            se = math.sqrt(var / cnt)
            lines.append(
                f"  {label:>4s} {t:5.2f} {100 * frac:9.4f}% "
                f"{100 * mean_pred:+9.4f}% {100 * mean_real:+9.4f}% "
                f"{100 * se:7.4f}% {100 * frac * mean_pred:+12.4f}u "
                f"{pred / res.shoes:+7.4f}u"
            )
    cnt, pred, prof, prof_sq = res.woo
    lines.append("")
    if cnt:
        mean_real = prof / cnt
        var = max(prof_sq / cnt - mean_real * mean_real, 0.0)
        se = math.sqrt(var / cnt)
        lines.append(
            f"WoO count comparator (TC >= +4): bet {100 * cnt / n:.3f}% of "
            f"rounds, exact ev on bet rounds {100 * pred / cnt:+.4f}%, "
            f"realized {100 * mean_real:+.4f}% ± {100 * se:.4f}%"
        )
        lines.append(
            f"  -> {100 * (cnt / n) * (pred / cnt):+.4f}u/100 rounds = "
            f"{pred / res.shoes:+.4f}u/shoe (exact-weighted; published "
            f"0.597u/shoe at cut-14)   realized {prof / res.shoes:+.4f}u/shoe"
        )
    else:
        lines.append("WoO count comparator: no trigger rounds")
    lines.append("")
    lines.append("windows by shoe depth (decks remaining, floor-binned):")
    lines.append(f"  {'decks':>6s} {'rounds':>10s} {'P(d7>0)':>9s} "
                 f"{'mean pos':>9s} {'P(p8>0)':>9s} {'mean pos':>9s}")
    for k in sorted(res.by_depth, reverse=True):
        cnt, pos7, sum7, pos8, sum8 = res.by_depth[k]
        m7 = 100 * sum7 / pos7 if pos7 else 0.0
        m8 = 100 * sum8 / pos8 if pos8 else 0.0
        lines.append(
            f"  {k:6.1f} {cnt:>10,d} {100 * pos7 / cnt:8.4f}% {m7:+8.4f}% "
            f"{100 * pos8 / cnt:8.4f}% {m8:+8.4f}%"
        )
    lines.append("")
    for label, acc in (("d7 all rounds", res.cal_d7_all),
                       ("d7 deep (<=1.5 decks)", res.cal_d7),
                       ("p8 all rounds", res.cal_p8_all)):
        z = _cal_z(acc)
        if z is None:
            continue
        zval, exp = z
        lines.append(
            f"calibration {label}: expected {exp:,.1f} wins, observed "
            f"{acc[2]:,}, z = {zval:+.2f}"
        )
    return "\n".join(lines)
