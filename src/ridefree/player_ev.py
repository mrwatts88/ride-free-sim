"""Exact infinite-deck player EV calculator — derives optimal total-dependent play.

Same model as dealer_odds: each draw is an i.i.d. rank with ten-weight 4/13. This is
the model behind published total-dependent charts, so the strategy it derives is the
like of what Wizard of Odds publishes — and the validation gate is the published
house edge, not a transcribed chart.

Money is expressed in units of the base bet as (own, free): a normal hand is (1, 0),
a free-split hand (0, 1). Settlement mirrors the engine's ledger exactly: a win pays
own+free, a loss costs own only, a push pays 0, and dealer 22 pushes when the rules
say so. The real-money vs free-hand strategy distinction the published charts make
falls out of this automatically — on a (0, 1) hand a push is worth the same as a
loss, so the calculator naturally plays those hands more aggressively.

This module is also the planned foundation for count-conditioned playing deviations
(roadmap M6): replace the fixed rank weights with the live shoe composition and the
same recursion yields the optimal action for the actual cards remaining.

Documented approximations (small, and none flip the cells we validate):
- Split EV values each post-split hand independently with no further resplits, which
  slightly understates free-resplit value (it only strengthens splits that are
  already taken).
- Split aces receive one card and are not re-split.
- The peek game conditions the dealer distribution on no dealer natural.
"""

from ridefree.cards import ACE, TEN
from ridefree.dealer_odds import dealer_distribution
from ridefree.engine import Action, HandView
from ridefree.rules import Rules

_RANKS = tuple(range(1, 11))
_W = {r: (4 if r == TEN else 1) for r in _RANKS}
_TW = 13


def _draw(total: int, soft: bool, rank: int) -> tuple[int, bool]:
    """Add one card to a (total, soft) state, demoting a soft ace as needed."""
    if rank == ACE:
        t = total + 11
        if t <= 21:
            return t, True
        t = total + 1
    else:
        t = total + rank
    if t > 21 and soft:
        return t - 10, False
    return t, soft


def _two_card_state(c1: int, c2: int) -> tuple[int, bool]:
    total, soft = _draw(0, False, c1)
    return _draw(total, soft, c2)


class EVCalculator:
    """Exact EVs for one rules object; memoized, so construction is cheap and the
    first few thousand lookups warm a small cache.

    `weights` overrides the infinite-deck rank frequencies (default ten-weight 4/13)
    for both player draws and dealer draws — the lever for effects-of-removal and,
    later, live-composition deviations."""

    def __init__(self, rules: Rules, weights: dict | None = None) -> None:
        self.rules = rules
        if weights is None:
            weights = {r: (4 if r == TEN else 1) for r in _RANKS}
        self._w = dict(weights)
        self._tw = sum(self._w.values())
        self._dealer: dict[int, dict] = {}
        self._memo: dict = {}

    def _p(self, rank: int) -> float:
        return self._w[rank] / self._tw

    def _dealer_dist(self, up: int) -> dict:
        if up not in self._dealer:
            exclude = self.rules.dealer_peeks_for_blackjack and up in (ACE, TEN)
            self._dealer[up] = dealer_distribution(
                up, self.rules, exclude_natural=exclude, weights=self._w
            )
        return self._dealer[up]

    def ev_final(self, total: int, own: float, free: float, up: int) -> float:
        """EV of a committed hand (stood, or doubled and done)."""
        if total > 21:
            return -own
        ev = 0.0
        for outcome, p in self._dealer_dist(up).items():
            if outcome == "bust":
                ev += p * (own + free)
            elif outcome == 22:
                if not self.rules.dealer_22_pushes:
                    ev += p * (own + free)
                # else: push, worth 0
            elif total > outcome:
                ev += p * (own + free)
            elif total < outcome:
                ev -= p * own
            # equal: push, worth 0
        return ev

    def ev_hit(self, total: int, soft: bool, own: float, free: float, up: int) -> float:
        """EV of taking exactly one card, then playing on optimally (hit/stand)."""
        ev = 0.0
        for r in _RANKS:
            t, s = _draw(total, soft, r)
            ev += self._p(r) * self.ev_play_on(t, s, own, free, up)
        return ev

    def ev_play_on(self, total: int, soft: bool, own: float, free: float, up: int) -> float:
        """Best of hit/stand from a 3+ card state (no doubles or splits left)."""
        if total > 21:
            return -own
        key = ("hs", total, soft, own, free, up)
        if key in self._memo:
            return self._memo[key]
        best = self.ev_final(total, own, free, up)
        if total < 21:
            best = max(best, self.ev_hit(total, soft, own, free, up))
        self._memo[key] = best
        return best

    def _free_double(self, c1: int, c2: int, soft: bool, is_split: bool) -> bool:
        rules = self.rules
        if not rules.free_double_totals:
            return False
        if is_split and not rules.free_double_after_split:
            return False
        if soft and not rules.free_double_soft_allowed:
            return False
        return (c1 + c2) in rules.free_double_totals

    def _post_split_hand_ev(self, card: int, own: float, free: float, up: int) -> float:
        """EV of a one-card hand after a split (no further resplits modeled)."""
        rules = self.rules
        total0, soft0 = _draw(0, False, card)
        ev = 0.0
        for r in _RANKS:
            p = self._p(r)
            if card == ACE and not rules.hit_split_aces:
                t, _ = _draw(total0, soft0, r)
                ev += p * self.ev_final(t, own, free, up)
            else:
                evs = self.two_card_evs(
                    card, r, up, own, free, is_split=True, allow_split=False
                )
                ev += p * max(evs.values())
        return ev

    def two_card_evs(
        self,
        c1: int,
        c2: int,
        up: int,
        own: float = 1.0,
        free: float = 0.0,
        is_split: bool = False,
        allow_split: bool = True,
    ) -> dict[Action, float]:
        """EV of every available action from a two-card hand."""
        rules = self.rules
        key = ("2c", min(c1, c2), max(c1, c2), up, own, free, is_split, allow_split)
        if key in self._memo:
            return self._memo[key]
        total, soft = _two_card_state(c1, c2)
        evs: dict[Action, float] = {Action.STAND: self.ev_final(total, own, free, up)}
        if total < 21:
            evs[Action.HIT] = self.ev_hit(total, soft, own, free, up)
        can_double = rules.double_any_two_cards or (
            not soft and total in rules.double_hard_totals
        )
        if is_split and not rules.double_after_split:
            can_double = False
        if can_double:
            if self._free_double(c1, c2, soft, is_split):
                o2, f2 = own, free + 1.0
            else:
                o2, f2 = own + 1.0, free
            dbl = 0.0
            for r in _RANKS:
                t, _ = _draw(total, soft, r)
                dbl += self._p(r) * self.ev_final(t, o2, f2, up)
            evs[Action.DOUBLE] = dbl
        if allow_split and c1 == c2:
            free_split = c1 in rules.free_split_ranks and (
                not is_split or rules.free_resplits
            )
            new_own, new_free = (0.0, 1.0) if free_split else (1.0, 0.0)
            evs[Action.SPLIT] = self._post_split_hand_ev(
                c1, own, free, up
            ) + self._post_split_hand_ev(c1, new_own, new_free, up)
        self._memo[key] = evs
        return evs


def game_ev(rules: Rules, weights: dict | None = None) -> float:
    """Full-round EV per unit initial bet under i.i.d. rank draws at `weights`.

    Sums over all (player two-card hand, dealer up-card) deals: player naturals paid
    at the blackjack rate unless the dealer also has one; dealer naturals (found on
    the peek) take exactly the initial bet; everything else plays best-action per
    two_card_evs, whose dealer distribution is already conditioned on no dealer
    natural for A/T up-cards — consistent with weighting by (1 - P(dealer BJ)).
    """
    calc = EVCalculator(rules, weights)
    p = calc._p
    ev = 0.0
    for up in _RANKS:
        p_up = p(up)
        if rules.dealer_peeks_for_blackjack and up == ACE:
            p_dealer_bj = p(TEN)
        elif rules.dealer_peeks_for_blackjack and up == TEN:
            p_dealer_bj = p(ACE)
        else:
            p_dealer_bj = 0.0
        for c1 in _RANKS:
            for c2 in _RANKS:
                if c2 < c1:
                    continue
                p_hand = (1 if c1 == c2 else 2) * p(c1) * p(c2)
                if {c1, c2} == {ACE, TEN}:  # player natural: push vs dealer BJ
                    ev += p_up * p_hand * (1 - p_dealer_bj) * rules.blackjack_payout
                    continue
                best = max(calc.two_card_evs(c1, c2, up).values())
                ev += p_up * p_hand * (p_dealer_bj * -1.0 + (1 - p_dealer_bj) * best)
    return ev


def choose_with_calc(calc: EVCalculator, view: HandView) -> Action:
    """Argmax-EV over the engine's legal actions, using the given calculator."""
    own, free = view.own_wager, view.free_wager
    if len(view.cards) == 2:
        c1, c2 = view.cards
        evs = calc.two_card_evs(
            c1, c2, view.dealer_up, own, free,
            is_split=view.is_split_hand,
            allow_split=Action.SPLIT in view.legal,
        )
        legal_evs = {a: v for a, v in evs.items() if a in view.legal}
        return max(legal_evs, key=legal_evs.get)  # type: ignore[arg-type]
    stand = calc.ev_final(view.total, own, free, view.dealer_up)
    hit = calc.ev_hit(view.total, view.soft, own, free, view.dealer_up)
    return Action.HIT if hit > stand else Action.STAND


class OptimalStrategy:
    """Plays argmax-EV per the exact calculator, restricted to the engine's legal
    actions. Total-dependent by construction (infinite-deck EVs depend only on
    total/softness/funding), so it corresponds to a published-style chart."""

    def __init__(self) -> None:
        self._calcs: dict[Rules, EVCalculator] = {}
        self._decisions: dict[tuple, Action] = {}

    def _calc(self, rules: Rules) -> EVCalculator:
        calc = self._calcs.get(rules)
        if calc is None:
            calc = self._calcs[rules] = EVCalculator(rules)
        return calc

    def choose(self, view: HandView, rules: Rules) -> Action:
        key = (
            rules, view.cards if len(view.cards) == 2 else (view.total, view.soft),
            view.dealer_up, view.own_wager, view.free_wager,
            view.is_split_hand, view.legal,
        )
        cached = self._decisions.get(key)
        if cached is not None:
            return cached
        action = choose_with_calc(self._calc(rules), view)
        self._decisions[key] = action
        return action


class CompositionStrategy:
    """Perfect-information playing deviations: argmax-EV with the LIVE remaining
    shoe composition as the deck model. Call `set_composition` once per round
    (composition is frozen intra-round — the tracker updates between rounds); all
    decisions in the round share one calculator and its memo."""

    def __init__(self) -> None:
        self._calc: EVCalculator | None = None

    def set_composition(self, rules: Rules, counts: dict[int, int]) -> None:
        weights = {r: max(counts[r], 0) for r in counts}
        self._calc = EVCalculator(rules, weights)

    def choose(self, view: HandView, rules: Rules) -> Action:
        assert self._calc is not None, "set_composition must be called each round"
        return choose_with_calc(self._calc, view)
