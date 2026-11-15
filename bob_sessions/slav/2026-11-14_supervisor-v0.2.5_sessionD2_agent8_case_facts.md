# Task: Supervisor, Session D2 — Agent 8 receives the confirmed case facts.

Repository: new branch `slav/agent8-case-facts` from the current main (`b1d9110`: #24 and #28 merged). The new test file `tests/test_agent8_case_facts.py` is already in the folder (I put it there; do not change it).

Why: Hisham's Agent 8 (#24, merged) adds the police non-emergency sentence to a lockout card. It learns about the lockout from the case facts, but the Supervisor sends the facts only to Agent 10 (`allowed_case_facts`), not to Agent 8. Fix: one argument in `agent8_request` (the first plan and every repair round), and one README sentence. PROPOSED for contracts v1.2 (4.8 "In" does not list the facts yet). No agent code changes.
Checked on a copy of this main: 530 tests OK (528 before; 2 new tests). All dialog scenarios on the team's agents pass with no WARN: the lockout plan has 11 cards and the legal-aid card ends with the police non-emergency sentence (before this change: one WARN, LOCKOUT).

Rules (budget is limited):
- Part 1: apply the 2 changes below exactly. One apply_diff per file: `navigator/supervisor/builders.py`, `navigator/supervisor/README.md`. Do not reformat anything. Do not read other files.
- Part 2: run only the commands I list, one at a time, exactly as written. Do not change any file in Part 2.
- Part 3: report and stop.

PART 1 — the changes

## navigator/supervisor/builders.py

Change 1
FIND:
```
    payload["ref_date"] = _ref_date_iso(ref_date, "agent8_request")
    return make_request(state, "agent_8", "build_plan", payload,
                        upstream_result_refs=[agent6_req["request_id"]])
```
REPLACE:
```
    payload["ref_date"] = _ref_date_iso(ref_date, "agent8_request")
    # The confirmed case facts, as for Agent 10, so a card can follow what the person said
    # (e.g. a lockout). PROPOSED for contracts v1.2 (4.8 "In" does not list them yet).
    return make_request(state, "agent_8", "build_plan", payload,
                        allowed_case_facts=state.case_facts,
                        upstream_result_refs=[agent6_req["request_id"]])
```


## navigator/supervisor/README.md

Change 2
FIND:
```
user dates from case facts; official deadlines only from the KB).
```
REPLACE:
```
user dates from case facts; official deadlines only from the KB); the confirmed case facts in `allowed_case_facts` for Agents 8 (also in repair rounds) and 10, so a card can follow what the person said, for example a lockout (Agent 8: PROPOSED for contracts v1.2).
```

PART 2 — the checks (I approve each command)

1. The full test suite:
```
python -I -W always::ResourceWarning -m unittest discover -s tests -t .; echo "EXIT: $LASTEXITCODE"
```
Expected: only dots, then `Ran 530 tests` and `OK`.

2. All dialog scenarios on the team's real agents, directly, into a folder outside the repository:
```
python -I tools/run_dialog_scenarios.py --repo . --agents agents.json --out "$env:TEMP\session_d2_check" --no-isolate --ref-date 2026-11-14; echo "EXIT: $LASTEXITCODE"
```
Expected: `FAIL: 0`, `WARN: 0`, `UNPLANNED: 0`, `EXIT: 0`.

PART 3 — the report
Report the last lines of each command's output and whether they match; each change you could not apply exactly; anything that looks wrong to you (a real defect). Then stop. Do not fix anything in this task.

---

**Status:** active  **Date:** 2026-11-15

---

### 👤 User

Task: Supervisor, Session D2 — Agent 8 receives the confirmed case facts.

Repository: new branch `slav/agent8-case-facts` from the current main (`b1d9110`: #24 and #28 merged). The new test file `tests/test_agent8_case_facts.py` is already in the folder (I put it there; do not change it).

Why: Hisham's Agent 8 (#24, merged) adds the police non-emergency sentence to a lockout card. It learns about the lockout from the case facts, but the Supervisor sends the facts only to Agent 10 (`allowed_case_facts`), not to Agent 8. Fix: one argument in `agent8_request` (the first plan and every repair round), and one README sentence. PROPOSED for contracts v1.2 (4.8 "In" does not list the facts yet). No agent code changes.
Checked on a copy of this main: 530 tests OK (528 before; 2 new tests). All dialog scenarios on the team's agents pass with no WARN: the lockout plan has 11 cards and the legal-aid card ends with the police non-emergency sentence (before this change: one WARN, LOCKOUT).

Rules (budget is limited):
- Part 1: apply the 2 changes below exactly. One apply_diff per file: `navigator/supervisor/builders.py`, `navigator/supervisor/README.md`. Do not reformat anything. Do not read other files.
- Part 2: run only the commands I list, one at a time, exactly as written. Do not change any file in Part 2.
- Part 3: report and stop.

PART 1 — the changes

## navigator/supervisor/builders.py

Change 1
FIND:
```
    payload["ref_date"] = _ref_date_iso(ref_date, "agent8_request")
    return make_request(state, "agent_8", "build_plan", payload,
                        upstream_result_refs=[agent6_req["request_id"]])
```
REPLACE:
```
    payload["ref_date"] = _ref_date_iso(ref_date, "agent8_request")
    # The confirmed case facts, as for Agent 10, so a card can follow what the person said
    # (e.g. a lockout). PROPOSED for contracts v1.2 (4.8 "In" does not list them yet).
    return make_request(state, "agent_8", "build_plan", payload,
                        allowed_case_facts=state.case_facts,
                        upstream_result_refs=[agent6_req["request_id"]])
```


## navigator/supervisor/README.md

Change 2
FIND:
```
user dates from case facts; official deadlines only from the KB).
```
REPLACE:
```
user dates from case facts; official deadlines only from the KB); the confirmed case facts in `allowed_case_facts` for Agents 8 (also in repair rounds) and 10, so a card can follow what the person said, for example a lockout (Agent 8: PROPOSED for contracts v1.2).
```

PART 2 — the checks (I approve each command)

1. The full test suite:
```
python -I -W always::ResourceWarning -m unittest discover -s tests -t .; echo "EXIT: $LASTEXITCODE"
```
Expected: only dots, then `Ran 530 tests` and `OK`.

2. All dialog scenarios on the team's real agents, directly, into a folder outside the repository:
```
python -I tools/run_dialog_scenarios.py --repo . --agents agents.json --out "$env:TEMP\session_d2_check" --no-isolate --ref-date 2026-11-14; echo "EXIT: $LASTEXITCODE"
```
Expected: `FAIL: 0`, `WARN: 0`, `UNPLANNED: 0`, `EXIT: 0`.

PART 3 — the report
Report the last lines of each command's output and whether they match; each change you could not apply exactly; anything that looks wrong to you (a real defect). Then stop. Do not fix anything in this task.

---

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[-] Part 1a: Apply change to navigator/supervisor/builders.py
[ ] Part 1b: Apply change to navigator/supervisor/README.md
[ ] Part 2a: Run full test suite
[ ] Part 2b: Run dialog scenarios
[ ] Part 3: Report


### 🤖 Assistant

> 🔧 called: grep, grep

First, let me find the exact lines in both files:

> 🔧 **grep** — user dates from case facts

> 🔧 **grep** — payload\[.ref_date.\] = _ref_date_iso\(ref_date, .agent8_request.\)

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — navigator\supervisor\builders.py

### 🤖 Assistant

> 🔧 called: apply_diff

Now apply both changes:

> 🔧 **apply_diff** — navigator\supervisor\builders.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — full line 9 containing user dates from case facts

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — navigator\supervisor\README.md

### 🤖 Assistant

> 🔧 called: search_and_replace

The file is a long single line at line 9. I need to use `search_and_replace` instead:

> 🔧 **search_and_replace** — navigator\supervisor\README.md

### 🤖 Assistant

> 🔧 called: update_todo_list

Both changes applied. Now Part 2:

> 🔧 **update_todo_list** — 
[x] Part 1a: Apply change to navigator/supervisor/builders.py
[x] Part 1b: Apply change to navigator/supervisor/README.md
[-] Part 2a: Run full test suite
[ ] Part 2b: Run dialog scenarios
[ ] Part 3: Report


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python -I -W always::ResourceWarning -m unittest discover -s tests -t .; echo "EXIT: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Part 1a: Apply change to navigator/supervisor/builders.py
[x] Part 1b: Apply change to navigator/supervisor/README.md
[x] Part 2a: Run full test suite
[-] Part 2b: Run dialog scenarios
[ ] Part 3: Report


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python -I tools/run_dialog_scenarios.py --repo . --agents agents.json --out "$env:TEMP\session_d2_check" --no-isolate --ref-date 2026-11-14; echo "EXIT: $LASTEXITCODE"

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Part 1a: Apply change to navigator/supervisor/builders.py
[x] Part 1b: Apply change to navigator/supervisor/README.md
[x] Part 2a: Run full test suite
[x] Part 2b: Run dialog scenarios
[-] Part 3: Report


### 🤖 Assistant

---

## Part 3 — Report

### Changes applied

**Change 1 — [`navigator/supervisor/builders.py`](navigator/supervisor/builders.py:513):** Applied exactly as specified. The two-line comment and the `allowed_case_facts=state.case_facts` keyword argument were inserted into the `agent8_request` return call.

**Change 2 — [`navigator/supervisor/README.md`](navigator/supervisor/README.md:9):** Applied exactly as specified. The sentence ending `…official deadlines only from the KB).` was extended with the new clause about `allowed_case_facts` for Agents 8 and 10.

---

### Command 1 — full test suite

```
Ran 530 tests in 12.777s
OK
EXIT: 0
```

✅ Matches expected: `Ran 530 tests` and `OK`.

---

### Command 2 — dialog scenarios

```
FAIL: 0
WARN: 0
UNPLANNED: 0
EXIT: 0
```

✅ Matches expected exactly. The LOCKOUT scenario ran with 11 released cards, 0 withheld, verdict PASS, no WARN — consistent with the description that before this change it produced one WARN on LOCKOUT.

---

### Anything that looks wrong

Nothing. Both changes applied exactly as written, all 530 tests pass, all dialog scenarios pass with zero FAIL / WARN / UNPLANNED.