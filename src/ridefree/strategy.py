"""Player strategies. The engine asks; a strategy answers.

BasicStrategyH17 is total-dependent basic strategy for the STANDARD_6D_H17 target:
multi-deck, dealer hits soft 17, double any two cards, DAS, no surrender. Chart
entries: H hit, S stand, D double-else-hit, Ds double-else-stand.
"""

from typing import Protocol

from ridefree.cards import ACE
from ridefree.engine import Action, HandView
from ridefree.rules import Rules


class PlayerStrategy(Protocol):
    def choose(self, view: HandView, rules: Rules) -> Action: ...


class ScriptedStrategy:
    """Plays a fixed action sequence; for constructing exact test scenarios."""

    def __init__(self, actions: list[Action]) -> None:
        self._queue = list(actions)

    def choose(self, view: HandView, rules: Rules) -> Action:
        if not self._queue:
            raise AssertionError(f"script exhausted; engine asked about {view}")
        return self._queue.pop(0)


class BasicStrategyH17:
    """Total-dependent basic strategy, multi-deck H17 DAS no-surrender."""

    def choose(self, view: HandView, rules: Rules) -> Action:
        up = 11 if view.dealer_up == ACE else view.dealer_up
        if (
            view.pair_rank is not None
            and Action.SPLIT in view.legal
            and self._split(view.pair_rank, up, rules.double_after_split)
        ):
            return Action.SPLIT
        code = self._soft(view.total, up) if view.soft else self._hard(view.total, up)
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
    def _hard(total: int, up: int) -> str:
        if total >= 17:
            return "S"
        if total >= 13:
            return "S" if up <= 6 else "H"
        if total == 12:
            return "S" if 4 <= up <= 6 else "H"
        if total == 11:
            return "D"  # H17: double 11 vs everything, ace included
        if total == 10:
            return "D" if up <= 9 else "H"
        if total == 9:
            return "D" if 3 <= up <= 6 else "H"
        return "H"

    @staticmethod
    def _soft(total: int, up: int) -> str:
        if total >= 20:
            return "S"
        if total == 19:
            return "Ds" if up == 6 else "S"  # H17: double A8 vs 6
        if total == 18:
            if up <= 6:
                return "Ds"  # H17: includes vs 2
            return "S" if up <= 8 else "H"
        if total == 17:
            return "D" if 3 <= up <= 6 else "H"
        if total in (15, 16):
            return "D" if 4 <= up <= 6 else "H"
        if total in (13, 14):
            return "D" if 5 <= up <= 6 else "H"
        return "H"  # soft 12: unsplittable A,A
