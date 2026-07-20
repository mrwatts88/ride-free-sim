"""E33 parallel launcher: run the insurance shards across cores.

Each job is a PyPy subprocess of e33_insurance.py (banks its own shard JSON):
6 single-deck shards (exact-filter anchor) + 6 six-deck shards (the real-game
money number). Pool/certify with data/e33_verdict.py {sd,6d}.

Run (CPython launcher, PyPy workers):
    python data/e33_launch.py
"""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

SHARDS = [1, 2, 3, 4, 5, 6]
JOBS = [("sd", s, 3000) for s in SHARDS] + [("6d", s, 500) for s in SHARDS]
WORKERS = 6


def run(job):
    config, shard, shoes = job
    cmd = ["uv", "run", "--python", "pypy@3.11", "--no-project",
           "data/e33_insurance.py", config, str(shard), str(shoes)]
    env = {**os.environ, "PYTHONPATH": "src"}
    p = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    tag = f"{config} shard{shard}"
    if p.returncode != 0:
        return f"[FAIL] {tag}\n{p.stderr[-800:]}"
    head = p.stdout.strip().splitlines()[0] if p.stdout else ""
    return f"[ok] {tag}: {head}"


print(f"launching {len(JOBS)} jobs ({WORKERS} workers)")
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for msg in ex.map(run, JOBS):
        print(msg)
        sys.stdout.flush()
print("done")
