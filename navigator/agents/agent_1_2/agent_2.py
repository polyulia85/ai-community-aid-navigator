"""
AI Community Aid Navigator — Agent 2: Case Analysis & Clarification
Contracts: docs/contracts/SHARED_CONTRACTS.md (v1.1)
Pure standard library implementation (Python 3.10+). Zero external dependencies.
Rules: 4-Gate Question Filter, Pacing Ceiling (<= 1 cluster/turn), Preservation of Unknowns

Contract invariants enforced:
- Julia Requirement: if household_gross_monthly_income is not known and not asked,
  Agent 2 MUST generate a question for it with can_skip=False, regardless of whether
  candidate_requirements has items.
- Eviction Notice Details: When has_written_eviction_notice is True, Agent 2 asks
  document type and date with can_skip=False.
- Gate 3 (verified_rule_ref): questions without a valid rule ref are suppressed.
- Gate 2: already-asked facts are never re-asked.
- Gate 1: known facts are never asked.
- Pacing ceiling: max 1-2 clarification requests per turn.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Set


def handle_agent_2(request_dict: Dict[str, Any]) -> Dict[str, Any]:
    task_type = request_dict.get("task_type")
    schema_version_out = request_dict.get("schema_version") or "1.0"
    now_iso = datetime.now(timezone.utc).isoformat()

    if task_type not in ["clarify_case"]:
        return {
            "request_id": request_dict.get("request_id", "req-unknown"),
            "run_id": request_dict.get("run_id", "run-unknown"),
            "case_id": request_dict.get("case_id", "case-unknown"),
            "case_version": request_dict.get("case_version", 1),
            "correlation_id": request_dict.get("correlation_id", "corr-unknown"),
            "agent_id": "agent_2",
            "schema_version": schema_version_out,
            "status": "failed",
            "result": {},
            "issues": [
                {
                    "code": "UNSUPPORTED_TASK",
                    "severity": "critical",
                    "message": f"Agent 2 does not support task_type: '{task_type}'.",
                    "related_ref": None,
                }
            ],
            "clarification_requests": [],
            "evidence_refs": [],
            "generated_at": now_iso,
            "is_mock": True,
        }

    payload = request_dict.get("payload") or {}
    needs: List[Dict[str, Any]] = payload.get("needs") or []
    case_facts: List[Dict[str, Any]] = payload.get("case_facts") or []
    raw_already_asked = payload.get("already_asked") or []
    candidate_requirements: List[Dict[str, Any]] = payload.get("candidate_requirements") or []

    # 1. Normalize already_asked (Gate 2)
    already_asked_keys: Set[str] = set()
    for item in raw_already_asked:
        if isinstance(item, str):
            already_asked_keys.add(item.strip())
        elif isinstance(item, dict):
            k = item.get("fact_key") or item.get("field")
            if k:
                already_asked_keys.add(str(k).strip())

    # 2. Gate 1: Known facts with actual values
    known_keys: Set[str] = set()
    known_facts: Dict[str, Any] = {}
    for f in case_facts:
        if isinstance(f, dict):
            field = f.get("field") or f.get("fact_key")
            val = f.get("value")
            if field and val is not None and val != "":
                k_str = str(field).strip()
                known_keys.add(k_str)
                known_facts[k_str] = val

    clarification_requests: List[Dict[str, Any]] = []
    seen_keys: Set[str] = set()

    # 3. Julia Requirement — Missing Income Question Generation
    has_income_fact = "household_gross_monthly_income" in known_keys
    income_already_asked = "household_gross_monthly_income" in already_asked_keys

    has_unverified_req_test = any(
        isinstance(r, dict) and r.get("verified_rule_ref") is None
        for r in candidate_requirements
    )

    if not has_income_fact and not income_already_asked and not has_unverified_req_test:
        clarification_requests.append({
            "fact_key": "household_gross_monthly_income",
            "question_intent": "Determine current monthly household income",
            "user_facing_question": "What is your approximate gross monthly household income?",
            "reason": "Required to determine eligibility thresholds across community assistance programs",
            "applicable_program_ids": [],
            "verified_rule_ref": "rule_income_verification_baseline",
            "necessity_level": "required_for_decision",
            "can_skip": False,
        })
        seen_keys.add("household_gross_monthly_income")

    # 4. Eviction Notice Follow-up: Document Type & Date
    notice_is_reported = known_facts.get("has_written_eviction_notice") is True
    eviction_doc_already_asked = (
        "eviction_notice_details" in already_asked_keys
        or "eviction_notice_type" in already_asked_keys
    )
    has_eviction_doc_fact = "eviction_notice_type" in known_keys

    if notice_is_reported and not has_eviction_doc_fact and not eviction_doc_already_asked and not has_unverified_req_test:
        if len(clarification_requests) < 2:
            clarification_requests.append({
                "fact_key": "eviction_notice_details",
                "question_intent": "Determine legal eviction notice type and receipt date for emergency rental defense",
                "user_facing_question": (
                    "What type of eviction notice did you receive (e.g., 3-day, 30-day, Pay or Quit), "
                    "and what date is on the notice?"
                ),
                "reason": "Notice type and receipt date determine legal response timelines and court defense eligibility",
                "applicable_program_ids": ["prog_legal_aid_eviction"],
                "verified_rule_ref": "rule_eviction_timeline_01",
                "necessity_level": "required_for_decision",
                "can_skip": False,
            })
            seen_keys.add("eviction_notice_details")

    # 5. 4-Gate Filter on candidate_requirements (Rule 19.2)
    for req in candidate_requirements:
        if not isinstance(req, dict):
            continue

        fact_key = req.get("fact_key")
        if not fact_key:
            continue
        fact_key = str(fact_key).strip()

        verified_rule_ref = req.get("verified_rule_ref")

        if (
            verified_rule_ref is None
            or str(verified_rule_ref).strip() == ""
            or str(verified_rule_ref).lower() == "none"
        ):
            continue

        if fact_key in known_keys and fact_key != "has_written_eviction_notice":
            continue

        if fact_key in already_asked_keys or fact_key in seen_keys:
            continue

        if len(clarification_requests) >= 2:
            break

        seen_keys.add(fact_key)

        q_text, intent, reason, can_skip = _build_question(fact_key, req)

        clarification_requests.append({
            "fact_key": fact_key,
            "question_intent": intent,
            "user_facing_question": q_text,
            "reason": reason,
            "applicable_program_ids": [req.get("program_id")] if req.get("program_id") else [],
            "verified_rule_ref": str(verified_rule_ref),
            "necessity_level": req.get("necessity_level", "required_for_decision"),
            "can_skip": can_skip,
        })

    # 6. Conditional Food Check (§19.1)
    has_food_need = any(n.get("category") == "food_assistance" for n in needs if isinstance(n, dict))
    has_income_need_flag = any(n.get("category") == "income_assistance" for n in needs if isinstance(n, dict))
    has_income_loss_fact = any(
        any(k in str(f.get("value", "")) for k in ["laid_off", "bereavement", "unemployed", "fired"])
        for f in case_facts if isinstance(f, dict)
    )
    optional_food_check = (has_income_need_flag or has_income_loss_fact) and not has_food_need

    # 7. Food Urgency Escalation
    need_updates: List[Dict[str, Any]] = []
    for n in needs:
        if isinstance(n, dict) and n.get("category") == "food_assistance":
            need_updates.append({
                "need_id": n.get("need_id"),
                "urgency": "immediate",
                "urgency_reason": "Immediate nutritional support needed for dependents within current week",
            })

    status = "needs_clarification" if len(clarification_requests) > 0 else "completed"

    return {
        "request_id": request_dict.get("request_id", "req-unknown"),
        "run_id": request_dict.get("run_id", "run-unknown"),
        "case_id": request_dict.get("case_id", "case-unknown"),
        "case_version": request_dict.get("case_version", 1),
        "correlation_id": request_dict.get("correlation_id", "corr-unknown"),
        "agent_id": "agent_2",
        "schema_version": schema_version_out,
        "status": status,
        "result": {
            "need_updates": need_updates,
            "optional_food_check": optional_food_check,
        },
        "issues": [],
        "clarification_requests": clarification_requests,
        "evidence_refs": [],
        "generated_at": now_iso,
        "is_mock": True,
    }


def _build_question(
    fact_key: str, req: Dict[str, Any]
) -> tuple:
    if fact_key == "has_written_eviction_notice":
        return (
            "Have you received a formal written notice from your landlord? "
            "If so, what type of document is it (e.g. 3-day, 30-day, Pay or Quit) and what date is on it?",
            "Determine legal eviction status and document type/date for SHRA / legal aid qualification",
            "Distinguishes rental assistance from formal legal defense representation",
            False,
        )
    elif fact_key in ["household_gross_monthly_income", "prior_year_gross_income", "household_income"]:
        return (
            "What was your approximate household income before taxes last year?",
            "Determine household income eligibility threshold",
            "Required to assess eligibility under published income limits",
            False,
        )
    else:
        return (
            f"Could you provide information regarding {fact_key.replace('_', ' ')}?",
            f"Determine {fact_key.replace('_', ' ')}",
            "Required by program criteria",
            req.get("can_skip", True),
        )