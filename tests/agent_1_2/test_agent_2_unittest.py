"""
Standard-Library Unittest Suite for Agent 2 (v6.1)
Zero external dependencies (Runs via `python -m unittest discover -s tests -t .`).
"""
import unittest

from navigator.agents.agent_1_2.agent_2 import handle_agent_2

class TestAgent2(unittest.TestCase):

    def test_deduplication_and_filtering(self):
        req = {
            "request_id": "req-0002",
            "run_id": "run-0001",
            "case_id": "case-demo-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": [
                    {"need_id": "need_003", "category": "food_assistance", "description": "Food"}
                ],
                "case_facts": [
                    {"field": "zip_code", "value": "95823"},
                    {"field": "employment_status", "value": "laid_off"},
                    {"field": "household_gross_monthly_income", "value": 1200},
                ],
                "already_asked": ["rent_amount_monthly"],
                "candidate_requirements": [
                    {"program_id": "prog_rent", "fact_key": "zip_code", "verified_rule_ref": "rule_geo"},
                    {"program_id": "prog_aid", "fact_key": "has_written_eviction_notice", "verified_rule_ref": "rule_evict"},
                ],
            },
        }
        res = handle_agent_2(req)
        self.assertEqual(res["status"], "needs_clarification")
        self.assertEqual(len(res["clarification_requests"]), 1)
        self.assertEqual(res["clarification_requests"][0]["fact_key"], "has_written_eviction_notice")
        self.assertFalse(res["result"]["optional_food_check"])

    def test_missing_income_question_generation(self):
        req = {
            "request_id": "req-income-q",
            "run_id": "run-0001",
            "case_id": "case-demo-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": [{"need_id": "need_001", "category": "income_assistance"}],
                "case_facts": [{"field": "zip_code", "value": "95823"}],
                "already_asked": [],
                "candidate_requirements": [],
            },
        }
        res = handle_agent_2(req)
        self.assertEqual(res["status"], "needs_clarification")
        self.assertEqual(len(res["clarification_requests"]), 1)
        self.assertEqual(res["clarification_requests"][0]["fact_key"], "household_gross_monthly_income")
        self.assertFalse(res["clarification_requests"][0]["can_skip"])

if __name__ == "__main__":
    unittest.main()
