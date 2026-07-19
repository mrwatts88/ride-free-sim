"""PyPy-vs-CPython benchmark for the paradigm-2 hot paths (M7 revisit).

Two workloads, both deterministic so the printed CHECKSUMS must be identical
under CPython and PyPy (a correctness gate for the alt interpreter — pure
stdlib should be bit-identical); the WALL times give the speedup.

  1. Blackjack reference engine (`simulate`, BasicStrategy) — the classic
     throughput question (is PyPy worth it before any Rust talk?).
  2. The rung-1 posterior proposition walk — the M12b hot path, which is
     what a multi-deck baccarat gate will be bottlenecked on.

Usage: <python> data/bench_pypy.py [scale]   (scale defaults to 1)
Run the SAME command under `python` (CPython) and a PyPy interpreter; compare.
"""

import sys
import time

from ridefree.posterior import proposition_experiment
from ridefree.rules import STANDARD_6D_H17
from ridefree.simulator import simulate
from ridefree.strategy import BasicStrategy

SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
print(f"interpreter: {sys.implementation.name} {sys.version.split()[0]}")


def timed(label, fn):
    t0 = time.perf_counter()
    checksum = fn()
    dt = time.perf_counter() - t0
    print(f"  {label:28s} {dt:8.3f}s   checksum={checksum}")
    return dt


def engine():
    rounds = int(300_000 * SCALE)
    m = simulate(STANDARD_6D_H17, BasicStrategy(), seed=990_000_001, rounds=rounds)
    return f"{m.edge:.8f}"


def posterior():
    trials = int(800 * SCALE)
    r = proposition_experiment(shelves=10, trials=trials, seed=990_000_002)
    return f"{r.realized:.6f}/{r.bets}"


print("== workloads ==")
timed("engine simulate (blackjack)", engine)
timed("posterior proposition walk", posterior)
print("done")
