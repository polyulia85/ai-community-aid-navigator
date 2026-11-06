# Change directory into clone-folder if not already there. Run the unit test discovery suite using python -m unittest discover -s tests -t . -v. Do not make any edits, modifications, or commits to the codebase. Capture the full console output, list the total number of passing tests, and provide a clean summary of any failures or error stack traces found.

---

**Status:** active  **Date:** 2026-11-03

---

### 👤 User

Change directory into clone-folder if not already there. Run the unit test discovery suite using python -m unittest discover -s tests -t . -v. Do not make any edits, modifications, or commits to the codebase. Capture the full console output, list the total number of passing tests, and provide a clean summary of any failures or error stack traces found.

---

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python -m unittest discover -s tests -t . -v 2>&1

### 🤖 Assistant

Here is the full summary:

---

## Test Discovery Results — `clone-folder`

**Command:** `python -m unittest discover -s tests -t . -v`
**Total tests run:** 84
**Passed:** 83 ✅
**Failed:** 1 ❌
**Errors:** 0

---

### ❌ Failing Test

**Test:** `test_planning_package_availability_and_timing`
**Class:** `tests.test_builders.TestWithKB`
**File:** [`tests/test_builders.py`](clone-folder/tests/test_builders.py:105)

**Traceback:**
```
AssertionError: 'confirmed_open' != 'temporarily_closed'
```

**Line:** [`test_builders.py:105`](clone-folder/tests/test_builders.py:105)
```python
self.assertEqual(avail["prog_housing_saintjohns_sac_001"], "temporarily_closed")
```

**Root cause:** The test expects program `prog_housing_saintjohns_sac_001` to have an availability status of `"temporarily_closed"`, but the planning package builder is resolving it as `"confirmed_open"`. This indicates a mismatch between the expected availability logic/timing evaluation and what the KB (knowledge base) builder is actually computing for that program entry.

---

### ✅ All Passing Test Suites

| Suite | Tests Passed |
|---|---|
| `tests.agent_1_2.test_agent_1_unittest.TestAgent1` | 6 |
| `tests.agent_1_2.test_agent_2_unittest.TestAgent2` | 2 |
| `tests.agent_3_4_5.test_agents_3_4_5` (T1–T8) | 16 |
| `tests.test_builders.TestFromAgent1` | 3 |
| `tests.test_builders.TestRequests` | 4 |
| `tests.test_builders.TestWithKB` | 5 of 6 |
| `tests.test_checks.TestEachCheck` | 10 |
| `tests.test_checks.TestPrivacy` | 5 |
| `tests.test_checks.TestWithSamples` | 2 |
| `tests.test_run.TestRunner` | 8 |
| `tests.test_run_v2.TestAgent2Updates` | 3 |
| `tests.test_run_v2.TestAgent7` | 3 |
| `tests.test_run_v2.TestConfigErrors` | 8 |
| `tests.test_run_v2.TestProcessIsolation` | 3 |