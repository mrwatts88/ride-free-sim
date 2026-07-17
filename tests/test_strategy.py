"""BasicStrategy tests, focused on the H17/S17 rule-dependent plays."""

from ridefree.engine import Action, HandView
from ridefree.rules import Rules
from ridefree.strategy import BasicStrategy, BasicStrategyH17

H17 = Rules(dealer_hits_soft_17=True)
S17 = Rules(dealer_hits_soft_17=False)


def view(cards, total, soft, dealer_up, legal):
    return HandView(
        cards=tuple(cards),
        total=total,
        soft=soft,
        pair_rank=None,
        dealer_up=dealer_up,
        is_split_hand=False,
        legal=frozenset(legal),
    )


ALL = {Action.HIT, Action.STAND, Action.DOUBLE}


def test_alias_points_at_new_class():
    assert BasicStrategyH17 is BasicStrategy


def test_hard_11_vs_ace_h17_doubles_s17_hits():
    v = view([6, 5], 11, False, 1, ALL)
    assert BasicStrategy().choose(v, H17) is Action.DOUBLE
    assert BasicStrategy().choose(v, S17) is Action.HIT


def test_soft_19_vs_6_h17_doubles_s17_stands():
    v = view([1, 8], 19, True, 6, ALL)
    assert BasicStrategy().choose(v, H17) is Action.DOUBLE
    assert BasicStrategy().choose(v, S17) is Action.STAND


def test_soft_18_vs_2_h17_doubles_s17_stands():
    v = view([1, 7], 18, True, 2, ALL)
    assert BasicStrategy().choose(v, H17) is Action.DOUBLE
    assert BasicStrategy().choose(v, S17) is Action.STAND


def test_shared_plays_agree_across_rules():
    # Hard 20 stands, hard 16 vs 10 hits, 11 vs 6 doubles — same under both rules.
    for v in (
        view([10, 10], 20, False, 7, ALL),
        view([10, 6], 16, False, 10, ALL),
        view([6, 5], 11, False, 6, ALL),
    ):
        assert BasicStrategy().choose(v, H17) is BasicStrategy().choose(v, S17)


def test_double_falls_back_to_hit_or_stand_when_illegal():
    # 11 vs 6 wants to double; if double isn't legal it hits (D -> hit).
    v = view([4, 3, 4], 11, False, 6, {Action.HIT, Action.STAND})
    assert BasicStrategy().choose(v, H17) is Action.HIT
    # Soft 18 vs 5 wants Ds; without double it stands (Ds -> stand).
    v2 = view([1, 7], 18, True, 5, {Action.HIT, Action.STAND})
    assert BasicStrategy().choose(v2, H17) is Action.STAND
