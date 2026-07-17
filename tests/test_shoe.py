from ridefree.cards import RANKS, TEN, Shoe, deck_composition


def drain(shoe: Shoe) -> list[int]:
    return [shoe.deal() for _ in range(shoe.cards_remaining)]


def test_same_seed_same_sequence():
    a = drain(Shoe(decks=6, penetration=0.75, seed=42))
    b = drain(Shoe(decks=6, penetration=0.75, seed=42))
    assert a == b


def test_different_seeds_differ():
    a = drain(Shoe(decks=6, penetration=0.75, seed=1))
    b = drain(Shoe(decks=6, penetration=0.75, seed=2))
    assert a != b


def test_six_deck_composition():
    shoe = Shoe(decks=6, penetration=0.75, seed=0)
    assert shoe.cards_remaining == 312
    counts = dict.fromkeys(RANKS, 0)
    for card in drain(shoe):
        counts[card] += 1
    assert counts == deck_composition(6)
    assert counts[TEN] == 96
    assert all(counts[rank] == 24 for rank in range(1, 10))


def test_remaining_composition_tracks_deals():
    shoe = Shoe(decks=1, penetration=1.0, seed=7)
    start = shoe.remaining_composition()
    assert start == deck_composition(1)
    first = shoe.deal()
    after = shoe.remaining_composition()
    assert after[first] == start[first] - 1
    assert sum(after.values()) == 51


def test_cut_card_and_penetration():
    shoe = Shoe(decks=6, penetration=0.75, seed=3)
    assert not shoe.needs_shuffle
    for _ in range(233):  # cut at round(312 * 0.75) = 234
        shoe.deal()
    assert not shoe.needs_shuffle
    shoe.deal()
    assert shoe.needs_shuffle


def test_empty_shoe_raises():
    shoe = Shoe(decks=1, penetration=1.0, seed=0)
    drain(shoe)
    try:
        shoe.deal()
    except IndexError:
        pass
    else:
        raise AssertionError("expected IndexError from empty shoe")


def test_dealt_cards_replay():
    shoe = Shoe(decks=2, penetration=0.5, seed=99)
    dealt = [shoe.deal() for _ in range(10)]
    assert list(shoe.dealt_cards()) == dealt
