"""Small CLI so a human can watch hands and get an edge estimate.

    uv run python -m ridefree.cli demo --seed 7 --hands 5
    uv run python -m ridefree.cli sim --rounds 200000 --seed 1
    uv run python -m ridefree.cli validate --rules h17 --rounds 5000000
    uv run python -m ridefree.cli validate --rules s17 --rounds 5000000
"""

import argparse
import dataclasses

from ridefree.cards import Shoe, shoe_seeds
from ridefree.engine import play_round
from ridefree.rules import (
    PAYTABLE_21P3_9TO1,
    RIDE_FREE,
    RIDE_FREE_WOO,
    SHOE_END_MODES,
    STANDARD_6D_H17,
    STANDARD_6D_S17,
)
from ridefree.simulator import simulate
from ridefree.strategy import BasicStrategy


def _strategy_for(rules):
    if rules.free_split_ranks or rules.free_double_totals:
        from ridefree.player_ev import OptimalStrategy

        return OptimalStrategy()
    return BasicStrategy()


def _apply_shoe_overrides(rules, args):
    changes = {}
    if getattr(args, "shoe_mode", None):
        changes["shoe_end_mode"] = args.shoe_mode
    if getattr(args, "rounds_per_shoe", None):
        changes["rounds_per_shoe"] = args.rounds_per_shoe
    return dataclasses.replace(rules, **changes) if changes else rules

# variant -> (name, rules, published player EV, default report path)
# ridefree_woo matches the exact WoO ruleset behind the published 1.04% house edge;
# ridefree (Potawatomi: no resplit aces) targets 1.04% + 0.08% = 1.12% per WoO's
# rule-variation table.
VARIANTS = {
    "h17": ("STANDARD_6D_H17", STANDARD_6D_H17, -0.0062, "validation_report.html"),
    "s17": ("STANDARD_6D_S17", STANDARD_6D_S17, -0.0040, "validation_report_s17.html"),
    "ridefree": ("RIDE_FREE", RIDE_FREE, -0.0112, "validation_report_ridefree.html"),
    "ridefree_woo": ("RIDE_FREE_WOO", RIDE_FREE_WOO, -0.0104,
                     "validation_report_ridefree_woo.html"),
}


def _demo(args: argparse.Namespace) -> None:
    _, rules, _, _ = VARIANTS[args.rules]
    strategy = _strategy_for(rules)
    seeds = shoe_seeds(args.seed)
    shoe = Shoe(rules.decks, rules.penetration, next(seeds))
    for n in range(1, args.hands + 1):
        if shoe.needs_shuffle or shoe.cards_remaining < 20:
            shoe = Shoe(rules.decks, rules.penetration, next(seeds))
        result = play_round(rules, shoe, strategy, bet=1.0, log=True)
        print(f"--- hand {n} ---")
        for line in result.events:
            print(f"  {line}")
    print()


def _sim(args: argparse.Namespace) -> None:
    _, rules, _, _ = VARIANTS[args.rules]
    rules = _apply_shoe_overrides(rules, args)
    print(f"shoe mode: {rules.shoe_end_mode}"
          + (f" ({rules.rounds_per_shoe} rounds/shoe)"
             if rules.shoe_end_mode == "fixed_rounds" else ""))
    if args.insurance or args.deviations:
        from ridefree.player_ev import CompositionPlayer

        strategy = CompositionPlayer(
            rules.decks, insurance=args.insurance, deviations=args.deviations
        )
        print(f"strategy: composition player (insurance={'on' if args.insurance else 'off'}, "
              f"deviations={'on' if args.deviations else 'off'})"
              + (" — deviations rebuild the EV calculator per round, ~0.5k rounds/s"
                 if args.deviations else ""))
    else:
        strategy = _strategy_for(rules)
        print("strategy: fixed reference (chart play, no insurance) — "
              "the published-edge comparator")
    if args.sb_21p3:
        from ridefree.strategy import AlwaysSideBet

        rules = dataclasses.replace(rules, side_bet_21p3=PAYTABLE_21P3_9TO1)
        strategy = AlwaysSideBet(strategy)
        print("21+3: always-bet 1 unit, flat 9-to-1 paytable")
    m = simulate(rules, strategy, seed=args.seed, rounds=args.rounds, bet=1.0)
    edge_pct = m.edge * 100
    err_pct = m.edge_stderr * 100
    print(f"rounds:            {m.rounds:,}")
    print(f"hands:             {m.hands:,}")
    print(f"player edge:       {edge_pct:+.3f}%  (±{err_pct:.3f}% = 1 std err)")
    print(f"house edge:        {-edge_pct:.3f}%")
    print(f"player naturals:   {m.player_naturals:,} "
          f"({100 * m.player_naturals / m.rounds:.2f}% of rounds)")
    print(f"per-round std dev: {m.profit_std:.3f} units")
    if m.insured_rounds:
        print(f"insurance:         {m.insured_rounds:,} rounds "
              f"({100 * m.insured_rounds / m.rounds:.2f}%), "
              f"staked {m.insurance_stake_total:g}, "
              f"profit {m.insurance_profit_total:+.1f} "
              f"({100 * m.insurance_profit_total / m.rounds:+.4f}%/round)")
    if m.sb21p3_rounds:
        sb_edge = m.sb21p3_profit_total / m.sb21p3_stake_total
        n = m.sb21p3_rounds
        print(f"21+3 side bet:     {n:,} rounds staked, "
              f"total {m.sb21p3_stake_total:g}, profit {m.sb21p3_profit_total:+.1f}")
        print(f"21+3 edge:         {100 * sb_edge:+.4f}% per unit staked "
              f"(published 9:1 six-deck: -3.2386%)")
        for cat in ("straight_flush", "three_of_a_kind", "straight", "flush", "none"):
            if cat in m.sb21p3_categories:
                v = m.sb21p3_categories[cat]
                print(f"  {cat:16s} {v:9,} ({100 * v / n:7.4f}%)")
    if m.free_splits or m.free_doubles or m.dealer_22_pushes:
        print(f"free splits:       {m.free_splits:,} "
              f"({100 * m.free_splits / m.rounds:.2f}% of rounds)")
        print(f"free doubles:      {m.free_doubles:,} "
              f"({100 * m.free_doubles / m.rounds:.2f}% of rounds)")
        print(f"dealer 22 pushes:  {m.dealer_22_pushes:,} "
              f"({100 * m.dealer_22_pushes / m.rounds:.2f}% of rounds)")
    total = sum(m.outcomes.values())
    print("outcomes (per hand):")
    for k in ("blackjack", "win", "push", "lose"):
        v = m.outcomes.get(k, 0)
        print(f"  {k:10s} {100 * v / total:5.2f}%")
    dealer_total = sum(m.dealer_final.values())
    print(f"dealer final (completed hands only, n={dealer_total:,}):")
    for k in sorted(m.dealer_final):
        label = "bust" if k == 22 else str(k)
        print(f"  {label:5s} {100 * m.dealer_final[k] / dealer_total:5.2f}%")


def _validate(args: argparse.Namespace) -> None:
    from datetime import datetime, timezone
    from pathlib import Path

    from ridefree.validation import format_report, run_suite, to_html

    name, rules, published_edge, default_html = VARIANTS[args.rules]
    rules = _apply_shoe_overrides(rules, args)
    checks, m = run_suite(
        rules,
        seed=args.seed,
        game_rounds=args.rounds,
        dealer_trials=args.dealer_trials,
        published_edge=published_edge,
    )
    print(f"ruleset: {name}   shoe mode: {rules.shoe_end_mode}")
    print(format_report(checks, m))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = to_html(checks, m, ruleset_name=name, generated_at=stamp)
    out = Path(args.html or default_html)
    out.write_text(html)
    print(f"\nHTML report written to {out}")


def _signals(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_experiment, run_conditional_ev

    name, rules, _, _ = VARIANTS[args.rules]
    rules = _apply_shoe_overrides(rules, args)
    print(f"ruleset: {name}   shoe mode: {rules.shoe_end_mode}")
    result = run_conditional_ev(
        rules, _strategy_for(rules), seed=args.seed, rounds=args.rounds
    )
    print(format_experiment(result, min_rounds=args.min_rounds))


def _grid(args: argparse.Namespace) -> None:
    import json

    from ridefree.experiments import format_grid, run_conditional_ev_grid

    name, rules, _, _ = VARIANTS[args.rules]
    rules = _apply_shoe_overrides(rules, args)
    print(f"ruleset: {name}   shoe mode: {rules.shoe_end_mode}")
    result = run_conditional_ev_grid(
        rules,
        _strategy_for(rules),
        seed=args.seed,
        rounds=args.rounds,
        row_signal=args.row,
        col_signal=args.col,
    )
    print(format_grid(result, min_cell=args.min_cell))
    if args.json:
        payload = {
            "rules": name,
            "seed": args.seed,
            "rounds": result.rounds,
            "row": result.row_name,
            "col": result.col_name,
            "grid": {
                str(row): {
                    str(col): [s.rounds, s.profit, s.profit_sq]
                    for col, s in cols.items()
                }
                for row, cols in result.grid.items()
            },
        }
        with open(args.json, "w") as f:
            json.dump(payload, f)
        print(f"\ngrid JSON written to {args.json}")


def _sbev(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_sb_ev_scan, run_sb_ev_scan
    from ridefree.strategy import AlwaysSideBet

    name, rules, _, _ = VARIANTS[args.rules]
    changes = {"side_bet_21p3": PAYTABLE_21P3_9TO1}
    if args.penetration is not None:
        changes["penetration"] = args.penetration
    rules = dataclasses.replace(rules, **changes)
    print(f"ruleset: {name} + 21+3 flat 9:1   penetration: {rules.penetration:.2f}")
    print("scan: exact pre-deal EV from remaining (rank,suit) composition, "
          "always-bet 1 unit")
    result = run_sb_ev_scan(
        rules, AlwaysSideBet(_strategy_for(rules)), seed=args.seed,
        rounds=args.rounds,
    )
    print(format_sb_ev_scan(result, min_cell=args.min_cell))


def _sbdecomp(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_sb_decomposition, run_sb_decomposition

    name, rules, _, _ = VARIANTS[args.rules]
    if args.penetration is not None:
        rules = dataclasses.replace(rules, penetration=args.penetration)
    print(f"ruleset: {name}   penetration: {rules.penetration:.2f}")
    print("E11a decomposition: exact 21+3 EV = depth + suit + rank + interaction")
    result = run_sb_decomposition(
        rules, _strategy_for(rules), seed=args.seed, rounds=args.rounds,
        paytable=PAYTABLE_21P3_9TO1, threshold=args.threshold,
    )
    print(format_sb_decomposition(result))


def _sbtrack(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_sb_trackers, run_sb_trackers

    name, rules, _, _ = VARIANTS[args.rules]
    if args.penetration is not None:
        rules = dataclasses.replace(rules, penetration=args.penetration)
    print(f"ruleset: {name}   penetration: {rules.penetration:.2f}")
    print("E11b: human tracker rules vs the exact 21+3 ceiling")
    result = run_sb_trackers(
        rules, _strategy_for(rules), seed=args.seed, rounds=args.rounds,
        paytable=PAYTABLE_21P3_9TO1,
    )
    print(format_sb_trackers(result))


def _combine(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_grid, load_grid_json, merge_grids

    grids = [load_grid_json(p) for p in args.paths]
    merged = merge_grids(grids)
    print(f"merged {len(grids)} grid(s)")
    print(format_grid(merged, min_cell=args.min_cell))


def _deviations(args: argparse.Namespace) -> None:
    from ridefree.experiments import run_deviation_value

    name, rules, _, _ = VARIANTS[args.rules]
    print(f"ruleset: {name}   window threshold: rf_ev >= {args.window_threshold:g}"
          + ("   (window-only mode)" if args.window_only else ""))
    r = run_deviation_value(
        rules, seed=args.seed, rounds=args.rounds,
        window_threshold=args.window_threshold, window_only=args.window_only,
    )
    print(f"rounds:                {r.rounds:,} (paired)")
    print(f"base EV:               {100 * r.base_profit / r.rounds:+.3f}%")
    if not args.window_only:
        print(f"deviation value:       {100 * r.deviation_value:+.4f}% ± "
              f"{100 * r.deviation_se:.4f}% per round")
        print(f"action-changed rounds: {100 * r.actions_changed / r.rounds:.2f}%   "
              f"profit-changed: {100 * r.rounds_changed / r.rounds:.2f}%")
    print(f"wong-in window value:  {100 * r.window_value:+.4f}% ± "
          f"{100 * r.window_se:.4f}% per round "
          f"({r.window_rounds:,} rounds in window)")


def main() -> None:
    parser = argparse.ArgumentParser(prog="ridefree")
    sub = parser.add_subparsers(required=True)

    d = sub.add_parser("demo", help="narrate a few hands")
    d.add_argument("--rules", choices=VARIANTS, default="h17")
    d.add_argument("--seed", type=int, default=1)
    d.add_argument("--hands", type=int, default=5)
    d.set_defaults(func=_demo)

    s = sub.add_parser("sim", help="simulate many hands and report metrics")
    s.add_argument("--rules", choices=VARIANTS, default="h17")
    s.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None,
                   help="override shoe-end mode (default: ruleset's cut_card)")
    s.add_argument("--rounds-per-shoe", type=int, default=None,
                   help="rounds per shoe for fixed_rounds mode")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--rounds", type=int, default=100_000)
    s.add_argument("--insurance", action=argparse.BooleanOptionalAction, default=True,
                   help="take insurance when the tracked composition makes it +EV "
                        "(default on; --no-insurance for the published-edge comparator)")
    s.add_argument("--21p3", dest="sb_21p3", action="store_true",
                   help="stake the 21+3 side bet (flat 9-to-1 paytable) every round")
    s.add_argument("--deviations", action=argparse.BooleanOptionalAction, default=True,
                   help="composition-based playing deviations (default on; slower "
                        "~0.5k rounds/s; --no-deviations for fixed chart play)")
    s.set_defaults(func=_sim)

    v = sub.add_parser("validate", help="run the validation battery vs references")
    v.add_argument("--rules", choices=VARIANTS, default="h17",
                   help="ruleset/variant to validate (default: h17)")
    v.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None,
                   help="override shoe-end mode (csm ≈ published off-the-top figure)")
    v.add_argument("--rounds-per-shoe", type=int, default=None,
                   help="rounds per shoe for fixed_rounds mode")
    v.add_argument("--seed", type=int, default=1)
    v.add_argument("--rounds", type=int, default=2_000_000)
    v.add_argument("--dealer-trials", type=int, default=2_000_000)
    v.add_argument("--html", default=None,
                   help="path for the HTML report (default: per-variant filename)")
    v.set_defaults(func=_validate)

    g = sub.add_parser(
        "signals", help="EV-vs-signal curves (pair P, free-double P, hi-lo TC)"
    )
    g.add_argument("--rules", choices=VARIANTS, default="ridefree")
    g.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None)
    g.add_argument("--rounds-per-shoe", type=int, default=None)
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--rounds", type=int, default=1_000_000)
    g.add_argument("--min-rounds", type=int, default=2_000,
                   help="hide bins with fewer rounds than this")
    g.set_defaults(func=_signals)

    t = sub.add_parser(
        "grid", help="2D conditional EV: rows x cols with within-row slopes"
    )
    t.add_argument("--rules", choices=VARIANTS, default="ridefree")
    from ridefree.experiments import SIGNALS

    t.add_argument("--row", choices=tuple(SIGNALS), default="hilo_tc")
    t.add_argument("--col", choices=tuple(SIGNALS), default="p_pair")
    t.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None)
    t.add_argument("--rounds-per-shoe", type=int, default=None)
    t.add_argument("--seed", type=int, default=1)
    t.add_argument("--rounds", type=int, default=4_000_000)
    t.add_argument("--min-cell", type=int, default=2_000)
    t.add_argument("--json", default=None, help="dump raw grid stats to this path")
    t.set_defaults(func=_grid)

    sb = sub.add_parser(
        "sbev", help="21+3 exact pre-deal EV scan (perfect-information ceiling)"
    )
    sb.add_argument("--rules", choices=VARIANTS, default="h17",
                    help="base blackjack rules (the side bet is added on top)")
    sb.add_argument("--seed", type=int, default=1)
    sb.add_argument("--rounds", type=int, default=2_000_000)
    sb.add_argument("--penetration", type=float, default=None,
                    help="override cut-card depth (default: ruleset's 0.75)")
    sb.add_argument("--min-cell", type=int, default=2_000)
    sb.set_defaults(func=_sbev)

    sd = sub.add_parser(
        "sbdecomp", help="21+3 EV decomposition: depth + suit + rank + interaction"
    )
    sd.add_argument("--rules", choices=VARIANTS, default="h17")
    sd.add_argument("--seed", type=int, default=1)
    sd.add_argument("--rounds", type=int, default=2_000_000)
    sd.add_argument("--penetration", type=float, default=None)
    sd.add_argument("--threshold", type=float, default=0.0,
                    help="wong-in threshold the selection rules are scored at")
    sd.set_defaults(func=_sbdecomp)

    st = sub.add_parser(
        "sbtrack", help="21+3 human tracker rules scored vs the exact ceiling"
    )
    st.add_argument("--rules", choices=VARIANTS, default="h17")
    st.add_argument("--seed", type=int, default=1)
    st.add_argument("--rounds", type=int, default=2_000_000)
    st.add_argument("--penetration", type=float, default=None)
    st.set_defaults(func=_sbtrack)

    c = sub.add_parser("combine", help="pool grid JSON dumps and report")
    c.add_argument("paths", nargs="+", help="grid JSON files to merge")
    c.add_argument("--min-cell", type=int, default=2_000)
    c.set_defaults(func=_combine)

    dv = sub.add_parser(
        "deviations", help="paired differential value of composition-conditioned play"
    )
    dv.add_argument("--rules", choices=VARIANTS, default="ridefree")
    dv.add_argument("--seed", type=int, default=1)
    dv.add_argument("--rounds", type=int, default=150_000)
    dv.add_argument("--window-threshold", type=float, default=0.0075,
                    help="rf_ev wong-in threshold for the window stats "
                         "(E4c/E8 operating point is 0.0125)")
    dv.add_argument("--window-only", action="store_true",
                    help="paired replay only inside the window (~7x more window "
                         "rounds per second; overall stats then cover the window only)")
    dv.set_defaults(func=_deviations)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
