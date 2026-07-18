"""SQLite persistence: every decision of every session, plus lifetime rollups.

One database (default data/trainer.db), two tables. `events` holds every scored
decision (bet / play / insurance / leave / count) with its full context JSON, so
new lifetime views are queries, not schema changes. `sessions` carries the
per-session rollup and is updated as the session runs, so a killed server loses
nothing but the final timestamp.
"""

import json
import sqlite3
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    started_at REAL NOT NULL,
    ended_at REAL,
    seed INTEGER NOT NULL,
    card TEXT NOT NULL,
    rounds INTEGER NOT NULL DEFAULT 0,
    shoes INTEGER NOT NULL DEFAULT 0,
    net REAL NOT NULL DEFAULT 0,
    wagered REAL NOT NULL DEFAULT 0,
    decisions INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    ts REAL NOT NULL,
    round_no INTEGER NOT NULL,
    shoe_no INTEGER NOT NULL,
    kind TEXT NOT NULL,
    correct INTEGER,
    expected TEXT NOT NULL,
    got TEXT NOT NULL,
    context TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind, correct);
"""


class Store:
    def __init__(self, path: str) -> None:
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(_SCHEMA)
        # 2026-07-18 migrations: profit^2 (winner-probability variance) and
        # active playing time (pace). Older sessions keep 0 and are excluded
        # from the respective lifetime estimates.
        for column in ("profit_sq", "active_seconds"):
            try:
                self.db.execute(
                    f"ALTER TABLE sessions ADD COLUMN {column} REAL NOT NULL DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass  # column already exists
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def start_session(self, seed: int, card: str, started_at: float) -> int:
        cur = self.db.execute(
            "INSERT INTO sessions (started_at, seed, card) VALUES (?, ?, ?)",
            (started_at, seed, card),
        )
        self.db.commit()
        return cur.lastrowid

    def log_event(self, session_id: int, event) -> None:
        self.db.execute(
            "INSERT INTO events (session_id, ts, round_no, shoe_no, kind, correct,"
            " expected, got, context) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                event.ts,
                event.round_no,
                event.shoe_no,
                event.kind,
                None if event.correct is None else int(event.correct),
                event.expected,
                event.got,
                json.dumps(event.context),
            ),
        )
        self.db.commit()

    def update_session(self, session_id: int, session, ended: bool = False) -> None:
        decisions = sum(a for a, _ in session.tally.values())
        errors = sum(e for _, e in session.tally.values())
        self.db.execute(
            "UPDATE sessions SET rounds = ?, shoes = ?, net = ?, wagered = ?,"
            " decisions = ?, errors = ?, profit_sq = ?, active_seconds = ?,"
            " ended_at = ? WHERE id = ?",
            (
                session.round_no,
                session.shoe_no,
                session.net,
                session.wagered,
                decisions,
                errors,
                session.profit_sq,
                session.active_seconds,
                time.time() if ended else None,
                session_id,
            ),
        )
        self.db.commit()

    # ---- lifetime stats -----------------------------------------------------

    def lifetime(self) -> dict:
        db = self.db
        totals = db.execute(
            "SELECT COUNT(*), COALESCE(SUM(rounds), 0), COALESCE(SUM(net), 0),"
            " COALESCE(SUM(wagered), 0), COALESCE(SUM(decisions), 0),"
            " COALESCE(SUM(errors), 0) FROM sessions"
        ).fetchone()
        by_kind = [
            {"kind": k, "attempts": n, "errors": e}
            for k, n, e in db.execute(
                "SELECT kind, COUNT(*), COALESCE(SUM(correct = 0), 0) FROM events"
                " WHERE correct IS NOT NULL GROUP BY kind ORDER BY kind"
            )
        ]
        play_situations = [
            {"situation": s, "attempts": n, "errors": e}
            for s, n, e in db.execute(
                "SELECT json_extract(context, '$.situation'), COUNT(*),"
                " COALESCE(SUM(correct = 0), 0) FROM events WHERE kind = 'play'"
                " GROUP BY 1 HAVING SUM(correct = 0) > 0"
                " ORDER BY SUM(correct = 0) DESC, COUNT(*) DESC LIMIT 15"
            )
        ]
        play_mistakes = [
            {"situation": s, "expected": ex, "got": g, "n": n}
            for s, ex, g, n in db.execute(
                "SELECT json_extract(context, '$.situation'), expected, got, COUNT(*)"
                " FROM events WHERE kind = 'play' AND correct = 0"
                " GROUP BY 1, 2, 3 ORDER BY COUNT(*) DESC LIMIT 15"
            )
        ]
        count_deltas = [
            {"delta": d, "n": n}
            for d, n in db.execute(
                "SELECT CAST(json_extract(context, '$.delta') AS INTEGER), COUNT(*)"
                " FROM events WHERE kind = 'count' GROUP BY 1 ORDER BY 1"
            )
        ]
        bet_mistakes = [
            {"expected": ex, "got": g, "n": n}
            for ex, g, n in db.execute(
                "SELECT expected, got, COUNT(*) FROM events"
                " WHERE kind = 'bet' AND correct = 0"
                " GROUP BY 1, 2 ORDER BY COUNT(*) DESC LIMIT 10"
            )
        ]
        recent_sessions = [
            {
                "id": sid,
                "started_at": started,
                "rounds": rounds,
                "net": net,
                "decisions": decisions,
                "errors": errors,
                "active_seconds": active,
            }
            for sid, started, rounds, net, decisions, errors, active in db.execute(
                "SELECT id, started_at, rounds, net, decisions, errors,"
                " active_seconds FROM sessions ORDER BY started_at DESC LIMIT 20"
            )
        ]
        # Variance inputs from sessions that recorded profit^2 (post-migration);
        # the winner panel falls back to the certified sigma when this is thin.
        var_rounds, var_net, var_p2 = db.execute(
            "SELECT COALESCE(SUM(rounds), 0), COALESCE(SUM(net), 0),"
            " COALESCE(SUM(profit_sq), 0) FROM sessions WHERE profit_sq > 0"
        ).fetchone()
        return {
            "sessions": totals[0],
            "rounds": totals[1],
            "net": totals[2],
            "wagered": totals[3],
            "decisions": totals[4],
            "errors": totals[5],
            "variance_sample": {
                "rounds": var_rounds,
                "net": var_net,
                "profit_sq": var_p2,
            },
            "pace": dict(
                zip(
                    ("rounds", "seconds"),
                    db.execute(
                        "SELECT COALESCE(SUM(rounds), 0),"
                        " COALESCE(SUM(active_seconds), 0) FROM sessions"
                        " WHERE active_seconds > 0"
                    ).fetchone(),
                )
            ),
            "by_kind": by_kind,
            "play_situations": play_situations,
            "play_mistakes": play_mistakes,
            "count_deltas": count_deltas,
            "bet_mistakes": bet_mistakes,
            "recent_sessions": recent_sessions,
        }
