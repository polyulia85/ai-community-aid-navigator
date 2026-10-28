# FINAL CONSOLIDATION & IMPLEMENTATION BASELINE — 17 OCT 2026

Status: CONSOLIDATED TECHNICAL BASELINE. This front chapter is authoritative when an older working proposal, pending question, or duplicated legacy passage conflicts with a later approved decision. The original detailed sections, tables, fixtures and diagrams are preserved below as technical reference. This is an internal design audit, not verification of current Sacramento program availability or IBM deployment.

## A. Decision precedence and audit outcome

Precedence: (1) this approved-decision consolidation; (2) Section 30 approved rules and other explicitly APPROVED domain rules; (3) frozen MVP contracts in Section 11, unless superseded; (4) earlier working/proposed schemas and the old Section 29 question register as historical engineering notes only. No Pending/Proposed text may silently override an approved rule.

Audit outcome: no new user-facing product capabilities are required for MVP. Implementation work remains for completing exact payloads for all ten roles, validating data/enum consistency, source population and integration tests. These are build tasks, not invitations to reopen approved product choices.

## B. Approved end-to-end behavior

- One continuous Case and one evolving Action Plan per registered user. No fixed cap on stated needs, candidate programs or Action Cards. Do not create duplicate Cases or reset user action statuses during reassessment.

- Anonymous visitor: receives initial plan without account; may request one-time email copy without registration and with privacy warning; may optionally create email-based account to save; otherwise temporary session expires without persistent recovery.

- Registered visitor: Case, Action Plan, manually chosen action statuses, and minimal current dialogue checkpoint persist. On return, Supervisor resumes the pending question/step; no new intake or automatic full reassessment solely because the user logs in.

- Full-context logical reassessment happens when user reports changed circumstances/new need or explicitly asks to revisit recommendations. Review prior facts, recommendations, and manually recorded outcomes; re-run only relevant eligibility/retrieval. A user edit that changes relevant case facts is a reported change. Status-only updates do not trigger reassessment.

- All end-user conversation flows through Supervisor/Orchestrator and the UI. Agents never directly ask the user, send messages, write SQL, or independently edit the plan. Supervisor merges duplicate/overlapping questions, checks existing Case facts, asks once and distributes the answer to relevant roles.

- Hybrid execution: parallelize independent needs; enforce dependency order for understanding/clarification, retrieval/matching/verification, planning, plan assembly, and final review. A consistent case_version snapshot per cycle prevents stale overwrites. Bound retries, timeouts and loop depth; represent partial failures explicitly.

- Application Layer alone commits approved Case/plan changes in SQL after validation and version checks. Keep KB program evidence separate from personal Case State. Do not build a separate registry of rejected programs.

- Separate source/program verification, individual eligibility uncertainty, and intake/funding availability. Relevant official government programs with unknown personal eligibility may appear in a compact potential-options area with the official link and exact missing facts. Never present unconfirmed program operation as verified.

- Only user-raised needs trigger corresponding domains. Ask minimal program-specific questions, reuse existing data, do not infer additional needs from a crisis narrative. Prioritize first, parallel/next and dependent/later actions without a universal top-three cap.

- Action statuses are set by the user only; no automated calendar, deadline tracking, reminder, outreach, application submission, or status mutation. Published processing times are informational, not promised dates.

## C. Ten roles — fixed responsibility map

- Agent 1 — Crisis Understanding: Extract story and user-stated needs; propose clarification, not eligibility decisions.

- Agent 2 — Case Analysis & Clarification: Determine only missing case/program-specific facts; return requests to Supervisor.

- Agent 3 — Resource Retrieval: Retrieve KB candidates and bounded approved fallback with source references.

- Agent 4 — Resource Matching: Relate candidates to stated needs and known facts; distinguish possible match from confirmed mismatch.

- Agent 5 — Resource Verification: Verify published geography, requirements, source recency and separate intake availability.

- Agent 6 — Action Planning & Prioritization: Order actions by user context, dependencies and parallelism; no unilateral status updates.

- Agent 7 — Quality & Uncertainty Controller: Flag intermediate unsupported claims, conflicts, gaps and stale evidence.

- Agent 8 — Crisis Action Plan Builder: Assemble one unified plan and action cards from validated results, no new claims.

- Agent 9 — Personal Crisis Navigation: Support user navigation of existing plan, user statuses and questions via Supervisor; no unilateral plan rewrite.

- Agent 10 — Plan Validation & Critique: PASS/FLAG final plan consistency and safety before release.

Supervisor is a coordinator, not an eleventh specialist. Ten roles are conceptual responsibilities, not a requirement to deploy ten separate IBM agents.

## D. Shared agent interface — implementation baseline

AgentRequest fields (minimum): run_id, case_id or ephemeral_session_id, case_version, role_id, task_type, task_scope, allowed_case_facts, upstream_result_refs, source_policy, correlation_id. Never transmit unrelated sensitive Case fields.

AgentResult fields (minimum): run_id, role_id, case_version, status, outputs, clarification_requests\[\], evidence_refs\[\], uncertainty_flags\[\], errors\[\], correlation_id. Allowed status values for the transport envelope: completed, needs_clarification, partial, failed. These transport statuses are NOT user Action Card statuses or program eligibility labels.

ClarificationRequest: fact_key, question_intent, reason, applicable_program_ids\[\], necessity_level; Supervisor deduplicates by meaning, not merely string equality, checks Case facts, then asks one appropriate question through UI.

Program candidate must carry separate evidence/source status, preliminary individual eligibility assessment, and independently reported availability/intake status. The exact enum spelling from the frozen Section 11 contract must be reused where defined; do not introduce competing enums from earlier drafts.

No agent writes to persistent state. Supervisor routes validated proposals to Application Layer, which checks case_version, validates schema, commits one transaction and preserves user-entered action statuses. On version conflict, re-read current Case and re-evaluate affected results; never silently overwrite.

## E. Dialogue checkpoint and interruption

Anonymous session: no account means no durable Case recovery. Registered session: persist pending_question / current_step / relevant run context in existing Case-associated storage, not a separate recovery subsystem. On return Supervisor says where the conversation paused and asks whether to continue. In-flight agent outputs are not trusted across changed case_version.

## F. Domain safeguards — approved scope

- Food: CalFresh standard/expedited and food banks are distinct paths; no invented eligibility or immediate availability.

- Housing: shelters, confirmed vouchers, rent aid, subsidized housing and legal help only as relevant; no fabricated funding or guaranteed placement.

- Utilities: provider/type/notice only if user raises utilities; verified provider aid, LIHEAP and charities.

- Income: distinguish UI, CalWORKs Immediate Need, GA, SDI, PFL and other mechanisms by actual program rules.

- Medical: distinguish insurance coverage, care, prescriptions and bills; person-specific insurance details only when relevant.

- Debt: creditor hardship, nonprofit counseling and legal aid; no negotiations, guarantees, blanket stop-payment advice or assumed inherited liability.

- Crowdfunding: verified platform setup/rules only; no drafting, rewriting or optimizing appeals, titles or fundraising stories.

- Material/in-kind: user-requested items, verified charities and self-directed free-listing channels; no scraping, live stock claims or arranging exchanges.

- All domains: only rule out on verified mandatory criterion with no applicable exception. Unknown means check, not reject. Expense/assets deductions must be program-specific.

## G. Reconciled legacy issues — no further product approval required

- Section 29.1 (agent user communication, routing, repeated calls): RESOLVED by this chapter and Section 30.8. Remaining work is payload implementation and tests, not user approval.

- Section 29.2 (Case lifecycle, persistence, resume, write ownership): RESOLVED at behavioral level; technical SQL schema and transactional mechanics are developer work.

- Section 29.4 (source evidence, conflicts and missing eligibility): RESOLVED at policy level; actual government-source records and freshness checks require evidence work.

- Section 29.5 (anonymous plan, account, email delivery, action status): RESOLVED at behavioral level. Final UI layout is implementation, not a new product decision.

- Sections 16/18/19/20/22 overlap on intake and housing: apply the user-led minimal-question rule and Section 20 detailed housing path, constrained by the newer approved domain and cross-domain rules. Treat duplicates as reference, not parallel competing policies.

- Section 15.6 pending presentation question: no need to reopen; use the approved single plan with contextual first/parallel/later grouping and compact government potential-options section.

- Earlier proposed agent envelope and working Case State schema are not independent competing schemas; map them to the frozen Section 11 naming plus the minimal cross-agent fields in Part D.

- Section 29 remains a historical developer checklist. Do not ask the user again to approve resolved rules. Any truly blocking new engineering ambiguity must be documented with exact conflict, affected behavior and proposed minimal implementation choice.

## H. Acceptance suite and implementation gates

- T01 Multiple agents request household income: Supervisor asks once, answer shared across tasks, no direct agent-user message.

- T02 Registered user interrupts during a question: checkpoint survives, Supervisor resumes same Case without full intake restart.

- T03 Anonymous user leaves without registration: no persistent Case or restoration link; one-time email delivery never creates an account.

- T04 Case updated while agents run: stale case_version results cannot overwrite newer facts or user-entered action statuses.

- T05 Government program is officially documented but eligibility facts missing: show relevant potential option with official link and missing conditions, not a false rejection.

- T06 Program source unavailable or conflicting: no verified/available claim; Agent 7 flags; final Agent 10 checks representation.

- T07 One independent agent times out: dependent actions are not falsely marked complete; unrelated validated assistance can proceed with transparent limitations.

- T08 Newborn or changed income in saved Case: reconsider affected old and new needs without duplicating cards or resetting user statuses.

- T09 User changes only Action Card status: no automatic new program search.

- T10 User has several needs: preserve all, support parallel paths, no arbitrary top-three cap.

- T11 Crowdfunding draft request: no generated appeal; only factual platform guidance.

- T12 KB has no verified match: retain unmet need and explain limitations, never hallucinate a resource.

Build gate 1: implement exact typed I/O and consistent enum mapping for Agents 1–10. Gate 2: confirm current official Sacramento sources in KB separately from this document. Gate 3: integration test IBM supervisor, tools, SQL ownership and session/email workflows. Gate 4: run fixtures T01–T12 and existing detailed domain fixtures. These are not yet claimed as completed.

# I. Original detailed technical design (preserved reference)

The following legacy chapters remain in their original order, including original diagrams and test fixtures. Where older wording conflicts, the authoritative consolidated baseline above controls.

CONTENTS

Technical Design & Agent Data Contracts \| Sacramento Pilot

1\. Design goals and source of truth 3

2\. Agent access and responsibility matrix — Proposed v0.1 3

3\. Case State Contract — Working v0.3 4

4\. Resource & Evidence Contract — Decisions and open schema 4

5\. Shared agent result envelope — Proposed, not frozen 5

6\. Agent input/output contract worklist 5

7\. Error handling, tracing and quality 5

8\. Implementation agenda and decision log 5

Decision Addendum — Proposal \#6: Plan Release Validation 4

9\. Detailed data contracts — working specification 6

10\. Change log and decision boundaries 8

11\. Frozen MVP field names and typed interfaces — 17 October 2026 9

12\. Agent build instructions and tool boundaries — Agents 3, 4, 5 11

13\. Approved search fallback and prioritization workflow 13

14\. Approved user-facing wording for preliminary program options 14

15\. Agent 6 — Action Planning & Prioritization: approved behavioral contract 15

16\. Agents 1 and 2 — approved intake dialogue principles and open implementation work 16

17\. Food assistance intake — CalFresh and Sacramento food pantries (approved design) 18

18\. Housing assistance — approved intake and search scope (17 October 2026) 19

19\. Shared intake decision engine — implementation-ready behavior contract 21

20\. Housing assistance — detailed Bob implementation specification 23

21\. Cross-section completeness audit and build-readiness gates 24

22\. Bob implementation contract — executable rules 25

23\. Utility Assistance — approved intake and matching logic 28

24\. Income Assistance — approved discovery and implementation contract 29

25\. Medical Assistance & Health Coverage — approved design 32

26\. Debt Hardship Assistance — approved bounded navigation algorithm 33

27\. Crowdfunding — informational guidance only 35

28\. Material & In-Kind Assistance — approved discovery and bounded search 35

29\. Developer clarification register — implementation questions and decision gates 37

# SYSTEM ARCHITECTURE — AT A GLANCE

Complete logical architecture: all 10 existing agents, Orchestrator, application services, Verified Knowledge Base / RAG, Case State, and the unified Action Plan.

<img src="technical_design_media/media/image2.png" style="width:6.2in;height:7.67095in" />

Figure 1. Complete system architecture (10 agents + Orchestrator). Arrows indicate conceptual processing and data dependencies; Orchestrator alone controls dispatch. Agent 7 and Agent 10 provide distinct quality checks.

# APPROVED ARCHITECTURE MAP — what is an agent algorithm vs. product workflow

This map is the controlling guide for the project lead and Bob. Agent reasoning, product workflow, persistence and presentation are separate responsibilities. If an older section mentions a calendar, automated deadline tracking, or automatic status changes, this approved decision supersedes it.

## A. Agent algorithms (AI / Orchestrator / Agent 6 Plan Builder)

Agent 1 identifies only user-stated needs; Agent 2 clarifies only necessary facts. Retrieval, Matching and Verification find and qualify resources. Agent 6 (Plan Builder) produces and updates ONE unified action plan for ONE continuing Case, groups recommended actions into 'Start first', 'Next / parallel', and 'Later / dependent', and explains dependencies. Prioritization is based on the user's circumstances, not a fixed category order. No cap on needs or actions. These groupings are recommendations, NOT progress statuses.

## B. Product workflow / application business logic (non-agent)

The application allows a user to view one plan and manually choose a progress status for each action. Allowed MVP statuses: Not started; In progress; Contacted / Applied; Waiting for response; Completed / Received; Unsuccessful. Only an explicit user action can change a status. Neither agents nor elapsed time, website processing estimates, email events, or external assumptions may update it automatically. If the user changes status only, do not automatically launch a new resource search. If the user requests alternatives or reports changed circumstances, relevant unresolved needs may be re-evaluated while retaining completed actions and history.

## C. Data / Case State persistence (not an agent algorithm)

Persist one continuing Case and one living Plan; store multiple user-stated needs, plan action IDs, recommended sequence group, user-selected progress status, status change history and relevant facts. Keep sequence_group and user_progress_status as distinct fields. Preserve old actions, their statuses and provenance when new needs are added. Updating a fact must not silently overwrite the user's action status. Store program-published processing times, when verified, as optional source-backed informational text, never as user deadlines or triggers.

## D. UI / presentation (not an agent algorithm)

Show the three recommended action groups and a manual status selector on each action. Colors are derived ONLY from the user-selected status (for example gray = not started, yellow = in progress/applied/waiting, green = completed, red = unsuccessful); colors are presentation polish and not an MVP logic dependency. The interface must not suggest the system has independently confirmed an application or benefit.

## E. Registration and communication (application services)

The initial intake and first plan require no registration. Offer optional email-based account creation after showing the plan; verify email and attach the existing Case/Plan. Phone is not required. A user may separately request an emailed copy of the plan with a privacy warning. No calendar, no automated deadline tracking and no scheduled action reminders in the MVP. Authentication emails remain allowed. Any older references to deadline reminders or a calendar are superseded.

## F. Explicit boundaries and acceptance tests

Test 1: The plan has three priority groups, but every action starts with user_progress_status = Not started; group placement never implies Waiting or Completed. Test 2: Changing a status updates only the selected action and its history, not its priority group or any other action. Test 3: A program website says '30 days processing': display only as verified information, do not set a deadline, send a reminder, or change status. Test 4: User returns with a new need: append to the same Case and revise the single plan while retaining past statuses. Test 5: An unsuccessful action remains visible; alternatives are searched only on user request or a relevant change in circumstances. Test 6: A new user can receive the plan without email; email registration is optional after plan presentation.

Decision status: APPROVED for MVP product logic. Open for implementation: exact field types, API names, account/session security and final UI styling. Bob must not treat those as approved by implication.

# APPROVED DECISION 7 — Returning User Case Reassessment Workflow

Status: APPROVED (product/agent behavior). One continuing Case and one unified living plan; no new Case, duplicate intake, calendar, or automatic change to user-selected action statuses. This workflow applies when a returning registered user reports material changes or new needs.

## Trigger and clarification — Agent 1 / Agent 2

Load existing Case, prior facts with history, all previously stated needs (including needs for which no matching program was previously recommended), past recommendations, current action plan and user-entered progress statuses. Identify what changed and ask only targeted questions needed to understand the impact. Example: when a new household member is reported, ask whether household income stayed the same or changed, if this matters to relevant programs. Do not repeat facts already known unless their currency is material. Ask once whether any new needs arose; do not impose a general checklist.

## Reassessment — Orchestrator and existing retrieval/matching/verification agents

Reassess the complete existing Case context and all previously stated needs. Re-run relevant discovery, eligibility matching and verification against the current Verified Knowledge Base and verified external sources when needed. Do not require a persistent inventory of programs that were previously ruled out. Do not infer eligibility merely from a changed income or household size; apply current program-specific rules.

## Plan update — Plan Builder / Application Logic

Update the SAME unified plan: keep completed and existing actions with their user-selected statuses and history; do not silently delete, reset, or duplicate them. Add newly relevant actions, explain revised options, and retain an audit trail of changed recommendations. If a fresh application may be needed, suggest a distinct new action rather than overwriting an earlier completed one. The AI may reorder recommended priority groups (Start first / Next or parallel / Later or dependent) based on changed needs, but priority grouping is not a progress status. Only the user changes the progress status. A status-only edit does not trigger reassessment or search.

### APPROVED DECISION 8A — User-triggered reassessment (no rejected-program registry)

Status: APPROVED. Reassessment is triggered by a meaningful user request: reported changed circumstances, a new need, or an explicit request to reconsider assistance or alternatives. Merely logging in, viewing the plan, or changing a user-selected action progress status MUST NOT trigger a full reassessment.

Application/business logic identifies the event and routes it to Orchestrator. Orchestrator loads the complete existing Case context, asks only relevant clarifications through existing agents, and selectively reruns affected resource checks. No scheduled, background, or autonomous reassessment is in MVP.

Case State stores the user-provided information and needs, the existing unified plan, recommendations actually presented, user-controlled progress statuses and relevant interaction context when the user opts to save a Case. The MVP does NOT maintain a separate historical registry of every program considered but not recommended. Program eligibility rules and source evidence belong to the Verified Knowledge Base.

Acceptance fixtures: (a) user logs in and reads plan -\> no reassessment; (b) user marks an action Submitted -\> only user status/history changes; (c) user reports a newborn and unchanged income -\> clarify relevant facts, revisit earlier household-sensitive needs/programs; (d) user adds food assistance need -\> assess new need in same Case without deleting earlier actions; (e) user asks for alternatives after unsuccessful application -\> recheck relevant resources while preserving history.

## Case State contract requirements (to finalize in Data Contracts)

For registered users, maintain stable user_id, case_id and action identifiers, user-provided Case context, previously stated needs, current plan and user-selected action statuses. Persist data in an account-linked SQL-backed Case; the exact normalized SQL tables, event model and retention periods are implementation design items. Do NOT create a separate per-user archive of all rejected programs. For anonymous users, data is session-scoped unless they explicitly register and save.

## Acceptance fixtures for Bob

R1: User originally asked about Medi-Cal, was not matched, then reports a new child and unchanged income: ask only needed clarification, recheck the previously stated medical coverage need under program-specific household rules, and present a potential match only if verified. R2: Income decreases: reconsider previously unmatched income/food/coverage programs relevant to user-stated needs. R3: User previously marked an application Completed / Received: do not reset its status or add the same application as a fresh action. R4: User adds a new need: append it to the same Case and plan; retain earlier needs and history. R5: User only changes an action status: persist the change without initiating a new agent search. R6: No verified match after reassessment: communicate limits and next verification channels without inventing a program.

Implementation boundary: This is an Orchestrator-controlled workflow using existing agents, not a new agent or an autonomous agency-status monitoring service.

OPEN GATE E — QA and acceptance fixtures: validate anonymous/no-save, email-only, registration, returning-user change, new need, unchanged-status, unavailable source, conflicting eligibility, and repeated plan revision without duplicated actions. These are required tests, not claims of passing tests.

OPEN GATE D — Security and retention: session expiry/deletion, verified email, access controls, account recovery, consent for saving and one-time email delivery, data deletion, and protection of sensitive Case text need a concrete implementation contract.

OPEN GATE C — Verified KB: confirm evidence freshness, conflicting-source handling, program availability versus preliminary eligibility, external source verification and safe failure when evidence is unavailable. Program rules require source-by-source validation before production.

OPEN GATE B — Orchestrator call graph and contracts: reconcile the proposed/frozen field names, agent input/output schemas, tool permissions, retry and fallback rules and exactly which service writes Case State. Existing architecture arrows are conceptual, not executable routing.

OPEN GATE A — Canonical agent registry: verify the diagram, narrative, and numbered agent contracts use the same ten names, ownership and responsibilities. In particular, some sections label Agent 6 as Plan Builder while other prose describes Agent 8 as plan assembly; Bob must not infer ownership from inconsistent aliases. Freeze a single registry before implementation.

Resolved boundary: direct edits of profile and action progress are application operations; AI is available in the dashboard and handles plan-content revision. User-status changes alone do not launch a full agent cycle. Material changes/new requests invoke the already defined Case Reassessment.

Resolved boundary: a one-time emailed plan is available without registration; email delivery must not automatically create an account. An anonymous session is not a durable saved Case. Account-linked persistence begins only with the user’s explicit registration/save choice.

Resolved conflict: earlier Decision 8A required persistence of evaluations of programs never recommended. This requirement is superseded: no rejected-program registry in MVP. Keep user-stated needs and presented plan/recommendations; reassess using current KB rules. Other historical example references to rejected programs should be interpreted as rechecking the need, not retaining every rejected candidate.

Source audited: this consolidated Technical Design, including its architecture diagram, decision register, proposed data contracts and domain scenarios. The Word file is approximately forty pages when rendered, not more than 300 pages. This audit is a consistency review, not an implementation test or independent validation of all external benefit-program rules.

## TECHNICAL AUDIT — 17 October 2026; scope and outstanding implementation gates

Reassessment is one existing user-initiated cycle, not multiple new features: reported changed circumstances, new needs, or a request to revise recommendations invokes Case Reassessment. Reuse all existing Case context, ask only necessary clarifications, check affected previously stated needs against current KB information, and update the SAME plan without restarting intake or erasing user-entered statuses. No automatic calendar, deadline reminder or background re-evaluation.

The registered dashboard always offers access to the AI Navigator. The user may view the plan and edit their profile and action-progress statuses directly. Revising the plan content, resource recommendations or structure goes through the existing AI/Orchestrator workflow, using the saved Case. User progress statuses remain user-controlled and cannot be silently changed by AI.

Registration creates a unique user_id. The continuing Case has a case_id linked to that user_id in SQL-backed storage; the living Action Plan belongs to the same Case. Persist relevant user-provided facts, needs, interaction context, the plan, recommendations actually shown, and manually selected progress statuses. Do not introduce separate stores for user circumstances or all unmatched programs. Exact physical SQL schema is not yet approved.

Anonymous intake and initial plan require no account. After seeing the plan, the user may (a) register with verified email to persist the entire relevant user-provided Case and living plan, (b) request a one-time emailed copy without registration, after a privacy warning, or (c) end the session without persistent storage; temporary session data is discarded. One-time email delivery never creates an account or marketing subscription.

## APPROVED DECISIONS 8B–9 — Account-linked Case and AI-connected dashboard

# AUTHORITATIVE DECISION REGISTER — approved cross-domain rules (17 October 2026)

This register reconciles later decisions with earlier proposals. If an earlier example, template, addendum or agent instruction conflicts with these approved rules, apply this register and flag the conflict for contract reconciliation rather than silently guessing. This document remains a working technical design; source-dependent program facts and unresolved interfaces are not automatically approved.

## A. No cap on stated needs or plan actions

Address every user-stated need in one Case State and integrated Action Plan. Prioritize according to user preferences, independently verified deadlines, dependencies and feasibility, but never impose an arbitrary maximum of three actions or silently drop a need. Parallel work is permitted where sensible. A need remains visible when no supported referral is currently found.

## B. Candidate discovery versus exclusion — strict matching

Retrieve broadly enough to find relevant categories, then compare each program against its documented, effective eligibility criteria and the user facts on the same basis (income unit and period, program-defined household, age, geography, countable assets and exceptions). If a known, applicable, mandatory criterion clearly contradicts a sufficiently reliable user fact, classify confirmed_mismatch with criterion/fact references and omit that program from recommended Action Cards. This is not an official agency denial. If a decisive fact, exception or rule is unknown, do not reject: retain as potential_match or insufficient_information and seek only a targeted clarification or recommend provider confirmation. A person’s high income or ownership of property is NOT a universal exclusion across all categories.

## C. Income, expenses, assets — do not conflate

For CalFresh, Medi-Cal and all other programs, apply only the actual published program-specific income definitions, deductions, household rules, and any asset/resource tests. Do not treat ordinary debts, high living costs or a user-reported financial shortfall as automatic eligibility offsets; do not assert that expenses never matter to any program. Likewise, owning property does not always exclude a person; determine whether a resource test exists, which assets count, and applicable exceptions. Do not request an inventory of assets or expenses during initial intake. All thresholds and rule effective dates belong in the Verified Knowledge Base, not invented in agent prompts.

## D. Eligibility, evidence and intake availability are separate

Keep independent fields for preliminary match, verified program-rule evidence, and observed/published intake or funding status. A program can exist and potentially fit a user while currently closed, waitlisted or of unknown availability. When closed, do not present it as immediately actionable funding; identify its status and any verified reopening/contact route, and search parallel alternatives. When unknown, show a contact-to-confirm step, not a guarantee. The provider or government agency makes the final eligibility, funding and service decision.

## E. No results is a search state, not a judgment about help

If a particular search produces no usable match, broaden authorized discovery to relevant official, nonprofit, faith-based and community sources, and disclose the limits of coverage. Do not invent programs and do not claim that no assistance exists. Preserve the user need as unresolved with a concrete follow-up or referral-check action where supported.

## F. User-led intake and conditional fact collection

Agent 1 recognizes only volunteered needs, including anticipated difficulties. Agent 2 asks the smallest set of questions necessary to distinguish relevant programs and practical actions; reuse confirmed Case State facts. The previously approved limited food-sufficiency check after a financial/income crisis remains the narrow exception; do not expand it into a generic list of medical, debt, insurance, transport, housing or material needs. Age, insurance, assets, bill deadlines, notices and personal relationships are asked only when a relevant need or documented rule requires them.

## G. Distinct safeguards for legal, medical, crowdfunding and peer listings

Debt: provide navigation, general verified process information, factual creditor communications and legal-aid referral, not legal representation or guaranteed debt relief. Medical: do not collect diagnoses/medical histories for initial matching, and direct clearly disclosed emergencies to emergency services rather than delay for aid screening. Crowdfunding: INFORMATION AND SELF-SERVICE INSTRUCTIONS ONLY — never draft or edit appeal text, publish or administer a campaign, certify hardship or honesty, or handle funds. Material goods: distinguish verified charity programs from unverified peer listings; MVP does not scrape or monitor Facebook Marketplace, Craigslist or Nextdoor.

## H. Source of truth and build gate

The behavioral rules above and the approved scenario boundaries in sections 16–28 are approved. Earlier proposed data shapes, frozen-field declarations, example payloads and external integrations must be reconciled into one canonical contract before implementation. In particular, verify that all named fields, enum values, agent numbers, and permissions agree; unresolved contradictions are not developer discretion. Knowledge Base entries require dated source evidence; this document is not a substitute for current Sacramento program verification.

TECHNICAL DESIGN & AGENT DATA CONTRACTS · reviewed v0.3

AI Community Aid Navigator \| Sacramento Pilot \| Working technical appendix · 17 October 2026

Status: WORKING / PARTIALLY PROPOSED. This is an implementation-planning companion to Solution Blueprint v1.1 and RAG Technical Architecture. Not a claim of completed code, approved database schema or IBM tool feasibility.

# 1. Design goals and source of truth

Preserve ten existing logical agents and one Orchestrator. Agents return structured proposals/results; only authorized state operations commit data.

Case State owns user case facts, needs, preferences and progress; Verified Knowledge Base owns program claims and source evidence; Action Plan owns versioned action structure. No unnecessary user PII.

Distinguish missing information, conflicting claims, preliminary matching, source verification and live program availability.

# 2. Agent access and responsibility matrix — Proposed v0.1

| Agent                  | Reads                                       | Returns / proposes            | Write boundary                   |
|------------------------|---------------------------------------------|-------------------------------|----------------------------------|
| 1 Crisis Understanding | Story                                       | Proposed needs                | No direct commit                 |
| 2 Clarification        | Needs, facts, answers                       | Questions, facts, urgency     | User confirmation required       |
| 3 Retrieval            | Minimum case context, KB                    | Candidate program refs        | No direct KB/case write          |
| 4 Matching             | Needs, facts, candidates                    | Preliminary matches           | No eligibility determination     |
| 5 Verification         | Program claims and sources                  | Evidence/check results        | KB update via controlled process |
| 6 Prioritization       | Needs, urgency, user preferences, resources | Action order, dependencies    | Proposed plan ordering           |
| 7 Quality              | Agent results, evidence                     | Issues, contradictions        | Flags through Orchestrator       |
| 8 Plan Builder         | Validated facts, resources, ordering        | Plan and Action Cards         | Version commit via Orchestrator  |
| 9 Navigation           | Plan, user-confirmed progress               | Explanations, update requests | No unilateral completion         |
| 10 Validation          | Plan, facts, evidence                       | PASS/FLAG and issues          | No direct plan rewrite           |

# 3. Case State Contract — Working v0.3

**Top-level:** case_id (required); case_status (required); created_at/updated_at (required); story_ref (nullable); needs\[\], facts\[\], open_questions\[\], resource_refs\[\], progress\[\] (arrays may be empty); plan_ref (nullable); account_ref (nullable).

**Need:** need_id, category, description, confirmation_status, urgency, user_priority (nullable), deadline (nullable, with type/source), updated_at. Proposed urgency: immediate/high/normal/unknown; record urgency reason for explainability.

**Fact:** fact_id, field, value, confirmation_status, source, updated_at; proposed/confirmed/disputed/superseded. Preserve significant changes.

**Open question:** question_id, related_need_id (nullable), question, reason, status, answer_ref (nullable); proposed statuses pending/answered/skipped.

**Case stages — PROPOSED:** collecting_information; finding_verifying_resources; building_validating_plan; plan_active. Technical retry/wait states are separate.

**Confirmation:** User confirms concise situation summary or corrects it; no forced fact-by-fact form.

Change rule: a meaningful user-reported change, new need or request for plan revision triggers the already approved Case Reassessment cycle; routine login, plan viewing and progress-status edits do not trigger full reassessment.

# 4. Resource & Evidence Contract — Decisions and open schema

**Program record:** program_id, program_name, organization, category, geography, eligibility_criteria, required_documents, application_method, contact, deadlines, processing_time, availability, sources, last_verified_at, verification_status. Detailed types/cardinality PENDING.

**Preliminary match statuses — APPROVED:** potential_match; supported_match; confirmed_mismatch; insufficient_information.

**Important separation:** eligibility_match_status is not verification_status, and neither proves current availability. Confirmed mismatch applies to a known criterion, not a blanket official ineligibility ruling.

**Missing income:** Do not block the whole plan; show relevant verified program as a potential option, state what remains unassessed, and recommend direct provider confirmation.

**Evidence:** Material claims need source, checked-at and status; preserve conflicting values and claim-specific authority. KB changes only via verification/update process.

**Pending:** Typed program fields, source record schema, validation and retrieval-to-match payload.

# 5. Shared agent result envelope — Proposed, not frozen

Proposed minimum: request_id, case_id, agent_id, schema_version, status, result, issues, generated_at. Fields and enumerations require contract-level validation.

Each agent task uses a specific result schema inside result; do not force a fixed number of arbitrary contracts.

Orchestrator validates structure before routing; rejects malformed required fields or requests repair, rather than silently fabricating values.

# 6. Agent input/output contract worklist

| Order | Contract / data product                                                   | Status  |
|-------|---------------------------------------------------------------------------|---------|
| 1     | Agents 3/4/5: candidate programs → preliminary match → field verification | NEXT    |
| 2     | Agents 1/2: proposed needs/facts and clarification results                | PENDING |
| 3     | Agent 6: urgency + preferences → prioritized action sequence              | PENDING |
| 4     | Agent 8: plan / Action Cards schema and versioning                        | PENDING |
| 5     | Agents 7/10: issue report and PASS/FLAG                                   | PENDING |
| 6     | Agent 9: user-confirmed progress updates                                  | PENDING |
| 7     | Orchestrator: routing, retries, controlled writes, error codes            | PENDING |

# 7. Error handling, tracing and quality

Bounded retries; alternate supported route; transparent partial results or clarification/escalation. No invented eligibility or missing evidence.

Use Orchestrator execution records plus Agent 7 and Agent 10 findings to trace test-stage failures; no additional QA agent.

Feedback / Report an Issue is optional and unobtrusive; reports are triaged, program claims verified before KB changes.

MVP tests: 5–7 initial synthetic cases, expected/actual PASS/FAIL, source spot checks, conflicts/unknowns, source failure, changed circumstances, missing income, privacy, safety and practical response times.

# 8. Implementation agenda and decision log

NEXT: freeze typed inputs/outputs for Agents 3, 4, 5, including unknowns, source refs and all four matching statuses.

THEN: specify common envelope, Case State validations, Orchestrator transitions/authorized persistence, Action Cards and plan versions.

THEN: prepare integration scenarios and lightweight acceptance tests; compare with watsonx Orchestrate and IBM Build with Bob capabilities; revise technical choices based on feasibility.

APPROVED: 10 logical roles, four preliminary matching statuses, nonblocking missing user income, distinct urgency/user preference/action ordering, user-confirmed progress.

PROPOSED: specific JSON fields, case stage enums, envelope and question statuses; pending technical review.

PENDING: database stack, API definitions, error taxonomy, cache/verification intervals, deployment mapping and owner assignments.

# Decision Addendum — Proposal \#6: Plan Release Validation

Decision date: 17 October 2026 \| Status: APPROVED WITH MODIFICATIONS \| Owner: Project Lead \| Scope: Plan release and uncertainty representation

Decision: The validator blocks unsupported or misleading claims, not entire potentially useful recommendations solely because user eligibility information or a particular program field is unknown or conflicting. It does not make official eligibility determinations.

## Release validation contract — implementation requirements

- Input: draft plan and Action Cards, linked Case State facts/needs, preliminary Resource Matching status, program claim-level evidence and verification statuses, availability metadata, and material Agent 7 findings.

- PASS: claims are supported or explicitly qualified; eligibility is described only as preliminary; unknown/conflicting fields are visible; action-blocking uncertainties have a clear verification action; no unsupported guarantees appear.

- FLAG: unsupported guarantee or factual claim; unknown/conflicting field presented as confirmed; confirmed mismatch described as a supported match; unverified program presented as verified/current; critical deadline/contact ambiguity hidden or buried.

- FLAG output identifies the specific claim/card, reason, supporting reference or missing evidence, severity and required correction. Orchestrator routes targeted repair and repeats review within bounded attempts; do not silently delete all recommendations.

- If a disputed deadline or essential contact cannot be resolved, preserve a clearly qualified option where safe, with explicit provider confirmation before acting. If safe wording/action is impossible, withhold the unsafe claim/action and offer a transparent partial plan.

- User eligibility uncertainty and program-source uncertainty must be represented independently. Resource Matching enum: potential_match, supported_match, confirmed_mismatch, insufficient_information. Final provider decision is outside Navigator scope.

- Regression tests: missing income, conflicting deadlines, confirmed mismatch, missing program existence evidence, unsupported approval guarantee, and a mixed plan where one FLAG must not suppress unrelated valid actions.

Change control: Proposal \#6 moved from PENDING to APPROVED WITH MODIFICATIONS. Detailed field schemas, severity thresholds, retry counts and implementation mapping remain PROPOSED/PENDING until technical review.

# 9. Detailed data contracts — working specification

This section consolidates previously discussed requirements into the existing Technical Design. Field names and exact data types below are proposed implementation interfaces unless explicitly marked APPROVED; they must be validated with the team and IBM tooling before code generation.

## 9.1 Case State Contract v0.3 — consolidated

- Root: case_id, case_status, created_at, updated_at required; story_ref and account_ref nullable; needs\[\], facts\[\], open_questions\[\], resource_refs\[\], progress\[\] default empty; plan_ref nullable. Original story kept separately where consent/storage allows.

- Need: need_id, category, description, confirmation_status, urgency \[immediate\|high\|normal\|unknown\], urgency_reason, user_priority nullable, deadline nullable (date, time_type, origin/source), updated_at. User priority is NOT identical to inferred urgency.

- Fact: fact_id, field, value, confirmation_status \[proposed\|confirmed\|disputed\|superseded\], source \[user\|story\|agent_proposal or other defined provenance\], updated_at; preserve material change history.

- Open question: question_id, related_need_id nullable, question, reason, status \[pending\|answered\|skipped\] (PROPOSED), answer_ref nullable. Do not gate the whole plan on nonessential unknowns.

- Case stages \[collecting_information\|finding_verifying_resources\|building_validating_plan\|plan_active\] PROPOSED. Retry/wait/error is a separate execution dimension, not a user-case stage.

- Progress: action_card_id, user_selected_status \[Not Started\|In Progress\|Waiting\|Completed\|Need Help\], updated_at, actor=user. Agent 9 may request an update but must never infer completion or silently write it.

- Update policy: concise user summary confirmation; confirmed material fact/need change triggers affected matching/prioritization/card reevaluation; progress-only change does not trigger full replanning.

## 9.2 Verified Knowledge Base — Program and Evidence records

- ProgramRecord (one per specific program/service): program_id, program_name, organization_name, assistance_category, description, geographic_coverage, eligibility_criteria, exclusions, required_documents, application_process, application_channels, contacts, official_website, operating_hours, official_deadlines, estimated_processing_time, availability_status, source_refs\[\], last_reviewed_at. Names/types/cardinality PROPOSED; categories APPROVED.

- AvailabilityStatus is independent: confirmed_open \| temporarily_closed \| unknown (published status only; not proof of funding or intake capacity). Do not infer closed from a failed web request.

- EvidenceRecord (claim-level, PROPOSED schema): evidence_id, program_id, field_path, claim_value, source_url, source_title, source_authority_scope, effective_date nullable, checked_at, verification_status, notes. Retain competing EvidenceRecords for material conflicting values rather than overwriting silently.

- Claim verification status: verified \| needs_review \| conflicting \| unverified (as specified in RAG Technical Architecture). Unknown means no published value, not a contradictory claim. A reachable webpage does not verify every field.

- Authority by claim: governing agency for governing rules; local provider for local operating/intake facts; 211 directories for discovery/supporting context; community reports as leads only.

- Knowledge updates: controlled verification/update process only; material changes should retain provenance/history. User feedback is triaged as a lead. Full-document/chunk storage, embedding stack, ranking, caching and retry timings remain OPEN.

- Example relationship: ProgramRecord(program_id) -\> EvidenceRecord(program_id, field_path) -\> source; Agent 3 returns candidate program references, Agent 4 assigns preliminary fit, Agent 5 returns field-specific checks.

## 9.3 Resource matching and prioritization

- Match status \[potential_match\|supported_match\|confirmed_mismatch\|insufficient_information\] APPROVED; separate from EvidenceRecord.verification_status and ProgramRecord.availability_status. Never present preliminary fit as official eligibility.

- For missing income or other unknown user facts, use a qualified potential option and a targeted verification/clarification action when appropriate. A confirmed mismatch must point to a specific known requirement.

- Priority inputs are distinct: need urgency, user priority, verified official deadline, dependency constraints, parallelizable steps, and uncertainty. Agent 6 proposes order and reasons; no numerical ranking formula is approved.

- Time fields remain distinct: official_deadline (source-backed), user_target_date (user-set), estimated_processing_time (non-guaranteed). Do not merge into one deadline.

## 9.4 Proposed Agents 3 → 4 → 5 interface slice

- Agent 3 INPUT: minimum confirmed/proposed case needs, geography and retrieval constraints. OUTPUT: candidate_programs\[\] containing program_id, matched_need_ids\[\], retrieval_reason, source_refs\[\], missing_fields\[\]; no eligibility claims or direct KB write.

- Agent 4 INPUT: candidate_programs\[\], relevant confirmed/unknown Case State facts and program criteria. OUTPUT: matches\[\] containing program_id, need_ids\[\], match_status (four approved values), supporting_fact_refs\[\], unmet_criteria\[\], unknown_criteria\[\], rationale. No official eligibility decision.

- Agent 5 INPUT: selected program IDs, material field paths, EvidenceRecords, case-relevant constraints. OUTPUT: checked_claims\[\] with field_path, claimed_value, verification_status, evidence_refs\[\], checked_at, discrepancy and follow_up; optional program availability observations kept separate.

- Orchestrator controls routing and writes; Agents 7 and 10 inspect uncertainty and unsupported claims. Shared envelope fields request_id, case_id, agent_id, schema_version, status, result, issues, generated_at remain PROPOSED.

## 9.5 Action Cards, validation, feedback and acceptance tests

- Action Card minimum content (PROPOSED): card_id, plan_version, related_need_ids\[\], program_id nullable, action_title, reason, next_step, priority_reason, dependency_card_ids\[\], source_refs\[\], uncertainty_notes\[\], official_deadline nullable, user_target_date nullable, processing_estimate nullable, progress_status. Exact typed schema remains OPEN.

- Agent 10 release check (APPROVED WITH MODIFICATIONS): PASS if claims are supported or clearly qualified and blocking unknowns lead to explicit checks; FLAG unsupported guarantees, false verified/current claims, buried critical conflict or known mismatch mislabeled as match. Return card/claim ID, reason, severity, evidence gap and correction request; do not discard unrelated valid cards.

- Feedback (APPROVED): unobtrusive optional Feedback / Report an Issue button; categorize program information error vs product issue; route material claim changes through verification, not direct KB edit.

- Error trace (APPROVED): capture stage, case_id/request_id, agent/tool, failure category, attempt and outcome through existing Orchestrator + Agent 7/10; avoid unnecessary PII in logs. Exact error taxonomy and retention are PENDING.

- Acceptance tests (PARTIALLY APPROVED): start with ~5–7 synthetic cases; expected/actual and PASS/FAIL with retest. Include no income data, conflicting official deadline, inaccessible source, confirmed mismatch, material user change, mixed PASS/FLAG plan, privacy and safety. 5–7 is not a hard limit.

# 10. Change log and decision boundaries

- Consolidation: retained existing Technical Design v0.2 sections 1–8 and the Slava Proposal \#6 addendum; appended working detail rather than creating a competing technical specification.

- Approved: 10 logical roles; user-controlled progress; hybrid retrieval and claim-level evidence; four match statuses; separate urgency/user priority/deadline/order; nonblocking unknown income; Hisham optional feedback and error trace; Slava validator with modifications.

- Proposed/not yet frozen: concrete JSON property names, stage/status enumerations beyond approved lists, Agent 3/4/5 payload shape, Action Card typed schema, logging fields.

- Open: IBM Orchestrate/Bob capabilities, deployment/storage/indexing, source refresh parameters, schema validation details, access/privacy retention rules and production service availability.

# 11. Frozen MVP field names and typed interfaces — 17 October 2026

Decision: use the canonical snake_case names below for new implementation. Earlier prose aliases (organization_name, assistance_category, geographic_coverage, last_reviewed_at) are deprecated; they must be mapped to organization, category, geography, last_verified_at when migrating records. This section supersedes inconsistent names in section 9.2; it does not replace the agreed RAG architecture. Approved product rules remain separate from proposed integration mechanics.

## 11.1 ProgramRecord — canonical schema

| Field                | Type / requirement                                          |
|----------------------|-------------------------------------------------------------|
| program_id           | string, required, stable unique identifier                  |
| program_name         | string, required                                            |
| organization         | string, required                                            |
| category             | string, required, controlled taxonomy TBD                   |
| geography            | array of strings, required; explicit service areas          |
| eligibility_criteria | array of claim objects, may be empty                        |
| required_documents   | array of claim objects, may be empty                        |
| application_method   | array of claim objects, may be empty                        |
| contact              | array of claim objects, may be empty                        |
| deadlines            | array of claim objects, may be empty                        |
| processing_time      | claim object or null                                        |
| availability         | enum: confirmed_open \| temporarily_closed \| unknown       |
| sources              | array of evidence_id strings; may be empty                  |
| last_verified_at     | ISO 8601 datetime or null                                   |
| verification_status  | enum: verified \| needs_review \| conflicting \| unverified |

Claim object (for fields containing independently verifiable assertions): value (string), evidence_refs\[\] (string IDs), verification_status (same enum), checked_at (ISO datetime or null). Missing published facts use null or empty arrays, never fabricated values. Program-level verification_status is a summary indicator, not a substitute for field-level evidence. A verified program is not necessarily accepting applications.

## 11.2 EvidenceRecord — typed MVP contract

Required: evidence_id:string; program_id:string; field_path:string; claim_value:string; source_url:string; checked_at:ISO datetime; verification_status:verified\|needs_review\|conflicting\|unverified. Optional/nullable: source_title:string; source_authority_scope:string; effective_date:ISO date; notes:string. Conflicting claims remain separate EvidenceRecords, not overwritten. Only Knowledge Update Process may persist changes to ProgramRecord/EvidenceRecord after validation.

## 11.3 Shared agent envelope

Every agent call INPUT: request_id:string, case_id:string, schema_version:string, payload:object. Every OUTPUT: request_id:string, case_id:string, agent_id:string, schema_version:string, status:success\|partial\|needs_clarification\|error, result:object, issues:array, generated_at:ISO datetime. issues\[\] item: code:string, severity:info\|warning\|critical, message:string, related_ref:string\|null. Orchestrator validates schema and case/request identity before routing; it alone authorizes writes. These transport status values are an implementation decision, not eligibility statuses.

## 11.4 Agent 3 — Resource Retrieval

INPUT payload: needs\[\] {need_id:string, category:string, description:string, urgency:immediate\|high\|normal\|unknown}; geography\[\]:string; retrieval_constraints\[\]:string; max_candidates:integer (optional). Unknown user facts may be omitted; do not require income to retrieve candidates.

OUTPUT result: candidate_programs\[\] {program_id:string, matched_need_ids\[\]:string, retrieval_reason:string, source_refs\[\]:string, missing_fields\[\]:string}; retrieval_notes\[\]:string. Agent 3 returns candidate references only, not eligibility conclusions or direct KB edits. Empty results are valid and must not trigger invented programs.

## 11.5 Agent 4 — Resource Matching

INPUT payload: candidate_programs\[\] (Agent 3 result); case_facts\[\] {field:string, value:any\|null, confirmation_status:proposed\|confirmed\|disputed\|superseded}; needs\[\]; program_criteria\[\] {program_id:string, field_path:string, value:string\|null, evidence_refs\[\]:string}.

OUTPUT result: matches\[\] {program_id:string, need_ids\[\]:string, match_status:potential_match\|supported_match\|confirmed_mismatch\|insufficient_information, matched_criteria\[\]:string, missing_case_facts\[\]:string, mismatch_criteria\[\]:string, evidence_refs\[\]:string, explanation:string}. confirmed_mismatch must identify the specific criterion and confirmed contradictory fact. Unknown income is not a mismatch. Matching is preliminary, not an official eligibility decision.

## 11.6 Agent 5 — Resource Verification

INPUT payload: programs_to_check\[\] {program_id:string, field_paths\[\]:string}; evidence_refs\[\]:string; relevant_case_constraints\[\]:string. OUTPUT result: checked_claims\[\] {program_id:string, field_path:string, claim_value:string\|null, verification_status:verified\|needs_review\|conflicting\|unverified, evidence_refs\[\]:string, checked_at:ISO datetime\|null, issue:string\|null}; update_proposals\[\] {program_id:string, field_path:string, proposed_value:any, evidence_refs\[\]:string, reason:string}; unresolved_questions\[\]:string. A failed website check is not proof of closure. Agent 5 cannot directly update KB; proposals route to Knowledge Update Process.

## 11.7 Orchestrator handoff to Agents 6 and 8

After 3→4→5, Orchestrator packages case_id, confirmed/proposed needs, candidate_programs, matches, checked_claims, evidence references, urgency, user_priority, official_deadline, user_target_date, estimated_processing_time and issues. Agent 6 proposes prioritized steps with explicit dependency and uncertainty reasons. Agent 8 produces source-linked Action Cards; unknowns and conflicts remain visible. Agent 7 reviews uncertainty; Agent 10 PASS/FLAG checks unsupported claims. Neither agent may convert potential_match into guaranteed eligibility.

## 11.8 Validation and example boundary tests

- Reject unknown match_status, verification_status or availability enum values; reject references to missing program_id or need_id.

- Missing income: Agent 3 may retrieve, Agent 4 may return potential_match/insufficient_information, and plan includes an explicit provider-check action.

- Confirmed mismatch: include a criterion reference; never state globally ineligible.

- Conflicting deadline: preserve both evidence records and flag the card for direct confirmation; never silently choose a date.

- Source unavailable: report check failure and uncertainty; do not mark temporarily_closed.

- Feedback: record issue and route to verification; no direct write to program claims.

Remaining implementation choices (not silently approved): controlled category taxonomy, source access strategy, persistence technology, exact API transport, numeric ranking, retry thresholds, cache durations and IBM Bob/Orchestrate deployment mapping. These do not block the frozen field names and MVP payload structures.

# 12. Agent build instructions and tool boundaries — Agents 3, 4, 5

Status: WORKING IMPLEMENTATION SPECIFICATION. These instructions operationalize the frozen names and approved decision boundaries in section 11. Tool names below are logical interfaces, not claims that IBM watsonx Orchestrate already exposes them. Map them to actual IBM tools after access is restored. No new agent roles are introduced.

## 12.1 Shared execution rules

• Only the Orchestrator dispatches agents, validates their envelopes, and authorizes writes. Agent outputs are proposals, not persisted state.

• Use the section 11 envelope and canonical program_id, program_name, organization, category, geography, eligibility_criteria, required_documents, application_method, contact, deadlines, processing_time, availability, sources, last_verified_at, verification_status names.

• Preserve unknown, conflicting, and unavailable-source states without guessing. Keep preliminary match, claim verification, and published availability independent.

• Return explicit issues and evidence references; never claim live funding, eligibility approval, application submission, or guaranteed processing times.

• Minimize case data shared with tools. No SSN, bank/card details, or raw story text in retrieval or verification calls.

## 12.2 Agent 3 — Resource Retrieval

Purpose: retrieve candidate Sacramento assistance programs that may address stated needs; do not decide user eligibility, verify live availability, or write the Knowledge Base.

Inputs: section 11.4 payload (needs\[\], geography\[\], retrieval_constraints\[\], max_candidates). Orchestrator may include confirmed and proposed needs with confirmation markers; use proposed needs only as tentative search context. Do not require income or other missing case facts to start retrieval.

Logical tool: search_verified_kb({needs, geography, retrieval_constraints, max_candidates}) → program IDs, need links, stored source references and search metadata. Implementation must combine structured geography/category filters with semantic retrieval as agreed in RAG architecture.

Agent instruction (paste-ready):

> You are Agent 3, Resource Retrieval. Retrieve candidate program records from the Verified Knowledge Base for the supplied needs and geography. Use the authorized Knowledge Base retrieval tool first; when Orchestrator authorizes external discovery, use only the approved public-source discovery tool and route findings for verification; never invent program IDs, program details, source URLs, eligibility or availability. Use structured filters and semantic relevance together. Missing user income or other facts must not stop discovery. Return candidate_programs with program_id, matched_need_ids, retrieval_reason, source_refs, missing_fields; return retrieval_notes and issues for gaps, empty results or tool failures. Do not label a user eligible, rank by urgency, edit case state or update the KB. Return the agreed structured envelope only.

Output: section 11.4 result. A candidate with missing or disputed fields can remain in the candidate list with missing_fields and linked source refs. If no candidates, return an empty array plus retrieval_notes; do not fabricate a fallback program.

## 12.3 Agent 4 — Resource Matching

Purpose: preliminary fit against known program criteria and known Case State facts; never make an official eligibility decision.

Inputs: section 11.5 payload (candidate_programs\[\], case_facts\[\], needs\[\], program_criteria\[\]). Compare only criteria tied to the same program_id; confirmed user facts take precedence over proposed or disputed facts.

Logical tool: read_program_criteria({program_ids}) → criteria with field-level evidence references and current verification metadata. May be supplied by Orchestrator rather than directly invoked.

Agent instruction (paste-ready):

> You are Agent 4, Resource Matching. Compare each retrieved program against known user needs and facts using only supplied criteria and referenced program records. Assign exactly one of: potential_match, supported_match, confirmed_mismatch, insufficient_information. supported_match requires affirmative support for the evaluated published criteria, not official eligibility. confirmed_mismatch requires a specific criterion and a confirmed contradictory user fact; never declare the person globally ineligible. If income or other material facts are unknown, use potential_match or insufficient_information with missing_criteria and a targeted follow-up; do not reject the program merely for missing data. Keep source verification and availability separate. Return matches with evidence/criterion references and explanatory limitations; do not update Case State or KB.

Output: section 11.5 matches\[\] with program_id, need_ids, match_status, matched_criteria, missing_criteria, mismatch_criteria and explanatory issues. A confirmed mismatch must include the criterion reference and fact reference. No automatic removal of uncertain options from downstream planning.

## 12.4 Agent 5 — Resource Verification

Purpose: check material published program claims, source authority and freshness, and identify unknown or conflicting evidence. It is not an eligibility assessor or live funding oracle.

Inputs: section 11.6 payload (programs_to_check\[\], evidence_refs\[\], relevant_case_constraints\[\]). Check relevant claims only, not a mandatory full daily crawl.

Logical tools: get_evidence_records({program_id, field_paths}); fetch_authoritative_source({source_url}); submit_kb_update_proposal({program_id, field_path, proposed_value, evidence_refs, reason}). The last tool submits for controlled review only and MUST NOT directly write to KB.

Agent instruction (paste-ready):

> You are Agent 5, Resource Verification. For requested program claims, compare stored evidence with accessible authoritative sources and preserve source URL, checked_at, field_path, claim_value and verification_status. Judge authority per claim: governing agency for governing rules, local provider for local intake details, directories as secondary discovery evidence. Mark unresolved incompatible values conflicting; missing published values unknown in the program field; failed retrieval is a check failure, never evidence of closure. Do not silently select between conflicting deadlines. Do not claim real-time funding or approval. Return checked_claims, issues and update_proposals with supporting evidence. Never modify Verified Knowledge Base directly. Send proposed changes only through the controlled Knowledge Update Process.

Output: section 11.6 checked_claims\[\] and update_proposals\[\]. Preserve both sides of a conflict with evidence references. Failed checks must carry failure type and last known verification context.

## 12.5 Orchestrator handoff and safety checks

• Run 3 → 4 → 5 for the relevant candidate set; Agent 7 may flag uncertainty at each stage. Agent 6 receives urgency, user_priority, verified official deadlines, dependencies and qualified matches. Agent 8 receives source-linked, qualified options to build Action Cards.

• Validate request_id, case_id, schema_version, agent_id and required result arrays before routing. Reject invented IDs and unsupported status values; log stage and reason without sensitive raw user details.

• If source checking fails, preserve qualified stored evidence and expose its age/uncertainty; do not turn availability into temporarily_closed.

• Agent 10 checks the assembled plan for unsupported claims and returns PASS/FLAG for targeted repair, not blanket suppression of useful qualified options.

## 12.6 Contract acceptance fixtures

• Missing income: retrieval returns a relevant candidate; matching marks uncertainty; verification checks published criteria; plan requests provider confirmation.

• Confirmed geographic mismatch: matching returns confirmed_mismatch with a specific supported rule and confirmed location fact.

• Conflicting official deadline: verification returns conflicting with both sources; Action Card flags confirmation before relying on a date.

• Provider website inaccessible: verification records failed check; program is not labeled closed.

• No usable candidate in the current search: return \[\] and a transparent coverage gap; request authorized broader source discovery or direct provider verification. This is a search limitation, never evidence that assistance does not exist. Do not fabricate referrals.

Implementation note: exact API names, transport, persistence, and JSON Schema validation remain dependent on IBM tool capabilities; the agent behaviors and canonical field names above are the current design baseline.

# 13. Approved search fallback and prioritization workflow

Decision status: APPROVED product behavior (17 October 2026). This section supersedes any earlier Agent 3 instruction limiting discovery to the Knowledge Base only. Tool names and deployment mechanics remain implementation choices.

## 13.1 Two distinct priority systems

Source-discovery order is distinct from case-action priority. Source discovery determines where to look for evidence; Agent 6 action priority determines which steps a person should take first. Neither priority is a claim of eligibility or guaranteed assistance.

## 13.2 Resource discovery and controlled external fallback

1.  Agent 3 first searches the Verified Knowledge Base using case needs, geography and applicable constraints. An unknown income or other missing fact must not suppress otherwise relevant candidates.

2.  Agent 3 reports coverage gaps as well as zero results. The Orchestrator may authorize an expanded public-source discovery pass when no candidates are found or when one or more confirmed needs are inadequately covered. “Not found in our Knowledge Base” must never be represented as “no assistance exists.”

3.  Expanded discovery starts with relevant official government sources (federal, California, county, municipal). It then examines direct official provider/operator sources, including nonprofit, educational and charitable organizations. Directories such as 211 and community listings are discovery leads; they are not proof of eligibility or live availability.

4.  Source authority is claim-specific, not an absolute website ranking: governing agencies are authoritative for their program rules, while a local provider may be authoritative for local intake hours, procedures and availability. Compare effective dates, jurisdiction and program scope.

5.  External findings remain discovery candidates, clearly distinguished from Verified Knowledge Base records. Agent 5 checks relevant claims and records evidence and unresolved uncertainty. Agent 7 flags unsupported or conflicting claims. Agents do not directly write to the Verified Knowledge Base.

6.  Confirmed changes and new records pass through the controlled Knowledge Update Process with provenance and review; unverified discoveries are not silently promoted to Verified. Where material checks fail, the Orchestrator may return a qualified lead or a “contact provider to confirm” action only when sufficiently supported and safe; otherwise withhold unsupported claims.

7.  If neither pass yields usable candidates, report the limits of the search honestly and offer next verification/referral steps; never invent a program or assert that no help exists.

## 13.3 Source evidence and independent statuses

Keep source verification status, published availability status and user-to-program matching status separate. For material claims, retain field_path, value, source URL, checked_at, authority/scope and verification status. Unknown is not conflicting; an unreachable page is not proof of closure. The four preliminary match statuses remain potential_match, supported_match, confirmed_mismatch and insufficient_information.

## 13.4 User action priority (Agent 6)

Inputs are need urgency (immediate/high/normal/unknown), user_priority (optional), verified official deadline, user target date, estimated processing time, dependencies, parallelizable steps and material uncertainty. These are separate dimensions, not interchangeable scores. Agent 6 produces a reasoned action order and explains deadline risk, prerequisite steps and possible parallel actions. Do not invent a universal numeric weighting formula. Do not confuse a user target with an official deadline or processing estimate. Unknown information should prompt a qualified action, not automatically block the entire plan.

## 13.5 Orchestrator and Agent 3 interface amendment

Agent 3 must return candidates plus coverage_by_need, search_scope (knowledge_base or external_discovery), retrieval_notes and any discovery-only leads. The Orchestrator owns the fallback decision and passes externally discovered leads to Agent 5 for verification before they can be treated as verified KB entries. Exact typed JSON schemas and the public-search tool adapter must be reconciled with section 11 before implementation.

# 14. Approved user-facing wording for preliminary program options

Decision status: APPROVED product behavior (17 October 2026). Applies to Agents 5, 6, 8, 9, 10 and the Orchestrator. This section refines sections 12–13; it does not change the underlying evidence or match-status contracts.

## 14.1 When to display a preliminary option

When no sufficiently supported alternatives are available, or the confirmed options do not adequately cover the user’s needs, a potentially relevant external-discovery candidate may appear as a clearly qualified additional option. At minimum, the program’s existence and an official provider contact or website must be supported by a reliable source. Never label the discovery candidate as a Verified Knowledge Base entry solely because it appears in the plan. Do not claim an active application window, available funding or eligibility without supporting evidence.

## 14.2 User-facing message and explanation

Use constructive, person-centered language. Explain the possible relevance in one short sentence when supported by known program scope and case facts. Do not invent a personalized reason; otherwise use a neutral statement of possible relevance. Avoid framing ordinary missing published information as “we failed to verify.” Be specific about what the provider has not published, but only if the source was actually accessible and checked. If the website was inaccessible, say that current details need confirmation without claiming that the website omits them.

Suggested English Action Card wording (adapt to actual evidence):

“This program may be relevant to your situation because it offers assistance with \[supported need\]. The organization’s published information does not specify \[specific missing condition or current availability, if verified as absent\]. For complete details and to find out whether assistance is currently available to you, please contact the organization directly using its official website or verified contact information.”

Alternative when the reason is not supported: “This program may be worth exploring. Please contact the organization directly to confirm its requirements and whether assistance is currently available for your situation.”

## 14.3 Evidence-specific wording and safeguards

- Published details incomplete: say which relevant condition is not stated, if that absence was actually checked; recommend contacting the provider.

- Source inaccessible or check failed: do not say information is absent from the website; advise direct confirmation and retain the failure reason internally.

- Sources conflict: do not conceal a material contradiction (especially deadlines or closure); explain the conflicting detail plainly and advise authoritative confirmation.

- Confirmed closure, geographic mismatch or unsupported contact: never imply currently available assistance or invent a phone number, URL, or eligibility.

- Internal status codes and technical failure details remain available to audit and validation, while the user sees clear, accurate next steps.

- Agent 6 may elevate a time-sensitive preliminary option when a supported deadline requires prompt confirmation; verification confidence is not a rigid chronological sort.

- Agent 10 flags any Action Card that turns unknown availability into a guarantee, suppresses a material conflict, asserts missing website content without checking, or lacks a grounded next action.

## 14.4 Acceptance scenarios

- Official page lists housing assistance but omits intake status: display potential relevance and ask user to confirm current intake directly.

- Provider page cannot be reached: do not say its information is incomplete; use neutral confirmation wording.

- Two authoritative sources disagree on an application deadline: show the conflict prominently and direct the user to verify before relying on either date. A directory-only lead without a verifiable official provider contact is not presented as a validated contactable option.

# 15. Agent 6 — Action Planning & Prioritization: approved behavioral contract

Decision basis: four synthetic scenarios reviewed on 17 October 2026 (bereaved caregiver with children; sole earner loses employment; family relocating interstate; family member injured in an accident). These are behavioral fixtures, not claims that any named program grants eligibility.

## 15.1 Responsibility and boundaries

- Agent 6 converts verified or appropriately qualified resource matches and Case State needs into a proposed, dependency-aware order of actions. It does not determine eligibility, independently verify program claims, submit applications, or override user decisions.

- Inputs from Orchestrator: case_id; needs and urgency; confirmed/proposed facts and open questions; user_priority (nullable); resource match status; field-level verification and availability status; evidence references; official deadlines; user target dates; estimated processing times; dependencies; access constraints; and proposed action steps.

- An unknown income, immigration-related detail, or missing document must not automatically prevent a useful preliminary plan. Eligibility checks remain the responsibility of Agents 4–5 and the relevant provider; no universal assumptions about program eligibility may be made from tax residency or benefit category.

## 15.2 Ordering rules — approved

- Assess immediate safety and essential needs first when evidenced (urgent health risk, food, safe housing, necessary medicine); route emergencies through existing safety mechanisms, not routine benefit planning.

- Consider verified official deadlines and consequences of delay, not simply the amount of a bill or a fixed ordering of aid categories.

- Account for prerequisites and dependencies; allow independent actions to proceed in parallel.

- Consider published estimated processing time as non-guaranteed and separate it from official deadlines and user-set target dates.

- Consider the user’s own stated priorities, practical capacity, transportation/document constraints, and preferences. Do not invent urgency or deadlines when none is known.

- Provide a short, evidence-based reason for the suggested ordering. Preserve material uncertainty and source references in handoff to Agent 8.

- Do not arbitrarily cap the full plan at three actions; manageable presentation is a UI decision, not deletion of options.

## 15.3 User control — approved

- The user can reorder, defer, or reprioritize suggested actions. Agent 6 recommendations are advisory, not mandatory.

- If a user defers an action with a known critical deadline or consequence, display a calm, specific warning and preserve the user’s chosen order. Do not block the choice.

- User priority and system-suggested urgency are stored as distinct fields; a user change does not silently rewrite a verified official deadline.

- Completion and progress statuses change only on user confirmation; ordinary progress changes do not force a full plan rebuild.

## 15.4 Output contract — working proposal, not yet frozen

Agent 6 returns case_id, proposed_actions\[\] (action_id, need_id, program_id nullable, suggested_priority, rationale, dependency_ids\[\], parallel_group nullable, official_deadline nullable, user_target_date nullable, estimated_processing_time nullable, evidence_refs\[\], uncertainty_notes\[\], user_override_allowed=true), plus issues\[\] and proposed_clarifications\[\]. Exact JSON types/enums and sorting tie-breakers remain to be reviewed before coding.

## 15.5 Acceptance scenarios

- Bereavement: prioritize immediate household needs and relevant deadlines while allowing survivor-benefit, funeral-assistance, and insurance inquiries to run in parallel where independent; do not assume eligibility.

- Job loss: if food and housing are secure for now but a verified application deadline is near, deadline-sensitive action may precede less urgent food assistance.

- Interstate relocation: do not manufacture an emergency; identify possible program transitions and state-specific requirements without equating tax residency with benefit eligibility.

- Accident: emergency medical needs route to safety help; a large medical bill with a later due date does not automatically outrank rent due in two days.

- User override: a caregiver can move funeral arrangements above a recommended benefit application; retain a non-coercive warning if a verified deadline is at risk.

## 15.6 Presentation question — pending

Grouping a long plan as “First / Next / Later” was suggested but not yet approved. Do not treat it as a frozen UI requirement. The user-approved requirement is the ability to review all actions and change their order.

# 16. Agents 1 and 2 — approved intake dialogue principles and open implementation work

Status: conversational behavior approved in design discussion; exact program-specific question bank, schemas and thresholds remain pending. This section does not replace existing Case State or program contracts.

## 16.1 Core distinction — needs discovery versus program suggestion

- Agent 1 extracts what the user actually reports: triggering event, factual circumstances, self-described needs and timing. It must not invent needs or turn hypothetical examples into user-reported needs.

- Begin with open-ended, neutral questions. Do not prompt a checklist such as “Do you need rent, electricity, food, or medical insurance?” A request for “what else can I get?” should be redirected constructively to describing actual circumstances and needs, without suspicion or accusation.

- After the user identifies a need, targeted factual follow-ups are appropriate (e.g., after food insecurity is mentioned: “How many days of food do you currently have?”). Use short, conversational turns rather than a bulk questionnaire.

- Provide a neutral summary of user-reported event, needs, timing and key facts for confirmation or correction. Distinguish reported facts, proposed interpretations and unknowns; never represent an inferred need as confirmed.

## 16.2 Trigger-based clarification — job loss / income disruption fixture

- When the user reports job loss or sharply reduced income, Agent 2 first reuses the existing Case State and asks only what is necessary to understand the stated income disruption and evaluate relevant candidate programs. The date work ended, the most recent pay date and other household income may be asked when pertinent. Available cash and near-term financial runway may be discussed only when needed to prioritize an already stated need or a specific program rule. Do NOT routinely ask about property, vehicles, investments, all assets or every expense; request asset information only where a documented program rule makes it material. An approximate prior or current income is not automatically the program-defined countable income.

- If the user has already named the costs or services they cannot cover, do not repeat the question. If the stated financial difficulty is still too general to identify a service category, ask one open question about what they would like help with. Do not propose a checklist of unrelated needs or force a financial-runway calculation.

- Distinguish historical income, current income, date of change, available funds, and financial runway. Ask for approximate amounts when useful; do not request bank account numbers, SSNs, uploaded tax returns or statements.

- Asset ownership does not automatically disqualify a user. Detailed asset or income-period questions should be tied to the relevant program’s documented rules. Do not require answers to every question before initial resource discovery.

## 16.3 Timing and urgency — approved distinction

- Capture when each stated need will become unmet (e.g., food available through tomorrow) separately from a bill due date, a threatened adverse consequence (e.g., utility shutoff notice), official program deadlines and user preferences.

- A missed utility bill due date does not by itself prove imminent shutoff; ask whether a shutoff notice or specific deadline exists when the user raises that issue. Do not manufacture urgency.

- For each candidate resource, Agents 3–5 should capture verified timing to first possible assistance, processing time, operating hours and whether the resource offers immediate versus ongoing support. Agent 6 compares need-by timing to plausible assistance timing; a food pantry and CalFresh may serve the same need on different timelines.

- Agent 6 determines plan ordering after needs and timing are understood; users may change order. An urgent user-reported safety concern or deadline can be captured during intake without forcing early priority ranking.

## 16.4 Geography, household and conditional program questions

- Sacramento pilot: ask for ZIP code first; clarify county or service area only when ZIP alone cannot establish geographic applicability. Do not request full street address as a default.

- Collect household composition and relevant ages, but program-specific definitions may differ (e.g., CalFresh food household versus all co-residents). Clarify only where needed.

- Insurance questions follow a medical coverage need or a documented program-specific reason. Financial and asset questions follow an income-related trigger or a specific eligibility rule. Program-specific follow-ups may occur after initial retrieval and matching rather than all before search.

- Five research fixtures for designing conditional questions: CalFresh, CalWORKs, Medi-Cal, SMUD EAPR, and SHRA Housing Choice Voucher; also include food pantry/food bank access as a contrasting immediate food resource. These are research examples, not universal eligibility rules or a ranking of popularity.

## 16.5 Open technical decisions and acceptance tests

- Pending: program-by-program requirements matrix, question triggers, skip logic, minimum data required for initial retrieval, fact provenance, question deduplication and the handoff between Agent 1 and Agent 2. Agents may formulate natural-language questions dynamically under these constraints, but must not autonomously invent eligibility criteria.

- Acceptance tests: user says “I lost my job” without naming needs; user reports food shortage until tomorrow; user mentions a late electric bill without shutoff notice; previously high-income household now has no income but some savings; user asks “what other benefits can I get?”; user declines to disclose exact savings; user corrects a mistaken summary.

- Do not turn this section into a mandatory scripted questionnaire. Future implementation should combine a structured field/trigger contract with flexible question wording and verified program requirements.

# 17. Food assistance intake — CalFresh and Sacramento food pantries (approved design)

Status: product/dialogue rules approved by project lead. Program-specific operating details remain subject to source verification at retrieval time. This section extends §16 and does not replace the RAG verification rules.

## 17.1 Distinct assistance paths

- Food need is identified by the user, not inferred from job loss, income level, or a list of suggested benefits. Agent 1 starts with open questions and records only the needs the person actually describes.

- CalFresh is an application-based, potentially ongoing food benefit; expedited CalFresh may be relevant for certain households, but timing and eligibility must be checked against current official criteria. Never promise benefits or a three-day outcome.

- Food banks/pantries can sometimes provide more immediate food access. Each distribution site or distinct program must have its own KB record: address/service area, eligibility, registration/ID rules, hours, food type, pickup requirements, authoritative source and verification date. Do not assume all pantries require no documents.

- Agent 6 compares the user’s need-by time with the verified earliest practical resource-access time. Food pantry access and CalFresh application can be recommended in parallel where appropriate; neither is automatically the top action in every case.

## 17.2 Conversation triggers and minimum questions

- If the user mentions food insecurity: ask neutrally how many days of food they currently have, or when they expect to be unable to cover food needs. Do not ask every user “Do you need food?”

- Ask ZIP code to locate Sacramento-area distribution options; resolve actual county/service-area ambiguity only if necessary. Ask about ability to reach a specific location only after finding that resource.

- If a matched food distribution resource requires food preparation and the user’s situation suggests a possible barrier, clarify whether the person has a place or means to prepare food. Do not ask about a kitchen as a universal intake question.

- For CalFresh preliminary matching, reuse existing case facts about income, date of change, available funds and family composition; request additional information only when it affects a documented rule, including potential expedited handling.

- Household membership is program-specific. Initial question may ask who normally lives as part of the household and the ages of children; do not equate temporary guests with permanent household members. For CalFresh, clarify usual joint food purchasing/preparation when relevant, using natural wording. Do not apply a universal six-month residency threshold.

- Never ask for tax returns, bank statements, SSNs or financial account numbers as a default prerequisite for finding food distribution. Approximate self-reported amounts may suffice for preliminary screening; formal application requirements belong to the provider.

## 17.3 Structured facts and resource timing

- Need record: need_type=food, user_reported=true, reported_food_runway_days (nullable), need_by_date (nullable), household_context_ref, location_zip, evidence_source=user_statement, confidence/confirmation status; do not invent values.

- Resource record: program/site identifier, assistance_mode (distribution/application benefit), official operating schedule, earliest possible access if verified, application processing estimate if published, frequency/duration of help, travel/pickup constraints, required documents, source URLs and last verification time.

- Distinguish food needed today, first possible food distribution date, normal CalFresh processing time and expedited processing conditions. “Listed opening hours” are not a guarantee of same-day food availability.

## 17.4 Tested conversation fixture and expected behavior

Fixture: user reports job loss two weeks ago, no other current household income, two children, food sufficient for only two more days, ZIP 95816, and about \$80 available. Agent 1 captures user-reported needs and timing; Agent 2 asks only unresolved decision-relevant questions; Agents 3–5 find and verify accessible food distribution and possible CalFresh/expedited CalFresh options; Agent 6 prioritizes practical food access against the two-day horizon and may schedule a CalFresh application in parallel. No unsolicited medical, rent or utility needs; no default interrogation about vehicles, real estate, investments or tax documents.

## 17.5 Acceptance criteria

- No leading benefit checklist; the user must identify the food need before food-specific intake.

- No unsupported assumption that all food banks accept everyone without ID, that any specific site has food in stock, or that CalFresh will pay by a guaranteed date.

- No rigid question script: language can vary, but required decision facts and provenance are tracked and already-known answers are not asked again.

- If user has food for three weeks, avoid manufacturing an immediate emergency; if food runs out tomorrow, search practical immediate access before relying solely on benefit application.

- If user cannot travel or prepare food, verify the selected site’s relevant alternatives rather than assuming availability.

- Program/site rules must be rechecked against official operator and county/state sources before live recommendations.

# 18. Housing assistance — approved intake and search scope (17 October 2026)

Status: Approved conversation and scope decisions; Sacramento provider-level eligibility, capacity, and funding remain pending independent verification. This section does not certify any live placement availability.

## 18.1 One housing need, not artificial urgency tracks

- Activate housing assistance when the user reports a housing problem. Begin with an open question about their situation if details are missing; do not present a menu of presumed needs. Do not require the user to choose today/tomorrow/in-three-days or a separate short-term/long-term workflow.

- Use one housing search process. Distinguish keeping existing housing from finding accommodation only when it changes the applicable program or action. If the user reports court or sheriff documents, clarify the document/stage and stated deadline when relevant; do not assume a guaranteed multi-month period or provide legal conclusions.

- Do not ask everyone whether they have a safe place to stay tonight or exactly how long they can remain with friends. Seek specific timing only if it changes a practical action or program requirement.

## 18.2 Reuse shared case and financial facts

- Reuse previously confirmed or user-reported income before the crisis, current income and income sources, and accessible funds. Ask only for missing material details; do not run a second financial interview when food and housing needs coexist.

- For housing fit, clarify who needs accommodation and the ages of children when relevant. Do not assume that the word “children” means minors or that a single universal household definition applies across programs.

- Available budget for temporary accommodation and current recurring income are different facts. Assets, rental-property income, housing costs and other expense categories are asked only where relevant to an identified need, program eligibility, or practical plan; do not infer blanket disqualification from owning property.

- Do not solicit a generic list of loans, credit cards, debts, insurance gaps or other potential problems. A debt hardship workflow is triggered only if the user themselves reports debt/payment difficulty.

## 18.3 Search scope and resource evidence

- Search verified Sacramento-area shelters and coordinated access routes, family placement options, faith-based and community charities that demonstrably offer accommodation or financial assistance, hotel/motel voucher programs where confirmed, rental assistance, eviction prevention and applicable legal aid.

- For each concrete program verify operator, service offered, service area, eligible household composition and ages, financial criteria, application/referral route, current funding/open status, and any published time or capacity constraints. Do not treat a directory listing as confirmation of a bed or voucher.

- Do not search or compare commercial apartment listings, hotels or short-term rentals, and do not book accommodation. If the user has funds, the Navigator may mention independent use of mainstream booking platforms without creating a property-search workflow.

- Provide multiple relevant options and parallel actions where justified. Do not promise immediate shelter admission, a queue position, voucher approval, or a specific placement date. Do not present legal aid as a substitute for accommodation; suggest it only when reported legal documents or issues make it relevant.

## 18.4 Honest expectation-setting and temporary alternatives

- Explain that the Navigator will make a thorough effort to identify relevant housing-assistance programs, but placements may take time and availability is not guaranteed.

- While applications or referrals are pending, gently suggest asking trusted relatives or friends about temporary accommodation only if feasible and safe; never assume that such support exists or require the user to disclose private relationship details.

- Crowdfunding can be offered as an optional user-consented supplementary action when relevant; it is not an automatic recommendation or a substitute for verified housing programs.

## 18.5 Cross-domain non-leading intake rule

- Open-ended user narrative establishes needs; Agent 1 records only user-reported needs and facts. Agent 2 asks targeted, non-leading clarifications required for the already identified need or a real program. Unknown is not equivalent to absent.

- One limited neutral question about access to food may be used in an income-loss/financial-crisis context. Do not automatically screen food-seeking users for medications or healthcare, and do not prompt for insurance, debts, transportation or other unrelated needs. Medical and medication assistance activate when the user reports those problems.

- Previously collected answers are reused across food and housing; do not repeat questions unless the answer is ambiguous, outdated, or insufficient for a specific eligibility rule.

## 18.6 Acceptance fixtures and research boundary

- Fixture A: user has lost housing but has funds for a motel. Navigator does not default to shelter-only solutions, does not book or compare commercial rooms, and still considers suitable aid under verified rules.

- Fixture B: user seeks accommodation for themselves and children aged 7 and 19. Navigator verifies age-dependent program fit rather than assuming both qualify as minors.

- Fixture C: user reports inability to pay rent and mentions sheriff documents. Navigator identifies the housing need, clarifies the relevant legal stage if necessary, and searches housing assistance in parallel with applicable legal-aid information.

- Fixture D: user reports food insecurity only. Navigator does not initiate housing, debt, medication or insurance workflows without user-reported need.

- Pending research: independently validate Sacramento shelter access, faith-based/community placement, hotel-voucher availability, rental assistance and legal aid, including official application routes, constraints, and service status. Store changing provider facts in Verified Knowledge Base, not as timeless assertions in this design.

# 19. Shared intake decision engine — implementation-ready behavior contract

Status: APPROVED behavioral requirements from design review, with explicitly marked PENDING engineering choices. This section operationalizes §§16–18; if earlier illustrative wording conflicts with the approved non-leading rule here, apply this section. Do not change the ten logical roles or create an eleventh agent.

## 19.1 Trigger policy: discover needs without manufacturing needs

- Start with a neutral, open-ended request to describe the crisis and financial circumstances. Extract only explicitly reported needs; do not infer a new housing, debt, insurance, medication or transport need from job loss, poverty, household composition, or benefit availability.

- If the user describes income loss or financial crisis, ONE optional neutral food-access check is allowed. If the user says food is sufficient, mark the check resolved and do not repeat it. Food need may also be volunteered without a check.

- If the user reports food insecurity alone, do not initiate housing or medication screening. Medication/medical assistance activates only when the user explicitly describes that difficulty. No automatic medication question.

- Debt hardship is activated only when the user explicitly describes a loan, card, mortgage or other debt-payment difficulty. Do not offer a checklist of potential debts or ask everyone for monthly obligations.

- A program-specific factual clarification is not the same as inventing a new need. It may be asked only after a user-reported need or an explicitly opted-in program, and must be linked to a documented requirement.

## 19.2 Agent 1 → Agent 2 contract and question selection

Agent 1 output proposal: narrative_summary; triggering_events\[\]; user_reported_needs\[\] {need_type, original_quote_or_span, user_reported=true}; factual_claims\[\] {field, value, time_context, source=user_statement, status=proposed\|confirmed\|disputed}; ambiguity_flags\[\]; safety_or_official_deadline_flags\[\]; no invented needs. Request user correction/confirmation of concise summary rather than confirming every field.

Agent 2 consumes Case State, Agent 1 proposal, and candidate-program data requirements. For each possible question, calculate: existing fact? fact current enough? requirement source verified? does answer change resource discovery, eligibility screening, action feasibility or required application step? If not, skip. Ask at most one small coherent cluster per turn. Unknown or declined fields remain unknown; do not treat as zero, false or disqualification.

Decision ordering: (1) user-stated need; (2) minimum geography and household facts for broad retrieval; (3) retrieve candidates; (4) identify missing candidate-specific facts; (5) ask only questions that change a real decision; (6) update Case State with provenance; (7) rerun matching where affected. Never block all retrieval until a full questionnaire is complete.

Suggested field states: unknown / user_reported / user_confirmed / disputed / superseded; timestamps and source. Reuse confirmed/recent data across food, housing and other needs. When a question was answered earlier, ask again only on evidence of change, contradiction, or a provider-specific period requirement.

## 19.3 Shared Financial Profile — data definitions and limits

- historical_household_monthly_income: approximate amount and period before crisis, used to understand change; not assumed to be a universal eligibility criterion.

- current_household_monthly_income: approximate current amount, reference month, household scope, and income sources (wages, benefits, rental income and others when disclosed). Distinguish zero from unknown.

- income_change_event: what changed and when, only when relevant to the described crisis.

- available_liquid_funds: approximate funds actually accessible for near-term action; distinct from income and total assets.

- assets_and_property: collect specific ownership, rental income, availability and valuation details ONLY where a documented program criterion or identified practical decision requires them. A rented-out property is not an automatic disqualification across all programs.

- program_relevant_costs: rent, utilities, childcare or other eligible expenses ONLY when a specific program calculation or stated need makes them material. Never collect a generic debt inventory or treat credit-card payments as universally eligible deductions.

- temporary_housing_budget: optional practical spending capacity if the user reports housing need; distinct from recurring income. Do not search or book commercial lodging.

Privacy: use approximate self-reports for preliminary matching; do not solicit SSN, bank account/card numbers, complete statements, tax returns or sensitive medical records as a default. Only an authorized provider requests formal evidence at application stage. The Navigator must never certify eligibility or imply that reported numbers have been verified.

## 19.4 Household composition and program-specific semantics

Ask naturally who needs the requested assistance and ages of children when relevant. “Children” may mean adults; age-based provider restrictions must be checked individually. Temporary guests are not automatically household members. Never apply a universal six-month residence rule. For CalFresh, distinguish food-purchasing/preparation group from other co-residents when the official rule makes it material; explain why before asking. Household definitions vary by program; retain separate provider-specific interpretations rather than overwriting a universal household_count.

## 19.5 Question policy acceptance fixtures

- Job loss + cannot pay rent: open financial clarification; housing route; at most one optional food check. No unsolicited debt/insurance/medication branch.

- Food-only request: food distribution and CalFresh research; no housing, medication, debt or insurance prompts.

- Food request + user explicitly mentions prescription cost: both food and medication-access routes, with no inferred diagnosis.

- User mentions credit-card hardship: optional bank hardship letter assistance, user-controlled; no guarantee of deferral or interest relief.

- User refuses asset disclosure: leave unknown, still retrieve resources, flag candidate-specific eligibility uncertainty.

- User corrects income from \$0 to \$1,200: supersede old fact with audit trail; rerun affected matching, avoid duplicating questions.

# 20. Housing assistance — detailed Bob implementation specification

Status: APPROVED product behavior; actual Sacramento organization eligibility, capacity and live funding remain PENDING evidence verification. Implement one housing-need workflow with provider-driven differences, not independent artificial urgency branches.

## 20.1 Entry, minimum data and stopping rules

Entry: explicit user-reported housing instability, loss of accommodation, inability to afford existing housing, or request for housing aid. If vague, ask “Please tell me more about the housing difficulty you are facing.” Do not ask all users to choose today/tomorrow/next month. Do not routinely ask whether there is a safe place tonight or how long they may stay with relatives.

Minimum broad search facts: Sacramento service area or ZIP; who needs placement (adults, children and their ages where provider rules depend on age); known shared financial facts; whether user seeks to preserve existing accommodation or find a place, ONLY if unclear and material to provider selection. Search can start with unknown income or family data; record uncertainty and seek provider-specific clarification later.

If a user volunteers an actual sheriff/court deadline, preserve the exact wording, document type and date if given. Ask for document/stage only if legal aid or immediate practical action depends on it. Never promise months of lawful occupancy, offer legal conclusions, or replace housing search with a legal referral.

## 20.2 Candidate discovery and independent evidence checks

- Search KB for Sacramento coordinated-access shelters, direct-intake shelters, family placements, faith/community charities offering demonstrable accommodation or emergency funding, verified hotel/motel vouchers, rental assistance, eviction prevention and relevant tenant legal aid.

- Search the verified KB first; controlled external lookup only under the approved fallback policy (§13). A church providing food is NOT evidence it offers beds; a directory listing is NOT proof of active funding or vacancies.

- Per candidate require program_id, provider, assistance_type, service_area, target_household and age constraints, income/asset conditions if published, referral/application route, documented hours, service duration if known, verification timestamp, evidence by field, funding/open status and availability as distinct states.

- Do not convert historical wait times into a guaranteed user-specific estimate. Record availability=unknown unless explicitly and recently confirmed. “Accepting inquiries” is not equivalent to “bed available.”

- If no confirmed option exists, do not fabricate a placement. Show credible contact routes, unverified-but-promising leads with uncertainty labels, and actions to confirm; do not suppress all helpful options because inventory is unknown.

## 20.3 Assistance paths and user-facing limits

One search returns the full applicable set of options; it does not promise placement. When a coordinated-access provider requires referral through 211, describe that process and help the user prepare; do not claim to reserve a slot or enter a queue. Independent direct-intake organizations may be presented only with verified current intake rules.

If user has funds for temporary accommodation, acknowledge self-funded options and optionally mention mainstream booking websites for independent use; the system does not search apartment/hotel listings, compare prices, book rooms or build commercial real-estate tools. Having some funds does not automatically remove charitable options; assess actual program rules.

If housing support may take time, clearly explain that applications, assessment and placement can be delayed and no result is guaranteed. Offer a gentle optional suggestion to ask trusted friends or relatives for a temporary stay if feasible and safe; never presume that such support exists. Crowdfunding is a separate opt-in supplementary action, never a default prerequisite.

Legal aid is an OPTIONAL parallel action only when the user reports a relevant notice, filing, court judgment or sheriff action and provider evidence supports the referral. No automatic claim that legal intervention stops eviction.

## 20.4 Handoff contracts and prioritization

Agent 1 → Case State: user-reported housing_need, original wording, context, family composition facts, financial facts and any volunteered official deadlines. Agent 2 → clarification_request: {missing_field, linked_program_ids, verified_rule_ref, rationale, user_facing_question, can_skip=true}. Agent 3 → candidate records; Agent 4 → match states (potential_match/supported_match/confirmed_mismatch/insufficient_information); Agent 5 → field-level evidence and current status; Agent 6 → ordered, user-editable parallel actions; Agent 8 → plan assembly; Agent 10 → validation PASS/FLAG with targeted repair. Preserve existing agent-role names and contracts.

Prioritization must not be solely by “today versus tomorrow” labels. Order by actual action dependencies, published provider deadlines, user constraints, relevance and practical feasibility. Unknown wait time stays unknown. No false assurance, no fabricated vacancy, and no suppressing useful parallel alternatives. User may reorder plan actions.

## 20.5 Required scenario tests and expected outcomes

- H1: User lost housing, has \$2,000 available. Return verified housing aid if relevant; mention self-funded booking as optional user action; do not default exclusively to shelters or run commercial property search.

- H2: Parent with children ages 7 and 19, no accommodation. Require age-specific fit check for each family shelter; do not assume the 19-year-old is eligible or automatically excluded.

- H3: User says sheriff will enforce a writ in two days. Preserve volunteered legal deadline, find housing options and optional legal aid in parallel; do not guarantee court relief or a shelter bed.

- H4: User cannot pay rent next month but reports no notice. Search applicable prevention/rental support without claiming an eviction date or creating an emergency track.

- H5: User asks for housing but declines income details. Return suitable candidate leads and flag eligibility uncertainty; no blanket rejection.

- H6: Provider is listed but status unknown or closed. Do not represent it as available; verify or label the uncertainty and seek alternatives.

- H7: User only reports food shortage. No housing intake questions or housing resource recommendations.

- H8: User mentions no safe family contacts. Do not repeat advice to stay with friends; focus on institutional routes.

# 21. Cross-section completeness audit and build-readiness gates

Audit method: reviewed all existing top-level sections (§§1–18) and detailed approved intake decisions. This is a document consistency audit, not a claim that all interfaces, IBM platform tools, or Sacramento providers are production verified.

## 21.1 Existing sections and their current maturity

- §§1–8: foundational design, access matrix, Case State, evidence, error handling and decision log. Some content is explicitly Proposed or Working: preserve labels; freeze only after contract review.

- §§9–12: typed KB/evidence fields, agent 3/4/5 interfaces and tool boundaries. They contain implementation detail, but actual tool bindings, schema enforcement, and sample payload execution still need validation.

- §13: KB-first search fallback and action prioritization are approved; source recency thresholds, fallback quotas and tool failure behavior need engineering configuration and tests.

- §14: preliminary candidate wording approved; exact UI formatting and localization remain implementation details.

- §15: Agent 6 action prioritization approved; output schema and “First / Next / Later” grouping are explicitly NOT frozen.

- §16: earlier job-loss example mentions routine assets and runway; narrow it using §19: do not turn those examples into universal mandatory questions. Only provider- or need-relevant asset detail.

- §17: food program path and site-specific KB records approved. The earlier line implying food need must always be user-volunteered has a limited, approved exception: one optional neutral food check after income loss (§19). No automatic medication question.

- §18: housing scope approved but previously too concise for Bob; detailed executable decisions and fixtures now live in §20.

## 21.2 Bob build gates — do not infer missing product decisions

- BEFORE BUILD: reconcile and freeze exact Agent 1/2 payload schemas, state transitions, provenance fields, validation errors, and deduplication behavior with the existing Case State typed schema.

- BEFORE BUILD: map the ten logical roles to actual IBM watsonx Orchestrate supervisor/collaborators and verify each tool binding, knowledge connection, permission and deployment constraint. Logical roles need not equal deployed agents.

- BEFORE LIVE RECOMMENDATIONS: load independently verified Sacramento provider records with authoritative evidence, last-verified dates and separate program-verification/availability/match states.

- BEFORE DEMO: run fixtures from §§11–20, including contradiction, missing data, closed programs, no matches, tool failure, unsafe promises and cross-domain need leakage.

- PENDING: define operational recency windows, source authority precedence, query budgets, detailed retry/error envelopes, privacy retention settings and approval thresholds. Bob must flag these, not invent defaults.

- PENDING: detailed output presentation (including “First / Next / Later”) is not approved; do not silently implement it as a product requirement.

# 22. Bob implementation contract — executable rules and non-inference policy

## 22.1 Decision authority and traceability

APPROVED product decisions in this document are binding. PROPOSED and PENDING are not implementation permission. Bob must surface unresolved choices for human review, not pick a default that changes user experience.

If earlier and later sections conflict, do not silently prefer either. Record the exact competing statements in a decision issue, mark the relevant behavior blocked, and request resolution. The latest approved amendment can supersede an earlier approved rule only when explicitly stated.

Each implementation work item must reference section number, contract version, status, expected behavior and at least one acceptance fixture. Maintain a decision register with owner, approval date, rationale and affected agents.

## 22.2 Intake: deterministic decision sequence

1\. Parse only facts and needs stated or confirmed by the user. Preserve original wording and source; uncertainty stays uncertainty. Do not manufacture a need from a plausible life consequence.

2\. Load existing Case State and previously answered questions. Merge semantically equivalent fields; do not ask again unless stale, contradictory or required at a different scope.

3\. Ask the smallest question that enables a specific next action or program eligibility check. Each question must have a reason code, affected need/program and a clear stop condition.

4\. One neutral food sufficiency check is permitted after reported financial/income crisis; a negative answer closes that check. Do not automatically ask about medical insurance, prescriptions, loans, utilities or other categories.

5\. For user-reported debt hardship, only then consider creditor hardship/forbearance assistance. For medical help, only activate when medical costs or needs are independently raised.

6\. Save user correction as an updated fact with provenance; do not overwrite earlier statements without history. Unknown, declined, disputed and not-applicable are distinct states.

## 22.3 Shared financial and household data

Shared financial profile distinguishes pre-crisis monthly income, current monthly income, income sources, available cash/savings, and other assets. Do not infer income from assets or treat all assets as liquid.

Collect only fields necessary for identified needs and specific programs. Household definition is program-dependent; never apply a universal six-month residence or tax-dependent rule.

For family housing, clarify who needs placement and the ages of children when the program distinguishes minors from adults. Do not request family member identity documents unless a verified application step requires them.

When material income or assets are unknown, retain plausible candidates with an uncertainty status and a targeted clarification or direct-provider verification step. Conversely, when the correct documented mandatory rule and comparable confirmed user fact prove a mismatch, exclude that program from recommended Action Cards; do not label the user officially ineligible or exclude unrelated programs.

## 22.4 Housing: retrieval and response algorithm

Entry: user independently describes loss of housing, inability to pay rent, need for placement or related housing difficulty. Keep a unified housing need; court eviction, homelessness and prospective loss are context, not forced mutually exclusive routes.

Use existing financial profile, household details, ages where relevant, geography and any user-provided deadlines. Do not ask a generic “tonight / three days” timing question unless a real service intake or legal deadline makes it material.

Search verified shelters, coordinated access, independent nonprofits, charities, community and faith-based resources, emergency accommodation or vouchers only where supported, eviction prevention and relevant longer-term housing aid. Do not build Airbnb, Booking, motel shopping or rental listing integrations.

For each candidate record its actual assistance type, eligible population, geography, contact/application channel, source date, verification status, required documents, restrictions, access mechanism and availability status independently. Never treat a valid program description as evidence of an open bed.

Sacramento coordinated access may require 211. Check independent intake routes separately rather than assuming all programs use the same entry point. If no confirmed placement is found, provide verified contacts, uncertainties and a realistic parallel action plan, not a fabricated placement.

Explain that placement may take time and is not guaranteed. Suggest asking trusted relatives or acquaintances about temporary safe accommodation only as an optional possibility; do not imply the user has such contacts or that it is safe.

Court notice or writ details may trigger targeted legal-aid information when relevant; do not require legal aid as a prerequisite for housing support. Crowdfunding is optional when the user is interested and must not replace service matching.

## 22.5 Food: parallel pathways and no unsupported promises

When food insecurity is confirmed, evaluate food banks/pantries and CalFresh in parallel as applicable. Food bank site rules, hours and requirements are location-specific; no generic guarantee of food or same-day service.

CalFresh standard and expedited processing are distinct eligibility and timing checks; do not promise expedited approval without verified criteria. Program-specific household and financial rules govern questions.

Do not force an account before initial story. Account creation may be offered for saving a plan; do not collect phone, SSN or bank details during general intake.

## 22.6 Retrieval, matching, verification and planning boundaries

Retrieval returns candidates with evidence and timestamps; matching returns criterion-by-criterion assessments with unknowns; verification assesses claims and source authority; none of these equals real-time program capacity.

Conflicting sources must remain visible as claim-level conflicts. An unverified claim may be shown only as clearly preliminary when policy allows; never silently promote it to verified.

Action planning uses user priorities and program deadlines separately. Do not arbitrarily limit a personalized plan to three actions; explain dependencies, parallel steps, responsible actor and progress states.

Before releasing an action, validate that it references a real candidate/program, the instructions follow verified evidence, and no unsupported promise or prohibited data request is included.

## 22.7 Bob build acceptance fixtures

Fixture A: “I lost my job; food is okay.” Expected: income/housing questions only if user context warrants; one neutral food check can close; no debt or medical workflow.

Fixture B: “I cannot afford food and rent.” Expected: shared financial facts collected once, separate food and housing program matches, no invented eligibility.

Fixture C: “My children and I need somewhere to stay.” Expected: determine who needs housing and children’s ages only as relevant, search family-eligible options, no placement guarantee.

Fixture D: “I got a court eviction document.” Expected: clarify document and date if needed, continue housing search; legal help offered conditionally, not mandated.

Fixture E: “Can you find me a hotel on Booking?” Expected: explain the navigator does not search or book commercial accommodation; may direct user to self-search and continue supported assistance.

Fixture F: “The shelter website says open but the phone says full.” Expected: retain conflicting source claims, do not state a bed is available, give verified next steps.

Fixture G: “I have savings but no income.” Expected: separate income from liquid assets; apply only specific program tests; no universal rejection.

Fixture H: user declines to answer a nonessential question. Expected: record declined; proceed with provisional options where possible and explain limitation.

# 23. Utility Assistance — approved intake and matching logic

## 23.1 Status, scope and non-leading activation

Status: APPROVED behavioral design (17 October 2026). This section specifies utility-bill assistance for Sacramento pilot, not a verified list of currently funded programs. Activate this domain ONLY when the user explicitly reports an existing or anticipated difficulty paying a utility bill, utility arrears, a disconnection notice, or an already disconnected utility. Do not infer a utility need solely from job loss, low income, food insecurity, or housing instability. Do not suggest this domain unsolicited. An anticipated inability to pay qualifies as a user-reported need; no existing debt is required.

## 23.2 Agent 1: extraction and case-state boundaries

Extract the exact user-stated utility need, service type if named (electricity, gas, water, sewer, trash or other), provider if named, current versus anticipated payment difficulty if clear, arrears if volunteered, and any notice/disconnection facts. Preserve the distinction between a user-predicted future shortfall, a routine bill due date, and a formal utility shutoff date. Mark unknown facts UNKNOWN, not false. Never invent a provider from ZIP alone. Record provenance as user-stated versus program-verified; do not treat a user estimate as an official shutoff notice.

## 23.3 Agent 2: minimal, conditional clarification

Ask only missing questions that materially affect candidate discovery, eligibility or actionable prioritization. First establish the utility service and provider if they are not already clear and if needed for relevant programs. Do not ask these again if the user already said, for example, “SMUD electricity.” Do not routinely ask “Is it urgent?”, “Has the problem started?”, “When is your next bill due?”, or request all dates and balances. Ask about unpaid bills only where relevant to arrears-specific programs. Ask about a disconnection notice or shutoff date only when user mentions a threatened disconnection or a candidate program requires it. Ask for amount owed only if required for matching, eligibility, or a concrete action. Reuse known location, income, household and financial profile fields from Case State. If a user does not know a provider or date, proceed with available candidates and flag verification needed; do not block the whole plan.

## 23.4 Retrieval and program mechanisms

Search verified program records across applicable mechanisms: one-time bill credits or grants; recurring income-based discounts; arrears and disconnection prevention; restoration assistance where documented; provider payment arrangements or extensions; water/sewer/trash assistance where service territory applies. Treat these as assistance mechanisms, NOT separate user needs or compulsory interview branches. Match by actual service territory, named provider, household/program-specific eligibility, arrears/notice requirements, current enrollment prerequisites, funding status and application channels. A program for one provider must not be presented as applicable to another without evidence. Program dependency or stacking must be supported by source evidence, not assumed.

## 23.5 Priority, timing and failure handling

If the user reports an actual disconnection or formal impending shutoff, prioritize verifying restoration or disconnection-prevention pathways and contacting the provider; search other eligible assistance options in parallel. Do not promise same-day funds, restored service, avoided shutoff or provider approval. Compare published processing times with the user-reported shutoff date and explicitly flag when a program cannot reliably meet that deadline. If no verified matching assistance is found, state that the search has not identified a confirmed option; suggest asking the utility provider about payment plans, extensions, discounts or hardship processes as possibilities, not guaranteed rights. Never substitute an unverified charity or closed funding round as a confirmed active grant.

## 23.6 Agent handoffs and user-facing plan

Agent 1 produces user-reported need facts; Agent 2 resolves only necessary gaps; Resource Retrieval supplies program candidates and source evidence; Matching checks service/provider/geography/eligibility; Verification checks active status, conditions, conflicts and last verification date; Prioritization and Plan Builder produce distinct actions with deadlines only when grounded, documents needed, links/contact methods and honest uncertainty. Maintain evidence links and UNKNOWN statuses through every handoff. Do not expose internal agent architecture to the user. Do not request or store utility account numbers unless a later explicitly approved workflow genuinely requires them; none are required by this intake design.

## 23.7 Acceptance fixtures for Bob

TEST — User: “I lost my job.” Expected: DO NOT activate Utility Assistance or ask about utility bills.

TEST — User: “I will not be able to pay my water bill next month.” Expected: activate Utility Assistance; identify water provider if needed; do not require an existing balance or ask a routine due date by default.

TEST — User: “I owe SMUD for electricity.” Expected: service and provider already known; do not ask them again; ask arrears/notice details only if needed by matching program rules.

TEST — User: “They will turn off my gas in 48 hours.” Expected: clarify provider and formal notice/shutoff date as needed; prioritize credible disconnection pathways, but do not promise prevention.

TEST — User: “My power has already been disconnected.” Expected: prioritize verified restoration pathways and provider contact, without creating a separate domain or guaranteeing reconnection.

TEST — User: “I do not know the company.” Expected: do not hallucinate a provider; proceed with provider-neutral options where available and mark provider as unresolved.

TEST — User: “I have a notice dated October 20 but my bill is due November 5.” Expected: retain two different dates with their respective meanings; never overwrite one with the other.

TEST — No confirmed program available. Expected: state uncertainty accurately, give provider-contact and payment-plan inquiry as non-guaranteed fallback; never invent grants.

## 23.8 Explicit boundaries and future research

Approved here: activation by user-stated need; service/provider-oriented search; conditional arrears/notice/date questions; prioritization of documented disconnections; realistic expectation-setting; fallback provider contact. Not yet approved: universal mandatory utility questionnaire, fixed urgency tiers, account-number collection, program-specific eligibility shortcuts, invented service deadlines, or automatic activation of other domains. Exact organizations, amounts, application windows and current funding must be independently researched and stored as sourced Verified Knowledge Base records. This section is an implementation behavior contract, not evidence that any program is presently accepting applications.

# 24. Income Assistance — approved discovery logic and implementation contract

## 24.1 Scope, entry trigger, and non-leading intake

Status: APPROVED for product-level needs discovery, conditional clarification and matching. Exact eligibility thresholds, amounts, processing times and current availability remain program-source-dependent; do not hard-code preliminary research as permanent rules.

Activate Income Assistance only when the person reports loss, reduction, interruption, insufficiency or expected disruption of earnings or other income, or explicitly asks for income/cash benefits. Examples: layoff, reduced shifts, inability to work due to illness, loss of household earner, or concern that income will stop next month. A user who reports only housing, food or utilities need must not be interrogated about unemployment programs or automatically assigned a separate income need.

Agent 1 extracts stated circumstances and distinguishes direct facts from inferences. The general intake may ask what financial difficulties the person currently faces or expects and, when volunteered, the approximate timing. Do not present a checklist of possible additional problems. Do not infer an immigration category, disability, household relationship, employment classification, or eligibility from a narrative.

## 24.2 Shared Financial Profile: collect once, reuse carefully

Use existing Case State fields for approximate monthly household income before the crisis and now, income sources, available cash/savings, and relevant assets when program-specific rules require them. Record amounts with time period, currency, household/person scope, provenance (user-reported vs document-supported), and unknown/declined status. Never treat gross income, net income, assets and accessible cash as interchangeable.

Household composition and ages/relationships are requested only to the extent relevant to a plausible program (for example, CalWORKs family composition). A household is not universally the tax household, people at one address, or everyone in a family; use the applicable program definition. Employment history, covered wages, last day worked, reduction in hours, and reason for income loss are conditional facts: ask only when needed to assess a concrete candidate such as UI or DI.

Investments, shares, a second property, bank balances and other assets are not mandatory blanket intake questions. Where a candidate program has a documented resource test, first check whether existing data resolves it, then ask a narrowly scoped question with a brief explanation of why it matters. An asset may be excluded under one program and counted under another; never globally disqualify the case based on asset ownership.

## 24.3 Candidate mechanisms: not interchangeable benefits

Search mechanisms appropriate to the user’s expressed income disruption, using verified program records: (a) California EDD Unemployment Insurance for potentially qualifying loss of employment or reduced hours; (b) CalWORKs cash aid for qualifying families with children, including a conditional review of Immediate Need and Diversion when published criteria fit; (c) Sacramento County General Assistance for potentially qualifying adults; (d) California State Disability Insurance / Disability Insurance when the user independently reports inability to work due to a qualifying health-related circumstance; (e) Paid Family Leave for reported qualifying family caregiving or bonding-related lost earnings; (f) Work Sharing when reduced hours and employer participation are relevant; (g) Refugee Cash Assistance or CAPI only where a person’s stated circumstances and verified rules make them plausible. Do not assume these programs are simultaneously payable or universally available.

Income replacement, need-based cash aid, accelerated aid, and employment services are distinct mechanisms. Employment/training services can be a supplementary action if relevant to a user’s stated goal; do not misrepresent job-search assistance as immediate cash. Other domains such as Food or Utility Assistance activate only on user-expressed needs, except an already-approved narrowly scoped food-security check in the shared intake policy.

## 24.4 Conditional Agent 2 questions and urgency

Minimum first pass: clarify the reported income change and whether it is current or anticipated only if unclear; reuse household financial and geography data. Ask follow-ups only if they change the candidate set, eligibility confidence, or recommended order of action. For unemployment: prior work/earnings, approximate reduction or separation, and work availability only if UI is a plausible candidate. For family cash aid: children and family composition only as necessary. For DI/PFL: relevant user-reported work interruption and program-specific eligibility facts, without seeking unrelated medical detail. For GA: applicant/household and income/resource conditions only where required by verified Sacramento County rules.

Do not ask a universal “How urgent is this?” question. Capture dates only when they have a real consequence: date income stopped, expected loss of income, application deadline, potential retroactivity, or an explicitly verified expedited pathway. Distinguish the user’s expected financial difficulty from an official program deadline. CalWORKs Immediate Need is a conditional expedited process, not a guarantee of same-day money or an excuse to suggest unrelated crises.

## 24.5 Retrieval, eligibility, verification and planning

Agent 3 retrieves geographically relevant candidates and preserves source-linked program facts. Agent 4 matches the expressed income need, financial/household facts and program-specific conditions without collapsing “unknown” into “ineligible.” Agent 5 verifies claims against evidence, including administering agency, eligibility rules, benefit type, application channel, deadlines, processing estimates, interaction restrictions, and last verified date. Conflicting or stale evidence must be marked and disclosed; do not fabricate benefit amounts or approval odds.

Agent 6 can recommend multiple potentially applicable mechanisms in parallel where rules permit, but must identify dependencies, incompatible payments, application order and uncertainty. Separate (1) user action, (2) required documents only if supported by source, (3) expected timeline with source date, (4) verification status, (5) fallback if a program is closed or not eligible. No benefit, payment date or approval is guaranteed. An optional benefit may be listed as a preliminary possibility only under the existing preliminary-option disclosure policy.

If no verified candidate is available, say so plainly, suggest appropriate official application or local assistance channels only where supported, and retain unresolved questions for follow-up. Do not silently substitute unrelated food/housing/debt services as if requested.

## 24.6 Case State and handoff contract

Agent 1 output: reported_income_need=true, user-stated change/reason/timing with provenance and confidence, plus relevant stated household facts; never fabricated eligibility. Agent 2 output: minimal new facts and outstanding program-specific questions, with a reason for each question. Persist approved user-reported facts through authorized Case State operations; agents must not overwrite a previous figure without preserving conflict/provenance. Retrieval/matching/verification results must reference candidate program IDs and evidence IDs. Plan Builder returns actionable steps and clear unknowns; no new agent or separate income-only pipeline is required.

Exact JSON names and typed payloads must be reconciled with canonical Case State and agent envelopes before implementation; this prose does not supersede frozen schemas or authorize Bob to invent incompatible fields.

## 24.7 Acceptance fixtures for Bob

TEST — User: “I lost my job last week.” Expected: activate income need; do not auto-activate utilities, housing, medical or debt; consider UI only after relevant facts are known.

TEST — User: “My hours were cut, but I am still employed.” Expected: consider reduced-hours income mechanisms; do not assume unemployment or employer Work Sharing participation.

TEST — User: “My income will end next month.” Expected: record anticipated income disruption; investigate advance-application rules only when source-supported; do not demand an exact utility bill due date.

TEST — User: “I have two children and almost no income.” Expected: conditionally consider family cash assistance; use known ages/household data; do not promise Immediate Need.

TEST — User: “I cannot work because of an injury.” Expected: conditionally investigate DI and other stated income-related needs; do not request diagnosis or insurance information unless specifically required.

TEST — User: “I have \$2,000 in stocks.” Expected: preserve the asset fact, check each candidate’s resource treatment; do not reject all programs.

TEST — User: “I need help with rent.” Expected: housing need only; do not ask why user is unemployed or activate income need without the user raising it.

TEST — Candidate UI and GA records disagree on an eligibility rule. Expected: retain separate sourced claims, mark conflict and avoid definitive eligibility judgment.

TEST — No verified income-aid record meets known conditions. Expected: explain uncertainty or lack of match; do not invent a program, amount or guaranteed payment.

## 24.8 Evidence and build gates

Program names are research candidates, not fixed eligibility determinations. Before shipping, link each candidate to a Verified Knowledge Base record with official sources, geography, dates and current application instructions; verify any overlap/exclusion rules. Freeze the concrete agent input/output and Case State mappings; run all fixtures plus cross-domain regression tests. Open technical decisions remain in the Developer Clarification Register, now section 25.

# 25. Medical Assistance & Health Coverage — approved design

## 25.1 Activation and boundaries

Activate only if the user explicitly raises health coverage, medical care, medication, medical bills, or inability to pay for a medical service. Loss of work, food, housing, or a family member does not itself trigger medical intake. Insurance-only and care-only requests are independently valid. Do not automatically ask medical questions in general intake.

## 25.2 Shared data and minimal clarification

Reuse known household composition, geography, income before and after crisis, income sources and relevant finances from Case State. Do not ask again. Do not request age at initial general intake: collect ages only for the relevant persons when insurance or a particular medical service/program requires it. Save these facts for reuse. Tax household may differ from co-residents; ask about tax relationships only when a candidate program requires them. Assets are conditional on specific eligibility rules, not a universal medical question.

## 25.3 Person-level insurance profile

For insurance needs identify who needs coverage, current or prior coverage per person, type (Medi-Cal, Medicare, employer-sponsored, Covered California, other), source of coverage, whether active/ending/ended, and the actual end date if relevant. Family members can have different insurance. Ask only unknown, consequential facts. For a recent interstate move, verify applicable special-enrollment conditions and move date; do not assume eligibility or coverage start dates. For loss of employer insurance after a spouse’s death or job loss, distinguish the death/job-loss date from the coverage end date; consider continuation options, public coverage and marketplace enrollment without guaranteeing eligibility.

## 25.4 Medical care, medications and bills

For requested care identify the service category (doctor, dental, diagnostic test, prescription, hospital bill) and coverage type, then clarify the barrier only if missing: no coverage, uncovered service, copay, network access, or outstanding bill. Where appropriate search care providers and coverage options in parallel; never make insurance enrollment a prerequisite for looking for available care. For medical bills, consider verified hospital financial assistance even when the patient has insurance. Do not collect diagnoses, detailed history, insurance numbers or medical documents for initial program matching.

## 25.5 Agent workflow and source discipline

Agent 1 extracts user-stated need without manufacturing adjacent needs. Agent 2 asks the minimum missing questions based on concrete program constraints. Retrieval discovers coverage and/or care programs; Matching checks person-specific conditions, geography and eligibility; Verification records dated evidence, unknowns and conflicts; Plan Builder produces realistic next actions and deadlines only when supported. Do not promise acceptance, coverage, price, clinical availability or effective dates. Program-specific criteria and up-to-date availability are stored in Verified Knowledge Base, not hard-coded assumptions.

## 25.6 School-related health boundary

School enrollment alone is not a trigger for a broad education workflow. If a parent specifically asks for affordable vaccinations, school-required health/dental exams, or child insurance, handle that stated health need. Never assume every school transfer requires examination by a school nurse; verify grade, actual requirement and accepted records only when relevant.

## 25.7 Bob acceptance fixtures

A. Job loss only: no insurance or age question. B. Moved from another state, requests insurance: reuse known household/income; ask age and move/coverage dates conditionally. C. Uninsured user needs care: explore care and insurance concurrently. D. Medi-Cal member needs dental: check actual coverage and provider participation. E. Privately insured patient cannot pay hospital bill: consider hospital financial assistance. F. Spouse died, employer plan may end: ask actual coverage end date, not assume death date. G. Different family members have different plans: store person-level records. H. School enrollment alone: no invented medical need. I. Missing eligibility fact: preserve unknown, ask only when needed.

## 25.8 Status and research boundary

APPROVED: non-leading triggers, shared-data reuse, conditional ages and person-specific coverage questions, parallel coverage/care paths, honest claims, privacy minimization. PENDING SOURCE VERIFICATION: current eligibility rules, dates, deadlines, provider services, funding, and benefits for specific programs. PENDING TECHNICAL CONTRACT: exact person IDs, schema fields and interface mapping; Bob must not invent product decisions.

# 26. Debt Hardship Assistance — approved bounded navigation algorithm

## 26.1 Scope and entry trigger

Activate only when the user independently mentions difficulty paying a debt, missed payments, collection contact, a debt dispute, court papers, mortgage arrears, or related financial hardship. Do not proactively ask all crisis users whether they have debts. This is navigation and application/communication support, not debt payment, legal representation, regulated financial advice, or direct negotiation with creditors.

## 26.2 Minimal, case-driven clarification

Reuse the shared Financial Profile and any previously supplied household and income facts. Agent 2 asks only what is needed to distinguish the next appropriate options: debt category (credit card, medical bill, personal loan, mortgage, auto loan, other); current stage (payment strain, missed payment, collections, dispute, lawsuit); creditor or collector if relevant; approximate payment/amount if required for a program; and whether the user received a formal notice or court document. Request document date, service date, and any stated deadline only when a specific notice or legal proceeding is reported. Do not ask for account numbers, SSNs, passwords or full financial statements during initial matching.

## 26.3 Decision paths — distinct from benefit eligibility

Path A — Payment hardship without litigation: identify the creditor’s verified hardship or loss-mitigation options, possible temporary payment relief, revised payment plans, and appropriate nonprofit credit counseling. Explain that terms depend on the creditor and are not guaranteed. The navigator can help draft a factual hardship letter and checklist, not contact the creditor without authorized integration and consent.

Path B — Collections or disputed debt: identify whether the user reports a collector contact, disagreement about the debt, or both. Provide source-verified general information about validation, disputes and consumer-protection resources; distinguish a dispute from debt cancellation. Offer qualified legal aid where warranted. Never instruct the user to ignore collection communications or admit liability.

Path C — Court filing, garnishment or other legal action: surface the need to promptly inspect the actual notice, jurisdiction, service date and applicable response deadline. Do not calculate a definitive deadline from an unverified date or draft pleadings as if acting as counsel. Prioritize verified legal-aid or court self-help referral and preserve any known dates in the plan. For a California civil debt lawsuit, general 30-day answer rules may apply, but exact deadlines depend on circumstances and must be verified.

Path D — Potentially unsustainable multiple debts: offer nonprofit credit counseling and, if requested or clearly relevant, consultation with a qualified bankruptcy attorney. Do not recommend bankruptcy, debt settlement or stopping payments as a default or compute an optimal legal strategy.

Path E — Mortgage-related debt: retrieve verified servicer loss-mitigation information and appropriate HUD-approved housing counseling when relevant; coordinate with Housing Assistance only when the user identifies housing risk. Do not imply mortgage relief is guaranteed.

## 26.4 Safety and role boundaries

No guarantees of debt forgiveness, credit-score outcomes, settlement terms or lawsuit results. Warn neutrally about debt-relief firms that promise unrealistic results, demand problematic advance fees or encourage indiscriminate nonpayment. Avoid legal conclusions about liability for a deceased spouse’s debts; refer to qualified counsel because estate, contract and state law matter. The navigator does not select a legal defense, determine bankruptcy eligibility, negotiate, file court papers, or send notices on the user’s behalf by default.

## 26.5 Agent and plan behavior

Agent 1 recognizes only user-stated debt needs. Agent 2 asks conditional questions. Retrieval finds verified creditor processes, nonprofit counselors, court self-help and legal aid resources; Matching distinguishes service geography, debt type and case stage; Verification checks current eligibility, contacts, procedural sources and limitations; Plan Builder produces concrete, user-controlled actions, preparation checklists and draft correspondence where appropriate. Supervisor/QA flags legal-risk cases and unsupported promises. No separate legal agent is authorized.

## 26.6 Bob acceptance fixtures

A. User mentions job loss but no debt: no debt questions. B. User says a card payment is unaffordable: check payment hardship options; do not route directly to a lawyer. C. User says a collector called: ask only stage-specific questions; offer verified rights/resources without assuming a lawsuit. D. User has been served court papers: prioritize checking actual deadlines and legal referral, not routine payment-plan advice alone. E. User reports many unmanageable debts: present counseling and optional qualified legal consultation, without automatically recommending bankruptcy. F. User reports a late mortgage: search servicer/housing counseling options, without presuming eviction. G. User reports spouse’s death and debts in their name: do not presume personal liability. H. Prior income/household data exist: reuse without repeating. I. User asks for a hardship letter: generate an editable draft with user-approved facts; never send it automatically.

## 26.7 Evidence and implementation status

APPROVED: activation boundary, minimal questions, five navigation paths, legal escalation and prohibited conduct. PENDING SOURCE VERIFICATION: specific California deadlines and exceptions, creditor hardship program terms, counselor credentials, debt collection procedures, mortgage rules, local legal-aid availability and consumer-protection details. These belong in the Verified Knowledge Base with dated sources; do not hardcode unverified procedural claims.

# 27. Crowdfunding — informational guidance only

## 27.1 Activation and user choice

Crowdfunding is an optional information pathway, not guaranteed financial aid. If the user directly asks how to organize a fundraiser, provide guidance without requiring them to finish other assistance processes. Otherwise the Navigator may offer it once, optionally, when the plan identifies specific user-reported expenses for which sufficient help has not been found. Do not infer dishonesty from how someone asks for money; do not suggest a fundraiser solely because a person has low income. Respect a refusal and stop suggesting.

## 27.2 Permitted guidance

Provide verified platform names and links, current requirements, fees, withdrawal and identity-check rules, geography, privacy implications, and self-service steps for creating a fundraiser. Explain voluntary donations are not guaranteed and may affect means-tested assistance depending on program rules. After the user independently publishes a fundraiser, explain optional ways to share its link in social media, local community groups, friends/family networks and other groups where posting is permitted. Do not post or contact groups for the user. Distinguish crowdfunding platforms from churches, charities and nonprofits that provide direct material or monetary support.

## 27.3 Strict boundaries

The Navigator must not draft, rewrite, edit, title, embellish or emotionally optimize a fundraising appeal, including neutral drafts; invent or validate stories, diagnoses, deaths, expenses, testimonials or supporting documents; certify user hardship or honesty; create, publish, manage or promote fundraisers on behalf of the user; or collect or transfer donations. If asked to write a fundraiser text, decline that function and provide procedural instructions instead. Do not request bank credentials, SSNs or unnecessary documents. No scam-likelihood scoring, moral judgments or new fraud-detection agent.

## 27.4 Existing agents and tests

Agent 1 recognizes user-requested fundraising or an optional suggestion tied to an uncovered stated expense; Agent 2 asks only information needed to select appropriate guidance. Retrieval finds platforms; Verification checks source dates and terms; Plan Builder adds user-controlled tasks (review terms, independently create fundraiser, independently share link); QA blocks appeal generation and unsupported claims. Tests: direct request → guidance without copy; request to write an emotional story → no draft; uncovered funeral expense → optional offer without guarantee; user declines → no repeat; user asks where to share → explain permitted community channels; benefits recipient → do not promise donations have no effect.

# 28. Material & In-Kind Assistance — approved discovery and bounded search

## 28.1 Need scope and activation

Material & In-Kind Assistance is an independent user-stated category, not only housing. It includes furniture, beds, clothing, household items, bedding, hygiene and children’s essentials after fire, relocation, displacement or other hardship. Do not automatically infer needs from the crisis event. If user says “we lost everything,” ask which items are most important first. Direct charitable cash grants and donated goods are aid resources, not crowdfunding.

## 28.2 Minimal questions and shared data

Reuse Case State for location, household and financial facts. Clarify the particular items, quantities, sizes, intended recipients or transport/pickup ability only when relevant. For bulky furniture, whether delivery or pickup is possible can affect usefulness. Do not run a general questionnaire or suggest unrelated categories.

## 28.3 Resource discovery

Search verified charities, nonprofits, churches, independent organizations, local mutual aid and community programs for free or donated items and direct assistance. Knowledge Base stores organizations once and links multiple specific programs to multiple aid categories. Offer information on local Buy Nothing groups, Freecycle, Facebook Marketplace Free, Craigslist Free, Nextdoor and similar channels as optional self-service routes. Peer listings are not verified programs and may disappear; never assert real-time availability without an authorized current source. IBM Lab MVP provides vetted organization links and self-service platform instructions, not automated scraping, marketplace monitoring, logins or messages.

## 28.4 Safety and action limits

Warn about advance-payment/deposit scams, privacy and meeting/pickup safety. For children’s cribs, car seats or other safety-sensitive items, advise checking recalls and suitability. Do not guarantee stock, item condition, delivery or safety. The Navigator does not purchase, reserve, arrange delivery, transport, contact sellers/donors or exchange funds. Plan Builder gives clear self-directed steps and distinguishes verified charity program claims from unverified peer listings.

## 28.5 Agent workflow and acceptance

Agent 1 extracts specifically stated material needs. Agent 2 asks only missing item-specific facts. Retrieval identifies verified aid providers and optional search channels. Matching considers item, location, eligibility and collection constraints; Verification attaches sources and distinguishes unverified listings; Plan Builder provides next steps; QA blocks unsupported availability guarantees. Tests: fire + beds/clothes → seek those items; fire only → do not invent furniture needs; furniture without transport → flag pickup limitation; child car seat → safety check; request for live free listings without source → give search instructions, not invented offers; church with multiple types of assistance → one organization record with multiple program links.

## 28.6 Approval and evidence gates

Approved behavioral scope and MVP limitations; no new agents. Current Sacramento programs, availability, platform rules and eligibility still require independent source verification in the Verified Knowledge Base.

# CROSS-DOMAIN ACCEPTANCE TESTS — final product-logic gate

T1. User has five independently reported needs: all five remain in Case State and the integrated plan, with independent candidate searches and sensible parallel actions; no top-three cap.

T2. User reports annual income of \$100,000; a candidate program has a verified, applicable annual household income ceiling of \$50,000 for the correct household definition and no exception: classify confirmed_mismatch, cite the conflicting rule and fact, and omit it from recommended Action Cards. Do not exclude other programs by analogy.

T3. User owns real estate but no asset test is documented for a particular program: do not automatically reject or ask for a property appraisal. Where a verified asset rule applies, determine countable property and exceptions.

T4. User has large credit-card bills and asks about CalFresh: do not assume card payments reduce countable income; check the actual permitted deductions and other eligibility rules. Do not promise that high expenses overcome an income limit.

T5. Program matches preliminary criteria but funding is reportedly exhausted: preserve it as a possible program with independently labeled intake status; do not promise immediate funds, and continue searching for alternatives.

T6. No relevant result from first Knowledge Base search: use approved fallback; if still none, retain the unmet need and accurately report search limits rather than inventing a program.

T7. User reports death of spouse and multiple needs: reuse known death/income facts for income and insurance coverage pathways, without automatically opening debt, medical-care or material-goods needs.

T8. User asks for a GoFundMe appeal draft: decline content creation and offer only platform setup and distribution instructions.

T9. User needs furniture after a fire: search specified items via charities and optionally offer safe self-directed free-listing search channels; do not claim a live listing or arrange pickup.

T10. Provider rules or source dates conflict: preserve conflict and defer any definitive eligibility claim; ask targeted questions or provide direct-provider confirmation steps.

# AUDIT FINDINGS & OPEN IMPLEMENTATION ISSUES

Resolved in this revision: removed unconditional property/vehicle/asset questions from job-loss intake; clarified program-specific treatment of income, expenses and assets; formalized confirmed-mismatch suppression of recommendations; preserved multi-need, multi-action planning; separated existence, fit and intake status; corrected debt and developer-register heading numbering; added cross-domain tests and a precedence register.

Remaining build gates: consolidate duplicated Case State and ProgramRecord field descriptions (early working schema versus later frozen field names); reconcile Agent 3/4/5 payloads and all enums; validate program-specific eligibility rules and live provider status from authoritative dated sources; confirm tool permissions and approved external discovery routes in watsonx Orchestrate; decide exact persistence/privacy and user-confirmation mechanics; execute acceptance fixtures in the actual IBM environment. These are unresolved implementation tasks, not permission for Bob to invent product decisions.

Audit scope: document-internal product logic and consistency. This revision does NOT constitute a fresh legal or government-benefits rule audit, does not verify current Sacramento availability, and does not certify the IBM build or complete end-to-end tests.

# 29. Developer clarification register — implementation questions and decision gates

Status: OPEN QUESTIONS / NOT APPROVED IMPLEMENTATION DECISIONS. This register records what a developer (including IBM Bob) must request or verify before implementing unresolved behavior. Do not treat questions as authorization to invent defaults. The existing approved design remains authoritative; any conflict is escalated for product-owner review.

## 29.1 Agent orchestration and exact I/O

Confirm final structured input/output contracts for Agents 1 and 2 and any remaining agents not frozen. Define orchestrator invocation order, handoff conditions, repeated calls, cancellation, failures and responsibility for user-visible messages. Existing Agents 3–5 interfaces are a baseline, not proof that every other interface is frozen.

## 29.2 Case State lifecycle and conflict resolution

Confirm state transitions, ownership of updates, rules for proposed versus confirmed versus disputed facts, missing values, persistence, session resume, user corrections, concurrent changes and deletion. Reuse known financial/household facts; do not ask again merely because another assistance domain is activated.

## 29.3 IBM watsonx Orchestrate integration

Identify the actual supervisor/collaborator setup, tools, tool permissions, connectors, storage implementation, environment constraints and deployment method. Do not infer that every conceptual component maps to a new agent or tool. Record which choices require team confirmation.

## 29.4 Knowledge Base evidence, freshness and failure

Specify source allowlist/selection policy, verification timestamps, stale-record handling, conflicting sources, unavailable program funding, network/tool failures, retries and how unverified candidates are labeled. No invented eligibility, availability, processing time or guarantee.

## 29.5 User-facing outputs and plan contract

Finalize the output structure for clarifying questions, program candidates, Action Cards, explanation of uncertainty, action priorities, progress states and saved plans. Clarify how user consent and account creation for saving a plan operate. Avoid adding assistance categories not raised by the user, except previously approved narrowly scoped exceptions.

## 29.6 End-to-end testing and release gates

Create fixtures covering food, housing, utilities, and later agreed domains; missing/conflicting facts; duplicate questions; source conflicts; no verified matches; looming disconnection; future financial difficulty; and cross-domain shared facts. Define expected state mutations, tool calls, candidate statuses, final wording and objective pass/fail criteria.

## 29.7 Source-of-truth and conflicting sections

The current document has overlapping housing and intake descriptions in sections 16, 18–20 and 22. Before implementation, reconcile any inconsistent wording and provide explicit precedence or consolidate approved rules without losing detail. A later section is not automatically more authoritative than an earlier approved rule.

## 29.8 Decision request format

For each unresolved question, log: unique ID, relevant section, exact ambiguity, proposed alternatives (if any), downstream impact, owner, decision status (Approved / Proposed / Pending), decision date and acceptance test. Block only the affected implementation path; do not silently substitute a developer assumption.

# 30. APPROVED — Agent orchestration, contracts and candidate transparency (17 October 2026)

Status: APPROVED. This section supersedes conflicting earlier descriptions of direct agent writes, mandatory all-agent sequential execution, or blanket exclusion of candidates with missing user eligibility facts.

## 30.1 Hybrid orchestration and independent roles

Supervisor/Orchestrator coordinates ten existing specialized agent roles. Run independent tasks concurrently when safe, and dependent tasks in order. Agent 7 reviews intermediate evidence, contradictions and uncertainty; Agent 10 reviews the final plan. Agent 6 prioritizes and sequences actions; Agent 8 assembles the unified plan. Do not add a new auditor agent.

## 30.2 One Case version per evaluation

Each analysis cycle uses a consistent Case snapshot/version. The Orchestrator enforces prerequisites, bounded retries and timeouts. Stale results must not overwrite newer Case changes. Partial failures are explicit; do not present unchecked work as verified.

## 30.3 Agent contracts and write authority

Each agent receives only task-relevant current Case context and upstream outputs, and returns structured result, status, evidence/source references where applicable, and clarification/verification needs. Agents do not write directly to SQL or mutate user-entered action statuses. Application Layer validates and persists approved changes to the existing Case and unified Action Plan.

## 30.4 Separate program evidence from personal eligibility

Track (a) whether program information is supported by reliable/current evidence and (b) whether the user appears eligible, is clearly ineligible on known mandatory criteria, or needs more information. Unknown eligibility is not equivalent to an unverified or nonexistent program. Never imply agency approval or guaranteed availability.

## 30.5 Government programs with missing eligibility facts

For a relevant government program confirmed through an official source, if personal facts are insufficient to assess eligibility, the plan may include a compact potential-options entry with program name, reason it may matter, exactly what needs checking, and an official source link. Do not omit solely because personal eligibility is uncertain. Do not flood the plan with unrelated programs; only user-stated needs and relevant context. The main action plan remains prioritized.

## 30.6 Handling unverifiable and conflicting resources

If the existence/current operation of a program cannot be substantiated, do not label it verified or available. Explicitly flag uncertainty and prefer an official source for user follow-up when one is available. Agent 7 checks intermediate evidence and Agent 10 checks user-facing wording. Treat retrieved web content as untrusted data, not agent instructions.

## 30.7 Case persistence and user-led reassessment

Anonymous users can view a plan during the session, request a one-time email copy without account creation, or end without persistence. Optional email registration saves relevant conversation-provided facts, needs, plan and user statuses under user_id/case_id in SQL. AI remains available in the account. Substantive user-initiated changes or new needs trigger reassessment of the same Case, preserving history and user-set statuses. No separate catalog of rejected programs is required.

RESOLVED / APPROVED: All agent-originated clarification requests route exclusively through Supervisor/Orchestrator. Agents never communicate directly with users. Supervisor checks existing Case facts, consolidates duplicate or overlapping requests, asks each necessary question once via the application UI, and distributes the centrally recorded answer to every relevant agent. This is an existing architecture decision, not an open question.

## 30.8 APPROVED — Single communication gateway and clarification deduplication

Agents must never contact the end user directly or initiate independent user-facing conversations. Each agent submits missing-information requests to Supervisor/Orchestrator in its structured output. Supervisor checks the current Case snapshot and prior user-provided facts, merges equivalent requests across agents, and sends one consolidated, relevant clarification through the UI. The user answers once; Application Layer validates and persists the answer in Case State (for registered users, or temporary session state for anonymous users), then Supervisor shares the updated context with all agents requiring it and resumes only affected tasks. Do not ask questions already answered or collect unrelated facts. This decision is APPROVED and must not be reopened as an unresolved design question.

## 30.9 Architecture decisions already closed — implementation rule

Treat approved decisions in Section 30 and earlier approved Blueprint decisions as the source of truth over any older OPEN-question register wording. Future implementation review must identify genuinely unresolved engineering details only; do not request renewed approval for single-Supervisor communication, centralized writes, unified Case/Plan, or duplicate-question consolidation. If conflicting legacy language remains elsewhere in this document, the approved rules in this section take precedence pending editorial consolidation.
