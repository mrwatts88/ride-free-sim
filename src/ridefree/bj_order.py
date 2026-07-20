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
from ridefree.dealer_odds import _distribution
from ridefree.player_ev import EVCalculator, choose_with_calc
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


# ============================================================================
# PLAYING DEVIATIONS via HOLE-CARD PLAY -- the toll-free, every-round converter
# (M12b Gate-B, arm 2)
# ============================================================================
#
# Insurance (above) proved order info converts to money, but it is one rare
# half-stake bet. The bigger, human-relevant PLAY signal is HOLE-CARD PLAY:
# knowing the dealer's hole card is worth ~+6.8% with perfect knowledge, and a
# weak shuffle lets an order observer PREDICT it -- the SAME hole posterior E33
# prices for insurance, now driving hit/stand/double/split instead of a side bet.
#
# The clean formulation (why it is NOT the naive "swap the filter marginal into
# EVCalculator", which corrupts multi-card evaluations and underperforms): the
# player does NOT see the hole, so it commits to ONE action per decision, and
# its EV is LINEAR in the dealer's outcome distribution. Therefore the
# hole-posterior-optimal action is the argmax under a single BLENDED dealer
# distribution, sum_v P(hole=v) * dealer_dist(up, hole=v) -- one EVCalculator
# with that blend injected for the up-card. Three players differ ONLY in the
# hole prior, isolating the hole-card channel exactly:
#   * composition  -- hole prior = remaining composition   (the perfect counter)
#   * order        -- hole prior = the filter's posterior   (E33's, AUC ~0.59)
#   * clairvoyant  -- hole prior = point mass on the true hole  (the ceiling)
# Player draws (hits) use composition for all three, so the only moving part is
# the dealer-hole model. Reality (the engine) always resolves with the TRUE
# hole, so realized profit rewards a better hole model honestly.
#
# Observation premise (realistic, unlike insurance's full-info convention): the
# observer has seen player1/up/player2 but NOT the hole when it plays -- the hole
# posterior is filter.next_value_probs() at that point (the pos-3 law). The hole
# is observed after the round. Still bounded by the memorability ceiling (E33).
# Hit-card order signal (pos-4 onward) is deferred; this isolates the hole.


def _value_law(class_law: dict) -> dict:
    """Collapse a {(rank,suit): p} law to {blackjack value: p}."""
    out = {v: 0.0 for v in range(1, 11)}
    for cls, p in class_law.items():
        out[bj_value(cls)] += p
    return out


def _blended_dealer_dist(rules: Rules, up: int, hole_law: dict, weights: dict) -> dict:
    """Dealer outcome distribution with the hole marginalized over `hole_law`
    (and, since a played round means the peek found no dealer natural, the
    natural-completing hole excluded for A/T up-cards -- matching
    dealer_distribution(exclude_natural=True))."""
    tw = sum(weights.values())
    memo: dict = {}
    drop = TEN if up == ACE else (ACE if up == TEN else None)
    kept = {v: p for v, p in hole_law.items() if v != drop and p > 0.0}
    s = sum(kept.values())
    if s <= 0.0:  # degenerate; fall back to the unconditioned law
        kept = {v: p for v, p in hole_law.items() if p > 0.0}
        s = sum(kept.values())
    blend: dict = {}
    for v, p in kept.items():
        w = p / s
        for o, pr in _distribution([up, v], rules, memo, weights, tw).items():
            blend[o] = blend.get(o, 0.0) + w * pr
    return blend


class _HoleCardStrategy:
    """Plays argmax-EV under a per-round EVCalculator whose up-card dealer
    distribution has the hole marginalized over a supplied hole prior."""

    def __init__(self) -> None:
        self.calc = None

    def choose(self, view, rules):
        return choose_with_calc(self.calc, view)


def deviation_experiment(
    rules: Rules,
    shelves: int,
    shoes: int,
    seed: int,
    *,
    passes: int = 1,
    decks: int | None = None,
    min_tail: int = 30,
) -> dict:
    """Paired hole-card-play value on shelf-shuffled known shoes: order and
    clairvoyant hole priors vs the composition counter. The composition arm is
    the canonical timeline; the order and clairvoyant arms replay each round
    from the same start cards (rounds that don't flip a decision cancel to exact
    zero -- the low-variance deviation estimand). Returns per-shoe paired deltas
    (order-comp, clair-comp) and tallies.
    """
    decks = rules.decks if decks is None else decks
    classes = [(rank, suit) for suit in SUITS for rank in RAW_RANKS]
    model = ShelfShuffle(shelves=shelves, passes=passes)
    eq_shelves = shelves
    for _ in range(passes - 1):
        eq_shelves = 2 * eq_shelves * shelves

    rng = random.Random(seed)
    stack_proto = [c for _ in range(decks) for c in classes]
    n = len(stack_proto)
    cutoff = int(rules.penetration * n)
    strat = _HoleCardStrategy()

    order_deltas, clair_deltas = [], []
    totals = {"comp": 0.0, "order": 0.0, "clair": 0.0}
    rounds_total = 0
    changed = {"order": 0, "clair": 0}
    surprises = 0
    for _shoe in range(shoes):
        stack = list(stack_proto)
        rng.shuffle(stack)
        dealt = [stack[p] for p in model.permute(list(range(n)), rng)]
        filt = AssumedDensityShelfPosterior(eq_shelves, stack, mix=0.0)
        comp = {v: 0 for v in range(1, 11)}
        for c in stack:
            comp[bj_value(c)] += 1

        pos = 0
        sd_order = sd_clair = 0.0
        while pos < cutoff and (n - pos) >= min_tail:
            up = bj_value(dealt[pos + 1])
            # the observer sees player1, up, player2 -- NOT the hole yet
            for c in dealt[pos:pos + 3]:
                filt.observe(c)
                comp[bj_value(c)] -= 1

            csum = sum(comp.values())
            hole_priors = {
                "comp": {v: comp[v] / csum for v in range(1, 11) if comp[v] > 0},
                "order": _value_law(filt.next_value_probs()),
                "clair": {bj_value(dealt[pos + 3]): 1.0},
            }
            weights = dict(comp)  # composition for player draws (all three arms)

            profits = {}
            used = None
            for name in ("comp", "order", "clair"):
                calc = EVCalculator(rules, weights)
                calc._dealer[up] = _blended_dealer_dist(
                    rules, up, hole_priors[name], weights)
                strat.calc = calc
                shoe = _ValueShoe(dealt, pos)
                profits[name] = play_round(rules, shoe, strat, bet=1.0).profit
                if name == "comp":
                    used = shoe.count

            totals["comp"] += profits["comp"]
            totals["order"] += profits["order"]
            totals["clair"] += profits["clair"]
            do = profits["order"] - profits["comp"]
            dc = profits["clair"] - profits["comp"]
            sd_order += do
            sd_clair += dc
            if do != 0.0:
                changed["order"] += 1
            if dc != 0.0:
                changed["clair"] += 1
            rounds_total += 1

            # advance the canonical (composition) timeline: hole + draws
            for c in dealt[pos + 3:pos + used]:
                filt.observe(c)
                comp[bj_value(c)] -= 1
            pos += used
        order_deltas.append(sd_order)
        clair_deltas.append(sd_clair)
        surprises += filt.surprises

    rt = rounds_total or 1
    return {
        "shoes": shoes,
        "rounds": rounds_total,
        "n": n,
        "decks": decks,
        "shelves": shelves,
        "passes": passes,
        "penetration": rules.penetration,
        "surprises": surprises,
        "comp_per_round": totals["comp"] / rt,
        "order_delta_per_round": (totals["order"] - totals["comp"]) / rt,
        "clair_delta_per_round": (totals["clair"] - totals["comp"]) / rt,
        "order_delta_per_shoe": sum(order_deltas) / len(order_deltas),
        "clair_delta_per_shoe": sum(clair_deltas) / len(clair_deltas),
        "order_z": _z_of(order_deltas),
        "clair_z": _z_of(clair_deltas),
        "order_changed_rate": changed["order"] / rt,
        "clair_changed_rate": changed["clair"] / rt,
        "order_deltas": order_deltas,
        "clair_deltas": clair_deltas,
    }
