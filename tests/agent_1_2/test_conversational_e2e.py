"""
test_conversational_e2e.py
End-to-End Multi-Turn Conversational Flow and Logic Validator.
Verifies human conversational sanity across multiple sequential turns.
Contracts Baseline: Shared JSON Contracts v1.1.
Pure Python 3.11+ Standard Library.
"""
from __future__ import annotations

import unittest
from typing import Any, Dict, List

from navigator.agents.agent_1_2.agent_1 import handle_agent_1
from navigator.agents.agent_1_2.agent_2 import handle_agent_2


class TestConversationalEndToEnd(unittest.TestCase):

    def test_e2e_vague_hardship_to_root_cause_resolution(self):
        """
        Scenario 1: User expresses vague distress without root cause.
        Turn 1: Navigator leads with empathetic inquiry, NOT income.
        Turn 2: User provides root cause (job cut); Navigator advances to eligibility screening.
        """
        case_facts: List[Dict[str, Any]] = []
        already_asked: List[str] = []

        # --- TURN 1 ---
        turn_1_input = (
            "Hi, I need help with food and rent. I'm having financial problems and "
            "I'm worried about how my family will get through next month."
        )

        req_1 = {
            "request_id": "req-t1-a1",
            "run_id": "run-e2e-001",
            "case_id": "case-e2e-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": turn_1_input},
        }
        res_1 = handle_agent_1(req_1)["result"]

        need_categories = [n["category"] for n in res_1.get("proposed_needs", [])]
        self.assertIn("food_assistance", need_categories)
        self.assertIn("housing_assistance", need_categories)
        self.assertEqual(len(res_1.get("triggering_events", [])), 0)
        af_notes = [
            (f["note"] if isinstance(f, dict) else f)
            for f in res_1.get("ambiguity_flags", [])
        ]
        self.assertIn("unspecified_hardship_cause", af_notes)

        req_2 = {
            "request_id": "req-t1-a2",
            "run_id": "run-e2e-001",
            "case_id": "case-e2e-001",
            "case_version": 1,
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": res_1["proposed_needs"],
                "case_facts": res_1.get("factual_claims", []),
                "already_asked": already_asked,
                "ambiguity_flags": res_1.get("ambiguity_flags", []),
                "candidate_requirements": [],
            },
        }
        res_2 = handle_agent_2(req_2)
        clarifications_t1 = res_2.get("clarification_requests", [])

        self.assertEqual(len(clarifications_t1), 1)
        first_q = clarifications_t1[0]
        self.assertEqual(first_q["fact_key"], "triggering_circumstances")
        self.assertIn("difficult time", first_q["user_facing_question"].lower())
        self.assertNotIn("gross monthly household income", first_q["user_facing_question"].lower())

        already_asked.append(first_q["fact_key"])

        # --- TURN 2 ---
        turn_2_input = (
            "My company cut my hours from 40 to 15 hours a week starting two weeks ago, "
            "so my paycheck dropped drastically."
        )

        req_3 = {
            "request_id": "req-t2-a1",
            "run_id": "run-e2e-001",
            "case_id": "case-e2e-001",
            "case_version": 2,
            "role_id": "agent_1",
            "task_type": "parse_clarification_answer",
            "payload": {
                "answer_text": turn_2_input,
                "pending_fact_keys": already_asked,
            },
        }
        res_3 = handle_agent_1(req_3)["result"]
        case_facts.extend(res_3.get("factual_claims", []))

        extracted_fields = {f["field"]: f["value"] for f in res_3.get("factual_claims", [])}
        self.assertEqual(extracted_fields.get("triggering_circumstances"), "reduced_hours")

        req_4 = {
            "request_id": "req-t2-a2",
            "run_id": "run-e2e-001",
            "case_id": "case-e2e-001",
            "case_version": 2,
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": res_1["proposed_needs"],
                "case_facts": case_facts,
                "already_asked": already_asked,
                "ambiguity_flags": [],
                "candidate_requirements": [],
            },
        }
        res_4 = handle_agent_2(req_4)
        clarifications_t2 = res_4.get("clarification_requests", [])

        # After unconditional ZIP fix: both zip_code and income are asked on Turn 2
        # (ZIP is missing and not asked; pacing ceiling allows up to 2 per turn)
        asked_keys_t2 = [q["fact_key"] for q in clarifications_t2]
        self.assertIn("zip_code", asked_keys_t2)
        self.assertIn("household_gross_monthly_income", asked_keys_t2)
        self.assertLessEqual(len(clarifications_t2), 2)

    def test_e2e_acute_eviction_urgency_flow(self):
        """
        Scenario 2: Acute eviction notice reported.
        Flow: Prioritizes notice details, records notice date and overdue amount accurately.
        """
        turn_1_input = (
            "My landlord gave me a 3-day notice to pay or quit yesterday and threatened to lock us out if we don't leave."
        )

        req_a1 = {
            "request_id": "req-ev-01",
            "run_id": "run-e2e-002",
            "case_id": "case-e2e-002",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": turn_1_input},
        }
        res_a1 = handle_agent_1(req_a1)["result"]

        facts_map = {f["field"]: f["value"] for f in res_a1["factual_claims"]}
        self.assertTrue(facts_map.get("has_written_eviction_notice"))

        req_a2 = {
            "request_id": "req-ev-02",
            "run_id": "run-e2e-002",
            "case_id": "case-e2e-002",
            "case_version": 1,
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": res_a1["proposed_needs"],
                "case_facts": res_a1["factual_claims"],
                "already_asked": [],
                "candidate_requirements": [],
            },
        }
        res_a2 = handle_agent_2(req_a2)
        clarifications = res_a2.get("clarification_requests", [])

        # After notice-type extraction fix: Agent 1 extracts eviction_notice_type="3_day_pay_or_quit"
        # from story, so Agent 2 will NOT re-ask for it; instead asks for zip_code + income.
        asked_keys = [q["fact_key"] for q in clarifications]
        self.assertNotIn("eviction_notice_type", asked_keys)
        self.assertIn("zip_code", asked_keys)
        self.assertLessEqual(len(clarifications), 2)

        # Turn 2: Notice date + amount due volunteered
        turn_2_input = "The notice date is November 6, 2026, and the amount due is $1,600."
        req_parse = {
            "request_id": "req-ev-03",
            "run_id": "run-e2e-002",
            "case_id": "case-e2e-002",
            "case_version": 2,
            "role_id": "agent_1",
            "task_type": "parse_clarification_answer",
            "payload": {
                "answer_text": turn_2_input,
                "pending_fact_keys": ["eviction_notice_type"],
            },
        }
        res_parse = handle_agent_1(req_parse)["result"]
        parsed_facts = {f["field"]: f["value"] for f in res_parse.get("factual_claims", [])}

        self.assertEqual(parsed_facts.get("eviction_notice_date"), "2026-11-06")
        # After arrears fix: "amount due is $1,600" maps to rent_arrears_amount, not rent_amount_monthly
        self.assertEqual(parsed_facts.get("rent_arrears_amount"), 1600)
        self.assertNotIn("rent_amount_monthly", parsed_facts)


if __name__ == "__main__":
    unittest.main()