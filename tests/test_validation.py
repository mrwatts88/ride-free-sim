"""Tests for the validation suite machinery (fast; small N)."""

from ridefree.rules import Rules
from ridefree.validation import Check, run_suite, to_html  # noqa: F401

H17 = Rules()


def test_check_pass_fail_logic():
    ok = Check("x", observed=0.10, reference=0.10, stderr=0.01, source="s")
    assert ok.status == "PASS"
    bad = Check("y", observed=0.20, reference=0.10, stderr=0.01, source="s")
    assert bad.status == "FAIL"  # 10 sigma off
    base = Check("z", observed=0.10, reference=None, stderr=0.0, source="s")
    assert base.status == "BASELINE"


def test_suite_structure_and_baselines():
    checks, m = run_suite(
        H17, seed=5, game_rounds=20_000, dealer_trials=100_000
    )
    names = {c.name for c in checks}
    # dealer bust checks for all ten up-cards, plus the headline metrics
    assert sum(1 for c in checks if c.name.startswith("dealer bust vs up-card")) == 10
    assert "dealer bust (aggregate)" in names
    assert "house edge" in names
    assert "player natural rate" in names
    assert "per-round std dev (abs)" in names
    assert m.rounds == 20_000
    # frequencies are collected as baselines, not hard failures
    assert any(c.name == "split rate" and c.status == "BASELINE" for c in checks)
    # std dev is advisory (imprecise folk reference), never gates a run
    assert any(c.name.startswith("per-round std dev") and c.status == "ADVISORY"
               for c in checks)


def test_advisory_never_fails():
    c = Check("x", observed=1.5, reference=1.0, stderr=0.001, source="s",
              is_percent=False, advisory=True)
    assert c.status == "ADVISORY"  # far off, but advisory → not FAIL


def test_html_report_renders():
    from ridefree.validation import to_html

    checks, m = run_suite(H17, seed=3, game_rounds=8_000, dealer_trials=80_000)
    html = to_html(checks, m, generated_at="2026-07-17 00:00 UTC")
    assert "<!doctype html>" in html
    assert "STANDARD_6D_H17" in html
    assert "house edge" in html
    assert "badge" in html


def test_dealer_checks_pass_at_small_scale():
    # The exact-vs-engine dealer checks should pass even at modest trial counts,
    # since the reference is the exact calc (same model as the MC).
    checks, _ = run_suite(
        H17, seed=9, game_rounds=10_000, dealer_trials=300_000
    )
    dealer_checks = [c for c in checks if c.name.startswith("dealer bust vs up-card")]
    assert all(c.status == "PASS" for c in dealer_checks)
