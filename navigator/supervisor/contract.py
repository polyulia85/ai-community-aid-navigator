"""Shared JSON Contracts v1.0 (frozen Oct 23, 2026) as Python constants.

One place for every allowed value. If the contract changes (v1.1),
only this file changes.
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
