"""Shared JSON Contracts v1.1 (Oct 27, 2026; built on v1.0, frozen Oct 23) as Python constants.

One place for every allowed value. If the contract changes, only this file changes.
"""

SCHEMA_VERSION = "1.0"
TIMEOUT_SECONDS = 30  # S7, contract 5.2

# 2.1 / 2.2 — fields every request and every result must carry
REQUEST_FIELDS = (
    "request_id", "run_id", "case_id", "case_version", "schema_version",
    "role_id", "task_type", "task_scope", "allowed_case_facts",
    "upstream_result_refs", "source_policy", "correlation_id", "payload",
)
RESULT_FIELDS = (
    "request_id", "run_id", "case_id", "case_version", "correlation_id",
    "agent_id", "schema_version", "status", "result", "issues",
    "clarification_requests", "evidence_refs", "generated_at", "is_mock",
)
ECHO_FIELDS = ("request_id", "run_id", "case_id", "correlation_id")  # S2

ROLES = ("agent_1", "agent_2", "agent_3", "agent_4", "agent_5",
         "agent_6", "agent_7", "agent_8", "agent_10")

TASK_TYPES = {
    "agent_1": ("understand_story", "parse_clarification_answer"),
    "agent_2": ("clarify_case",),
    "agent_3": ("retrieve_candidates",),
    "agent_4": ("match_resources",),
    "agent_5": ("verify_resources",),
    "agent_6": ("prioritize_actions",),
    "agent_7": ("review_stage",),
    "agent_8": ("build_plan",),
    "agent_10": ("validate_plan",),
}

# 3.4 and 3.6 — enums. Key = field name as it appears in JSON.
ENUMS = {
    "status": ("completed", "partial", "needs_clarification", "failed"),
    "severity": ("info", "warning", "critical"),
    "category": ("food_assistance", "housing_assistance", "income_assistance",
                 "utility_assistance", "medical_health_coverage", "debt_hardship",
                 "material_in_kind", "crowdfunding_guidance", "other_unlisted"),
    "confirmation_status": ("proposed", "confirmed", "disputed", "superseded"),
    "urgency": ("immediate", "high", "normal", "unknown"),
    "source": ("user_statement", "user_confirmed", "system_derived"),
    "necessity_level": ("required_for_decision", "helpful"),
    "match_status": ("potential_match", "supported_match",
                     "confirmed_mismatch", "insufficient_information"),
    "verification_status": ("verified", "needs_review", "conflicting", "unverified"),
    "availability": ("confirmed_open", "temporarily_closed", "unknown"),
    "order_group": ("first", "parallel", "later"),
    "progress_status": ("not_started", "in_progress", "contacted_applied",
                        "waiting_for_response", "completed_received", "unsuccessful"),
    "verdict": ("PASS", "FLAG"),
    "stage_assessment": ("clear", "issues_found"),
}

# Fields whose values are free text in some places (e.g. Agent 5 claim for
# "availability" carries evidence text). S4 checks these only inside the
# objects named here.
ENUM_ONLY_IN = {
    "availability": ("program_availability",),
    "source": ("factual_claims", "case_facts", "allowed_case_facts"),
}

# S9 — field names that must never appear (exact names, not substrings)
FORBIDDEN_FIELDS = {
    "ssn", "social_security_number", "date_of_birth", "dob",
    "bank_account", "bank_account_number", "routing_number",
    "card_number", "credit_card_number", "cvv",
}

# Per-role, per-task_type required result fields (FIX 5).
# Structure: RESULT_REQUIRED[role_id][task_type] = {
#   "result": [top-level keys that must be present in result{}],
#   "lists":  [which of those keys must be a list],
#   <list_key>: [required keys of each item in that list],
# }
# Rules (contract §2.4):
#   "or null" fields are required as keys (value may be null).
#   Only Need.subcategory (§3.4) and Agent 6 suggested_priority (§4.6)
#   are truly optional (may be absent from the object).
#   Lists with no item-key entry have no required item structure checked.
RESULT_REQUIRED = {
    "agent_1": {
        "understand_story": {
            "result": ["narrative_summary", "triggering_events", "proposed_needs",
                       "factual_claims", "ambiguity_flags",
                       "safety_or_official_deadline_flags"],
            "lists":  ["triggering_events", "proposed_needs", "factual_claims",
                       "ambiguity_flags", "safety_or_official_deadline_flags"],
            "proposed_needs":  ["need_id", "category", "description",
                                "original_quote", "confirmation_status",
                                "user_reported", "urgency", "urgency_reason",
                                "user_priority"],
            "factual_claims":  ["fact_id", "field", "value",
                                "confirmation_status", "source", "time_context"],
            "ambiguity_flags": ["field", "quote", "note"],
            "safety_or_official_deadline_flags": ["type", "quote", "note"],
        },
        "parse_clarification_answer": {
            "result": ["factual_claims"],
            "lists":  ["factual_claims"],
            "factual_claims": ["fact_id", "field", "value",
                               "confirmation_status", "source", "time_context"],
        },
    },
    "agent_2": {
        "clarify_case": {
            "result": ["need_updates", "optional_food_check"],
            "lists":  ["need_updates"],
            "need_updates": ["need_id", "urgency", "urgency_reason"],
        },
    },
    "agent_3": {
        "retrieve_candidates": {
            "result": ["candidate_programs", "retrieval_notes"],
            "lists":  ["candidate_programs", "retrieval_notes"],
            "candidate_programs": ["program_id", "matched_need_ids",
                                   "retrieval_reason", "source_refs", "missing_fields"],
        },
    },
    "agent_4": {
        "match_resources": {
            "result": ["matches"],
            "lists":  ["matches"],
            "matches": ["program_id", "need_ids", "match_status",
                        "matched_criteria", "missing_case_facts",
                        "mismatch_criteria", "evidence_refs", "explanation"],
        },
    },
    "agent_5": {
        "verify_resources": {
            "result": ["checked_claims", "update_proposals", "unresolved_questions"],
            "lists":  ["checked_claims", "update_proposals", "unresolved_questions"],
            "checked_claims": ["program_id", "field_path", "claim_value",
                               "verification_status", "evidence_refs",
                               "checked_at", "issue"],
            "update_proposals": ["program_id", "field_path", "proposed_value",
                                 "evidence_refs", "reason"],
        },
    },
    "agent_6": {
        "prioritize_actions": {
            "result": ["proposed_actions"],
            "lists":  ["proposed_actions"],
            # suggested_priority is truly optional (§4.6: "optional"); all others "or null" = required
            "proposed_actions": ["action_id", "need_id", "program_id",
                                 "order_group", "rationale", "dependency_ids",
                                 "official_deadline", "user_target_date",
                                 "estimated_processing_time",
                                 "evidence_refs", "uncertainty_notes",
                                 "user_override_allowed"],
        },
    },
    "agent_7": {
        "review_stage": {
            "result": ["stage_assessment", "findings"],
            "lists":  ["findings"],
            "findings": ["finding_id", "rule_id", "severity",
                         "program_id", "need_id", "field_path",
                         "evidence_refs", "description", "recommended_action"],
        },
    },
    "agent_8": {
        "build_plan": {
            "result": ["plan_version", "action_cards", "potential_options", "coverage_gaps"],
            "lists":  ["action_cards", "potential_options", "coverage_gaps"],
            "action_cards": ["card_id", "source_action_ids", "related_need_ids",
                             "program_id", "action_title", "reason", "next_step",
                             "priority_reason", "order_group", "dependency_card_ids",
                             "source_refs", "uncertainty_notes",
                             "official_deadline", "user_target_date",
                             "processing_estimate", "progress_status"],
            "potential_options": ["program_id", "program_name",
                                  "why_it_may_matter", "what_needs_checking",
                                  "official_link"],
            "coverage_gaps": ["need_id", "note"],
        },
    },
    "agent_10": {
        "validate_plan": {
            "result": ["verdict", "repair_round", "flags", "passed_card_ids"],
            "lists":  ["flags", "passed_card_ids"],
            "flags": ["flag_id", "card_id", "rule_id", "severity",
                      "claim_text", "reason", "evidence_refs",
                      "required_correction", "blocks_release"],
        },
    },
}
