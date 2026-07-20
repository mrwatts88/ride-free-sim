"""E36 — break the n! wall: is the optimal per-step hit probability a function
of a SMALL sufficient statistic of the prefix?  (docs/GUESSING_THEOREM.md §1)

The exact value is E_opt(n,m) = Σ over prefixes q of P(q) · max_c P(next=c | q)
(the trie-max sum in `guessing_theorem.exact_e`). That enumeration is O(n·n!),
so exact values die at n≈9. The prize (Clay's OPEN m-shelf transition matrix)
is to aggregate that sum over prefixes WITHOUT enumerating them — which is
possible iff the per-step optimal hit h(q) = max_c P(next=c | q) depends on the
prefix q only through a small, Markov-evolving statistic σ(q).

This is the cheap scoping probe: enumerate EVERY prefix exactly (n ≤ 9, via a
DFS carrying a `ShelfPosterior`), and for each candidate statistic σ, test
whether h(q) is CONSTANT across all prefixes sharing σ(q). A ladder of σ from
coarse to the ceiling:

  step            : (t)                              -- control, must fail
  dir_rank        : (t, G-direction, rank of last among remaining)
  dir_gaps        : (t, dir, gap below, gap above)   -- clipped, "coarse gaps"
  dir_rank_gaps   : (t, dir, rank, gap below, gap above)   -- the doc's candidate
  dir_rank_ext    : (t, dir, rank, last-is-min?, last-is-max?)
  set_last_dir    : (remaining SET, last, dir)       -- ceiling: does order matter?
  set_last        : (remaining SET, last)            -- ceiling without direction

Verdict per σ: max within-group RANGE of h (exact-sufficiency; <1e-9 ⇒ σ is a
sufficient statistic) and the mass-weighted R² (how much of h's variation σ
explains — an "approximately sufficient" read). Plus |state space| growth in n
(polynomial ⇒ the DP is buildable; exponential ⇒ only a partial win).

Cards are labelled 1..n = original stack positions (forensics convention), so
rank/gap statistics are exactly what DFH's strategy G reads.

    uv run python data/gt_sufficiency.py [n_max] [m1,m2,...]
    # PyPy (~4x) for n=9:
    # PYTHONPATH=src ~/.local/bin/pypy3.11 -u data/gt_sufficiency.py 9 2,3,5
"""

import sys
from bisect import bisect_left

from ridefree.guessing_theorem import exact_e, run_lengths, walk_prefixes
from ridefree.posterior import ShelfPosterior

CAP = 4  # gaps clipped here: "coarse summary of the gap structure"


def candidate_keys(t, dir_up, last, R, n, ndesc, runcomp):
    """All candidate statistics σ(prefix) as hashable keys.

    `R` is the sorted list of remaining cards (last ∉ R); `last` is the most
    recently revealed card (0 at t=0); `dir_up` is DFH strategy G's direction;
    `ndesc` is the number of descents in the revealed prefix (each descent
    forces a shelf-lane boundary — the order information set+last discards).
    """
    rank = bisect_left(R, last)  # remaining cards strictly below last
    nR = len(R)
    below_card = R[rank - 1] if rank > 0 else 0
    above_card = R[rank] if rank < nR else n + 1
    d_below = last - below_card  # ≥1 when a remaining card is below, else = last
    d_above = above_card - last
    cb, ca = min(d_below, CAP), min(d_above, CAP)
    return {
        "step": (t,),
        "dir_rank": (t, dir_up, rank),
        "dir_gaps": (t, dir_up, cb, ca),
        "dir_rank_gaps": (t, dir_up, rank, cb, ca),
        "dir_rank_ext": (t, dir_up, rank, rank == 0, rank == nR),
        "dir_rank_desc": (t, dir_up, rank, ndesc),
        "dir_rank_desc_gaps": (t, dir_up, rank, ndesc, cb, ca),
        "dir_rank_runcomp": (dir_up, rank, runcomp),
        "set_last_dir": (frozenset(R), last, dir_up),
        "set_last": (frozenset(R), last),
    }


STAT_NAMES = [
    "step", "dir_rank", "dir_gaps", "dir_rank_gaps", "dir_rank_ext",
    "dir_rank_desc", "dir_rank_desc_gaps", "dir_rank_runcomp",
    "set_last_dir", "set_last",
]


class Agg:
    """Per-group accumulator: mass-weighted moments of the hit probability plus
    the exact min/max (for the strict within-group range test)."""

    __slots__ = ("count", "mass", "mh", "mh2", "lo", "hi")

    def __init__(self):
        self.count = 0
        self.mass = 0.0
        self.mh = 0.0
        self.mh2 = 0.0
        self.lo = 2.0
        self.hi = -1.0

    def add(self, hit, mass):
        self.count += 1
        self.mass += mass
        self.mh += mass * hit
        self.mh2 += mass * hit * hit
        if hit < self.lo:
            self.lo = hit
        if hit > self.hi:
            self.hi = hit


def prefix_statistics(prefix, n):
    """Derive (t, dir_up, last, R, ndesc, runcomp) from a revealed prefix —
    everything the candidate keys read. `R` is the sorted remaining cards,
    `dir_up` is DFH strategy G's direction, `runcomp` its ascending-run
    composition (see `run_lengths`)."""
    t = len(prefix)
    last = prefix[-1] if prefix else 0
    R = sorted(set(range(1, n + 1)).difference(prefix))
    runcomp = run_lengths(prefix)
    ndesc = len(runcomp) - 1 if runcomp else 0
    dir_up = (t < 2) or (prefix[-1] > prefix[-2])
    return t, dir_up, last, R, ndesc, runcomp


def probe(n, m):
    """Walk every prefix once (shared `walk_prefixes` core); bin the optimal
    per-step hit by each candidate statistic. Returns (aggs, totals)."""
    aggs = {name: {} for name in STAT_NAMES}
    tot = {"e_opt": 0.0, "mass": 0.0, "mh": 0.0, "mh2": 0.0}
    for prefix, hit, pprob in walk_prefixes(n, m):
        tot["e_opt"] += pprob * hit
        tot["mass"] += pprob
        tot["mh"] += pprob * hit
        tot["mh2"] += pprob * hit * hit
        t, dir_up, last, R, ndesc, runcomp = prefix_statistics(prefix, n)
        for name, key in candidate_keys(
                t, dir_up, last, R, n, ndesc, runcomp).items():
            a = aggs[name].get(key)
            if a is None:
                a = aggs[name][key] = Agg()
            a.add(hit, pprob)
    return aggs, tot


def witness(n, m, keyfn, label):
    """Find a concrete collision: two prefixes with the SAME statistic `keyfn`
    but different optimal hit — proof the statistic is not sufficient. `keyfn`
    takes (prefix, R, last, dir_up, ndesc, n) and returns a hashable key."""
    buckets: dict = {}

    def descend(post, prefix, dir_up, ndesc):
        t = len(prefix)
        probs = post.next_probs()
        hit = max(probs.values())
        last = prefix[-1] if prefix else 0
        R = sorted(probs)
        key = keyfn(prefix, R, last, dir_up, ndesc, n)
        buckets.setdefault(key, []).append((prefix, hit, probs))
        if t == n - 1:
            return
        for c, pc in probs.items():
            if pc <= 0.0:
                continue
            child = post.copy()
            child.observe(c)
            nd = ndesc + (1 if (last and c < last) else 0)
            descend(child, prefix + (c,), dir_up if t == 0 else (c > last), nd)

    descend(ShelfPosterior(m, list(range(1, n + 1))), (), True, 0)
    worst_key, worst_rng = None, 0.0
    for key, members in buckets.items():
        if len(members) < 2:
            continue
        rng = max(h for _, h, _ in members) - min(h for _, h, _ in members)
        if rng > worst_rng:
            worst_key, worst_rng = key, rng
    if worst_key is None or worst_rng < 1e-9:
        print(f"  ({label}: no collision at n={n}, m={m} — SUFFICIENT here)")
        return
    print(f"  worst {label} collision at n={n}, m={m}: key={worst_key}"
          f"  → Δhit={worst_rng:.4f}")
    for prefix, hit, probs in sorted(buckets[worst_key]):
        law = "  ".join(f"{c}:{probs[c]:.3f}" for c in sorted(probs))
        print(f"    prefix {prefix}  runs={run_lengths(prefix)}  "
              f"hit={hit:.4f}   P(next)= {law}")


def _key_set_last_dir(prefix, R, last, dir_up, ndesc, n):
    return (frozenset(R), last, dir_up)


def _key_dir_rank_desc(prefix, R, last, dir_up, ndesc, n):
    return (len(prefix), dir_up, bisect_left(R, last), ndesc)


def posterior_sufficiency(n, m):
    """Stronger than hit-sufficiency: is the ENTIRE next-card posterior — indexed
    by the next card's RANK among the remaining — a function of the state
    (direction, rank-of-last, run composition)? If yes, the state's TRANSITION is
    closed (the run composition either extends the last run or opens a new one),
    so the O(2ⁿ) exact DP over this state is VALID. Reports the max component
    deviation within a state (0 ⇒ closed) and the state count."""
    ref: dict = {}
    maxdev = 0.0

    def descend(post, prefix, dir_up):
        nonlocal maxdev
        probs = post.next_probs()
        R = sorted(probs)
        vec = tuple(probs[c] for c in R)  # posterior by remaining-rank
        t = len(prefix)
        last = prefix[-1] if prefix else 0
        key = (dir_up, bisect_left(R, last), run_lengths(prefix))
        seen = ref.get(key)
        if seen is None:
            ref[key] = vec
        else:
            dev = max(abs(a - b) for a, b in zip(seen, vec))
            if dev > maxdev:
                maxdev = dev
        if t == n - 1:
            return
        for c, pc in probs.items():
            if pc > 0.0:
                child = post.copy()
                child.observe(c)
                descend(child, prefix + (c,), dir_up if t == 0 else (c > last))

    descend(ShelfPosterior(m, list(range(1, n + 1))), (), True)
    return maxdev, len(ref)


def group_stats(agg_map, tot):
    """(#groups, max within-group hit range, mass-weighted R²) for one σ."""
    resid = 0.0
    max_range = 0.0
    for a in agg_map.values():
        if a.mass > 0.0:
            resid += a.mh2 - a.mh * a.mh / a.mass
        rng = a.hi - a.lo
        if rng > max_range:
            max_range = rng
    total_var = tot["mh2"] - tot["mh"] * tot["mh"] / tot["mass"]
    r2 = 1.0 if total_var <= 1e-18 else 1.0 - resid / total_var
    return len(agg_map), max_range, r2


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    m_list = (
        [int(x) for x in sys.argv[2].split(",")]
        if len(sys.argv) > 2 else [1, 2, 3, 5]
    )
    n_list = list(range(4, n_max + 1))

    # growth[(name, m)] = {n: #groups}  -- for the polynomial-vs-exponential read
    growth = {}

    for m in m_list:
        print(f"\n{'='*74}\n m = {m} shelves\n{'='*74}")
        for n in n_list:
            aggs, tot = probe(n, m)
            # gate: the trie-max reconstruction must equal the exact rational
            if n <= 7:
                e_exact = float(exact_e(n, m)[0])
                err = abs(tot["e_opt"] - e_exact)
                gate = f"E_opt={tot['e_opt']:.6f} vs exact {e_exact:.6f} (Δ{err:.1e})"
                assert err < 1e-7, gate
            else:
                gate = f"E_opt={tot['e_opt']:.6f}"
            print(f"\n  n={n}  [{gate}]")
            print(f"    {'statistic':<16}{'#groups':>9}{'max Δhit':>12}"
                  f"{'weighted R²':>14}   verdict")
            for name in STAT_NAMES:
                ng, mr, r2 = group_stats(aggs[name], tot)
                growth.setdefault((name, m), {})[n] = ng
                verdict = "SUFFICIENT" if mr < 1e-9 else ""
                print(f"    {name:<16}{ng:>9}{mr:>12.2e}{r2:>14.6f}   {verdict}")

    # concrete order-dependence witnesses (why no set-level statistic works)
    print(f"\n{'='*74}\n order-dependence witnesses  (same set+last+dir, "
          f"different optimal hit)\n{'='*74}")
    wn = min(n_max, 6)
    for m in m_list:
        witness(wn, m, _key_set_last_dir, "set+last+dir")
        witness(wn, m, _key_dir_rank_desc, "dir+rank+#desc")

    # full-posterior sufficiency of the run-composition state (⇒ exact DP valid)
    print(f"\n{'='*74}\n full-posterior sufficiency of (dir, rank, run-comp)"
          f"   max Δposterior per state  (0 ⇒ transition closed ⇒ O(2ⁿ) DP exact)"
          f"\n{'='*74}")
    for m in m_list:
        cells = []
        for n in n_list:
            dev, nstates = posterior_sufficiency(n, m)
            cells.append(f"n{n}:{dev:.1e}({nstates})")
        print(f"  m={m:<2d} " + "  ".join(cells))

    # state-space growth of the interesting statistics
    print(f"\n{'='*74}\n state-space growth  #groups(n)  (polynomial ⇒ DP buildable)"
          f"\n{'='*74}")
    for m in m_list:
        print(f"\n  m={m}")
        for name in ("dir_rank", "dir_rank_desc", "dir_rank_runcomp",
                     "set_last_dir"):
            row = growth.get((name, m), {})
            cells = "  ".join(f"n{n}:{row.get(n, '-'):>6}" for n in n_list)
            print(f"    {name:<16} {cells}")


if __name__ == "__main__":
    main()
