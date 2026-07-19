"""E22 step 0: is a positive-end main ramp worth anything ON THE RIDE FREE
TABLE (where the side card seats us)? Arithmetic over the banked E20
normal-arm bins — the TC-perfect ceiling for crouch-style ramps, i.e. the
most any "all-in-one" card could add on the main-bet side.

    uv run python data/e22_positive_end.py

Answer (2026-07-18, drove the E22 design): DEAD. RF main EV doesn't cross
zero until TC +5 (the dealer-22 push blunts ten-rich standing), the
crouch15-style ramp is NEGATIVE on this table, and the biggest sane rung
adds ~$7/h against the side's $69-300/h. The comprehensive play is a
portfolio (pog2 at Ride Free, crouch15-2r at classic), not a fusion count.
"""

from ridefree.experiments import load_pog_curve_json, merge_pog_curves

PACE = 200
FLOOR = 15.0
RAMPS = [
    ("crouch15 jumps ($100/+2 $150/+3 $200/+4)", {2: 100, 3: 150, 4: 200}),
    ("2-rung ($100/+2 $200/+4)", {2: 100, 4: 200}),
    ("top-only ($200/+4)", {4: 200}),
    ("top-only ($200/+3)", {3: 200}),
    ("monster ($500/+4)", {4: 500}),
]


def main() -> None:
    norm = merge_pog_curves(
        [load_pog_curve_json(f"data/m10b_rf_p75_s{i:02d}.json")
         for i in range(1, 11)]
    )
    print("RIDE_FREE main EV by hi-lo TC bin (pen .75, 20M rounds, "
          "normal arm):")
    print(f"  {'tc':>4s} {'freq':>8s} {'main EV':>9s} {'±1se':>8s}")
    for k in sorted(norm.bins):
        b = norm.bins[k]
        if b.rounds < 20_000:
            continue
        print(f"  {k:+4d} {100 * b.rounds / norm.rounds:7.3f}% "
              f"{100 * b.main_ev:+8.3f}% {100 * b.main_stderr:7.3f}%")

    print("\ncrouch-style positive-end ramps over the $15 floor (marginal "
          "$/h vs flat $15 at 200 r/h — the ADD-ON a dual card could earn):")
    for name, rungs in RAMPS:
        total = 0.0
        for k, b in norm.bins.items():
            bet = FLOOR
            for thresh in sorted(rungs):
                if k >= thresh:
                    bet = rungs[thresh]
            total += (b.rounds / norm.rounds) * (bet - FLOOR) * b.main_ev
        print(f"  {name:<44s} {PACE * total:>+8.2f}/h")


if __name__ == "__main__":
    main()
