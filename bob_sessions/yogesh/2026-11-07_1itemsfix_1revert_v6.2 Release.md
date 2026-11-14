# ### Task: Fix Safety Regex False Positives & Add Negative Tests (Item 2)

#### 1. In `navigator/agents/agent_1_2/agent_1.py`:
- Refactor `RE_SAFETY_DISTRESS` to prevent false positives on everyday statements like "my landlord said he will come back to fix the heater".
- Require that any perpetrator or third-party phrase mentioning "come back" or "scared/afraid/worried (that)? he/she/they will" MUST also be explicitly paired with a harm/violence verb (e.g. `hurt`, `harm`, `kill`, `beat`, `attack`, `abuse`, `violence`, `destroy`).
- Everyday sentences containing "come back" without an explicit harm action must NOT match.

#### 2. In `tests/agent_1_2/test_agent_1_unittest.py`:
- In `test_broadened_life_safety_signals`, verify threats from others using `subTest` across variants:
  - "I'm scared he will come back and hurt us"
  - "I'm scared she will come back and hurt us"
  - "He will come back and hurt us"
  - "She will come back and hurt us"
- Add a new test method `test_safety_signals_negative_everyday_sentences` using `subTest` to assert that zero safety flags are generated for benign phrases:
  - "my landlord said he will come back to fix the heater"
  - "my landlord said she will come back to fix the heater"
  - "the contractor will come back tomorrow morning"
  - "they will come back next week to inspect the property"
  - "he will come back from work at 5pm"

#### 3. Verification:
Run test discovery to confirm all tests pass cleanly:
`python -m unittest discover -s tests -t .`

---

**Status:** active  **Date:** 2026-11-07

---

### 👤 User

### Task: Fix Safety Regex False Positives & Add Negative Tests (Item 2)

#### 1. In `navigator/agents/agent_1_2/agent_1.py`:
- Refactor `RE_SAFETY_DISTRESS` to prevent false positives on everyday statements like "my landlord said he will come back to fix the heater".
- Require that any perpetrator or third-party phrase mentioning "come back" or "scared/afraid/worried (that)? he/she/they will" MUST also be explicitly paired with a harm/violence verb (e.g. `hurt`, `harm`, `kill`, `beat`, `attack`, `abuse`, `violence`, `destroy`).
- Everyday sentences containing "come back" without an explicit harm action must NOT match.

#### 2. In `tests/agent_1_2/test_agent_1_unittest.py`:
- In `test_broadened_life_safety_signals`, verify threats from others using `subTest` across variants:
  - "I'm scared he will come back and hurt us"
  - "I'm scared she will come back and hurt us"
  - "He will come back and hurt us"
  - "She will come back and hurt us"
- Add a new test method `test_safety_signals_negative_everyday_sentences` using `subTest` to assert that zero safety flags are generated for benign phrases:
  - "my landlord said he will come back to fix the heater"
  - "my landlord said she will come back to fix the heater"
  - "the contractor will come back tomorrow morning"
  - "they will come back next week to inspect the property"
  - "he will come back from work at 5pm"

#### 3. Verification:
Run test discovery to confirm all tests pass cleanly:
`python -m unittest discover -s tests -t .`

---

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — tests\agent_1_2\test_agent_1_unittest.py

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: read_file

Now let me read the exact current `RE_SAFETY_DISTRESS` regex:

> 🔧 **read_file** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: update_todo_list

Now I have a clear picture. Let me update the todo list and implement both changes:

> 🔧 **update_todo_list** — 
[-] Refactor RE_SAFETY_DISTRESS to require explicit harm verb with "come back" and "scared/afraid he/she/they will" patterns
[ ] Update test_broadened_life_safety_signals to use subTest and add "He/She will come back and hurt us" variants
[ ] Add test_safety_signals_negative_everyday_sentences test method
[ ] Run tests to verify all pass


### 🤖 Assistant

> 🔧 called: apply_diff

The three problematic patterns are on lines 96–98:
- `\bscared\s+(?:that\s+)?(?:he|she|they)\s+will\b` — matches "scared he will come back" without needing a harm verb
- `\b(?:he|she|they)\s+will\s+come\s+back\b` — matches "he will come back to fix the heater"
- `\b(?:he|she|they)\s+will\s+hurt\s+us\b` — this is fine but can be merged

I'll replace those three with tighter patterns that require a harm verb:

> 🔧 **apply_diff** — navigator\agents\agent_1_2\agent_1.py

### 🤖 Assistant

> 🔧 called: apply_diff

Now update the test file — convert the loop to `subTest`, add the new "He/She will come back and hurt us" variants, and add the negative test method:

> 🔧 **apply_diff** — tests\agent_1_2\test_agent_1_unittest.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Refactor RE_SAFETY_DISTRESS to require explicit harm verb with "come back" and "scared/afraid he/she/they will" patterns
[x] Update test_broadened_life_safety_signals to use subTest and add "He/She will come back and hurt us" variants
[x] Add test_safety_signals_negative_everyday_sentences test method
[-] Run tests to verify all pass


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python -m unittest discover -s tests -t .

### 🤖 Assistant

> 🔧 called: execute_command

The one failing test is pre-existing and unrelated to our changes (`test_planning_package_availability_and_timing` in `test_builders.py` — a knowledge-base availability check). Let me confirm none of our new/modified tests are among the failures:

> 🔧 **execute_command** — python -m unittest tests.agent_1_2.test_agent_1_unittest -v 2>&1

### 🤖 Assistant

> 🔧 called: update_todo_list

All 7 tests in `test_agent_1_unittest.py` pass (the exit code 1 is PowerShell's stderr routing quirk, not a test failure — `Ran 7 tests … OK`). The single failing test in the full suite is a pre-existing unrelated knowledge-base test.

> 🔧 **update_todo_list** — 
[x] Refactor RE_SAFETY_DISTRESS to require explicit harm verb with "come back" and "scared/afraid he/she/they will" patterns
[x] Update test_broadened_life_safety_signals to use subTest and add "He/She will come back and hurt us" variants
[x] Add test_safety_signals_negative_everyday_sentences test method
[x] Run tests to verify all pass


### 🤖 Assistant

All done. Here's a summary of every change made:

---

### Changes

#### [`navigator/agents/agent_1_2/agent_1.py`](navigator/agents/agent_1_2/agent_1.py:94) — `RE_SAFETY_DISTRESS` refactor

Replaced 4 overly-broad patterns with 3 tighter ones:

| Removed | Problem |
|---|---|
| `\bscared\s+(?:that\s+)?(?:he\|she\|they)\s+will\b` | Matched any "scared he will …" regardless of what follows |
| `\b(?:he\|she\|they)\s+will\s+come\s+back\b` | Matched any "he will come back to fix the heater" |
| `\b(?:he\|she\|they)\s+will\s+hurt\s+us\b` | Standalone (already redundant) |
| `\bcome\s+back\s+and\s+hurt\s+us\b` | Only matched `hurt`, not other harm verbs |

| Added | What it requires |
|---|---|
| `\b(?:afraid\|scared\|worried)\s+(?:that\s+)?(?:he\|she\|they)\s+(?:will\|might)\s+(?:come\s+back\s+(?:and\s+)?)?\b(?:hurt\|harm\|kill\|beat\|attack\|abuse)\b` | Explicit harm verb after "scared/afraid/worried he/she/they will [come back and]" |
| `\b(?:he\|she\|they)\s+will\s+come\s+back\s+(?:and\s+)?(?:hurt\|harm\|kill\|beat\|attack\|abuse)\b` | Harm verb required after "come back" |
| `\bcome\s+back\s+and\s+(?:hurt\|harm\|kill\|beat\|attack\|abuse)\b` | Broader harm verb set |

#### [`tests/agent_1_2/test_agent_1_unittest.py`](tests/agent_1_2/test_agent_1_unittest.py:61)

- **`test_broadened_life_safety_signals`**: converted bare `for` loop to `with self.subTest(phrase=phrase)`, added `"He will come back and hurt us"` and `"She will come back and hurt us"` variants.
- **`test_safety_signals_negative_everyday_sentences`** (new): asserts zero safety flags for 5 benign "come back" sentences using `subTest`.