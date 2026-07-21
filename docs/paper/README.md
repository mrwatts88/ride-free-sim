# Paper 1 — the focused theorem (m-shelf card-guessing value law)

The self-contained math paper proving the value half of Clay's Conjecture 3 for all m:
slope (E41) + fade rate (E42) + exact intercept (E44). See `docs/GUESSING_THEOREM.md`
§CLAIM BOUNDARY and §WRITE-UP & OUTREACH PLAN for the scope and the outreach decision, and
`docs/EXPERIMENTS.md` E41/E42/E44 for the underlying experiments.

## Files
- `main.tex` — the paper source (LaTeX).
- `main.pdf` — compiled, 9 pages.
- `clay_email.md` — the separate cover email to Alexander Clay (ajclay@usc.edu), outreach
  framing, honest AI + claim-boundary disclosure.

## Build
Requires [tectonic](https://tectonic-typesetting.github.io/) (`brew install tectonic`):

```
cd docs/paper && tectonic main.tex
```

Tectonic auto-downloads packages on first run; no separate TeX install needed.

## Status
Draft for outreach to Clay first; authorship/venue deliberately left open pending his read.
Machine-verification for every identity lives in `data/gt_s_excess.py`,
`data/gt_hit_formula.py`, `data/gt_slope_proof.py`, `data/gt_fade_intercept.py`, and the pins
in `tests/test_guessing_theorem.py`.

## Known rigor gap — expand before FORMAL submission (fine for outreach)
§6 (the exact intercept) is written at preprint rigor: the arguments are complete and every
identity is machine-verified, but the limit-exchange steps are *stated* rather than fully
ε-managed. Specifically:
- §6.3 (`onC`): "as n→∞ this vanishes whenever c_d > 0 … only d=1 survives" — needs an
  explicit dominated-convergence / geometric-tail bound.
- §6.4–6.6 (`offC`, `onE`, `offE`): "O(1) distinguished cards", "conditioning on all blocks
  nonempty is exact in the limit", "remaining configurations have vanishing probability" —
  each needs a written bound. All are controlled by geometric tails (block-emptiness is
  O((1−1/2m)ⁿ); the dominant competing-hypothesis / survival tail is the O(n²(1−1/m)ⁿ) of §5),
  so the machinery is in hand; it just isn't spelled out.

A referee will push here. Not required for the Clay outreach draft; required before a journal
submission. (Banked at Matt's request, 2026-07-20.)

**This is DIFFERENT IN KIND from the remainder correction** (the n² fix): the remainder was a
literal error (a false statement), now fixed; this is an under-rigor gap (true statements, not
fully ε-managed). And per the independent review: writing these tail bounds out rigorously
reproduces the *corrected* O(n²(1−1/m)ⁿ) remainder — so the rigor gap and the remainder fix are
consistent, not competing.
