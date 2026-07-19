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
    # E16: paired profit difference binned by pre-deal hi-lo TC (only rounds
    # actually replayed — every round unless window_only skipped it). The
    # paired variance is tiny, so this resolves per-TC deviation value far
    # beyond what independent arm-vs-arm curves could.
    by_tc: dict = field(default_factory=dict)  # tc bin -> BinStat of the diff

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
        tc_bin = max(-8, min(8, int(round(tracker.hilo_true()))))
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
        result.by_tc.setdefault(tc_bin, BinStat()).add(d)
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


# --- E14 (M9c): human trackers for the Dragon 7 / Panda 8 pair ---------------

# Exact removal effects (EV change per one card removed from the fresh 8-deck
# shoe), derived from `fast_outcomes` 2026-07-17; regeneration-tested in
# tests/test_baccarat.py. Cross-validation: the d7 vector x10 reproduces WoO's
# published optimal "System 1" tags digit-for-digit; the p8 vector's shape
# matches their appendix-8 integer tags.
BAC_EOR_D7 = {0: 0.000863, 1: 0.000498, 2: -0.000896, 3: -0.001076,
              4: -0.002680, 5: -0.002635, 6: -0.003242, 7: -0.003584,
              8: 0.005378, 9: 0.004785}
BAC_EOR_P8 = {0: 0.001208, 1: 0.001322, 2: 0.001444, 3: -0.002861,
              4: -0.002536, 5: -0.002655, 6: -0.000892, 7: -0.000914,
              8: -0.002241, 9: 0.004502}

# First-order model (fraction-space gradient, see E14 notes): for tags equal
# to the removal effects, predicted EV = ev_fresh + (415/52) * TC, so the
# analytic wong-in threshold is TC* = -ev_fresh * 52/415. No fitting.
_LINEAR_SLOPE = 415.0 / 52.0


@dataclass
class BacTrackRow:
    """One policy row: stake `bet` when the row's true count clears trigger."""

    name: str
    bet: str  # "d7" | "p8"
    tags: dict  # baccarat value (0-9) -> tag
    trigger: float
    rounds_bet: int = 0
    ev_sum: float = 0.0  # exact EV of the staked bet on trigger rounds
    profit: float = 0.0
    profit_sq: float = 0.0
    running: float = 0.0

    def new_shoe(self) -> None:
        self.running = 0.0

    def observe_cards(self, cards) -> None:
        for card in cards:
            self.running += self.tags.get(card % 10, 0.0)


# The PLAYABLE integer tags: the exact removal effects (x1000), rounded
# UNDER A BALANCE CONSTRAINT — an unbalanced count's running total drifts
# with depth and wrecks the true-count conversion (verified the hard way:
# the naive rounding summed to -4/deck and its triggers never fired). Ties
# are broken toward balance with minimum distortion: d7 rounds the ace UP
# (its effect is genuinely positive); p8 rounds 4 and 5 to -2. The p8 set is
# one step from WoO's appendix tags (sharper 3 and 9). d7 is WoO System 1
# rounded. Balance is asserted in bac_track_rows and regeneration-tested.
PAPER_TAGS_D7 = {0: 1, 1: 1, 2: -1, 3: -1, 4: -3, 5: -3, 6: -3, 7: -4,
                 8: 5, 9: 5}
PAPER_TAGS_P8 = {0: 1, 1: 1, 2: 1, 3: -3, 4: -2, 5: -2, 6: -1, 7: -1,
                 8: -2, 9: 5}


def _assert_balanced(tags: dict) -> dict:
    total = sum((16 if v == 0 else 4) * tags.get(v, 0) for v in range(10))
    if total != 0:
        raise ValueError(f"unbalanced tag set (sum {total}/deck): {tags}")
    return tags

# Per-card frequency weights for the analytic trigger of an arbitrary tag set.
_CARD_FREQ = {v: (16.0 if v == 0 else 4.0) / 52.0 for v in range(10)}


def analytic_trigger(tags: dict, eors: dict, ev_fresh_deficit: float) -> float:
    """True-count trigger for integer tags, no fitting: the least-squares
    projection of the first-order EV model onto the count. Predicted EV shift
    per TC unit = (415/52) * cov_f(eor, tags) / var_f(tags) (frequency-
    weighted, means are ~0 for near-balanced counts); bet when the predicted
    shift covers the fresh-shoe deficit."""
    num = sum(_CARD_FREQ[v] * eors[v] * tags.get(v, 0) for v in range(10))
    den = sum(_CARD_FREQ[v] * tags.get(v, 0) ** 2 for v in range(10))
    slope = _LINEAR_SLOPE * num / den
    return ev_fresh_deficit / slope


def bac_track_rows() -> list:
    """The E14 row set. Triggers: published rows use the published triggers
    (WoO d7 TC>=4; WoO p8 appendix TC>=11); linear-EOR and paper rows use
    analytic thresholds from the first-order model. The shared-count row
    quantifies what a single (d7) count loses when it must also trigger the
    panda."""
    d7_thr = 0.076113 / _LINEAR_SLOPE
    p8_thr = 0.101876 / _LINEAR_SLOPE
    d7_paper_thr = analytic_trigger(_assert_balanced(PAPER_TAGS_D7),
                                    BAC_EOR_D7, 0.076113)
    p8_paper_thr = analytic_trigger(_assert_balanced(PAPER_TAGS_P8),
                                    BAC_EOR_P8, 0.101876)
    return [
        BacTrackRow("d7 linear-EOR (analytic)", "d7", dict(BAC_EOR_D7), d7_thr),
        BacTrackRow(f"d7 PAPER tags @ TC>={d7_paper_thr:.1f}", "d7",
                    dict(PAPER_TAGS_D7), d7_paper_thr),
        BacTrackRow("d7 WoO count @ TC>=4", "d7",
                    {4: -1, 5: -1, 6: -1, 7: -1, 8: 2, 9: 2}, 4.0),
        BacTrackRow("p8 linear-EOR (analytic)", "p8", dict(BAC_EOR_P8), p8_thr),
        BacTrackRow(f"p8 PAPER tags @ TC>={p8_paper_thr:.1f}", "p8",
                    dict(PAPER_TAGS_P8), p8_paper_thr),
        BacTrackRow("p8 WoO appendix @ TC>=11", "p8",
                    {0: 1, 1: 1, 2: 1, 3: -2, 4: -2, 5: -2, 6: -1, 7: -1,
                     8: -2, 9: 4}, 11.0),
        BacTrackRow("p8 on d7-count trigger (shared-count cost)", "p8",
                    dict(BAC_EOR_D7), d7_thr),
    ]


@dataclass
class BacTrackResult:
    rounds: int = 0
    shoes: int = 0
    penetration: float = 0.0
    # exact ceilings accumulated on the same rounds, for capture denominators
    ceiling_d7: float = 0.0  # sum of max(ev_d7, 0)
    ceiling_p8: float = 0.0
    rows: list = field(default_factory=list)


def run_bac_track(rules, *, seed: int, rounds: int) -> BacTrackResult:
    """Score the E14 policy rows against exact EV, same shoes for all rows.

    Every row's bet is scored in TRUE exact EV (the E11b doctrine) and also
    settled for real (realized column). All parameters are analytic or
    published — nothing is fit to simulation data."""
    from ridefree.baccarat import (
        FlatBettor,
        _needs_reshuffle as bac_needs_reshuffle,
        composition_from_shoe,
        fast_outcomes,
        play_baccarat_round,
    )

    res = BacTrackResult(penetration=rules.penetration, rows=bac_track_rows())
    bettor = FlatBettor(main=None, dragon7=1.0, panda8=1.0)
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    res.shoes = 1
    rounds_since = 0
    for _ in range(rounds):
        if bac_needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            res.shoes += 1
            for row in res.rows:
                row.new_shoe()
            rounds_since = 0
        out = fast_outcomes(composition_from_shoe(shoe.remaining_composition()))
        ev = {"d7": out.ev_dragon7(rules), "p8": out.ev_panda8(rules)}
        decks_left = shoe.cards_remaining / 52.0
        triggered = []
        for row in res.rows:
            tc = row.running / decks_left if decks_left > 0 else 0.0
            if tc >= row.trigger:
                triggered.append(row)
        result = play_baccarat_round(rules, shoe, bettor)
        rounds_since += 1
        realized = {"d7": result.dragon7_profit, "p8": result.panda8_profit}
        for row in res.rows:
            row.observe_cards(result.player_cards + result.banker_cards)
        for row in triggered:
            row.rounds_bet += 1
            row.ev_sum += ev[row.bet]
            p = realized[row.bet]
            row.profit += p
            row.profit_sq += p * p
        res.rounds += 1
        res.ceiling_d7 += max(ev["d7"], 0.0)
        res.ceiling_p8 += max(ev["p8"], 0.0)
    return res


def format_bac_track(res: BacTrackResult) -> str:
    n = res.rounds
    lines = [
        f"rounds: {n:,}   shoes: {res.shoes:,}   penetration: "
        f"{res.penetration:.3f}",
        f"exact ceilings: d7 {100 * res.ceiling_d7 / n:+.4f}u/100 "
        f"({res.ceiling_d7 / res.shoes:+.4f}u/shoe)   "
        f"p8 {100 * res.ceiling_p8 / n:+.4f}u/100 "
        f"({res.ceiling_p8 / res.shoes:+.4f}u/shoe)",
        "",
        f"  {'row':<44} {'bet%':>7} {'mean ev':>8} {'u/100':>8} "
        f"{'u/shoe':>8} {'capture':>8} {'realized':>9}",
    ]
    for row in res.rows:
        ceiling = res.ceiling_d7 if row.bet == "d7" else res.ceiling_p8
        if row.rounds_bet == 0:
            lines.append(f"  {row.name:<44} {'—':>7}")
            continue
        frac = row.rounds_bet / n
        mean_ev = row.ev_sum / row.rounds_bet
        mean_real = row.profit / row.rounds_bet
        var = max(row.profit_sq / row.rounds_bet - mean_real ** 2, 0.0)
        se = math.sqrt(var / row.rounds_bet)
        lines.append(
            f"  {row.name:<44} {100 * frac:6.3f}% {100 * mean_ev:+7.3f}% "
            f"{100 * frac * mean_ev:+7.4f}u {row.ev_sum / res.shoes:+7.4f}u "
            f"{100 * row.ev_sum / ceiling:7.2f}% "
            f"{100 * mean_real:+7.3f}%±{100 * se:.2f}"
        )
    return "\n".join(lines)


# --- E15 (M9 epilogue): how much of the ceiling is beyond ANY linear count? --


def _bac_taylor_grid(rules, step: int = 13, n_min: int = 39):
    """Per-depth exact Taylor terms of both side-bet EVs around the BALANCED
    composition: B (level), g (gradient), H (Hessian), by finite differences
    of the fractional evaluator. All analytic — nothing fit to simulation."""
    from ridefree.baccarat import frac_probs

    freq = {v: (16.0 if v == 0 else 4.0) / 52.0 for v in range(10)}
    pays = (rules.dragon7_pays, rules.panda8_pays)

    def ev2(comp):
        pd, pp = frac_probs(comp)
        return (pd * (pays[0] + 1.0) - 1.0, pp * (pays[1] + 1.0) - 1.0)

    grid = {}
    max_n = rules.decks * 52
    for n_total in range(n_min, max_n + 1, step):
        base = {v: n_total * freq[v] for v in range(10)}
        b = ev2(base)
        plus, minus = {}, {}
        for v in range(10):
            up = dict(base); up[v] += 1.0
            dn = dict(base); dn[v] -= 1.0
            plus[v], minus[v] = ev2(up), ev2(dn)
        g = [[0.5 * (plus[v][i] - minus[v][i]) for v in range(10)]
             for i in range(2)]
        h = [[[0.0] * 10 for _ in range(10)] for _ in range(2)]
        for i in range(2):
            for v in range(10):
                h[i][v][v] = plus[v][i] + minus[v][i] - 2.0 * b[i]
        for v in range(10):
            for w in range(v + 1, 10):
                pp_c = dict(base); pp_c[v] += 1.0; pp_c[w] += 1.0
                pm_c = dict(base); pm_c[v] += 1.0; pm_c[w] -= 1.0
                mp_c = dict(base); mp_c[v] -= 1.0; mp_c[w] += 1.0
                mm_c = dict(base); mm_c[v] -= 1.0; mm_c[w] -= 1.0
                e_pp, e_pm, e_mp, e_mm = ev2(pp_c), ev2(pm_c), ev2(mp_c), ev2(mm_c)
                for i in range(2):
                    val = 0.25 * (e_pp[i] - e_pm[i] - e_mp[i] + e_mm[i])
                    h[i][v][w] = h[i][w][v] = val
        grid[n_total] = (b, g, h)
    return grid, freq


@dataclass
class BacOrderResult:
    rounds: int = 0
    penetration: float = 0.0
    ceiling_d7: float = 0.0
    ceiling_p8: float = 0.0
    # selection value (sum of TRUE exact ev on bet rounds) per model order
    lin_d7: float = 0.0
    lin_p8: float = 0.0
    quad_d7: float = 0.0
    quad_p8: float = 0.0


def run_bac_order_scan(rules, *, seed: int, rounds: int) -> BacOrderResult:
    """Score 'bet when the ORDER-k Taylor model is positive' in TRUE exact EV.

    The order-1 row is the ceiling of EVERY possible linear count (depth-exact
    coefficients, better than any static-tag true count); order-2 adds the
    exact quadratic. The gap order-1 -> exact is what no linear count can
    reach; the gap order-2 -> exact is genuinely high-order."""
    from ridefree.baccarat import (
        FlatBettor,
        _needs_reshuffle as bac_needs_reshuffle,
        composition_from_shoe,
        fast_outcomes,
        play_baccarat_round,
    )

    grid, freq = _bac_taylor_grid(rules)
    ns = sorted(grid)
    res = BacOrderResult(penetration=rules.penetration)
    bettor = FlatBettor(main=None)
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    rounds_since = 0
    for _ in range(rounds):
        if bac_needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            rounds_since = 0
        comp = composition_from_shoe(shoe.remaining_composition())
        n_total = sum(comp.values())
        out = fast_outcomes(comp)
        ev = (out.ev_dragon7(rules), out.ev_panda8(rules))
        # nearest grid points, linear interpolation in N
        hi = min((n for n in ns if n >= n_total), default=ns[-1])
        lo = max((n for n in ns if n <= n_total), default=ns[0])
        t = 0.0 if hi == lo else (n_total - lo) / (hi - lo)
        e = [comp[v] - n_total * freq[v] for v in range(10)]
        model = [0.0, 0.0], [0.0, 0.0]  # (lin, quad) x (d7, p8)
        for i in range(2):
            vals = []
            for n_ref in (lo, hi):
                b, g, h = grid[n_ref]
                lin = b[i] + sum(g[i][v] * e[v] for v in range(10))
                quad = lin + 0.5 * sum(
                    h[i][v][w] * e[v] * e[w]
                    for v in range(10) for w in range(10))
                vals.append((lin, quad))
            model[0][i] = vals[0][0] * (1 - t) + vals[1][0] * t
            model[1][i] = vals[0][1] * (1 - t) + vals[1][1] * t
        play_baccarat_round(rules, shoe, bettor)
        rounds_since += 1
        res.rounds += 1
        res.ceiling_d7 += max(ev[0], 0.0)
        res.ceiling_p8 += max(ev[1], 0.0)
        if model[0][0] > 0:
            res.lin_d7 += ev[0]
        if model[0][1] > 0:
            res.lin_p8 += ev[1]
        if model[1][0] > 0:
            res.quad_d7 += ev[0]
        if model[1][1] > 0:
            res.quad_p8 += ev[1]
    return res


def format_bac_order(res: BacOrderResult) -> str:
    lines = [
        f"rounds: {res.rounds:,}   penetration: {res.penetration:.3f}",
        "capture of the exact ceiling by Taylor order (TRUE-exact-EV scored;",
        "tangent models at the balanced composition, depth-exact coefficients —",
        "NOT a strict supremum over the class: at the extreme compositions",
        "where selection happens, a static count fit to the fluctuation",
        "distribution can beat the tangent, cf. the E14 p8 rows):",
        f"  {'model':<38} {'dragon 7':>9} {'panda 8':>9}",
    ]
    for label, d7, p8 in (
        ("order-1 tangent (linear class)", res.lin_d7, res.lin_p8),
        ("order-2 tangent (+ exact quadratic)", res.quad_d7, res.quad_p8),
    ):
        lines.append(f"  {label:<38} {100 * d7 / res.ceiling_d7:8.2f}% "
                     f"{100 * p8 / res.ceiling_p8:8.2f}%")
    lines.append(f"  (ceilings this run: d7 {100 * res.ceiling_d7 / res.rounds:+.4f}"
                 f"u/100, p8 {100 * res.ceiling_p8 / res.rounds:+.4f}u/100)")
    return "\n".join(lines)


# --- E16: standard-game hi-lo TC curve + configurable bet ramps --------------
#
# The cover-ledger design (docs/EXPERIMENTS.md E16): one flat-bet pass banks
# per-true-count bins of round profit (mean AND second moment, so variance is
# free) plus the insurance attribution; every betting pattern is then ledger
# arithmetic over the banked bins (data/e16_ledger.py), and only chosen
# operating points get a live verification run via run_ramp. Rounds are always
# PLAYED at bet=1 and profit scaled by the round's bet: profit is exactly
# linear in the initial bet (every wager, insurance included, derives from
# it), so scaling is exact and the card stream is identical across ramps —
# common random numbers for free. A bet of 0 is a sit-out round: the hand is
# still played out (cards must flow for the count to move — the table-with-
# other-players model), it just carries no money.


def _bin_tc8(value: float) -> int:
    """Integer TC bins clamped to ±8 (ramps are flat beyond; the tails pool)."""
    return max(-8, min(8, int(round(value))))


E16_ARMS = ("basic", "ins", "full")


def _arm_strategy(rules: Rules, arm: str):
    """The three E16 playing arms: pure chart / +composition insurance /
    +composition deviations (each layer is the exact ceiling of its human
    approximation — indexes are distillations of these)."""
    from ridefree.player_ev import CompositionPlayer, OptimalStrategy

    if arm == "basic":
        return OptimalStrategy()
    if arm == "ins":
        return CompositionPlayer(rules.decks, insurance=True, deviations=False)
    if arm == "full":
        return CompositionPlayer(rules.decks, insurance=True, deviations=True)
    raise ValueError(f"unknown arm {arm!r}; expected one of {E16_ARMS}")


@dataclass
class TcBin:
    rounds: int = 0
    profit: float = 0.0
    profit_sq: float = 0.0
    tc_sum: float = 0.0  # exact (unbinned) TC, for within-bin means
    ins_rounds: int = 0
    ins_profit: float = 0.0

    def add(self, profit: float, tc: float, result) -> None:
        self.rounds += 1
        self.profit += profit
        self.profit_sq += profit * profit
        self.tc_sum += tc
        if result.insurance_stake:
            self.ins_rounds += 1
            self.ins_profit += result.insurance_profit

    @property
    def ev(self) -> float:
        return self.profit / self.rounds if self.rounds else 0.0

    @property
    def var(self) -> float:
        if not self.rounds:
            return 0.0
        m = self.ev
        return max(self.profit_sq / self.rounds - m * m, 0.0)

    @property
    def stderr(self) -> float:
        return math.sqrt(self.var / self.rounds) if self.rounds >= 2 else 0.0


@dataclass
class TcCurveResult:
    rules_name: str
    arm: str
    penetration: float
    rounds: int = 0
    total_profit: float = 0.0
    bins: dict[int, TcBin] = field(default_factory=dict)

    @property
    def overall_ev(self) -> float:
        return self.total_profit / self.rounds if self.rounds else 0.0


def run_tc_curve(
    rules: Rules, arm: str, *, seed: int, rounds: int, rules_name: str = ""
) -> TcCurveResult:
    """Flat-bet pass binning per-round profit by pre-deal hi-lo true count."""
    strategy = _arm_strategy(rules, arm)
    on_round = getattr(strategy, "observe_round", None)
    on_shuffle = getattr(strategy, "new_shoe", None)
    res = TcCurveResult(rules_name=rules_name, arm=arm, penetration=rules.penetration)
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    tracker = CompositionTracker(rules.decks)
    rounds_since = 0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            tracker.new_shoe()
            rounds_since = 0
            if on_shuffle is not None:
                on_shuffle()
        tc = tracker.hilo_true()
        result = play_round(rules, shoe, strategy, bet=1.0)
        rounds_since += 1
        tracker.observe_round(result)
        if on_round is not None:
            on_round(result)
        res.rounds += 1
        res.total_profit += result.profit
        res.bins.setdefault(_bin_tc8(tc), TcBin()).add(result.profit, tc, result)
    return res


def tc_curve_to_json(res: TcCurveResult, seed: int) -> dict:
    return {
        "kind": "tc_curve",
        "rules": res.rules_name,
        "arm": res.arm,
        "penetration": res.penetration,
        "seed": seed,
        "rounds": res.rounds,
        "total_profit": res.total_profit,
        "bins": {
            str(k): [b.rounds, b.profit, b.profit_sq, b.tc_sum,
                     b.ins_rounds, b.ins_profit]
            for k, b in res.bins.items()
        },
    }


def load_tc_curve_json(path: str) -> TcCurveResult:
    import json

    with open(path) as f:
        payload = json.load(f)
    if payload.get("kind") != "tc_curve":
        raise ValueError(f"{path} is not a tc_curve dump")
    res = TcCurveResult(
        rules_name=payload["rules"],
        arm=payload["arm"],
        penetration=payload["penetration"],
        rounds=payload["rounds"],
        total_profit=payload["total_profit"],
    )
    for key, (n, p, p2, tcs, ir, ip) in payload["bins"].items():
        res.bins[int(key)] = TcBin(
            rounds=n, profit=p, profit_sq=p2, tc_sum=tcs,
            ins_rounds=ir, ins_profit=ip,
        )
    return res


def merge_tc_curves(results: list[TcCurveResult]) -> TcCurveResult:
    """Pool independently-seeded curve runs (bin stats are additive)."""
    assert results
    first = results[0]
    merged = TcCurveResult(
        rules_name=first.rules_name, arm=first.arm, penetration=first.penetration
    )
    for r in results:
        assert (r.rules_name, r.arm, r.penetration) == (
            first.rules_name, first.arm, first.penetration
        ), "cannot pool curves from different games/arms"
        merged.rounds += r.rounds
        merged.total_profit += r.total_profit
        for k, b in r.bins.items():
            t = merged.bins.setdefault(k, TcBin())
            t.rounds += b.rounds
            t.profit += b.profit
            t.profit_sq += b.profit_sq
            t.tc_sum += b.tc_sum
            t.ins_rounds += b.ins_rounds
            t.ins_profit += b.ins_profit
    return merged


def format_tc_curve(res: TcCurveResult, min_rounds: int = 1000) -> str:
    lines = [
        f"rules: {res.rules_name}   arm: {res.arm}   "
        f"penetration: {res.penetration:.2f}",
        f"rounds: {res.rounds:,}   overall EV: {100 * res.overall_ev:+.4f}%",
        "",
        f"  {'tc':>4s} {'rounds':>11s} {'freq':>8s} {'EV':>9s} {'±1se':>8s} "
        f"{'sd':>6s} {'mean tc':>8s} {'ins/round':>10s}",
    ]
    for k in sorted(res.bins):
        b = res.bins[k]
        if b.rounds < min_rounds:
            continue
        ins = 100 * b.ins_profit / b.rounds if b.rounds else 0.0
        lines.append(
            f"  {k:+4d} {b.rounds:>11,d} {100 * b.rounds / res.rounds:7.3f}% "
            f"{100 * b.ev:+8.3f}% {100 * b.stderr:7.3f}% "
            f"{math.sqrt(b.var):6.3f} {b.tc_sum / b.rounds:+8.2f} {ins:+9.4f}%"
        )
    return "\n".join(lines)


# --- E16: configurable bet ramp, simulated live (the verification arm) -------


def parse_ramp(spec: str) -> tuple[tuple[float, float], ...]:
    """Parse 'min_tc:units,min_tc:units,...' into a sorted step function.

    The bet at true count tc is the units of the highest min_tc <= tc; below
    the lowest step the bet is 0 (wong-out / sit-out). A flat bet is '-99:1'.
    Example 1-8 spread with exit: '-99:0,-1:1,1:2,2:4,3:6,4:8'.
    """
    steps = []
    for part in spec.split(","):
        lo, _, units = part.partition(":")
        steps.append((float(lo), float(units)))
    steps.sort()
    return tuple(steps)


def ramp_bet(ramp: tuple[tuple[float, float], ...], tc: float) -> float:
    bet = 0.0
    for lo, units in ramp:
        if tc >= lo:
            bet = units
        else:
            break
    return bet


@dataclass
class RampResult:
    rules_name: str
    arm: str
    penetration: float
    ramp: tuple = ()
    rounds: int = 0
    rounds_bet: int = 0  # rounds with a nonzero bet
    bet_sum: float = 0.0  # total units staked (initial bets)
    profit: float = 0.0  # bet-scaled units
    profit_sq: float = 0.0
    ins_profit: float = 0.0  # bet-scaled, inside profit
    # corr(bet, tc) accumulators over ALL observed rounds
    s_bet: float = 0.0
    ss_bet: float = 0.0
    s_tc: float = 0.0
    ss_tc: float = 0.0
    x_bet_tc: float = 0.0

    @property
    def ev_per_round(self) -> float:
        return self.profit / self.rounds if self.rounds else 0.0

    @property
    def std_per_round(self) -> float:
        if self.rounds < 2:
            return 0.0
        m = self.ev_per_round
        return math.sqrt(max(self.profit_sq / self.rounds - m * m, 0.0))

    @property
    def ev_stderr(self) -> float:
        return self.std_per_round / math.sqrt(self.rounds) if self.rounds else 0.0

    @property
    def money_edge(self) -> float:
        """Profit per unit staked (the 'edge on money' convention)."""
        return self.profit / self.bet_sum if self.bet_sum else 0.0

    @property
    def corr_bet_tc(self) -> float:
        n = self.rounds
        if not n:
            return 0.0
        vb = self.ss_bet / n - (self.s_bet / n) ** 2
        vt = self.ss_tc / n - (self.s_tc / n) ** 2
        if vb <= 0 or vt <= 0:
            return 0.0
        cov = self.x_bet_tc / n - (self.s_bet / n) * (self.s_tc / n)
        return cov / math.sqrt(vb * vt)


def run_ramp(
    rules: Rules,
    arm: str,
    ramp: tuple[tuple[float, float], ...],
    *,
    seed: int,
    rounds: int,
    rules_name: str = "",
) -> RampResult:
    """Simulate a bet ramp live: bet(tc) chosen pre-deal from the tracked
    count, the round played at bet=1 and its profit scaled (exact — see the
    section comment). This is the verification arm for the ledger arithmetic
    and the repo's first betting simulator (STATUS 'combined-play' item)."""
    strategy = _arm_strategy(rules, arm)
    on_round = getattr(strategy, "observe_round", None)
    on_shuffle = getattr(strategy, "new_shoe", None)
    res = RampResult(
        rules_name=rules_name, arm=arm, penetration=rules.penetration, ramp=ramp
    )
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    tracker = CompositionTracker(rules.decks)
    rounds_since = 0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            tracker.new_shoe()
            rounds_since = 0
            if on_shuffle is not None:
                on_shuffle()
        tc = tracker.hilo_true()
        b = ramp_bet(ramp, tc)
        result = play_round(rules, shoe, strategy, bet=1.0)
        rounds_since += 1
        tracker.observe_round(result)
        if on_round is not None:
            on_round(result)
        p = b * result.profit
        res.rounds += 1
        if b:
            res.rounds_bet += 1
            res.bet_sum += b
        res.profit += p
        res.profit_sq += p * p
        res.ins_profit += b * result.insurance_profit
        res.s_bet += b
        res.ss_bet += b * b
        res.s_tc += tc
        res.ss_tc += tc * tc
        res.x_bet_tc += b * tc
    return res


# --- E17: unbalanced running counts for the crouch (no-division play) --------
#
# An unbalanced count (per-deck tag sum s != 0) read as a RAW running count
# encodes depth implicitly: with the initial running count pivot-zeroed at
# IRC = -s*decks, RC ~= decks_remaining * (TC - s), so RC >= 0 tests TC >= s
# EXACTLY at every depth — no division, no deck estimation. Off-pivot
# thresholds blur with depth; banking EV per RC bin prices that blur honestly
# (a fixed-RC play IS what a human executes). Red 7 (red sevens +1, s=+2)
# puts the pivot exactly on the crouch's jump threshold.

# Half-bump devices: rank -> +1 on two of the four suits (the red-7 trick
# generalized). Suits {0,1} are "red" by convention (arbitrary, symmetric).
_RED_SUITS = (0, 1)

TEN_RANK = 10


def unbalanced_bc(base_tags: dict[int, float], eors: dict[int, float]) -> float:
    """Betting correlation of a (possibly fractional) tag vector with an EOR
    vector: card-frequency-weighted Pearson correlation over the 52 cards."""
    w = {r: (16 if r == TEN_RANK else 4) for r in range(1, 11)}
    n = 52.0
    mt = sum(w[r] * base_tags[r] for r in w) / n
    me = sum(w[r] * eors[r] for r in w) / n
    vt = sum(w[r] * (base_tags[r] - mt) ** 2 for r in w)
    ve = sum(w[r] * (eors[r] - me) ** 2 for r in w)
    cov = sum(w[r] * (base_tags[r] - mt) * (eors[r] - me) for r in w)
    return cov / math.sqrt(vt * ve) if vt > 0 and ve > 0 else 0.0


def search_unbalanced_level1(eors: dict[int, float], top: int = 3):
    """Best level-1 unbalanced counts with per-deck imbalance +2 (pivot at
    TC ~ +2): integer base tags in {-1,0,+1} for A..9, ten fixed at -1, plus
    ONE half-rank bump (+1 on two suits of one rank — the red-7 device).
    Imbalance = 4*sum(base A..9) - 16 + 2*b = +2 with b=+1 forces
    sum(base A..9) = 4. Ranked by betting correlation vs `eors`. Analytic —
    nothing fit to simulation data."""
    import itertools

    results = []
    ranks = list(range(1, 10))
    for tags in itertools.product((-1, 0, 1), repeat=9):
        if sum(tags) != 4:
            continue
        base = dict(zip(ranks, tags))
        base[TEN_RANK] = -1
        for bump in ranks:  # half-bump rank (raw suits exist only for 1..9)
            eff = dict(base)
            eff[bump] = eff[bump] + 0.5  # two of four suits at +1
            bc = unbalanced_bc(eff, eors)
            results.append((bc, tuple(sorted(base.items())), bump))
    results.sort(reverse=True)
    return results[:top]


@dataclass
class CountCurvesResult:
    rules_name: str
    arm: str
    penetration: float
    rounds: int = 0
    total_profit: float = 0.0
    # signal name -> {bin -> TcBin}
    by_signal: dict[str, dict] = field(default_factory=dict)


def _clamp_rc(value: float) -> int:
    return max(-40, min(40, int(round(value))))


def run_count_curves(
    rules: Rules,
    arm: str,
    *,
    seed: int,
    rounds: int,
    rules_name: str = "",
    custom: tuple[dict[int, int], int] | None = None,
) -> CountCurvesResult:
    """One flat-bet pass banking per-round profit into bins of SEVERAL count
    signals at once (same card stream — directly comparable):

      hilo_tc   — rounded hi-lo true count (E16 reference / cross-check)
      red7_rc   — hi-lo + red sevens +1, pivot-zeroed IRC (s=+2, pivot TC+2)
      ko_rc     — hi-lo + all sevens +1, pivot-zeroed IRC (s=+4, pivot TC+4)
      half7_rc  — hi-lo + sevens at +0.5: the deterministic ideal red-7
                  (what red-7 approximates with color noise)
      custom_rc — optional (base_tags, bump_rank) from the analytic search

    Insurance attribution rides on every signal's bins (TcBin.add)."""
    strategy = _arm_strategy(rules, arm)
    on_round = getattr(strategy, "observe_round", None)
    on_shuffle = getattr(strategy, "new_shoe", None)
    res = CountCurvesResult(
        rules_name=rules_name, arm=arm, penetration=rules.penetration
    )
    names = ["hilo_tc", "red7_rc", "ko_rc", "half7_rc"]
    if custom is not None:
        names.append("custom_rc")
    res.by_signal = {n: {} for n in names}
    decks = rules.decks
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    tracker = CompositionTracker(decks)
    raw = RawCompositionTracker(decks)
    rounds_since = 0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            tracker.new_shoe()
            raw.new_shoe()
            rounds_since = 0
            if on_shuffle is not None:
                on_shuffle()
        bal = tracker.hilo_running()
        sevens_dealt = 4 * decks - tracker.counts[7]
        red7_dealt = sum(decks - raw.counts[(7, s)] for s in _RED_SUITS)
        signals = {
            "hilo_tc": _bin_tc8(tracker.hilo_true()),
            "red7_rc": _clamp_rc(bal + red7_dealt - 2 * decks),
            "ko_rc": _clamp_rc(bal + sevens_dealt - 4 * decks),
            "half7_rc": _clamp_rc(bal + 0.5 * sevens_dealt - 2 * decks),
        }
        if custom is not None:
            base_tags, bump = custom  # bump rank in 1..9 (two red suits +1)
            dealt = {
                r: (16 if r == TEN_RANK else 4) * decks - tracker.counts[r]
                for r in range(1, 11)
            }
            bump_dealt = sum(decks - raw.counts[(bump, s)] for s in _RED_SUITS)
            s_deck = sum(
                base_tags[r] * (16 if r == TEN_RANK else 4) for r in range(1, 11)
            ) + 2  # per-deck imbalance incl. the half-rank bump
            rc = (sum(base_tags[r] * dealt[r] for r in range(1, 11))
                  + bump_dealt - s_deck * decks)  # pivot-zeroed IRC
            signals["custom_rc"] = _clamp_rc(rc)
        tc_exact = tracker.hilo_true()
        start = shoe.snapshot()
        result = play_round(rules, shoe, strategy, bet=1.0)
        rounds_since += 1
        tracker.observe_round(result)
        raw.observe(shoe.raw_slice(start, shoe.snapshot()))
        if on_round is not None:
            on_round(result)
        res.rounds += 1
        res.total_profit += result.profit
        for name, key in signals.items():
            res.by_signal[name].setdefault(key, TcBin()).add(
                result.profit, tc_exact, result
            )
    return res


def count_curves_to_json(res: CountCurvesResult, seed: int, custom=None) -> dict:
    return {
        "kind": "count_curves",
        "rules": res.rules_name,
        "arm": res.arm,
        "penetration": res.penetration,
        "seed": seed,
        "custom": (
            None if custom is None
            else {"tags": {str(r): t for r, t in custom[0].items()},
                  "bump": custom[1]}
        ),
        "rounds": res.rounds,
        "total_profit": res.total_profit,
        "signals": {
            name: {
                str(k): [b.rounds, b.profit, b.profit_sq, b.tc_sum,
                         b.ins_rounds, b.ins_profit]
                for k, b in bins.items()
            }
            for name, bins in res.by_signal.items()
        },
    }


def load_count_curves_json(path: str) -> CountCurvesResult:
    import json

    with open(path) as f:
        payload = json.load(f)
    if payload.get("kind") != "count_curves":
        raise ValueError(f"{path} is not a count_curves dump")
    res = CountCurvesResult(
        rules_name=payload["rules"],
        arm=payload["arm"],
        penetration=payload["penetration"],
        rounds=payload["rounds"],
        total_profit=payload["total_profit"],
    )
    for name, bins in payload["signals"].items():
        res.by_signal[name] = {
            int(k): TcBin(rounds=n, profit=p, profit_sq=p2, tc_sum=tcs,
                          ins_rounds=ir, ins_profit=ip)
            for k, (n, p, p2, tcs, ir, ip) in bins.items()
        }
    return res


def merge_count_curves(results: list[CountCurvesResult]) -> CountCurvesResult:
    assert results
    first = results[0]
    merged = CountCurvesResult(
        rules_name=first.rules_name, arm=first.arm, penetration=first.penetration
    )
    for r in results:
        assert (r.rules_name, r.arm, r.penetration) == (
            first.rules_name, first.arm, first.penetration
        )
        assert sorted(r.by_signal) == sorted(first.by_signal)
        merged.rounds += r.rounds
        merged.total_profit += r.total_profit
        for name, bins in r.by_signal.items():
            target = merged.by_signal.setdefault(name, {})
            for k, b in bins.items():
                t = target.setdefault(k, TcBin())
                t.rounds += b.rounds
                t.profit += b.profit
                t.profit_sq += b.profit_sq
                t.tc_sum += b.tc_sum
                t.ins_rounds += b.ins_rounds
                t.ins_profit += b.ins_profit
    return merged


def format_count_curves(res: CountCurvesResult, min_rounds: int = 5000) -> str:
    lines = [
        f"rules: {res.rules_name}   arm: {res.arm}   "
        f"penetration: {res.penetration:.2f}   rounds: {res.rounds:,}   "
        f"overall EV: {100 * res.total_profit / res.rounds:+.4f}%",
    ]
    for name, bins in res.by_signal.items():
        lines.append("")
        lines.append(f"EV by {name} (bins with >= {min_rounds:,} rounds):")
        lines.append(f"  {'bin':>5s} {'rounds':>11s} {'freq':>8s} {'EV':>9s} "
                     f"{'±1se':>8s} {'mean hilo tc':>13s}")
        for k in sorted(bins):
            b = bins[k]
            if b.rounds < min_rounds:
                continue
            lines.append(
                f"  {k:+5d} {b.rounds:>11,d} {100 * b.rounds / res.rounds:7.3f}% "
                f"{100 * b.ev:+8.3f}% {100 * b.stderr:7.3f}% "
                f"{b.tc_sum / b.rounds:+13.2f}"
            )
    return "\n".join(lines)


def format_ramp(res: RampResult) -> str:
    ramp_txt = ",".join(f"{lo:g}:{u:g}" for lo, u in res.ramp)
    n = res.rounds
    lines = [
        f"rules: {res.rules_name}   arm: {res.arm}   "
        f"penetration: {res.penetration:.2f}",
        f"ramp (min_tc:units): {ramp_txt}",
        f"rounds observed: {n:,}   bet: {res.rounds_bet:,} "
        f"({100 * res.rounds_bet / n:.2f}%)   avg bet: {res.s_bet / n:.3f}u/round",
        f"EV: {100 * res.ev_per_round:+.4f} ± {100 * res.ev_stderr:.4f} u/100 "
        f"observed rounds   (money edge {100 * res.money_edge:+.4f}% per unit "
        f"staked)",
        f"per-round sd: {res.std_per_round:.3f}u   corr(bet, tc): "
        f"{res.corr_bet_tc:+.3f}",
    ]
    if res.ins_profit:
        lines.append(f"insurance contribution: {100 * res.ins_profit / n:+.4f}u/100")
    return "\n".join(lines)


# --- M10b: Pot of Gold per-TC curve (side and main profit binned separately) --
#
# The E16 pattern applied to the Silver Stack attack: one flat-bet pass banks
# per-hi-lo-TC bins carrying the SIDE bet's profit moments and the MAIN game's
# profit moments separately, so any threshold/ramp card prices as arithmetic
# over the bins WITH the Ride Free toll charged at the counts where the side
# bet actually fires (the toll worsens exactly where the signal lives — a flat
# toll would flatter the verdict). Tracker convention matches run_tc_curve:
# the CompositionTracker sees every card in a settled RoundResult including
# the hole card — the perfect-information curve convention E16/E17 used; a
# live-visibility distillation is a later, separate measurement (E18 pattern).


def _bin_tc12(value: float) -> int:
    """Integer TC bins clamped to ±12 — wider than the E16 ±8 clamp because
    the Pot of Gold signal's money lives in the deep-negative tail."""
    return max(-12, min(12, int(round(value))))


@dataclass
class PogBin:
    rounds: int = 0
    pog_profit: float = 0.0
    pog_sq: float = 0.0
    main_profit: float = 0.0
    main_sq: float = 0.0
    tc_sum: float = 0.0
    tokens: int = 0  # lammer count, for the rate-vs-TC picture

    def add(self, pog: float, main: float, tc: float, tokens: int) -> None:
        self.rounds += 1
        self.pog_profit += pog
        self.pog_sq += pog * pog
        self.main_profit += main
        self.main_sq += main * main
        self.tc_sum += tc
        self.tokens += tokens

    @property
    def pog_ev(self) -> float:
        return self.pog_profit / self.rounds if self.rounds else 0.0

    @property
    def pog_stderr(self) -> float:
        if self.rounds < 2:
            return 0.0
        m = self.pog_ev
        var = max(self.pog_sq / self.rounds - m * m, 0.0)
        return math.sqrt(var / self.rounds)

    @property
    def main_ev(self) -> float:
        return self.main_profit / self.rounds if self.rounds else 0.0

    @property
    def main_stderr(self) -> float:
        if self.rounds < 2:
            return 0.0
        m = self.main_ev
        var = max(self.main_sq / self.rounds - m * m, 0.0)
        return math.sqrt(var / self.rounds)


@dataclass
class PogCurveResult:
    rules_name: str
    penetration: float
    paytable: tuple[float, ...] = ()
    rounds: int = 0
    pog_total: float = 0.0
    main_total: float = 0.0
    bins: dict[int, PogBin] = field(default_factory=dict)


def run_pog_curve(
    rules: Rules, *, seed: int, rounds: int, rules_name: str = ""
) -> PogCurveResult:
    """Flat-bet pass: main 1 unit + Pot of Gold 1 unit every round, binned by
    pre-deal hi-lo true count. `rules` must carry side_bet_pot_of_gold."""
    from ridefree.player_ev import OptimalStrategy
    from ridefree.strategy import AlwaysPotOfGold

    assert rules.side_bet_pot_of_gold, "rules must offer the Pot of Gold bet"
    strategy = AlwaysPotOfGold(OptimalStrategy())
    res = PogCurveResult(
        rules_name=rules_name, penetration=rules.penetration,
        paytable=rules.side_bet_pot_of_gold,
    )
    seeds = shoe_seeds(seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    tracker = CompositionTracker(rules.decks)
    rounds_since = 0
    for _ in range(rounds):
        if _needs_reshuffle(rules, shoe, rounds_since):
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
            tracker.new_shoe()
            rounds_since = 0
        tc = tracker.hilo_true()
        result = play_round(rules, shoe, strategy, bet=1.0)
        rounds_since += 1
        tracker.observe_round(result)
        main = result.profit - result.pog_profit
        res.rounds += 1
        res.pog_total += result.pog_profit
        res.main_total += main
        res.bins.setdefault(_bin_tc12(tc), PogBin()).add(
            result.pog_profit, main, tc, result.pog_tokens
        )
    return res


def pog_curve_to_json(res: PogCurveResult, seed: int) -> dict:
    return {
        "kind": "pog_curve",
        "rules": res.rules_name,
        "penetration": res.penetration,
        "paytable": list(res.paytable),
        "seed": seed,
        "rounds": res.rounds,
        "pog_total": res.pog_total,
        "main_total": res.main_total,
        "bins": {
            str(k): [b.rounds, b.pog_profit, b.pog_sq, b.main_profit,
                     b.main_sq, b.tc_sum, b.tokens]
            for k, b in res.bins.items()
        },
    }


def load_pog_curve_json(path: str) -> PogCurveResult:
    import json

    with open(path) as f:
        payload = json.load(f)
    if payload.get("kind") != "pog_curve":
        raise ValueError(f"{path} is not a pog_curve dump")
    res = PogCurveResult(
        rules_name=payload["rules"],
        penetration=payload["penetration"],
        paytable=tuple(payload["paytable"]),
        rounds=payload["rounds"],
        pog_total=payload["pog_total"],
        main_total=payload["main_total"],
    )
    for key, (n, pp, p2, mp, m2, tcs, tok) in payload["bins"].items():
        res.bins[int(key)] = PogBin(
            rounds=n, pog_profit=pp, pog_sq=p2, main_profit=mp, main_sq=m2,
            tc_sum=tcs, tokens=tok,
        )
    return res


def merge_pog_curves(results: list[PogCurveResult]) -> PogCurveResult:
    """Pool independently-seeded pog-curve runs (bin stats are additive)."""
    assert results
    first = results[0]
    merged = PogCurveResult(
        rules_name=first.rules_name, penetration=first.penetration,
        paytable=first.paytable,
    )
    for r in results:
        assert (r.rules_name, r.penetration, r.paytable) == (
            first.rules_name, first.penetration, first.paytable
        ), "cannot pool pog curves from different games/paytables"
        merged.rounds += r.rounds
        merged.pog_total += r.pog_total
        merged.main_total += r.main_total
        for k, b in r.bins.items():
            t = merged.bins.setdefault(k, PogBin())
            t.rounds += b.rounds
            t.pog_profit += b.pog_profit
            t.pog_sq += b.pog_sq
            t.main_profit += b.main_profit
            t.main_sq += b.main_sq
            t.tc_sum += b.tc_sum
            t.tokens += b.tokens
    return merged


def format_pog_curve(res: PogCurveResult, min_rounds: int = 1000) -> str:
    n = res.rounds
    lines = [
        f"rules: {res.rules_name}   penetration: {res.penetration:.2f}   "
        f"paytable: {'/'.join(f'{p:g}' for p in res.paytable)}",
        f"rounds: {n:,}   pog EV: {100 * res.pog_total / n:+.4f}%   "
        f"main EV: {100 * res.main_total / n:+.4f}%",
        "",
        f"  {'tc':>4s} {'rounds':>11s} {'freq':>8s} {'pog EV':>9s} {'±1se':>8s} "
        f"{'main EV':>9s} {'±1se':>8s} {'lam/round':>10s} {'mean tc':>8s}",
    ]
    for k in sorted(res.bins):
        b = res.bins[k]
        if b.rounds < min_rounds:
            continue
        lines.append(
            f"  {k:+4d} {b.rounds:>11,d} {100 * b.rounds / n:7.3f}% "
            f"{100 * b.pog_ev:+8.3f}% {100 * b.pog_stderr:7.3f}% "
            f"{100 * b.main_ev:+8.3f}% {100 * b.main_stderr:7.3f}% "
            f"{b.tokens / b.rounds:10.4f} {b.tc_sum / b.rounds:+8.2f}"
        )
    return "\n".join(lines)
