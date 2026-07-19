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
    and `.info`."""
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
    # One deck = 52 distinct rank+suit classes, no copies, so the filter is
    # exact-deterministic and a single particle suffices (no wasted work).
    if decks == 1:
        particles = 1
    bets = 0
    predicted = 0.0
    realized = 0.0
    deck_deltas = []
    bits = 0.0
    steps = 0
    for _ in range(trials):
        stack = list(deck)
        rng.shuffle(stack)  # shoe k, known to the observer at rank+suit level
        dealt = [stack[p] for p in model.permute(list(range(n)), rng)]
        # The filter's equivalence classes ARE the rank+suit identities, so
        # copies of a rank+suit are indistinct — the honest observation model.
        filt = MultiDeckShelfPosterior(
            eq_shelves, stack, particles=particles, seed=rng.getrandbits(31)
        )
        vcount: dict = {}  # baccarat value -> remaining count (perfect counter)
        for c in stack:
            v = bacc[c]
            vcount[v] = vcount.get(v, 0) + 1
        remaining = n
        deck_pred = 0.0
        deck_real = 0.0
        for card in dealt:
            probs = filt.next_value_probs()  # over rank+suit classes
            pval: dict = {}
            for c, pr in probs.items():
                v = bacc[c]
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
            filt.observe(card)
            remaining -= 1
            vcount[actual] -= 1
        predicted += deck_pred
        realized += deck_real
        deck_deltas.append(deck_real - deck_pred)
    result = PropositionResult(trials, bets, predicted, realized, deck_deltas)
    result.bits_per_shoe = bits / trials / math.log(2)
    result.info = {"decks": decks, "shelves": shelves, "passes": passes,
                   "particles": particles, "n": n, "steps": steps}
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
