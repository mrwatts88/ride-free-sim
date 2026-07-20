"""The blackjack insurance order-adapter (M12b Gate-B): ordered-posterior
insurance pricing.

The two-layer rule (STATUS, 2026-07-19): the posterior core never imports a
game -- THIS module is the thin adapter over (posterior filter, blackjack
insurance settlement). It answers the Gate-B question the baccarat coup adapter
(coup.py) could not: does the value-level order channel (E27-E29) turn into
REAL money at the best single-card converter we have? Insurance is exactly that
converter -- a direct bet on ONE card (the dealer's hole), offered when the
upcard is an ace, paying `insurance_pays`:1 iff the hole is a ten. Breakeven is
P(hole is ten) > 1/(1 + pays) = 1/3 at 2:1.

Why this adapter is far thinner than the coup adapter: a coup's payoff depends
on the JOINT law of the next 4-6 cards (no closed form; coup.py samples it by
coupled control variates and pays the E31 over-shrink toll). Insurance depends
on ONE marginal card, so the observer's price is a single `next_value_probs()`
query summed over the value-10 classes -- exact under the filter, no Monte
Carlo, no winner's-curse split. And because the assumed-density `mix` blends the
OUTPUT law linearly toward composition, the observer's price at any mix is

    P_obs(ten | mix) = (1 - mix) * P_model(ten) + mix * P_counter(ten),

where P_counter(ten) = tens_remaining / cards_remaining is the perfect
composition counter's price (E29: occ[v] == remaining count of value v, exact
bookkeeping). So a full contamination sweep is post-hoc arithmetic over the two
recorded probabilities -- the walk runs once, at mix 0.

The perfect-counter comparator is the same idea as coup.py's `fast_outcomes`
arm: it prices insurance on the remaining composition alone, so its profit is
everything composition can see and the observer's EXCESS over it is pure order
structure -- the paradigm-2 quantity, now in real insurance dollars. The
counter arm reproduces the validated `CompositionPlayer.take_insurance` rule
(`tens * (1 + pays) > cards_left`, player_ev.py) exactly.

Observation premise (on record, the degradation knob for later): the observer
sees every dealt card of shoe k+1 in physical order, INCLUDING the hole card
after the round -- the full-information convention E27-E30 assumed and the same
one CompositionPlayer carries. A live player only sees the hole when the dealer
reveals it (not on player-bust rounds at many houses); partial hole observation
is a later degradation curve, not this first measurement.
"""

import math
import random

from ridefree.cards import ACE, RAW_RANKS, SUITS, TEN
from ridefree.cards import value as bj_value
from ridefree.engine import play_round
from ridefree.posterior import AssumedDensityShelfPosterior
from ridefree.rules import Rules
from ridefree.shuffle import ShelfShuffle
from ridefree.strategy import BasicStrategy


class _ValueShoe:
    """Deals blackjack VALUES (1-10) from `classes[start:]`; `count` records how
    many cards the engine consumed, which advances the shoe past a resolved
    round. The observer watches the same classes (rank+suit) separately."""

    def __init__(self, classes, start: int) -> None:
        self._classes = classes
        self._i = start
        self.count = 0

    def deal(self) -> int:
        c = self._classes[self._i]
        self._i += 1
        self.count += 1
        return bj_value(c)


def insurance_experiment(
    rules: Rules,
    shelves: int,
    shoes: int,
    seed: int,
    *,
    passes: int = 1,
    decks: int | None = None,
    min_tail: int = 30,
    strategy=None,
) -> dict:
    """Walk shelf-shuffled known shoes; record every ace-up insurance spot.

    Per shoe: a fresh uniformly-ordered stack (shoe k, fully observed by
    premise) is shelf-shuffled into the dealt order; rounds resolve through the
    VALIDATED engine (`play_round`, never a reimplemented deal) to advance the
    shoe by exactly the cards a heads-up basic-strategy player consumes. At each
    round whose upcard is an ace, BEFORE the hole is observed, the observer's
    model price P_model(hole is ten) is read from the filter and the counter's
    price P_counter = tens/cards from the tracked composition; the realized hole
    is recorded. Those triples price insurance under any mix in `summarize`.

    The filter runs at mix 0 (pure model); the contamination sweep is post-hoc
    (see module docstring). Returns the raw per-spot records plus metadata.
    """
    strategy = BasicStrategy() if strategy is None else strategy
    decks = rules.decks if decks is None else decks
    classes = [(rank, suit) for suit in SUITS for rank in RAW_RANKS]
    model = ShelfShuffle(shelves=shelves, passes=passes)
    # Two passes == one (2*m*m)-shelf pass (DFH Cor 4.2), matched by the filter
    # geometry exactly as coup.py does -- so the channel-closing regime is
    # reachable by this adapter without new posterior code.
    eq_shelves = shelves
    for _ in range(passes - 1):
        eq_shelves = 2 * eq_shelves * shelves

    rng = random.Random(seed)
    stack_proto = [c for _ in range(decks) for c in classes]
    n = len(stack_proto)
    cutoff = int(rules.penetration * n)

    spots: list[dict] = []
    surprises = 0
    rounds_total = 0
    for shoe_idx in range(shoes):
        stack = list(stack_proto)
        rng.shuffle(stack)  # shoe k, known to the observer
        dealt = [stack[p] for p in model.permute(list(range(n)), rng)]
        filt = AssumedDensityShelfPosterior(eq_shelves, stack, mix=0.0)
        comp = {v: 0 for v in range(1, 11)}
        for c in stack:
            comp[bj_value(c)] += 1

        pos = 0
        while pos < cutoff and (n - pos) >= min_tail:
            up = dealt[pos + 1]
            insured = rules.insurance_offered and bj_value(up) == ACE
            # resolve the true round to learn how many cards it consumes
            shoe = _ValueShoe(dealt, pos)
            play_round(rules, shoe, strategy, bet=1.0)
            used = shoe.count

            # observe the three visible cards (player1, dealer up, player2)
            for c in dealt[pos:pos + 3]:
                filt.observe(c)
                comp[bj_value(c)] -= 1

            if insured:
                law = filt.next_value_probs()
                model_p = math.fsum(p for cls, p in law.items()
                                    if bj_value(cls) == TEN)
                cards_left = sum(comp.values())
                counter_p = comp[TEN] / cards_left
                spots.append({
                    "shoe": shoe_idx,
                    "model_p": model_p,
                    "counter_p": counter_p,
                    "hole_ten": bj_value(dealt[pos + 3]) == TEN,
                })

            # observe the hole and any draw cards (physical order)
            for c in dealt[pos + 3:pos + used]:
                filt.observe(c)
                comp[bj_value(c)] -= 1
            pos += used
            rounds_total += 1
        surprises += filt.surprises

    return {
        "spots": spots,
        "shoes": shoes,
        "rounds": rounds_total,
        "n": n,
        "decks": decks,
        "shelves": shelves,
        "passes": passes,
        "eq_shelves": eq_shelves,
        "penetration": rules.penetration,
        "insurance_pays": rules.insurance_pays,
        "surprises": surprises,
    }


def _z_of(deltas: list[float]) -> float:
    if len(deltas) < 2:
        return 0.0
    m = sum(deltas) / len(deltas)
    var = sum((d - m) ** 2 for d in deltas) / (len(deltas) - 1)
    return m * math.sqrt(len(deltas) / var) if var > 0 else 0.0


def summarize_insurance(result: dict, mixes, pays: float | None = None) -> dict:
    """Price insurance for the observer (each mix) vs the perfect counter.

    Ledgers are in insurance-STAKE units (win +pays, lose -1; multiply by the
    half-unit stake for main-bet dollars). The counter arm is mix-invariant.
    For each mix reports: bets/predicted/realized for both arms; the per-shoe
    realized excess (observer - counter) and its z -- the honest shard/shoe
    unit, since insurance bets inside one shoe share its order (the E31 lesson
    against per-bet pooling); the calibration (realized ten-rate vs mean
    predicted at the observer's taken spots -- the E17 gate that catches an
    over-confident low-mix model); and the model's information gain over the
    counter in bits per spot on the hole ten/not-ten prediction.
    """
    pays = result["insurance_pays"] if pays is None else pays
    spots = result["spots"]
    n_shoes = result["shoes"]
    threshold = 1.0 / (1.0 + pays)  # 1/3 at 2:1

    def realized(hole_ten: bool) -> float:
        return pays if hole_ten else -1.0

    # bits: mean over all spots of log2 P_arm(actual) improvement, model - counter
    bits_num = 0.0
    for s in spots:
        pm = s["model_p"] if s["hole_ten"] else 1.0 - s["model_p"]
        pc = s["counter_p"] if s["hole_ten"] else 1.0 - s["counter_p"]
        pm = min(max(pm, 1e-12), 1.0)
        pc = min(max(pc, 1e-12), 1.0)
        bits_num += math.log2(pm) - math.log2(pc)
    bits_per_spot = bits_num / len(spots) if spots else 0.0

    # counter arm (mix-invariant)
    c_shoe = {}
    counter = {"bets": 0, "predicted": 0.0, "realized": 0.0,
               "taken_p": 0.0, "taken_ten": 0}
    for s in spots:
        if (1.0 + pays) * s["counter_p"] > 1.0:
            counter["bets"] += 1
            counter["predicted"] += (1.0 + pays) * s["counter_p"] - 1.0
            r = realized(s["hole_ten"])
            counter["realized"] += r
            counter["taken_p"] += s["counter_p"]
            counter["taken_ten"] += 1 if s["hole_ten"] else 0
            c_shoe[s["shoe"]] = c_shoe.get(s["shoe"], 0.0) + r

    out = {
        "spots": len(spots),
        "shoes": n_shoes,
        "insured_rate_per_shoe": len(spots) / n_shoes if n_shoes else 0.0,
        "bits_per_spot": bits_per_spot,
        "counter": counter,
        "mixes": {},
    }

    for mix in mixes:
        f_shoe = {}
        arm = {"bets": 0, "predicted": 0.0, "realized": 0.0,
               "taken_p": 0.0, "taken_ten": 0}
        for s in spots:
            obs_p = (1.0 - mix) * s["model_p"] + mix * s["counter_p"]
            if (1.0 + pays) * obs_p > 1.0:
                arm["bets"] += 1
                arm["predicted"] += (1.0 + pays) * obs_p - 1.0
                r = realized(s["hole_ten"])
                arm["realized"] += r
                arm["taken_p"] += obs_p
                arm["taken_ten"] += 1 if s["hole_ten"] else 0
                f_shoe[s["shoe"]] = f_shoe.get(s["shoe"], 0.0) + r
        deltas = [f_shoe.get(k, 0.0) - c_shoe.get(k, 0.0) for k in range(n_shoes)]
        cal_pred = arm["taken_p"] / arm["bets"] if arm["bets"] else 0.0
        cal_real = arm["taken_ten"] / arm["bets"] if arm["bets"] else 0.0
        out["mixes"][mix] = {
            "filter": arm,
            "excess_realized": arm["realized"] - counter["realized"],
            "excess_per_shoe": (arm["realized"] - counter["realized"]) / n_shoes
            if n_shoes else 0.0,
            "excess_z": _z_of(deltas),
            "cal_predicted_ten": cal_pred,   # mean predicted P(ten) at taken spots
            "cal_realized_ten": cal_real,    # actual ten-rate there (E17 gate)
        }
    return out
