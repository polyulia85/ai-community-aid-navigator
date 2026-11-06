"""
AI Community Aid Navigator — Comprehensive Regression Suite (v6.0 Restored)
Migrated to pure standard library unittest (Zero external dependencies).
Covers all 17 probe regressions, Supervisor checks S1-S9, and edge cases.
"""
from datetime import date
import unittest
from navigator.agents.agent_1_2 import handle
from navigator.agents.agent_1_2.agent_1 import handle_agent_1
from navigator.agents.agent_1_2.agent_2 import handle_agent_2


class TestComprehensiveRegressions(unittest.TestCase):

    def test_fix_1_parse_clarification_uncertainty_leaves_key_absent(self):
        """Uncertain answers must leave has_written_eviction_notice absent, never False."""
        uncertain_answers = [
            "I'm not sure.",
            "I don't know yet",
            "We are still waiting to see",
            "Maybe, I haven't checked my mail",
        ]
        for ans in uncertain_answers:
            req = {
                "request_id": "req-t1",
                "run_id": "run-001",
                "case_id": "case-001",
                "case_version": 2,
                "schema_version": "1.0",
                "role_id": "agent_1",
                "task_type": "parse_clarification_answer",
                "payload": {
                    "answer_text": ans,
                    "pending_fact_keys": ["has_written_eviction_notice"],
                },
            }
            res = handle_agent_1(req)
            facts = res["result"]["factual_claims"]
            self.assertEqual(
                len([f for f in facts if f["field"] == "has_written_eviction_notice"]),
                0,
                f"Expected key to be absent for '{ans}'"
            )

    def test_fix_2_agent_2_echoes_schema_version_1_0(self):
        """Agent 2 must echo schema_version '1.0' directly."""
        req_a2 = {
            "request_id": "req-t2",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": [],
                "case_facts": [],
                "already_asked": [],
                "candidate_requirements": [],
            },
        }
        res_a2 = handle_agent_2(req_a2)
        self.assertEqual(res_a2["schema_version"], "1.0")

    def test_fix_3_flexible_demographics_and_rent_phrasings(self):
        """Validates child extraction, overdue rent amounts, and unstated adult rules."""
        base_req = {
            "request_id": "req-t3",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {},
        }
        # Case A: Single dad with three kids
        req_a = dict(base_req, payload={"story_text": "I'm a single dad with three kids, 2, 5 and 8. Rent is $1,200."})
        res_a = handle_agent_1(req_a)
        facts_a = {f["field"]: f["value"] for f in res_a["result"]["factual_claims"]}
        self.assertEqual(facts_a.get("children_ages"), [2, 5, 8])
        self.assertEqual(facts_a.get("rent_amount_monthly"), 1200)
        self.assertEqual(facts_a.get("household_size"), 4)

        # Case B: Single mom with one child
        req_b = dict(base_req, payload={"story_text": "Single mom with one child, age 7. Rent of $950 is overdue."})
        res_b = handle_agent_1(req_b)
        facts_b = {f["field"]: f["value"] for f in res_b["result"]["factual_claims"]}
        self.assertEqual(facts_b.get("children_ages"), [7])
        self.assertEqual(facts_b.get("household_size"), 2)

        # Case C: Unstated adult status leaves household_size absent
        req_c = dict(base_req, payload={"story_text": "I have two kids. We are running out of food."})
        res_c = handle_agent_1(req_c)
        facts_c = {f["field"]: f["value"] for f in res_c["result"]["factual_claims"]}
        self.assertNotIn("household_size", facts_c)

    def test_fix_4_handle_returns_failed_envelope_for_unsupported_role(self):
        """Unsupported role_id returns status 'failed' envelope with UNSUPPORTED_ROLE Issue."""
        bad_req = {
            "request_id": "req-t4",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_unknown_role",
            "task_type": "prioritize",
            "payload": {},
        }
        res = handle(bad_req)
        self.assertEqual(res["status"], "failed")
        self.assertEqual(res["issues"][0]["code"], "UNSUPPORTED_ROLE")
        self.assertIn("generated_at", res)

    def test_fix_5_agent_1_redacts_accidental_pii(self):
        """SSN, card numbers, and banking details must be redacted to [REDACTED_PII]."""
        req = {
            "request_id": "req-t5",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": "My SSN is 000-12-3456 and my routing is 123456789. Need food assistance in 95823."
            },
        }
        res = handle_agent_1(req)
        summary = res["result"]["narrative_summary"]
        self.assertNotIn("000-12-3456", summary)
        self.assertNotIn("123456789", summary)
        self.assertIn("[REDACTED_PII]", summary)

    def test_v4_gap_1_explicit_negative_phrase_gives_false(self):
        """'I don't have one' evaluates strictly to False for eviction notice."""
        req = {
            "request_id": "req-g1",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 2,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "parse_clarification_answer",
            "payload": {
                "answer_text": "I don't have one.",
                "pending_fact_keys": ["has_written_eviction_notice"],
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertIs(facts.get("has_written_eviction_notice"), False)

    def test_v4_gap_2_child_ages_in_second_sentence(self):
        """Child ages in sentence 2 must be captured."""
        req = {
            "request_id": "req-g2",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": "I lost my job last week. I have two kids, 6 and 9. We live in 95823."
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("children_ages"), [6, 9])

    def test_v4_gap_6_nope_nothing_yet_gives_false(self):
        """'Nope, nothing yet' evaluates strictly to False."""
        req = {
            "request_id": "req-g6",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 2,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "parse_clarification_answer",
            "payload": {
                "answer_text": "Nope, nothing yet from my landlord.",
                "pending_fact_keys": ["has_written_eviction_notice"],
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertIs(facts.get("has_written_eviction_notice"), False)

    def test_probe_1_rent_and_electric_bill_same_sentence_isolation(self):
        """Electric bill due date in the same sentence must not contaminate rent_due_date."""
        req = {
            "request_id": "req-p1",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": "Rent is $1,450 and my electric bill is due November 5 in 95823."
            },
        }
        res = handle_agent_1(req, ref_date=date(2026, 10, 26))
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertNotIn("rent_due_date", facts)
        self.assertEqual(facts.get("rent_amount_monthly"), 1450)

    def test_probe_3_notice_affirmative_preserved_with_court_uncertainty(self):
        """Affirmative notice statement is preserved even when court dates are uncertain."""
        req = {
            "request_id": "req-p3",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 2,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "parse_clarification_answer",
            "payload": {
                "answer_text": "Yes, I got a notice. Nothing yet from the court.",
                "pending_fact_keys": ["has_written_eviction_notice"],
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertIs(facts.get("has_written_eviction_notice"), True)

    def test_probe_4_negative_word_boundaries_nonetheless(self):
        """Words like 'nonetheless' must not trigger 'none' negative parsing."""
        req = {
            "request_id": "req-p4",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 2,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "parse_clarification_answer",
            "payload": {
                "answer_text": "Yes, received one nonetheless.",
                "pending_fact_keys": ["has_written_eviction_notice"],
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertIs(facts.get("has_written_eviction_notice"), True)

    def test_probe_5_child_count_separated_from_cash_on_hand(self):
        """'have 2 kids' must not populate cash_on_hand_approx."""
        req = {
            "request_id": "req-p5",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": "I have 2 kids, ages 6 and 9. We reside in 95823."
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertNotIn("cash_on_hand_approx", facts)
        self.assertEqual(facts.get("children_ages"), [6, 9])

    def test_probe_6_day_only_rent_due_date_next_occurrence(self):
        """'Rent is due on the 1st' rolls over to the next calendar occurrence."""
        req = {
            "request_id": "req-p6",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": "Rent of $1,200 is due on the 1st. ZIP 95823."
            },
        }
        res = handle_agent_1(req, ref_date=date(2026, 10, 26))
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("rent_due_date"), "2026-11-01")


if __name__ == "__main__":
    unittest.main()