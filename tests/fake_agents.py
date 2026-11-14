"""Minimal fake agents for testing the Supervisor runner without the team's code.

Each returns a valid AgentResult (is_mock: true) built from the request.
Programs and evidence are real IDs from the frozen Supervisor test KB
(tests/fixtures/kb_supervisor_fixture.json). Use FIXTURE_KB as the KB path in tests.
"""
import datetime
import os
import re
import time

# Path to the frozen KB fixture.  All Supervisor tests must use this, not the live KB.
FIXTURE_KB = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "fixtures", "kb_supervisor_fixture.json"))

# Path to the frozen ZIP fixture.  All Supervisor tests must use this, not the live ZIP list.
FIXTURE_ZIPS = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "fixtures", "zips_fixture.json"))


def _env(req, result, status="completed"):
    return {k: req[k] for k in ("request_id", "run_id", "case_id", "case_version", "correlation_id")} | {
        "agent_id": req["role_id"], "schema_version": "1.0", "status": status, "result": result,
        "issues": [], "clarification_requests": [], "evidence_refs": [],
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "is_mock": True}


def agent_1(req):
    return _env(req, {"narrative_summary": "Lost job; rent due Nov 1.", "triggering_events": ["job_loss"],
        "proposed_needs": [
            {"need_id": "need_001", "category": "income_assistance", "subcategory": None, "description": "Lost job",
             "original_quote": "laid off", "confirmation_status": "proposed", "user_reported": True,
             "urgency": "high", "urgency_reason": None, "user_priority": None},
            {"need_id": "need_002", "category": "housing_assistance", "subcategory": "rental_assistance",
             "description": "Rent due Nov 1", "original_quote": "rent", "confirmation_status": "proposed",
             "user_reported": True, "urgency": "high", "urgency_reason": None, "user_priority": None}],
        "factual_claims": [
            {"fact_id": "fact_001", "field": "zip_code", "value": "95823", "confirmation_status": "proposed",
             "source": "user_statement", "time_context": None},
            {"fact_id": "fact_002", "field": "rent_due_date", "value": "2026-11-01", "confirmation_status": "proposed",
             "source": "user_statement", "time_context": None}],
        "ambiguity_flags": [], "safety_or_official_deadline_flags": []})


def agent_3(req):
    pairs = [("prog_income_edd_ui_ca_001", "need_001"), ("prog_housing_saintjohns_sac_001", "need_002")]
    return _env(req, {"candidate_programs": [
        {"program_id": p, "matched_need_ids": [n], "retrieval_reason": "fake", "source_refs": [], "missing_fields": []}
        for p, n in pairs], "retrieval_notes": []})


def agent_4(req):
    return _env(req, {"matches": [
        {"program_id": c["program_id"], "need_ids": c["matched_need_ids"], "match_status": "potential_match",
         "matched_criteria": [], "missing_case_facts": [], "mismatch_criteria": [], "evidence_refs": [],
         "explanation": "fake"} for c in req["payload"]["candidate_programs"]]})


def agent_5(req):
    return _env(req, {"checked_claims": [], "update_proposals": [], "unresolved_questions": []})


def agent_6(req):
    return _env(req, {"proposed_actions": [
        {"action_id": f"act_{i:02d}", "need_id": m["need_ids"][0], "program_id": m["program_id"],
         "suggested_priority": i, "order_group": "first" if i == 1 else "parallel", "rationale": "fake",
         "dependency_ids": [], "official_deadline": None, "user_target_date": None,
         "estimated_processing_time": None, "evidence_refs": [], "uncertainty_notes": [],
         "user_override_allowed": True} for i, m in enumerate(req["payload"]["matches"], 1)]})


def agent_8(req):
    return _env(req, {"plan_version": "1", "potential_options": [], "coverage_gaps": [], "action_cards": [
        {"card_id": f"card_{i:02d}", "source_action_ids": [a["action_id"]], "related_need_ids": [a["need_id"]],
         "program_id": a["program_id"], "action_title": "Contact the program", "reason": "fake",
         "next_step": "Call the program.", "priority_reason": "fake", "order_group": a["order_group"],
         "dependency_card_ids": [], "source_refs": [], "uncertainty_notes": [], "official_deadline": None,
         "user_target_date": None, "processing_estimate": None, "progress_status": "not_started"}
        for i, a in enumerate(req["payload"]["proposed_actions"], 1)]})


def agent_10_pass(req):
    ids = [c["card_id"] for c in req["payload"]["action_cards"]]
    return _env(req, {"verdict": "PASS", "repair_round": req["payload"]["repair_round"],
                      "flags": [], "passed_card_ids": ids})


def agent_10_always_flags_card_02(req):
    ids = [c["card_id"] for c in req["payload"]["action_cards"]]
    flag = {"flag_id": "FLAG-001", "card_id": "card_02", "rule_id": "V1", "severity": "critical",
            "claim_text": "You will get help", "reason": "guarantee", "evidence_refs": [],
            "required_correction": "Remove the guarantee", "blocks_release": True}
    return _env(req, {"verdict": "FLAG", "repair_round": req["payload"]["repair_round"],
                      "flags": [flag], "passed_card_ids": [i for i in ids if i != "card_02"]})


def agent_10_flags_card02_once(req):
    """Flags card_02 on repair_round 0 only; passes on every subsequent round."""
    if req["payload"]["repair_round"] == 0:
        return agent_10_always_flags_card_02(req)
    return agent_10_pass(req)


def agent_8_repair_card02(req):
    """Repair-round Agent 8: returns only card_02 with new text + repaired_card_ids.

    On a normal (non-repair) call it behaves like agent_8.
    """
    if "repair_flags" not in req["payload"]:
        return agent_8(req)
    # Find the original card_02 action from the payload to copy required fields
    actions = req["payload"].get("proposed_actions", [])
    card02_action = next((a for a in actions if a["action_id"] == "act_02"), None)
    if card02_action is None:
        # fallback: no action for card_02 known; just return minimal
        return _env(req, {"plan_version": "1r", "potential_options": [], "coverage_gaps": [],
                          "action_cards": [], "repaired_card_ids": ["card_02"]})
    repaired_card = {
        "card_id": "card_02", "source_action_ids": [card02_action["action_id"]],
        "related_need_ids": [card02_action["need_id"]], "program_id": card02_action["program_id"],
        "action_title": "Contact the program (repaired)", "reason": "repaired",
        "next_step": "Call the program (repaired).", "priority_reason": "repaired",
        "order_group": card02_action["order_group"], "dependency_card_ids": [],
        "source_refs": [], "uncertainty_notes": [], "official_deadline": None,
        "user_target_date": None, "processing_estimate": None, "progress_status": "not_started",
    }
    return _env(req, {"plan_version": "1r", "potential_options": [], "coverage_gaps": [],
                      "action_cards": [repaired_card], "repaired_card_ids": ["card_02"]})


def agent_8_repair_unknown_card(req):
    """Repair-round Agent 8: returns a card whose card_id is not in the current plan."""
    if "repair_flags" not in req["payload"]:
        return agent_8(req)
    actions = req["payload"].get("proposed_actions", [])
    card02_action = next((a for a in actions if a["action_id"] == "act_02"), actions[0] if actions else None)
    unknown_card = {
        "card_id": "card_99", "source_action_ids": [],
        "related_need_ids": [card02_action["need_id"]] if card02_action else [],
        "program_id": card02_action["program_id"] if card02_action else None,
        "action_title": "Unknown card", "reason": "unknown", "next_step": "n/a",
        "priority_reason": "unknown", "order_group": "parallel", "dependency_card_ids": [],
        "source_refs": [], "uncertainty_notes": [], "official_deadline": None,
        "user_target_date": None, "processing_estimate": None, "progress_status": "not_started",
    }
    return _env(req, {"plan_version": "1r", "potential_options": [], "coverage_gaps": [],
                      "action_cards": [unknown_card], "repaired_card_ids": ["card_02"]})


def agent_8_repair_missing_listed_card(req):
    """Repair-round Agent 8: lists card_02 in repaired_card_ids but does not return it."""
    if "repair_flags" not in req["payload"]:
        return agent_8(req)
    # Returns an empty action_cards list but claims card_02 was repaired
    return _env(req, {"plan_version": "1r", "potential_options": [], "coverage_gaps": [],
                      "action_cards": [], "repaired_card_ids": ["card_02"]})


def agent_8_repair_card02_no_ids(req):
    """Repair-round Agent 8: returns only card_02 with NO repaired_card_ids field."""
    if "repair_flags" not in req["payload"]:
        return agent_8(req)
    actions = req["payload"].get("proposed_actions", [])
    card02_action = next((a for a in actions if a["action_id"] == "act_02"), None)
    if card02_action is None:
        return _env(req, {"plan_version": "1r", "potential_options": [], "coverage_gaps": [],
                          "action_cards": []})
    repaired_card = {
        "card_id": "card_02", "source_action_ids": [card02_action["action_id"]],
        "related_need_ids": [card02_action["need_id"]], "program_id": card02_action["program_id"],
        "action_title": "Contact the program (no-ids repair)", "reason": "repaired",
        "next_step": "Call the program (repaired).", "priority_reason": "repaired",
        "order_group": card02_action["order_group"], "dependency_card_ids": [],
        "source_refs": [], "uncertainty_notes": [], "official_deadline": None,
        "user_target_date": None, "processing_estimate": None, "progress_status": "not_started",
    }
    return _env(req, {"plan_version": "1r", "potential_options": [], "coverage_gaps": [],
                      "action_cards": [repaired_card]})


def crashing_agent(req):
    raise ValueError("something broke inside the agent")


def slow_agent(req):
    time.sleep(2)
    return agent_3(req)


def agent_with_ssn(req):
    r = agent_3(req)
    r["result"]["retrieval_notes"] = ["Client SSN 123-45-6789"]
    return r


ALL = {"agent_1": agent_1, "agent_3": agent_3, "agent_4": agent_4, "agent_5": agent_5,
       "agent_6": agent_6, "agent_8": agent_8, "agent_10": agent_10_pass}


def agent_2(req):
    return _env(req, {"need_updates": [
        {"need_id": "need_002", "urgency": "immediate", "urgency_reason": "Rent due in days"}],
        "optional_food_check": False})


def agent_2_unknown_need(req):
    return _env(req, {"need_updates": [
        {"need_id": "need_999", "urgency": "high", "urgency_reason": "a need that does not exist"}],
        "optional_food_check": False})


def agent_7(req):
    stage = req["payload"]["stage"]
    finding = {"finding_id": f"F7-{stage}", "rule_id": "Q7", "severity": "warning", "program_id": None,
               "need_id": None, "field_path": None, "evidence_refs": [], "description": f"fake {stage} finding",
               "recommended_action": "no_action"}
    return _env(req, {"stage": stage, "stage_assessment": "issues_found", "findings": [finding]})


def very_slow_agent(req):
    time.sleep(30)
    return agent_3(req)


# ---------------------------------------------------------------- dialog fake agents

def agent_1_dialog(req):
    """Dialog fake Agent 1.

    understand_story: returns housing + food needs, one ambiguity flag, no facts.
    parse_clarification_answer:
      - a 5-digit number → zip_code
      - "0" or a number with "month" → household_gross_monthly_income (value 0 or the number)
      - "hours" in text → triggering_circumstances = "reduced_hours"
      - "doctor" in text → also proposed_needs with one medical_health_coverage need
      - otherwise: no claims
    Follows the contract shapes exactly.
    """
    task = req.get("task_type")

    if task == "understand_story":
        return _env(req, {
            "narrative_summary": "You have problems with housing and food.",
            "triggering_events": [],
            "proposed_needs": [
                {"need_id": "need_001", "category": "housing_assistance", "subcategory": None,
                 "description": "Problems with housing", "original_quote": req["payload"].get("story_text", ""),
                 "confirmation_status": "proposed", "user_reported": True,
                 "urgency": "normal", "urgency_reason": None, "user_priority": None},
                {"need_id": "need_002", "category": "food_assistance", "subcategory": None,
                 "description": "Problems with food", "original_quote": req["payload"].get("story_text", ""),
                 "confirmation_status": "proposed", "user_reported": True,
                 "urgency": "normal", "urgency_reason": None, "user_priority": None},
            ],
            "factual_claims": [],
            "ambiguity_flags": [
                {"field": "triggering_circumstances",
                 "quote": req["payload"].get("story_text", ""),
                 "note": "unspecified_hardship_cause"}
            ],
            "safety_or_official_deadline_flags": [],
        })

    # parse_clarification_answer
    answer_text = req["payload"].get("answer_text", "")
    pending    = req["payload"].get("pending_fact_keys", [])
    claims = []
    proposed_needs = []

    # 5-digit ZIP
    if re.search(r"\b\d{5}\b", answer_text) and "zip_code" in pending:
        m = re.search(r"\b(\d{5})\b", answer_text)
        claims.append({"fact_id": "fa_zip", "field": "zip_code", "value": m.group(1),
                       "confirmation_status": "proposed", "source": "user_statement",
                       "time_context": None})

    # "0" or number + "month" → income
    income_key = "household_gross_monthly_income"
    if income_key in pending:
        if answer_text.strip() == "0":
            claims.append({"fact_id": "fa_inc", "field": income_key, "value": 0,
                           "confirmation_status": "proposed", "source": "user_statement",
                           "time_context": None})
        else:
            m2 = re.search(r"\b(\d[\d,]*)\b", answer_text)
            if m2 and "month" in answer_text.lower():
                val = int(m2.group(1).replace(",", ""))
                claims.append({"fact_id": "fa_inc", "field": income_key, "value": val,
                               "confirmation_status": "proposed", "source": "user_statement",
                               "time_context": None})

    # "hours" → triggering_circumstances
    tc_key = "triggering_circumstances"
    if tc_key in pending and "hours" in answer_text.lower():
        claims.append({"fact_id": "fa_tc", "field": tc_key, "value": "reduced_hours",
                       "confirmation_status": "proposed", "source": "user_statement",
                       "time_context": None})

    # "doctor" → propose medical_health_coverage need (new id not in existing_needs)
    if "doctor" in answer_text.lower():
        existing_ids = {n["need_id"] for n in req["payload"].get("existing_needs", [])}
        new_id = "need_003"
        while new_id in existing_ids:
            new_id = f"need_{int(new_id.split('_')[1]) + 1:03d}"
        proposed_needs.append(
            {"need_id": new_id, "category": "medical_health_coverage", "subcategory": None,
             "description": "Medical care need", "original_quote": answer_text,
             "confirmation_status": "proposed", "user_reported": True,
             "urgency": "normal", "urgency_reason": None, "user_priority": None})

    result = {"factual_claims": claims}
    if proposed_needs:
        result["proposed_needs"] = proposed_needs
    return _env(req, result)


def agent_2_dialog(req):
    """Dialog fake Agent 2.

    Asks triggering_circumstances while the ambiguity flag is passed and it is not a fact/asked.
    Then asks zip_code and household_gross_monthly_income (can_skip false) if missing and not asked.
    Then nothing.
    """
    facts = {f["field"] for f in req["payload"].get("case_facts", [])}
    asked = set(req["payload"].get("already_asked", []))
    flags = req["payload"].get("ambiguity_flags", [])

    crs = []

    # Ask triggering_circumstances if flagged and not known
    tc_flagged = any(f.get("field") == "triggering_circumstances" for f in flags)
    if tc_flagged and "triggering_circumstances" not in facts and "triggering_circumstances" not in asked:
        crs.append({
            "fact_key": "triggering_circumstances",
            "question_intent": "What caused the difficulty",
            "user_facing_question": ("Could you tell me a little more about what happened "
                                     "that led to these difficulties?"),
            "reason": "The cause decides which programs fit.",
            "applicable_program_ids": [],
            "verified_rule_ref": None,
            "necessity_level": "helpful",
            "can_skip": True,
        })

    # Ask zip_code if missing and not asked
    if "zip_code" not in facts and "zip_code" not in asked:
        crs.append({
            "fact_key": "zip_code",
            "question_intent": "Where the person lives",
            "user_facing_question": "What is your ZIP code?",
            "reason": "Programs depend on where you live.",
            "applicable_program_ids": [],
            "verified_rule_ref": None,
            "necessity_level": "required_for_decision",
            "can_skip": True,
        })

    # Ask household_gross_monthly_income if missing and not asked (can_skip false)
    if ("household_gross_monthly_income" not in facts
            and "household_gross_monthly_income" not in asked):
        crs.append({
            "fact_key": "household_gross_monthly_income",
            "question_intent": "Income for eligibility",
            "user_facing_question": "What is your approximate gross monthly household income?",
            "reason": "Income limits decide CalFresh and rent help.",
            "applicable_program_ids": [],
            "verified_rule_ref": None,
            "necessity_level": "required_for_decision",
            "can_skip": False,
        })

    return _env(req, {"need_updates": [], "optional_food_check": False},
                status="completed") | {"clarification_requests": crs}


def agent_2_dialog_no_questions(req):
    """Dialog fake Agent 2 that never asks any questions (geography guard test)."""
    return _env(req, {"need_updates": [], "optional_food_check": False},
                status="completed") | {"clarification_requests": []}


def agent_2_dialog_repeats_asked(req):
    """Dialog fake Agent 2 that always asks triggering_circumstances again (drop + summary test)."""
    crs = [{
        "fact_key": "triggering_circumstances",
        "question_intent": "repeat",
        "user_facing_question": "What happened again?",
        "reason": "testing drop",
        "applicable_program_ids": [],
        "verified_rule_ref": None,
        "necessity_level": "helpful",
        "can_skip": True,
    }]
    return _env(req, {"need_updates": [], "optional_food_check": False},
                status="completed") | {"clarification_requests": crs}


def agent_2_dialog_always_new(req):
    """Dialog fake Agent 2 that always asks a new key (loop guard test)."""
    asked = set(req["payload"].get("already_asked", []))
    # Pick a new key not yet asked
    for i in range(1, 100):
        key = f"new_key_{i:02d}"
        if key not in asked:
            break
    crs = [{
        "fact_key": key,
        "question_intent": "loop guard test",
        "user_facing_question": f"Question about {key}?",
        "reason": "testing loop guard",
        "applicable_program_ids": [],
        "verified_rule_ref": None,
        "necessity_level": "helpful",
        "can_skip": True,
    }]
    return _env(req, {"need_updates": [], "optional_food_check": False},
                status="completed") | {"clarification_requests": crs}


def agent_1_dialog_with_safety(req):
    """Agent 1 that returns a safety flag when answer contains 'hurt' (parse_clarification_answer).

    For understand_story: behaves like agent_1_dialog.
    """
    if req.get("task_type") == "understand_story":
        return agent_1_dialog(req)
    # parse_clarification_answer
    r = agent_1_dialog(req)
    answer_text = req["payload"].get("answer_text", "")
    if "hurt" in answer_text.lower():
        r["result"]["safety_or_official_deadline_flags"] = [
            {"type": "safety", "quote": "[REDACTED]",
             "note": "Threat of physical harm reported"}]
    return r


def agent_8_dialog_with_gap(req):
    """Agent 8 that returns one card for need_001 and a coverage gap for need_002."""
    base = agent_8(req)
    # Remove any card for need_002
    base["result"]["action_cards"] = [
        c for c in base["result"]["action_cards"]
        if "need_002" not in c.get("related_need_ids", [])]
    base["result"]["coverage_gaps"] = [
        {"need_id": "need_002",
         "note": "We have not found a verified program for this need yet."}]
    return base


def agent_3_dialog(req):
    """Dialog fake Agent 3: like agent_3, but matches only the needs it receives (as the real Agent 3)."""
    ids = {n["need_id"] for n in req["payload"]["needs"]}
    r = agent_3(req)
    r["result"]["candidate_programs"] = [
        c for c in r["result"]["candidate_programs"] if set(c["matched_need_ids"]) <= ids]
    return r


def agent_1_dialog_fails_on_answer(req):
    """Agent 1 that answers understand_story normally but raises on parse_clarification_answer."""
    if req.get("task_type") == "understand_story":
        return agent_1_dialog(req)
    raise ValueError("Agent 1 internal error on answer")
