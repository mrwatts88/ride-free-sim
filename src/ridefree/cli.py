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
    PAYTABLE_POG_1,
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
    if args.split_fives:
        from ridefree.strategy import SplitFives

        strategy = SplitFives(strategy)
        print("split fives: free-splitting 5s whenever funded (Pot of Gold farm)")
    if args.pog:
        from ridefree.strategy import AlwaysPotOfGold

        rules = dataclasses.replace(rules, side_bet_pot_of_gold=PAYTABLE_POG_1)
        strategy = AlwaysPotOfGold(strategy)
        print("pot of gold: always-bet 1 unit, pay table 1 (3/10/30/60/100/300/1000)")
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
    if m.pog_rounds:
        pog_edge = m.pog_profit_total / m.pog_stake_total
        n = m.pog_rounds
        print(f"pot of gold:       {n:,} rounds staked, "
              f"total {m.pog_stake_total:g}, profit {m.pog_profit_total:+.1f}")
        print(f"pot of gold edge:  {100 * pog_edge:+.4f}% per unit staked "
              f"(WoO sim convention -5.7687%; NV-rules arithmetic ~-7.7%, "
              f"see E19)")
        for k in sorted(m.pog_tokens):
            v = m.pog_tokens[k]
            print(f"  {k} lammer(s)     {v:9,} ({100 * v / n:8.4f}%)")
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
    if args.penetration is not None:
        rules = dataclasses.replace(rules, penetration=args.penetration)
    print(f"ruleset: {name}   pen: {rules.penetration:.2f}   "
          f"window threshold: rf_ev >= {args.window_threshold:g}"
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
    if r.by_tc:
        print("\ndeviation value by hi-lo TC (paired diff per replayed round):")
        print(f"  {'tc':>4s} {'rounds':>10s} {'value':>9s} {'±1se':>8s}")
        for k in sorted(r.by_tc):
            s = r.by_tc[k]
            if s.rounds < 1000:
                continue
            print(f"  {k:+4d} {s.rounds:>10,d} {100 * s.ev:+8.4f}% "
                  f"{100 * s.stderr:7.4f}%")
    if args.json:
        import json

        payload = {
            "kind": "dev_tc",
            "rules": name,
            "penetration": rules.penetration,
            "seed": args.seed,
            "rounds": r.rounds,
            "diff_sum": r.diff_sum,
            "diff_sq": r.diff_sq,
            "by_tc": {
                str(k): [s.rounds, s.profit, s.profit_sq]
                for k, s in r.by_tc.items()
            },
        }
        with open(args.json, "w") as f:
            json.dump(payload, f)
        print(f"\ndeviation JSON written to {args.json}")


def _curve(args: argparse.Namespace) -> None:
    import json

    from ridefree.experiments import format_tc_curve, run_tc_curve, tc_curve_to_json

    name, rules, _, _ = VARIANTS[args.rules]
    rules = _apply_shoe_overrides(rules, args)
    if args.penetration is not None:
        rules = dataclasses.replace(rules, penetration=args.penetration)
    res = run_tc_curve(
        rules, args.arm, seed=args.seed, rounds=args.rounds, rules_name=name
    )
    print(format_tc_curve(res, min_rounds=args.min_rounds))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(tc_curve_to_json(res, args.seed), f)
        print(f"\ncurve JSON written to {args.json}")


def _curvecombine(args: argparse.Namespace) -> None:
    from ridefree.experiments import (
        format_tc_curve,
        load_tc_curve_json,
        merge_tc_curves,
    )

    curves = [load_tc_curve_json(p) for p in args.paths]
    merged = merge_tc_curves(curves)
    print(f"merged {len(curves)} curve(s)")
    print(format_tc_curve(merged, min_rounds=args.min_rounds))


def _countcurve(args: argparse.Namespace) -> None:
    import json

    from ridefree.counting import STANDARD_H17_EOR
    from ridefree.experiments import (
        count_curves_to_json,
        format_count_curves,
        run_count_curves,
        search_unbalanced_level1,
    )

    name, rules, _, _ = VARIANTS[args.rules]
    rules = _apply_shoe_overrides(rules, args)
    if args.penetration is not None:
        rules = dataclasses.replace(rules, penetration=args.penetration)
    custom = None
    if args.custom:
        best = search_unbalanced_level1(STANDARD_H17_EOR, top=3)
        print("analytic search — best level-1 unbalanced counts "
              "(imbalance +2/deck, pivot ~TC+2), by betting correlation:")
        for bc, base, bump in best:
            tags = dict(base)
            print(f"  BC {bc:.4f}   tags {tags}   half-bump on rank {bump} "
                  f"(two red suits +1)")
        bc, base, bump = best[0]
        custom = (dict(base), bump)
        print(f"banking the winner as custom_rc (BC {bc:.4f})\n")
    res = run_count_curves(
        rules, args.arm, seed=args.seed, rounds=args.rounds, rules_name=name,
        custom=custom,
    )
    print(format_count_curves(res, min_rounds=args.min_rounds))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(count_curves_to_json(res, args.seed, custom), f)
        print(f"\ncount-curves JSON written to {args.json}")


def _countcombine(args: argparse.Namespace) -> None:
    from ridefree.experiments import (
        format_count_curves,
        load_count_curves_json,
        merge_count_curves,
    )

    curves = [load_count_curves_json(p) for p in args.paths]
    merged = merge_count_curves(curves)
    print(f"merged {len(curves)} count-curve dump(s)")
    print(format_count_curves(merged, min_rounds=args.min_rounds))


def _ramp(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_ramp, parse_ramp, run_ramp

    name, rules, _, _ = VARIANTS[args.rules]
    rules = _apply_shoe_overrides(rules, args)
    if args.penetration is not None:
        rules = dataclasses.replace(rules, penetration=args.penetration)
    res = run_ramp(
        rules, args.arm, parse_ramp(args.ramp),
        seed=args.seed, rounds=args.rounds, rules_name=name,
    )
    print(format_ramp(res))


def _pogcurve(args: argparse.Namespace) -> None:
    import json

    from ridefree.experiments import format_pog_curve, pog_curve_to_json, run_pog_curve
    from ridefree.rules import PAYTABLE_POG_04, PAYTABLE_POG_2

    paytables = {"1": PAYTABLE_POG_1, "2": PAYTABLE_POG_2, "04": PAYTABLE_POG_04}
    name, rules, _, _ = VARIANTS[args.rules]
    changes = {"side_bet_pot_of_gold": paytables[args.paytable]}
    if args.penetration is not None:
        changes["penetration"] = args.penetration
    rules = dataclasses.replace(rules, **changes)
    arm = "farm (SplitFives)" if args.split_fives else "normal"
    print(f"ruleset: {name}   pen: {rules.penetration:.2f}   "
          f"pot of gold pay table {args.paytable}, always-bet 1 unit   arm: {arm}")
    res = run_pog_curve(rules, seed=args.seed, rounds=args.rounds, rules_name=name,
                        farm=args.split_fives)
    print(format_pog_curve(res, min_rounds=args.min_rounds))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(pog_curve_to_json(res, args.seed), f)
        print(f"\npog-curve JSON written to {args.json}")


def _pogcombine(args: argparse.Namespace) -> None:
    from ridefree.experiments import (
        format_pog_curve,
        load_pog_curve_json,
        merge_pog_curves,
    )

    curves = [load_pog_curve_json(p) for p in args.paths]
    merged = merge_pog_curves(curves)
    print(f"merged {len(curves)} pog curve(s)")
    print(format_pog_curve(merged, min_rounds=args.min_rounds))


def _bac_rules(args: argparse.Namespace):
    import dataclasses as _dc

    from ridefree.baccarat import BACCARAT_8D, EZ_BACCARAT_8D

    rules = EZ_BACCARAT_8D if args.rules == "ez" else BACCARAT_8D
    changes = {}
    if args.decks:
        changes["decks"] = args.decks
    if args.penetration:
        changes["penetration"] = args.penetration
    if getattr(args, "shoe_mode", None):
        changes["shoe_end_mode"] = args.shoe_mode
    if getattr(args, "rounds_per_shoe", None):
        changes["rounds_per_shoe"] = args.rounds_per_shoe
    return _dc.replace(rules, **changes) if changes else rules


def _bacexact(args: argparse.Namespace) -> None:
    from ridefree.baccarat import exact_outcomes, fresh_composition

    rules = _bac_rules(args)
    out = exact_outcomes(fresh_composition(rules.decks))
    print(f"exact enumeration, {rules.decks} decks "
          f"({'EZ' if rules.banker_push_on_three_card_7 else 'classic'} settlement)")
    print(f"total 6-card sequences: {out.total:,}")
    for name, combos, p in [
        ("banker", out.banker, out.p_banker),
        ("player", out.player, out.p_player),
        ("tie", out.tie, out.p_tie),
        ("dragon 7", out.dragon7, out.p_dragon7),
        ("panda 8", out.panda8, out.p_panda8),
    ]:
        print(f"  {name:<9} {combos:>26,}   p = {p:.6f}")
    print(f"EV banker: {100 * out.ev_main(rules, 'banker'):+.4f}%   "
          f"player: {100 * out.ev_main(rules, 'player'):+.4f}%   "
          f"tie ({rules.tie_pays:g}:1): {100 * out.ev_main(rules, 'tie'):+.4f}%")
    print(f"EV dragon 7 ({rules.dragon7_pays:g}:1): {100 * out.ev_dragon7(rules):+.4f}%   "
          f"panda 8 ({rules.panda8_pays:g}:1): {100 * out.ev_panda8(rules):+.4f}%")


def _bac(args: argparse.Namespace) -> None:
    import math

    from ridefree.baccarat import (
        FlatBettor,
        exact_outcomes,
        fresh_composition,
        simulate_baccarat,
    )

    rules = _bac_rules(args)
    main_bet = None if args.main == "none" else (args.main, 1.0)
    bettor = FlatBettor(main=main_bet, dragon7=args.dragon7, panda8=args.panda8)
    print(f"baccarat {'EZ' if rules.banker_push_on_three_card_7 else 'classic'}, "
          f"{rules.decks} decks, shoe mode: {rules.shoe_end_mode}"
          + (f" (pen {rules.penetration:g})" if rules.shoe_end_mode == "cut_card" else "")
          + f", main: {args.main}, dragon7 stake: {args.dragon7:g}, "
          f"panda8 stake: {args.panda8:g}")
    m = simulate_baccarat(rules, bettor, seed=args.seed, rounds=args.rounds)
    out = exact_outcomes(fresh_composition(rules.decks))
    n = m.rounds
    print(f"rounds: {n:,}")

    def _freq(label: str, observed: int, p: float) -> None:
        sigma = math.sqrt(p * (1.0 - p) * n)
        z = (observed - p * n) / sigma if sigma else 0.0
        print(f"  {label:<22} {observed / n:>9.6f}  exact {p:.6f}  ({z:+.2f}σ)")

    print("frequencies vs exact (fresh-shoe; cut_card mode carries the "
          "round-frequency analogue of the cut-card effect):")
    _freq("banker", m.outcomes.get("banker", 0), out.p_banker)
    _freq("player", m.outcomes.get("player", 0), out.p_player)
    _freq("tie", m.outcomes.get("tie", 0), out.p_tie)
    _freq("banker 3-card 7", m.banker_three_card_7s, out.p_dragon7)
    _freq("player 3-card 8", m.player_three_card_8s, out.p_panda8)

    def _edge(label: str, profit: float, staked: float, exact_ev: float,
              exact_var: float) -> None:
        if not staked:
            return
        edge = profit / staked
        sigma = math.sqrt(exact_var / n)
        z = (edge - exact_ev) / sigma if sigma else 0.0
        print(f"  {label:<22} {100 * edge:>+8.4f}%  exact {100 * exact_ev:+.4f}%  "
              f"(±{100 * sigma:.4f}%, {z:+.2f}σ)")

    print("edges per unit staked vs exact:")
    if main_bet is not None:
        ev = out.ev_main(rules, args.main)
        if args.main == "tie":
            e2 = (rules.tie_pays ** 2) * out.p_tie + (1.0 - out.p_tie)
        elif args.main == "banker":
            win = (out.p_banker - out.p_dragon7
                   if rules.banker_push_on_three_card_7 else out.p_banker)
            e2 = win * (1.0 - rules.banker_commission) ** 2 + out.p_player
        else:
            e2 = out.p_player + out.p_banker
        _edge(f"main ({args.main})", m.main_profit_total, m.main_wager_total,
              ev, e2 - ev * ev)
    if args.dragon7:
        ev = out.ev_dragon7(rules)
        e2 = (rules.dragon7_pays ** 2) * out.p_dragon7 + (1.0 - out.p_dragon7)
        _edge("dragon 7", m.dragon7_profit_total, m.dragon7_stake_total,
              ev, e2 - ev * ev)
    if args.panda8:
        ev = out.ev_panda8(rules)
        e2 = (rules.panda8_pays ** 2) * out.p_panda8 + (1.0 - out.p_panda8)
        _edge("panda 8", m.panda8_profit_total, m.panda8_stake_total,
              ev, e2 - ev * ev)
    print(f"per-round profit std: {m.profit_std:.3f} units")


def _bacev(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_bac_ev_scan, run_bac_ev_scan

    rules = _bac_rules(args)
    print(f"baccarat exact pre-deal EV scan "
          f"({'EZ' if rules.banker_push_on_three_card_7 else 'classic'}, "
          f"{rules.decks} decks, pen {rules.penetration:g}, "
          f"D7 {rules.dragon7_pays:g}:1 / P8 {rules.panda8_pays:g}:1, "
          f"both staked every round)")
    res = run_bac_ev_scan(rules, seed=args.seed, rounds=args.rounds)
    print(format_bac_ev_scan(res, min_cell=args.min_cell))


def _bactrack(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_bac_track, run_bac_track

    rules = _bac_rules(args)
    print(f"baccarat tracker scoring "
          f"({'EZ' if rules.banker_push_on_three_card_7 else 'classic'}, "
          f"{rules.decks} decks, pen {rules.penetration:g}; analytic/published "
          f"parameters only, scored in exact EV)")
    res = run_bac_track(rules, seed=args.seed, rounds=args.rounds)
    print(format_bac_track(res))


def _bacorder(args: argparse.Namespace) -> None:
    from ridefree.experiments import format_bac_order, run_bac_order_scan

    rules = _bac_rules(args)
    print(f"baccarat Taylor-order bounds ({rules.decks} decks, "
          f"pen {rules.penetration:g}) — what any linear/quadratic model can reach")
    res = run_bac_order_scan(rules, seed=args.seed, rounds=args.rounds)
    print(format_bac_order(res))


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
    s.add_argument("--pog", action="store_true",
                   help="stake the Pot of Gold side bet (pay table 1) every round")
    s.add_argument("--split-fives", dest="split_fives", action="store_true",
                   help="free-split 5s instead of doubling (the Pot of Gold farm "
                        "line; costs the main bet ~0.15%%)")
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
    dv.add_argument("--penetration", type=float, default=None,
                    help="override cut-card depth (default: ruleset's 0.75)")
    dv.add_argument("--json", default=None,
                    help="dump per-TC paired diffs to this path (E16 shards)")
    dv.set_defaults(func=_deviations)

    cv = sub.add_parser(
        "curve", help="per-hi-lo-TC EV/variance curve with insurance attribution "
                      "(E16: the cover ledger's input)"
    )
    cv.add_argument("--rules", choices=VARIANTS, default="h17")
    cv.add_argument("--arm", choices=("basic", "ins", "full"), default="basic",
                    help="basic = chart play, no insurance; ins = +composition "
                         "insurance; full = +composition deviations (~0.5k r/s)")
    cv.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None)
    cv.add_argument("--rounds-per-shoe", type=int, default=None)
    cv.add_argument("--penetration", type=float, default=None,
                    help="override cut-card depth (default: ruleset's 0.75)")
    cv.add_argument("--seed", type=int, default=1)
    cv.add_argument("--rounds", type=int, default=1_000_000)
    cv.add_argument("--min-rounds", type=int, default=1_000)
    cv.add_argument("--json", default=None, help="dump curve bins to this path")
    cv.set_defaults(func=_curve)

    cc = sub.add_parser("curvecombine", help="pool curve JSON dumps and report")
    cc.add_argument("paths", nargs="+", help="curve JSON files to merge")
    cc.add_argument("--min-rounds", type=int, default=1_000)
    cc.set_defaults(func=_curvecombine)

    kc = sub.add_parser(
        "countcurve", help="EV bins for unbalanced RUNNING counts (red7/KO/"
                           "half-7/custom) in one pass (E17)"
    )
    kc.add_argument("--rules", choices=VARIANTS, default="h17")
    kc.add_argument("--arm", choices=("basic", "ins", "full"), default="ins")
    kc.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None)
    kc.add_argument("--rounds-per-shoe", type=int, default=None)
    kc.add_argument("--penetration", type=float, default=None)
    kc.add_argument("--seed", type=int, default=1)
    kc.add_argument("--rounds", type=int, default=1_000_000)
    kc.add_argument("--min-rounds", type=int, default=5_000)
    kc.add_argument("--custom", action="store_true",
                    help="run the analytic unbalanced-count search and bank "
                         "the best candidate as custom_rc")
    kc.add_argument("--json", default=None)
    kc.set_defaults(func=_countcurve)

    kcc = sub.add_parser("countcombine", help="pool count-curve JSON dumps")
    kcc.add_argument("paths", nargs="+")
    kcc.add_argument("--min-rounds", type=int, default=5_000)
    kcc.set_defaults(func=_countcombine)

    rp = sub.add_parser(
        "ramp", help="simulate a bet ramp live: bet(tc) each round, real spread "
                     "(E16 verification arm)"
    )
    rp.add_argument("--rules", choices=VARIANTS, default="h17")
    rp.add_argument("--arm", choices=("basic", "ins", "full"), default="ins")
    rp.add_argument("--ramp", required=True,
                    help="'min_tc:units,...' step function; bet 0 below the "
                         "lowest step. Flat = '-99:1'; e.g. '-99:1,1:2,2:4,3:8'")
    rp.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None)
    rp.add_argument("--rounds-per-shoe", type=int, default=None)
    rp.add_argument("--penetration", type=float, default=None)
    rp.add_argument("--seed", type=int, default=1)
    rp.add_argument("--rounds", type=int, default=1_000_000)
    rp.set_defaults(func=_ramp)

    pg = sub.add_parser(
        "pogcurve", help="Pot of Gold EV by hi-lo TC, side and main binned "
                         "separately (M10b: the Silver Stack attack input)"
    )
    pg.add_argument("--rules", choices=VARIANTS, default="ridefree",
                    help="base game (default: the Potawatomi RIDE_FREE config)")
    pg.add_argument("--paytable", choices=("1", "2", "04"), default="1",
                    help="Pot of Gold paytable (Potawatomi felt-confirmed: 1)")
    pg.add_argument("--penetration", type=float, default=None)
    pg.add_argument("--split-fives", dest="split_fives", action="store_true",
                    help="farm arm: free-split 5s (lammer farming) instead of "
                         "the main-EV free double — run on the SAME seed as a "
                         "normal shard for a paired delta")
    pg.add_argument("--seed", type=int, default=1)
    pg.add_argument("--rounds", type=int, default=1_000_000)
    pg.add_argument("--min-rounds", type=int, default=1_000)
    pg.add_argument("--json", default=None, help="dump curve bins to this path")
    pg.set_defaults(func=_pogcurve)

    pgc = sub.add_parser("pogcombine", help="pool pog-curve JSON dumps")
    pgc.add_argument("paths", nargs="+")
    pgc.add_argument("--min-rounds", type=int, default=1_000)
    pgc.set_defaults(func=_pogcombine)

    bx = sub.add_parser("bacexact", help="exact baccarat outcome table (enumeration)")
    bx.add_argument("--rules", choices=("ez", "classic"), default="ez")
    bx.add_argument("--decks", type=int, default=None)
    bx.add_argument("--penetration", type=float, default=None)
    bx.set_defaults(func=_bacexact, shoe_mode=None, rounds_per_shoe=None)

    b = sub.add_parser("bac", help="simulate baccarat and check against the exact "
                                   "enumeration (M9a gate: csm mode)")
    b.add_argument("--rules", choices=("ez", "classic"), default="ez")
    b.add_argument("--decks", type=int, default=None)
    b.add_argument("--penetration", type=float, default=None)
    b.add_argument("--shoe-mode", choices=SHOE_END_MODES, default=None)
    b.add_argument("--rounds-per-shoe", type=int, default=None)
    b.add_argument("--seed", type=int, default=1)
    b.add_argument("--rounds", type=int, default=200_000)
    b.add_argument("--main", choices=("banker", "player", "tie", "none"),
                   default="banker")
    b.add_argument("--dragon7", type=float, default=0.0,
                   help="dragon 7 stake per round (0 = not played)")
    b.add_argument("--panda8", type=float, default=0.0,
                   help="panda 8 stake per round (0 = not played)")
    b.set_defaults(func=_bac)

    be = sub.add_parser("bacev", help="exact Dragon 7 / Panda 8 pre-deal EV scan "
                                      "(M9b: ceiling, calibration, WoO comparator)")
    be.add_argument("--rules", choices=("ez", "classic"), default="ez")
    be.add_argument("--decks", type=int, default=None)
    be.add_argument("--penetration", type=float, default=None)
    be.add_argument("--seed", type=int, default=1)
    be.add_argument("--rounds", type=int, default=100_000)
    be.add_argument("--min-cell", type=int, default=2_000)
    be.set_defaults(func=_bacev, shoe_mode=None, rounds_per_shoe=None)

    bt = sub.add_parser("bactrack", help="score human D7/P8 count systems vs the "
                                         "exact ceiling (M9c)")
    bt.add_argument("--rules", choices=("ez", "classic"), default="ez")
    bt.add_argument("--decks", type=int, default=None)
    bt.add_argument("--penetration", type=float, default=None)
    bt.add_argument("--seed", type=int, default=1)
    bt.add_argument("--rounds", type=int, default=100_000)
    bt.set_defaults(func=_bactrack, shoe_mode=None, rounds_per_shoe=None)

    bo = sub.add_parser("bacorder", help="Taylor-order capture bounds: what any "
                                         "linear or quadratic model can reach (E15)")
    bo.add_argument("--rules", choices=("ez", "classic"), default="ez")
    bo.add_argument("--decks", type=int, default=None)
    bo.add_argument("--penetration", type=float, default=None)
    bo.add_argument("--seed", type=int, default=1)
    bo.add_argument("--rounds", type=int, default=100_000)
    bo.set_defaults(func=_bacorder, shoe_mode=None, rounds_per_shoe=None)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
