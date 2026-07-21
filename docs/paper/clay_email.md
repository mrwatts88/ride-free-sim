# Cover email to Alexander Clay — framing notes

> **The email body itself lives in `clay_email.txt`** (plain text, the send version — Markdown
> doesn't render in Gmail). This file holds only the rationale and reminders, so there's no
> duplicated body to drift.

**To:** ajclay@usc.edu
**Subject:** A possible proof of your Conjecture 3 (m-shelf card guessing)
**Attach:** `main.pdf`

### Framing decisions (2026-07-20)
- **Honest about the division of labor.** Matt built the simulator, directed the investigation,
  and owns the computational verification (defensible); the AI developed the analytic proof (not
  personally defensible). Front-loaded, not back-loaded: "software developer, not a
  mathematician" is the first sentence, and the body splits "what I can / can't vouch for."
- **Subject line keeps "AI" out** (avoids a reflexive "AI slop" delete); the disclosure is the
  first sentence of the body instead.
- **Tone: outreach, not submission.** Authorship/venue undecided pending his reply (see
  `docs/GUESSING_THEOREM.md` §WRITE-UP & OUTREACH PLAN). If he's interested, a Clay
  co-authorship / arXiv endorsement is the best outcome.
- **Punctuation:** no em-dashes (Matt's preference; they read as an AI tell). Math minus signs
  kept.
- **Salutation: "Dear Alexander Clay,"** — NOT "Professor" or "Dr." Verified 2026-07-20: Clay is
  a PhD *candidate* at USC (started Fall 2022; advisor Jason Fulman, the "F" in DFH; BA Notre
  Dame 2022), not faculty and not yet a doctor. Full-name salutation avoids any wrong title or
  gender assumption; "Dear Alexander," (first name) is an acceptable warmer alternative.
  Homepage: sites.google.com/usc.edu/alexanderclay/.

### If he asks for the verification code
The probes are `data/gt_*.py` and the test pins in `tests/test_guessing_theorem.py`; we can
package a minimal standalone script (block-model enumeration + the four-bin decomposition) if
useful.
