# ### Task: Implement Context-First Circumstance Clarification in Agent 1 & Agent 2

Modify `navigator/agents/agent_1_2/agent_1.py`, `navigator/agents/agent_1_2/agent_2.py`, and `tests/agent_1_2/test_agent_2_unittest.py` using Python 3.11+ standard library.

---

#### 1. File: `navigator/agents/agent_1_2/agent_1.py`
In `handle_agent_1`:
- Detect whether any root cause / triggering event is present in `story_text` (e.g., job loss, laid off, fired, medical emergency, illness, accident, rent increase, unexpected bill).
- If the story expresses needs (`food`, `housing`, or `income`) but lacks ANY specific root cause/triggering event:
  - Add `"unspecified_hardship_cause"` to `ambiguity_flags`.
  - Do not invent triggering events.

---

#### 2. File: `navigator/agents/agent_1_2/agent_2.py`
In `handle_agent_2`:
- **Step 1 (Circumstance-First Gate):** Check if `"unspecified_hardship_cause"` is in `ambiguity_flags`:
  - If `triggering_circumstances` is NOT in `already_asked` and NOT in `case_facts`:
    - Return a single clarification request:
      - `fact_key`: `"triggering_circumstances"`
      - `question_intent`: `"Identify root cause and circumstances of hardship"`
      - `user_facing_question`: `"I'm sorry your family is going through a difficult time. Could you tell me a little more about what happened that led to these financial difficulties?"`
      - `reason`: `"Understanding what caused the hardship determines applicable crisis and emergency programs"`
      - `applicable_program_ids`: `[]`
      - `verified_rule_ref`: `None`
      - `necessity_level`: `"helpful_for_discovery"`
      - `can_skip`: `True`
    - Do NOT ask for `household_gross_monthly_income` on this turn.
- **Step 2 (De-prioritize Default Income):** Never ask for `household_gross_monthly_income` as an automatic first question when `unspecified_hardship_cause` is present. Only ask about income after circumstances are established or when candidate requirements are provided.

---

#### 3. File: `tests/agent_1_2/test_agent_2_unittest.py`
Add a multi-turn scenario test:
- User story: `"Hi, I need help with food and rent. I'm having financial problems and I'm worried about how my family will get through next month."`
- Assert that Agent 1 flags `"unspecified_hardship_cause"`.
- Assert that Agent 2's first question is the circumstance question: `"I'm sorry your family is going through a difficult time. Could you tell me a little more about what happened that led to these financial difficulties?"`
- Assert that Agent 2 does NOT ask for `household_gross_monthly_income` on this turn.

---

#### 4. Verification:
Run test discovery:
`python -m unittest discover -s tests -t .`

---

**Status:** active  **Date:** 2026-11-08

---

### 👤 User

### Task: Implement Context-First Circumstance Clarification in Agent 1 & Agent 2

Modify `navigator/agents/agent_1_2/agent_1.py`, `navigator/agents/agent_1_2/agent_2.py`, and `tests/agent_1_2/test_agent_2_unittest.py` using Python 3.11+ standard library.

---

#### 1. File: `navigator/agents/agent_1_2/agent_1.py`
In `handle_agent_1`:
- Detect whether any root cause / triggering event is present in `story_text` (e.g., job loss, laid off, fired, medical emergency, illness, accident, rent increase, unexpected bill).
- If the story expresses needs (`food`, `housing`, or `income`) but lacks ANY specific root cause/triggering event:
  - Add `"unspecified_hardship_cause"` to `ambiguity_flags`.
  - Do not invent triggering events.

---

#### 2. File: `navigator/agents/agent_1_2/agent_2.py`
In `handle_agent_2`:
- **Step 1 (Circumstance-First Gate):** Check if `"unspecified_hardship_cause"` is in `ambiguity_flags`:
  - If `triggering_circumstances` is NOT in `already_asked` and NOT in `case_facts`:
    - Return a single clarification request:
      - `fact_key`: `"triggering_circumstances"`
      - `question_intent`: `"Identify root cause and circumstances of hardship"`
      - `user_facing_question`: `"I'm sorry your family is going through a difficult time. Could you tell me a little more about what happened that led to these financial difficulties?"`
      - `reason`: `"Understanding what caused the hardship determines applicable crisis and emergency programs"`
      - `applicable_program_ids`: `[]`
      - `verified_rule_ref`: `None`
      - `necessity_level`: `"helpful_for_discovery"`
      - `can_skip`: `True`
    - Do NOT ask for `household_gross_monthly_income` on this turn.
- **Step 2 (De-prioritize Default Income):** Never ask for `household_gross_monthly_income` as an automatic first question when `unspecified_hardship_cause` is present. Only ask about income after circumstances are established or when candidate requirements are provided.

---

#### 3. File: `tests/agent_1_2/test_agent_2_unittest.py`
Add a multi-turn scenario test:
- User story: `"Hi, I need help with food and rent. I'm having financial problems and I'm worried about how my family will get through next month."`
- Assert that Agent 1 flags `"unspecified_hardship_cause"`.
- Assert that Agent 2's first question is the circumstance question: `"I'm sorry your family is going through a difficult time. Could you tell me a little more about what happened that led to these financial difficulties?"`
- Assert that Agent 2 does NOT ask for `household_gross_monthly_income` on this turn.

---

#### 4. Verification:
Run test discovery:
`python -m unittest discover -s tests -t .`

---

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[-] Read existing agent_1.py, agent_2.py, and test file to understand current structure
[ ] Modify agent_1.py: add unspecified_hardship_cause detection
[ ] Modify agent_2.py: add circumstance-first gate and de-prioritize income question
[ ] Modify test file: add multi-turn scenario test
[ ] Run test discovery to verify


### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file



> 🔧 **read_file** — tests\agent_1_2\test_agent_2_unittest.py

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_2.py

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: read_file

Now let me read the `handle_agent_1` function to understand its structure:

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — _understand_story function: ambiguity_flags, needs detection, result structure, what triggers ambiguity_flags

### 🤖 Assistant

> 🔧 called: read_file

Now I have a complete picture. Let me also look at what the existing regex patterns look like for triggering events (around lines 147-170):

> 🔧 **read_file** — RE_JOB_LOSS, RE_BEREAVEMENT regex pattern definitions

### 🤖 Assistant

> 🔧 called: update_todo_list

Now I have everything I need. Let me implement all three changes:

> 🔧 **update_todo_list** — 
[x] Read existing agent_1.py, agent_2.py, and test file to understand current structure
[-] Modify agent_1.py: add unspecified_hardship_cause detection
[ ] Modify agent_2.py: add circumstance-first gate and de-prioritize income question
[ ] Modify test file: add multi-turn scenario test
[ ] Run test discovery to verify


### 🤖 Assistant

> 🔧 called: apply_diff

**`agent_1.py`** — Add a regex for triggering events and populate `ambiguity_flags` when needs are present but no triggering event is found:

> 🔧 **apply_diff** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: apply_diff

I left the dead intermediate `has_aid_need` assignment in. Let me clean that up:

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:782
-------
    # 13. Ambiguity: unspecified hardship cause
    ambiguity_flags: List[str] = []
    has_aid_need = any(
        re.search(r"\b(food|groceries|eat|hungry|pantry)\b", story_lower)
        or re.search(r"\b(rent|housing|shelter|homeless)\b", story_lower)
        or re.search(r"\b(income|money|financial|afford)\b", story_lower)
        for _ in [1]  # single-pass — evaluated once
    )
    has_aid_need = bool(
        re.search(r"\b(food|groceries|eat|hungry|pantry|rent|housing|shelter|homeless|income|money|financial|afford)\b", story_lower)
    )
=======
    # 13. Ambiguity: unspecified hardship cause
    ambiguity_flags: List[str] = []
    has_aid_need = bool(
        re.search(r"\b(food|groceries|eat|hungry|pantry|rent|housing|shelter|homeless|income|money|financial|afford)\b", story_lower)
    )
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: update_todo_list

Now modify **`agent_2.py`** — add the circumstance-first gate (Step 1) before the income question block, and guard the income question from firing when `unspecified_hardship_cause` is present:

> 🔧 **update_todo_list** — 
[x] Read existing agent_1.py, agent_2.py, and test file to understand current structure
[x] Modify agent_1.py: add unspecified_hardship_cause detection
[-] Modify agent_2.py: add circumstance-first gate and de-prioritize income question
[ ] Modify test file: add multi-turn scenario test
[ ] Run test discovery to verify


### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — navigator\agents\agent_1_2\agent_2.py

### 🤖 Assistant

> 🔧 called: update_todo_list

Now add the test. I need to check what `handle_agent_1` import looks like in the test file, then add the new test:

> 🔧 **update_todo_list** — 
[x] Read existing agent_1.py, agent_2.py, and test file to understand current structure
[x] Modify agent_1.py: add unspecified_hardship_cause detection
[x] Modify agent_2.py: add circumstance-first gate and de-prioritize income question
[-] Modify test file: add multi-turn scenario test
[ ] Run test discovery to verify


### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:7
-------
from navigator.agents.agent_1_2.agent_2 import handle_agent_2
=======
from navigator.agents.agent_1_2.agent_1 import handle_agent_1
from navigator.agents.agent_1_2.agent_2 import handle_agent_2
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:64
-------
if __name__ == "__main__":
    unittest.main()
=======
    def test_unspecified_hardship_circumstance_clarification(self):
        """Multi-turn: vague story → Agent 1 flags unspecified_hardship_cause →
        Agent 2 asks for circumstances first, NOT income."""
        story = (
            "Hi, I need help with food and rent. "
            "I'm having financial problems and I'm worried about how my family will get through next month."
        )
        a1_req = {
            "request_id": "req-a1-circ",
            "run_id": "run-0001",
            "case_id": "case-circ-001",
            "case_version": 1,
            "task_type": "understand_story",
            "payload": {"story_text": story},
        }
        a1_res = handle_agent_1(a1_req)
        self.assertEqual(a1_res["status"], "completed")
        ambiguity_flags = a1_res["result"]["ambiguity_flags"]
        self.assertIn("unspecified_hardship_cause", ambiguity_flags)

        a2_req = {
            "request_id": "req-a2-circ",
            "run_id": "run-0001",
            "case_id": "case-circ-001",
            "case_version": 1,
            "task_type": "clarify_case",
            "payload": {
                "needs": a1_res["result"]["proposed_needs"],
                "case_facts": a1_res["result"]["factual_claims"],
                "already_asked": [],
                "candidate_requirements": [],
                "ambiguity_flags": ambiguity_flags,
            },
        }
        a2_res = handle_agent_2(a2_req)
        self.assertEqual(a2_res["status"], "needs_clarification")
        self.assertEqual(len(a2_res["clarification_requests"]), 1)

        first_q = a2_res["clarification_requests"][0]
        self.assertEqual(first_q["fact_key"], "triggering_circumstances")
        self.assertEqual(
            first_q["user_facing_question"],
            "I'm sorry your family is going through a difficult time. "
            "Could you tell me a little more about what happened that led to these financial difficulties?",
        )

        asked_keys = [r["fact_key"] for r in a2_res["clarification_requests"]]
        self.assertNotIn("household_gross_monthly_income", asked_keys)


if __name__ == "__main__":
    unittest.main()
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: update_todo_list

Now run the test suite:

> 🔧 **update_todo_list** — 
[x] Read existing agent_1.py, agent_2.py, and test file to understand current structure
[x] Modify agent_1.py: add unspecified_hardship_cause detection
[x] Modify agent_2.py: add circumstance-first gate and de-prioritize income question
[x] Modify test file: add multi-turn scenario test
[-] Run test discovery to verify


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python -m unittest discover -s tests -t . 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

The single failing test (`test_planning_package_availability_and_timing`) is pre-existing and completely unrelated to the changes here (it's in `tests/test_builders.py` and checks a program's open/closed status). All three new tests in `test_agent_2_unittest.py` passed. Let me confirm by running just the targeted test file:

> 🔧 **execute_command** — python -m unittest tests.agent_1_2.test_agent_2_unittest -v 2>&1

### 🤖 Assistant

> 🔧 called: update_todo_list

All 3 tests pass (exit code 1 here is a PowerShell stderr-redirect artifact — the `OK` and `Ran 3 tests` confirm success). The pre-existing unrelated failure is unchanged.

> 🔧 **update_todo_list** — 
[x] Read existing agent_1.py, agent_2.py, and test file to understand current structure
[x] Modify agent_1.py: add unspecified_hardship_cause detection
[x] Modify agent_2.py: add circumstance-first gate and de-prioritize income question
[x] Modify test file: add multi-turn scenario test
[x] Run test discovery to verify


### 🤖 Assistant

All three files are updated and tests pass. Here's a summary of every change:

---

### Changes made

#### [`navigator/agents/agent_1_2/agent_1.py`](navigator/agents/agent_1_2/agent_1.py)

1. **New regex `RE_TRIGGERING_EVENT`** (after `RE_JOB_LOSS`, line ~158) — matches all documented root-cause/triggering terms: job loss, medical emergency, illness, accident, injury, hospital, rent increase, unexpected bill, bereavement, divorce, disability, disaster, fire, eviction.

2. **Section 13 in `_understand_story`** (before the `env["result"]` assignment) — after all fact/need extraction:
   - Checks if the story mentions any food/housing/income need via regex.
   - Checks if `RE_TRIGGERING_EVENT` matches anything in the story.
   - If needs present **and** no triggering event found → appends `"unspecified_hardship_cause"` to `ambiguity_flags`.
   - `ambiguity_flags` is now returned in `env["result"]` instead of the previous hardcoded `[]`.

#### [`navigator/agents/agent_1_2/agent_2.py`](navigator/agents/agent_1_2/agent_2.py)

1. **Reads `ambiguity_flags`** from `payload` (alongside the other payload fields).

2. **Step 1 — Circumstance-First Gate** (new block before the income question):
   - If `"unspecified_hardship_cause"` is in `ambiguity_flags` and `triggering_circumstances` has not been asked and is not in `case_facts` — returns **immediately** with the single circumstance question (`fact_key: "triggering_circumstances"`), bypassing income and all other questions entirely for this turn.

3. **Step 2 — Income guard**: the income question condition gains `and not unspecified_hardship`, so it is never emitted on the same turn as an unresolved hardship cause.

#### [`tests/agent_1_2/test_agent_2_unittest.py`](tests/agent_1_2/test_agent_2_unittest.py)

- Added `from navigator.agents.agent_1_2.agent_1 import handle_agent_1` import.
- Added **`test_unspecified_hardship_circumstance_clarification`** — a full multi-turn scenario:
  - Runs Agent 1 on the vague story, asserts `"unspecified_hardship_cause"` is flagged.
  - Passes the flags into Agent 2, asserts exactly one clarification request with `fact_key = "triggering_circumstances"` and the specified question text.
  - Asserts `"household_gross_monthly_income"` is **not** asked on that turn.