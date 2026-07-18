"""Server layer: TrainerApp routing/validation plus one live HTTP smoke test."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from ridefree.trainer.server import TrainerApp, make_handler


def test_app_flow(tmp_path):
    app = TrainerApp(str(tmp_path / "t.db"))
    status, state = app.new_session({"seed": 424344})
    assert status == 200 and state["phase"] == "bet"
    assert state["card"]["name"] == "crouch15-2r"

    status, state = app.bet({"amount": 5})
    assert status == 400  # below the table minimum

    status, state = app.bet({"amount": 15})
    assert status == 200
    assert state["feedback"][0]["kind"] in ("bet", "leave")
    assert state["phase"] in ("bet", "insurance", "action")

    status, state = app.peek()
    assert status == 200 and isinstance(state["peek_rc"], int)

    status, summary = app.end_session()
    assert status == 200 and summary["rounds"] == 1

    status, stats = app.stats()
    assert status == 200 and stats["sessions"] == 1


def test_http_smoke(tmp_path):
    app = TrainerApp(str(tmp_path / "t.db"), default_seed=555)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        def call(path, body=None):
            if body is None:
                req = urllib.request.Request(f"http://127.0.0.1:{port}{path}")
            else:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}{path}",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"},
                )
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())

        status, page = 200, urllib.request.urlopen(
            f"http://127.0.0.1:{port}/"
        ).read()
        assert b"crouch15" in page.lower() or b"trainer" in page.lower()

        status, state = call("/api/state")
        assert status == 200 and state["phase"] == "none"

        status, state = call("/api/session/new", {})
        assert status == 200 and state["phase"] == "bet"

        status, state = call("/api/bet", {"amount": 15})
        assert status == 200 and state["round_no"] == 1

        status, stats = call("/api/stats")
        assert status == 200 and stats["sessions"] == 1
    finally:
        httpd.shutdown()
        httpd.server_close()
