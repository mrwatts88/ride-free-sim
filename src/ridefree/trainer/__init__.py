"""Live-play trainer for the chosen blackjack attack (docs/ARTICLE_BLACKJACK.md).

A localhost web app that deals the exact game (STANDARD_6D_H17, cut-card pen .75)
through the validated engine and checks every human decision against the crouch15
Red 7 card: bet sizing, basic strategy, insurance, the leave threshold, and the
running count itself. The engine is reused untouched (driver.py replays
`play_round` against the deterministic shoe); the play oracle is the same
`BasicStrategy` object the published-edge gates validated.
"""
