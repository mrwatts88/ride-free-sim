"""Fast/slow test split — keeps a routine `uv run pytest` quick.

The heavy statistical / Monte-Carlo gate tests (each simulating tens of
thousands to millions of rounds) are auto-marked `slow` here, so the default
run — which `pyproject.toml` pins to `-m 'not slow'` — skips them and leaves the
fast unit + exact tests (~40 s instead of ~6.5 min). Run the full validation
battery before any milestone gate, per the CLAUDE.md ladder:

    uv run pytest -m slow                # only the heavy gates
    uv run pytest -m "slow or not slow"  # everything

The list below is the >~2 s tests from a full-suite `--durations=40` run
(2026-07-20; total 6:34, with ~90% of the wall-clock in these). It fails OPEN: a
renamed/removed test simply rejoins the fast suite (a little slower) — never a
wrong result. Re-measure and update if it drifts:

    uv run pytest -m "slow or not slow" --durations=40
"""

import pytest

# Whole modules that are nothing but heavy end-to-end simulations.
SLOW_FILES = {
    "test_bj_order.py",  # E33/E34 order-adapter capture curves (78 s + 52 s + …)
    "test_ra_bank.py",   # E25 RA-bank paired second-moment sims
}

# Individual heavy tests living inside otherwise-fast (exact / unit) modules.
SLOW_TESTS = {
    "test_bac_track_smoke",                              # test_baccarat.py
    "test_bac_ev_scan_smoke",                            # test_baccarat.py
    "test_side_bet_invariant_to_playing_strategy",       # test_21p3.py
    "test_csm_always_bet_edge_near_published",           # test_21p3.py
    "test_csm_always_bet_edge_near_nv_rules_prediction", # test_pog.py
    "test_split_fives_farms_more_tokens",                # test_pog.py
    "test_pog_leaves_the_main_game_untouched",           # test_pog.py
    "test_metrics_histogram_and_max_tokens",             # test_pog.py
    "test_insurance_ev_matches_exact_six_deck_value",    # test_insurance.py
    "test_posterior_guesser_dominates_conjectured_strategy",  # test_posterior.py
    "test_multideck_matches_brute_force_within_mc",      # test_posterior.py
    "test_proposition_realizes_predicted_edge",          # test_posterior.py
    "test_adf_proposition_realizes_predicted_edge",      # test_posterior.py
    "test_exact_e_dp_deck_scale_m2_matches_mc",          # test_guessing_theorem.py (E37)
    "test_approx_e_dp_multiset_beats_run_count_at_deck_scale",  # test_guessing_theorem.py (E38)
    "test_approx_e_dp_deck_scale_m10_matches_mc",        # test_guessing_theorem.py (E38)
    "test_coup_experiment_smoke_and_gate",               # test_coup.py
    "test_shelf_guessing_reproduces_dfh_table2",         # test_shuffle.py
    "test_two_pass_guessing_near_chance",                # test_shuffle.py
    "test_riffle_sampler_matches_bayer_diaconis",        # test_shuffle.py
    "test_color_changes_reproduce_dfh",                  # test_shuffle.py
    "test_exact_matches_engine_monte_carlo",             # test_dealer_odds.py
}


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Tag the heavy gate tests `slow` before pytest's `-m` filter deselects."""
    slow = pytest.mark.slow
    for item in items:
        base = getattr(item, "originalname", None) or item.name
        if item.path.name in SLOW_FILES or base in SLOW_TESTS:
            item.add_marker(slow)
