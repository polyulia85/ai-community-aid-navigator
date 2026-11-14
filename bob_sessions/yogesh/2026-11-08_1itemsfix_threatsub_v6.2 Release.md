# ### Task: Add Partner/Family Subjects to Threat Pattern and Add Test Cases

#### 1. File: `navigator/agents/agent_1_2/agent_1.py`
In `_HARM_SUBJECTS`:
- Keep the leading `\b` anchor.
- Add `boyfriend`, `girlfriend`, `fiance`, `fiancee`, `stepfather`, and `stepmother` to the relationship nouns.
- Ensure "My boyfriend will hurt me.", "My girlfriend is going to hurt the kids.", and "My boyfriend said he would kill us." trigger safety flags.
- Preserve negative patterns so "headache/toothache/backache will kill me" remain unflagged.

#### 2. File: `tests/agent_1_2/test_agent_1_unittest.py`
In `test_broadened_life_safety_signals`:
- Add these three must-flag positive tests:
  - "My boyfriend will hurt me."
  - "My girlfriend is going to hurt the kids."
  - "My boyfriend said he would kill us."
- Ensure all pain negatives ("headache will kill me", etc.) remain in `test_safety_signals_negative_everyday_sentences`.

#### 3. Verification:
Run test discovery:
`python -m unittest discover -s tests -t .`

---

**Status:** active  **Date:** 2026-11-08

---

### 👤 User

### Task: Add Partner/Family Subjects to Threat Pattern and Add Test Cases

#### 1. File: `navigator/agents/agent_1_2/agent_1.py`
In `_HARM_SUBJECTS`:
- Keep the leading `\b` anchor.
- Add `boyfriend`, `girlfriend`, `fiance`, `fiancee`, `stepfather`, and `stepmother` to the relationship nouns.
- Ensure "My boyfriend will hurt me.", "My girlfriend is going to hurt the kids.", and "My boyfriend said he would kill us." trigger safety flags.
- Preserve negative patterns so "headache/toothache/backache will kill me" remain unflagged.

#### 2. File: `tests/agent_1_2/test_agent_1_unittest.py`
In `test_broadened_life_safety_signals`:
- Add these three must-flag positive tests:
  - "My boyfriend will hurt me."
  - "My girlfriend is going to hurt the kids."
  - "My boyfriend said he would kill us."
- Ensure all pain negatives ("headache will kill me", etc.) remain in `test_safety_signals_negative_everyday_sentences`.

#### 3. Verification:
Run test discovery:
`python -m unittest discover -s tests -t .`

---

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — tests\agent_1_2\test_agent_1_unittest.py

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: read_file

Now let me read the `_HARM_SUBJECTS` pattern:

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: update_todo_list

Now I have a clear picture. Let me update both files:

> 🔧 **update_todo_list** — [-] Add boyfriend/girlfriend/fiance/fiancee/stepfather/stepmother to _HARM_SUBJECTS in agent_1.py
[ ] Add three new positive test cases to test_broadened_life_safety_signals in test_agent_1_unittest.py
[ ] Run test discovery to verify


### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — [x] Add boyfriend/girlfriend/fiance/fiancee/stepfather/stepmother to _HARM_SUBJECTS in agent_1.py
[-] Add three new positive test cases to test_broadened_life_safety_signals in test_agent_1_unittest.py
[ ] Run test discovery to verify


### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — tests\agent_1_2\test_agent_1_unittest.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — [x] Add boyfriend/girlfriend/fiance/fiancee/stepfather/stepmother to _HARM_SUBJECTS in agent_1.py
[x] Add three new positive test cases to test_broadened_life_safety_signals in test_agent_1_unittest.py
[-] Run test discovery to verify


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python -m unittest discover -s tests -t .

### 🤖 Assistant

> 🔧 called: execute_command

The single failure is in [`test_planning_package_availability_and_timing`](tests/test_builders.py:105) — it's an unrelated pre-existing test in a different file that checks a knowledge base record, not anything touched by this change. All agent_1_2 tests pass.

Let me confirm by running only the agent_1_2 test suite:

> 🔧 **execute_command** — python -m unittest discover -s tests/agent_1_2 -t .

### 🤖 Assistant

> 🔧 called: update_todo_list

All 60 agent_1_2 tests pass, including the 3 new ones.

> 🔧 **update_todo_list** — [x] Add boyfriend/girlfriend/fiance/fiancee/stepfather/stepmother to _HARM_SUBJECTS in agent_1.py
[x] Add three new positive test cases to test_broadened_life_safety_signals in test_agent_1_unittest.py
[x] Run test discovery to verify


### 🤖 Assistant

All done. Here's a summary of what changed:

---

### Changes Made

**[`navigator/agents/agent_1_2/agent_1.py`](navigator/agents/agent_1_2/agent_1.py:92) — `_HARM_SUBJECTS`**

Added `boyfriend`, `girlfriend`, `fiance[e]?` (covers both `fiance` and `fiancee`), `stepfather`, and `stepmother` to the alternation group inside the existing `\b` anchor:

```
Before: ...ex|husband|wife|roommate|manager|neighbor|father|mother|dad|mom|...
After:  ...ex|husband|wife|boyfriend|girlfriend|fiance[e]?|roommate|manager|neighbor|father|mother|stepfather|stepmother|dad|mom|...
```

These new terms flow into all downstream patterns that use `_HARM_SUBJECTS`, including the `will/might/is going to/said he would` threat pattern on line 116, so all three new test phrases are matched by that single branch.

**[`tests/agent_1_2/test_agent_1_unittest.py`](tests/agent_1_2/test_agent_1_unittest.py:80) — `test_broadened_life_safety_signals`**

Appended three positive cases:
- `"My boyfriend will hurt me."`
- `"My girlfriend is going to hurt the kids."`
- `"My boyfriend said he would kill us."`

**Verification:** 60/60 agent_1_2 tests pass. The 1 failure in the full suite (`test_planning_package_availability_and_timing`) is a pre-existing unrelated KB record mismatch, not introduced by these changes.