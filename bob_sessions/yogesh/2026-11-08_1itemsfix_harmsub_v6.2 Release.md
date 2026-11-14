# ### Task: Anchor _HARM_SUBJECTS with Word Boundary and Add Negative Tests

#### 1. File: `navigator/agents/agent_1_2/agent_1.py`
In `_HARM_SUBJECTS`, ensure a leading word boundary `\b` is present at the start of the pattern string:
`_HARM_SUBJECTS = r"\b(?:he|she|they|(?:(?:the|my|our)\s+)?(?:landlord|partner|ex|husband|wife|roommate|manager|neighbor|father|mother|dad|mom|brother|sister))"`
Ensure `he` cannot match inside words ending in "he" like "headache", "toothache", or "backache".

#### 2. File: `tests/agent_1_2/test_agent_1_unittest.py`
In `test_safety_signals_negative_everyday_sentences`, add these three must-not-flag test cases to the `negatives` list:
- `"The headache will kill me."`
- `"This toothache will kill me."`
- `"My backache is going to kill me."`
Assert that all three produce zero safety flags.

#### 3. Verification:
Run the test suite:
`python -m unittest discover -s tests -t .`

---

**Status:** active  **Date:** 2026-11-07

---

### 👤 User

### Task: Anchor _HARM_SUBJECTS with Word Boundary and Add Negative Tests

#### 1. File: `navigator/agents/agent_1_2/agent_1.py`
In `_HARM_SUBJECTS`, ensure a leading word boundary `\b` is present at the start of the pattern string:
`_HARM_SUBJECTS = r"\b(?:he|she|they|(?:(?:the|my|our)\s+)?(?:landlord|partner|ex|husband|wife|roommate|manager|neighbor|father|mother|dad|mom|brother|sister))"`
Ensure `he` cannot match inside words ending in "he" like "headache", "toothache", or "backache".

#### 2. File: `tests/agent_1_2/test_agent_1_unittest.py`
In `test_safety_signals_negative_everyday_sentences`, add these three must-not-flag test cases to the `negatives` list:
- `"The headache will kill me."`
- `"This toothache will kill me."`
- `"My backache is going to kill me."`
Assert that all three produce zero safety flags.

#### 3. Verification:
Run the test suite:
`python -m unittest discover -s tests -t .`

---

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — tests\agent_1_2\test_agent_1_unittest.py

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: read_file

Now let me read the exact current `_HARM_SUBJECTS` definition:

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: apply_diff

Now I have everything I need. I'll make both changes simultaneously:

> 🔧 **apply_diff** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — tests\agent_1_2\test_agent_1_unittest.py

### 🤖 Assistant

> 🔧 called: execute_command

Both edits done. Now run the test suite:

> 🔧 **execute_command** — python -m unittest discover -s tests -t .

### 🤖 Assistant

> 🔧 called: execute_command

The one failing test (`test_planning_package_availability_and_timing`) is pre-existing and completely unrelated to the changes made here — it's in [`tests/test_builders.py`](tests/test_builders.py) and concerns a KB availability value, not safety signals. Let me confirm by checking whether it was already failing before our changes:

> 🔧 **execute_command** — git stash; python -m unittest tests.test_builders.TestWithKB.test_planning_package_availability_and_timing 2>&1; git stash pop

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python -m unittest tests.agent_1_2.test_agent_1_unittest 2>&1

### 🤖 Assistant

All 7 tests in [`tests/agent_1_2/test_agent_1_unittest.py`](tests/agent_1_2/test_agent_1_unittest.py) pass cleanly. The single failure in the full suite (`test_planning_package_availability_and_timing`) is a pre-existing KB data mismatch unrelated to this task.

Here's a summary of what was changed:

**1. [`navigator/agents/agent_1_2/agent_1.py`](navigator/agents/agent_1_2/agent_1.py:92)** — `_HARM_SUBJECTS` replaced with the anchored single-string pattern:
```python
_HARM_SUBJECTS = (
    r"\b(?:he|she|they|(?:(?:the|my|our)\s+)?(?:landlord|partner|ex|husband|wife|roommate|manager|neighbor|father|mother|dad|mom|brother|sister))"
)
```
The leading `\b` ensures `he` can only match at a word boundary, so "headache", "toothache", and "backache" are no longer caught.

**2. [`tests/agent_1_2/test_agent_1_unittest.py`](tests/agent_1_2/test_agent_1_unittest.py:108)** — Three new must-not-flag cases appended to the `negatives` list in `test_safety_signals_negative_everyday_sentences`:
- `"The headache will kill me."`
- `"This toothache will kill me."`
- `"My backache is going to kill me."`