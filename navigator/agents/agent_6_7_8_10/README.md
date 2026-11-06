# Agents 6, 7, 8, 10: Action Plan and Validation (mock component v0.9)
Owner: Hisham | Contracts: SHARED_CONTRACTS_v1.1 + Slav's Agent 7/10 notes | Status: local mock, not yet IBM integrated

## What it does
- Agent 7 reviews results from Agents 3-5 and reports findings (Q rules).
- Agent 6 orders actions into first / parallel / later with a reason for each.  Open programs for a housing need with urgency "immediate" are placed in "first".
- Agent 8 builds one unified Action Plan of Action Cards.  Each card now includes a `contacts[]` field (see below).
- Agent 10 returns PASS or FLAG (V rules); one flag never removes unrelated cards.
- Supervisor entry point: handle(request) in agent_6_7_8_10.py (role_id agent_6, agent_7, agent_8, agent_10). All results set is_mock = true.

## contacts[] field (v0.7)

Every Agent 8 Action Card carries a `contacts[]` array built from the card's program's `checked_claims[]` rows.

**Inclusion rules**
- `verification_status` must be `"verified"`
- `checked_at` must be a parseable `YYYY-MM-DD` date (rows without a date are excluded)
- `field_path` must start with `"contact"` or `"application_method"`
- Temporarily closed programs always get `contacts: []`

**Item shape**
```json
{
  "label":        "How to apply" | "Contact",
  "value":        "<claim_value as string>",
  "hours":        "<hours substring if the value contains a time expression, e.g. '8:00 am - 4:00 pm Mon-Fri'>" | null,
  "checked_at":   "YYYY-MM-DD",
  "evidence_refs": ["ev_id", ...]
}
```
`label` is `"How to apply"` for `application_method*` field paths and `"Contact"` for `contact*` field paths.

**next_step truncation**
`next_step` is the template sentence plus **at most 2** items from `contacts[]`:
1. The first online application method (has a URL or contains "online")
2. The first phone contact (matches a US phone pattern or 2-1-1)

Each appended item is followed by `"(checked Mon D)."` using the portable date helper.  All other verified contact items remain only in `contacts[]`.

## PR #2 audit fixes (v0.9)

| Item | Fix |
| --- | --- |
| **A6-01** Multiple needs | Actions now carry `need_ids[]` listing every need the match covers; coverage is computed across all entries, so input-order reversal cannot leave a need in `coverage_gaps`. |
| **A6-02** Conflicting deadlines | `_deadline_info` now also flags two verified claims with different values, and any verified claim with `claim_value=None`; the confirm action always shows plain text — never `()` or `None`. |
| **A6-03** Time-based ordering | Within a group, actions sort by `official_deadline`, then `user_target_date`, then processing-time presence; a plain-text note is added when processing time may exceed the time remaining. |
| **A6-04** Unsupported urgency | The `rental_assistance` template rationale was reworded to neutral text; date-specific phrases are only appended when a real date is present in the input. |
| **A7-01** Empty matches | Q8 now fires for every uncovered need whenever the stage_result has a `"matches"` key (even when the list is empty). |
| **A7-02** Evidence ref validation | An empty `evidence_records` list is no longer treated as "not provided"; any `evidence_refs` entry that is absent from the list triggers Q1. |
| **A7-03** None-value conflict severity | A `conflicting` claim with `claim_value=None` now routes to Q2 (not Q3); severity follows the existing field-path table (`critical` for deadline/contact/availability, `warning` otherwise). |
| **A10-02** False coverage | Agent 10 now checks that every entry in a card's `related_need_ids` is actually in `matches[pid]["need_ids"]`; mismatches are flagged V12. |
| **C-OD2** Overdue rent ordering | Housing subcategories sort before food/income within the same `order_group` via a `_HOUSING_SUBS` constant in the sort key. |

## Files
| File | Purpose |
| --- | --- |
| agent_6_7_8_10.py | The component |
| tests/agent_6_7_8_10/run_tests.py | Runs 69 integration checks (writes navigator/samples/agent_6_7_8_10/ only with --save) |
| tests/agent_6_7_8_10/test_pr11_regression.py | 9 KB-based regression tests from PR #11 |
| tests/agent_6_7_8_10/test_pr2_regression.py | 20 regression tests for PR #2 audit items (A6-01 to A6-04, A7-01 to A7-03, A10-02, C-OD2) |
| tests/agent_6_7_8_10/fixtures/ | Slav's test files (Agent 6 Sacramento input, Agent 10 mixed plan) |
| tests/agent_6_7_8_10/mock_input_v0.2.json | Our own mock data for the same case |
| navigator/samples/agent_6_7_8_10/ | Example AgentResult JSON for every agent, including full Action Plans |
| rules_agents_6_7_8_10_v0.6.md | Rules, severity tables, after-FLAG behavior, open items |

## How to run (from the repository root)
1. `python3 tests/agent_6_7_8_10/run_tests.py`
2. Expected last line: `69 of 69 checks passed`
3. `python3 -m unittest discover -s tests -t .`
4. Expected: 105 tests, 1 pre-existing `test_builders` failure (KB availability field, waiting on update)

Tested on macOS, Python 3.14.3.  Standard Python 3 only — no extra packages.

## Example output on Slav's case (navigator/samples/agent_6_7_8_10/slav_case_agent8_plan.json)
1. first: Confirm the rent program's application deadline (sources disagree: Oct 30 vs Nov 6)
2. first: Ask about rent help (depends on 1; Nov 1 shown as the user's date, not a program deadline)
3. first: Check food benefits (income to be confirmed with the provider)
4. parallel: Apply for unemployment benefits
5. later: Follow up on the applications

## Known issues and limits
- Program data and wording templates are MOCK. Real program names and text come from Silver's records and, later, the Orchestrate model.
- Guarantee and prohibited-data checks use phrase matching.
- All Agent 7 and 10 rules are automated. Q7 reports evidence age only until the team agrees a freshness window.
- Injection (Q9) and wording checks use pattern matching; new phrasings may need new patterns.
- Not connected to the Supervisor or IBM watsonx Orchestrate yet.
- **Deferred (contract review Oct 30):** (a) done Nov 1: `next_step` contacts and hours come only from verified `checked_claims[]` items, with the check date; (b) `agent7_findings[]` (Agents 6 & 8) and `open_agent7_findings[]` (Agent 10) are accepted in the envelope but not yet acted on; (c) `case_facts[]` is accepted by Agent 7 but not read; (d) `potential_options[]` is always returned empty.
- **Deferred (contracts v1.2, Julia):** A6-05, A8-05, A10-03 — not yet implemented, waiting on contract finalisation.
- The Windows date fix (PR #8) was made outside Bob; later changes are in Bob sessions.
