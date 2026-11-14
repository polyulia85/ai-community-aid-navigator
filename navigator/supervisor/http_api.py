"""Local HTTP API for the dialog mode (Supervisor v0.2.5, Session B).

Endpoints:
  GET  /health                       -> {"status": "ok", "dialog_version": "0.2"}
  POST /start   {story_text, ref_date?}
  POST /answer  {case, answers}
  POST /confirm {case, corrections?, rejected_need_ids?, added_needs?}

Each POST returns the dialog response with HTTP 200 (even on status "failed").
Body > 64 KB -> 413.  Not JSON or not an object -> 400 with BAD_REQUEST issue.
Unknown path -> 404.  Wrong method -> 405.  No stack trace in any response.

Usage:
  python -m navigator.supervisor.http_api [--host 127.0.0.1] [--port 8765]
      [--agents agents.json] [--kb PATH] [--zips PATH] [--no-isolate]
      [--allow-origin ORIGIN]

Standard library only.  Python 3.11+.
"""
import argparse
import http.server
import json
import sys
import threading
from http import HTTPStatus

from navigator.supervisor import dialog as D
from navigator.supervisor import run as R

DIALOG_VERSION = D.DIALOG_VERSION
_MAX_BODY = 64 * 1024   # 64 KB

_BAD_REQUEST_RESPONSE = {
    "status": "failed",
    "issues": [
        {
            "code":        "BAD_REQUEST",
            "severity":    "critical",
            "message":     "Request body must be a JSON object",
            "related_ref": None,
        }
    ],
}

_POST_PATHS = {"/start", "/answer", "/confirm"}


class _DialogHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the dialog API.

    Server attributes used:
        agents, kb_path, zips_path, isolate, allow_origin
    """

    # --- logging: only method, path, status (no body) ---

    def log_message(self, fmt, *args):
        # args[0] is "METHOD /path HTTP/1.1", args[1] status code, args[2] size
        # We print only method, path, status.
        try:
            request_line = args[0]
            status_code  = args[1]
            parts = request_line.split()
            method = parts[0] if parts else "-"
            path   = parts[1] if len(parts) > 1 else "-"
        except Exception:
            method = path = "-"
            status_code = "-"
        print(f"{method} {path} {status_code}", flush=True)

    # --- helpers ---

    def _send_json(self, code, body):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        origin = getattr(self.server, "allow_origin", None)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.end_headers()
        self.wfile.write(payload)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",
                         self.server.allow_origin)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _read_json_body(self):
        """Read and parse the request body.

        Returns (data, error_code) where error_code is None on success,
        413 for oversized body, or 400 for bad JSON / non-object.
        """
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            return None, HTTPStatus.BAD_REQUEST
        if length < 0:
            return None, HTTPStatus.BAD_REQUEST
        if length > _MAX_BODY:
            return None, HTTPStatus.REQUEST_ENTITY_TOO_LARGE
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, HTTPStatus.BAD_REQUEST
        if not isinstance(data, dict):
            return None, HTTPStatus.BAD_REQUEST
        return data, None

    # --- dispatch ---

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok",
                                   "dialog_version": DIALOG_VERSION})
        elif self.path in _POST_PATHS:
            self._handle_unknown_method()
        else:
            self._send_json(404, {"status": "failed",
                                   "issues": [{"code": "NOT_FOUND",
                                               "severity": "critical",
                                               "message": "Unknown path",
                                               "related_ref": None}]})

    def do_OPTIONS(self):
        origin = getattr(self.server, "allow_origin", None)
        if origin and self.path in _POST_PATHS:
            self.send_response(204)
            self._cors_headers()
            self.end_headers()
        else:
            self._send_json(405, {"status": "failed",
                                   "issues": [{"code": "METHOD_NOT_ALLOWED",
                                               "severity": "critical",
                                               "message": "Method not allowed",
                                               "related_ref": None}]})

    def do_POST(self):
        if self.path not in _POST_PATHS:
            self._send_json(404, {"status": "failed",
                                   "issues": [{"code": "NOT_FOUND",
                                               "severity": "critical",
                                               "message": "Unknown path",
                                               "related_ref": None}]})
            return

        data, err = self._read_json_body()
        if err == HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
            self._send_json(413, {"status": "failed",
                                   "issues": [{"code": "REQUEST_TOO_LARGE",
                                               "severity": "critical",
                                               "message": "Request body exceeds 64 KB",
                                               "related_ref": None}]})
            return
        if err == HTTPStatus.BAD_REQUEST:
            self._send_json(400, _BAD_REQUEST_RESPONSE)
            return

        kw = dict(agents=self.server.agents,
                  kb_path=self.server.kb_path,
                  zips_path=self.server.zips_path,
                  isolate=self.server.isolate)

        try:
            if self.path == "/start":
                resp = D.start(
                    story_text=data.get("story_text", ""),
                    ref_date=data.get("ref_date"),
                    **kw,
                )
            elif self.path == "/answer":
                resp = D.answer(
                    case=data.get("case"),
                    answers=data.get("answers"),
                    **kw,
                )
            else:  # /confirm
                resp = D.confirm(
                    case=data.get("case"),
                    corrections=data.get("corrections"),
                    rejected_need_ids=data.get("rejected_need_ids"),
                    added_needs=data.get("added_needs"),
                    **kw,
                )
        except Exception:
            # Safety net: never expose a stack trace
            resp = D._failed(None, [{"code": "INTERNAL_ERROR", "severity": "critical",
                                     "message": "An unexpected error occurred",
                                     "related_ref": None}])

        self._send_json(200, resp)

    def _handle_unknown_method(self):
        self._send_json(405, {"status": "failed",
                               "issues": [{"code": "METHOD_NOT_ALLOWED",
                                           "severity": "critical",
                                           "message": "Method not allowed",
                                           "related_ref": None}]})

    def do_PUT(self):    self._handle_unknown_method()
    def do_DELETE(self): self._handle_unknown_method()
    def do_PATCH(self):  self._handle_unknown_method()
    def do_HEAD(self):   self._handle_unknown_method()


class _DialogServer(http.server.ThreadingHTTPServer):
    """ThreadingHTTPServer augmented with dialog configuration."""

    def __init__(self, server_address, handler_class,
                 agents, kb_path, zips_path, isolate, allow_origin):
        super().__init__(server_address, handler_class)
        self.agents      = agents
        self.kb_path     = kb_path
        self.zips_path   = zips_path
        self.isolate     = isolate
        self.allow_origin = allow_origin


def make_server(host="127.0.0.1", port=8765,
                agents=None, kb_path=None, zips_path=None,
                isolate=True, allow_origin=None):
    """Create and return a configured _DialogServer (not yet started).

    Pass agents=<dict> and port=0 in tests (port 0 → OS assigns a free port).
    """
    return _DialogServer(
        (host, port),
        _DialogHandler,
        agents=agents,
        kb_path=kb_path,
        zips_path=zips_path,
        isolate=isolate,
        allow_origin=allow_origin,
    )


def main(argv=None):
    """Entry point: python -m navigator.supervisor.http_api"""
    ap = argparse.ArgumentParser(description="Dialog local HTTP API")
    ap.add_argument("--host",         default="127.0.0.1")
    ap.add_argument("--port",         default=8765, type=int)
    ap.add_argument("--agents",       default=None, metavar="PATH")
    ap.add_argument("--kb",           default=None, metavar="PATH")
    ap.add_argument("--zips",         default=None, metavar="PATH")
    ap.add_argument("--no-isolate",   action="store_true")
    ap.add_argument("--allow-origin", default=None, metavar="ORIGIN",
                    help="Exact origin for Access-Control-Allow-Origin")
    a = ap.parse_args(argv)

    agents = None
    if a.agents:
        try:
            agents = R.load_agents(a.agents)
        except R.AgentConfigError as exc:
            print(f"Cannot load agents: {exc}")
            return 2

    server = make_server(
        host=a.host,
        port=a.port,
        agents=agents,
        kb_path=a.kb,
        zips_path=a.zips,
        isolate=not a.no_isolate,
        allow_origin=a.allow_origin,
    )
    host, port = server.server_address
    print(f"Listening on http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
