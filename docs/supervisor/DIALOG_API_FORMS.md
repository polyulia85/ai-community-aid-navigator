# Supervisor dialog mode — call and response forms (for the App Layer)

Version 0.2.4 (Nov 14, 2026) · built on v0.2.3 · owner: Slav
v0.2.4: `locale` now works in all three ways of calling `start` (the HTTP API and the command line passed it on to nobody before) and is checked: anything other than a language tag such as `en-US` gives `failed` `LOCALE_INVALID` (§4.1, §4.4). `--allow-origin` takes an origin such as `http://localhost:3000` (§2). No response field changed; `dialog_version` stays `"0.2"`. 475 tests.
v0.2.3: matches the code as built (Supervisor v0.2.5, branch `slav/supervisor-v0.2.5`, 467 tests). Added: the command line (§2), HTTP 405 and the `BAD_REQUEST` body (§2), the type rules for corrections and the code `FACT_VALUE_INVALID` (§4.3), the verified 9-1-1 and 988 contacts in `safety_notice` and the code `SAFETY_CONTACT_UNVERIFIED` (§5), `skipped_keys`, `limitations` and full questions in the `case` (§6). No response field was renamed or removed; `dialog_version` stays `"0.2"`.
v0.2.2: the county comes from the verified county ZIP list in the KB (option `--zips` / `zips_path`); three more developer codes (`COUNTY_FROM_ZIP_LIST`, `ZIP_LIST_UNAVAILABLE`, `ANSWER_FACT_INVALID`). No field of any call or response changed; `dialog_version` stays `"0.2"`.
v0.2.1: a need with no card and no gap now gets a plain explanation for the user (Julia: no need disappears from the plan without an explanation); facts the person states beyond the question are kept, not dropped.
Status: built and tested (Supervisor v0.2.5). Field values in the examples are illustrative; real examples from a run with the team's agents will be added in `docs/examples/dialog/`.

What changed since v0.1 (Julia's answers, Nov 11):
- The App Layer is a browser app with a Python backend → an **HTTP API** (§2). The backend may also import the three functions directly.
- **No fixed limit** on question turns: the dialog is adaptive; a question is never repeated; a technical fuse stops a loop caused by an agent defect (§1).
- At confirmation the user can **correct facts, remove needs and add needs** (§4.3).
- The ZIP can be skipped; then the response says what is limited, in plain words (`limitations`, §3).
- `plan_by_need` follows the plan's own order; urgency is only a label, never used for sorting (§4.3).
- 911 and 988 are shown by the app at all times. `safety_notice` appears only on a direct threat to physical safety; a landlord's lockout threat is a housing and legal issue, not a safety notice (§5).
- The case can be kept in the user's session for now; persistent storage (Case State, SQLite) stays in the architecture and is connected later (§6).

---

## 1. The flow

```
start(story)                                  → needs_clarification (questions) or needs_confirmation (summary)
answer(case, answers)                         → needs_clarification (new questions) or needs_confirmation (summary)
confirm(case, corrections, rejected, added)   → completed (action plan) or failed
```

- Order (Julia, Nov 9): questions first, then the Situation Summary for confirmation, then the plan. The plan is built only after the user confirms.
- **Adaptive questions** (Julia, Nov 11): Agent 2 asks only what is needed; when nothing more is needed, the summary comes. A question whose fact is already known or was already asked (answered or skipped) is never asked again.
- **Technical fuse, not a product limit:** if an agent keeps asking new questions after 8 answered turns, the Supervisor goes to the summary with the warning `QUESTION_LOOP_GUARD`. A normal dialog never reaches it.
- One turn holds at most 2 questions; each question has its own answer field.
- A new need mentioned in an answer (for example "we have no groceries left") is added to the summary as a proposed need (CR-014).
- `safety_notice` never blocks questions or the plan (Julia, Nov 7).

## 2. How to call it

**HTTP API** (for the browser app; the Python backend calls it, or the browser calls it directly if allowed):
```
python -m navigator.supervisor.http_api --agents agents.json --no-isolate
```
| Method and path | Body | Response |
|---|---|---|
| `GET /health` | — | `{"status": "ok", "dialog_version": "0.2"}` |
| `POST /start` | `{"story_text": "...", "ref_date": "2026-11-13", "locale": "en-US"}` (`ref_date` and `locale` optional) | the response of §4.1 |
| `POST /answer` | `{"case": {...}, "answers": [...]}` | §4.2 |
| `POST /confirm` | `{"case": {...}, "corrections": {...}, "rejected_need_ids": [...], "added_needs": [...]}` | §4.3 |

- Options: `--host` (default 127.0.0.1), `--port` (default 8765), `--agents PATH`, `--kb PATH` (program KB), `--zips PATH` (county ZIP list; default `navigator/kb/sacramento_county_zips.json`), `--no-isolate` (agents run in the server process; recommended for local testing and the demo: without it every agent call starts its own process and each step is slower), `--allow-origin ORIGIN` (a browser page on that one origin, for example `http://localhost:3000`, may call the server; never `*`).
- Every dialog response is HTTP 200, also `status: failed` (for example a missing or wrong `case`). A body that is not a JSON object, or a bad `Content-Length` → 400 with `{"status": "failed", "issues": [{"code": "BAD_REQUEST", ...}]}`; unknown path → 404; wrong method (e.g. `GET /start`) → 405; body over 64 KB → 413. Never a stack trace.
- The server does not log request or response bodies (they hold the user's words).

**Python** (if the backend imports the Supervisor):
```python
from navigator.supervisor.dialog import start, answer, confirm
r1 = start("I have problems with housing and food. I need help.")
r2 = answer(r1["case"], [{"question_id": "q1-1", "answer_text": "My hours were cut at work."}])
r3 = confirm(r2["case"])
```
Optional keyword arguments of all three functions: `agents`, `kb_path`, `zips_path`, `isolate` (default `False`). The functions never raise; a problem comes back as `status: failed`.

**Command line** (for testing without an app):
```
python -m navigator.supervisor.dialog start   --story-file story.txt [--ref-date 2026-11-13] [--locale en-US] --out r1.json
python -m navigator.supervisor.dialog answer  --case-in r1.json --answers-file answers.json --out r2.json
python -m navigator.supervisor.dialog confirm --case-in r2.json [--corrections-file c.json] [--rejected need_002 ...] [--added-file n.json] --out r3.json
```
All three take `--agents`, `--kb`, `--zips`, `--no-isolate`. `--case-in` is the whole previous response file; the other files hold the JSON of the matching field of §4. Exit code 0, 1 when the status is `failed`, 2 for a wrong argument or an unreadable file.

All three ways return the same JSON.

## 3. Common response fields (every call)

| Field | Type | Meaning |
|---|---|---|
| `dialog_version` | string | `"0.2"` |
| `status` | enum | `needs_clarification` · `needs_confirmation` · `completed` · `failed` |
| `case_id` | string | the same for the whole dialog |
| `case_version` | integer | goes up when the user answers or confirms |
| `turn` | integer | question turn number (0 at start if there are no questions) |
| `case` | object | **pass it back unchanged** in the next call; the App Layer does not read or edit it (§6) |
| `questions` | Question[] | only when `needs_clarification`; otherwise `[]` |
| `summary` | Summary or null | only when `needs_confirmation` |
| `plan`, `plan_by_need`, `final_validation`, `rejected_needs` | objects | only when `completed` |
| `limitations` | string[] | plain sentences for the user about what is limited (empty list when nothing is); show them near the plan |
| `safety_notice` | SafetyNotice or null | show above everything else when not null |
| `user_message` | string or null | calm text for the user when `failed` |
| `issues` | Issue[] | technical, for a developer panel or logs, **not** for the user |

**Question** — `{question_id, fact_key, text, can_skip, necessity_level, reason}`
| Field | Meaning |
|---|---|
| `question_id` | e.g. `q2-1` (turn 2, question 1); used in `answer()` |
| `fact_key` | the fact it fills, e.g. `zip_code` |
| `text` | the question to show |
| `can_skip` | `true` → show a "Skip" button; a skipped question is never asked again |
| `necessity_level` | `required_for_decision` · `helpful` |
| `reason` | why we ask (can be shown as a hint) |

**Issue** — `{code, severity, message, related_ref}`; `severity` = `info` · `warning` · `critical`. No user data in `message`.

## 4. The three calls

### 4.1 `start`
**In:** `story_text` (the user's own words), `ref_date` (ISO date, optional; default today; then fixed for the whole dialog), `locale` (optional, default `en-US`; a language tag such as `en-US` or `es-US`, anything else gives `failed` `LOCALE_INVALID`; it is passed to Agent 1, and the team's agents do not use it yet).

The Supervisor masks SSN, card and account-like numbers before any agent sees the text → Agent 1 reads the story → Agent 2 decides what to ask. If nothing is asked but there is no ZIP and it was never asked, the Supervisor asks for the ZIP itself.

**Out — example** (`needs_clarification`), story: "I have problems with housing and food. I need help."
```json
{
  "dialog_version": "0.2",
  "status": "needs_clarification",
  "case_id": "case-3f9a1c2e",
  "case_version": 1,
  "turn": 1,
  "questions": [
    {"question_id": "q1-1", "fact_key": "triggering_circumstances",
     "text": "I'm sorry your family is going through a difficult time. Could you tell me a little more about what happened that led to these financial difficulties?",
     "can_skip": true, "necessity_level": "helpful",
     "reason": "The cause decides which programs fit."}
  ],
  "summary": null, "limitations": [], "safety_notice": null, "user_message": null, "issues": [],
  "case": {"...": "pass back unchanged"}
}
```

### 4.2 `answer`
**In:** `case` (from the last response) and `answers` — one item for **every** question of the turn:
```json
[
  {"question_id": "q2-1", "answer_text": "95823"},
  {"question_id": "q2-2", "answer_text": "About 800 a month"}
]
```
or `{"question_id": "q2-1", "skipped": true}`.
- A question with `can_skip: false` cannot be skipped → `failed` `SKIP_NOT_ALLOWED`, the same questions again, the case unchanged.
- "0" is a real answer (income 0 is stored as 0, never as unknown). `answer_text` may also be sent as a number. An empty answer is recorded as not answered (it shows in `unknown` with `why: "not_answered"`) and the question is not asked again.
- Agent 1 reads each answer for that question's fact and for anything else the person states in it. Facts said beyond the question are kept as proposed and shown on the summary, so they are never asked again (an already known fact is not overwritten this way; the user can correct it on the summary). A fact the answer does not settle stays unknown. A new need mentioned in the answer is added as proposed (it never repeats a need already there).

**Out — `needs_confirmation`** (when nothing more is needed):
```json
{
  "status": "needs_confirmation",
  "case_id": "case-3f9a1c2e", "case_version": 3, "turn": 2, "questions": [],
  "summary": {
    "narrative": "You have problems with housing and food. Your work hours were cut.",
    "needs": [
      {"need_id": "need_001", "category": "food_assistance", "label": "Food",
       "description": "Food problem reported", "urgency": "high",
       "urgency_reason": "Food problem reported", "original_quote": "I have problems with housing and food."},
      {"need_id": "need_002", "category": "housing_assistance", "label": "Housing",
       "description": "Housing problem reported", "urgency": "high",
       "urgency_reason": "Housing problem reported", "original_quote": "I have problems with housing and food."}
    ],
    "facts": [
      {"field": "triggering_circumstances", "label": "What happened", "value": "reduced_hours", "display_value": "reduced hours"},
      {"field": "zip_code", "label": "ZIP code", "value": "95823", "display_value": "95823"},
      {"field": "household_gross_monthly_income", "label": "Monthly household income (before taxes)", "value": 800, "display_value": "$800"},
      {"field": "household_size", "label": "People in your household", "value": 3, "display_value": "3"}
    ],
    "unknown": []
  },
  "limitations": [], "safety_notice": null, "user_message": null, "issues": [],
  "case": {"...": "pass back unchanged"}
}
```
`unknown` lists facts that were asked and skipped or not settled: `{field, label, why: "skipped" | "not_answered"}`.

### 4.3 `confirm`
**In:**
```json
{
  "case": {"...": "from the needs_confirmation response"},
  "corrections": {"household_gross_monthly_income": 1500},
  "rejected_need_ids": ["need_002"],
  "added_needs": [{"category": "utility_assistance", "description": "My electric bill is overdue"}]
}
```
- `corrections`: change or add one of the facts in the summary (`facts` or `unknown`). Unknown field → `failed` `UNKNOWN_FACT_KEY`. The value must fit the fact: money (rent, income, money available, rent owed) a number ≥ 0 or text like `"1500"` or `"1,500"` (stored as a number); dates text `YYYY-MM-DD`; yes/no facts `true` or `false`; other facts text or a number. Otherwise → `failed` `FACT_VALUE_INVALID`. On any of these nothing is changed.
- `rejected_need_ids`: needs the user says are not theirs. Each must be a need of the case (else `UNKNOWN_NEED_ID`). Rejected needs are not planned and are listed back in `rejected_needs`. Rejecting every need → `failed` `NO_NEEDS_LEFT` with the same summary.
- `added_needs`: `category` must be one of: `food_assistance`, `housing_assistance`, `income_assistance`, `utility_assistance`, `medical_health_coverage`, `debt_hardship`, `material_in_kind`, `crowdfunding_guidance`, `other_unlisted` (else `UNKNOWN_ENUM`); a category already present → `NEED_ALREADY_PRESENT`. `description` up to 200 characters; numbers like SSN are masked.
- All three are optional; `confirm(case)` alone confirms the summary as it is.

**Out — `completed`** (card shortened from a real run):
```json
{
  "status": "completed",
  "case_id": "case-3f9a1c2e", "case_version": 4,
  "plan": {
    "plan_version": "plan-001",
    "action_cards": [
      {"card_id": "card_01", "related_need_ids": ["need_001"], "program_id": "prog_food_calfresh_sac_001",
       "action_title": "Check food benefits: Sacramento County Department of Human Assistance (DHA), CalFresh",
       "next_step": "Contact the provider or apply through the official site. They decide eligibility based on your household. Apply by phone: 1-800-560-0976 (checked Oct 21).",
       "order_group": "first", "progress_status": "not_started",
       "contacts": [{"label": "Apply by phone", "value": "1-800-560-0976", "hours": null, "checked_at": "2026-10-21"}],
       "...": "other card fields as in run_report.json"}
    ],
    "potential_options": [], "coverage_gaps": [], "withheld_card_ids": [], "withheld_cards": []
  },
  "plan_by_need": [
    {"need_id": "need_001", "category": "food_assistance", "label": "Food",
     "urgency": "high", "urgency_reason": "Food problem reported", "card_ids": ["card_01"], "gap_notes": []},
    {"need_id": "need_002", "category": "housing_assistance", "label": "Housing",
     "urgency": "high", "urgency_reason": "Housing problem reported", "card_ids": ["card_02", "card_03"], "gap_notes": []}
  ],
  "rejected_needs": [],
  "final_validation": {"verdict": "PASS", "repair_rounds_used": 0, "flags": [], "passed_card_ids": ["card_01", "card_02", "card_03"]},
  "limitations": [], "safety_notice": null, "user_message": null, "issues": [],
  "case": {"...": "the confirmed case"}
}
```
- `plan` is the plan of `run_report.json` (contract §4.8 plus `contacts[]`).
- `plan_by_need`: rows follow the plan's own order (the position of each need's first card); needs with no card come last. **Urgency is a label only** (Julia, Nov 11). A card serving two needs appears under both. `gap_notes` explain a need with no verified program. A need with neither card nor gap gets, in its row, the `gap_notes` sentence "We have not found a verified program for this need yet." for the user, plus the warning `NEED_NOT_IN_PLAN` for developers. It never disappears, and nothing promises that a search is still going on (Julia).
- `withheld_cards`: cards the final check did not release; show "We could not verify this option yet", not the technical reason.
- `progress_status` starts as `not_started`; only the user changes it (six statuses, contract §3.6). Storing progress between visits comes with Case State (§6).

### 4.4 `failed` (any call)
```json
{
  "status": "failed", "case_id": "case-3f9a1c2e", "case_version": 2,
  "user_message": "Something went wrong on our side. Your answers are saved. Please try again.",
  "issues": [{"code": "SUPERVISOR_INPUT_ERROR", "severity": "critical", "message": "agent_3 input could not be processed: KeyError: need_id", "related_ref": null}],
  "case": {"...": "the last good case — retry the same call with it"}
}
```

**Issue codes** the App Layer may see:
| Code | When | What to show the user |
|---|---|---|
| `SKIP_NOT_ALLOWED` | a required question was skipped | the same question, marked required |
| `UNKNOWN_QUESTION_ID`, `UNKNOWN_FACT_KEY`, `UNKNOWN_NEED_ID`, `UNKNOWN_ENUM` | the App Layer sent a wrong id or value | a developer bug: fix the request |
| `NEED_ALREADY_PRESENT`, `NO_NEEDS_LEFT` | need editing at confirmation | "This need is already in your list" / "Please keep at least one need" |
| `FACT_VALUE_INVALID` | a correction has the wrong type or format | ask the user to check the value |
| `LOCALE_INVALID` | `locale` in `start` is not a language tag such as `en-US` | a developer bug: fix the request |
| `CASE_INVALID`, `WRONG_STAGE` | the case is broken, or e.g. `confirm` before the questions are done | a developer bug: send the last case to the right call |
| `SUPERVISOR_INPUT_ERROR`, `AGENT_FAILED`, `TIMEOUT`, `SCHEMA_INVALID` | something failed inside | `user_message`; let the user retry |
| `GEOGRAPHY_MISSING` (warning) | the ZIP was skipped | the `limitations` sentence |
| `QUESTION_DROPPED`, `QUESTION_LOOP_GUARD`, `ANSWER_FACT_OUTSIDE_QUESTION`, `ANSWER_FACT_CONFLICT`, `ANSWER_FACT_INVALID`, `ANSWER_NEED_DUPLICATE`, `ANSWER_NEED_INVALID`, `ANSWER_NEEDS_INVALID`, `NEED_NOT_IN_PLAN`, `PII_MASKED`, `COUNTY_UNKNOWN`, `COUNTY_FROM_ZIP_LIST`, `ZIP_LIST_UNAVAILABLE`, `FACT_LABEL_MISSING`, `SAFETY_CONTACT_UNVERIFIED`, `MOCK_COMPONENT`, and the agent check codes of a stopped plan (e.g. `UNKNOWN_REFERENCE`) | information for developers | nothing |

`STALE_CASE` (an older case sent back) needs a store and is not detected in the MVP.

## 5. Safety
- **The app shows 911 and 988 at all times** (Julia, Nov 11).
- `safety_notice` appears only when Agent 1 raises a safety flag for a direct threat to physical safety; from then on it is in every response. It never blocks the questions or the plan.
- A landlord's threat to change the locks is a housing and legal issue: no `safety_notice`; the plan carries housing and legal help.
```json
"safety_notice": {
  "risk_type": "safety",
  "message": "If you or someone with you is in danger right now, call 9-1-1. You can keep going with your plan below.",
  "contacts": [
    {"name": "9-1-1 Emergency", "value": "9-1-1", "hours": null, "checked_at": "2026-11-06"},
    {"name": "988 Suicide & Crisis Lifeline", "value": "Call or text 988.", "hours": null, "checked_at": "2026-11-06"}
  ],
  "blocks_plan": false
}
```
Contacts come from `navigator/kb/emergency/emergency_directory.json` (Silver, PR #16): only the 9-1-1 record and the 988 record, 9-1-1 first, and only contact lines whose evidence is verified (the 988 record also has verified lines in Spanish and for veterans; they are included). Local police non-emergency records in the same directory never appear in this notice. If the directory cannot be read or has no verified line, the notice comes without contacts and `issues` carries `SAFETY_CONTACT_UNVERIFIED`. The notice is also kept in a `failed` response.
- Known limit: a threat stated only in an answer, not in the story, does not raise the notice yet (Agent 1 does not return safety flags when it reads an answer; the Supervisor accepts them once it does).

## 6. The `case` object (reference only — pass it back unchanged)
```json
{
  "case_id": "case-3f9a1c2e", "run_id": "run-3f9a1c2e", "correlation_id": "corr-3f9a1c2e",
  "case_version": 2, "stage": "clarifying", "turn": 1, "ref_date": "2026-11-13",
  "next_request_seq": 4, "narrative_summary": "...",
  "needs": [], "case_facts": [], "already_asked": ["triggering_circumstances"],
  "ambiguity_flags": [], "safety_flags": [], "limitations": [], "skipped_keys": [],
  "pending_questions": [{"question_id": "q1-1", "fact_key": "triggering_circumstances", "text": "...",
                         "can_skip": true, "necessity_level": "helpful", "reason": "..."}]
}
```
- `stage`: `clarifying` → `awaiting_confirmation` → `completed`.
- It holds the user's facts (masked), never the raw story. Keep it only in the user's session; never write it to logs.
- For the MVP tests it can live in the session. Persistent storage (My Case, Case State SQLite by Silver) stays in the architecture: only the Supervisor writes to it, after its checks; it is connected after the dialog mode works.

## 7. Decisions behind this version
| Question | Decision (Julia, Nov 11) |
|---|---|
| App Layer | browser app with a Python backend → HTTP API |
| Case storage | session for first tests; SQLite / My Case stays in the architecture |
| Question turns | adaptive, no fixed limit, no repeated or irrelevant questions |
| Needs at confirmation | the user can correct, add and remove needs |
| ZIP | asked when needed for local programs; can be skipped; the limitation is said, the process goes on |
| Action Plan | `plan_by_need` fits; urgency separate from display order; progress tracking and plan updates stay |
| Lockout threat | housing and legal issue, not a safety notice; 911 and 988 always visible |
