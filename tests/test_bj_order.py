"""M12b Gate-B gates: the blackjack insurance order-adapter (bj_order.py).

The load-bearing science gates are structural, not numeric-remembered:

  * SINGLE-DECK EXACTNESS -- on a distinct one-deck stack the assumed-density
    filter is the exact rung-1 posterior (E29, 1e-9), so the walk drifts nowhere
    (`surprises == 0`) and prices are exact.
  * CHANNEL CLOSED BY TWO PASSES -- DFH Cor 4.2 makes two 10-shelf passes a
    ~200-shelf (near-uniform) mix; the observer's hole-ten price must collapse
    onto the composition counter's (E27: two passes kill the value channel).
  * CHANNEL OPEN AND CALIBRATED AT ONE PASS -- one 10-shelf pass leaves a real
    ordered-vs-composition gap (E27: +5.47 u/deck of order value), and the exact
    ordered price stays calibrated: its taken-spot ten-rate matches its own
    predicted rate within binomial noise (the E17 realized-vs-predicted gate).

Plus exact pricing arithmetic on a synthetic ledger and the mix=1 invariant
(the observer degenerates to the perfect counter). The large-N calibration and
the real 6-deck numbers live in the data run (data/e33_*.py, PyPy). Test pins:
23.5e9 block.
"""

import math

from ridefree.bj_order import (
    deviation_experiment,
    insurance_experiment,
    summarize_insurance,
)
from ridefree.rules import STANDARD_6D_H17


def _mean_abs_gap(result):
    spots = result["spots"]
    return sum(abs(s["model_p"] - s["counter_p"]) for s in spots) / len(spots)


def test_single_deck_is_the_exact_regime():
    # decks=1 -> distinct stack -> the ADF is ShelfPosterior exactly, so no
    # projection ever drifts and every recorded price is a real probability.
    res = insurance_experiment(
        STANDARD_6D_H17, shelves=10, shoes=60, seed=23_500_000_101,
        decks=1, min_tail=18,
    )
    assert res["surprises"] == 0, "distinct single deck must not drift"
    assert res["spots"], "expected some ace-up rounds"
    for s in res["spots"]:
        assert 0.0 <= s["model_p"] <= 1.0
        assert 0.0 <= s["counter_p"] <= 1.0


def test_two_passes_close_the_channel():
    # One pass leaves order structure; two passes (Cor 4.2 ~200 shelves) wash it
    # out, so the observer's price must fall back onto composition.
    one = insurance_experiment(
        STANDARD_6D_H17, shelves=10, shoes=80, seed=23_500_000_201,
        decks=1, min_tail=18, passes=1,
    )
    two = insurance_experiment(
        STANDARD_6D_H17, shelves=10, shoes=15, seed=23_500_000_211,
        decks=1, min_tail=18, passes=2,
    )
    gap_one = _mean_abs_gap(one)
    gap_two = _mean_abs_gap(two)
    assert gap_two < 0.5 * gap_one, (gap_one, gap_two)
    assert gap_two < 0.02, gap_two  # near-uniform: price ~ composition


def test_one_pass_channel_is_open_and_calibrated():
    # The scientific claim in miniature: a real ordered->composition gap that is
    # honestly calibrated. Single deck, exact filter, mix irrelevant (0).
    res = insurance_experiment(
        STANDARD_6D_H17, shelves=10, shoes=500, seed=23_500_000_301,
        decks=1, min_tail=18,
    )
    assert _mean_abs_gap(res) > 0.03, "one pass should leave a real gap"
    summ = summarize_insurance(res, mixes=[0.0])
    m0 = summ["mixes"][0.0]
    assert summ["bits_per_spot"] > 0.0  # order beats composition in log-loss
    bets = m0["filter"]["bets"]
    if bets >= 40:  # enough taken spots for a calibration read
        se = math.sqrt(max(m0["cal_predicted_ten"] * (1 - m0["cal_predicted_ten"]),
                           1e-6) / bets)
        cal_gap = abs(m0["cal_realized_ten"] - m0["cal_predicted_ten"])
        assert cal_gap < 3.5 * se, (m0, se)  # exact model calibrated within noise


def test_mix_one_degenerates_to_the_counter():
    res = insurance_experiment(
        STANDARD_6D_H17, shelves=10, shoes=60, seed=23_500_000_401,
        decks=1, min_tail=18,
    )
    summ = summarize_insurance(res, mixes=[1.0])
    m1 = summ["mixes"][1.0]["filter"]
    c = summ["counter"]
    assert m1["bets"] == c["bets"]
    assert m1["realized"] == c["realized"]
    assert summ["mixes"][1.0]["excess_realized"] == 0.0


def test_summarize_prices_insurance_exactly():
    # Two hand-computed spots (pays 2:1, threshold 1/3), one shoe.
    result = {
        "shoes": 1, "insurance_pays": 2.0,
        "spots": [
            {"shoe": 0, "model_p": 0.5, "counter_p": 0.30, "hole_ten": True},
            {"shoe": 0, "model_p": 0.2, "counter_p": 0.40, "hole_ten": False},
        ],
    }
    summ = summarize_insurance(result, mixes=[0.0])
    m = summ["mixes"][0.0]
    # observer(mix0): takes spot1 (0.5>1/3, +2), skips spot2 -> realized +2
    assert m["filter"]["bets"] == 1
    assert m["filter"]["realized"] == 2.0
    assert abs(m["filter"]["predicted"] - 0.5) < 1e-12  # (1+2)*0.5 - 1
    # counter: skips spot1 (0.30<1/3), takes spot2 (0.40>1/3, -1) -> realized -1
    assert summ["counter"]["bets"] == 1
    assert summ["counter"]["realized"] == -1.0
    assert abs(summ["counter"]["predicted"] - 0.2) < 1e-12
    # excess = +2 - (-1) = +3
    assert m["excess_realized"] == 3.0
    # bits: spot1 log2(.5/.3) + spot2 log2(.8/.6), averaged
    exp_bits = 0.5 * (math.log2(0.5 / 0.3) + math.log2(0.8 / 0.6))
    assert abs(summ["bits_per_spot"] - exp_bits) < 1e-12


def test_smoke_multideck_mix_sweep():
    # decks=2 exercises the copy-ambiguity drift and the contamination floor
    # cheaply; the mix sweep and excess z must stay well-formed.
    res = insurance_experiment(
        STANDARD_6D_H17, shelves=10, shoes=40, seed=23_500_000_501, decks=2,
    )
    assert res["spots"]
    summ = summarize_insurance(res, mixes=[0.0, 0.1, 0.4, 1.0])
    for mix, d in summ["mixes"].items():
        assert d["filter"]["bets"] >= 0
        assert math.isfinite(d["excess_z"])
    # mix=1 still degenerates to the counter even with copies present
    assert summ["mixes"][1.0]["excess_realized"] == 0.0


# --- hole-card play (deviations arm) ---------------------------------------

def test_clairvoyant_hole_play_is_large_and_composition_is_sane():
    # Perfect hole knowledge is worth ~+10%/round (the known large value of
    # hole-card play); composition-optimal play is near even. These anchor the
    # harness: the ceiling is real and the baseline plays correctly.
    r = deviation_experiment(
        STANDARD_6D_H17, shelves=10, shoes=1200, seed=23_600_000_701,
        decks=1, min_tail=18,
    )
    assert r["clair_delta_per_round"] > 0.05, r  # huge, well above noise
    assert r["clair_z"] > 6.0, r
    assert -0.03 < r["comp_per_round"] < 0.04, r  # composition ~ even
    # the order arm cannot beat perfect hole knowledge
    assert r["order_delta_per_round"] <= r["clair_delta_per_round"] + 1e-9


def test_hole_play_turns_on_at_weak_shuffles():
    # The scientific claim: order-driven hole-card play is dead at the
    # well-mixed 10-shelf machine but turns on as the shuffle weakens. One
    # shelf leaves strong order structure -> a real, significant play edge.
    weak = deviation_experiment(
        STANDARD_6D_H17, shelves=1, shoes=1500, seed=23_600_000_801,
        decks=1, min_tail=18,
    )
    strong = deviation_experiment(
        STANDARD_6D_H17, shelves=10, shoes=1500, seed=23_600_000_801,
        decks=1, min_tail=18,
    )
    assert weak["order_delta_per_round"] > strong["order_delta_per_round"], (
        weak["order_delta_per_round"], strong["order_delta_per_round"])
    assert weak["order_z"] > 2.5, weak  # a real edge at a weak shuffle
    assert weak["order_delta_per_round"] > 0.01, weak  # and a big one
