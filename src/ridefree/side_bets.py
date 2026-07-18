"""Side-bet hand classification and settlement.

21+3 resolves on the 3-card poker hand of (player card 1, player card 2,
dealer up) using raw (rank, suit) cards — see DESIGN.md M8 decision record.
Classification precedence matches the Wizard of Odds combination tables:
straight flush > three of a kind > straight > flush. Suited trips (possible in
a multi-deck shoe: three identical cards) therefore count as three of a kind,
and a flush containing an identical pair is just a flush. Ace counts both high
and low in straights (A-2-3 and Q-K-A both qualify; 12 sequences).
"""

from math import comb

RawCard = tuple[int, int]

# Highest-first precedence; the first category a hand satisfies is its class.
CATEGORIES_21P3 = ("straight_flush", "three_of_a_kind", "straight", "flush")

# The 12 rank sequences that make a straight (ace low through ace high).
_SEQUENCES = tuple((a, a + 1, a + 2) for a in range(1, 12)) + ((12, 13, 1),)


def _is_straight(ranks: list[int]) -> bool:
    a, b, c = sorted(ranks)
    return (a + 1 == b and b + 1 == c) or (a, b, c) == (1, 12, 13)


def classify_21p3(c1: RawCard, c2: RawCard, c3: RawCard) -> str | None:
    """The hand's 21+3 category, or None for a losing hand."""
    ranks = [c1[0], c2[0], c3[0]]
    flush = c1[1] == c2[1] == c3[1]
    if ranks[0] == ranks[1] == ranks[2]:
        return "three_of_a_kind"  # can't be a straight; suited trips land here
    if _is_straight(ranks):
        return "straight_flush" if flush else "straight"
    return "flush" if flush else None


def category_combos_21p3(
    counts: dict[RawCard, int],
) -> tuple[dict[str, int], int]:
    """Exact unordered-triple counts per 21+3 category for a shoe with
    per-(rank, suit) remaining `counts` — the closed-form pre-deal EV core.

    Integer arithmetic throughout (exact); classification identical to
    `classify_21p3`: trips = all same rank (suited trips included); straight
    excludes straight flushes; flush excludes straight flushes AND same-suit
    trips. Returns ({category: combos}, total_triples).
    """
    n_rank = [0] * 14  # index by rank 1-13
    n_suit = [0, 0, 0, 0]
    for (rank, suit), c in counts.items():
        n_rank[rank] += c
        n_suit[suit] += c
    n = sum(n_suit)
    total = comb(n, 3)
    trips = sum(comb(n_rank[r], 3) for r in range(1, 14))
    straights_all = sum(n_rank[a] * n_rank[b] * n_rank[c] for a, b, c in _SEQUENCES)
    sf = sum(
        counts[(a, s)] * counts[(b, s)] * counts[(c, s)]
        for a, b, c in _SEQUENCES
        for s in range(4)
    )
    suited_trips = sum(comb(c, 3) for c in counts.values())
    flush = sum(comb(ns, 3) for ns in n_suit) - sf - suited_trips
    return (
        {
            "straight_flush": sf,
            "three_of_a_kind": trips,
            "straight": straights_all - sf,
            "flush": flush,
        },
        total,
    )


def _c3(n: float) -> float:
    """n choose 3 as a polynomial — identical to comb(n, 3) on integers, and
    well-defined on the fractional 'smoothed' compositions the E11
    decomposition evaluates (the category identities are polynomials)."""
    return n * (n - 1.0) * (n - 2.0) / 6.0


def category_fracs_21p3(
    counts: dict[RawCard, float],
) -> tuple[dict[str, float], float]:
    """Float-tolerant twin of `category_combos_21p3` (same identities via
    `_c3`); equal to it on integer compositions (tested differentially)."""
    n_rank = [0.0] * 14
    n_suit = [0.0, 0.0, 0.0, 0.0]
    for (rank, suit), c in counts.items():
        n_rank[rank] += c
        n_suit[suit] += c
    n = sum(n_suit)
    total = _c3(n)
    trips = sum(_c3(n_rank[r]) for r in range(1, 14))
    straights_all = sum(n_rank[a] * n_rank[b] * n_rank[c] for a, b, c in _SEQUENCES)
    sf = sum(
        counts[(a, s)] * counts[(b, s)] * counts[(c, s)]
        for a, b, c in _SEQUENCES
        for s in range(4)
    )
    suited_trips = sum(_c3(c) for c in counts.values())
    flush = sum(_c3(ns) for ns in n_suit) - sf - suited_trips
    return (
        {
            "straight_flush": sf,
            "three_of_a_kind": trips,
            "straight": straights_all - sf,
            "flush": flush,
        },
        total,
    )


def _ev_from(
    combos: dict[str, float], total: float, paytable: tuple[tuple[str, float], ...]
) -> float:
    if total == 0:
        return 0.0
    pays = dict(paytable)
    won = sum((pays[c] + 1.0) * combos[c] for c in combos if c in pays)
    return won / total - 1.0


def ev_21p3(
    counts: dict[RawCard, int], paytable: tuple[tuple[str, float], ...]
) -> float:
    """Exact pre-deal EV per unit staked, given the remaining composition.

    EV = Σ_cat P(cat)·(pays+1) − 1; a category absent from the paytable
    contributes nothing (it loses the stake), matching `settle_21p3`.
    """
    combos, total = category_combos_21p3(counts)
    return _ev_from(combos, total, paytable)


def ev_fracs_21p3(
    counts: dict[RawCard, float], paytable: tuple[tuple[str, float], ...]
) -> float:
    """EV of a (possibly fractional) composition via the polynomial identities."""
    combos, total = category_fracs_21p3(counts)
    return _ev_from(combos, total, paytable)


def settle_21p3(
    paytable: tuple[tuple[str, float], ...],
    cards: tuple[RawCard, RawCard, RawCard],
    stake: float,
) -> tuple[float, str | None]:
    """(profit, category) for a staked 21+3 bet. A category absent from the
    paytable loses (tiered variants are configurations)."""
    category = classify_21p3(*cards)
    for cat, pays in paytable:
        if cat == category:
            return pays * stake, category
    return -stake, category
