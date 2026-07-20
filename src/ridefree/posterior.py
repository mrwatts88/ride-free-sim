"""Exact next-card posterior for a shelf shuffle of a KNOWN stack (M12b rung 1).

The observer premise of Track A: you watched shoe k being dealt, so you know
the exact pre-shuffle order (`stack`); the house applies a physical shuffle;
cards are then dealt face up one at a time. What is the exact conditional
distribution of the next card, given everything dealt so far?

For the DFH shelf machine this is EXACTLY computable, because the shelf
shuffle is a *label sort* (DFH Description 1): every card independently
draws one of 2m lanes (shelf x top/bottom, i.i.d. uniform), and the output
order is a deterministic function of the draws — sort by (shelf, side,
+position for top lanes / -position for bottom lanes). Equivalently, each
card occupies one of 2m possible SLOTS in a fixed global order, chosen
uniformly and independently. Observing the dealt prefix is observing "the t
smallest realized slots belong to these cards, in this order", and the
next-card law follows by exact filtering over the slot axis:

    h_t(s)  = P(prefix chain with the t-th card's slot at s)   [recursive:
              h_{t+1}(s) proportional to H_t(s-1) on the observed card's slots]
    P(next = c | prefix) proportional to
        sum over c's slots s' of H_t(s'-1) * prod_{d remaining, d != c} F_d(s')

where F_d(s) = P(card d's slot > s) and H_t is the running sum of h_t. All
factors are per-card independent, so the product is a sweep with per-slot
updates — O(slots + remaining x lanes) per dealt card, exact to float
precision (brute-force enumeration gate in tests/test_posterior.py).

Multi-pass shelves need no new machinery: DFH Corollary 4.2 says an m1-pass
then an m2-pass IS a 2*m1*m2-shelf single pass (E26 gate-confirmed), so the
posterior for the manufacturer's two-pass fix is `ShelfPosterior(shelves=200)`
run against two-pass output.

Scope honesty (rung 1): `stack` entries must be distinct (one physical deck
of raw cards — the observer can identify each dealt card). Multi-deck shoes
repeat physical cards and need copy-marginalization in the observation
model — a rung-2 extension. The forward GSR riffle is NOT a label sort (its
inverse is); its exact posterior is a separate (easy, cut-conditioned)
construction, deferred until a riffle target needs pricing.

`PosteriorGuesser` adapts the posterior to the `forensics` guesser protocol
(guess/observe), so `guessing_experiment` scores it directly against DFH's
conjectured-optimal strategy — the posterior argmax is by construction the
true optimal feedback guesser, so it must score >= ShelfGuesser; the paired
delta measures how much (if anything) the published conjecture leaves on the
table.
"""

import math
from bisect import bisect_left


class ShelfPosterior:
    """Exact filtering posterior over the next dealt card, for one pass of an
    m-shelf machine applied to a known stack of distinct cards."""

    def __init__(self, shelves: int, stack) -> None:
        stack = list(stack)
        if len(set(stack)) != len(stack):
            raise ValueError("stack entries must be distinct (rung-1 scope)")
        if shelves < 1:
            raise ValueError("shelves must be >= 1")
        self.stack = stack
        self.shelves = shelves
        n = self.n = len(stack)
        lanes = self.lanes = 2 * shelves
        self.nslots = lanes * n
        self._index = {card: i for i, card in enumerate(stack)}
        # Slot of (card at position i+1, lane): shelf j = lane >> 1; top lanes
        # (even) sort ascending by position, bottom lanes descending — the
        # global output order of ShelfShuffle, matched by test gates.
        slots = []
        owner = [-1] * self.nslots
        for i in range(n):
            pos = i + 1
            row = []
            for lane in range(lanes):
                j = lane >> 1
                s = j * 2 * n + (pos - 1 if lane % 2 == 0 else 2 * n - pos)
                row.append(s)
            row.sort()
            slots.append(row)
            for s in row:
                owner[s] = i
        self._slots = slots
        self._owner = owner
        self._logk = [0.0] + [math.log(k / lanes) for k in range(1, lanes + 1)]
        self._remaining = [True] * n
        self._n_remaining = n
        # The prefix-chain term h_t: support (sorted slots of the last observed
        # card) and cumulative sums; None means t = 0 (H_0 == 1 everywhere).
        self._h_slots: list[int] | None = None
        self._h_cum: list[float] | None = None

    # -- internals ----------------------------------------------------------

    def _h_before(self, s: int) -> float:
        """H_t(s-1): total chain weight with the last observed slot < s."""
        if self._h_slots is None:
            return 1.0
        i = bisect_left(self._h_slots, s)
        return self._h_cum[i]

    def _sweep_q(self):
        """Per-slot remaining-cards product: after the sweep, logq[s] is
        sum of log F_d(s) over remaining d with F_d(s) > 0, and zeros[s]
        counts remaining d with F_d(s) == 0."""
        lanes = self.lanes
        logk = self._logk
        remaining = self._remaining
        owner = self._owner
        count = [lanes] * self.n
        cur_log, cur_zeros = 0.0, 0
        logq = [0.0] * self.nslots
        zeros = [0] * self.nslots
        for s in range(self.nslots):
            d = owner[s]
            if remaining[d]:
                k = count[d]
                count[d] = k - 1
                cur_log -= logk[k]
                if k == 1:
                    cur_zeros += 1
                else:
                    cur_log += logk[k - 1]
            logq[s] = cur_log
            zeros[s] = cur_zeros
        return logq, zeros

    # -- public API ---------------------------------------------------------

    def next_probs(self) -> dict:
        """P(next dealt card = c | everything observed), for all remaining c."""
        if self._n_remaining == 0:
            raise ValueError("shoe exhausted")
        lanes = self.lanes
        logk = self._logk
        logq, zeros = self._sweep_q()
        weights = {}
        total = 0.0
        for i in range(self.n):
            if not self._remaining[i]:
                continue
            acc = 0.0
            for r, s in enumerate(self._slots[i]):
                h = self._h_before(s)
                if h == 0.0:
                    continue
                kc = lanes - r - 1  # F_c at its own r-th slot: (lanes-r-1)/lanes
                if zeros[s] - (1 if kc == 0 else 0) > 0:
                    continue
                acc += h * math.exp(logq[s] - logk[kc])
            weights[self.stack[i]] = acc
            total += acc
        if total <= 0.0:
            raise ValueError("observed prefix impossible under this model")
        return {card: w / total for card, w in weights.items()}

    def observe(self, card) -> None:
        """Condition on `card` having been dealt next."""
        i = self._index[card]
        if not self._remaining[i]:
            raise ValueError(f"card {card!r} was already dealt")
        h_slots = self._slots[i]
        h_vals = [self._h_before(s) for s in h_slots]
        total = math.fsum(h_vals)
        if total <= 0.0:
            raise ValueError("observed prefix impossible under this model")
        cum = [0.0]
        acc = 0.0
        for v in h_vals:
            acc += v / total  # normalize: only conditionals are ever used
            cum.append(acc)
        self._h_slots = h_slots
        self._h_cum = cum
        self._remaining[i] = False
        self._n_remaining -= 1

    def copy(self) -> "ShelfPosterior":
        """A clone sharing immutable precompute, with independent conditioning
        state (for particle-filter resampling)."""
        twin = object.__new__(ShelfPosterior)
        twin.stack = self.stack
        twin.shelves = self.shelves
        twin.n = self.n
        twin.lanes = self.lanes
        twin.nslots = self.nslots
        twin._index = self._index
        twin._slots = self._slots
        twin._owner = self._owner
        twin._logk = self._logk
        twin._remaining = list(self._remaining)
        twin._n_remaining = self._n_remaining
        twin._h_slots = self._h_slots  # replaced wholesale on observe; safe to share
        twin._h_cum = self._h_cum
        return twin


class MultiDeckShelfPosterior:
    """Next-VALUE posterior for a shelf pass of a multi-deck shoe, where the
    observer knows the pre-shuffle order but CANNOT distinguish copies of the
    same physical card (M12b rung 2).

    Rung 1's `ShelfPosterior` is exact because each distinct card, once dealt,
    pins one input position. With repeated cards the observer sees only the
    value; the copy that produced it is latent, and the exact next-value law
    is a permanent-like sum over copy assignments (intractable at shoe scale).
    This is a sequential-importance particle filter over that latent history:
    each particle is a `ShelfPosterior` over the DISTINCT input positions
    carrying one hypothesis of which copy produced each observed value. The
    proposal is locally optimal — on observing value v, a particle samples the
    next position from its own exact conditional restricted to positions of
    value v, and its incremental weight is exactly that value's marginal
    probability — so the filter is unbiased and converges to the exact law as
    particles -> infinity (gated against brute force in tests). `values` maps
    each input position (top of deck first) to its observed value (rank+suit,
    or blackjack value, or baccarat value — the caller's equivalence class;
    copies = equal values).
    """

    def __init__(self, shelves: int, values, particles: int = 200, seed: int = 0):
        import random

        self.values = list(values)
        self.n = len(self.values)
        self.particles = particles
        self._rng = random.Random(seed)
        positions = list(range(self.n))
        base = ShelfPosterior(shelves, positions)
        self._value_of = {i: self.values[i] for i in positions}
        # particle = [posterior, log_weight]; all start identical.
        self._parts = [[base if k == 0 else base.copy(), 0.0] for k in range(particles)]
        self._cache = None  # per-particle (val_probs, pos_probs), shared by
        #                     next_value_probs and the immediately following observe

    def _particle_cache(self):
        if self._cache is None:
            cache = []
            for post, _ in self._parts:
                pos_probs = post.next_probs()
                val_probs: dict = {}
                for i, p in pos_probs.items():
                    v = self._value_of[i]
                    val_probs[v] = val_probs.get(v, 0.0) + p
                cache.append((val_probs, pos_probs))
            self._cache = cache
        return self._cache

    def _weights(self):
        m = max(lw for _, lw in self._parts)
        ws = [math.exp(lw - m) for _, lw in self._parts]
        total = math.fsum(ws)
        return [w / total for w in ws], m

    def next_value_probs(self) -> dict:
        """Filter estimate of P(next dealt value = v | everything observed)."""
        ws, _ = self._weights()
        cache = self._particle_cache()
        out: dict = {}
        for (vp, _), w in zip(cache, ws):
            if w == 0.0:
                continue
            for v, p in vp.items():
                out[v] = out.get(v, 0.0) + w * p
        s = math.fsum(out.values())
        return {v: p / s for v, p in out.items()} if s > 0 else out

    def prob_value(self, value) -> float:
        return self.next_value_probs().get(value, 0.0)

    def observe(self, value) -> None:
        """Condition on `value` having been dealt next; advance every particle
        by sampling which same-value copy it was, and resample if degenerate."""
        cache = self._particle_cache()
        for part, (vp, pos_probs) in zip(self._parts, cache):
            post = part[0]
            q = vp.get(value, 0.0)
            if q <= 0.0:
                part[1] = -math.inf  # this history can't produce the value
                continue
            candidates = [(i, p) for i, p in pos_probs.items()
                          if self._value_of[i] == value]
            r = self._rng.random() * q
            chosen = candidates[-1][0]
            acc = 0.0
            for i, p in candidates:
                acc += p
                if r <= acc:
                    chosen = i
                    break
            post.observe(chosen)
            part[1] += math.log(q)
        self._cache = None
        self._maybe_resample()

    def _maybe_resample(self) -> None:
        ws, _ = self._weights()
        ess = 1.0 / math.fsum(w * w for w in ws)
        if not math.isfinite(ess) or ess >= self.particles / 2:
            return
        # systematic resampling
        n = self.particles
        step = 1.0 / n
        u = self._rng.random() * step
        cum = 0.0
        j = 0
        picked = []
        for k, w in enumerate(ws):
            cum += w
            while u <= cum and len(picked) < n:
                picked.append(k)
                u += step
        seen: set = set()
        new_parts = []
        for k in picked:
            post = self._parts[k][0]
            if k in seen:
                post = post.copy()
            else:
                seen.add(k)
            new_parts.append([post, 0.0])
        self._parts = new_parts


class AssumedDensityShelfPosterior:
    """O(slots)-per-step next-VALUE posterior for a shelf pass of a multi-deck
    shoe — the assumed-density companion to `MultiDeckShelfPosterior` (M12b
    rung 3), built because the particle filter's O(particles x slots) cost is
    the throughput wall in front of any 8-deck number.

    The state is the exact filter's sufficient statistic, softened where copy
    ambiguity makes it uncertain:

      - `alive[i]`  — P(input position i not yet dealt | observations), a
        fractional occupancy (rung 1's boolean `remaining`, made soft);
      - a chain law over the LAST DEALT SLOT (rung 1's h_t/H_t), now a
        mixture over which same-value copy each observation was.

    Remaining positions keep their ORIGINAL uniform slot laws exactly as in
    rung 1 — all truncation flows through the chain — so with distinct values
    the update is rung 1's update verbatim: alive stays 0/1, the chain has a
    single candidate, and this filter IS `ShelfPosterior`, deterministically
    (gated to 1e-9). With copies, the single (alive, chain) pair is the
    projection of the exact mixture over copy-assignment histories onto a
    product family — an assumed-density approximation whose BIAS is measured,
    not assumed (brute-force gap gate; E17 predicted-vs-realized on the
    adapters). Unlike the particle filter it is deterministic — no filter
    RNG, so identical observations always give identical prices — and
    `copy()` is O(positions), which is what makes the coup adapter's
    clone-heavy sampling affordable.

    Per step: P(next dealt is position i at slot s) is scored as
        alive[i] * G(s-1) * prod_{j != i} f_j(s),
    f_j(s) = 1 - alive[j] * (1 - F_j(s)) — position j either was already
    dealt (weight 1 - alive) or survives past s (original survival F_j) —
    computed in one soft sweep of the global slot axis (the rung-1 sweep
    with fractional occupancy). Observing value v soft-assigns the deal
    across v's alive copies (responsibilities), decrements their occupancy
    (total mass n - t is conserved exactly), and the responsibility-weighted
    slot law becomes the next chain."""

    STRAND_TOL = 0.5  # alive mass a frontier may strand before it's overshoot
    # Contamination floor: with probability MIX the projected state is wrong
    # and the honest fallback is the filter's own exact occupancy bookkeeping
    # (the composition). Applied to the OUTPUT law only, and only when copies
    # exist (distinct stacks are exact — no contamination to model). Cure for
    # a measured disease: at 3 decks, 6 of 40 probe shoes drifted into
    # near-certain wrong claims late-shoe (p ~ 1e-72 on a 5% card, one step
    # = -234 bits), flipping the whole-shoe log-loss negative; the floor
    # bounds any step at log2(MIX) while costing healthy shoes ~0.03
    # bits/step. Internal state updates stay pure-model; `surprises` still
    # reports drift honestly. The right value grows with copy count (drift
    # is copy-ambiguity's child): 0.02 calibrates at 2-3 decks, 8 decks
    # needs ~0.25 — fit per configuration on probe seeds, certify on fresh
    # ones (E29), and pass via `mix`.
    MIX = 0.02

    def __init__(self, shelves: int, values, mix: float | None = None) -> None:
        self.mix = self.MIX if mix is None else mix
        self.values = list(values)
        n = self.n = len(self.values)
        base = ShelfPosterior(shelves, list(range(n)))  # slot geometry only
        self.shelves = shelves
        self.lanes = base.lanes
        self.nslots = base.nslots
        self._slots = base._slots
        self._owner = base._owner
        self._alive = [1.0] * n
        self._dealt = 0
        self._class_positions: dict = {}
        for i, v in enumerate(self.values):
            self._class_positions.setdefault(v, []).append(i)
        self.surprises = 0  # observations the projected state couldn't place
        # Copy-class positions never get a HARD survival wall: under soft
        # assignment "this copy is certainly alive" is itself an estimate, so
        # its zero-survival region would poison the whole axis on drift (a
        # stale copy the in-class repair couldn't move walls off every legal
        # slot — measured on the 3-deck E28 probe). The hedge caps their
        # occupancy inside survival factors at 1 - 1e-9; distinct classes
        # keep exact hard walls (their identity is pinned by observation),
        # which is what preserves the exact rung-1 reduction.
        self._max_occ = [
            1.0 - 1e-9 if len(self._class_positions[v]) > 1 else 1.0
            for v in self.values
        ]
        # Positions ordered by their last (largest) slot: the chain-vs-
        # occupancy consistency walk in observe() uses this to price how
        # much alive mass a candidate frontier would strand behind it.
        self._by_last = sorted(range(n), key=lambda i: self._slots[i][-1])
        self._last_sorted = [self._slots[i][-1] for i in self._by_last]
        self._has_copies = any(
            len(ps) > 1 for ps in self._class_positions.values()
        )
        # Chain over the last dealt slot: support + cumulative (None = step 0,
        # G == 1 everywhere). Replaced wholesale on observe; safe to share.
        self._g_slots: list[int] | None = None
        self._g_cum: list[float] | None = None
        self._cache = None  # (gbefore, lognz, zeros) sweep arrays, per step
        self._table = None  # (score rows, shift), per step

    def _g_before(self, s: int) -> float:
        if self._g_slots is None:
            return 1.0
        i = bisect_left(self._g_slots, s)
        return self._g_cum[i]

    def _sweep(self):
        """One pass of the slot axis: gbefore[s] = G(s-1); lognz[s] = sum of
        log f_j(s) over positions with f_j(s) > 0; zeros[s] = count of
        positions with f_j(s) == 0 (only possible at alive == 1)."""
        if self._cache is not None:
            return self._cache
        lanes = self.lanes
        alive = self._alive
        owner = self._owner
        max_occ = self._max_occ
        g_slots, g_cum = self._g_slots, self._g_cum
        passed = [0] * self.n  # of position's slots at or below the sweep point
        cur_log, cur_zeros = 0.0, 0
        gbefore = [0.0] * self.nslots
        lognz = [0.0] * self.nslots
        zeros = [0] * self.nslots
        gi = 0
        gcur = 1.0 if g_slots is None else 0.0
        for s in range(self.nslots):
            if g_slots is not None:
                while gi < len(g_slots) and g_slots[gi] < s:
                    gi += 1
                gcur = g_cum[gi]
            gbefore[s] = gcur
            d = owner[s]
            a = alive[d]
            if a > 0.0:
                if a > max_occ[d]:
                    a = max_occ[d]
                r = passed[d] = passed[d] + 1
                old = 1.0 - a * (r - 1) / lanes
                new = 1.0 - a * r / lanes
                cur_log -= math.log(old)  # old > 0 always (r-1 < lanes)
                if new <= 0.0:
                    cur_zeros += 1
                else:
                    cur_log += math.log(new)
            lognz[s] = cur_log
            zeros[s] = cur_zeros
        self._cache = (gbefore, lognz, zeros)
        return self._cache

    def _log_score_row(self, i: int, sweep) -> list[float]:
        """Log of unnormalized P(position i is dealt next at its r-th slot);
        -inf marks impossible slots. Log space: at shoe scale the survival
        product underflows exp() long before the law itself degenerates."""
        gbefore, lognz, zeros = sweep
        a = self._alive[i]
        log_a = math.log(a)
        a_eff = min(a, self._max_occ[i])  # mirror the sweep's hedged factor
        lanes = self.lanes
        row = []
        for r, s in enumerate(self._slots[i], start=1):
            g = gbefore[s]
            if g == 0.0:
                row.append(-math.inf)
                continue
            f_own = 1.0 - a_eff * r / lanes
            if f_own <= 0.0:
                if zeros[s] - 1 > 0:
                    row.append(-math.inf)
                    continue
                row.append(log_a + math.log(g) + lognz[s])
            else:
                if zeros[s] > 0:
                    row.append(-math.inf)
                    continue
                row.append(log_a + math.log(g) + lognz[s] - math.log(f_own))
        return row

    def _score_table(self, sweep):
        """(rows, shift): per-alive-position exp(log_row - shift) score rows,
        max-shifted so the largest entry is 1.0 — safe at any shoe size.
        Cached per step: next_value_probs and the following observe share it."""
        if self._table is not None:
            return self._table
        log_rows = {}
        shift = -math.inf
        for i in range(self.n):
            if self._alive[i] <= 0.0:
                continue
            row = self._log_score_row(i, sweep)
            m = max(row)
            if m > shift:
                shift = m
            log_rows[i] = row
        if shift == -math.inf:
            if self._g_slots is not None:
                # Chain overshoot: the mixed deferred chain drifted past every
                # remaining position's last slot (the exact chain cannot; the
                # projection's can, late in the shoe). The frontier estimate
                # is provably lost — reset it to uninformative, keep the
                # occupancy state (still exact per class), and re-form.
                self.surprises += 1
                self._g_slots = None
                self._g_cum = None
                self._cache = None
                return self._score_table(self._sweep())
            raise ValueError("observed prefix impossible under this model")
        rows = {
            i: [math.exp(x - shift) if x > -math.inf else 0.0 for x in row]
            for i, row in log_rows.items()
        }
        self._table = (rows, shift)
        return self._table

    def next_value_probs(self) -> dict:
        """Assumed-density estimate of P(next dealt value = v | observed)."""
        if self._dealt >= self.n:
            raise ValueError("shoe exhausted")
        rows, _ = self._score_table(self._sweep())
        out: dict = {}
        for i, row in rows.items():
            w = math.fsum(row)
            if w > 0.0:
                v = self.values[i]
                out[v] = out.get(v, 0.0) + w
        total = math.fsum(out.values())
        if total <= 0.0:
            raise ValueError("observed prefix impossible under this model")
        probs = {v: w / total for v, w in out.items()}
        if not self._has_copies or self._dealt == 0:
            return probs  # exact regimes: no drift for the floor to model
        occ: dict = {}
        occ_total = 0.0
        for v, positions in self._class_positions.items():
            m = math.fsum(self._alive[i] for i in positions)
            if m > 0.0:
                occ[v] = m
                occ_total += m
        mix = self.mix
        return {
            v: (1.0 - mix) * probs.get(v, 0.0) + mix * occ[v] / occ_total
            for v in occ
        }

    def prob_value(self, value) -> float:
        return self.next_value_probs().get(value, 0.0)

    def observe(self, value) -> None:
        """Condition on `value` dealt next: soft-assign the deal over its
        alive copies, decrement their occupancy, rebuild the chain.

        Which copy was dealt is judged with FULL information (score rows,
        survival products included), but two structural rules override the
        raw responsibilities. (1) OCCUPANCY IS CAPPED: the deal removes
        exactly one unit of occupancy from the observed value class (per
        class, sum(alive) == copies - dealt is EXACT bookkeeping, not mean
        field), so the subtraction is the water-filling projection of the
        responsibilities onto {0 <= d_i <= alive_i, sum d_i = 1} — without
        the cap, a copy whose evidence outruns its occupancy under-subtracts
        and the leaked mass eventually walls off the slot axis (measured:
        the 3-deck E28 probe crashes without this). (2) The stored chain is
        the DEFERRED weight — G(s-1) on the dealt copy's row, per-candidate
        normalized, mixed by the projected shares — exactly as rung 1 defers
        survival factors to query time; baking survivals into the chain
        would double-count them at the next query (and break the rung-1
        reduction)."""
        sweep = self._sweep()
        gbefore = sweep[0]
        all_rows, _ = self._score_table(sweep)
        cands = [i for i in self._class_positions.get(value, ())
                 if self._alive[i] > 0.0]
        if not cands:
            raise ValueError("observed prefix impossible under this model")
        weights = {i: math.fsum(all_rows[i]) if i in all_rows else 0.0
                   for i in cands}
        if math.fsum(weights.values()) <= 0.0:
            # The projected state says this value can't be next, yet here it
            # is: fall back to occupancy-proportional shares. Counted, and
            # priced by the E17 predicted-vs-realized gate like every other
            # projection error.
            self.surprises += 1
            weights = {i: self._alive[i] for i in cands}
        shares = self._water_fill(weights)
        support: dict[int, float] = {}
        for i, share in shares.items():
            if share <= 0.0:
                continue
            a = self._alive[i] - share
            self._alive[i] = a if a > 1e-15 else 0.0
            drow = [gbefore[s] for s in self._slots[i]]
            dsum = math.fsum(drow)
            if dsum <= 0.0:
                continue  # no deferred mass to place (fallback path only)
            for s, w in zip(self._slots[i], drow):
                if w > 0.0:
                    support[s] = support.get(s, 0.0) + share * w / dsum
        if support:
            g_slots = sorted(support)
            # Chain defers to occupancy: per-class occupancy totals are exact
            # bookkeeping while the chain is wholly a projection, so a
            # frontier that would strand more than STRAND_TOL of alive mass
            # below itself (positions whose every slot it has passed, still
            # carried as alive) is evidence of chain overshoot, not of those
            # copies being dealt. Truncate the support there; the certain-
            # dealt repair below then only cleans genuine residue. Without
            # this the mixed chain ratchets high slot by slot and, near the
            # shoe's end, strands the whole remaining stack (measured on the
            # 3-deck E28 probe: 3.25 chain resets/shoe, bits −23; with it the
            # resets vanish at probe scale).
            keep = len(g_slots)
            bi = 0
            stranded = 0.0
            for k, s in enumerate(g_slots):
                while bi < self.n and self._last_sorted[bi] < s:
                    stranded += self._alive[self._by_last[bi]]
                    bi += 1
                if stranded > self.STRAND_TOL:
                    keep = k
                    break
            if keep == 0:
                keep = 1  # below even the lowest slot: occupancy repair's job
            g_slots = g_slots[:keep]
            cum = [0.0]
            acc = 0.0
            for s in g_slots:
                acc += support[s]
                cum.append(acc)
            self._g_slots = g_slots
            self._g_cum = cum
        else:
            self.surprises += 1  # chain unchanged: nowhere legal to put it
        self._dealt += 1
        self._cache = None
        self._table = None
        self._repair_certain_dealt()

    def _water_fill(self, weights: dict) -> dict:
        """Project responsibility weights onto the feasible subtractions
        {0 <= d_i <= alive_i, sum d_i = 1}: proportional to weight among the
        uncapped, capped copies pay their whole occupancy. If the class
        cannot absorb a full unit (drifted state), whatever fits is taken."""
        shares = {i: 0.0 for i in weights}
        active = [i for i in weights if self._alive[i] > 0.0]
        remaining = 1.0
        while active and remaining > 1e-15:
            wtot = math.fsum(weights[i] for i in active)
            if wtot <= 0.0:
                # degenerate round: spread by occupancy headroom instead
                weights = {i: self._alive[i] - shares[i] for i in active}
                wtot = math.fsum(weights.values())
                if wtot <= 0.0:
                    self.surprises += 1
                    break
            capped = []
            for i in active:
                want = shares[i] + weights[i] / wtot * remaining
                if want >= self._alive[i]:
                    capped.append(i)
            if not capped:
                for i in active:
                    shares[i] += weights[i] / wtot * remaining
                remaining = 0.0
                break
            for i in capped:
                remaining -= self._alive[i] - shares[i]
                shares[i] = self._alive[i]
                active.remove(i)
        if remaining > 1e-12 and not active:
            self.surprises += 1  # class under-full: drift got here first
        return shares

    def _repair_certain_dealt(self) -> None:
        """Occupancy repair: a position whose whole slot row lies below the
        chain frontier's minimum CANNOT still be alive (its card was dealt as
        some earlier same-value observation, whatever the responsibilities
        said then). Zero it and return the occupancy to the other alive
        copies of its value — in-class only, so per-class bookkeeping stays
        exact; if the class has no headroom behind the frontier, the residue
        stays put (soft factors never hard-wall the axis, and the observe
        fallback settles the score when the value arrives)."""
        if not self._g_slots:
            return
        frontier = self._g_slots[0]
        by_value: dict = {}
        for i in range(self.n):
            if self._alive[i] > 0.0 and self._slots[i][-1] < frontier:
                by_value.setdefault(self.values[i], []).append(i)
        for v, stale in by_value.items():
            targets = [(j, 1.0 - self._alive[j])
                       for j in self._class_positions[v]
                       if self._alive[j] < 1.0 and self._slots[j][-1] >= frontier]
            room = math.fsum(h for _, h in targets)
            if room <= 0.0:
                continue
            mass = math.fsum(self._alive[i] for i in stale)
            take = min(mass, room)
            scale_out = take / mass
            for i in stale:
                self._alive[i] -= scale_out * self._alive[i]
                if self._alive[i] <= 1e-15:
                    self._alive[i] = 0.0
            scale_in = take / room
            for j, h in targets:
                self._alive[j] += scale_in * h

    def copy(self) -> "AssumedDensityShelfPosterior":
        """A clone sharing immutable precompute — O(positions), which is what
        the coup adapter's sampling leans on."""
        twin = object.__new__(AssumedDensityShelfPosterior)
        twin.values = self.values
        twin.mix = self.mix
        twin.n = self.n
        twin.shelves = self.shelves
        twin.lanes = self.lanes
        twin.nslots = self.nslots
        twin._slots = self._slots
        twin._owner = self._owner
        twin._class_positions = self._class_positions
        twin._max_occ = self._max_occ
        twin._by_last = self._by_last
        twin._last_sorted = self._last_sorted
        twin._has_copies = self._has_copies
        twin._alive = list(self._alive)
        twin._dealt = self._dealt
        twin.surprises = self.surprises
        twin._g_slots = self._g_slots  # replaced wholesale on observe
        twin._g_cum = self._g_cum
        twin._cache = self._cache  # invalidated on observe; safe to share
        twin._table = self._table
        return twin


class PropositionResult:
    """Per-deck ledger of the composition-fair value proposition."""

    def __init__(self, trials, bets, predicted, realized, deck_deltas) -> None:
        self.trials = trials
        self.bets = bets
        self.predicted = predicted  # sum of (p - q)/q over staked steps
        self.realized = realized  # realized profit, 1 unit per staked step
        self.deck_deltas = deck_deltas  # per-deck (realized - predicted)

    @property
    def z(self) -> float:
        """Realized vs predicted, on per-deck paired deltas (steps within a
        deck are correlated; decks are independent)."""
        d = self.deck_deltas
        n = len(d)
        mean = sum(d) / n
        var = sum((x - mean) ** 2 for x in d) / (n - 1)
        if var == 0.0:
            return 0.0
        return mean * math.sqrt(n / var)

    @property
    def edge_per_bet(self) -> float:
        return self.realized / self.bets if self.bets else 0.0


def proposition_experiment(
    shelves: int,
    trials: int,
    seed: int,
    threshold: float = 0.02,
    target_value: int = 10,
    passes: int = 1,
):
    """The first payoff adapter (M12b rung 1): a composition-fair proposition.

    Each step, the house offers a bet on "next card's blackjack value ==
    target_value" at odds fair against the REMAINING COMPOSITION — so a
    perfect card counter has exactly zero edge on every offer, by
    construction. The observer, who watched shoe k (knows the pre-shuffle
    stack) and models the machine, stakes 1 unit whenever posterior minus
    composition clears `threshold`. Any profit is pure ORDER structure —
    the paradigm-2 quantity, isolated from everything paradigm 1 could see.

    Per trial: a fresh uniformly-shuffled known 52-card stack, shelf-shuffled
    with `passes` passes of `shelves` shelves; the posterior models the
    Cor 4.2 equivalent single pass. Gate: `z` (realized vs the posterior's
    own predicted edge, per-deck paired) — the E17 ramp pattern.
    """
    import random

    from ridefree.cards import RAW_RANKS, SUITS, value
    from ridefree.shuffle import ShelfShuffle

    eq_shelves = shelves
    for _ in range(passes - 1):
        eq_shelves = 2 * eq_shelves * shelves  # DFH Corollary 4.2
    model = ShelfShuffle(shelves=shelves, passes=passes)
    rng = random.Random(seed)
    deck = [(rank, suit) for suit in SUITS for rank in RAW_RANKS]
    bets = 0
    predicted = 0.0
    realized = 0.0
    deck_deltas = []
    for _ in range(trials):
        stack = list(deck)
        rng.shuffle(stack)  # shoe k: known to the observer
        dealt = model.permute(stack, rng)
        posterior = ShelfPosterior(eq_shelves, stack)
        remaining = len(stack)
        target_left = sum(1 for c in stack if value(c) == target_value)
        deck_pred = 0.0
        deck_real = 0.0
        for card in dealt:
            if 0 < target_left < remaining:
                q = target_left / remaining
                probs = posterior.next_probs()
                p = sum(
                    pr for c, pr in probs.items() if value(c) == target_value
                )
                if p - q > threshold:
                    bets += 1
                    deck_pred += (p - q) / q
                    if value(card) == target_value:
                        deck_real += (1 - q) / q
                    else:
                        deck_real -= 1.0
            posterior.observe(card)
            remaining -= 1
            if value(card) == target_value:
                target_left -= 1
        predicted += deck_pred
        realized += deck_real
        deck_deltas.append(deck_real - deck_pred)
    return PropositionResult(trials, bets, predicted, realized, deck_deltas)


def multideck_proposition_experiment(
    decks: int,
    shelves: int,
    trials: int,
    seed: int,
    *,
    passes: int = 1,
    particles: int = 200,
    target_value: int = 8,
    threshold: float = 0.02,
    method: str = "pf",
    adf_mix: float | None = None,
    observer: str = "class",
):
    """The composition-fair value proposition at multi-deck scale (M12b rung 2).

    Honest observation model: the observer knows shoe k's order at rank+suit
    resolution but cannot tell the `decks` copies of a rank+suit apart. Each
    step the house offers a bet on "next card's BACCARAT value == target_value"
    at odds fair against the remaining composition (a perfect counter's edge is
    exactly zero), and the observer stakes 1 unit when the filter's value
    probability minus the composition clears `threshold`. Realized profit is
    pure order structure surviving copy ambiguity — the quantity that decides
    whether hand-shuffled multi-deck baccarat is attackable. `passes` folds in
    via DFH Cor 4.2 (the equivalent single-pass shelf count). Returns a
    `PropositionResult` plus `.bits_per_shoe` (log-loss vs the perfect counter)
    and `.info`.

    `method`: "pf" = the rung-2 particle filter, "adf" = the rung-3
    assumed-density filter. Both consume the rng identically (the ADF needs
    no filter seed but one is drawn anyway), so both methods walk IDENTICAL
    shoes for a given `seed` — a paired CRN comparison by construction.

    `observer`: "class" is the honest model (copies of a rank+suit are
    indistinguishable); "position" grants the observer distinct-card
    resolution on the SAME shoes (the filter's classes become the input
    positions, so it reduces to the exact rung-1 posterior). The paired
    difference is the pure COPY TAX at fixed n — the E29 isolation study's
    instrument, separating it from the mixing-adequacy confound (a fixed
    machine mixes a bigger stack worse)."""
    import random

    from ridefree.baccarat import baccarat_value
    from ridefree.cards import RAW_RANKS, SUITS
    from ridefree.cards import value as bj_value
    from ridefree.shuffle import ShelfShuffle

    eq_shelves = shelves
    for _ in range(passes - 1):
        eq_shelves = 2 * eq_shelves * shelves
    classes = [(rank, suit) for suit in SUITS for rank in RAW_RANKS]
    bacc = {c: baccarat_value(bj_value(c)) for c in classes}
    model = ShelfShuffle(shelves=shelves, passes=passes)
    rng = random.Random(seed)
    deck = [c for _ in range(decks) for c in classes]
    n = len(deck)
    if method not in ("pf", "adf"):
        raise ValueError(f"unknown method: {method!r}")
    if observer not in ("class", "position"):
        raise ValueError(f"unknown observer: {observer!r}")
    # One deck = 52 distinct rank+suit classes, no copies (likewise the
    # position-resolution observer at any deck count), so the filter is
    # exact-deterministic and a single particle suffices (no wasted work).
    if decks == 1 or observer == "position":
        particles = 1
    bets = 0
    predicted = 0.0
    realized = 0.0
    deck_deltas = []
    bits = 0.0
    steps = 0
    surprises = 0
    for _ in range(trials):
        stack = list(deck)
        rng.shuffle(stack)  # shoe k, known to the observer at rank+suit level
        perm = model.permute(list(range(n)), rng)
        dealt = [stack[p] for p in perm]
        # The filter's equivalence classes are the rank+suit identities
        # (copies indistinct — the honest observation model) or, for the
        # position-resolution observer, the input positions themselves.
        if observer == "position":
            filter_values = list(range(n))
            tokens = perm
            token_bacc = {p: bacc[stack[p]] for p in range(n)}
        else:
            filter_values = stack
            tokens = dealt
            token_bacc = bacc
        filter_seed = rng.getrandbits(31)  # drawn for BOTH methods: CRN shoes
        if method == "pf":
            filt = MultiDeckShelfPosterior(
                eq_shelves, filter_values, particles=particles, seed=filter_seed
            )
        else:
            filt = AssumedDensityShelfPosterior(
                eq_shelves, filter_values, mix=adf_mix
            )
        vcount: dict = {}  # baccarat value -> remaining count (perfect counter)
        for c in stack:
            v = bacc[c]
            vcount[v] = vcount.get(v, 0) + 1
        remaining = n
        deck_pred = 0.0
        deck_real = 0.0
        for tok, card in zip(tokens, dealt):
            probs = filt.next_value_probs()  # over the observer's classes
            pval: dict = {}
            for c, pr in probs.items():
                v = token_bacc[c]
                pval[v] = pval.get(v, 0.0) + pr
            actual = bacc[card]
            target_left = vcount.get(target_value, 0)
            if 0 < target_left < remaining:
                q = target_left / remaining
                p = pval.get(target_value, 0.0)
                if p - q > threshold:
                    bets += 1
                    deck_pred += (p - q) / q
                    deck_real += (1 - q) / q if actual == target_value else -1.0
            q_v = vcount[actual] / remaining
            p_v = pval.get(actual, 0.0)
            if p_v > 0 and q_v > 0:
                bits += math.log(p_v) - math.log(q_v)
                steps += 1
            filt.observe(tok)
            remaining -= 1
            vcount[actual] -= 1
        predicted += deck_pred
        realized += deck_real
        deck_deltas.append(deck_real - deck_pred)
        surprises += getattr(filt, "surprises", 0)
    result = PropositionResult(trials, bets, predicted, realized, deck_deltas)
    result.bits_per_shoe = bits / trials / math.log(2)
    result.info = {"decks": decks, "shelves": shelves, "passes": passes,
                   "particles": particles, "n": n, "steps": steps,
                   "method": method, "observer": observer,
                   "surprises": surprises}
    return result


class PosteriorGuesser:
    """The exact posterior as a feedback guesser (the `forensics` protocol):
    guess the argmax of `next_probs`. This is the true optimal strategy, and
    `predicted` accumulates its own claimed per-step hit probability, so
    calibration (predicted vs realized correct guesses) is a free gate."""

    def __init__(self, shelves: int, stack) -> None:
        self._posterior = ShelfPosterior(shelves, stack)
        self.predicted = 0.0

    def guess(self):
        probs = self._posterior.next_probs()
        best = max(probs, key=probs.get)
        self.predicted += probs[best]
        return best

    def observe(self, card) -> None:
        self._posterior.observe(card)
