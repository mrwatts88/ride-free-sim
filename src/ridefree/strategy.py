"""Player strategies. The engine asks; a strategy answers.

BasicStrategy is total-dependent basic strategy for a multi-deck, double-any-two, DAS,
no-surrender game. It adapts to the dealer's soft-17 rule (`rules.dealer_hits_soft_17`)
for the three plays that genuinely differ between H17 and S17 — 11 vs A, soft 18 vs 2,
soft 19 vs 6 — so the same object plays both STANDARD_6D_H17 and STANDARD_6D_S17
correctly. Chart entries: H hit, S stand, D double-else-hit, Ds double-else-stand.
"""

from typing import Protocol

from ridefree.cards import ACE
from ridefree.engine import Action, HandView
from ridefree.rules import Rules


class PlayerStrategy(Protocol):
    """`choose` is required. Three OPTIONAL hooks (looked up by name):

    - take_insurance(cards, rules) -> bool: engine asks when the dealer shows an
      ace and rules.insurance_offered; absent = never insure.
    - observe_round(result), new_shoe(): the simulator feeds settled rounds and
      reshuffles to card-tracking strategies (see player_ev.CompositionPlayer).
    """

    def choose(self, view: HandView, rules: Rules) -> Action: ...


class ScriptedStrategy:
    """Plays a fixed action sequence; for constructing exact test scenarios."""

    def __init__(self, actions: list[Action]) -> None:
        self._queue = list(actions)

    def choose(self, view: HandView, rules: Rules) -> Action:
        if not self._queue:
            raise AssertionError(f"script exhausted; engine asked about {view}")
        return self._queue.pop(0)


class BasicStrategy:
    """Total-dependent basic strategy, multi-deck DAS no-surrender, H17/S17-aware."""

    def choose(self, view: HandView, rules: Rules) -> Action:
        up = 11 if view.dealer_up == ACE else view.dealer_up
        h17 = rules.dealer_hits_soft_17
        if (
            view.pair_rank is not None
            and Action.SPLIT in view.legal
            and self._split(view.pair_rank, up, rules.double_after_split)
        ):
            return Action.SPLIT
        code = self._soft(view.total, up, h17) if view.soft else self._hard(view.total, up, h17)
        if code == "S":
            return Action.STAND
        if code == "H":
            return Action.HIT
        if Action.DOUBLE in view.legal:
            return Action.DOUBLE
        return Action.STAND if code == "Ds" else Action.HIT

    @staticmethod
    def _split(rank: int, up: int, das: bool) -> bool:
        if rank == ACE or rank == 8:
            return True
        if rank == 9:
            return up in (2, 3, 4, 5, 6, 8, 9)
        if rank == 7:
            return up <= 7
        if rank == 6:
            return up <= 6 if das else 3 <= up <= 6
        if rank == 4:
            return das and up in (5, 6)
        if rank in (2, 3):
            return up <= 7 if das else 4 <= up <= 7
        return False  # 5s play as hard 10; tens stand

    @staticmethod
    def _hard(total: int, up: int, h17: bool) -> str:
        if total >= 17:
            return "S"
        if total >= 13:
            return "S" if up <= 6 else "H"
        if total == 12:
            return "S" if 4 <= up <= 6 else "H"
        if total == 11:
            # 11 vs A: double under H17, hit under S17; double vs everything else.
            return "H" if (up == 11 and not h17) else "D"
        if total == 10:
            return "D" if up <= 9 else "H"
        if total == 9:
            return "D" if 3 <= up <= 6 else "H"
        return "H"

    @staticmethod
    def _soft(total: int, up: int, h17: bool) -> str:
        if total >= 20:
            return "S"
        if total == 19:
            return "Ds" if (up == 6 and h17) else "S"  # double A8 vs 6 only under H17
        if total == 18:
            if up <= 6:
                if up == 2 and not h17:
                    return "S"  # S17: stand A7 vs 2 (H17 doubles)
                return "Ds"
            return "S" if up <= 8 else "H"
        if total == 17:
            return "D" if 3 <= up <= 6 else "H"
        if total in (15, 16):
            return "D" if 4 <= up <= 6 else "H"
        if total in (13, 14):
            return "D" if 5 <= up <= 6 else "H"
        return "H"  # soft 12: unsplittable A,A


# Back-compat alias; the strategy now adapts to H17/S17 via the rules object.
BasicStrategyH17 = BasicStrategy


class FreeBetStrategy(BasicStrategy):
    """PROVISIONAL free-bet strategy for M3 plumbing — not yet the published chart.

    Rules of thumb encoded here:
    - Always take a free double (pure upside; the engine funds it).
    - Free-split every eligible pair except 5,5 (a pair of 5s is hard 10 — the free
      double is the better free money).
    - Otherwise fall back to standard basic strategy.

    M4 replaces the fallback with the published Free Bet chart (hit/stand deviations
    exist because dealer 22 pushing devalues standing) and validates the whole thing
    against the published house edge. Do not treat this class's EV as meaningful.
    """

    def choose(self, view: HandView, rules: Rules) -> Action:
        if view.free_split_available and view.pair_rank != 5:
            return Action.SPLIT
        if view.free_double_available:
            return Action.DOUBLE
        return super().choose(view, rules)
