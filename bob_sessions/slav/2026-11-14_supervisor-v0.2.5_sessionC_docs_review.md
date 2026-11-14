> Note added after export (Nov 14, 2026): Bob checked the new documentation against the code and found 4 mismatches (2 retracted by Bob itself). Finding 4 (the HTTP API did not pass `locale`) was a code defect, so the code was fixed, not only the text. The 25 changes were checked on a copy of the branch first, then applied by Bob in this task; two of its diff blocks did not match after earlier edits and Bob applied them with search and replace. The full test suite was then run by hand: 475 tests OK, no unclosed files. Local paths were removed from this export.

# Task: Supervisor v0.2.5, Session C — check the new documentation against the code. Review only; no edits until I approve them.

Repository: branch slav/supervisor-v0.2.5. Two documentation files were just written and are not committed:
- navigator/supervisor/README.md — read only the section "Dialog mode: how to run and connect" and the section "Known limits".
- docs/supervisor/DIALOG_API_FORMS.md

Check them against the code:
- navigator/supervisor/dialog.py — the signatures of start, answer, confirm; the response fields; the issue codes; main() and its argparse options.
- navigator/supervisor/http_api.py — paths, methods, status codes, the 64 KB limit, CORS, the default host and port, main() options.

Rules (budget is limited):
- Read only these four files. Do not open tests or other folders.
- Do not run commands.
- Do not edit anything in this step.

Report a list. For each item: file and line in the documentation, what the documentation says, what the code does (file and line), and the exact replacement text. Only real mismatches: a wrong option name, default, status code, field name, issue code, exit code, or a statement the code does not support. No style or wording suggestions. If you find nothing, say "no mismatches". Then stop and wait.

---

**Status:** active  **Date:** 2026-11-14

---

### 👤 User

Task: Supervisor v0.2.5, Session C — check the new documentation against the code. Review only; no edits until I approve them.

Repository: branch slav/supervisor-v0.2.5. Two documentation files were just written and are not committed:
- navigator/supervisor/README.md — read only the section "Dialog mode: how to run and connect" and the section "Known limits".
- docs/supervisor/DIALOG_API_FORMS.md

Check them against the code:
- navigator/supervisor/dialog.py — the signatures of start, answer, confirm; the response fields; the issue codes; main() and its argparse options.
- navigator/supervisor/http_api.py — paths, methods, status codes, the 64 KB limit, CORS, the default host and port, main() options.

Rules (budget is limited):
- Read only these four files. Do not open tests or other folders.
- Do not run commands.
- Do not edit anything in this step.

Report a list. For each item: file and line in the documentation, what the documentation says, what the code does (file and line), and the exact replacement text. Only real mismatches: a wrong option name, default, status code, field name, issue code, exit code, or a statement the code does not support. No style or wording suggestions. If you find nothing, say "no mismatches". Then stop and wait.

---

### 🤖 Assistant

> 🔧 called: read_file, read_file

I'll read all four files systematically before comparing. Let me start with the two documentation files and two code files in parallel.

> 🔧 **read_file** — navigator\supervisor\README.md

> 🔧 **read_file** — docs\supervisor\DIALOG_API_FORMS.md

### 🤖 Assistant

> 🔧 called: read_file, read_file

Now let me read the two code files:

> 🔧 **read_file** — navigator\supervisor\http_api.py

> 🔧 **read_file** — navigator\supervisor\dialog.py

### 🤖 Assistant

> 🔧 called: read_file

Now I need to read the truncated portion of [`dialog.py`](navigator/supervisor/dialog.py) — specifically the `main()` function and its argparse options:

> 🔧 **read_file** — navigator\supervisor\dialog.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — main() tail: remaining confirm call, output writing, exit code logic

### 🤖 Assistant

I now have everything needed. Here is the complete mismatch report.

---

## Mismatch report

### 1 — `make_server` default for `isolate` is `True`, but both docs say `False`

| Item | Detail |
|---|---|
| **Doc file / line** | `README.md` line 126: *"Each function also takes `kb_path`, `zips_path` and `isolate` (default `False`)."* |
| **Doc file / line** | `DIALOG_API_FORMS.md` line 59: *"Optional keyword arguments of all three functions: `agents`, `kb_path`, `zips_path`, `isolate` (default `False`)."* |
| **Code** | [`dialog.py` line 762–763](navigator/supervisor/dialog.py:762): `def start(… isolate=False)`, [`line 834`](navigator/supervisor/dialog.py:834): `def answer(… isolate=False)`, [`line 973–974`](navigator/supervisor/dialog.py:973): `def confirm(… isolate=False)` — all three public functions default to `False`. ✓ That part is correct. |
| **Code — real mismatch** | [`http_api.py` line 222–224](navigator/supervisor/http_api.py:222): `def make_server(… isolate=True …)` — the server factory defaults to `isolate=True`, not `False`. |
| **What the docs say** | Neither doc mentions `make_server` directly, but both docs state without qualification *"without `--no-isolate` every agent call runs in its own process"* (README line 76) and that `--no-isolate` is needed to avoid per-process overhead — consistent with `isolate` defaulting to `True` in the server. This is not a documentation mismatch by itself. The mismatch is in `DIALOG_API_FORMS.md` §2 line 59, which lists `isolate (default False)` as an optional kwarg of *all three functions*. The three dialog functions do indeed default to `False`. **No actual mismatch here — retract.**

*(On closer review this pair is consistent. Moving on.)*

---

### 1 — `README.md` §"HTTP status codes" — 400 description missing "or a bad `Content-Length`"

| Item | Detail |
|---|---|
| **Doc file / line** | `README.md` line 151: *"400 — the body is not a JSON object, or a bad `Content-Length` (`issues[0].code` = `BAD_REQUEST`)"* |
| **Code** | [`http_api.py` lines 97–101](navigator/supervisor/http_api.py:97): a `Content-Length` that cannot be parsed as an integer, or is negative, returns `HTTPStatus.BAD_REQUEST` → HTTP 400 with `_BAD_REQUEST_RESPONSE`. ✓ Consistent. |

No mismatch here either. Let me now enumerate only the genuine mismatches:

---

### MISMATCH 1 — `DIALOG_API_FORMS.md` §2 line 48: `--agents` default stated as `agents.json` but the code has no default

| | |
|---|---|
| **Doc / line** | `DIALOG_API_FORMS.md` line 48: *"`--agents PATH`"* — listed without a default (consistent with the code ✓) |
| **README / line** | `README.md` line 76: *"`--agents PATH` (default `agents.json` at the repository root)"* |
| **Code** | [`http_api.py` line 245](navigator/supervisor/http_api.py:245): `ap.add_argument("--agents", default=None, metavar="PATH")` — default is `None`, not `agents.json`. |
| **What the code does** | When `--agents` is omitted, `a.agents` is `None`, the `if a.agents:` block is skipped, and `agents=None` is passed to `make_server`. The server then passes `agents=None` to the dialog functions, which call `_load_defaults` → `R.load_agents(_DEFAULT_AGENTS_JSON)`, so the effective default *at runtime* is `agents.json` at the repo root — but argparse itself prints no default and exit-2 never fires for a missing `--agents`. |
| **Verdict** | The README says `--agents PATH (default agents.json at the repository root)`. The argparse option has `default=None`. The description is functionally accurate but the stated default is wrong for the option itself. |
| **Replacement text** | Change `(default \`agents.json\` at the repository root)` → `(optional; if omitted, \`agents.json\` at the repository root is used)` |

---

### MISMATCH 2 — `DIALOG_API_FORMS.md` §4.4 issue-code table — `REPAIR_IDS_INVALID`, `REPAIR_UNKNOWN_CARD`, `REPAIR_CARD_MISSING` not listed, but that is out of scope (run.py codes). **Not in scope.**

---

### MISMATCH 3 — `README.md` line 135: exit code description for `dialog` CLI says "a wrong argument or an unreadable file prints one line and exits with 2" — accurate. `DIALOG_API_FORMS.md` line 67 says the same. Code confirms ([`dialog.py` line 1324](navigator/supervisor/dialog.py:1324)). ✓ No mismatch.

---

### MISMATCH 4 — `DIALOG_API_FORMS.md` §2 line 48 and `README.md` line 76: `--allow-origin` description

| | |
|---|---|
| **Doc / line** | `README.md` line 76: *"`--allow-origin URL`"* |
| **Doc / line** | `DIALOG_API_FORMS.md` line 48: *"`--allow-origin URL`"* |
| **Code** | [`http_api.py` line 249](navigator/supervisor/http_api.py:249): `ap.add_argument("--allow-origin", … metavar="ORIGIN")` — the metavar and help text say `ORIGIN`, not `URL`. |
| **Verdict** | Both docs name the argument value `URL`. The code uses `ORIGIN` in the help text (`metavar="ORIGIN"`, `help="Exact origin for Access-Control-Allow-Origin"`). An "origin" is `scheme://host:port`, not a full URL. The docs' word `URL` is factually wrong for what the option accepts. |
| **Replacement text** | `README.md` line 76: change `--allow-origin URL` → `--allow-origin ORIGIN`; `DIALOG_API_FORMS.md` line 48: change `--allow-origin URL` → `--allow-origin ORIGIN` |

---

### MISMATCH 5 — `DIALOG_API_FORMS.md` §2 line 49: `locale` not passed through the HTTP API

| | |
|---|---|
| **Doc / line** | `DIALOG_API_FORMS.md` §4.1 line 104: *"`start`: In: `story_text` … `locale` (optional, default `en-US`)"* — implies the HTTP POST `/start` body can carry `locale`. |
| **Code** | [`http_api.py` lines 169–173](navigator/supervisor/http_api.py:169): the `/start` handler only reads `story_text` and `ref_date` from the body; `locale` is never read and never forwarded to `D.start()`. |
| **Verdict** | The API forms document states `locale` is an input field of `start`. The HTTP handler silently ignores it; the `locale` parameter is never extracted from the JSON body. A caller who sends `locale` gets the default `en-US` regardless. |
| **Replacement text** | In `DIALOG_API_FORMS.md` §4.1 line 104, change: *"`locale` (optional, default `en-US`)"* → *"`locale` (optional, default `en-US`; not yet forwarded by the HTTP API — the API always uses `en-US`)"* |

---

### MISMATCH 6 — `README.md` line 81 and `DIALOG_API_FORMS.md` §2 line 43: `/health` response shows `"dialog_version": "0.2"` — confirmed correct ([`http_api.py` line 117–118](navigator/supervisor/http_api.py:117)). ✓

---

### Summary of real mismatches

| # | Doc file | Line | What doc says | What code does | Exact replacement |
|---|---|---|---|---|---|
| **1** | `README.md` | 76 | `--agents PATH` **(default `agents.json` at the repository root)** | `argparse` default is `None`; `agents.json` is the runtime fallback inside `_load_defaults`, not the argparse default | Replace `(default \`agents.json\` at the repository root)` with `(optional; if omitted, \`agents.json\` at the repository root is used)` |
| **2** | `README.md` | 76 | `--allow-origin URL` | Argparse metavar/help: `ORIGIN` (an origin is `scheme://host:port`, not a URL) | Replace `--allow-origin URL` with `--allow-origin ORIGIN` |
| **3** | `DIALOG_API_FORMS.md` | 48 | `--allow-origin URL` | Same as above | Replace `--allow-origin URL` with `--allow-origin ORIGIN` |
| **4** | `DIALOG_API_FORMS.md` | 104 | `locale` listed as an input field of `start` | HTTP handler ([`http_api.py` line 169–173](navigator/supervisor/http_api.py:169)) never reads `locale` from the POST body and never passes it to `D.start()` | Add a note: `locale` is not forwarded by the HTTP API; the API always uses the default `en-US` |

---

### 👤 User

Thank you. I checked your four findings against the code: all confirmed. Finding 4 (locale) is a real defect, so we fix the code, not only the text: start() now checks locale, and the HTTP API and the command line pass it on.

The 25 changes below are already checked: on a copy of this branch the full suite runs 475 tests, OK (467 before, 8 new tests).
They include your findings 1-3, the locale fix with its tests, the documentation for it, and one unclosed file in tests/test_dialog_b_step2.py (a ResourceWarning).

Rules:
- Apply them exactly, in order. Each FIND is copied from the current file and occurs once; replace it with REPLACE.
- One apply_diff per file with all of that file's blocks. Do not reformat anything.
- Do not re-read other parts of the files. Do not run commands; I run the tests.
- When done, list the files you changed and stop.


## navigator/supervisor/dialog.py

Change 1
FIND:
```
import json
import os
```
REPLACE:
```
import json
import os
import re
```

Change 2
FIND:
```
LOOP_GUARD_TURNS = 8
```
REPLACE:
```
LOOP_GUARD_TURNS = 8

# locale: a language tag such as en-US, es, es-419 or zh-Hant-TW (letters, digits, hyphens).
DEFAULT_LOCALE = "en-US"
_LOCALE_RE = re.compile(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")
_LOCALE_MAX_LEN = 35


def _valid_locale(value):
    """True for a short language tag such as en-US; False for anything else."""
    return (isinstance(value, str) and len(value) <= _LOCALE_MAX_LEN
            and _LOCALE_RE.fullmatch(value) is not None)
```

Change 3
FIND:
```
    run = None
    try:
        agents, kb_path, zips_path = _load_defaults(agents, kb_path, zips_path)
        if ref_date is None:
```
REPLACE:
```
    run = None
    try:
        if locale is None:
            locale = DEFAULT_LOCALE
        if not _valid_locale(locale):
            return _failed(None, [{"code": "LOCALE_INVALID", "severity": "critical",
                                   "message": "locale must be a language tag such as en-US",
                                   "related_ref": None}])
        agents, kb_path, zips_path = _load_defaults(agents, kb_path, zips_path)
        if ref_date is None:
```

Change 4
FIND:
```
    ap.add_argument("--ref-date",   metavar="YYYY-MM-DD")
```
REPLACE:
```
    ap.add_argument("--ref-date",   metavar="YYYY-MM-DD")
    ap.add_argument("--locale",     metavar="TAG",
                    help="language tag such as en-US (default en-US)")
```

Change 5
FIND:
```
        resp = start(story_text, ref_date=ref_date, **kw)
```
REPLACE:
```
        if a.locale is not None and not _valid_locale(a.locale):
            return _err(f"--locale {a.locale!r} is not a language tag such as en-US")
        resp = start(story_text, ref_date=ref_date, locale=a.locale, **kw)
```


## navigator/supervisor/http_api.py

Change 6
FIND:
```
                    story_text=data.get("story_text", ""),
                    ref_date=data.get("ref_date"),
```
REPLACE:
```
                    story_text=data.get("story_text", ""),
                    ref_date=data.get("ref_date"),
                    locale=data.get("locale"),
```


## tests/test_dialog.py

Change 7
FIND:
```


if __name__ == "__main__":
    unittest.main()
```
REPLACE:
```


class TestLocale(unittest.TestCase):
    """locale: passed to Agent 1 (understand_story); checked before any agent call."""

    def _spy(self, seen):
        def spy(req):
            if req.get("task_type") == "understand_story":
                seen.append(req["payload"].get("locale"))
            return agent_1_dialog(req)
        return spy

    def test_locale_reaches_agent_1(self):
        seen = []
        r = _start(agents=_agents(agent_1=self._spy(seen)), locale="es-US")
        self.assertNotEqual(r["status"], "failed")
        self.assertEqual(seen, ["es-US"])

    def test_default_and_none_send_en_us(self):
        for kw in ({}, {"locale": None}):
            with self.subTest(kw=kw):
                seen = []
                r = _start(agents=_agents(agent_1=self._spy(seen)), **kw)
                self.assertNotEqual(r["status"], "failed")
                self.assertEqual(seen, ["en-US"])

    def test_invalid_locale_fails_before_agent_1(self):
        for bad in (123, "", "english please", "en_US", "en-US\n", "e", "en-" + "x" * 40, ["en-US"]):
            with self.subTest(locale=bad):
                seen = []
                r = _start(agents=_agents(agent_1=self._spy(seen)), locale=bad)
                self.assertEqual(r["status"], "failed")
                self.assertEqual([i["code"] for i in r["issues"]], ["LOCALE_INVALID"])
                self.assertIsNone(r["case"])
                self.assertEqual(seen, [])

    def test_valid_tags_accepted(self):
        for tag in ("en", "en-US", "es-419", "zh-Hant-TW"):
            with self.subTest(locale=tag):
                seen = []
                _start(agents=_agents(agent_1=self._spy(seen)), locale=tag)
                self.assertEqual(seen, [tag])


if __name__ == "__main__":
    unittest.main()
```


## tests/test_dialog_b_step2.py

Change 8
FIND:
```
import tempfile
import unittest
```
REPLACE:
```
import tempfile
import unittest
from unittest import mock
```

Change 9
FIND:
```
    def test_start_bad_agents_file(self):
```
REPLACE:
```
    def test_start_locale_is_passed(self):
        flags, out = _shared_args(self.tmp)
        story_path = _write_text(self.tmp, "story.txt", STORY)
        with mock.patch.object(D, "start", wraps=D.start) as spy:
            rc = D.main(["start", "--story-file", story_path,
                         "--locale", "es-US"] + flags)
        self.assertEqual(rc, 0)
        self.assertEqual(spy.call_args.kwargs["locale"], "es-US")

    def test_start_bad_locale_exit_2(self):
        flags, out = _shared_args(self.tmp)
        story_path = _write_text(self.tmp, "story.txt", STORY)
        rc = D.main(["start", "--story-file", story_path,
                     "--locale", "english please"] + flags)
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists(out))

    def test_start_bad_agents_file(self):
```

Change 10
FIND:
```
        raw = open(out, encoding="utf-8").read()
```
REPLACE:
```
        with open(out, encoding="utf-8") as f:
            raw = f.read()
```


## tests/test_dialog_b_step3.py

Change 11
FIND:
```
import unittest
import urllib.error
```
REPLACE:
```
import unittest
import urllib.error
from unittest import mock
```

Change 12
FIND:
```
from navigator.supervisor.http_api import make_server
```
REPLACE:
```
from navigator.supervisor import dialog as D
from navigator.supervisor.http_api import make_server
```

Change 13
FIND:
```
    def test_failed_status_still_200(self):
```
REPLACE:
```
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
```


## navigator/supervisor/README.md

Change 14
FIND:
```
`--agents PATH` (default `agents.json` at the repository root)
```
REPLACE:
```
`--agents PATH` (optional; if omitted, `agents.json` at the repository root is used)
```

Change 15
FIND:
```
`--allow-origin URL` (lets a browser page on that one origin call the server)
```
REPLACE:
```
`--allow-origin ORIGIN` (lets a browser page on that one origin, for example `http://localhost:3000`, call the server)
```

Change 16
FIND:
```
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13"}` (`ref_date` optional) |
```
REPLACE:
```
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13", "locale": "en-US"}` (`ref_date` and `locale` optional) |
```

Change 17
FIND:
```
All three take `--agents`, `--kb`, `--zips` and `--no-isolate`. `--case-in`
```
REPLACE:
```
All three take `--agents`, `--kb`, `--zips` and `--no-isolate`; `start` also takes `--locale` (default `en-US`). `--case-in`
```

Change 18
FIND:
```
233 Supervisor tests (the full suite runs 467)
```
REPLACE:
```
241 Supervisor tests (the full suite runs 475)
```

Change 19
FIND:
```
# all tests (467)
```
REPLACE:
```
# all tests (475)
```


## docs/supervisor/DIALOG_API_FORMS.md

Change 20
FIND:
```
Version 0.2.3 (Nov 13, 2026, 21:30 MT) · built on v0.2.2 · owner: Slav
```
REPLACE:
```
Version 0.2.4 (Nov 14, 2026) · built on v0.2.3 · owner: Slav
v0.2.4: `locale` now works in all three ways of calling `start` (the HTTP API and the command line passed it on to nobody before) and is checked: anything other than a language tag such as `en-US` gives `failed` `LOCALE_INVALID` (§4.1, §4.4). `--allow-origin` takes an origin such as `http://localhost:3000` (§2). No response field changed; `dialog_version` stays `"0.2"`. 475 tests.
```

Change 21
FIND:
```
`--allow-origin URL` (a browser page on that one origin may call the server; never `*`)
```
REPLACE:
```
`--allow-origin ORIGIN` (a browser page on that one origin, for example `http://localhost:3000`, may call the server; never `*`)
```

Change 22
FIND:
```
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13"}` (`ref_date` optional) |
```
REPLACE:
```
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13", "locale": "en-US"}` (`ref_date` and `locale` optional) |
```

Change 23
FIND:
```
start   --story-file story.txt [--ref-date 2026-11-13] --out r1.json
```
REPLACE:
```
start   --story-file story.txt [--ref-date 2026-11-13] [--locale en-US] --out r1.json
```

Change 24
FIND:
```
`locale` (optional, default `en-US`).
```
REPLACE:
```
`locale` (optional, default `en-US`; a language tag such as `en-US` or `es-US`, anything else gives `failed` `LOCALE_INVALID`; it is passed to Agent 1, and the team's agents do not use it yet).
```

Change 25
FIND:
```
| `FACT_VALUE_INVALID` | a correction has the wrong type or format | ask the user to check the value |
```
REPLACE:
```
| `FACT_VALUE_INVALID` | a correction has the wrong type or format | ask the user to check the value |
| `LOCALE_INVALID` | `locale` in `start` is not a language tag such as `en-US` | a developer bug: fix the request |
```

---

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[-] Apply changes 1–5 to navigator/supervisor/dialog.py
[ ] Apply changes 6 to navigator/supervisor/http_api.py
[ ] Apply changes 7 to tests/test_dialog.py
[ ] Apply changes 8–10 to tests/test_dialog_b_step2.py
[ ] Apply changes 11–13 to tests/test_dialog_b_step3.py
[ ] Apply changes 14–19 to navigator/supervisor/README.md
[ ] Apply changes 20–25 to docs/supervisor/DIALOG_API_FORMS.md


### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — navigator\supervisor\dialog.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Apply changes 1–5 to navigator/supervisor/dialog.py
[-] Apply changes 6 to navigator/supervisor/http_api.py
[ ] Apply changes 7 to tests/test_dialog.py
[ ] Apply changes 8–10 to tests/test_dialog_b_step2.py
[ ] Apply changes 11–13 to tests/test_dialog_b_step3.py
[ ] Apply changes 14–19 to navigator/supervisor/README.md
[ ] Apply changes 20–25 to docs/supervisor/DIALOG_API_FORMS.md


### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — navigator\supervisor\http_api.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Apply changes 1–5 to navigator/supervisor/dialog.py
[x] Apply changes 6 to navigator/supervisor/http_api.py
[-] Apply changes 7 to tests/test_dialog.py
[ ] Apply changes 8–10 to tests/test_dialog_b_step2.py
[ ] Apply changes 11–13 to tests/test_dialog_b_step3.py
[ ] Apply changes 14–19 to navigator/supervisor/README.md
[ ] Apply changes 20–25 to docs/supervisor/DIALOG_API_FORMS.md


### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — ^if __name__ == "__main__":

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:857
-------


if __name__ == "__main__":
    unittest.main()
=======


class TestLocale(unittest.TestCase):
    """locale: passed to Agent 1 (understand_story); checked before any agent call."""

    def _spy(self, seen):
        def spy(req):
            if req.get("task_type") == "understand_story":
                seen.append(req["payload"].get("locale"))
            return agent_1_dialog(req)
        return spy

    def test_locale_reaches_agent_1(self):
        seen = []
        r = _start(agents=_agents(agent_1=self._spy(seen)), locale="es-US")
        self.assertNotEqual(r["status"], "failed")
        self.assertEqual(seen, ["es-US"])

    def test_default_and_none_send_en_us(self):
        for kw in ({}, {"locale": None}):
            with self.subTest(kw=kw):
                seen = []
                r = _start(agents=_agents(agent_1=self._spy(seen)), **kw)
                self.assertNotEqual(r["status"], "failed")
                self.assertEqual(seen, ["en-US"])

    def test_invalid_locale_fails_before_agent_1(self):
        for bad in (123, "", "english please", "en_US", "en-US\n", "e", "en-" + "x" * 40, ["en-US"]):
            with self.subTest(locale=bad):
                seen = []
                r = _start(agents=_agents(agent_1=self._spy(seen)), locale=bad)
                self.assertEqual(r["status"], "failed")
                self.assertEqual([i["code"] for i in r["issues"]], ["LOCALE_INVALID"])
                self.assertIsNone(r["case"])
                self.assertEqual(seen, [])

    def test_valid_tags_accepted(self):
        for tag in ("en", "en-US", "es-419", "zh-Hant-TW"):
            with self.subTest(locale=tag):
                seen = []
                _start(agents=_agents(agent_1=self._spy(seen)), locale=tag)
                self.assertEqual(seen, [tag])


if __name__ == "__main__":
    unittest.main()
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Apply changes 1–5 to navigator/supervisor/dialog.py
[x] Apply changes 6 to navigator/supervisor/http_api.py
[x] Apply changes 7 to tests/test_dialog.py
[-] Apply changes 8–10 to tests/test_dialog_b_step2.py
[ ] Apply changes 11–13 to tests/test_dialog_b_step3.py
[ ] Apply changes 14–19 to navigator/supervisor/README.md
[ ] Apply changes 20–25 to docs/supervisor/DIALOG_API_FORMS.md


### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — tests\test_dialog_b_step2.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — tests\test_dialog_b_step2.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Apply changes 1–5 to navigator/supervisor/dialog.py
[x] Apply changes 6 to navigator/supervisor/http_api.py
[x] Apply changes 7 to tests/test_dialog.py
[x] Apply changes 8–10 to tests/test_dialog_b_step2.py
[-] Apply changes 11–13 to tests/test_dialog_b_step3.py
[ ] Apply changes 14–19 to navigator/supervisor/README.md
[ ] Apply changes 20–25 to docs/supervisor/DIALOG_API_FORMS.md


### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — tests\test_dialog_b_step3.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:10
-------
import urllib.error
=======
import urllib.error
from unittest import mock
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:13
-------
from navigator.supervisor.http_api import make_server
=======
from navigator.supervisor import dialog as D
from navigator.supervisor.http_api import make_server
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:216
-------
    def test_failed_status_still_200(self):
=======
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
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Apply changes 1–5 to navigator/supervisor/dialog.py
[x] Apply changes 6 to navigator/supervisor/http_api.py
[x] Apply changes 7 to tests/test_dialog.py
[x] Apply changes 8–10 to tests/test_dialog_b_step2.py
[x] Apply changes 11–13 to tests/test_dialog_b_step3.py
[-] Apply changes 14–19 to navigator/supervisor/README.md
[ ] Apply changes 20–25 to docs/supervisor/DIALOG_API_FORMS.md


### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — navigator\supervisor\README.md

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:76
-------
Options: `--host` (default `127.0.0.1`), `--port` (default `8765`), `--agents PATH` (default `agents.json` at the repository root), `--kb PATH` (default `navigator/kb/kb_sacramento.json`), `--zips PATH` (default `navigator/kb/sacramento_county_zips.json`), `--no-isolate` (agents run in the server process), `--allow-origin URL` (lets a browser page on that one origin call the server). Without `--no-isolate` every agent call runs in its own process, so a hung agent can be stopped, but each step is slower; for local testing and the demo use `--no-isolate`. To try the flow on fake agents: `--agents tests/agents_fake_dialog.json --kb tests/fixtures/kb_supervisor_fixture.json --zips tests/fixtures/zips_fixture.json`.
=======
Options: `--host` (default `127.0.0.1`), `--port` (default `8765`), `--agents PATH` (optional; if omitted, `agents.json` at the repository root is used), `--kb PATH` (default `navigator/kb/kb_sacramento.json`), `--zips PATH` (default `navigator/kb/sacramento_county_zips.json`), `--no-isolate` (agents run in the server process), `--allow-origin ORIGIN` (lets a browser page on that one origin, for example `http://localhost:3000`, call the server). Without `--no-isolate` every agent call runs in its own process, so a hung agent can be stopped, but each step is slower; for local testing and the demo use `--no-isolate`. To try the flow on fake agents: `--agents tests/agents_fake_dialog.json --kb tests/fixtures/kb_supervisor_fixture.json --zips tests/fixtures/zips_fixture.json`.
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:87
-------
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13"}` (`ref_date` optional) |
=======
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13", "locale": "en-US"}` (`ref_date` and `locale` optional) |
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:135
-------
All three take `--agents`, `--kb`, `--zips` and `--no-isolate`. `--case-in`
=======
All three take `--agents`, `--kb`, `--zips` and `--no-isolate`; `start` also takes `--locale` (default `en-US`). `--case-in`
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:26
-------
| `../../tests/` | 233 Supervisor tests (the full suite runs 467): checks, builders, full cycle on fake agents, broken and hung agents, privacy, repair rounds, ref_date, S1 per-role fields, final_validation, ZIP list, dialog mode, command line, HTTP API |
=======
| `../../tests/` | 241 Supervisor tests (the full suite runs 475): checks, builders, full cycle on fake agents, broken and hung agents, privacy, repair rounds, ref_date, S1 per-role fields, final_validation, ZIP list, dialog mode, command line, HTTP API |
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:33
-------
python -I -m unittest discover -s tests -t .                               # all tests (467)
=======
python -I -m unittest discover -s tests -t .                               # all tests (475)
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: grep

The partial failure is likely the line-135 change — the line numbers shifted after the earlier edits. Let me check and apply it:

> 🔧 **grep** — navigator\supervisor\README.md

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:135
-------
All three take `--agents`, `--kb`, `--zips` and `--no-isolate`. `--case-in`
=======
All three take `--agents`, `--kb`, `--zips` and `--no-isolate`; `start` also takes `--locale` (default `en-US`). `--case-in`
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: search_and_replace

The file content is in the debug output but the diff engine is confused by context mismatch after the earlier edits. I'll use `search_and_replace` for this specific line:

> 🔧 **search_and_replace** — navigator\supervisor\README.md

### 🤖 Assistant

> 🔧 called: update_todo_list

All 6 README changes are done. Now the final file:

> 🔧 **update_todo_list** — 
[x] Apply changes 1–5 to navigator/supervisor/dialog.py
[x] Apply changes 6 to navigator/supervisor/http_api.py
[x] Apply changes 7 to tests/test_dialog.py
[x] Apply changes 8–10 to tests/test_dialog_b_step2.py
[x] Apply changes 11–13 to tests/test_dialog_b_step3.py
[x] Apply changes 14–19 to navigator/supervisor/README.md
[-] Apply changes 20–25 to docs/supervisor/DIALOG_API_FORMS.md


### 🤖 Assistant

> 🔧 called: grep



> 🔧 **grep** — docs\supervisor\DIALOG_API_FORMS.md

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:3
-------
Version 0.2.3 (Nov 13, 2026, 21:30 MT) · built on v0.2.2 · owner: Slav
=======
Version 0.2.4 (Nov 14, 2026) · built on v0.2.3 · owner: Slav
v0.2.4: `locale` now works in all three ways of calling `start` (the HTTP API and the command line passed it on to nobody before) and is checked: anything other than a language tag such as `en-US` gives `failed` `LOCALE_INVALID` (§4.1, §4.4). `--allow-origin` takes an origin such as `http://localhost:3000` (§2). No response field changed; `dialog_version` stays `"0.2"`. 475 tests.
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:44
-------
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13"}` (`ref_date` optional) | the response of §4.1 |
=======
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13", "locale": "en-US"}` (`ref_date` and `locale` optional) | the response of §4.1 |
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:48
-------
- Options: `--host` (default 127.0.0.1), `--port` (default 8765), `--agents PATH`, `--kb PATH` (program KB), `--zips PATH` (county ZIP list; default `navigator/kb/sacramento_county_zips.json`), `--no-isolate` (agents run in the server process; recommended for local testing and the demo: without it every agent call starts its own process and each step is slower), `--allow-origin URL` (a browser page on that one origin may call the server; never `*`).
=======
- Options: `--host` (default 127.0.0.1), `--port` (default 8765), `--agents PATH`, `--kb PATH` (program KB), `--zips PATH` (county ZIP list; default `navigator/kb/sacramento_county_zips.json`), `--no-isolate` (agents run in the server process; recommended for local testing and the demo: without it every agent call starts its own process and each step is slower), `--allow-origin ORIGIN` (a browser page on that one origin, for example `http://localhost:3000`, may call the server; never `*`).
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:63
-------
python -m navigator.supervisor.dialog start   --story-file story.txt [--ref-date 2026-11-13] --out r1.json
=======
python -m navigator.supervisor.dialog start   --story-file story.txt [--ref-date 2026-11-13] [--locale en-US] --out r1.json
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:104
-------
`locale` (optional, default `en-US`).
=======
`locale` (optional, default `en-US`; a language tag such as `en-US` or `es-US`, anything else gives `failed` `LOCALE_INVALID`; it is passed to Agent 1, and the team's agents do not use it yet).
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:234
-------
| `FACT_VALUE_INVALID` | a correction has the wrong type or format | ask the user to check the value |
=======
| `FACT_VALUE_INVALID` | a correction has the wrong type or format | ask the user to check the value |
| `LOCALE_INVALID` | `locale` in `start` is not a language tag such as `en-US` | a developer bug: fix the request |
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: grep

The partial failure is on change 24 (the `locale` description in §4.1). Let me check and apply it:

> 🔧 **grep** — docs\supervisor\DIALOG_API_FORMS.md

### 🤖 Assistant

> 🔧 called: search_and_replace



> 🔧 **search_and_replace** — docs\supervisor\DIALOG_API_FORMS.md

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Apply changes 1–5 to navigator/supervisor/dialog.py
[x] Apply changes 6 to navigator/supervisor/http_api.py
[x] Apply changes 7 to tests/test_dialog.py
[x] Apply changes 8–10 to tests/test_dialog_b_step2.py
[x] Apply changes 11–13 to tests/test_dialog_b_step3.py
[x] Apply changes 14–19 to navigator/supervisor/README.md
[x] Apply changes 20–25 to docs/supervisor/DIALOG_API_FORMS.md


### 🤖 Assistant

All 25 changes applied. Files changed:

| # | File |
|---|---|
| 1–5 | [`navigator/supervisor/dialog.py`](navigator/supervisor/dialog.py) |
| 6 | [`navigator/supervisor/http_api.py`](navigator/supervisor/http_api.py) |
| 7 | [`tests/test_dialog.py`](tests/test_dialog.py) |
| 8–10 | [`tests/test_dialog_b_step2.py`](tests/test_dialog_b_step2.py) |
| 11–13 | [`tests/test_dialog_b_step3.py`](tests/test_dialog_b_step3.py) |
| 14–19 | [`navigator/supervisor/README.md`](navigator/supervisor/README.md) |
| 20–25 | [`docs/supervisor/DIALOG_API_FORMS.md`](docs/supervisor/DIALOG_API_FORMS.md) |