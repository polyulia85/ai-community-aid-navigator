"""Tests for Step 3: local HTTP API (Supervisor v0.2.5, Session B).

Run from the repo root:  python -m unittest tests.test_dialog_b_step3 -v
Server starts on port 0 (OS picks a free port) in a daemon thread.
Uses fake agents and isolate=False.
"""
import json
import threading
import unittest
import urllib.error
from unittest import mock
import urllib.request

from navigator.supervisor import dialog as D
from navigator.supervisor.http_api import make_server
from tests.fake_agents import (
    FIXTURE_KB, FIXTURE_ZIPS,
    agent_1_dialog, agent_2_dialog, agent_3_dialog,
    agent_4, agent_5, agent_6, agent_8, agent_10_pass,
)

STORY = "I need help with housing and food."

_AGENTS = {
    "agent_1":  agent_1_dialog,
    "agent_2":  agent_2_dialog,
    "agent_3":  agent_3_dialog,
    "agent_4":  agent_4,
    "agent_5":  agent_5,
    "agent_6":  agent_6,
    "agent_8":  agent_8,
    "agent_10": agent_10_pass,
}


def _post(url, body):
    """POST a dict as JSON; return (status_code, response_dict)."""
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def _get(url, headers=None):
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def _request(url, method, body=None, headers=None):
    headers = headers or {}
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        payload = None
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


class TestHttpAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = make_server(
            host="127.0.0.1", port=0,
            agents=_AGENTS,
            kb_path=FIXTURE_KB,
            zips_path=FIXTURE_ZIPS,
            isolate=False,
            allow_origin=None,
        )
        _, cls.port = cls.server.server_address
        cls.base = f"http://127.0.0.1:{cls.port}"
        t = threading.Thread(target=cls.server.serve_forever, daemon=True)
        t.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    # --- /health ---

    def test_health(self):
        code, body = _get(f"{self.base}/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["dialog_version"], "0.2")

    # --- /start ---

    def test_start_returns_200(self):
        code, body = _post(f"{self.base}/start",
                           {"story_text": STORY, "ref_date": "2026-11-15"})
        self.assertEqual(code, 200)
        self.assertIn("status", body)
        self.assertIn("dialog_version", body)

    # --- full start → answer → confirm ---

    def _drive_to_confirmation(self, start_resp):
        """Skip all questions until needs_confirmation."""
        resp = start_resp
        for _ in range(10):
            if resp.get("status") != "needs_clarification":
                break
            answers = [{"question_id": q["question_id"], "skipped": True} if q["can_skip"]
                       else {"question_id": q["question_id"], "answer_text": "0"}
                       for q in resp.get("questions", [])]
            _, resp = _post(f"{self.base}/answer",
                            {"case": resp["case"], "answers": answers})
        return resp

    def test_full_start_answer_confirm(self):
        _, start_resp = _post(f"{self.base}/start",
                              {"story_text": STORY, "ref_date": "2026-11-15"})
        conf_input = self._drive_to_confirmation(start_resp)
        self.assertEqual(conf_input.get("status"), "needs_confirmation")

        _, conf_resp = _post(f"{self.base}/confirm", {"case": conf_input["case"]})
        self.assertEqual(conf_resp.get("status"), "completed")
        self.assertTrue(conf_resp["plan"]["action_cards"])
        self.assertEqual(conf_resp["dialog_version"], "0.2")

    # --- error cases ---

    def test_400_non_json_body(self):
        req = urllib.request.Request(
            f"{self.base}/start",
            data=b"not json",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as r:
                code, body = r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            code, body = e.code, json.loads(e.read())
        self.assertEqual(code, 400)
        self.assertEqual(body["status"], "failed")
        codes = [i["code"] for i in body.get("issues", [])]
        self.assertIn("BAD_REQUEST", codes)

    def test_400_json_array_not_object(self):
        """A JSON array body is not an object → 400 BAD_REQUEST."""
        payload = json.dumps([1, 2, 3]).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base}/start",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as r:
                code, body = r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            code, body = e.code, json.loads(e.read())
        self.assertEqual(code, 400)

    def test_404_unknown_path(self):
        code, body = _get(f"{self.base}/unknown_endpoint")
        self.assertEqual(code, 404)

    def test_404_post_unknown_path(self):
        code, body = _post(f"{self.base}/unknown_endpoint", {"x": 1})
        self.assertEqual(code, 404)

    def test_405_get_on_post_path(self):
        code, body = _get(f"{self.base}/start")
        self.assertEqual(code, 405)

    def test_400_bad_content_length(self):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.putrequest("POST", "/start")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", "abc")
            conn.endheaders()
            resp = conn.getresponse()
            self.assertEqual(resp.status, 400)
            self.assertEqual(json.loads(resp.read())["status"], "failed")
        finally:
            conn.close()

    def test_413_oversized_body(self):
        big = "x" * (65 * 1024)
        payload = json.dumps({"story_text": big}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base}/start",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as r:
                code, body = r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            code, body = e.code, json.loads(e.read())
        self.assertEqual(code, 413)

    def test_start_passes_locale(self):
        with mock.patch.object(D, "start", wraps=D.start) as spy:
            code, body = _post(f"{self.base}/start",
                               {"story_text": STORY, "ref_date": "2026-11-15", "locale": "es-US"})
        self.assertEqual(code, 200)
        self.assertNotEqual(body["status"], "failed")
        self.assertEqual(spy.call_args.kwargs["locale"], "es-US")

    def test_start_bad_locale_is_failed_200(self):
        code, body = _post(f"{self.base}/start", {"story_text": STORY, "locale": 123})
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "failed")
        self.assertEqual([i["code"] for i in body["issues"]], ["LOCALE_INVALID"])

    def test_failed_status_still_200(self):
        """A 'failed' dialog response (bad case) is still HTTP 200."""
        code, body = _post(f"{self.base}/confirm", {"case": None})
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "failed")

    # --- no CORS header when allow_origin not set ---

    def test_no_cors_header_without_allow_origin(self):
        req = urllib.request.Request(
            f"{self.base}/health",
            method="GET",
        )
        with urllib.request.urlopen(req) as resp:
            headers = dict(resp.headers)
        # Key lookup is case-insensitive in http.client
        self.assertNotIn("access-control-allow-origin", {k.lower() for k in headers})


class TestHttpAPICORS(unittest.TestCase):
    """Separate server instance with allow_origin set."""

    @classmethod
    def setUpClass(cls):
        cls.server = make_server(
            host="127.0.0.1", port=0,
            agents=_AGENTS,
            kb_path=FIXTURE_KB,
            zips_path=FIXTURE_ZIPS,
            isolate=False,
            allow_origin="https://example.com",
        )
        _, cls.port = cls.server.server_address
        cls.base = f"http://127.0.0.1:{cls.port}"
        t = threading.Thread(target=cls.server.serve_forever, daemon=True)
        t.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_cors_header_present_on_post(self):
        payload = json.dumps({"story_text": STORY}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base}/start",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
        self.assertIn("access-control-allow-origin", headers)
        self.assertEqual(headers["access-control-allow-origin"], "https://example.com")

    def test_options_reply_on_post_path(self):
        req = urllib.request.Request(
            f"{self.base}/start",
            method="OPTIONS",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                code = resp.status
                headers = {k.lower(): v for k, v in resp.headers.items()}
        except urllib.error.HTTPError as e:
            code = e.code
            headers = {}
        self.assertEqual(code, 204)
        self.assertIn("access-control-allow-origin", headers)

    def test_cors_header_on_health_get(self):
        req = urllib.request.Request(f"{self.base}/health", method="GET")
        with urllib.request.urlopen(req) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
        self.assertIn("access-control-allow-origin", headers)
        self.assertEqual(headers["access-control-allow-origin"], "https://example.com")


if __name__ == "__main__":
    unittest.main()
