"""E31 parallel launcher: run the mix-sweep realized shards across cores.

Each job is a PyPy subprocess of e31_mixsweep.py (banks its own shard JSON).
A bounded pool keeps to the machine's performance cores. This is the cheap-way
realized read: de-shrunk mixes (0.0, 0.05) at scale, to compare the filter's
D7/P8 SELECTION and realized excess against the existing mix-0.40 E30 shards.

Run (CPython launcher, PyPy workers):
    python data/e31_launch.py
"""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

MIXES = [0.0, 0.05]
SHARDS = [1, 2, 3, 4, 5, 6]
SHOES = 6
SAMPLES = 120
WORKERS = 6

jobs = [(mix, shard) for mix in MIXES for shard in SHARDS]


def run(job):
    mix, shard = job
    cmd = ["uv", "run", "--python", "pypy@3.11", "--no-project",
           "data/e31_mixsweep.py", str(shard), str(SHOES), str(SAMPLES),
           str(mix)]
    env = {"PYTHONPATH": "src"}
    import os
    env = {**os.environ, **env}
    p = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    tag = f"mix{mix} shard{shard}"
    if p.returncode != 0:
        return f"[FAIL] {tag}\n{p.stderr[-500:]}"
    return f"[ok] {tag}: {p.stdout.strip().splitlines()[-2] if p.stdout else ''}"


print(f"launching {len(jobs)} jobs ({len(MIXES)} mixes x {len(SHARDS)} shards, "
      f"{SHOES} shoes each), {WORKERS} workers")
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for msg in ex.map(run, jobs):
        print(msg)
        sys.stdout.flush()
print("done")
