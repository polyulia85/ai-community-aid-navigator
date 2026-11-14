# Supervisor — AI Community Aid Navigator

Owner: Slav (Supervisor / Orchestrator and integration). Contract: `docs/contracts/SHARED_CONTRACTS.md` (v1.1, Oct 27, 2026). Version: v0.2.5 (Nov 13, 2026): adds the dialog mode (start / answer / confirm), a command line and a local HTTP API for the App Layer. Local Python prototype, standard library only (Python 3.11+); not connected to IBM watsonx Orchestrate (see Known limits).

## What it does

- **Dialog mode (v0.2.5):** the Navigator as a conversation: the user's story, a few questions, the Situation Summary to confirm, then the action plan. See "Dialog mode: how to run and connect" below.
- **Runs one cycle:** Agent 1 → 2 → 3 → 4 → 5 → 6 → 8 → 10, with Agent 7 reviewing the retrieval, matching, verification and planning stages. Agents never call each other; every call is one AgentRequest and one AgentResult (contracts sections 1–2).
- **Builds every request** with only the facts that agent needs: S0 input masking before Agent 1; `ref_date` (ISO string, same value for the whole run) in the payloads of Agents 1, 6, 8 (including every repair round) and 10, so all four agents resolve dates against the same fixed reference (PROPOSED for contracts v1.2, approved by Julia Nov 6); `agent1_request`, `agent6_request`, `agent8_request` and `agent10_request` each raise `ValueError` if `ref_date` is `None` — the runner always supplies it, using `_today()` in `run.py` when no date is given (patchable in tests); user confirmation turns Agent 1 claims into case facts and bumps `case_version`; county + ZIP for Agent 3; `program_criteria` for Agent 4; `programs_to_check` for Agent 5 (no confirmed mismatches); the planning package for Agents 6, 8 and 10 (availability and its evidence from the KB; program name, organization and subcategory added to each match; user dates from case facts; official deadlines only from the KB).
- **Checks every result (S1–S9):** schema, identity echo, stale version, enums, references, failed status, 30 s timeout, mock flag, privacy (SSN, bank and card numbers by value pattern and field name). A result that fails a check is rejected and reported, never treated as success. S1 now also checks per-role result fields: for every `(role_id, task_type)` pair in `TASK_TYPES`, `RESULT_REQUIRED` in `contract.py` lists the required top-level `result` keys, which of those must be lists, and the required keys of each list item (from contract §4.1–4.9, §3.1–3.2). A missing key or wrong container type is `SCHEMA_INVALID` (critical), and the result is rejected and retried exactly like any other S1 failure. The check reads `role_id` and `task_type` from the **request** (not the result). A failed result (status `failed`, result `{}`) is not checked. Unknown `(role_id, task_type)` pairs also produce `SCHEMA_INVALID` (fail-closed).
- **Safety net:** in `Run._execute_body`, if any builder step raises `KeyError`, `TypeError`, `ValueError`, `AttributeError` or `IndexError`, the Supervisor records `SUPERVISOR_INPUT_ERROR` (critical) naming the stage and exception type (no user data), and returns `stopped_at_<stage>`. A run never ends with a traceback (some CLI input errors before the run starts still do; see Known limits).
- **Retries and repair** (contracts 5.3): 1 retry per call (none for stale or privacy results); after an Agent 10 FLAG, up to 2 repair rounds; then only cards still flagged with `blocks_release` are withheld and the rest of the plan is released. In each repair round the Supervisor sends only the blocking flags to Agent 8; Agent 8 must return `repaired_card_ids` (a list of strings). The Supervisor then merges only those cards back into the current plan, preserving all other cards, potential options, and coverage gaps in their original order. If `repaired_card_ids` is absent or is not a list of strings, nothing is merged, the current plan is kept, and `REPAIR_IDS_INVALID` (warning) is added to `supervisor_issues`. If the repair result has no `plan_version`, the current plan's `plan_version` is kept. Agent 10 always receives the full merged plan. If the repair result contains an unknown `card_id` it is not added (`REPAIR_UNKNOWN_CARD` warning); if a listed card is missing it is kept unchanged (`REPAIR_CARD_MISSING` warning). The merge logic is in `merge_repaired_plan()` in `run.py` and is covered by unit tests.
- **Isolation:** each agent call runs in its own process (`spawn`, same on Windows and Linux). On a timeout the process is stopped, so a hung agent cannot keep running. `--no-isolate` runs agents in-process (faster, no hard stop).
- **Writes `run_report.json`:** every step and its issues (technical errors); Agent 7 findings; `ref_date`; `final_validation` (whenever Agent 10 ran, regardless of outcome): `{verdict, repair_rounds_used, flags: [{card_id, rule_id, severity, blocks_release, reason, required_correction}], passed_card_ids}` — only these six fields, no `claim_text` or user facts; the plan with `withheld_card_ids`, `withheld_cards` (for each withheld card: `{card_id, rule_ids, reasons}` from its last blocking flags), `action_cards`, `potential_options`, `coverage_gaps`; and a `partially_mocked` flag. `steps[].issues` (technical errors) and `final_validation.flags` (content findings) are kept separate.

## Files

| File | Purpose |
|---|---|
| `contract.py` | allowed values from the contract; `RESULT_REQUIRED` table (per-role, per-task_type required result fields) |
| `checks.py` | S0 input masking and checks S1–S9; `s1_result_fields()` (S1 extension) |
| `builders.py` | `CaseState` (the Supervisor's memory of one case), `_ref_date_iso()` helper, and the request builder for every agent |
| `run.py` | the runner, `_execute_body()` / `_plan_body()` / `_input_error()`, `merge_repaired_plan()` helper, and `agents.json` loader (clear one-line errors, exit code 2) |
| `dialog.py` | dialog mode: `start()`, `answer()`, `confirm()`, the Situation Summary, `plan_by_need`, the safety notice with verified 9-1-1 and 988 contacts, and the command line (`main()`) |
| `http_api.py` | local HTTP API over the three dialog calls (standard library `http.server`) |
| `../../tests/` | 241 Supervisor tests (the full suite runs 475): checks, builders, full cycle on fake agents, broken and hung agents, privacy, repair rounds, ref_date, S1 per-role fields, final_validation, ZIP list, dialog mode, command line, HTTP API |
| `../../tests/fixtures/kb_supervisor_fixture.json` | Frozen KB copy for Supervisor tests (Nov 6, 2026). Tests use this, not the live KB. |
| `../../tests/fixtures/zips_fixture.json`, `emergency_fixture.json` | Frozen ZIP list and emergency directory for tests. |

## How to run (from the repository root)

```
python -I -m unittest discover -s tests -t .                               # all tests (475)
python -m navigator.supervisor.run --agents tests/agents_fake.json --kb tests/fixtures/kb_supervisor_fixture.json               # full cycle on fake agents
python -m navigator.supervisor.run --agents tests/agents_fake.json --kb tests/fixtures/kb_supervisor_fixture.json --demo-broken   # the Supervisor rejects sample 03
python -m navigator.supervisor.run --agents agents.json                    # the team's components
```

Supervisor tests use the frozen fixture `tests/fixtures/kb_supervisor_fixture.json` (a copy of the KB as of Nov 6, 2026) so they do not depend on live KB data. The live KB `navigator/kb/kb_sacramento.json` is only used by the real end-to-end run.

## Other options

| Option | Description |
|---|---|
| `--kb PATH` | path to the KB JSON file (default: `navigator/kb/kb_sacramento.json`) |
| `--zips PATH` | the verified county ZIP list (default: `navigator/kb/sacramento_county_zips.json`); a list not marked `verified` is not used |
| `--story-file PATH` | text file with the user's story (default: sample 01) |
| `--correct field=value` | user correction at confirmation, e.g. `cash_on_hand_approx=300` (repeatable) |
| `--out PATH` | output file for the run report (default: `run_report.json`) |
| `--no-isolate` | run agents inside this process (faster; a timed-out agent keeps running) |
| `--demo-broken` | replace Agent 1 with sample 03 to demonstrate rejection |
| `--ref-date YYYY-MM-DD` | reference date for Agents 1, 6, 8 and 10 (ISO format); defaults to today. An invalid value prints one clear error line and exits with code 2. |

## Dialog mode: how to run and connect (v0.2.5)

Dialog mode runs the Navigator as a conversation: the user tells their story, answers a few questions, checks the Situation Summary, then gets the action plan. The full call and response forms are in `docs/supervisor/DIALOG_API_FORMS.md`.

**Requirements:** Python 3.11 or newer (tested on 3.12), standard library only, nothing to install. The dialog writes no files and keeps no database; no internet is needed.

### The three steps

| Step | Call | Returns |
|---|---|---|
| 1. The user tells the story | `start` | `needs_clarification` (questions) or `needs_confirmation` (summary) |
| 2. The user answers (repeat while there are questions) | `answer` | new questions, or the summary |
| 3. The user confirms the summary (may correct facts, remove or add needs) | `confirm` | `completed` (action plan) or `failed` |

Every response has a `case` object. **Send it back unchanged in the next call**; it is the only memory of the dialog between calls. Keep it in the user's session and do not log it (it holds the user's facts).

### Option A — HTTP (for the browser app)

Start the server from the repository root:
```
python -m navigator.supervisor.http_api --agents agents.json --no-isolate
```
Options: `--host` (default `127.0.0.1`), `--port` (default `8765`), `--agents PATH` (optional; if omitted, `agents.json` at the repository root is used), `--kb PATH` (default `navigator/kb/kb_sacramento.json`), `--zips PATH` (default `navigator/kb/sacramento_county_zips.json`), `--no-isolate` (agents run in the server process), `--allow-origin ORIGIN` (lets a browser page on that one origin, for example `http://localhost:3000`, call the server). Without `--no-isolate` every agent call runs in its own process, so a hung agent can be stopped, but each step is slower; for local testing and the demo use `--no-isolate`. To try the flow on fake agents: `--agents tests/agents_fake_dialog.json --kb tests/fixtures/kb_supervisor_fixture.json --zips tests/fixtures/zips_fixture.json`.

Check it is up:
```
curl.exe http://127.0.0.1:8765/health
→ {"status": "ok", "dialog_version": "0.2"}
```

| Method and path | Body |
|---|---|
| `GET /health` | — |
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13", "locale": "en-US"}` (`ref_date` and `locale` optional) |
| `POST /answer` | `{"case": {...}, "answers": [{"question_id": "q1-1", "answer_text": "..."}]}`; a skipped question: `{"question_id": "q1-1", "skipped": true}` |
| `POST /confirm` | `{"case": {...}, "corrections": {...}, "rejected_need_ids": [...], "added_needs": [...]}` (the last three optional) |

From a Python backend:
```python
import json, urllib.request, urllib.error

def call(path, body):
    req = urllib.request.Request("http://127.0.0.1:8765" + path,
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:          # 400, 404, 405, 413 also carry a JSON body
        return json.loads(e.read().decode("utf-8"))

r = call("/start", {"story_text": "I have problems with housing and food. I need help."})
while r["status"] == "needs_clarification":
    answers = [{"question_id": q["question_id"], "answer_text": input(q["text"] + " ")}
               for q in r["questions"]]
    r = call("/answer", {"case": r["case"], "answers": answers})
if r["status"] == "needs_confirmation":
    r = call("/confirm", {"case": r["case"]})
print(r["status"], len((r.get("plan") or {}).get("action_cards", [])), "cards")
```

### Option B — import in Python (same JSON, no server)

```python
from navigator.supervisor.dialog import start, answer, confirm
from navigator.supervisor.run import load_agents

agents = load_agents("agents.json")
r1 = start("I have problems with housing and food. I need help.", agents=agents)
r2 = answer(r1["case"], [{"question_id": "q1-1", "answer_text": "My hours were cut at work."}], agents=agents)
r3 = confirm(r2["case"], agents=agents)
```
Each function also takes `kb_path`, `zips_path` and `isolate` (default `False`). Default paths are built from the package location, not from the current folder. The functions never raise: a problem comes back as `status: failed`.

### Option C — command line (for testing without an app)

```
python -m navigator.supervisor.dialog start   --story-file story.txt --ref-date 2026-11-13 --out r1.json
python -m navigator.supervisor.dialog answer  --case-in r1.json --answers-file answers.json --out r2.json
python -m navigator.supervisor.dialog confirm --case-in r2.json [--corrections-file c.json] [--rejected need_002] [--added-file n.json] --out r3.json
```
All three take `--agents`, `--kb`, `--zips` and `--no-isolate`; `start` also takes `--locale` (default `en-US`). `--case-in` is the whole previous response file. The command prints one line (status, turn, questions, needs or cards). Exit code 0, or 1 when the status is `failed`; a wrong argument or an unreadable file prints one line and exits with 2. Files saved by Notepad (UTF-8 with a BOM) are read correctly.

### What to show the user

- `questions[]`: show `text`; one answer field per question; a "Skip" button when `can_skip` is true. Send an item for every question of the turn. A required question (`can_skip: false`) that is skipped comes back as `failed` `SKIP_NOT_ALLOWED` with the same questions.
- `summary`: `narrative`; the `needs` (each can be removed); the `facts` with `label` and `display_value` (each can be corrected; facts the person mentioned beyond a question are here too); the `unknown` list; an "Add a need" option.
- `plan.action_cards` in their order, and `plan_by_need` for a "by need" view (urgency is a label, not the order). Show each row's `gap_notes`: a need with no verified program keeps its row with a plain explanation. `withheld_cards`: "We could not verify this option yet".
- `limitations[]`: plain sentences (for example when the ZIP was skipped); show them near the plan.
- `safety_notice`: when not null, show it above everything, with its `contacts` (verified 9-1-1 and 988 from the emergency directory). The app shows 9-1-1 and 988 at all times anyway.
- `failed`: show `user_message` and let the user retry with the `case` from the same response. `issues` are for developers only.

### HTTP status codes

| HTTP | Meaning |
|---|---|
| 200 | every dialog response, including `status: failed` (for example a missing or wrong `case`); read `status` and `issues` |
| 400 | the body is not a JSON object, or a bad `Content-Length` (`issues[0].code` = `BAD_REQUEST`) |
| 404 | unknown path |
| 405 | wrong method (for example `GET /start`) |
| 413 | body larger than 64 KB |

### Troubleshooting

| Problem | Cause and fix |
|---|---|
| `ModuleNotFoundError: navigator` | run from the repository root (the folder that holds `navigator/`) |
| `Address already in use` | another server is on 8765: stop it or use `--port 8766` |
| The browser shows a CORS error | start with `--allow-origin http://localhost:3000` (your app's exact origin, with port) |
| `curl` in PowerShell asks for parameters | PowerShell's `curl` is another command: use `curl.exe` |
| Each step takes a second or more | the server runs every agent call in its own process; start it with `--no-isolate` (on the team's agents a full dialog then takes well under a second per step) |
| `status: failed` with `TIMEOUT` | an agent took longer than 30 s; retry with the same case |
| `limitations` mentions the ZIP | the ZIP was skipped; local programs need it |
| `COUNTY_UNKNOWN` in `issues` | the ZIP is not on the verified county ZIP list (`navigator/kb/sacramento_county_zips.json`); the request goes to Agent 3 with the ZIP and no county |
| `COUNTY_FROM_ZIP_LIST` in `issues` (info) | normal: the county comes from the ZIP list; a ZIP area can cross the county line |
| `ZIP_LIST_UNAVAILABLE` in `issues` | the ZIP list file is missing, unreadable or not marked `verified`; check `--zips` |
| `SAFETY_CONTACT_UNVERIFIED` in `issues` | the emergency directory could not be read or has no verified 9-1-1 / 988 contact; the notice is shown without contacts |
| The same question comes back | it should not; save the request and the response and send them to Slav |

## Known limits

- The one-shot run (`python -m navigator.supervisor.run`) is a test tool: it does not stop for questions (it notes `CLARIFICATION_PENDING` and goes on) and has no safety notice. The App Layer uses the dialog mode.
- The `case` is not signed, and an older case sent back is not detected (`STALE_CASE` needs a store); Case State (SQLite, My Case) is not connected, the case lives in the user's session; owner: Slav and Silver, after the MVP.
- A safety threat stated only in an answer (not in the story) does not raise the safety notice yet: Agent 1 does not return safety flags when it reads an answer; the Supervisor already accepts them. Owner: Yogesh.
- New needs found in answers (`proposed_needs` in `parse_clarification_answer`, CR-014), forwarding Agent 1's ambiguity flags to Agent 2, `ref_date` for Agents 1, 6, 8 and 10 and the repair-round merge rule are PROPOSED for contracts v1.2 and not yet in the official shared contract.
- S1 checks that result fields are present and that lists are lists, but not the types of single values; plan-level blocking flags (card_id null) are not handled; S5 does not check references inside clarification requests; owner: Slav, after Nov 16.
- In the one-shot run, a need with no card and no coverage gap is not reported, and a `--correct` value for a fact Agent 1 did not extract is ignored (the dialog mode handles both); some one-shot CLI input errors end with a traceback; owner: Slav, after Nov 16.
- `make_request` uses `assert`; a boolean `case_version` is not rejected; owner: Slav, after Nov 16.
- The HTTP server is for local use: no HTTPS and no sign-in. Not connected to IBM watsonx Orchestrate: the lab environment does not confirm importing Python tools, and a public deployment is not available in the lab account.
