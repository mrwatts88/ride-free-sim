"""E29 — M12b rung 3a: the O(slots) assumed-density posterior, gated; the
copy-isolation study; the 8-deck door opened.

Four parts, all on the composition-fair value-8 proposition (perfect counter
nets exactly zero by construction — profit is pure order structure):

1. ADF-vs-PF paired fidelity (CRN: identical shoes per seed) at 1-3 decks —
   the deck counts where the E28 particle filter is a trustworthy referee.
2. The 8-deck contamination fit: MIX swept on a fit block, the chosen value
   certified on a FRESH out-of-sample block (the E17 gate on untouched
   seeds). This is the first 8-deck number in the project.
3. The copy-isolation study: the same shoes priced by the honest class
   observer (copies indistinct) and by a position-resolution observer
   (exact rung-1 filtering) — the paired difference is the pure COPY TAX at
   fixed n, freed of the mixing-adequacy confound (a fixed 10-shelf machine
   mixes a bigger stack worse); the position rows across n measure that
   confound directly.
4. The manufacturer's-fix control: two passes must collapse the channel for
   the ADF exactly as they did for the exact posterior (E27) and PF (E28).

Usage: PYTHONPATH=src uv run --python pypy@3.11 --no-project \
           python data/e29_adf.py [scale]
Seeds: 23.1e9 block. Banks data/e29_adf.json.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ridefree.posterior import multideck_proposition_experiment as mpe

SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0


def run(tag, trials, **kw):
    trials = max(10, int(trials * SCALE))
    t0 = time.perf_counter()
    r = mpe(trials=trials, shelves=10, target_value=8, **kw)
    dt = time.perf_counter() - t0
    row = {
        "tag": tag,
        "trials": trials,
        **r.info,
        "seed": kw["seed"],
        "ms_per_shoe": dt / trials * 1000,
        "bets_per_shoe": r.bets / trials,
        "edge_per_bet": r.edge_per_bet,
        "units_per_shoe": r.realized / trials,
        "predicted_per_shoe": r.predicted / trials,
        "bits_per_shoe": r.bits_per_shoe,
        "z": r.z,
    }
    print(
        f"{tag:34s} n={row['n']:3d} trials={trials:4d} "
        f"bets {row['bets_per_shoe']:7.2f}  u/shoe {row['units_per_shoe']:+8.3f} "
        f"pred {row['predicted_per_shoe']:+8.3f}  bits {row['bits_per_shoe']:+9.3f} "
        f"z {row['z']:+6.2f}  surp {row['surprises']/trials:6.2f}  ms {row['ms_per_shoe']:6.0f}"
    )
    return row


results = {"scale": SCALE, "target_value": 8, "threshold": 0.02, "rows": []}
R = results["rows"]

print("== part 1: ADF vs PF, CRN-paired (identical shoes per seed) ==")
for i, (decks, trials, particles) in enumerate(((1, 150, 120), (2, 100, 120), (3, 60, 120))):
    seed = 23_100_000_001 + i
    R.append(run(f"p1 d{decks} pf", trials, decks=decks, seed=seed, particles=particles, method="pf"))
    R.append(run(f"p1 d{decks} adf", trials, decks=decks, seed=seed, particles=particles, method="adf"))

print("== part 2: the 8-deck contamination fit (fit block) ==")
fit_rows = []
for mix in (0.02, 0.10, 0.25, 0.40):
    row = run(f"p2 d8 adf mix={mix:.2f} FIT", 40, decks=8, seed=23_100_000_010,
              particles=1, method="adf", adf_mix=mix)
    row["mix"] = mix
    fit_rows.append(row)
    R.append(row)
# The stated rule, fixed before the OOS block runs: the smallest mix with
# bits > 0 and |z| < 2 on the fit block; if none qualifies, the largest mix.
chosen = next((r for r in fit_rows if r["bits_per_shoe"] > 0 and abs(r["z"]) < 2),
              fit_rows[-1])
results["mix_chosen"] = chosen["mix"]
print(f"   -> chosen mix {chosen['mix']:.2f} (rule: smallest with bits>0 and |z|<2)")

print("== part 2b: 8-deck OUT-OF-SAMPLE certification (fresh seeds) ==")
oos = run(f"p2 d8 adf mix={chosen['mix']:.2f} OOS", 80, decks=8, seed=23_100_000_011,
          particles=1, method="adf", adf_mix=chosen["mix"])
oos["mix"] = chosen["mix"]
R.append(oos)

print("== part 3: copy isolation — class vs position observer, same shoes ==")
for i, (decks, trials) in enumerate(((1, 100), (2, 80), (3, 60), (4, 40))):
    seed = 23_100_000_020 + i
    R.append(run(f"p3 d{decks} class (copies)", trials, decks=decks, seed=seed,
                 particles=1, method="adf", observer="class"))
    R.append(run(f"p3 d{decks} position (distinct)", trials, decks=decks, seed=seed,
                 particles=1, method="adf", observer="position"))

print("== part 4: the two-pass fix control (ADF) ==")
R.append(run("p4 d2 adf 2-pass", 40, decks=2, seed=23_100_000_030, particles=1,
             method="adf", passes=2))

out = Path(__file__).with_name("e29_adf.json")
out.write_text(json.dumps(results, indent=1))
print(f"\nBanked {out}")
