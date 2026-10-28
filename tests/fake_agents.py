"""Minimal fake agents for testing the Supervisor runner without the team's code.

Each returns a valid AgentResult (is_mock: true) built from the request.
Programs and evidence are real IDs from kb/kb_sacramento.json.
"""
import datetime
import time


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
