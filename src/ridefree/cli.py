"""Small CLI so a human can watch hands and get an edge estimate.

    uv run python -m ridefree.cli demo --seed 7 --hands 5
    uv run python -m ridefree.cli sim --rounds 200000 --seed 1
"""

import argparse

from ridefree.cards import Shoe
from ridefree.engine import play_round
from ridefree.rules import STANDARD_6D_H17
from ridefree.simulator import simulate
from ridefree.strategy import BasicStrategyH17


def _demo(args: argparse.Namespace) -> None:
    rules = STANDARD_6D_H17
    strategy = BasicStrategyH17()
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
    rules = STANDARD_6D_H17
    m = simulate(
        rules, BasicStrategyH17(), seed=args.seed, rounds=args.rounds, bet=1.0
    )
    edge_pct = m.edge * 100
    err_pct = m.edge_stderr * 100
    print(f"rounds:            {m.rounds:,}")
    print(f"hands:             {m.hands:,}")
    print(f"player edge:       {edge_pct:+.3f}%  (±{err_pct:.3f}% = 1 std err)")
    print(f"house edge:        {-edge_pct:.3f}%")
    print(f"player blackjacks: {m.player_blackjacks:,} "
          f"({100 * m.player_blackjacks / m.hands:.2f}% of hands)")
    print(f"per-round std dev: {m.profit_std:.3f} units")
    total = sum(m.outcomes.values())
    print("outcomes:")
    for k in ("blackjack", "win", "push", "lose"):
        v = m.outcomes.get(k, 0)
        print(f"  {k:10s} {100 * v / total:5.2f}%")
    dealer_total = sum(m.dealer_final.values())
    print("dealer final:")
    for k in sorted(m.dealer_final):
        label = "bust" if k == 22 else str(k)
        print(f"  {label:5s} {100 * m.dealer_final[k] / dealer_total:5.2f}%")


def main() -> None:
    parser = argparse.ArgumentParser(prog="ridefree")
    sub = parser.add_subparsers(required=True)

    d = sub.add_parser("demo", help="narrate a few hands")
    d.add_argument("--seed", type=int, default=1)
    d.add_argument("--hands", type=int, default=5)
    d.set_defaults(func=_demo)

    s = sub.add_parser("sim", help="simulate many hands and report metrics")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--rounds", type=int, default=100_000)
    s.set_defaults(func=_sim)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
