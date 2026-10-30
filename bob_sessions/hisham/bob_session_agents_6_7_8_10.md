# Review my Agents 6, 7, 8 and 10 in navigator/agents/agent_6_7_8_10 against docs/contracts/SHARED_CONTRACTS.md sections 4.6 to 4.9. List anything that doesn’t match the contract. Then run python3 tests/agent_6_7_8_10/run_tests.py and report the result. Don’t change any files.

---

**Status:** active  **Date:** 2026-10-30

---

### 👤 User

Review my Agents 6, 7, 8 and 10 in navigator/agents/agent_6_7_8_10 against docs/contracts/SHARED_CONTRACTS.md sections 4.6 to 4.9. List anything that doesn’t match the contract. Then run python3 tests/agent_6_7_8_10/run_tests.py and report the result. Don’t change any files.

---

### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file

I'll start by reading the relevant files in parallel.

> 🔧 **read_file** — /Users/hashamkahn/Documents/ai-community-aid-navigator/docs/contracts/SHARED_CONTRACTS.md

> 🔧 **read_file** — /Users/hashamkahn/Documents/ai-community-aid-navigator/navigator/agents/agent_6_7_8_10/rules_agents_6_7_8_10_v0.6.md

> 🔧 **read_file** — /Users/hashamkahn/Documents/ai-community-aid-navigator/navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py

### 🤖 Assistant

> 🔧 called: read_file

Now let me look at the test file and run it:

> 🔧 **read_file** — all test cases, assertions, what each test checks

### 🤖 Assistant

> 🔧 called: execute_command

Now let me run the tests:

> 🔧 **execute_command** — cd /Users/hashamkahn/Documents/ai-community-aid-navigator && python3 tests/agent_6_7_8_10/run_tests.py 2>&1

### 🤖 Assistant

All 51 tests pass. Now let me compile the contract-review findings. I have all the information I need.

---

## Contract review — Agents 6, 7, 8, 10 vs SHARED_CONTRACTS.md §§4.6–4.9

### Legend
- ✅ Matches the contract
- ⚠️ Minor deviation / gap worth noting
- ❌ Does not match the contract

---

### §4.6 Agent 6 — Action Planning & Prioritization

| # | Contract requirement | Code | Finding |
|---|---|---|---|
| 1 | `proposed_actions[]` output fields include `action_id`, `need_id or null`, `program_id or null`, `suggested_priority (integer or null)`, `order_group`, `rationale`, `dependency_ids[]`, `official_deadline`, `user_target_date`, `estimated_processing_time`, `evidence_refs[]`, `uncertainty_notes[]`, `user_override_allowed = true` | All fields present in `add()` factory ([`agent_6_7_8_10.py:181-187`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:181)) | ✅ |
| 2 | `order_group` uses `OrderGroup` enum (`first · parallel · later`) — replaces `parallel_group` | `GROUP_ORDER = {"first": 0, "parallel": 1, "later": 2}` ([`agent_6_7_8_10.py:147`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:147)) | ✅ |
| 3 | `suggested_priority` is relative order inside one group; no scoring formula | Assigned as a simple global rank `i` across all actions, not per-`order_group` ([`agent_6_7_8_10.py:244-245`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:244)) | ⚠️ Contract says "relative order **inside one** `order_group`". The code numbers actions globally after sorting by group, so action #4 in group `parallel` has `suggested_priority = 4`, not `1`. This is a cosmetic deviation (the contract says it is "optional" and the formula is explicitly banned), but the per-group semantics are not honoured. |
| 4 | Reopening date comes from `effective_date` first, ISO date in `claim_value` as fallback | [`_reopen_date()`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:58) implements exactly this priority | ✅ |
| 5 | When reopening is after the user's `rent_due_date`, the note must say so ("reopens Nov 2, after your Nov 1 date") | Implemented in [`agent_6_7_8_10.py:220`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:220) | ✅ |
| 6 | Input must include `agent7_findings[]`, `candidate_programs[]`, `timing[]`, `program_availability[]`, `evidence_records[]` | `agent_6` reads `matches`, `checked_claims`, `evidence_records`, `program_availability`, `timing`. It reads `agent7_findings` from payload but does **not use** the findings (they are accepted but not acted on). The contract says Agent 6 depends on Agent 7 findings. | ⚠️ `agent7_findings[]` arrives but nothing in `agent_6()` inspects or acts on it. The contract states it "may be empty" so this is not a hard failure, but a Q-rule finding that blocks an Agent 3/4/5 stage result should arguably influence prioritisation. |
| 7 | `confirmed_mismatch` programs never become actions | [`agent_6_7_8_10.py:191`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:191) skips them | ✅ |
| 8 | `unknown` availability gets an uncertainty note | [`_uncertainty()`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:163) adds the note | ✅ |

---

### §4.7 Agent 7 — Quality & Uncertainty Controller

| # | Contract requirement | Code | Finding |
|---|---|---|---|
| 1 | Input: `stage` (`retrieval · matching · verification · planning`), `stage_result`, `evidence_records[]`, `case_facts[]`, `needs[]` | Agent 7 reads `stage`, `stage_result`, `evidence_records`, `needs`. It does **not read `case_facts[]`** even though the contract lists it as an input. | ⚠️ `case_facts[]` is defined as an input to Agent 7 but the code never accesses it. No current rule in Q1–Q10 uses case facts, but future Q-rules might. Low risk now. |
| 2 | `findings[]` shape: `finding_id`, `rule_id`, `severity (Severity)`, `program_id or null`, `need_id or null`, `field_path or null`, `evidence_refs[]`, `description`, `recommended_action` | All fields present in [`add()` closure](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:344) | ✅ |
| 3 | `stage_assessment` values: `clear · issues_found` | [`agent_6_7_8_10.py:422`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:422) | ✅ |
| 4 | `recommended_action` values: `recheck_source · request_clarification · show_conflict_and_add_provider_confirmation · omit_unsupported_claim · report_coverage_gap · no_action` | All six values used in code. `omit_unsupported_claim` is also used for Q9 (injection finding), which fits. | ✅ |
| 5 | Each finding copied into envelope `issues[]` with `code = rule_id` | [`agent_6_7_8_10.py:423`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:423) | ✅ |
| 6 | `status = partial`, issue `INPUT_INCOMPLETE` when information is missing; never assumes data | Handled at the top-level `handle()` for a missing field ([`agent_6_7_8_10.py:47-48`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:47)); Agent 7's own body does not check for an empty/null `stage_result` — it would raise a `TypeError` caught by `handle()`. | ✅ (covered by envelope catch) |
| 7 | `info` findings do not change `stage_assessment` | [`agent_6_7_8_10.py:421`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:421): `real = [f for f in findings if f["severity"] != "info"]` | ✅ |

---

### §4.8 Agent 8 — Crisis Action Plan Builder

| # | Contract requirement | Code | Finding |
|---|---|---|---|
| 1 | Output fields: `plan_version` (string), `action_cards[]`, `potential_options[]`, `coverage_gaps[]` | All present ([`agent_6_7_8_10.py:316`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:316)) | ✅ |
| 2 | `action_cards[]` fields: `card_id`, `source_action_ids[]`, `related_need_ids[]`, `program_id or null`, `action_title`, `reason`, `next_step`, `priority_reason`, `order_group`, `dependency_card_ids[]`, `source_refs[]`, `uncertainty_notes[]`, `official_deadline`, `user_target_date`, `processing_estimate`, `progress_status = not_started` | All present in the card dict ([`agent_6_7_8_10.py:282-288`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:282)) | ✅ |
| 3 | `potential_options[]` fields: `program_id`, `program_name`, `why_it_may_matter`, `what_needs_checking[]`, `official_link` | Agent 8 always emits `"potential_options": []` — it never populates potential options from the input. The contract defines `potential_options[]` as an output, not as a pass-through, so this is not strictly wrong, but the code has no logic to surface programs that nearly match. | ⚠️ `potential_options[]` is always empty. The contract defines the shape but does not say which agent populates it. In practice, any potential options from Agent 6/Supervisor would never appear in Agent 8's output. Minor gap. |
| 4 | `progress_status` is never changed; always `not_started` | Both main path and repair path set `not_started` ([`agent_6_7_8_10.py:287`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:287), [`agent_6_7_8_10.py:309`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:309)) | ✅ |
| 5 | Card title (v1.1 PROPOSED): when `organization` and `program_name` are present, title names both; closed-program title keeps the name | [`_program_label()`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:109) + title construction at [line 269](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:269) | ✅ |
| 6 | Contacts/hours in `next_step` only from a `checked_claims[]` item with `verification_status = verified`, with the check date shown | The TEMPLATES bake in generic next steps (e.g. "Call 2-1-1…") with no evidence check; contacts from templates are not verified against `checked_claims`. The contract (ACCEPTED Oct 26) and Agent 10 rule V8 enforce this — and V8 catches any hard-coded phone/URL at validation time — but Agent 8 itself does not consult `checked_claims` when writing `next_step`. | ❌ Agent 8 does not read `checked_claims[]` at all (the field is not even in its input schema at [`agent_6_7_8_10.py:252-257`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:252)). The contract (§4.8, v1.1 ACCEPTED) requires contacts and hours in `next_step` to come only from a verified claim with the check date. Agent 8's templates can produce generic next-step text without a phone/URL (which currently passes V8), but the structure that would allow it to name a specific contact and check date is absent. Implementation date was "to agree with Hisham" per the contract, so this is a known deferred item — but it is a gap relative to the written contract. |
| 7 | Repair round: `repair_flags[]` causes only flagged cards to be rebuilt | Implemented at [`agent_6_7_8_10.py:289-312`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:289); `repaired_card_ids` returned | ✅ (v1.1 PROPOSED — accepted) |
| 8 | Input must include `agent7_findings[]` | The repair path does not re-accept `agent7_findings[]` and the normal path passes it through to the envelope only implicitly. The contract lists it as a required input to Agent 8. | ⚠️ `agent7_findings[]` is listed in the §4.8 input but `agent_8()` never reads it. Like Agent 6, Agent 8 receives it via the Supervisor's package but does not use it to adjust cards. |

---

### §4.9 Agent 10 — Plan Validation & Critique

| # | Contract requirement | Code | Finding |
|---|---|---|---|
| 1 | Input: `plan_version`, `repair_round`, `action_cards[]`, `potential_options[]`, `coverage_gaps[]`, `needs[]`, `matches[]`, `checked_claims[]`, `program_availability[]`, `evidence_records[]`, `open_agent7_findings[]`; case facts in envelope `allowed_case_facts` | Agent 10 reads all these except **`open_agent7_findings[]`**, which is in the contract but never accessed. `coverage_gaps[]` is read at [line 516](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:516). | ⚠️ `open_agent7_findings[]` is a required contract input that is silently ignored. |
| 2 | Output: `verdict (PASS · FLAG)`, `repair_round`, `flags[]`, `passed_card_ids[]` | All present ([`agent_6_7_8_10.py:531-532`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:531)) | ✅ |
| 3 | `flags[]` fields: `flag_id`, `card_id`, `rule_id`, `severity (Severity)`, `claim_text`, `reason`, `evidence_refs[]`, `required_correction`, `blocks_release` | All present in `flag()` closure ([`agent_6_7_8_10.py:454-458`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:454)) | ✅ |
| 4 | Every card appears either in `flags[]` or `passed_card_ids[]` | Blocked/unchecked cards excluded from `passed_card_ids`; all others included ([`agent_6_7_8_10.py:530-532`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:530)) | ✅ |
| 5 | V8 severity is **critical** | `SEVERITY = {..., "V8": "critical", ...}` ([`agent_6_7_8_10.py:438-440`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:438)) | ✅ |
| 6 | V4 also covers a `temporarily_closed` program shown as open or current help | [Lines 478-482](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:478) check both "shown as open" and "shown as current help" | ✅ |
| 7 | V13 fires only when Navigator itself is asked for the data; program requirements pass | `ASK_NAVIGATOR` regex + `PROHIBITED` patterns at [lines 432-433](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:432) | ✅ |
| 8 | `repair_round` echoed in result | `"repair_round": p.get("repair_round", 0)` ([`agent_6_7_8_10.py:531`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:531)) | ✅ |

---

### Summary of deviations

| Severity | Agent | Finding |
|---|---|---|
| ❌ Gap | **Agent 8** | `checked_claims[]` is not in Agent 8's input and `next_step` templates do not pull contacts/hours from a verified claim with a check date — as required by §4.8 (v1.1, ACCEPTED Oct 26). Implementation is deferred by mutual agreement ("to agree with Hisham") but the written contract is not met. |
| ⚠️ Minor | **Agent 6** | `suggested_priority` is numbered globally across all actions rather than per-`order_group`. §4.6 says it is "relative order inside one `order_group`". |
| ⚠️ Minor | **Agent 6 & 8** | `agent7_findings[]` is listed as a required input in §4.6 and §4.8 but neither agent reads or acts on the findings. The Supervisor passes them in, and they are accepted without error, but no prioritisation or card-building logic is influenced by Q-rule findings. |
| ⚠️ Minor | **Agent 7** | `case_facts[]` is listed as a required input in §4.7 but the code never accesses it. No current Q-rule uses it, so there is no functional impact today. |
| ⚠️ Minor | **Agent 8** | `potential_options[]` is always emitted as an empty list. The contract defines its shape; Agent 8 has no logic to populate it. |
| ⚠️ Minor | **Agent 10** | `open_agent7_findings[]` is a listed input in §4.9 but is never read. |

---

### Test run result

**51 of 51 checks passed** — all of Part A (Slav's fixtures), Part B (own pipeline), and Part C (all automated rules including v1.1 additions).

---

### 👤 User

Fix only the suggested_priority finding: in agent_6, number suggested_priority from 1 inside each order_group (first, parallel, later) instead of globally. Don’t change anything else. Then add a short line to the Known issues section of navigator/agents/agent_6_7_8_10/README.md listing the other review findings as deferred: verified contacts and hours in next_step (date to agree), agent7_findings / open_agent7_findings / case_facts accepted but not yet used, potential_options always empty. Then rerun python3 tests/agent_6_7_8_10/run_tests.py.

---

### 🤖 Assistant

> 🔧 called: read_file, read_file

Let me read the current README and the exact lines to change in the agent file first.

> 🔧 **read_file** — suggested_priority assignment loop, actions sort, enumerate

> 🔧 **read_file** — Known issues section or any section at the bottom of the file

### 🤖 Assistant

> 🔧 called: apply_diff

Now I have exactly what I need. Two targeted changes:

1. Replace the global `enumerate` with per-group counters in [`agent_6_7_8_10.py`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:244).
2. Append the deferred-findings line to the Known issues section of [`README.md`](navigator/agents/agent_6_7_8_10/README.md:34).

> 🔧 **apply_diff** — /Users/hashamkahn/Documents/ai-community-aid-navigator/navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — /Users/hashamkahn/Documents/ai-community-aid-navigator/navigator/agents/agent_6_7_8_10/README.md

### 🤖 Assistant

> 🔧 called: execute_command

Now run the tests:

> 🔧 **execute_command** — cd /Users/hashamkahn/Documents/ai-community-aid-navigator && python3 tests/agent_6_7_8_10/run_tests.py 2>&1

### 🤖 Assistant

51 of 51 still pass. Here's what was done:

### Changes made

**[`agent_6_7_8_10.py`](navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py:243) — `suggested_priority` fix**

Replaced the single global `enumerate` with a per-group counter dict. After the `actions.sort()` call, each action now receives a `suggested_priority` that restarts at 1 within each `order_group` (`first`, `parallel`, `later`) — matching the §4.6 definition of "relative order inside one `order_group`". The existing tests don't assert specific priority values, only ordering and coverage, so all 51 checks continue to pass.

**[`README.md`](navigator/agents/agent_6_7_8_10/README.md:40) — deferred findings note**

Added one bullet to the **Known issues and limits** section covering all four deferred items from the review:
- `next_step` verified-contact sourcing (§4.8 ACCEPTED, implementation date TBD)
- `agent7_findings[]` / `open_agent7_findings[]` accepted but not acted on
- `case_facts[]` accepted by Agent 7 but not read
- `potential_options[]` always empty