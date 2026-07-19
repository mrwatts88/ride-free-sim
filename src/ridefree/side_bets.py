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


def exact_p0_pot_of_gold(rules) -> float:
    """Exact P(Pot of Gold loses) — the strategy-independent tier-1 reference.

    A round collects >=1 lammer iff the initial two player cards are free-bet
    eligible under `rules` (free-split pair, or free-double two-card total,
    hard-only unless the soft flag is on) AND the dealer has no blackjack —
    and every strategy in the repo takes every offered free bet (the 5,5
    free-double-vs-free-split choice yields one lammer either way), so P(0)
    is pure dealing arithmetic. Because "all Pot of Gold wagers lose to a
    dealer blackjack" (NV rules of play), P(lose) is identical under peek and
    no-peek conventions: 1 - P(eligible) + P(eligible AND dealer natural).

    Wizard of Odds' simulated table (fetched 2026-07-18) publishes
    P(0) = 0.833420 for six decks — irreconcilable with this arithmetic under
    the stated rules (exact: 0.838228); see docs/EXPERIMENTS.md E19 for the
    reconciliation hypothesis (their sim appears to let lammers survive
    ten-up dealer blackjacks).
    """
    from fractions import Fraction

    copies = {r: (16 if r == 10 else 4) * rules.decks for r in range(1, 11)}
    total = 52 * rules.decks

    def p_seq(cards):
        seen: dict[int, int] = {}
        p = Fraction(1)
        left = total
        for c in cards:
            p *= Fraction(copies[c] - seen.get(c, 0), left)
            seen[c] = seen.get(c, 0) + 1
            left -= 1
        return p

    def eligible(c1, c2):
        if c1 == c2 and c1 in rules.free_split_ranks:
            return True
        soft = c1 == 1 or c2 == 1
        if soft and not rules.free_double_soft_allowed:
            return False
        return (c1 + c2) in rules.free_double_totals

    p_elig = Fraction(0)
    p_elig_bj = Fraction(0)
    for c1 in range(1, 11):
        for c2 in range(1, 11):
            if not eligible(c1, c2):
                continue
            p_elig += p_seq([c1, c2])
            for up, hole in ((1, 10), (10, 1)):
                p_elig_bj += p_seq([c1, c2, up, hole])
    return float(1 - p_elig + p_elig_bj)


def settle_pot_of_gold(
    paytable: tuple[float, ...], tokens: int, stake: float
) -> float:
    """Profit of a staked Pot of Gold bet settled on `tokens` free-bet lammers.

    Paytable entry [k-1] pays exactly k lammers; a count past the top rung pays
    the top rung (data semantics — unreachable when max_hands caps lammers at
    the rung count); zero lammers loses the stake. Rounds the player never acts
    in (dealer blackjack, player natural) settle here as tokens=0, matching the
    NV rules of play ("all Pot of Gold wagers lose to a dealer blackjack")."""
    if tokens <= 0:
        return -stake
    return paytable[min(tokens, len(paytable)) - 1] * stake


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
