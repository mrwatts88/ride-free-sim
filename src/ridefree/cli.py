"""Small CLI so a human can watch hands and get an edge estimate.

    uv run python -m ridefree.cli demo --seed 7 --hands 5
    uv run python -m ridefree.cli sim --rounds 200000 --seed 1
    uv run python -m ridefree.cli validate --rules h17 --rounds 5000000
    uv run python -m ridefree.cli validate --rules s17 --rounds 5000000
"""

import argparse
import dataclasses

from ridefree.cards import Shoe
from ridefree.engine import play_round
from ridefree.rules import (
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
    shoe = Shoe(rules.decks, rules.penetration, args.seed)
    for n in range(1, args.hands + 1):
        if shoe.needs_shuffle or shoe.cards_remaining < 20:
            shoe = Shoe(rules.decks, rules.penetration, args.seed + n)
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
    m = simulate(rules, _strategy_for(rules), seed=args.seed, rounds=args.rounds, bet=1.0)
    edge_pct = m.edge * 100
    err_pct = m.edge_stderr * 100
    print(f"rounds:            {m.rounds:,}")
    print(f"hands:             {m.hands:,}")
    print(f"player edge:       {edge_pct:+.3f}%  (±{err_pct:.3f}% = 1 std err)")
    print(f"house edge:        {-edge_pct:.3f}%")
    print(f"player naturals:   {m.player_naturals:,} "
          f"({100 * m.player_naturals / m.rounds:.2f}% of rounds)")
    print(f"per-round std dev: {m.profit_std:.3f} units")
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
    t.add_argument("--row", choices=("hilo_tc", "p_pair", "p_free_double"),
                   default="hilo_tc")
    t.add_argument("--col", choices=("hilo_tc", "p_pair", "p_free_double"),
                   default="p_pair")
    t.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None)
    t.add_argument("--rounds-per-shoe", type=int, default=None)
    t.add_argument("--seed", type=int, default=1)
    t.add_argument("--rounds", type=int, default=4_000_000)
    t.add_argument("--min-cell", type=int, default=2_000)
    t.add_argument("--json", default=None, help="dump raw grid stats to this path")
    t.set_defaults(func=_grid)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
