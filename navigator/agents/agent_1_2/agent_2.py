"""
AI Community Aid Navigator — Agent 2: Case Analysis & Clarification
Contracts: docs/contracts/SHARED_CONTRACTS.md (v1.1)
Pure standard library implementation (Python 3.11+). Zero external dependencies.
Rules: 4-Gate Question Filter, Pacing Ceiling (<= 2/turn §30.8), Preservation of Unknowns

Contract invariants enforced:
- ZIP Code Question (Item 2): if zip_code is not known and not asked, Agent 2 asks for the
  resident's Sacramento ZIP code with can_skip=True on Turn 1.
- Household Size Question (Item 3): if household_size is not known and not asked, and either
  candidate_requirements ask for it or food_assistance is in needs, ask with can_skip=True.
- Income Question: if household_gross_monthly_income is not known, not asked, AND no
  candidate_requirements are provided, Agent 2 MUST generate a question for it with can_skip=False.
- Eviction Notice Details: When has_written_eviction_notice is True in case_facts, Agent 2 asks
  document type and date with can_skip=False (fact_key: eviction_notice_type).
- Gate 3 (verified_rule_ref): questions without a valid rule ref are suppressed.
- Gate 2: already-asked facts are never re-asked.
- Gate 1: known facts are never asked (except eviction follow-up).
- Pacing ceiling: max 2 clarification requests per turn (§30.8).
- Backward Compatibility (Item 4): triggering_circumstances already_asked key covers
  triggering_events / employment_status root-cause tokens from previous turns.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

_THREAT_CLARIFICATION_ITEMS = [
    (
        "has_written_eviction_notice",
        "Determine whether landlord gave a formal written eviction notice",
        "Did you receive a written eviction notice from your landlord?",
        "Distinguishes a verbal threat from a formal legal notice with statutory response timelines",
    ),
    (
        "has_court_writ_or_judgment",
        "Determine whether a court judgment or writ of eviction exists",
        "Is there a court judgment or writ of eviction?",
        "Identifies active court enforcement requiring immediate legal aid intervention",
    ),
    (
        "specific_move_out_date",
        "Determine whether a specific move-out date was named",
        "Did the landlord name a specific move-out date?",
        "Establishes urgency window for emergency housing and legal defense",
    ),
    (
        "imminent_removal_in_progress",
        "Determine whether landlord is attempting immediate physical removal or lock change",
        "Is the landlord trying to remove you right now, for example by changing the locks?",
        "Identifies active illegal lockout requiring immediate emergency response",
    ),
]


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
    raw_ambiguity_flags: List[Any] = payload.get("ambiguity_flags") or []

    ambiguity_flag_notes: Set[str] = set()
    for af in raw_ambiguity_flags:
        if isinstance(af, str):
            ambiguity_flag_notes.add(af.strip())
        elif isinstance(af, dict):
            note = af.get("note")
            if note:
                ambiguity_flag_notes.add(str(note).strip())

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

    if "triggering_circumstances" in already_asked_keys:
        already_asked_keys.add("triggering_events")
        already_asked_keys.add("employment_status")

    # Step 1 — Circumstance-First Gate
    unspecified_hardship = "unspecified_hardship_cause" in ambiguity_flag_notes
    circumstances_already_asked = "triggering_circumstances" in already_asked_keys
    circumstances_in_facts = "triggering_circumstances" in known_keys

    if unspecified_hardship and not circumstances_already_asked and not circumstances_in_facts:
        clarification_requests.append({
            "fact_key": "triggering_circumstances",
            "question_intent": "Identify root cause and circumstances of hardship",
            "user_facing_question": (
                "I'm sorry your family is going through a difficult time. "
                "Could you tell me a little more about what happened that led to these financial difficulties?"
            ),
            "reason": "Understanding what caused the hardship determines applicable crisis and emergency programs",
            "applicable_program_ids": [],
            "verified_rule_ref": None,
            "necessity_level": "helpful",
            "can_skip": True,
        })
        seen_keys.add("triggering_circumstances")

        return {
            "request_id": request_dict.get("request_id", "req-unknown"),
            "run_id": request_dict.get("run_id", "run-unknown"),
            "case_id": request_dict.get("case_id", "case-unknown"),
            "case_version": request_dict.get("case_version", 1),
            "correlation_id": request_dict.get("correlation_id", "corr-unknown"),
            "agent_id": "agent_2",
            "schema_version": schema_version_out,
            "status": "needs_clarification",
            "result": {
                "need_updates": [],
                "optional_food_check": False,
            },
            "issues": [],
            "clarification_requests": clarification_requests,
            "evidence_refs": [],
            "generated_at": now_iso,
            "is_mock": True,
        }

    # Detect housing threat without confirmed written notice or actual lockout (Item 2)
    is_actual_lockout = known_facts.get("eviction_notice_type") == "lockout"
    notice_is_reported = known_facts.get("has_written_eviction_notice") is True
    has_housing_threat = any(
        isinstance(n, dict)
        and n.get("category") == "housing_assistance"
        and any(
            w in f"{n.get('description', '')} {n.get('urgency_reason', '')} {n.get('original_quote', '')}".lower()
            for w in ["threat", "lock", "evict"]
        )
        for n in needs
    ) and not notice_is_reported and not is_actual_lockout

    # 2. ZIP Code Question
    has_zip_fact = "zip_code" in known_keys
    zip_already_asked = "zip_code" in already_asked_keys
    eviction_followup_pending = (
        notice_is_reported
        and ("eviction_notice_type" not in already_asked_keys)
        and ("eviction_notice_type" not in known_keys)
    )

    if (
        not has_zip_fact
        and not zip_already_asked
        and needs
        and not eviction_followup_pending
    ):
        if len(clarification_requests) < 2:
            clarification_requests.append({
                "fact_key": "zip_code",
                "question_intent": "Determine resident's Sacramento service area ZIP code",
                "user_facing_question": (
                    "What is your Sacramento ZIP code? "
                    "This helps us find the right local programs in your area."
                ),
                "reason": "ZIP code is required to match geographic eligibility for local programs",
                "applicable_program_ids": [],
                "verified_rule_ref": None,
                "necessity_level": "required_for_decision",
                "can_skip": True,
            })
            seen_keys.add("zip_code")

    # 3. Income Question — required (can_skip=False), never repeated once in already_asked
    has_income_fact = "household_gross_monthly_income" in known_keys

    should_ask_income = (
        not has_income_fact
        and "household_gross_monthly_income" not in already_asked_keys
        and not candidate_requirements
        and not unspecified_hardship
        and not eviction_followup_pending
    )

    if should_ask_income and len(clarification_requests) < 2:
        clarification_requests.append({
            "fact_key": "household_gross_monthly_income",
            "question_intent": "Determine current monthly household income",
            "user_facing_question": "What is your approximate gross monthly household income?",
            "reason": "Required to determine eligibility thresholds across community assistance programs",
            "applicable_program_ids": [],
            "verified_rule_ref": None,
            "necessity_level": "required_for_decision",
            "can_skip": False,
        })
        seen_keys.add("household_gross_monthly_income")

    # 4a. Eviction Notice Follow-up (when written notice IS already known)
    eviction_type_already_asked = (
        "eviction_notice_type" in already_asked_keys
        or "eviction_notice_details" in already_asked_keys
    )
    has_eviction_type_fact = "eviction_notice_type" in known_keys

    if notice_is_reported and not has_eviction_type_fact and not eviction_type_already_asked:
        if len(clarification_requests) < 2:
            clarification_requests.append({
                "fact_key": "eviction_notice_type",
                "question_intent": "Determine legal eviction notice type and receipt date for emergency rental defense",
                "user_facing_question": (
                    "What type of eviction notice did you receive (such as a 3-day notice), "
                    "and what date is listed on it?"
                ),
                "reason": "Notice type and receipt date determine legal response timelines and court defense eligibility",
                "applicable_program_ids": [],
                "verified_rule_ref": None,
                "necessity_level": "required_for_decision",
                "can_skip": False,
            })
            seen_keys.add("eviction_notice_type")

    # 4b. Follow-up Item 5: All 4 threat clarification questions must be skippable ("helpful", can_skip=True)
    if has_housing_threat and len(clarification_requests) < 2:
        for t_key, t_intent, t_question, t_reason in _THREAT_CLARIFICATION_ITEMS:
            if len(clarification_requests) >= 2:
                break
            if t_key in known_keys or t_key in already_asked_keys or t_key in seen_keys:
                continue
            clarification_requests.append({
                "fact_key": t_key,
                "question_intent": t_intent,
                "user_facing_question": t_question,
                "reason": t_reason,
                "applicable_program_ids": [],
                "verified_rule_ref": None,
                "necessity_level": "helpful",
                "can_skip": True,
            })
            seen_keys.add(t_key)

    # 5. 4-Gate Filter on candidate_requirements (Rule 19.2)
    for req in candidate_requirements:
        if not isinstance(req, dict):
            continue

        fact_key = req.get("fact_key")
        if not fact_key:
            continue
        fact_key = str(fact_key).strip()

        if fact_key in already_asked_keys:
            continue

        verified_rule_ref = req.get("verified_rule_ref")
        if (
            verified_rule_ref is None
            or str(verified_rule_ref).strip() == ""
            or str(verified_rule_ref).lower() == "none"
        ):
            continue

        if fact_key in known_keys and fact_key != "has_written_eviction_notice":
            continue

        if fact_key in seen_keys:
            continue

        if fact_key == "has_written_eviction_notice" and known_facts.get("has_written_eviction_notice") is True:
            continue

        if fact_key == "has_written_eviction_notice" and known_facts.get("has_written_eviction_notice") is False:
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

    # 5b. Household Size Question
    has_hh_size_fact = "household_size" in known_keys
    hh_size_already_asked = "household_size" in already_asked_keys
    cand_needs_hh_size = any(
        isinstance(r, dict) and str(r.get("fact_key", "")).strip() == "household_size"
        for r in candidate_requirements
    )
    has_food_need_for_hh = any(
        isinstance(n, dict) and n.get("category") == "food_assistance" for n in needs
    )

    should_ask_hh_size = (
        not has_hh_size_fact
        and not hh_size_already_asked
        and "household_size" not in seen_keys
        and (
            cand_needs_hh_size
            or (has_food_need_for_hh and len(clarification_requests) == 0)
        )
        and len(clarification_requests) < 2
    )

    if should_ask_hh_size:
        clarification_requests.append({
            "fact_key": "household_size",
            "question_intent": "Determine total number of people in the household",
            "user_facing_question": (
                "How many people are currently living in your household, including yourself?"
            ),
            "reason": "Household size affects eligibility thresholds for food and assistance programs",
            "applicable_program_ids": [],
            "verified_rule_ref": None,
            "necessity_level": "required_for_decision",
            "can_skip": True,
        })
        seen_keys.add("household_size")

    # 6. Conditional Food Check (§19.1)
    has_food_need = any(isinstance(n, dict) and n.get("category") == "food_assistance" for n in needs)
    has_income_need_flag = any(n.get("category") == "income_assistance" for n in needs if isinstance(n, dict))
    has_income_loss_fact = any(
        any(k in str(f.get("value", "")) for k in ["laid_off", "unemployed", "fired", "reduced_hours"])
        for f in case_facts if isinstance(f, dict)
    )
    optional_food_check = (has_income_need_flag or has_income_loss_fact) and not has_food_need

    # 7. Need Updates: emit ONLY when urgency actually changes
    need_updates: List[Dict[str, Any]] = []
    late_stage_housing = (
        known_facts.get("has_court_writ_or_judgment") is True
        or known_facts.get("imminent_removal_in_progress") is True
        or known_facts.get("eviction_notice_type") in {"judgment", "writ", "lockout"}
    )
    for n in needs:
        if not isinstance(n, dict):
            continue
        if n.get("category") == "housing_assistance" and late_stage_housing:
            if n.get("urgency") != "immediate":
                is_lockout_now = (
                    known_facts.get("imminent_removal_in_progress") is True
                    or known_facts.get("eviction_notice_type") == "lockout"
                )
                need_updates.append({
                    "need_id": n.get("need_id"),
                    "urgency": "immediate",
                    "urgency_reason": (
                        "Active lockout or imminent removal reported"
                        if is_lockout_now
                        else "Court judgment or writ of eviction reported"
                    ),
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
            "If so, what type of document is it (such as a 3-day notice) and what date is listed on it?",
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