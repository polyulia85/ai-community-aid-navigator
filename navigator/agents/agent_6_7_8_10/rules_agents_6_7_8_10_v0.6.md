# Agents 6, 7, 8, 10: Rules (v0.3)
Owner: Hisham | Aligned to SHARED_CONTRACTS_v1.0 and Slav's Agent_7_10_IO_Contracts_Proposal (rule IDs adopted as-is).
Code: agent_6_7_8_10.py, entry point handle(request). Tests: run_tests.py.

## How the four roles fit together
1. Agent 7 checks results from Agents 3-5 before planning.
2. Agent 6 orders the actions (first / parallel / later) and explains why.
3. Agent 8 turns the actions into one unified plan of Action Cards.
4. Agent 10 reviews the finished plan: PASS or FLAG.
No agent talks to the user, writes to SQL or the Knowledge Base, or changes a progress status.

## Agent 6: Prioritization
P6-1 Safety emergencies go to the safety path, not routine planning.
P6-2 Urgency sets the starting group: immediate -> first, high -> parallel, normal -> later.
P6-3 A conflicting official deadline adds a "confirm the deadline" step first; the application depends on it.
P6-4 Only a verified deadline becomes official_deadline. The user's own date (for example rent due Nov 1) is user_target_date, never official.
P6-5 Benefit applications start early and run in parallel; a follow-up step depends on them.
P6-6 Missing facts become "confirm with the provider" notes. Unknown income never blocks the plan.
P6-7 No invented urgency, deadlines or processing times. No numeric scoring formula.
P6-8 No cap on actions; every stated need is covered. The user can reorder anything (user_override_allowed = true).
P6-9 Confirmed mismatches are never turned into actions.

## Agent 8: Plan Builder
B8-1 One plan covering every stated need; needs with no program go to coverage_gaps with an honest note.
B8-2 Card fields per contracts 4.8; progress_status always starts as not_started.
B8-3 No new claims: every statement comes from the input; uncertainty stays visible in plain words.
B8-4 Wording follows Technical Design 14.2 ("This program may be relevant to your situation because...").

## Agent 7: severity table (proposal for Slav's open decision #7)
Agent 7 reports findings; the Supervisor decides the consequence. Blocks release = no (Agent 7 never blocks; Agent 10 does).
| Rule | Detects | Severity |
| --- | --- | --- |
| Q1 | Claim marked verified without resolvable evidence | critical for deadlines, contacts, availability; warning otherwise |
| Q2 | Conflicting values for the same field | critical for deadlines and contacts; warning otherwise |
| Q3 | Unknown labeled conflicting, or the reverse | warning |
| Q4 | Closure inferred from a failed website check | critical |
| Q5 | Match status not supported (for example mismatch without a named rule) | critical for a wrong mismatch; warning otherwise |
| Q6 | Broken program or need reference | critical |
| Q7 | Stale evidence | warning (window still to be agreed; report age only) |
| Q8 | Stated need with no candidate or coverage gap | warning |
| Q9 | Instructions found inside retrieved web content | critical (treated as data, never followed) |
| Q10 | Discovery candidate labeled as a Knowledge Base entry | warning |

## Agent 10: severity table (proposal for Slav's open decision #7)
| Rule | FLAG when | Severity | Blocks release of that card |
| --- | --- | --- | --- |
| V1 | Guarantee ("you will receive", "you qualify"), including in processing_estimate | critical | yes |
| V2 | Unknown or conflicting field shown as confirmed | critical | yes |
| V3 | Confirmed mismatch shown as a match | critical | yes |
| V4 | Unverified program shown as verified or open | critical | yes |
| V5 | Conflicting deadline or contact hidden, or one date chosen | critical | yes |
| V6 | No grounded next step | warning | no |
| V7 | Says a website lacks information when it was not reachable | warning | no |
| V8 | Phone, URL, contact or program not in the evidence | critical | yes |
| V9 | User date or processing estimate shown as an official deadline | warning | no |
| V10 | Progress status changed without user input | critical | yes |
| V11 | Potential option missing official link or what needs checking | warning | no |
| V12 | Stated need missing with no coverage-gap note | warning | no |
| V13 (proposed) | Asks for SSN, bank or card numbers | critical | yes |
Warnings are released but fixed in the repair round. One flag never removes unrelated cards (passed_card_ids).

## After a FLAG (agree with Slav's proposal)
The Supervisor sends only the flagged cards back to Agent 8, maximum 2 repair rounds. A card still blocked after round 2 is withheld; all other cards are released and the issue goes to the run report.

## Tests (run_tests.py)
Part A, Slav's files: Agent 6 fixture (11 checks from his must / must-not list), full chain Agent 8 -> Agent 10 on his case (PASS), Agent 10 mixed-plan fixture (only CARD-001 flagged V1; CARD-002 and CARD-003 released), Agent 7 conflict finding (Q2 critical).
Part C, added Oct 22: V2 (unknown described as confirmed), V7 (website said to lack info when unreachable), Q3 (single value labeled conflicting), Q4 (closure from failed check), Q9 (hidden instructions in retrieved text), Q10 (discovery candidate labeled as KB entry).
Part B, our own: coverage, ordering, unknown income PASS, hidden conflict V5, guarantee V1 on one card only, mismatch V3, invented program V8, user date as official V9, phone not in evidence V8, system-set status V10, Agent 7 Q2.

## Still open
1. Evidence freshness window for Q7 (team decision).
2. Timeout per agent call: closed. Handled in the Supervisor (own process, 30 s limit).
All Agent 7 and Agent 10 rules are now checked automatically except Q7 (needs the freshness window).

## Added Oct 22 (from Slav's contract notes)
- Q5 full: supported_match with missing required facts -> warning. A mismatch decided while facts are unknown (e.g. unknown income) -> critical.
- Q7: no window agreed yet, so Agent 7 reports the oldest evidence age per program as info only. If `recency_window_days` is passed, older evidence -> warning.
- Agent 10 (contract 4.4): a card citing evidence not passed in -> status `partial`, issue `INPUT_INCOMPLETE`, card not in passed_card_ids.
- Tests C-Q5a, C-Q5b, C-Q7a, C-Q7b, C-IN added.
- V13 (accepted by Slav with a condition): flags only cards asking the user to give SSN, bank or card numbers to the Navigator. Program requirements such as "the county may ask for your Social Security card" pass. Test C-V13.
- Timeout: 30 s per agent call, handled in the Supervisor.

## v0.4, Oct 23 (contracts v1.0 frozen; Slav's integration run findings)
- Agent 6: a temporarily_closed program goes to `later`, never current help. Reopening date only if an evidence record states it. Note: "reopens Nov 2, after your Nov 1 date". An open program for the same need (for example 2-1-1 press 8) goes `first`.
- Agent 8: the closed card title says "reopens Nov 2, after your Nov 1 date". Every card has source_action_ids[]. plan_version is a string.
- Agent 10: V4 also flags a temporarily_closed program shown as current help (not in `later`, or no closed/reopens wording). Critical, card held.
- All results use schema_version "1.0". need_id may be null.
- Tests: C-CL6, C-CL8, C-CL10a, C-CL10b. 51 of 51 checks pass.
- handle() checks task_type per role (agent_6 prioritize_actions, agent_7 review_stage, agent_8 build_plan, agent_10 validate_plan). A wrong task_type returns status `failed` with issue UNSUPPORTED_TASK and is not processed. Test C-TASK. 51 of 51 checks pass.
- Oct 26: reopening date read from the evidence row's effective_date first, ISO date in claim_value as fallback (Slav's integration run). Test C-EFF. Labels for v1.1 fact names has_written_eviction_notice and household_gross_monthly_income. 51 of 51.

## v0.6, Oct 29 (contracts v1.1)
- Agent 8 titles name the organization and program when the Supervisor passes them, also on a closed program's card, for example "Ask about rent help: Org, Program (reopens Nov 2, after your Nov 1 date)".
- Every P0 subcategory has its own wording, including eviction_prevention, emergency_shelter, motel_voucher, housing_legal_aid, cash_aid, disability_family_leave and employment_services.
- Repair round: when repair_flags[] is passed, Agent 8 rebuilds only the flagged cards, applies each flag's correction and lists them in repaired_card_ids.
- Missing or null input (for example needs: null) returns partial with INPUT_INCOMPLETE instead of an error.
- Tests: C-NULL, C-NAME, C-EVP, C-REP. 51 of 51 checks pass.
