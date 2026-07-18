"""E16 harness gates: the TC curve is an exact partition of the simulation,
the ramp simulator's bet-scaling is exact (flat ramp == plain simulator), and
the paired deviation harness's per-TC bins partition its overall diff.

Seeds here are test-local, not from the experiment seed blocks.
"""

import math

from ridefree.experiments import (
    merge_tc_curves,
    parse_ramp,
    ramp_bet,
    run_deviation_value,
    run_ramp,
    run_tc_curve,
    tc_curve_to_json,
    load_tc_curve_json,
)
from ridefree.player_ev import OptimalStrategy
from ridefree.rules import STANDARD_6D_H17
from ridefree.simulator import simulate

SEED = 987_654_321


def test_curve_bins_partition_rounds():
    res = run_tc_curve(
        STANDARD_6D_H17, "basic", seed=SEED, rounds=20_000, rules_name="h17"
    )
    assert res.rounds == 20_000
    assert sum(b.rounds for b in res.bins.values()) == res.rounds
    assert math.isclose(
        sum(b.profit for b in res.bins.values()), res.total_profit, abs_tol=1e-9
    )
    # the basic arm never insures
    assert all(b.ins_rounds == 0 for b in res.bins.values())
    assert all(b.ins_profit == 0.0 for b in res.bins.values())


def test_curve_deterministic_merge_and_json_roundtrip(tmp_path):
    a = run_tc_curve(
        STANDARD_6D_H17, "basic", seed=SEED, rounds=10_000, rules_name="h17"
    )
    b = run_tc_curve(
        STANDARD_6D_H17, "basic", seed=SEED, rounds=10_000, rules_name="h17"
    )
    assert a.total_profit == b.total_profit
    assert sorted(a.bins) == sorted(b.bins)
    for k in a.bins:
        assert a.bins[k].profit == b.bins[k].profit
        assert a.bins[k].tc_sum == b.bins[k].tc_sum

    merged = merge_tc_curves([a, b])
    assert merged.rounds == 20_000
    assert math.isclose(merged.total_profit, 2 * a.total_profit, abs_tol=1e-9)

    path = tmp_path / "curve.json"
    import json

    path.write_text(json.dumps(tc_curve_to_json(a, SEED)))
    loaded = load_tc_curve_json(str(path))
    assert loaded.rounds == a.rounds
    assert loaded.total_profit == a.total_profit
    for k in a.bins:
        assert loaded.bins[k].rounds == a.bins[k].rounds
        assert loaded.bins[k].profit == a.bins[k].profit


def test_ins_arm_attributes_insurance():
    res = run_tc_curve(
        STANDARD_6D_H17, "ins", seed=SEED, rounds=40_000, rules_name="h17"
    )
    insured = sum(b.ins_rounds for b in res.bins.values())
    assert insured > 0
    # composition-+EV insurance concentrates at high counts: the mean TC of
    # insured rounds must sit well above the overall mean (~0)
    hi = sum(b.ins_rounds for k, b in res.bins.items() if k >= 2)
    assert hi / insured > 0.5


def test_flat_ramp_matches_plain_simulator():
    m = simulate(
        STANDARD_6D_H17, OptimalStrategy(), seed=SEED, rounds=20_000, bet=1.0
    )
    res = run_ramp(
        STANDARD_6D_H17, "basic", parse_ramp("-99:1"),
        seed=SEED, rounds=20_000, rules_name="h17",
    )
    assert res.rounds == 20_000
    assert res.rounds_bet == 20_000
    assert res.bet_sum == 20_000.0
    assert res.profit == m.total_profit  # identical stream, identical arithmetic


def test_ramp_scaling_is_exact():
    r1 = run_ramp(
        STANDARD_6D_H17, "basic", parse_ramp("-99:1"),
        seed=SEED, rounds=15_000, rules_name="h17",
    )
    r2 = run_ramp(
        STANDARD_6D_H17, "basic", parse_ramp("-99:2"),
        seed=SEED, rounds=15_000, rules_name="h17",
    )
    assert math.isclose(r2.profit, 2 * r1.profit, abs_tol=1e-9)
    assert math.isclose(r2.money_edge, r1.money_edge, abs_tol=1e-12)


def test_ramp_wong_out_rounds_carry_no_money():
    res = run_ramp(
        STANDARD_6D_H17, "basic", parse_ramp("99:1"),
        seed=SEED, rounds=5_000, rules_name="h17",
    )
    assert res.rounds == 5_000
    assert res.rounds_bet == 0
    assert res.profit == 0.0


def test_parse_ramp_step_function():
    ramp = parse_ramp("-99:1,1:2,2:4,3:8")
    assert ramp_bet(ramp, -5.0) == 1.0
    assert ramp_bet(ramp, 0.9) == 1.0
    assert ramp_bet(ramp, 1.0) == 2.0
    assert ramp_bet(ramp, 2.5) == 4.0
    assert ramp_bet(ramp, 7.0) == 8.0
    assert ramp_bet(ramp, -100.0) == 0.0  # below the lowest step: sit out


def test_deviation_by_tc_partitions_diff():
    r = run_deviation_value(STANDARD_6D_H17, seed=SEED, rounds=2_000)
    assert sum(s.rounds for s in r.by_tc.values()) == r.rounds
    assert math.isclose(
        sum(s.profit for s in r.by_tc.values()), r.diff_sum, abs_tol=1e-9
    )
