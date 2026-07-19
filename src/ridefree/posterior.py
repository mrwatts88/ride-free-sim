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
