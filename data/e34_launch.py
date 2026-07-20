"""E34 parallel launcher: the hole-card-play capture curve vs shuffle strength.

Single-deck (exact filter) shelf sweep + a 200-shelf null (two 10-shelf passes),
plus a few six-deck points for the real-game magnitude. Each job is a PyPy
subprocess of e34_holeplay.py. Pool with data/e34_verdict.py.

Run:  python data/e34_launch.py
"""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (config, shelves, shoes, passes)
JOBS = [("sd", m, 5000, 1) for m in (1, 2, 3, 4, 6, 8, 10)]
JOBS += [("sd", 10, 5000, 2)]                       # two-pass null (~200 shelves)
JOBS += [("6d", m, 600, 1) for m in (1, 2, 4, 10)]  # real-game magnitude
WORKERS = 6


def run(job):
    config, shelves, shoes, passes = job
    cmd = ["uv", "run", "--python", "pypy@3.11", "--no-project",
           "data/e34_holeplay.py", config, str(shelves), str(shoes), str(passes)]
    env = {**os.environ, "PYTHONPATH": "src"}
    p = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    tag = f"{config} m{shelves} p{passes}"
    if p.returncode != 0:
        return f"[FAIL] {tag}\n{p.stderr[-800:]}"
    lines = p.stdout.strip().splitlines()
    return f"[ok] {tag}: {lines[-2] if len(lines) >= 2 else ''}"


print(f"launching {len(JOBS)} jobs ({WORKERS} workers)")
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for msg in ex.map(run, JOBS):
        print(msg)
        sys.stdout.flush()
print("done")
