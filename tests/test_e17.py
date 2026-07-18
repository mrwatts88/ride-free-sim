"""E17 harness gates: the analytic unbalanced-count search obeys its
constraints, and the multi-count curve pass partitions exactly, reproduces
the E16 hi-lo bins differentially, and round-trips through JSON.
"""

import math

from ridefree.counting import HILO_TAGS, STANDARD_H17_EOR
from ridefree.experiments import (
    load_count_curves_json,
    merge_count_curves,
    count_curves_to_json,
    run_count_curves,
    run_tc_curve,
    search_unbalanced_level1,
    unbalanced_bc,
)
from ridefree.rules import STANDARD_6D_H17

SEED = 246_813_579


def test_search_respects_constraints_and_beats_red7():
    best = search_unbalanced_level1(STANDARD_H17_EOR, top=3)
    assert len(best) == 3
    for bc, base, bump in best:
        tags = dict(base)
        assert tags[10] == -1
        assert sum(tags[r] for r in range(1, 10)) == 4  # imbalance +2 w/ bump
        assert 1 <= bump <= 9
        assert 0 < bc <= 1
    # red 7 = hi-lo base with the half-bump on 7; the search winner must be
    # at least as correlated with the EORs (red 7 is in the search space)
    red7 = dict(HILO_TAGS)
    red7[7] = red7[7] + 0.5
    assert best[0][0] >= unbalanced_bc(red7, STANDARD_H17_EOR) - 1e-12


def test_count_curves_partition_and_match_e16_hilo_bins():
    multi = run_count_curves(
        STANDARD_6D_H17, "basic", seed=SEED, rounds=15_000, rules_name="h17"
    )
    for name, bins in multi.by_signal.items():
        assert sum(b.rounds for b in bins.values()) == multi.rounds, name
        assert math.isclose(
            sum(b.profit for b in bins.values()), multi.total_profit,
            abs_tol=1e-9,
        ), name
    # differential: identical card stream => hilo_tc bins equal run_tc_curve's
    ref = run_tc_curve(
        STANDARD_6D_H17, "basic", seed=SEED, rounds=15_000, rules_name="h17"
    )
    assert multi.total_profit == ref.total_profit
    assert sorted(multi.by_signal["hilo_tc"]) == sorted(ref.bins)
    for k, b in ref.bins.items():
        m = multi.by_signal["hilo_tc"][k]
        assert (m.rounds, m.profit) == (b.rounds, b.profit)


def test_count_curves_custom_json_and_merge(tmp_path):
    custom = (dict(HILO_TAGS), 7)  # red 7 itself as the custom candidate
    a = run_count_curves(
        STANDARD_6D_H17, "basic", seed=SEED, rounds=8_000, rules_name="h17",
        custom=custom,
    )
    assert "custom_rc" in a.by_signal
    # custom == red 7 must produce IDENTICAL bins to the built-in red7_rc
    assert sorted(a.by_signal["custom_rc"]) == sorted(a.by_signal["red7_rc"])
    for k, b in a.by_signal["red7_rc"].items():
        c = a.by_signal["custom_rc"][k]
        assert (c.rounds, c.profit) == (b.rounds, b.profit)

    import json

    path = tmp_path / "cc.json"
    path.write_text(json.dumps(count_curves_to_json(a, SEED, custom)))
    loaded = load_count_curves_json(str(path))
    merged = merge_count_curves([loaded, loaded])
    assert merged.rounds == 2 * a.rounds
    for name, bins in a.by_signal.items():
        for k, b in bins.items():
            assert merged.by_signal[name][k].rounds == 2 * b.rounds
