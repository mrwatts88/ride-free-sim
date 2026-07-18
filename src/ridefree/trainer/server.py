"""Stdlib HTTP server: static frontend + JSON API over one TrainerSession.

No frameworks, no dependencies (matching the repo). ThreadingHTTPServer with a
single lock around all session/store access — the app is one human clicking,
concurrency exists only so static files and API calls never block each other.
"""

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

from ridefree.engine import Action
from ridefree.rules import STANDARD_6D_H17
from ridefree.trainer.card import (
    CARDS,
    CERTIFIED_EV_PER_ROUND,
    CERTIFIED_ROUNDS_PER_HOUR,
    CERTIFIED_SIGMA_PER_ROUND,
    DEFAULT_CARD,
)
from ridefree.trainer.session import Config, SessionError, TrainerSession
from ridefree.trainer.store import Store

_STATIC = Path(__file__).parent / "static"
_MIME = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}

_ACTIONS = {a.value: a for a in Action}


class TrainerApp:
    """Session + store behind one lock; the handler delegates everything here."""

    def __init__(self, db_path: str, default_seed: int | None = None) -> None:
        self.store = Store(db_path)
        self.lock = Lock()
        self.session: TrainerSession | None = None
        self.session_id: int | None = None
        self.default_seed = default_seed

    # Every public method returns (http_status, json_payload).

    def new_session(self, body: dict) -> tuple[int, dict]:
        if self.session is not None:
            self._finalize()
        seed = body.get("seed")
        if seed is None:
            seed = self.default_seed if self.default_seed is not None else int(time.time())
        card = CARDS.get(body.get("card", DEFAULT_CARD.name))
        if card is None:
            return 400, {"error": f"unknown card {body.get('card')!r}"}
        session = TrainerSession(STANDARD_6D_H17, card, int(seed), Config())
        session_id = self.store.start_session(session.seed, card.name, session.started_at)
        session.on_event = lambda event: self.store.log_event(session_id, event)
        self.session, self.session_id = session, session_id
        return 200, session.state_json()

    def state(self) -> tuple[int, dict]:
        if self.session is None:
            return 200, {"phase": "none"}
        return 200, self.session.state_json()

    def bet(self, body: dict) -> tuple[int, dict]:
        session = self._require()
        amount = float(body["amount"])
        if not (session.card.floor_bet <= amount <= session.card.table_max):
            return 400, {
                "error": f"bet must be ${session.card.floor_bet:g}-${session.card.table_max:g}"
            }
        feedback = session.place_bet(amount)
        self.store.update_session(self.session_id, session)
        return 200, session.state_json(feedback)

    def leave(self) -> tuple[int, dict]:
        session = self._require()
        feedback = session.leave_table()
        return 200, session.state_json(feedback)

    def action(self, body: dict) -> tuple[int, dict]:
        session = self._require()
        action = _ACTIONS.get(body.get("action"))
        if action is None:
            return 400, {"error": f"unknown action {body.get('action')!r}"}
        feedback = session.answer_action(action)
        self.store.update_session(self.session_id, session)
        return 200, session.state_json(feedback)

    def insurance(self, body: dict) -> tuple[int, dict]:
        session = self._require()
        feedback = session.answer_insurance(bool(body["take"]))
        return 200, session.state_json(feedback)

    def count(self, body: dict) -> tuple[int, dict]:
        session = self._require()
        feedback = session.check_count(int(body["rc"]), on_demand=bool(body.get("on_demand")))
        return 200, session.state_json(feedback)

    def skip_quiz(self) -> tuple[int, dict]:
        session = self._require()
        session.skip_quiz()
        return 200, session.state_json()

    def peek(self) -> tuple[int, dict]:
        session = self._require()
        rc, _event = session.peek()
        state = session.state_json()
        state["peek_rc"] = rc
        return 200, state

    def config(self, body: dict) -> tuple[int, dict]:
        session = self._require()
        for key in ("quiz_on_shuffle", "reveal_on_error", "score_leave"):
            if key in body:
                setattr(session.config, key, bool(body[key]))
        if "random_quiz_mean_rounds" in body:
            session.config.random_quiz_mean_rounds = max(0, int(body["random_quiz_mean_rounds"]))
        return 200, session.state_json()

    def end_session(self) -> tuple[int, dict]:
        session = self._require()
        summary = session.end()
        self._finalize()
        return 200, summary

    def stats(self) -> tuple[int, dict]:
        data = self.store.lifetime()
        data["certified"] = {  # E18b operating numbers (see trainer/card.py)
            "ev_per_round": CERTIFIED_EV_PER_ROUND,
            "sigma_per_round": CERTIFIED_SIGMA_PER_ROUND,
            "rounds_per_hour": CERTIFIED_ROUNDS_PER_HOUR,
        }
        return 200, data

    def _finalize(self) -> None:
        if self.session is not None and self.session_id is not None:
            self.store.update_session(self.session_id, self.session, ended=True)
        self.session = None
        self.session_id = None

    def _require(self) -> TrainerSession:
        if self.session is None:
            raise SessionError("no active session")
        return self.session


def make_handler(app: TrainerApp):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the terminal quiet
            pass

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self._static("index.html")
            if self.path.startswith("/static/"):
                return self._static(self.path.removeprefix("/static/"))
            route = {
                "/api/state": app.state,
                "/api/stats": app.stats,
            }.get(self.path)
            if route is None:
                return self._json(404, {"error": "not found"})
            with app.lock:
                status, payload = route()
            self._json(status, payload)

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._json(400, {"error": "bad JSON"})
            route = {
                "/api/session/new": lambda: app.new_session(body),
                "/api/session/end": app.end_session,
                "/api/bet": lambda: app.bet(body),
                "/api/leave": app.leave,
                "/api/action": lambda: app.action(body),
                "/api/insurance": lambda: app.insurance(body),
                "/api/count": lambda: app.count(body),
                "/api/quiz/skip": app.skip_quiz,
                "/api/peek": app.peek,
                "/api/config": lambda: app.config(body),
            }.get(self.path)
            if route is None:
                return self._json(404, {"error": "not found"})
            try:
                with app.lock:
                    status, payload = route()
            except SessionError as err:
                return self._json(409, {"error": str(err)})
            except (KeyError, ValueError, TypeError) as err:
                return self._json(400, {"error": f"bad request: {err}"})
            self._json(status, payload)

        def _static(self, name: str):
            path = _STATIC / Path(name).name  # basename only: no traversal
            if not path.is_file():
                return self._json(404, {"error": "not found"})
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", _MIME.get(path.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _json(self, status: int, payload: dict):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve(port: int, db_path: str, seed: int | None = None) -> None:
    app = TrainerApp(db_path, default_seed=seed)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app))
    print(f"crouch15 trainer: http://127.0.0.1:{port}/  (db: {db_path})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        with app.lock:
            app._finalize()
        app.store.close()
        httpd.server_close()
