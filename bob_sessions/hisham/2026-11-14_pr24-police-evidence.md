# PR #24 review fixes (Slav, Nov 14). Branch hisham/lockout-closures. Change ONLY navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py and tests/agent_6_7_8_10/test_slav_nov12.py. Do not touch the root README, navigator/supervisor/, tests/test_dialog*.py, or any other file.

1. Agent 8, lockout block (after police_contacts = _police_contacts_from_directory(dir_data)): keep a police contact only when it has evidence_refs and every one of them is an evidence_id in the request's evidence_records (ev_records_all). Otherwise drop the contact and keep only the sentence "If you are already locked out, you can also contact the local police non-emergency line." Reason: Supervisor check S5 rejects evidence_refs it did not send, which stops the whole plan.
2. Tests: in test_lockout_with_verified_police_record_adds_contacts, test_lockout_sheriff_has_verified_hours and test_lockout_sacpd_hours_none, add the police evidence records (same evidence_ids as the directory fixture) to the request's evidence_records so they still pass. Add test_lockout_police_evidence_missing_sentence_only: lockout, directory has verified police records, but their evidence is NOT in evidence_records, so the card has the sentence and no police contacts.
Run python3 tests/agent_6_7_8_10/run_tests.py and python3 -I -m unittest discover -s tests -t . and show both summary lines.

---

**Status:** active  **Date:** 2026-11-14

---

### 👤 User

PR #24 review fixes (Slav, Nov 14). Branch hisham/lockout-closures. Change ONLY navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py and tests/agent_6_7_8_10/test_slav_nov12.py. Do not touch the root README, navigator/supervisor/, tests/test_dialog*.py, or any other file.

1. Agent 8, lockout block (after police_contacts = _police_contacts_from_directory(dir_data)): keep a police contact only when it has evidence_refs and every one of them is an evidence_id in the request's evidence_records (ev_records_all). Otherwise drop the contact and keep only the sentence "If you are already locked out, you can also contact the local police non-emergency line." Reason: Supervisor check S5 rejects evidence_refs it did not send, which stops the whole plan.
2. Tests: in test_lockout_with_verified_police_record_adds_contacts, test_lockout_sheriff_has_verified_hours and test_lockout_sacpd_hours_none, add the police evidence records (same evidence_ids as the directory fixture) to the request's evidence_records so they still pass. Add test_lockout_police_evidence_missing_sentence_only: lockout, directory has verified police records, but their evidence is NOT in evidence_records, so the card has the sentence and no police contacts.
Run python3 tests/agent_6_7_8_10/run_tests.py and python3 -I -m unittest discover -s tests -t . and show both summary lines.

---

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[-] Read the agent and test files to understand current structure
[ ] Implement Agent 8 lockout block filter (drop police contacts without valid evidence_refs)
[ ] Update existing tests to add police evidence records to evidence_records
[ ] Add new test test_lockout_police_evidence_missing_sentence_only
[ ] Run both test commands and report results


### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — tests/agent_6_7_8_10/test_slav_nov12.py

> 🔧 **read_file** — navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py

### 🤖 Assistant

> 🔧 called: read_file

Now let me read the Agent 8 lockout block specifically:

> 🔧 **read_file** — navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — lockout block after police_contacts = _police_contacts_from_directory, ev_records_all, lockout card assembly, police_contacts appended to contacts

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — lockout block after contacts, police_contacts, _LOCKOUT_SENTENCE, ev_records_all, lockout card assembly with police contacts

### 🤖 Assistant

> 🔧 called: update_todo_list

Now I have a full picture. Let me understand the structure:

1. **Agent 8 lockout block** (lines 1267-1308): After `police_contacts = _police_contacts_from_directory(dir_data)`, we need to filter `police_contacts` — keep only those where the contact has `evidence_refs` and every evidence_id in those refs is in `ev_records_all`. Otherwise drop the contact and keep only the sentence.

2. **Tests to update**: `test_lockout_with_verified_police_record_adds_contacts`, `test_lockout_sheriff_has_verified_hours`, `test_lockout_sacpd_hours_none` — need to add police evidence records to the request's `evidence_records`.

3. **New test**: `test_lockout_police_evidence_missing_sentence_only`.

The `ev_records_all` is already computed at line 1255: `ev_records_all = p.get("evidence_records") or []`.

Now I need to understand what `ev_records_all` contains — it's the request payload's `evidence_records`. The police directory fixture has its own `evidence_records` with IDs `ev_sacpd_001`, `ev_sacpd_002`, `ev_sheriff_001`, `ev_sheriff_002`.

The fix: after getting `police_contacts`, filter them so we only keep contacts whose `evidence_refs` are non-empty AND every ref exists as an `evidence_id` in `ev_records_all`. If none pass the filter, `police_contacts = []` and we still append the sentence.

> 🔧 **update_todo_list** — 
[x] Read the agent and test files to understand current structure
[-] Implement Agent 8 lockout block filter (drop police contacts without valid evidence_refs)
[ ] Update existing tests to add police evidence records to evidence_records
[ ] Add new test test_lockout_police_evidence_missing_sentence_only
[ ] Run both test commands and report results


### 🤖 Assistant

> 🔧 called: apply_diff

Now let me implement the agent change. The lockout block starts at line 1267. I need to add filtering right after line 1271 (`police_contacts = _police_contacts_from_directory(dir_data)`):

> 🔧 **apply_diff** — navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Read the agent and test files to understand current structure
[x] Implement Agent 8 lockout block filter (drop police contacts without valid evidence_refs)
[-] Update existing tests to add police evidence records to evidence_records
[ ] Add new test test_lockout_police_evidence_missing_sentence_only
[ ] Run both test commands and report results


### 🤖 Assistant

> 🔧 called: apply_diff

Now I need to update the three existing lockout tests to pass the police evidence records in the request's `evidence_records`. The fixture `_POLICE_DIR_FIXTURE` has `evidence_records` with `ev_sacpd_001`, `ev_sacpd_002`, `ev_sheriff_001`, `ev_sheriff_002`. The police contacts returned have `evidence_refs: ["ev_sacpd_001"]` (SACPD) and `["ev_sheriff_001"]` (Sheriff).

For the three tests to still pass (police contacts appear), I need to add those evidence records to the request `evidence_records`. I'll extract the police evidence records from the fixture.

For the new test `test_lockout_police_evidence_missing_sentence_only`, the evidence is NOT in `evidence_records`, so police contacts are dropped and only the sentence remains.

Looking at the three tests to update:
1. `test_lockout_with_verified_police_record_adds_contacts` (line 426)
2. `test_lockout_sheriff_has_verified_hours` (line 448)  
3. `test_lockout_sacpd_hours_none` (line 464)

All three call `self._lockout_plan(needs, matches, actions, allowed_case_facts=facts)` without `evidence_records`. I need to add `evidence_records=_POLICE_DIR_FIXTURE["evidence_records"]` (or at minimum the contact evidence records).

> 🔧 **apply_diff** — tests/agent_6_7_8_10/test_slav_nov12.py

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Read the agent and test files to understand current structure
[x] Implement Agent 8 lockout block filter (drop police contacts without valid evidence_refs)
[x] Update existing tests to add police evidence records to evidence_records
[-] Add new test test_lockout_police_evidence_missing_sentence_only
[ ] Run both test commands and report results


### 🤖 Assistant

> 🔧 called: apply_diff

Now I need to add `test_lockout_police_evidence_missing_sentence_only`. It should:
- Have a lockout, directory has verified police records
- But their evidence is NOT in `evidence_records` (pass empty or unrelated evidence_records)
- Verify: card has the sentence and no police contacts

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:479
-------
    def test_lockout_no_legal_aid_uses_first_housing_card(self):
=======
    def test_lockout_police_evidence_missing_sentence_only(self):
        """Lockout + verified police records in directory, but their evidence_ids are NOT in
        the request's evidence_records → police contacts are dropped; only the sentence remains."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        # evidence_records does NOT contain the police evidence_ids
        result = self._lockout_plan(needs, matches, actions, allowed_case_facts=facts,
                                    evidence_records=[])
        card = result["result"]["action_cards"][0]
        # Sentence must still be there
        self.assertIn("locked out", card["next_step"].lower(),
                      "Police sentence must still appear when evidence is missing")
        self.assertIn("police non-emergency", card["next_step"].lower())
        # No police contacts — all were dropped because their evidence_refs are not in ev_records_all
        police_contacts = [c for c in card.get("contacts", [])
                           if "police non-emergency" in c["label"].lower()]
        self.assertEqual(police_contacts, [],
                         "Police contacts must be absent when their evidence is not in evidence_records")

    def test_lockout_no_legal_aid_uses_first_housing_card(self):
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Read the agent and test files to understand current structure
[x] Implement Agent 8 lockout block filter (drop police contacts without valid evidence_refs)
[x] Update existing tests to add police evidence records to evidence_records
[x] Add new test test_lockout_police_evidence_missing_sentence_only
[-] Run both test commands and report results


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd . && python3 tests/agent_6_7_8_10/run_tests.py 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd . && python3 -I -m unittest discover -s tests -t . 2>&1

### 🤖 Assistant

> 🔧 called: update_todo_list

Both suites pass clean.

> 🔧 **update_todo_list** — 
[x] Read the agent and test files to understand current structure
[x] Implement Agent 8 lockout block filter (drop police contacts without valid evidence_refs)
[x] Update existing tests to add police evidence records to evidence_records
[x] Add new test test_lockout_police_evidence_missing_sentence_only
[x] Run both test commands and report results


### 🤖 Assistant

Both commands pass:

```
69 of 69 checks passed
----------------------------------------------------------------------
Ran 524 tests in 22.215s

OK
```

### What was changed

**[`navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:1274)** — after `police_contacts = _police_contacts_from_directory(dir_data)` in the lockout block, added an S5 filter:
```python
ev_all_ids = {e["evidence_id"] for e in ev_records_all if "evidence_id" in e}
police_contacts = [
    pc for pc in police_contacts
    if pc.get("evidence_refs")
    and all(r in ev_all_ids for r in pc["evidence_refs"])
]
```
Contacts without `evidence_refs`, or whose refs aren't in the request's `evidence_records`, are dropped. The sentence is appended regardless (it's added after, unconditionally).

**[`tests/agent_6_7_8_10/test_slav_nov12.py`](tests/agent_6_7_8_10/test_slav_nov12.py:434)**:
- `test_lockout_with_verified_police_record_adds_contacts`, `test_lockout_sheriff_has_verified_hours`, `test_lockout_sacpd_hours_none` — each now passes `evidence_records=_POLICE_DIR_FIXTURE["evidence_records"]` so the police contact `evidence_refs` resolve and the contacts still appear.
- New [`test_lockout_police_evidence_missing_sentence_only`](tests/agent_6_7_8_10/test_slav_nov12.py:479) — passes `evidence_records=[]`; asserts the sentence is present and `police_contacts == []`.