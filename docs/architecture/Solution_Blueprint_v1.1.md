Consolidated master draft v1.1 • 17 October 2026 • v1.0 preserved; v1.1 decisions integrated; pending choices remain open

Purpose: one shared, source-grounded architecture for the five-person team before prototype development. This document consolidates existing design artifacts and the approved RAG specification. It is not a claim that all implementation decisions are finalized.

# 1. Product purpose, boundaries and success criterion

**Problem:** Families facing sudden financial crises must navigate multiple needs, agencies, eligibility rules, deadlines and follow-ups while under stress.

**Core value:** Convert a free-form crisis story into a living, personalized Crisis Action Plan: priorities, verified referrals, actions, official deadlines versus user targets, dependencies, progress and targeted updates.

**Pilot:** Sacramento residents and families; initial scenario: job loss, two children, imminent rent payment and food insecurity.

**Not our role:** Not a replacement for 211 or service providers. No official eligibility determination, guaranteed assistance, automatic applications, legal/medical professional advice or unsupported claims of live funding availability.

**Success for prototype:** Demonstrate an understandable, traceable plan whose actions link to sources, whose uncertainties are visible and whose progress changes only on user confirmation.

# 2. End-to-end user journey

**Step 1 — Tell the story:** No registration required before the initial story. Preserve original story separately where storage is permitted.

**Step 2 — Confirm needs:** Agent 1 extracts proposed needs; user confirms, edits or removes them.

**Step 3 — Clarify facts:** Agent 2 asks only necessary questions, distinguishes confirmed facts from assumptions and captures urgency.

**Step 4 — Find and check options:** Agent 3 retrieves candidate programs; Agent 4 matches; Agent 5 checks published requirements; Agent 7 flags gaps and contradictions.

**Step 5 — Build and validate:** Agent 6 prioritizes and sequences; Agent 8 builds plan; Agent 10 independently critiques; Orchestrator handles revisions.

**Step 6 — Use and update:** Agent 9 and UI expose Action Cards. User sets status; material changes in confirmed needs/facts trigger targeted re-evaluation. Account offered when saving the case.

**v1.1 — Optional feedback (APPROVED)**

Provide a low-friction, optional Feedback / Report an Issue control; no forced questionnaire or pop-up. User-reported program errors are leads for verification, not automatic Knowledge Base changes.

# 3. System architecture and control flow

**System flow:** User / UI → Agents 1–2 → Orchestrator + Case State → Agent 3 / Hybrid RAG → Agent 4 → Agent 5 → Agent 6 → Agent 8 → Agent 10 → Plan / Action Cards → Agent 9 / UI. Agent 7 checks quality throughout; safety/privacy applies across the system.

**Orchestrator:** Central rule-guided dispatcher; selects agents and tools, handles statuses, retries, failure, escalation and review. Agents do not command one another directly.

**Case State:** Shared source of truth for confirmed needs, facts, urgency, resource references, plan, cards, time metadata and user-confirmed progress. Original story retained separately for traceability.

**Failure path:** Retry → alternate tool/path if available → controlled partial result or escalation. Do not silently invent missing information.

**Safety path:** Urgent/safety-sensitive situations can route to a separate Verified Emergency Resource Directory and appropriate human/organization channels.

**v1.1 — Testing trace (APPROVED)**

During MVP tests, trace failures to existing processing stages via Orchestrator, Agent 7 and Agent 10; do not create an additional debugging or QA agent. Bounded retries and transparent partial results apply; precise limits remain pending.

# 4. Ten agents — existing approved responsibilities

**Agent 1 — Crisis Understanding:** Understand story; propose needs for user confirmation.

**Agent 2 — Case Analysis & Clarification:** Identify missing facts and urgency; ask targeted questions.

**Agent 3 — Resource Retrieval:** Use RAG and Verified Knowledge Base to answer “What exists?”

**Agent 4 — Resource Matching:** Relate candidates to confirmed case needs/facts; tentative match only.

**Agent 5 — Resource Verification:** Check published geography, requirements, restrictions, documents, deadlines, freshness and availability claims; not official eligibility.

**Agent 6 — Action Planning & Prioritization:** Set urgency, dependencies, parallel tasks and sequence of actions.

**Agent 7 — Quality & Uncertainty Controller:** Cross-cutting detection of unsupported, conflicting, stale or missing evidence; reports to Orchestrator.

**Agent 8 — Crisis Action Plan Builder:** Assemble structured plan from validated inputs without new claims.

**Agent 9 — Personal Crisis Navigation:** User-facing help with plan, Action Cards and progress; no unilateral plan rewrite.

**Agent 10 — Plan Validation & Critique:** Independent PASS/FLAG review of assembled plan; routed via Orchestrator.

**Implementation note:** Ten logical roles are the full architecture, not a commitment to deploy ten independent AI services in the MVP.

# 5. RAG and Verified Knowledge Base — approved design

**Retrieval method — APPROVED:** Hybrid Retrieval = structured field filtering + semantic search. Semantic similarity alone is not proof of eligibility.

**Record granularity — APPROVED:** One Knowledge Base record per assistance program/service, not one per organization.

**Core record fields:** Resource ID, organization, program, category, description, geography, requirements, required documents, application steps, contacts, hours, official deadlines, processing time, availability, source and verification metadata.

**Field-level evidence — APPROVED:** Important claims have value, source, checked-at timestamp and verification status. Verification status is independent of availability status.

**Source authority — APPROVED:** Authority depends on the claim: governing agency for statewide rules; provider for its local operations; directories such as 211 as supporting discovery. Community reports are leads, not proof.

**Request-time verification — APPROVED PRINCIPLE:** When selecting new programs or materially refreshing resources, attempt to compare relevant published authoritative sources against stored facts; show failed checks honestly. Do not require a daily crawl of the whole KB.

**Conflicts — APPROVED:** Investigate scope/date/authority. If unresolved, mark field Conflicting, do not assert eligibility, and offer “contact provider to clarify” as a possible action. Missing information is Unknown, not Conflicting.

**Uncertainty and availability:** Published rules do not prove real-world availability, funding, acceptance or approval. A source being reachable does not establish that every field was verified.

**Open implementation choices:** Whether to retain full official document text alongside structured cards; exact storage/indexing/embedding stack; caching, timeouts, ranking, initial Sacramento corpus and ingestion validation.

**v1.1 — Preliminary Resource Matching statuses (APPROVED)**

Agent 4 uses potential_match, supported_match, confirmed_mismatch and insufficient_information. These are matching assessments, not official eligibility or field verification statuses.

**v1.1 — Missing user information (APPROVED)**

If income or other eligibility details are missing or declined, a verified, relevant program may remain a potential option, with the unassessed requirement explicitly identified and a provider-confirmation action. Do not present the user as eligible.

Implementation reference (APPROVED PRINCIPLES): The separate RAG Technical Architecture remains the authoritative detailed specification; it is not replaced or rewritten here. The KB stores one record per program/service with field-level claim evidence. Program availability, claim verification, and case-specific preliminary matching are three independent dimensions.

Program data categories (DESIGN REQUIREMENT): identity and provider; aid type/description; geography; published eligibility criteria and exclusions; required application documents; application channels and contact; hours; official deadlines; published processing estimates; reported availability; source references and claim-level verification timestamps/status. Unknown values remain explicit; conflicting claims and their sources are preserved.

Priority separation (APPROVED): case urgency (immediate/high/normal/unknown), user priority, official deadline, action dependencies, and computed action order are separate concepts. No fixed universal numerical weighting has been approved.

# 6. Data, state and security boundaries

**Case data objects — conceptual:** Case ID; original story; confirmed/unconfirmed facts; needs; urgency; candidate/matched/verified resource references; plan versions; action cards; status and timestamp history; source evidence; account link if saved.

**User-controlled progress:** Not Started / In Progress / Waiting / Completed / Need Help. AI must never infer completion from conversation alone.

**Three time categories:** Official Deadline (verified source); My Target Date (user-set); Estimated Processing Time (non-guaranteed estimate). Keep distinct in storage and UI.

**Plan re-evaluation:** Only confirmed material changes to needs/facts trigger dependency-aware re-evaluation of affected actions. Simple completion changes progress without rebuilding entire plan.

**Security & Privacy Layer:** Data minimization, avoid unnecessary SSN/bank/card collection, masking, least privilege, access controls, encryption, audit, retention/deletion rules. Implementation specifics and consent/storage flows remain to be finalized.

**Access and accessibility:** No account before initial story; account when saving. Shared case permissions may be post-MVP. Accessible UI and speech input/output are architectural options, not guaranteed MVP deliverables.

**v1.1 — Case State refinements (WORKING CONTRACT)**

Capture needs with urgency immediate/high/normal/unknown and reason; separately capture user_priority when stated. Facts may be proposed, confirmed, disputed or superseded. Include open questions, story reference, resource references, plan reference and progress. User confirmation is for the case summary and material corrections, not a forced confirmation of every individual fact. Exact field schemas and transitions remain in the companion technical specification.

**v1.1 — Ordering versus urgency (APPROVED PRINCIPLE)**

Agent 2 captures urgency; user_priority reflects user preference; Agent 6 determines action ordering using urgency, dependencies and preference. Do not conflate these concepts.

Case State contract reference (WORKING v0.3): Case ID/status/timestamps/story reference; needs with confirmation status, urgency, optional user priority and reported deadline; facts with proposed/confirmed/disputed/superseded states; open questions; program references; plan reference; user-confirmed progress; optional account reference. See Technical Design for proposed field names and validation boundaries.

User confirmation and updates (APPROVED): confirm or edit a concise needs/facts summary rather than mandatory confirmation of every field. Unknown income or unanswered nonessential questions must not automatically suppress useful possible resources. Material confirmed changes trigger targeted plan review; progress updates alone do not rebuild the plan.

# 7. Non-agent rules and supporting components

**Deterministic / rule-based mechanisms:** Orchestration; time handling; dependency sequencing; safety escalation; sensitive-data handling; Action Card configuration; handoff to Agent 9; progress tracking; targeted re-evaluation; account/case creation.

**Infrastructure components:** Orchestrator; Case Database; Original Story record; Verified Knowledge Base; RAG Retrieval Service; Verified Emergency Directory; Authentication; optional Permissions; Security/Privacy; Presentation/UI; Quick Help UI; optional accessibility/multimodal layer.

**Action Card concept:** Each card must represent a concrete plan action with reason/priority, next step, linked resource, source/uncertainty, dependencies, time type and user-controlled status. Exact field schema and UX remain pending.

**v1.1 — Additional supporting functions (WORKING IMPLEMENTATION)**

The RAG technical specification also describes a Source Verification Service and Knowledge Update Process. These are supporting technical functions, not new AI agents. Feedback reports require independent checking before material Knowledge Base changes.

Feedback / Report an Issue (APPROVED LIMITED ADDITION — Hisham): optional, unobtrusive user-facing control; never a mandatory popup or survey. A user report about a program is a lead for review, not permission to overwrite verified KB claims.

Error-stage tracing (APPROVED LIMITED ADDITION — Hisham): for MVP tests, capture which existing stage failed using Orchestrator records and Agent 7/10 findings. No extra diagnostic agent.

# 8. MVP build slice — proposed, not yet approved

**Minimum demonstrable journey:** Text story → confirm needs/facts → search curated Sacramento programs → verify or explicitly mark source uncertainty → prioritized plan → Action Cards → manual status updates → one material-change re-evaluation.

**Scope discipline:** Implement logical agent roles with pragmatic services/prompts and rules; do not require ten separately deployed agents. Use a limited manually reviewed program set for the demo.

**Suggested exclusions until approved:** Automated benefit applications, funding/eligibility guarantees, broad statewide coverage, live provider inventory, complex shared access, full speech stack and comprehensive crawling.

**Evidence for evaluation:** Trace each recommended action to user need + program source; demonstrate at least one conflicting/unknown field, one source failure and one plan change.

**Status:** PROPOSED: team must confirm exact MVP boundaries, stack, and owner assignments after reviewing this Blueprint.

**v1.1 — Acceptance testing (PARTIALLY APPROVED)**

Begin with approximately 5–7 synthetic crisis scenarios as a practical starting point, not a hard cap. Define expected results before running each case; compare expected/actual, record PASS/FAIL, defects and retests. Cover multi-need cases, unknown/conflicting evidence, source failures, changed user facts, a relevant program outside the initial KB, declined income, safety/privacy and source traceability. Independent spot checks should use authoritative sources. No extra testing agent or mandatory pytest infrastructure.

Acceptance testing (PARTIALLY APPROVED — Hisham): begin with approximately 5–7 synthetic cases as a practical starting set, not a ceiling. Include unknown income, conflicting deadline, unreachable source, known mismatch, changed circumstances, privacy/safety and mixed valid/flagged action plans. Record expected versus actual and PASS/FAIL; re-test corrections.

Plan Release Validator (APPROVED WITH MODIFICATIONS — Slava): Agent 10 flags unsupported/misleading claims, concealed critical conflicts or guarantees, not entire useful options merely because a field is unknown. Orchestrator repairs specific cards and revalidates within bounded attempts; show qualified partial options where safe.

# 9. Open questions and decision gates

**Research dependency:** Yogesh Research \#2: deliverable and scope not yet confirmed; no findings attributed. Integrate only evidence that changes a requirement, risk or design decision.

**Architecture gaps:** Exact Case State schema and transitions; Orchestrator input/output contracts; Action Card schema; agent/tool interfaces; error taxonomy and escalation thresholds.

**RAG gaps:** Document text retention, retrieval indexes, corpus selection, ranking, field extraction validation, verification latency/cache policy and site access failures.

**Prototype gaps:** UI screen flow; privacy and data retention implementation; MVP technology choices; demo test cases; responsibilities and build sequencing.

**Decision gate before coding:** One-page system diagram + core data schema + user flow + MVP scope + failure/safety paths reviewed by team; then ask IBM mentor for focused design sanity check.

**v1.1 — Technical specification linkage (WORKING)**

Case State, Resource/Evidence, Action Plan, common agent envelope, input/output contracts and validation rules are developed in the separate Technical Design & Agent Data Contracts document. Their presence there does not automatically mean all implementation details are approved.

# 10. Research integration and source register

**Research \#1 — Existing navigation:** 211 Sacramento and official program research show existing referral and follow-up functions; Navigator differentiates through a cross-needs living action plan, not by claiming 211 does nothing.

**Research \#2 — Yogesh:** PENDING; scope and results must be confirmed.

**Research \#3 — Crisis support:** Trauma-informed boundaries and emergency/escalation routing; no substitute for crisis professionals.

**Research \#4 — Community signals:** Exploratory social/community feedback suggests friction in financial assistance and applications; nonrepresentative data, not evidence of adoption.

**Research \#5 — Verification:** Official guidance and provider pages may conflict on local details; field-level provenance and uncertainty are required.

**Research \#6 — Crowdfunding:** Potential supplementary path; lower MVP priority, no promise of donations.

**Source documents used:** AI Agents & Responsibilities; Updated System Functions; System Algorithms & Rules; System Components, Data & Infrastructure; Week 3 Solution Definition & MVP; RAG Technical Architecture (EN/RU); Consolidated Research Review (EN/RU).

# 11. Team review protocol

**How to review:** Review the single Blueprint first. Comment on incorrect assumptions, missing connections, unresolved decisions and implementation feasibility. Do not treat proposed MVP choices as approved.

**Change control:** Record every change as Approved / Proposed / Pending, its reason, affected component and decision owner. Avoid silently rewriting previously agreed roles.

Next deliverable: Team review of this consolidated Master v1.1, then finalize implementation contracts and prototype sequencing.

**v1.1 — Decision Addendum: Proposal \#6, Plan Release Validation (APPROVED WITH MODIFICATIONS; 17 October 2026)**

Agent 10 reviews the assembled plan with PASS/FLAG; Agent 7 detects evidence and uncertainty issues; Orchestrator routes corrections. The validator blocks unsupported or misleading claims, not whole potentially useful recommendations solely because some user information or program fields are unknown. No additional agent or independent validator service.

**Plan release rules**

A verified potentially relevant program can appear with explicit unknown eligibility conditions. Separate evidence quality, user eligibility uncertainty and real-world availability. If a material published deadline conflicts, prominently flag it and add a provider-confirmation action without asserting a disputed value. If a confirmed program requirement conflicts with confirmed user facts, do not label it a suitable match. Exact severity thresholds and retry limits remain pending.

**Change-control record**

Proposal \#6: APPROVED WITH MODIFICATIONS. Hisham feedback control and MVP test refinements: limited approved additions. All unselected stack choices and exact implementation parameters remain PROPOSED or PENDING. Preserve the ten existing agent roles.
