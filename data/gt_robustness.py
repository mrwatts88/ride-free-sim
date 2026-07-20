"""Robustness check (experiment **E35**): is E_opt a real maximum, or an artifact?

Score DFH's ShelfGuesser AND two deliberately-suboptimal deterministic
strategies exactly (sum_perm P(perm)*correct), and compare to the trie E_opt.
If E_opt is genuine, the weak strategies must fall STRICTLY below it while DFH
ties it — ruling out a "scoring the same thing twice" bug.

`e_opt_exact` here is a DELIBERATELY INDEPENDENT re-implementation of the
prefix-trie value in `ridefree.guessing_theorem` (a second pair of eyes on the
exact computation); it is not imported on purpose. See docs/GUESSING_THEOREM.md.
"""

from fractions import Fraction
from itertools import permutations

from ridefree.forensics import ShelfGuesser, shelf_class_prob, valleys, uniform_guessing_mean


class AlwaysSmallest:
    """Ignore all order structure: always guess the smallest unseen card.
    On a uniform deck this scores H_n; it should badly trail on structured decks."""

    def __init__(self, n):
        self.avail = list(range(1, n + 1))

    def guess(self):
        return self.avail[0]

    def observe(self, card):
        if card in self.avail:
            self.avail.remove(card)


class UpOnly:
    """Nearest unseen strictly ABOVE the last shown card (wrap to smallest);
    a plausible but suboptimal rule that never reverses direction."""

    def __init__(self, n):
        self.avail = list(range(1, n + 1))
        self.prev = 0

    def guess(self):
        for c in self.avail:
            if c > self.prev:
                return c
        return self.avail[0]

    def observe(self, card):
        if card in self.avail:
            self.avail.remove(card)
        self.prev = card


def score_exact(n, m, perms, factory):
    tot = Fraction(0)
    for perm, p in perms:
        g = factory(n)
        c = 0
        for card in perm:
            if g.guess() == card:
                c += 1
            g.observe(card)
        tot += p * c
    return tot


def e_opt_exact(n, m, perms):
    mass = {}
    zero = Fraction(0)
    for perm, p in perms:
        for t in range(1, n + 1):
            key = perm[:t]
            mass[key] = mass.get(key, zero) + p
    best = {}
    for key, mval in mass.items():
        parent = key[:-1]
        if parent not in best or mval > best[parent]:
            best[parent] = mval
    return sum(best.values(), zero)


def main():
    n = 7
    print(f"strict-inequality check at n={n}  (H_n={uniform_guessing_mean(n):.4f})")
    print(f"{'m':>3} | {'E_opt':>9} {'DFH':>9} {'UpOnly':>9} {'Smallest':>9}  DFH==opt?")
    for m in (1, 2, 3, 5, 10):
        perms = [
            (perm, shelf_class_prob(n, m, valleys(perm)))
            for perm in permutations(range(1, n + 1))
        ]
        eo = e_opt_exact(n, m, perms)
        edfh = score_exact(n, m, perms, ShelfGuesser)
        eup = score_exact(n, m, perms, UpOnly)
        esm = score_exact(n, m, perms, AlwaysSmallest)
        print(
            f"{m:>3} | {float(eo):9.5f} {float(edfh):9.5f} {float(eup):9.5f} "
            f"{float(esm):9.5f}  {edfh == eo} "
            f"(opt-up={float(eo-eup):.4f}, opt-sm={float(eo-esm):.4f})"
        )


if __name__ == "__main__":
    main()
