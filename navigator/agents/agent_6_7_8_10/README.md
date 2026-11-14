# Agents 6, 7, 8, 10: Action Plan and Validation (mock component v0.16)
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
| **A6-01** Multiple needs | Actions carry `need_id` (singular per contract 4.6); Agent 8 merges actions for the same program into one card. |
| **A6-02** Conflicting deadlines | `_deadline_info` flags two verified claims with different values, and any verified claim with `claim_value=None`; confirm action always shows plain text. |
| **A6-03** Time-based ordering | Within a group, actions sort by `official_deadline`, then `user_target_date`, then processing-time presence. |
| **A6-04** Unsupported urgency | Template rationale is neutral text; date-specific phrases are only appended when a real date is present. |
| **A7-01** Empty matches | Q8 fires for every uncovered need whenever the stage_result has a `"matches"` key. |
| **A7-02** Evidence ref validation | An empty `evidence_records` list is not treated as "not provided"; absent refs trigger Q1. |
| **A7-03** None-value conflict severity | A `conflicting` claim with `claim_value=None` routes to Q2 (not Q3). |
| **A10-02** False coverage | Agent 10 checks `related_need_ids` against `matches[pid]["need_ids"]`; mismatches flagged V12. |
| **C-OD2** Overdue rent ordering | Housing subcategories sort before food/income via `_HOUSING_SUBS` when `_immediate_housing_threat` triggers. |

## PR #13 audit fixes (v0.10)

| Item | Root cause | Fix |
| --- | --- | --- |
| **1** No double periods | `_strip_trailing_period` stripped the period after `p.m.` treating it as a sentence end, producing `p.m (checked …)` instead of `p.m. (checked …)`. | `_ABBREV_END_RE` now detects `x.y.` endings; only true sentence-ending periods are stripped. |
| **2** Phone dedup | `_next_step_contacts` could show the same phone twice if "How to apply" and "Contact" both carried it. | Compare first `_phone_re` match in each; skip Contact when the primary phone matches. |
| **3** `_subcategory` in output | `add()` in Agent 6 passed `_subcategory=sub` as a keyword, which persisted in the action dict. | `add()` deletes all keys starting with `_` before appending; a parallel `_action_sub` dict carries the subcategory internally. |
| **4** `ref_date` instead of `datetime.now()` | Agent 6 used `datetime.now()` for overdue and processing-time comparisons. | Agent 6 reads `payload["ref_date"]` (ISO date); missing or invalid `ref_date` adds a `MISSING_REF_DATE` issue and skips all date comparisons. |
| **5** Ordering — eviction notice alone | `_overdue_housing_signal` returned `True` for any eviction notice or utility shutoff, forcing housing first even when a far-future date was supplied. | Replaced with `_immediate_housing_threat`: only a sheriff/writ, an eviction notice with no date (imminent), or an eviction date within 7 days triggers housing-first. Utility shutoff alone never triggers. |
| **6** `user_priority` respected | Agent 6 ignored `need.user_priority`. | When `user_priority == 1`, the action is promoted to group `"first"` regardless of urgency-based group. |
| **7** Urgency wording | Templates hard-coded "Food is running low" regardless of actual urgency. | Templates use neutral wording; "Food is running low. " prefix is added only when `urgency == "immediate"` for food-category needs. |
| **8** Generic "Follow up" action removed | Agent 6 always added a `program_id=None` follow-up action; Agent 8 rendered it as a card. | The follow-up action is no longer created; Agent 8 skips any group with `m=None`. |
| **9** Duplicate date in rationale | `user_date` was appended to the template rationale and also in the deadline sentence. | Template base wording is kept neutral; `user_date` is appended exactly once in the deadline sentence. |
| **10** Processing time unit | All processing times were multiplied by 7 (assuming weeks), so "30 days" became 210 days. | `_parse_processing_days()` parses the unit: `days` → ×1, `weeks` → ×7, `months` → ×30. |
| **11** Agent 8 deps + uncertainty; Agent 10 dep check | Agent 8 only copied `a["uncertainty_notes"]` from the first merged action, and `dependency_card_ids` referenced action IDs not card IDs; Agent 10 did not check dep validity. | Agent 8 merges `uncertainty_notes` across all actions in the group and filters `dependency_ids` to those present in `id_map`. Agent 10 flags `V12` for any `dependency_card_ids` entry that is not a real card. |
| **12** A6-05 "Use an open option first" | Phrase appeared even when no open alternative existed for that need. | Added `has_open_for_need` check; phrase only included when another non-closed, non-mismatch match exists for the same need. |

## PR #13 follow-up fixes (v0.11 — Julia's review, §15.2 rules)

| # | Root cause | Fix |
| --- | --- | --- |
| **1** Fixed 7-day eviction threshold removed | `_immediate_housing_threat` treated any eviction notice with no date as imminent (return True), and applied a 7-day window for dated notices. Both made housing jump before food incorrectly. | Removed the 7-day threshold and the "no date → imminent" shortcut entirely. `_immediate_housing_threat` now delegates to `_confirmed_late_legal_stage` only. |
| **2** Undated / unknown-stage notice raises EVICTION_STAGE_UNKNOWN | An eviction notice with no confirmed late-legal-stage field silently triggered housing-first. | New `_eviction_notice_unknown_stage()` helper; Agent 6 adds an `EVICTION_STAGE_UNKNOWN` warning issue asking the Supervisor to clarify: notice type, date on the notice, court case filed, judgment or sheriff notice. Housing is ordered as a normal need until clarified. |
| **3** Housing-first only on confirmed late legal stage | Any overdue-rent signal or eviction notice (regardless of stage) could trigger housing-first. | `_immediate_housing_threat` now returns `True` only for `sheriff_notice`, `writ_of_execution`, `sheriff_enforcement`, `court_judgment`, `lockout_notice`, `displaced_now`, or `no_safe_place_to_stay`. |
| **4** Overdue / due-today rent never places housing above food | `rent_due_date` in the past triggered housing-first; and copying `rent_due_date` into `user_target_date` for housing shifted the sort key, placing housing before food even when `housing_first=False`. | `_immediate_housing_threat` no longer checks `rent_due_date`. `rent_due_date` is also no longer copied into `user_target_date` for housing actions. |
| **5** `user_priority` must NOT change `order_group` | `user_priority == 1` promoted the action to group `"first"` regardless of urgency. | Removed the promotion block; `order_group` is now set solely by `urgency`. `user_priority` is preserved in the need but does not affect ordering. |
| **6** No guarantee wording for late-stage housing | When `housing_first=True` the code showed emergency-shelter/legal-aid actions as first without noting that help is uncertain. | When `housing_first` is True, every action whose subcategory is in `_LATE_STAGE_HOUSING_SUBS` receives an `uncertainty_notes` entry: "Help from this program is not guaranteed. Contact them directly to confirm current availability." |

## PR #13 follow-up fixes (v0.12 — Julia's review round 2, §15.2 follow-up)

| # | Root cause | Fix |
| --- | --- | --- |
| **1** Invented fact field names | `_confirmed_late_legal_stage` checked non-existent fields (`sheriff_notice`, `writ_of_execution`, `court_judgment`, `lockout_notice`, `displaced_now`, `no_safe_place_to_stay`). Agents 1–2 only produce `has_written_eviction_notice` and `eviction_notice_type`. | Removed all invented fields. Late-stage detection now reads `eviction_notice_type` free text for keywords: `sheriff`, `writ`, `lockout`, `judgment`, `unlawful detainer`. "Displaced now" is detected from the housing need's `description`/`urgency_reason`/`original_quote`. |
| **2** EVICTION_STAGE_UNKNOWN raised too broadly | The issue was raised whenever a notice existed with no confirmed late-stage field, including when `eviction_notice_type` was present (early stage type like "3-day pay or quit"). | `_eviction_notice_unknown_stage` now fires **only** when `has_written_eviction_notice=True` AND `eviction_notice_type` is absent or empty. Any present type suppresses the issue. |
| **3** `rent_due_date` removed from housing action card | The v0.11 fix removed the `rent_due_date → user_target_date` copy entirely, so the user's rent date no longer appeared on the card. | Restored: `rent_due_date` is set as `user_target_date` on the housing action (shown to the user). A new `_action_rent_date` set marks these actions; `_sort_key_6` uses `_FAR_DATE` for them in the cross-need sort, so the rent date cannot reorder housing before food. |
| **4** "Acting before a housing deadline" with no deadline | When `user_date` came from `rent_due_date`, the rationale said "Acting before your date of …" implying it was an application deadline. | Separate wording: if the date came from `rent_due_date` the rationale says "Your rent is due …" (informational); if it came from `timing`, it says "Acting before your date of … gives the most time." The `eviction_prevention` template base wording is also made neutral ("Getting this contact early gives you the most options."). |

## PR #13 follow-up fixes (v0.13 — Julia's review round 3)

| # | Root cause | Fix |
| --- | --- | --- |
| **1** "is due" used for overdue rent | `rent_due_date` in the past still produced "Your rent is due Oct 1" regardless of whether the date had passed. | Compare `user_date` against `ref_date_str`; if `user_date < ref_date_str` (strictly past) say "Your rent **was** due …", otherwise "Your rent is due …". |
| **2** `emergency_shelter` "comes first" shown unconditionally | The template wording "A safe place to stay comes first if your housing is at risk." appeared on every emergency-shelter action, even when the notice stage was unknown or there was no housing signal at all. | Template default changed to neutral "Ask about current openings; availability changes and is not guaranteed." After `housing_first` is resolved, shelter actions are patched: if `housing_first=True` the rationale is switched to "A safe place to stay comes first…"; otherwise the neutral wording stays. |

## PR #13 follow-up fixes (v0.14 — TD 20.5 H3, date in eviction_notice_type)

| # | Root cause | Fix |
| --- | --- | --- |
| **1** Date in eviction_notice_type not surfaced | When Agent 2 records `eviction_notice_type` as free text including a date (e.g. "Writ of possession, sheriff lockout Nov 11"), that date was ignored. | New `_parse_date_from_text(text, ref_date_str)` helper extracts the first date token (month-name + day, M/D, or ISO). If the date falls before `ref_date` it advances by one year. When a housing-category action has no other `user_date`, the parsed date is set as `user_target_date` (never `official_deadline`). The rationale appends "The date you gave is …" once. The action is added to `_action_rent_date` so the date is excluded from the cross-need sort key (cannot reorder housing before food). |

## PR #14 fixes (v0.16 — Slav Nov 12)

| # | Root cause | Fix |
| --- | --- | --- |
| **Fix 1** Q8 false warning | Q8 fired at the retrieval/matching/verification stages (before Agent 8 creates `coverage_gaps`). A need with no match at that stage is expected; Agent 10 V12 already checks the final plan. | Q8 fires only when `stage_result` contains **both** `"matches"` and `"coverage_gaps"` keys. A need absent from both fires Q8; a need absent only from matches (no gaps key) stays silent. |
| **Fix 2** Already locked out | No detection of a lockout situation; no police non-emergency guidance given. | `_is_lockout()` checks `eviction_notice_type` fact ("lockout") OR any need description/original_quote ("locked out", "changed the locks", "locked me out"). When True, Agent 8 appends one plain sentence to the housing_legal_aid card (or first late-stage housing card): "If you are already locked out, you can also contact the local police non-emergency line." Police contacts are loaded read-only from `navigator/kb/emergency/emergency_directory.json` (subcategory `local_police_non_emergency`). Every verified record is included (no ZIP selection). Label: "Police non-emergency (\<geography[0]\>)". Hours only when the availability EvidenceRecord is verified (today only the Sheriff, 24/7). When no housing program is matched, the coverage-gap note says "No legal-help program was found yet." (no search promise) plus the police sentence. `_EMERGENCY_DIR_LOADER` can be replaced with a fixture callable in tests. |
| **Fix 3** Pantry closures | Availability evidence rows with dates were never surfaced to the user. | For each card, `_closure_rows_for_card()` reads verified/conflicting `checked_claims[]` with `field_path` starting with `"availability"` for that program. Rows with no parseable date are skipped; rows whose range ended before `ref_date` are skipped. One `uncertainty_note` per row: `"Closed Nov 25-27 (thanksgiving holiday) (checked Nov 12)."` / `"Closed Dec 24 - Jan 1 (holiday closure) (checked Nov 12)."` / `"Extra holiday distribution: Tue Nov 24, 10:30am - 1:30pm (checked Nov 12)."` / conflicting: `"Sources differ on whether this site is open on Nov 20. Call before you go."` `next_step` is not changed. Uses `payload["ref_date"]`, never system date. |
| **Fix 4** contacts[] labels | All `contact[]` rows got label `"Contact"` regardless of content. | `_contact_label()` returns `"Address"` for street address values, `"Hours"` for opening-hours-only day+time values (must start with a day name), `"Contact"` otherwise. `"How to apply"` for `application_method*` is unchanged. Phone `next_step` lookup still works (it uses a phone-RE pattern, not the label). |

## Files
| File | Purpose |
| --- | --- |
| agent_6_7_8_10.py | The component |
| tests/agent_6_7_8_10/run_tests.py | Runs 69 integration checks (writes navigator/samples/agent_6_7_8_10/ only with --save) |
| tests/agent_6_7_8_10/test_pr11_regression.py | 9 KB-based regression tests from PR #11 |
| tests/agent_6_7_8_10/test_pr2_regression.py | Regression tests for PR #2 audit items + §15.2 follow-up (A6-01 to A6-04, A7-01 to A7-03, A10-02, C-OD2, and §15.2 rules 1–6) — updated for Fix 1 (Q8 behavior) |
| tests/agent_6_7_8_10/test_slav_nov12.py | 30 new tests for Fixes 1–4 (Nov 12 2026, all fixtures, ref_date 2026-11-13, no live KB) |
| tests/agent_6_7_8_10/fixtures/ | Slav's test files (Agent 6 Sacramento input, Agent 10 mixed plan) |
| tests/agent_6_7_8_10/mock_input_v0.2.json | Our own mock data for the same case |
| navigator/samples/agent_6_7_8_10/ | Example AgentResult JSON for every agent, including full Action Plans |
| rules_agents_6_7_8_10_v0.6.md | Rules, severity tables, after-FLAG behavior, open items |

## How to run (from the repository root)
1. `python3 tests/agent_6_7_8_10/run_tests.py`
2. Expected last line: `69 of 69 checks passed`
3. `python3 -I -m unittest discover -s tests -t .`
4. Expected: all tests pass (364 as of v0.16)

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
