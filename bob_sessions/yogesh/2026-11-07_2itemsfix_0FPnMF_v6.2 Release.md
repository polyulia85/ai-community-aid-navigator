# ### Task: Restrict Threat Pattern to Person Objects & Add Landlord Subject Match

#### 1. File: `navigator/agents/agent_1_2/agent_1.py`
In `RE_SAFETY_DISTRESS`:
- Update the third-party threat pattern to require that the object of harm verbs (`hurt|harm|kill|beat|attack|abuse`) must strictly be a person: `(?:me|us|her|him|them|my\s+kids?|the\s+kids?|my\s+family|our\s+family|someone|anyone)`.
- Ensure non-person objects do not match (e.g., "harm my credit score", "kill my hours", "beat the deadline").
- Allow person-noun subjects in addition to pronouns (e.g. `(?:the\s+|my\s+)?(?:landlord|partner|ex|husband|wife|roommate|manager|neighbor)`).
- Match explicit threats like `"The landlord threatened to attack us."` and `"threatened to (attack|hurt|harm|kill|beat) (me|us|...)"`.

#### 2. File: `tests/agent_1_2/test_agent_1_unittest.py`
- In `test_broadened_life_safety_signals`, add `"The landlord threatened to attack us."` as a must-flag positive test.
- In `test_safety_signals_negative_everyday_sentences`, add these three must-not-flag negative tests:
  - `"They might harm my credit score if I miss rent."`
  - `"They will kill my hours at work."`
  - `"They are going to beat the deadline."`

#### 3. Verification:
Run test discovery to confirm all unit tests pass with zero failures:
`python -m unittest discover -s tests -t .`

---

**Status:** active  **Date:** 2026-11-07

---

### 👤 User

### Task: Restrict Threat Pattern to Person Objects & Add Landlord Subject Match

#### 1. File: `navigator/agents/agent_1_2/agent_1.py`
In `RE_SAFETY_DISTRESS`:
- Update the third-party threat pattern to require that the object of harm verbs (`hurt|harm|kill|beat|attack|abuse`) must strictly be a person: `(?:me|us|her|him|them|my\s+kids?|the\s+kids?|my\s+family|our\s+family|someone|anyone)`.
- Ensure non-person objects do not match (e.g., "harm my credit score", "kill my hours", "beat the deadline").
- Allow person-noun subjects in addition to pronouns (e.g. `(?:the\s+|my\s+)?(?:landlord|partner|ex|husband|wife|roommate|manager|neighbor)`).
- Match explicit threats like `"The landlord threatened to attack us."` and `"threatened to (attack|hurt|harm|kill|beat) (me|us|...)"`.

#### 2. File: `tests/agent_1_2/test_agent_1_unittest.py`
- In `test_broadened_life_safety_signals`, add `"The landlord threatened to attack us."` as a must-flag positive test.
- In `test_safety_signals_negative_everyday_sentences`, add these three must-not-flag negative tests:
  - `"They might harm my credit score if I miss rent."`
  - `"They will kill my hours at work."`
  - `"They are going to beat the deadline."`

#### 3. Verification:
Run test discovery to confirm all unit tests pass with zero failures:
`python -m unittest discover -s tests -t .`

---

### 🤖 Assistant

> 🔧 called: read_file, read_file

Let me start by reading the relevant files to understand the current code before making changes.

> 🔧 **read_file** — tests\agent_1_2\test_agent_1_unittest.py

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: read_file

Now let me read the actual `RE_SAFETY_DISTRESS` pattern in detail:

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: update_todo_list

Now I have a clear picture of the current patterns. Let me analyze what needs to change:

**Line 94** — `\b(?:threaten|threatened|threatening)\s+(?:to\s+)?(?:kill|hurt|harm|shoot|beat)\b` — This matches `"threatened to kill"` but doesn't require a person object, and doesn't allow person-noun subjects like "landlord". I need to add a pattern that matches `"The landlord threatened to attack us."`.

**Line 98** — `\b(?:he|she|they)\s+(?:will|might|...)` — Only allows pronoun subjects; needs to also allow person-noun subjects like "landlord".

**Lines 94-98** — The harm verbs need a person object requirement for some patterns to avoid matching "harm my credit score", "kill my hours", "beat the deadline".

Let me carefully design the new patterns:

> 🔧 **update_todo_list** — [-] Update RE_SAFETY_DISTRESS in agent_1.py: add person-object constraint and person-noun subject support
[ ] Update test file: add positive test and three negative tests
[ ] Run tests to verify all pass


### 🤖 Assistant

> 🔧 called: apply_diff

Now let me make the changes. The key insight is:

1. **Line 94** (`threatened to ...`): Currently has no object requirement. Add person-object constraint and expand subject to include person nouns.
2. **Line 96** (`afraid/scared ... he/she/they will hurt`): Already ends before the object — these are fine because the verb alone after "afraid he will hurt" is a clear threat signal.
3. **Line 97** (`he/she/they will come back and hurt`): No object constraint needed — "come back and hurt" is already a threat signal.
4. **Line 98** (`he/she/they will/might hurt`): This is the pattern that would match "they will harm my credit score". Needs person-object constraint. Also needs to support person-noun subjects.

> 🔧 **apply_diff** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: apply_diff

Now I also need to check the existing test case `"He said he will hurt us if we don't leave."` (line 73) — this uses pattern on line 98 (now the last updated pattern). The sentence `"he said he will hurt us"` — subject is "he", verb phrase is "said he will", harm verb is "hurt", object is "us". The new pattern requires `\s+(?:me|us|...)` after the harm verb, and "us" is in the list — ✓

Now let me check `"I'm scared he will come back and hurt us"` — this matches line 96 (`afraid|scared...he...will...come back and hurt`) — no object constraint on that line, so it still matches ✓.

Now update the test file:

> 🔧 **apply_diff** — tests\agent_1_2\test_agent_1_unittest.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — [x] Update RE_SAFETY_DISTRESS in agent_1.py: add person-object constraint and person-noun subject support
[x] Update test file: add positive test and three negative tests
[-] Run tests to verify all pass


### 🤖 Assistant

> 🔧 called: execute_command

Before running, let me do a quick sanity check on the three negative phrases against the updated patterns to make sure none slip through:

- `"They might harm my credit score if I miss rent."` — pattern requires `harm\s+(?:me|us|her|him|them|my\s+kids?|...)` — "my credit score" is NOT in the list ✓ won't match
- `"They will kill my hours at work."` — requires `kill\s+(?:me|us|...)` — "my hours" NOT in list ✓
- `"They are going to beat the deadline."` — requires `beat\s+(?:me|us|...)` — "the deadline" NOT in list ✓

And the positive: `"The landlord threatened to attack us."` — matches new pattern: `the\s+landlord` → `threatened\s+to` → `attack` → `us` ✓

Also verify existing tests aren't broken by the `\b(?:he|she|they)\s+will\s+come\s+back\s+(?:and\s+)?(?:hurt|harm|kill|beat|attack|abuse)\b` pattern (line 97 — unchanged, no object required). `"He will come back and hurt us"` still matches that ✓.

And `"He said he will hurt us if we don't leave."` — matches the last updated pattern: subject `he`, verb phrase `said he will`, harm `hurt`, object `us` ✓.

> 🔧 **execute_command** — python -m unittest discover -s tests -t .

### 🤖 Assistant

> 🔧 called: grep

The failure is in `test_planning_package_availability_and_timing` in `tests/test_builders.py` — entirely unrelated to our changes (it's about a knowledge-base program availability status). Let me confirm it was already failing before our changes by checking if it touches anything we modified:

> 🔧 **grep** — RE_SAFETY_DISTRESS|agent_1_2|agent_1\.py|test_broadened|test_safety_signals

### 🤖 Assistant

> 🔧 called: execute_command

That test has zero connection to our changes. Let me run just the agent_1_2 tests to confirm our specific suite is clean:

> 🔧 **execute_command** — python -m unittest discover -s tests/agent_1_2 -t .

### 🤖 Assistant

> 🔧 called: execute_command

All 60 tests in the agent_1_2 suite pass. Now confirm the pre-existing `test_builders` failure was not introduced by us:

> 🔧 **execute_command** — git stash; python -m unittest tests.test_builders.TestWithKB.test_planning_package_availability_and_timing 2>&1; git stash pop

### 🤖 Assistant

> 🔧 called: update_todo_list

Confirmed — `test_planning_package_availability_and_timing` was already failing on the baseline before our changes. It's a pre-existing, unrelated failure about a knowledge-base program status value.

> 🔧 **update_todo_list** — [x] Update RE_SAFETY_DISTRESS in agent_1.py: add person-object constraint and person-noun subject support
[x] Update test file: add positive test and three negative tests
[x] Run tests to verify all pass


### 🤖 Assistant

All changes are complete. Here's a summary of what was done:

---

### Changes made

#### [`navigator/agents/agent_1_2/agent_1.py`](navigator/agents/agent_1_2/agent_1.py:94) — `RE_SAFETY_DISTRESS`

**Old line 94** (bare `threatened to …` with no object guard):
```python
r"\b(?:threaten|threatened|threatening)\s+(?:to\s+)?(?:kill|hurt|harm|shoot|beat)\b|"
```

**Old line 98** (pronoun-only subjects, no object guard):
```python
r"\b(?:he|she|they)\s+(?:will|might|...)\s+(?:hurt|harm|kill|beat|attack|abuse)\b|"
```

**Replaced with three lines:**

1. A new first-priority pattern — person-noun **or** pronoun subject + `threatened to` + harm verb + **person object**:
   ```python
   r"\b(?:(?:the\s+|my\s+)?(?:landlord|partner|ex|husband|wife|roommate|manager|neighbor)|he|she|they)\s+threatened\s+to\s+(?:hurt|harm|kill|beat|attack|abuse)\s+(?:me|us|her|him|them|my\s+kids?|the\s+kids?|my\s+family|our\s+family|someone|anyone)\b|"
   ```
2. The old `threaten/threatened/threatening` pattern now **requires a person object** after the verb.
3. The old pronoun-only subject pattern now also allows person-noun subjects (`landlord|partner|ex|…`) **and requires a person object**, preventing "harm my credit score", "kill my hours", "beat the deadline" from matching.

#### [`tests/agent_1_2/test_agent_1_unittest.py`](tests/agent_1_2/test_agent_1_unittest.py:75)

- Added `"The landlord threatened to attack us."` to `test_broadened_life_safety_signals` positive cases.
- Added `"They might harm my credit score if I miss rent."`, `"They will kill my hours at work."`, `"They are going to beat the deadline."` to `test_safety_signals_negative_everyday_sentences`.

#### Test results
- **60/60 agent_1_2 tests pass** ✅
- The 1 failure (`test_planning_package_availability_and_timing`) is pre-existing on the baseline branch and entirely unrelated to this change.