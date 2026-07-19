"""Tests for the E25 RA bank: paired second-moment machinery.

The strongest gate is exact agreement with the certified E5/E16 paired
harness (run_deviation_value) on the same seed — both walk the same chart
timeline and replay the same composition strategy, so the per-bin deviation
sums must match bit for bit.
"""

from ridefree.experiments import (
    load_ra_bank_json,
    merge_ra_banks,
    ra_bank_to_json,
    run_deviation_value,
    run_ra_bank,
)
from ridefree.rules import STANDARD_6D_H17

SEED = 25_250_001  # test-local; experiment blocks stay at 21.4e9+


def _small(seed=SEED, rounds=20_000, dev_tc_min=2, **kw):
    return run_ra_bank(
        STANDARD_6D_H17, seed=seed, rounds=rounds, dev_tc_min=dev_tc_min,
        rules_name="STANDARD_6D_H17", **kw,
    )


def test_deterministic_under_seed():
    a = ra_bank_to_json(_small(rounds=8_000), SEED)
    b = ra_bank_to_json(_small(rounds=8_000), SEED)
    assert a == b


def test_replay_self_check_passes():
    # The harness re-replays the chart from its snapshot and asserts the
    # profit reproduces — the snapshot/restore mechanics gate.
    _small(rounds=4_000, self_check=True)


def test_bin_bookkeeping():
    res = _small(rounds=20_000)
    assert sum(b.rounds for b in res.bins.values()) == res.rounds
    for k, b in res.bins.items():
        if k < res.dev_tc_min:
            assert b.dev_rounds == 0
        else:
            assert b.dev_rounds == b.rounds  # every round there is replayed
        assert b.ins_bj <= b.ins_rounds <= b.rounds


def test_candidate_cells_are_chart_shaped():
    res = _small(rounds=60_000)
    keys = set(res.cells)
    # the chart doubles 11 v 6 constantly; it never doubles a hard 16
    assert any(k.startswith("noD:h11v") for k in keys)
    assert not any(k.startswith("noD:h16") or k.startswith("noD:h17") for k in keys)
    # suppression cells are only doubles/splits; splits carry pair rows
    for k in keys:
        if k.startswith("no"):
            assert k[2] in ("D", "P")
            if k.startswith("noP:"):
                assert k[4] == "p"
    # dev cells appear only at bins >= dev_tc_min
    for k, by_bin in res.cells.items():
        if k.startswith("dev:"):
            assert min(by_bin) >= res.dev_tc_min


def test_insurance_overlay_counts_sane():
    res = _small(rounds=60_000)
    n_a = sum(b.ins_rounds for b in res.bins.values())
    n_bj = sum(b.ins_bj for b in res.bins.values())
    # ace up ~1/13 of rounds; hole completes a natural ~96/311 of those
    assert 0.055 < n_a / res.rounds < 0.10
    assert 0.24 < n_bj / n_a < 0.38


def test_merge_and_json_roundtrip(tmp_path):
    import json

    a, b = _small(seed=SEED, rounds=10_000), _small(seed=SEED + 7, rounds=10_000)
    merged = merge_ra_banks([a, b])
    assert merged.rounds == a.rounds + b.rounds
    k = max(merged.bins, key=lambda k: merged.bins[k].rounds)
    assert merged.bins[k].p_sum == (
        (a.bins[k].p_sum if k in a.bins else 0.0)
        + (b.bins[k].p_sum if k in b.bins else 0.0)
    )
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(ra_bank_to_json(merged, SEED)))
    loaded = load_ra_bank_json(str(path))
    assert ra_bank_to_json(loaded, SEED) == ra_bank_to_json(merged, SEED)


def test_dev_moments_match_certified_paired_harness():
    # Bit-exact cross-gate: run_deviation_value walks the same chart timeline
    # (same shoe_seeds, same OptimalStrategy base) and replays the same
    # composition strategy, so per-bin paired sums must agree EXACTLY with the
    # RA bank's dev accumulators when the bank replays every bin.
    rounds = 5_000
    bank = _small(rounds=rounds, dev_tc_min=-8)
    ref = run_deviation_value(STANDARD_6D_H17, seed=SEED, rounds=rounds)
    ref_bins = {k: s for k, s in ref.by_tc.items()}
    for k, b in bank.bins.items():
        s = ref_bins.get(k)
        assert s is not None and s.rounds == b.dev_rounds
        assert abs(s.profit - b.dev_d_sum) < 1e-9
        assert abs(s.profit_sq - b.dev_d_sq) < 1e-9
    assert abs(ref.diff_sum - sum(b.dev_d_sum for b in bank.bins.values())) < 1e-9
