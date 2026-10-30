---
title: "Shared JSON Contracts v1.1 — AI Community Aid Navigator"
subtitle: "Applied Intelligence Group · Supervisor / Orchestrator and integration · v1.1"
date: "October 27, 2026 · v1.1 (built on v1.0, frozen Oct 23) · Prepared by Slav"
---

# 0. How to use this document

- **Purpose.** One set of data structures so that Yogesh (Agents 1, 2), Silver (Agents 3, 4, 5) and Hisham (Agents 6, 7, 8, 10) can build in parallel and plug into the Supervisor on October 24–26 without rework.
- **Source of truth.** Final Consolidation Baseline (Oct 17): front chapter (Parts A–F) → Section 30 and other APPROVED rules → Section 11 frozen contracts → Sections 12–29 → RAG Technical Architecture → Solution Blueprint v1.1. Nothing here changes an approved decision. Where the Baseline leaves a field open, this draft proposes one and marks it **PROPOSED**.
- **Labels.** **FROZEN** = copied from the Baseline (section given), do not change. **PROPOSED** = added by this contract; since the v1.0 freeze it is binding for the build like everything else. **PENDING JULIA** = a default is in place and the code uses it; Julia can change it (Section 10).
- **Rule for everyone.** If you need a field that is not here, ask in the channel before adding it. No private formats.
- **Status: v1.1, published Oct 27, 2026.** v1.0 was frozen on Oct 23. Changes since then went through change requests in the team channel (what, why, who is affected). In v1.1, **ACCEPTED** marks a change the team agreed in the channel; it is binding now. **PROPOSED (v1.1)** marks a change still waiting for replies; until it is accepted, components may ignore it. **OPEN** marks a question without an answer yet.
- **What changed since v1.0:** see Section 9 (v1.1 entry). Every v1.1 change in the text is marked "v1.1".

# 1. The flow in one picture

```
UI → Application Layer → SUPERVISOR
        Supervisor → Agent 1 (understand story) → Agent 2 (clarify)
        Supervisor → Agent 3 (retrieve) → Agent 4 (match) → Agent 5 (verify)   [Agent 7 checks each stage]
        Supervisor → Agent 6 (prioritize) → Agent 8 (build plan) → Agent 10 (PASS/FLAG)
        Supervisor → Application Layer → UI : one unified Action Plan
```

- Agents never call each other, never talk to the user and never write to SQL or the Knowledge Base (Baseline B, Part D, §30.3, §30.8).
- Every call is one **AgentRequest** from the Supervisor and one **AgentResult** back.
- One `case_version` per cycle; a result from an older version is discarded (Part D, §30.2).

# 2. Envelope (every agent call)

The Baseline defines the envelope twice: Part D (front chapter, takes precedence) and §11.3. As the front chapter instructs ("map them to the frozen Section 11 naming plus the minimal cross-agent fields in Part D"), this contract keeps one envelope with §11 names plus the Part D fields; Section 2.3 maps the names.

## 2.1 AgentRequest

| Field | Type | Req. | Status | Note |
|---|---|---|---|---|
| request_id | string | yes | FROZEN §11.3 | unique per call |
| run_id | string | yes | FROZEN Part D | one end-to-end cycle |
| case_id | string | yes | FROZEN Part D | for anonymous sessions put the ephemeral session id here (Part D: "case_id or ephemeral_session_id") |
| case_version | integer | yes | FROZEN Part D | snapshot the agent works on |
| schema_version | string | yes | FROZEN §11.3 | `"1.0"` |
| role_id | enum | yes | FROZEN Part D | `agent_1` … `agent_10` |
| task_type | enum | yes | FROZEN Part D (values PROPOSED) | see table below |
| task_scope | string | yes | FROZEN Part D (type PROPOSED) | what this call covers, e.g. `"need_002"` or `"all_needs"` |
| allowed_case_facts | CaseFact[] | yes | FROZEN Part D | only facts this agent needs; never unrelated sensitive fields |
| upstream_result_refs | string[] | yes | FROZEN Part D | request_ids of results this call depends on |
| source_policy | enum | yes | FROZEN Part D (values PROPOSED) | `verified_kb_only` (until Oct 26, Julia's plan) · `kb_plus_external` (from Oct 27) |
| correlation_id | string | yes | FROZEN Part D | same for the whole user request; used in logs |
| payload | object | yes | FROZEN §11.3 | agent-specific, Section 4 |

**task_type values (PROPOSED):**

| role_id | task_type |
|---|---|
| agent_1 | `understand_story` · `parse_clarification_answer` |
| agent_2 | `clarify_case` |
| agent_3 | `retrieve_candidates` |
| agent_4 | `match_resources` |
| agent_5 | `verify_resources` |
| agent_6 | `prioritize_actions` |
| agent_7 | `review_stage` |
| agent_8 | `build_plan` |
| agent_10 | `validate_plan` |

## 2.2 AgentResult

| Field | Type | Req. | Status | Note |
|---|---|---|---|---|
| request_id, run_id, case_id, case_version, correlation_id | as in 2.1 | yes | FROZEN | must echo the request |
| agent_id | enum | yes | FROZEN §11.3 (= Part D `role_id`) | same values as role_id |
| schema_version | string | yes | FROZEN §11.3 | `"1.0"` (echo the request's value) |
| status | enum | yes | **FROZEN Part D** | `completed` · `partial` · `needs_clarification` · `failed` |
| result | object | yes | FROZEN §11.3 (= Part D `outputs`) | agent-specific, Section 4; `{}` if failed |
| issues | Issue[] | yes | FROZEN §11.3 (covers Part D `errors[]`) | may be empty |
| clarification_requests | ClarificationRequest[] | yes | FROZEN Part D | may be empty |
| evidence_refs | string[] | yes | FROZEN Part D | may be empty |
| uncertainty_flags | string[] | no | FROZEN Part D (type PROPOSED) | short codes, e.g. `"income_unknown"`; may be omitted |
| generated_at | ISO 8601 datetime | yes | FROZEN §11.3 | |
| is_mock | boolean | yes | PROPOSED | `true` for mock components (plan: mocks must be clearly identified) |

**Issue** (FROZEN §11.3): `code` string, `severity` `info · warning · critical`, `message` string, `related_ref` string or null.

**Wrong role or task (v1.1, ACCEPTED):** a component that receives a `role_id` it does not handle returns `status = failed` with issue `UNSUPPORTED_ROLE` (critical); a `task_type` not listed for that role in 2.1 returns `status = failed` with issue `UNSUPPORTED_TASK` (critical). Nothing is processed, `result` is `{}`, and every required envelope field is still present (including `generated_at`). All three components do this since Oct 26.

## 2.3 Name mapping Part D ↔ §11.3

| Part D | §11.3 / this contract | Rule |
|---|---|---|
| role_id (result) | agent_id | same value |
| outputs | result | same object |
| errors[] | issues[] | an error is an Issue with `severity = critical` |
| status `completed` / `failed` | status `success` / `error` | Part D values are used; if any code already uses §11.3 values: `success → completed`, `error → failed` |

## 2.4 Dates and times

- `official_deadline`, `user_target_date`, and date-valued case facts (e.g. `rent_due_date`): ISO date `YYYY-MM-DD`.
- `checked_at`, `generated_at`, `last_verified_at`: ISO 8601 datetime.
- A field marked "or null" may be null; any other field must be present and non-null.

# 3. Shared types

## 3.1 Need

| Field | Type | Status | Note |
|---|---|---|---|
| need_id | string | FROZEN | `need_001` … |
| category | enum | PROPOSED (taxonomy by Silver, Oct 20) | see 3.4 |
| subcategory | string or null | PROPOSED, OPEN (Julia) | optional; if set, must belong to its category (3.4) |
| description | string | FROZEN | short, in the user's terms |
| original_quote | string or null | FROZEN §19.2 | the user's words that support the need |
| confirmation_status | enum | FROZEN Case State | `proposed · confirmed · disputed · superseded` |
| user_reported | boolean | FROZEN §19.2 | must be `true`; we never invent needs |
| urgency | enum | FROZEN §11.4 | `immediate · high · normal · unknown` |
| urgency_reason | string or null | FROZEN | |
| user_priority | integer or null | FROZEN | rank set only by the user (1 = most important) |

## 3.2 CaseFact

| Field | Type | Status | Note |
|---|---|---|---|
| fact_id | string | FROZEN | |
| field | string | FROZEN | e.g. `household_size`, `zip_code`, `rent_due_date` |
| value | any or null | FROZEN §11.5 | null = unknown; unknown is never zero or false (§19.2) |
| confirmation_status | enum | FROZEN §11.5 | `proposed · confirmed · disputed · superseded` |
| source | enum | PROPOSED | `user_statement · user_confirmed · system_derived` |
| time_context | string or null | FROZEN §19.2 | e.g. "before job loss" |

**Fact keys in use (v1.1, ACCEPTED Oct 26).** One name per fact across all components:

| `field` | Value | Set by | Note |
|---|---|---|---|
| `zip_code` | string, 5 digits | Agent 1 | |
| `county` | string, e.g. "Sacramento County" | Supervisor (from ZIP, official source only) | |
| `household_size` | integer | Agent 1 | only when the adults are stated; never guessed |
| `children_ages` | integer[] | Agent 1 | only ages stated next to the children |
| `employment_status` | string | Agent 1 | e.g. `laid_off` |
| `rent_amount_monthly` | number | Agent 1 | |
| `rent_due_date` | ISO date | Agent 1 | the user's date, never an official deadline; must be a real calendar date; the next occurrence of the stated day |
| `cash_on_hand_approx` | number | Agent 1 | |
| `has_written_eviction_notice` | boolean | Agent 1 (`parse_clarification_answer`) | replaces `landlord_notice_exists`; absent if the answer does not settle it |
| `household_gross_monthly_income` | number | Agent 1 / user | replaces `current_monthly_income`; unknown income is never a mismatch |

A new fact key is added here through a change request before any component uses it.

- **Facts the user never stated are not stored as CaseFact** (PROPOSED, open decision 1; matches §11.4 "Unknown user facts may be omitted"). A fact the system needs but does not have appears in `missing_case_facts[]` (Agent 4) or as a ClarificationRequest; a question the user skipped or declined is recorded in `already_asked[]` (Agent 2) and the fact stays absent.
- Geography is ZIP or county only. The Supervisor passes both county and ZIP to agents (e.g. `["Sacramento County", "95823"]`); statewide ProgramRecords use `"California"` and cover all 58 counties. Never SSN, date of birth, ID, bank or card numbers (approved privacy rule).

## 3.3 ClarificationRequest

| Field | Type | Status | Note |
|---|---|---|---|
| fact_key | string | FROZEN Part D | the CaseFact.field it would fill |
| question_intent | string | FROZEN Part D | what we need to learn |
| user_facing_question | string | FROZEN §20.4 | plain language, one question |
| reason | string | FROZEN Part D | why it changes a real decision |
| applicable_program_ids | string[] | FROZEN Part D | may be empty for broad retrieval facts |
| verified_rule_ref | string or null | FROZEN §20.4 | evidence_id of the rule that makes it necessary |
| necessity_level | enum | FROZEN Part D (values PROPOSED) | required field: `required_for_decision · helpful` |
| can_skip | boolean | FROZEN §20.4 | `true` by default; a skipped answer stays unknown |

The Supervisor merges requests with the same meaning, checks existing facts and asks once (Part D, §30.8).

## 3.4 Category enum (Silver's taxonomy, Oct 20, with one addition) · PENDING JULIA (decisions 2, 6)

| category | subcategories | Priority |
|---|---|---|
| `food_assistance` | `calfresh_benefits`, `food_pantry` | P0 |
| `housing_assistance` | `emergency_shelter`, `motel_voucher`, `rental_assistance`, `eviction_prevention`, `housing_legal_aid` | P0 |
| `income_assistance` | `unemployment_insurance`, `cash_aid`, `disability_family_leave`, `employment_services` | P0 |
| `utility_assistance` | `bill_credit_grant`, `income_based_discount`, `arrears_disconnection_prevention`, `payment_arrangement`, `water_sewer_trash` | later |
| `medical_health_coverage` | `health_coverage`, `medical_care_access`, `prescription_assistance`, `medical_bill_assistance` | later |
| `debt_hardship` | `credit_counseling`, `consumer_protection_legal_aid`, `court_self_help`, `mortgage_housing_counseling` | later |
| `material_in_kind` | `furniture_household`, `clothing`, `hygiene_essentials`, `children_essentials` | later |
| `crowdfunding_guidance` | `platform_guidance` | P2, informational only (§27) |
| `other_unlisted` | — | **needs only** (PROPOSED, open decision 2): keeps a user-stated need outside the list as a coverage gap (T12). Not allowed in ProgramRecord |

Rules (Silver): lowercase snake_case, unknown values rejected, one category per ProgramRecord, 211 is a source not a category, legal aid sits under the area that triggered it. Crisis resources (988 and similar) live in the separate Verified Emergency Directory, not in KB categories. `subcategory` is optional: null or omitted means "not specified".

## 3.5 ProgramRecord and EvidenceRecord

**FROZEN §11.1 and §11.2, used as is.** ProgramRecord: program_id, program_name, organization, category, geography[], eligibility_criteria[], required_documents[], application_method[], contact[], deadlines[], processing_time, availability (`confirmed_open · temporarily_closed · unknown`), sources[], last_verified_at, verification_status (`verified · needs_review · conflicting · unverified`). Claim object: value, evidence_refs[], verification_status, checked_at. EvidenceRecord: evidence_id, program_id, field_path, claim_value, source_url, checked_at, verification_status; optional source_title, source_authority_scope, effective_date, notes. PROPOSED addition: optional `subcategory`.

**Reopening and effective dates (v1.1, ACCEPTED Oct 26):** when a page states when something changes (for example, a closed program that "re-opens Monday, November 2"), the EvidenceRecord keeps the page's exact wording in `claim_value` and the date in `effective_date` (ISO date). A closure and its reopening date are stored as `availability` rows of the same program. Agent 6 reads the reopening date from `effective_date`; an ISO date inside `claim_value` is only a fallback.

**Three separate things, never merged (Part D; cross-domain rule "Eligibility, evidence and intake availability are separate"):** evidence status (`verification_status`), preliminary individual match (`match_status`), and intake availability (`availability`). A verified program is not proof that intake is open; an open program is not proof that the user qualifies.

## 3.6 Shared enums (one definition, used everywhere)

| Enum | Values | Status |
|---|---|---|
| MatchStatus | `potential_match · supported_match · confirmed_mismatch · insufficient_information` | FROZEN §11.5 |
| VerificationStatus | `verified · needs_review · conflicting · unverified` | FROZEN §11.1 |
| Availability | `confirmed_open · temporarily_closed · unknown` | FROZEN §11.1 |
| Severity | `info · warning · critical` | FROZEN §11.3 |
| OrderGroup | `first · parallel · later` | FROZEN front chapter ("first/parallel/later grouping"); replaces `parallel_group` of §15.4 |
| ProgressStatus | `not_started · in_progress · contacted_applied · waiting_for_response · completed_received · unsuccessful` | FROZEN Baseline B (six MVP statuses); snake_case wire values PROPOSED |

**UI labels (presentation only):**

| Wire value | Label |
|---|---|
| `first` / `parallel` / `later` | Start first / Next / parallel / Later / dependent |
| `not_started` | Not started |
| `in_progress` | In progress |
| `contacted_applied` | Contacted / Applied |
| `waiting_for_response` | Waiting for response |
| `completed_received` | Completed / Received |
| `unsuccessful` | Unsuccessful |

Only an explicit user action changes `progress_status`. Agents always create cards with `not_started` and never change it (Baseline B).

# 4. Agent contracts

For each agent: payload in, result out, what it reports when information is missing, and what it depends on. `issues[]` and `clarification_requests[]` always travel in the envelope (2.2). Agent 9 (Yogesh) follows in the next phase.

## 4.1 Agent 1 — Crisis Understanding (Yogesh) · PROPOSED from §19.2

- **In (`understand_story`):** `story_text` (string), `locale` (string, default `en-US`).
- **In (`parse_clarification_answer`):** `answer_text` (string), `pending_fact_keys[]` (string — the fact_keys of the question that was asked). Out: `factual_claims[]` only for those keys; a key the answer does not settle stays absent (never guessed).
- **Out:**
  - `narrative_summary`: string
  - `triggering_events[]`: string
  - `proposed_needs[]`: Need (`confirmation_status = proposed`, `user_reported = true`)
  - `factual_claims[]`: CaseFact (`source = user_statement`)
  - `ambiguity_flags[]`: {field: string, quote: string, note: string}
  - `safety_or_official_deadline_flags[]`: {type: `safety` or `official_deadline`, quote: string, note: string}
- **Mapping to §19.2 names:** `user_reported_needs[]` → `proposed_needs[]` (`need_type` → `category`, `original_quote_or_span` → `original_quote`); factual claim `status` → `confirmation_status`.
- **Missing info:** never asks the user; ambiguities go to `ambiguity_flags`, Agent 2 decides. A value not stated in the story (e.g. children's ages) is not filled with a default.
- **Rules:** extract only explicitly stated needs; no inferred housing, debt, medical or transport needs (§19.1). Safety flags go to the Supervisor, which routes them to the safety path.
- **Depends on:** nothing upstream.

## 4.2 Agent 2 — Case Analysis & Clarification (Yogesh) · PROPOSED from §19.2, §20.4

- **In:**
  - `needs[]`: Need
  - `case_facts[]`: CaseFact
  - `already_asked[]`: string (fact_keys already asked, including skipped or declined)
  - `candidate_requirements[]` (optional, after retrieval): {program_id: string, fact_key: string, verified_rule_ref: string}
- **Out:**
  - `clarification_requests` in the envelope (at most one small cluster per turn)
  - `need_updates[]`: {need_id: string, urgency: enum, urgency_reason: string or null}
  - `optional_food_check`: boolean (one neutral food check allowed after income loss, §19.1)
- **Missing info:** that is its job; returns `needs_clarification` with the requests.
- **Rules:** ask only questions that change a real decision; never repeat an answered or declined question; unknown or declined stays unknown.
- **Depends on:** Agent 1 result; later rounds also Agent 3 candidates.

## 4.3 Agent 3 — Resource Retrieval (Silver) · FROZEN §11.4

- **In:** `needs[]` {need_id, category, description, urgency} — the Supervisor passes exactly these four fields of each Need; `geography[]`: string (county and ZIP, see 3.2); `retrieval_constraints[]`: string; `max_candidates`: integer (optional, no default).
- **Out:** `candidate_programs[]` {program_id, matched_need_ids[], retrieval_reason, source_refs[], missing_fields[]}, `retrieval_notes[]`: string. `missing_fields[]` holds ProgramRecord field names that are empty in the KB (e.g. `deadlines`, `processing_time`).
- **Missing info:** missing income does not block retrieval; empty result is valid and reported as a coverage gap, never filled with invented programs.
- **Depends on:** confirmed or proposed needs, geography. `source_policy = verified_kb_only` until Oct 26; external discovery from Oct 27 (Julia).

## 4.4 Agent 4 — Resource Matching (Silver) · FROZEN §11.5

- **In:** `candidate_programs[]` (Agent 3 result), `case_facts[]`, `needs[]`, `program_criteria[]` {program_id, field_path, value, evidence_refs[]}. **`program_criteria[]` is built by the Supervisor** from the KB records of the candidate programs (§11.5: "May be supplied by Orchestrator").
- **Out:** `matches[]` {program_id, need_ids[], match_status (MatchStatus), matched_criteria[], missing_case_facts[], mismatch_criteria[], evidence_refs[], explanation}.
  - `missing_case_facts[]`: CaseFact.field keys the match needs but does not have.
  - `matched_criteria[]`, `mismatch_criteria[]`: short text of the criterion.
  - `confirmed_mismatch` must name the criterion and the confirmed contradictory fact (§11.5).
- **Missing info:** missing user facts go to `missing_case_facts[]`; the Supervisor may turn them into one clarification. Unknown income is never a mismatch.
- **Depends on:** Agent 3.

## 4.5 Agent 5 — Resource Verification (Silver) · FROZEN §11.6

- **In:** `programs_to_check[]` {program_id, field_paths[]}, `evidence_refs[]`, `relevant_case_constraints[]`. **`programs_to_check[]` is built by the Supervisor** from Agent 4 matches, excluding `confirmed_mismatch`; `field_paths[]` are the fields the plan will show (eligibility criteria, deadlines, contact, application method, required documents, availability).
- **Out:**
  - `checked_claims[]` {program_id, field_path, claim_value, verification_status, evidence_refs[], checked_at, issue}
  - `update_proposals[]` {program_id: string, field_path: string, proposed_value: any, evidence_refs[]: string, reason: string}
  - `unresolved_questions[]`: string
- **Missing info:** a failed website check is reported as an issue, never as closure; no direct KB writes; proposals go to the Knowledge Update Process (§11.6).
- **Notes:** recertification rules such as CalFresh SAR 7 are claims inside `eligibility_criteria[]`, not a new field. A `checked_claims[]` item for `availability` carries the evidence text; the Availability enum for Agents 6, 8, 10 comes from the ProgramRecord via the Supervisor (`program_availability[]`).
- **Several statements from one source (v1.1, OPEN):** since v1.3, Agent 5 joins different values from the same `source_url` into one `verified` claim when all rows are verified (for example "closed in October" + "re-opens Nov 2"). Open question: how a real contradiction inside one page (as in our SMUD research) stays `conflicting`. Silver proposes the approach; a test case is required.
- **Depends on:** Agent 4.

## 4.6 Agent 6 — Action Planning & Prioritization (Hisham) · PROPOSED from §11.7, §15.4

- **In (the Supervisor's package, §11.7):**
  - `needs[]`: Need (with urgency and user_priority)
  - `candidate_programs[]`: Agent 3 result items
  - `matches[]`: Agent 4 result items; **v1.1 (ACCEPTED):** the Supervisor adds `program_name`, `organization` and `subcategory` from the KB record to each item (Agent 4's own result is not changed)
  - `checked_claims[]`: Agent 5 result items
  - `program_availability[]`: {program_id, availability (Availability), evidence_refs[]}
  - `timing[]`: {need_id, program_id or null, official_deadline (date or null), user_target_date (date or null), estimated_processing_time (string or null)}
  - `evidence_records[]`: EvidenceRecord (only those referenced; **v1.1:** includes the `availability` rows listed in `program_availability[]`)
  - `agent7_findings[]`: Agent 7 findings (4.7), may be empty
- **Out:** `proposed_actions[]` {action_id, need_id or null, program_id or null, suggested_priority (integer or null), order_group (OrderGroup), rationale, dependency_ids[], official_deadline, user_target_date, estimated_processing_time, evidence_refs[], uncertainty_notes[], user_override_allowed = true}.
  - `suggested_priority`: relative order inside one `order_group` (1 = first); optional. **No scoring formula** — the reason goes in `rationale` (§9.3: no numerical ranking formula is approved).
  - `order_group` replaces `parallel_group` of §15.4.
  - Steps the user must take before acting (e.g. "confirm the deadline with the provider") are written in `rationale` / `uncertainty_notes`; Agent 8 turns them into the card's `next_step`. A separate "confirm first, then apply" action is allowed (linked by `dependency_ids[]`); `need_id` may be null for an action that serves the whole case.
  - **Availability (integration run, Oct 23):** a `temporarily_closed` program is never presented as current help: `order_group = later`, the reopening date only if it is in the evidence, and an open program for the same need goes first. `unknown` availability gets an uncertainty note. **v1.1:** the reopening date comes from `effective_date` (3.5); when it is after the user's `rent_due_date`, the note says so ("reopens Nov 2, after your Nov 1 date").
- **Missing info:** unknown deadlines stay null; no invented urgency (§15.2); a conflicting deadline is never resolved by choosing one date.
- **Depends on:** Agents 3, 4 and 5 (and Agent 7 findings).

## 4.7 Agent 7 — Quality & Uncertainty Controller (Hisham) · PROPOSED

Rule list and fixtures: *Agent_7_10_IO_Contracts_Proposal* (starting point for Hisham).

- **In:** `stage` (`retrieval · matching · verification · planning`), `stage_result` (the `result` object of the agent under review — Agent 3, 4, 5 or 6 — passed unchanged), `evidence_records[]` (referenced only), `case_facts[]` (referenced only), `needs[]`.
- **Out:** `stage_assessment` (`clear · issues_found`), `findings[]` {finding_id, rule_id, severity (Severity), program_id or null, need_id or null, field_path or null, evidence_refs[], description, recommended_action}.
  - `rule_id`: `Q1` … `Q10` (rule list in the Agent 7/10 notes; thresholds — open decision 4).
  - `recommended_action`: `recheck_source · request_clarification · show_conflict_and_add_provider_confirmation · omit_unsupported_claim · report_coverage_gap · no_action`. A recommendation; the Supervisor decides.
  - Each finding is also copied into envelope `issues[]` (code = rule_id).
- **Missing info:** `status = partial`, issue `INPUT_INCOMPLETE`; never assumes data.
- **Depends on:** the stage it reviews.

## 4.8 Agent 8 — Crisis Action Plan Builder (Hisham) · PROPOSED from §9.5, §30.5

- **In:** `proposed_actions[]` (Agent 6), `needs[]`, `matches[]`, `checked_claims[]`, `program_availability[]`, `evidence_records[]`, `agent7_findings[]`.
- **Out:**
  - `plan_version`: string
  - `action_cards[]` {card_id, source_action_ids[], related_need_ids[], program_id or null, action_title, reason, next_step, priority_reason, order_group, dependency_card_ids[], source_refs[], uncertainty_notes[], official_deadline, user_target_date, processing_estimate, progress_status = `not_started`}
  - `potential_options[]` {program_id, program_name, why_it_may_matter, what_needs_checking[], official_link}
  - `coverage_gaps[]` {need_id, note}
- **Link to Agent 6 (PROPOSED):** every card lists the Agent 6 `action_id`s it is built from in `source_action_ids[]`; `dependency_card_ids[]` is translated from Agent 6 `dependency_ids[]`.
- **Rules:** no new claims; contacts, links and dates only from evidence; `progress_status` is never changed by agents.
- **Card title (v1.1, PROPOSED):** when `organization` and `program_name` are present, the title names both and keeps the name on a closed program's card (for example "Ask about rent help: Saint John's Program for Real Change — Housing Assistance Program (reopens Nov 2)"). Each P0 subcategory, including `eviction_prevention`, gets its own wording instead of the default "Contact the organization".
- **Contacts and hours in `next_step` (v1.1, change request ACCEPTED Oct 26, with Silver's condition):** a card may name a phone number, link or opening hours only from a `checked_claims[]` item with `verification_status = verified`, and shows the date it was checked (for example "Call 2-1-1 and press 8, Mon–Sat 7 a.m.–7 p.m. (checked Oct 21)"). Agent 10 keeps flagging any contact that is not in the evidence (V8). Implementation date: to agree with Hisham.
- **Repair input (v1.1, PROPOSED):** in a repair round the Supervisor passes `repair_flags[]` (the Agent 10 flags for the cards being repaired) so Agent 8 fixes exactly what was flagged.
- **Depends on:** Agent 6.

## 4.9 Agent 10 — Plan Validation & Critique (Hisham) · APPROVED rules, PROPOSED fields

- **In:** `plan_version`, `repair_round` (integer, 0 on first check), `action_cards[]`, `potential_options[]`, `coverage_gaps[]`, `needs[]`, `matches[]`, `checked_claims[]`, `program_availability[]`, `evidence_records[]`, `open_agent7_findings[]`. Case facts come in envelope `allowed_case_facts`.
- **Out:** `verdict` (`PASS · FLAG`), `repair_round`, `flags[]` {flag_id, card_id, rule_id, severity (Severity), claim_text, reason, evidence_refs[], required_correction, blocks_release}, `passed_card_ids[]`.
  - `rule_id`: `V1` … `V13` (Hisham's rules v0.3).
  - Severity (decision 4, agreed with Hisham): **critical, blocks the card** — V1, V2, V3, V4, V5, V8, V10, V13; **warning, does not block** — V6, V7, V9, V11, V12. `blocks_release = true` only for critical. Agent 7 never blocks.
  - V4 also covers a `temporarily_closed` program shown as open or as current help.
  - V13: a card asks the user to give an SSN, bank or card number to the Navigator. Saying that a program may ask for a document (e.g. "the county may ask for your Social Security card") passes.
  - Every card appears either in `flags[]` or in `passed_card_ids[]`.
- **Rules (APPROVED, Proposal #6 addendum):** flag unsupported guarantees, unknown or conflicting fields shown as confirmed, confirmed mismatch shown as a match, unverified program shown as verified, hidden critical deadline or contact ambiguity. One flag never suppresses unrelated valid cards.
- **Depends on:** Agent 8.

# 5. The Supervisor

## 5.1 What it builds

- The AgentRequest for every call, with only the facts each agent needs.
- `program_criteria[]` for Agent 4 (from KB records of Agent 3 candidates).
- `programs_to_check[]` for Agent 5 (from Agent 4 matches, excluding `confirmed_mismatch`).
- The Agent 6 package (4.6) and the Agent 8 and Agent 10 inputs (4.8, 4.9).
- One merged question to the user when several agents request clarifications.
- `case_facts[]` from Agent 1 `factual_claims[]` after the user confirms the summary (a corrected value replaces the claim).
- `program_availability[]` (Availability enum from the ProgramRecord) and `timing[]` (user dates from case facts, official deadlines only from evidence) for Agent 6.
- **v1.1 (done in Supervisor v0.2.1–v0.2.2):** the `availability` evidence rows go into `evidence_records[]`; each `matches[]` item in the planning package gets `program_name`, `organization` and `subcategory` from the KB.
- **One KB (v1.1):** the Supervisor and Agents 3–5 read the same file, `navigator/kb/kb_sacramento.json`. Two different copies stop the run at Agent 3 (unknown evidence IDs).

## 5.2 What it checks on every result

**Before any agent call — S0 input masking:** SSN-, bank- and card-number patterns in user text are replaced with `[REDACTED]` before the text reaches any agent, and the user is told not to share them. The Navigator never captures them.

A result is **accepted** only if all checks pass. Otherwise it is **rejected** and reported, never treated as success (plan acceptance criterion).

| # | Check | On failure |
|---|---|---|
| S1 | Valid JSON; all required envelope fields present | reject, issue `SCHEMA_INVALID` |
| S2 | request_id, run_id, case_id, correlation_id echo the request | reject, `IDENTITY_MISMATCH` |
| S3 | case_version equals the current snapshot | discard, `STALE_RESULT`, re-run if needed |
| S4 | All enum values are from Sections 2–3 | reject, `UNKNOWN_ENUM` |
| S5 | Every program_id / need_id / evidence_id referenced exists | reject, `UNKNOWN_REFERENCE` |
| S6 | status = `failed` | record, continue unrelated paths, no "completed" for dependents (T07) |
| S7 | No response within 30 seconds | treat as failed, `TIMEOUT` |
| S8 | `is_mock = true` | accept, but mark the run as partially mocked |
| S9 | No forbidden values (SSN, date of birth, bank or card numbers) — checked by value patterns and field names, not by words in plain text | reject, `PRIVACY_VIOLATION` |

## 5.3 Retries and repair (decision 3, agreed with Hisham)

- 1 retry per agent call.
- After an Agent 10 FLAG: only the flagged cards go back to Agent 8, maximum 2 repair rounds. If a card is still flagged, only that card is withheld; the other cards are released and the issue goes to the run report (Addendum: transparent partial plan).

# 6. Common synthetic test case — "Sacramento family, income loss" (P0)

Synthetic; no real people. Used by every component from Oct 21 to Oct 26.

**v1.1 (ACCEPTED Oct 26): demo date.** The demo story uses **rent due December 1** (the Nov 1 date is in the past after Nov 2). The Nov 1 version below stays as an extra test: it is the case where the user's date comes before Saint John's reopens. Sample `06_agent1_request_dec1.json` holds the demo story; samples 01 and 02 keep Nov 1.

**Story (input to Agent 1):**
> "I'm a single mom in Sacramento, ZIP 95823, with two kids, 6 and 9. I was laid off from my warehouse job last Friday. Rent of $1,450 is due on November 1 and I only have about $300 left. We're also running low on food this week. I don't know where to start."

**Expected Agent 1 result (key points):**
- Needs (proposed, user_reported): `income_assistance` (job loss), `housing_assistance` / `rental_assistance` (rent due Nov 1, cannot pay), `food_assistance` (low on food this week).
- Facts: zip_code 95823; household of 3 (1 adult, 2 children); employment_status laid off, last day "last Friday"; rent amount 1450, rent_due_date 2026-11-01 (user-stated, not an official deadline); cash_on_hand ≈ 300.
- **Must not appear:** medical, debt, utility, transport needs; any eligibility statement; any program name.

**Expected Agent 2 clarifications (at most one small cluster):** nothing that is already known. Candidate questions only if a real decision depends on them, for example whether a written notice from the landlord exists (affects eviction-prevention options). The food check is not needed: food was volunteered.

**Expected end state on Oct 26 (mocks allowed):** one plan covering all three needs; every program card has a source and a last-verified date or an explicit uncertainty note; no "you qualify" wording; the rent date is shown as the user's date, not as an official deadline.

**Sample files (`navigator/samples/`):**

| File | What it is |
|---|---|
| 01_agent1_request.json | Agent 1 request with the story |
| 02_agent1_result_expected.json | expected Agent 1 result |
| 03_invalid_result_for_supervisor_test.json | deliberately broken result for the Supervisor demo |
| 04_agent6_fixture_sacramento.json | mock input for Agent 6 (tests: unknown income, conflicting deadline) |
| 05_agent10_fixture_mixed_plan.json | 3-card plan for Agent 10 (test: one unsupported guarantee flagged, two cards pass) |
| 06_agent1_request_dec1.json | v1.1: Agent 1 request with the demo story (rent due Dec 1) |

Programs in 04/05 are placeholders (MOCK-*), not real Sacramento programs. For integration the real records come from Silver's single KB file `navigator/kb/kb_sacramento.json` (v1.1: package v1.3, Oct 27; 4 programs, 116 evidence records: CalFresh, EDD Unemployment Insurance, Saint John's Housing Assistance — temporarily closed, reopens Nov 2 (`effective_date` 2026-11-02), Coordinated Access via 2-1-1 press 8).

# 7. Integration instructions

1. **Language:** Python 3.11+. Standard library first; any extra package must be listed in `requirements.txt`.
2. **Component shape:** each owner's package exposes `handle(request: dict) -> dict` that takes an AgentRequest and returns an AgentResult; one `handle` per package may route by `role_id`. No network calls to other agents. Results set `schema_version` to `"1.0"`.
3. **Mocks:** until your logic is ready, return a fixed result with `is_mock: true`. Mocks must still pass the Supervisor checks.
4. **Repository layout (v1.1: superseded by the GitHub repository and its CONTRIBUTING.md; the structure below is kept for reference):**

```
navigator/
  contracts/        schemas and this document
  samples/          shared test case JSON (inputs and expected outputs)
  supervisor/       Slav
  agents/agent_1_2/ Yogesh
  agents/agent_3_4_5/ Silver
  agents/agent_6_7_8_10/ Hisham
  kb/               ProgramRecord / EvidenceRecord JSON (from Silver's sheet)
  tests/            each owner's tests (expected vs actual)
  bob_sessions/     Bob task session screenshots and exported .md (required for judging)
```

5. **Submitting a component:** post in the channel: what it does, how to run it, sample input, sample output, test results, known issues (Julia's deliverable rule).
6. **Security:** no `venv/`, `__pycache__/` or local caches in packages or the repository; no API keys, tokens or passwords in the repository or in samples. The final repository will be public; IBM deactivates exposed credentials.
7. **Bob:** build in Bob IDE and keep task names clear; at the end each of us exports the relevant task sessions to `bob_sessions/`.
8. **IBM integration:** if Orchestrate access is ready, we map the same contracts to Orchestrate agents and tools; if not, the local Python prototype uses the same contracts (Julia: "A local prototype does not count as completed IBM integration.").

# 8. Not in v1.0

Agent 9 contracts; SQL schema and Application Layer API; UI contracts; email and account flows. These follow after Oct 26 when owners are assigned.

# 9. Change log

- **v1.1 (Oct 27, 2026):** ACCEPTED in the channel (Oct 25–26): one name per fact key with a registry (3.2), `has_written_eviction_notice` and `household_gross_monthly_income`; failed envelope with `UNSUPPORTED_ROLE` / `UNSUPPORTED_TASK` everywhere (2.2); reopening date in `effective_date` on `availability` rows (3.5, 4.6); program name, organization and subcategory added to matches by the Supervisor (4.6, 5.1); availability evidence passed to Agents 6, 8, 10 (5.1); contacts and hours in `next_step` only from verified claims with the check date (4.8); demo rent date Dec 1, Nov 1 kept as an extra test (6); one KB file (5.1); repository layout moved to GitHub (7). PROPOSED: card titles with organization and program name, own wording per P0 subcategory (4.8); `repair_flags[]` (4.8). OPEN: same-source statements in Agent 5 (4.5); progress statuses (decision 11); evidence freshness window for Q7 (decision 12).
- **v1.0 (Oct 23, 2026) — FROZEN:** `schema_version "1.0"`; Agent 1 `parse_clarification_answer`; Agent 6 `need_id` may be null, separate confirm-then-apply action allowed, availability rule for `temporarily_closed`; Agent 5 notes (SAR 7 as a claim; availability enum from ProgramRecord); Agent 10 V13 and severity table, V4 covers closed programs; geography = county + ZIP, statewide = "California"; Supervisor S0 input masking, S7 timeout 30 s, S9 by values, builds case facts, availability and timing; `handle()` may route by role_id; decisions status in Section 10.
- **v1.0-RC (Oct 22, 2026):** checked against the Final Consolidation Baseline. Envelope: status FROZEN per Part D; Part D fields `task_scope`, `source_policy`, `uncertainty_flags[]` added; name mapping Part D ↔ §11.3; `run_id` added to check S2; `task_type` values; date formats. Types: six ProgressStatus values with UI labels; shared enums table; OrderGroup replaces `parallel_group`; evidence / match / availability kept separate; `necessity_level` required (Part D); unstated facts not stored as CaseFact (proposed); `subcategory` optional. Agents: Agent 1 flag name restored to §19.2 (`safety_or_official_deadline_flags`) with name mapping and typed arrays; Agent 2 typed arrays; Agent 3 receives the four §11.4 fields; Supervisor builds `program_criteria[]` and `programs_to_check[]`; Agent 5 `update_proposals[]` fields from §11.6; Agent 6 exact input incl. `candidate_programs[]`, `suggested_priority` without formula; Agent 7 `stage_result` and enums; Agent 8 `source_action_ids[]`, nullable `program_id`, `program_name` in potential options; Agent 10 exact input and enums. Retries and repair proposal moved to 5.3. Sample files listed.
- **v0.1 (Oct 21, 2026):** first draft from the Baseline, Section 11, §§15, 19, 20, 30, the Proposal #6 addendum and Silver's taxonomy.

# 10. Decisions status (updated in v1.1)

| # | Decision | Status in v1.1 |
|---|---|---|
| 1 | Unstated facts not stored as CaseFact | used as written (no objections) |
| 2 | Silver's taxonomy, `other_unlisted` for needs only | **default in use, PENDING JULIA** |
| 3 | 1 retry per call, 2 repair rounds, then partial release; timeout 30 s | agreed (Hisham); timeout set |
| 4 | Severity thresholds for Agents 7 and 10 | agreed (Hisham's table, 4.9) |
| 5 | Repository owner | later, separate proposal |
| 6 | Optional `subcategory` | **default: optional, PENDING JULIA** |
| 7 | Funeral and burial assistance | **default: later (P2), PENDING JULIA** |
| 8 | One-time charity emergency grants | **default: later (P2), PENDING JULIA** |
| 9 | Should `supported_match` require that no criterion (e.g. income) is missing? | open — new from the Oct 23 integration run; current code keeps Silver's rule |
| 10 | task_type names | fixed as in 2.1 (`match_resources`, `verify_resources`) |
| 11 | Progress statuses: six in the Baseline (3.6) or five in Blueprint v1.1 (Not Started / In Progress / Waiting / Completed / Need Help)? | **v1.1: OPEN, PENDING JULIA** — contracts keep the six Baseline values until decided |
| 12 | Evidence freshness window for Agent 7 rule Q7 (`recency_window_days`): after how many days a check is too old | **v1.1: OPEN, PENDING JULIA** — until decided, Agent 7 reports the oldest evidence age per program as info only |
