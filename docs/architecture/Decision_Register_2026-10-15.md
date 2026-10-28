October 15, 2026 \| Applied Intelligence Group \| Working document for team review

# Purpose and Status

This document records the outcomes of discussions on ten proposals concerning Solution Blueprint v1.0 and the RAG Technical Architecture. It does NOT amend the source documents and is NOT a newly approved architecture revision. Team members may provide comments through October 17; the agreed items can then be incorporated into the relevant documents.

Status definitions: “Approved” — accepted in principle; “Partially Approved” — accepted with limitations; “Already Covered” — no separate change required; “Not Approved” — do not incorporate; “Under Discussion” — decision remains open.

# Where Changes Belong

| Document                   | Scope                                                                                                                                   |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| Solution Blueprint v1.0    | User journey, responsibilities of existing agents, Orchestrator, Action Cards, Crisis Action Plan, MVP scenarios, and testing criteria. |
| RAG Technical Architecture | Program and evidence structures, hybrid retrieval, source verification, Unknown/Conflicting states, updates, and safe data retrieval.   |
| Both documents             | Only when a decision changes both the product contract and the retrieval/verification mechanism; avoid duplicating details.             |

# Decisions on Proposals \#1–10

## 01. Machine-Readable Data Contracts

**Status: Approved in principle \| Target: Blueprint + RAG**

Document four minimal Data Contracts: Case State, Action Card, Orchestrator command/result, and Evidence & Conflict Record. Adapt fields to actual IBM platform capabilities; do not treat draft schemas as a rigid standard before implementation.

**Potential sections: Blueprint: §3, §6–7; RAG: §3–6 — evidence/contract fields.**

## 02. Claim Ledger / Claim History

**Status: Partially Approved \| Target: RAG**

Use a compact evidence and conflict record for material claims. Do not build a fully versioned historical Claim Ledger for the MVP.

**Potential sections: RAG: §5–7; Blueprint: §5 — traceability principle only.**

## 03. Consequence-Aware Uncertainty

**Status: Approved with limitations \| Target: RAG + Blueprint**

Handle Unknown/Conflicting information with regard to its potential consequences for a recommendation; clearly explain uncertainty and the safe next step. Implement this through existing RAG, Supervisor/Orchestrator, and agent roles, without adding an agent. Do not automatically exclude a program merely because information is unknown.

**Potential sections: RAG: §6–8; Blueprint: §4–5.**

## 04. Conflict Test Cases

**Status: Already Covered \| Target: Blueprint**

Add concrete conflict and uncertainty examples to the existing demonstration/acceptance scenarios; no separate feature or subsystem is needed.

**Potential sections: Blueprint: §8–9.**

## 05. “Start Here” Screen with Three Cards

**Status: Not Approved \| Target: Blueprint**

Do not hide the complete Crisis Action Plan behind an extra click. The full personalized plan must be visible immediately; actions are already prioritized, and the most important ones can be highlighted visually.

**Potential sections: Blueprint: §2, §7; retain the current principle.**

## 06. Deterministic Plan-Release Validator

**Status: Under Discussion \| Target: Blueprint + RAG (if approved)**

Do not approve a separate release gate yet. Clarify which checks are genuinely necessary and whether they could block the full plan or remove programs marked Unknown/Conflicting. Slav did not explicitly propose that such programs must be excluded.

**Potential sections: Blueprint: §3–4, §7; RAG: §8 — only after a decision.**

## 07. Passing an Evidence Bundle Through All Agents

**Status: Not Approved as a separate architecture \| Target: Blueprint + RAG**

Do not require an end-to-end Evidence Bundle for every agent. Evidence is stored and verified within RAG; the necessary fields pass through the Orchestrator; the Supervisor and review roles oversee quality.

**Potential sections: Blueprint: §3–5; RAG: §3–6.**

## 08. Safe Source Retrieval and Updates

**Status: Partially Approved \| Target: RAG**

Include reasonable safeguards for retrieving information within the existing RAG process. Do not impose a strict source allowlist, mandatory manual approval for every material Knowledge Base update, or a Pending state caused solely by the absence of such approval.

**Potential sections: RAG: §6–8.**

## 09. Initial Sacramento Corpus and External Discovery

**Status: Approved with clarifications \| Target: RAG + Blueprint**

A small verified set of Sacramento programs is a starting point, not a coverage ceiling. The system must discover relevant programs beyond the initial Knowledge Base; include at least one such case in the demo/tests. Do not require separate manual researcher and reviewer roles for each record or perpetual manual approval.

**Potential sections: RAG: §3–7; Blueprint: §5, §8–9.**

## 10. Independent MVP Acceptance Testing

**Status: Partially Approved \| Target: Blueprint**

Existing RAG Verification, Agent 7, Agent 10, and the Orchestrator already provide internal quality control. Supplement this with lightweight independent testing: approximately 5–7 synthetic crisis scenarios with expected outcomes; needs identification, program relevance, verification of key claims against authoritative primary sources, plan completeness, Unknown/Conflicting information, unavailable sources, changes in circumstances, and discovery beyond the initial Knowledge Base. Record PASS/FAIL results, issues, and retests. Structured manual testing is sufficient; pytest and comparison with a static resource directory are optional. Do not add agents, dedicated infrastructure, or effort estimates. Tests assess the Navigator’s quality, not users’ honesty or perceived deservingness.

**Potential sections: Blueprint: §8–9; no new RAG architecture is required.**

# Constraints and Unchanged Principles

- The Navigator organizes needs and produces a complete personalized Crisis Action Plan; it does not replace 211, directly provide assistance, or guarantee benefits or eligibility.

- Unknown or conflicting program requirements must be explicitly identified; a program is not excluded solely because some requirements remain unknown.

- No new agents are added; retain the ten existing logical roles and Orchestrator control.

- Existing Blueprint and RAG decisions remain in force unless an agreed change is explicitly identified above. Blueprint §8 remains proposed until approved by the team.

# Open Questions and Next Steps

1\. Resolve Proposal \#6 (validator / release gate).

2\. Collect feedback from the rest of the team on every item by Saturday, October 17, 2026.

3\. After team review, finalize Approved / Proposed / Pending statuses, and only then incorporate approved changes into the Blueprint and/or RAG Technical Architecture. Do not treat silence as individual approval; if no further feedback is received, the team will proceed based on the documented decisions.

# Source Materials

IBM_Solution_Blueprint (1).docx — Solution Blueprint v1.0 (Oct 11, 2026)

IBM_RAG_Technical_Architecture_EN(1).docx — RAG Technical Architecture (Oct 11, 2026)

Blueprint_RAG_Proposed_Additions.docx — Slav’s proposals

Note: the previously created addendum for Proposal \#10 does not constitute an amendment to the original Blueprint; the current wording in this register contains no time estimate.
