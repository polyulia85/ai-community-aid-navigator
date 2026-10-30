This document consolidates agreed RAG decisions and the proposed technical implementation. RAG is part of the Navigator architecture, not a standalone AI agent. It retrieves and checks publicly available information; it does not guarantee funding, approval, or receipt of assistance.

# 1. Agreed design principles

| **Principle**            | **Decision**                                                                                                                                                                       |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Unit of data             | One Knowledge Base record represents one specific program or service, not an entire organization.                                                                                  |
| Independent statuses     | Verification Status measures evidence quality; Availability Status describes known published availability. Verified does not mean assistance is guaranteed.                        |
| Incomplete records       | The Knowledge Base retains incomplete or conflicting records, but Navigator never presents disputed details as established facts.                                                  |
| Source authority         | Authority is assessed per claim. Program rules and local operating hours may be best supported by different competent sources.                                                     |
| Field-level verification | Significant fields carry value, source, verification date, and status. A conflict in one field does not invalidate other fields.                                                   |
| Request-time checking    | For new resource recommendations or material updates, the system attempts to recheck relevant published information. Routine conversational turns do not trigger full site checks. |
| No mandatory daily crawl | Periodic background refresh may be added later but is not required for the MVP.                                                                                                    |
| Conflict resolution      | An unresolved discrepancy does not always exclude a program: the plan can recommend confirming the disputed condition without claiming eligibility.                                |
| Hybrid retrieval         | Hybrid Retrieval is selected: structured filters plus semantic search; semantic relevance is not eligibility.                                                                      |

# 2. Product responsibility boundaries

Navigator guides people to resources, explains published conditions, and organizes a personalized action plan. It does not replace 211, government agencies, or professionals; make official eligibility decisions; automatically submit applications; or guarantee assistance. Unpublished changes cannot be reliably detected, so source transparency and honest verification limits are essential.

# 3. Technical components

| **Component**               | **Purpose**                                                                                             |
|-----------------------------|---------------------------------------------------------------------------------------------------------|
| Verified Knowledge Base     | Structured program records with field-level evidence and provenance.                                    |
| RAG / Retrieval Service     | Structured and semantic search returning candidate programs with metadata.                              |
| Source Verification Service | Where technically possible, retrieves linked authoritative sources and compares relevant claims.        |
| Knowledge Update Process    | Updates verified field changes, evidence, and verification dates; preserves significant change history. |
| Orchestrator                | Coordinates execution, retries, failures, and escalation; agents do not directly command each other.    |

# 4. Request processing pipeline

| **\#** | **Component**                  | **Action**                                                                                          |
|--------|--------------------------------|-----------------------------------------------------------------------------------------------------|
| 1      | Agents 1–2                     | Identify and confirm needs, necessary case facts, and initial urgency.                              |
| 2      | Orchestrator                   | Pass only the minimum case information needed for retrieval.                                        |
| 3      | Agent 3 + RAG                  | Find candidate programs via structured filtering and semantic retrieval.                            |
| 4      | Agent 4                        | Match candidates to Needs and Case Facts; no final eligibility decision.                            |
| 5      | Agent 5 + Verification Service | Attempt to verify relevant conditions, timelines, documents, geography, and published availability. |
| 6      | Agent 7 (cross-cutting)        | Flag unknown, conflicting, and insufficiently supported claims.                                     |
| 7      | Orchestrator                   | Route targeted rechecks, clarification, or safe escalation when necessary.                          |
| 8      | Agent 6                        | Determine priorities, dependencies, official deadlines, and parallel steps.                         |
| 9      | Agent 8                        | Assemble the structured Crisis Action Plan.                                                         |
| 10     | Agent 10                       | Review the completed plan for material errors and unsupported claims.                               |
| 11     | Agent 9                        | Explain the plan and assist with Action Cards; do not invent facts.                                 |

# 5. Program record fields

| **Field**                         | **Contents**                                                          |
|-----------------------------------|-----------------------------------------------------------------------|
| Resource ID                       | Unique record identifier                                              |
| Organization Name / Program Name  | Provider and specific program                                         |
| Assistance Category / Description | Aid category and service description                                  |
| Geographic Coverage               | Service area                                                          |
| Eligibility Requirements          | Rules, limits, and exclusions                                         |
| Required Documents                | Documents for application                                             |
| Application Process / Contacts    | Application steps, contacts, official website                         |
| Operating Hours                   | Operating and intake hours                                            |
| Official Deadlines                | Verified official deadlines                                           |
| Estimated Processing Time         | Published estimates, not guarantees                                   |
| Availability Status               | Confirmed Open / Temporarily Closed / Unknown, with supporting source |
| Source Reference / Last Verified  | Evidence link and verification date                                   |
| Verification Status               | Verified / Needs Review / Conflicting / Unverified                    |

# 6. Source and conflict rules

| **Situation**                  | **Rule**                                                                                                                |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Competent primary authority    | Use the body setting program rules for eligibility; local operator/provider for local intake details.                   |
| Directories, including 211     | Useful for discovery and contacts; a listing does not prove live funding or actual receipt of aid.                      |
| Research and community reports | May trigger review but do not establish official rules or a program closure.                                            |
| Conflicts                      | Compare jurisdiction, effective period, authority, and dates; unresolved claims receive field-level Conflicting status. |
| Unknown vs. Conflicting        | No published value is Unknown; incompatible published values are Conflicting.                                           |
| Plan implications              | Add a “confirm with provider” action for material uncertainty; do not claim eligibility without support.                |

# 7. Request-time verification and updates

When resources are being selected, the system retrieves relevant records, attempts to access linked sources, compares material published conditions, and routes detected changes for verification. Confirmed changes update the Knowledge Base. A failed website request does not mean a program has closed. Parallel requests, timeouts, and limiting checks to relevant programs may reduce latency. Exact caching and repeat-check intervals remain implementation decisions.

# 8. Uncertainty and failure handling

| **Situation**                        | **Response**                                                                             |
|--------------------------------------|------------------------------------------------------------------------------------------|
| Source reachable; details agree      | Use supported information with provenance.                                               |
| Source reachable; details changed    | Check applicability and reliability, then update the affected field.                     |
| Source unreachable                   | Do not infer closure; disclose limits of stored data or withhold it for critical claims. |
| Sources disagree                     | Flag the field; seek authoritative clarification or ask user to confirm with provider.   |
| No published data                    | Mark Unknown; do not invent a value.                                                     |
| Possible fit but eligibility unclear | Recommend contacting the organization; do not declare the user eligible.                 |

# 9. Outstanding design decisions

- Whether the Knowledge Base will store full official documents/chunks alongside structured program cards remains undecided.

- Storage/indexing schema, vector database, embedding model, and ranking implementation are not selected.

- Specific timeouts, caching, rate limits, and optional background refresh cadence remain undefined.

- The Sacramento pilot program set and initial ingestion/manual validation process remain implementation work.

- Automated site-change updates need testing to avoid storing incorrectly extracted program rules.

# 10. Decision status

AGREED: Knowledge Base principles, independent statuses, field-level verification, claim-specific source authority, request-time verification, conflict handling, and Hybrid Retrieval. PROPOSED IMPLEMENTATION: four internal technical functions and the pipeline described here. OPEN: document storage, technical stack, and operational parameters. This is the complete record of current RAG decisions, not yet a final build-ready engineering specification.
