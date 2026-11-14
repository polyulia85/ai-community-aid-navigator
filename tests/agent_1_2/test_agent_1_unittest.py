"""
Standard-Library Unittest Suite for Agent 1 (v6.1)
Zero external dependencies (Runs via `python -m unittest discover -s tests -t .`).
"""
from datetime import date
import unittest

from navigator.agents.agent_1_2.agent_1 import handle_agent_1

class TestAgent1(unittest.TestCase):

    def test_sacramento_benchmark(self):
        req = {
            "request_id": "req-0001",
            "run_id": "run-0001",
            "case_id": "case-demo-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": (
                    "I'm a single mom in Sacramento, ZIP 95823, with two kids, 6 and 9. "
                    "I was laid off from my warehouse job last Friday. Rent of $1,450 is due on "
                    "November 1 and I only have about $300 left. We're also running low on food "
                    "this week. I don't know where to start."
                ),
                "locale": "en-US",
            },
        }
        res = handle_agent_1(req, ref_date=date(2026, 10, 23))
        self.assertEqual(res["status"], "completed")
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("zip_code"), "95823")
        self.assertEqual(facts.get("household_size"), 3)
        self.assertEqual(facts.get("children_ages"), [6, 9])
        self.assertEqual(facts.get("rent_amount_monthly"), 1450)
        self.assertEqual(facts.get("cash_on_hand_approx"), 300)
        self.assertEqual(facts.get("rent_due_date"), "2026-11-01")

    def test_overdue_rent_date_stays_in_past(self):
        req = {
            "request_id": "req-overdue",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": "Rent of $1,450 was due on November 1. ZIP 95823."
            },
        }
        res = handle_agent_1(req, ref_date=date(2026, 11, 3))
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("rent_due_date"), "2026-11-01")
        needs = res["result"]["proposed_needs"]
        housing = [n for n in needs if n["category"] == "housing_assistance"][0]
        self.assertEqual(housing["urgency"], "immediate")
        self.assertEqual(housing["urgency_reason"], "Rent is overdue")

    def test_broadened_life_safety_signals(self):
        phrases = [
            "I'm thinking about ending it all",
            "I can't go on like this",
            "I'm scared he will come back and hurt us",
            "I'm scared she will come back and hurt us",
            "He will come back and hurt us",
            "She will come back and hurt us",
            "I might hurt someone",
            "I want to kill myself",
            "My partner hits me",
            "I feel unsafe at home",
            "He said he will hurt us if we don't leave.",
            "He said he will hurt us if we don\u2019t leave.",
            "The landlord threatened to attack us.",
            "My husband threatened to kill himself.",
            "He threatened to hurt my son.",
            "He will hurt my daughter.",
            "She said she would hurt the children.",
            "He is going to hurt my baby.",
            "He threatened to kill my children.",
            "They threatened to kill my dog.",
            "My boyfriend will hurt me.",
            "My girlfriend is going to hurt the kids.",
            "My boyfriend said he would kill us.",
        ]
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                req = {
                    "request_id": "req-safe",
                    "run_id": "run-001",
                    "case_id": "case-001",
                    "case_version": 1,
                    "role_id": "agent_1",
                    "task_type": "understand_story",
                    "payload": {"story_text": phrase},
                }
                res = handle_agent_1(req)
                flags = res["result"].get("safety_or_official_deadline_flags", [])
                self.assertGreaterEqual(len(flags), 1, f"Failed to flag: {phrase}")
                self.assertEqual(flags[0]["type"], "safety")
                self.assertNotIn("safety_or_deadline_flags", res["result"])

    def test_safety_signals_negative_everyday_sentences(self):
        benign_phrases = [
            "my landlord said he will come back to fix the heater",
            "my landlord said she will come back to fix the heater",
            "the contractor will come back tomorrow morning",
            "they will come back next week to inspect the property",
            "he will come back from work at 5pm",
            "They might harm my credit score if I miss rent.",
            "They will kill my hours at work.",
            "They are going to beat the deadline.",
            "The headache will kill me.",
            "This toothache will kill me.",
            "My backache is going to kill me.",
        ]
        for phrase in benign_phrases:
            with self.subTest(phrase=phrase):
                req = {
                    "request_id": "req-safe-neg",
                    "run_id": "run-001",
                    "case_id": "case-001",
                    "case_version": 1,
                    "role_id": "agent_1",
                    "task_type": "understand_story",
                    "payload": {"story_text": phrase},
                }
                res = handle_agent_1(req)
                flags = res["result"].get("safety_or_official_deadline_flags", [])
                safety_flags = [f for f in flags if f.get("type") == "safety"]
                self.assertEqual(
                    len(safety_flags),
                    0,
                    f"Unexpected safety flag on benign phrase: {phrase}",
                )

    def test_monthly_household_income_extraction(self):
        req_approx = {
            "request_id": "req-inc-1",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": "I make about $1,200 a month in 95823."},
        }
        res_approx = handle_agent_1(req_approx)
        facts_approx = {f["field"]: f for f in res_approx["result"]["factual_claims"]}
        self.assertIn("household_gross_monthly_income", facts_approx)
        self.assertEqual(facts_approx["household_gross_monthly_income"]["value"], 1200)
        self.assertTrue(facts_approx["household_gross_monthly_income"]["is_approximate"])

        req_zero = {
            "request_id": "req-inc-2",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": "I have no income right now."},
        }
        res_zero = handle_agent_1(req_zero)
        facts_zero = {f["field"]: f for f in res_zero["result"]["factual_claims"]}
        self.assertIn("household_gross_monthly_income", facts_zero)
        self.assertEqual(facts_zero["household_gross_monthly_income"]["value"], 0)

        req_none = {
            "request_id": "req-inc-3",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": "I need help paying rent in 95823."},
        }
        res_none = handle_agent_1(req_none)
        fields = [f["field"] for f in res_none["result"]["factual_claims"]]
        self.assertNotIn("household_gross_monthly_income", fields)

    def test_sleeping_in_car_housing_need(self):
        req = {
            "request_id": "req-car",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": "We are sleeping in our car tonight in 95823."},
        }
        res = handle_agent_1(req)
        needs = [n for n in res["result"]["proposed_needs"] if n["category"] == "housing_assistance"]
        self.assertGreaterEqual(len(needs), 1)
        self.assertEqual(needs[0]["subcategory"], "emergency_shelter")
        self.assertEqual(needs[0]["urgency"], "immediate")

    def test_housing_and_food_both_detected(self):
        """Housing Need Regex + Contract 4.1: 'housing and food' produces both needs,
        ambiguity_flags is an array of objects with field/quote/note."""
        req = {
            "request_id": "req-hf-1",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": "I have problems with housing and food. I need help."},
        }
        res = handle_agent_1(req)
        self.assertEqual(res["status"], "completed")
        categories = [n["category"] for n in res["result"]["proposed_needs"]]
        self.assertIn("housing_assistance", categories)
        self.assertIn("food_assistance", categories)
        # Contract 4.1: ambiguity_flags must be an array of objects
        af = res["result"]["ambiguity_flags"]
        self.assertIsInstance(af, list)
        self.assertGreater(len(af), 0)
        self.assertIsInstance(af[0], dict)
        self.assertIn("field", af[0])
        self.assertIn("quote", af[0])
        self.assertIn("note", af[0])
        self.assertEqual(af[0]["note"], "unspecified_hardship_cause")

    def test_passive_hours_cut_clears_unspecified_hardship(self):
        """Passive hours-cut phrasing ('My hours were cut at work') must be recognized
        as a root cause, so unspecified_hardship_cause is NOT flagged."""
        req = {
            "request_id": "req-hc-1",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": "My hours were cut at work and I can't pay rent."},
        }
        res = handle_agent_1(req)
        self.assertEqual(res["status"], "completed")
        af_notes = [
            (f["note"] if isinstance(f, dict) else f)
            for f in res["result"]["ambiguity_flags"]
        ]
        self.assertNotIn("unspecified_hardship_cause", af_notes)

    def test_zip_code_answer_during_income_clarification(self):
        """Income Sanity Guard: answer '95660' when income is pending sets
        zip_code='95660' and does NOT set household_gross_monthly_income."""
        req = {
            "request_id": "req-zip-income-1",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "parse_clarification_answer",
            "payload": {
                "answer_text": "95660",
                "pending_fact_keys": ["household_gross_monthly_income"],
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("zip_code"), "95660")
        self.assertNotIn("household_gross_monthly_income", facts)

    def test_bad_input_handling(self):
        res_null = handle_agent_1({
            "request_id": "req-1", "run_id": "r-1", "case_id": "c-1", "case_version": 1,
            "role_id": "agent_1", "task_type": "understand_story", "payload": {"story_text": None}
        })
        self.assertEqual(res_null["status"], "failed")
        self.assertEqual(res_null["issues"][0]["code"], "EMPTY_STORY")

        res_no_pl = handle_agent_1({
            "request_id": "req-2", "run_id": "r-1", "case_id": "c-1", "case_version": 1,
            "role_id": "agent_1", "task_type": "understand_story"
        })
        self.assertEqual(res_no_pl["status"], "failed")
        self.assertEqual(res_no_pl["issues"][0]["code"], "MISSING_PAYLOAD")

        res_bad_date = handle_agent_1({
            "request_id": "req-3", "run_id": "r-1", "case_id": "c-1", "case_version": 1,
            "role_id": "agent_1", "task_type": "understand_story",
            "payload": {"story_text": "Laid off in 95823", "ref_date": "not-a-date"}
        })
        self.assertEqual(res_bad_date["status"], "failed")
        self.assertEqual(res_bad_date["issues"][0]["code"], "INVALID_REF_DATE")

    def test_3_day_notice_extracts_eviction_notice_type(self):
        """Defect fix: '3-day notice to pay or quit' must extract both
        has_written_eviction_notice=True and eviction_notice_type='3_day_pay_or_quit'."""
        req = {
            "request_id": "req-evict-type-1",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": (
                    "My landlord gave me a 3-day notice to pay or quit yesterday "
                    "and threatened to lock us out if we don't pay."
                )
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertTrue(facts.get("has_written_eviction_notice"))
        self.assertEqual(facts.get("eviction_notice_type"), "3_day_pay_or_quit")

    def test_arrears_amount_not_rent_amount_monthly(self):
        """Defect fix: 'the amount due is $1,600' in a clarification answer must extract
        rent_arrears_amount and leave rent_amount_monthly untouched."""
        req = {
            "request_id": "req-arrears-1",
            "run_id": "run-001",
            "case_id": "case-001",
            "case_version": 1,
            "role_id": "agent_1",
            "task_type": "parse_clarification_answer",
            "payload": {
                "answer_text": "The notice date is November 6, 2026, and the amount due is $1,600.",
                "pending_fact_keys": ["eviction_notice_type"],
            },
        }
        res = handle_agent_1(req)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("rent_arrears_amount"), 1600)
        self.assertNotIn("rent_amount_monthly", facts)

    def test_clarification_food_keywords_add_food_assistance_need(self):
        """Defect fix: clarification answer with 'groceries' / 'food' / 'hungry'
        must append food_assistance to proposed_needs."""
        for phrase in [
            "we have no groceries left for the kids",
            "we don't have food at home",
            "the kids are hungry",
        ]:
            with self.subTest(phrase=phrase):
                req = {
                    "request_id": "req-food-claric",
                    "run_id": "run-001",
                    "case_id": "case-001",
                    "case_version": 1,
                    "role_id": "agent_1",
                    "task_type": "parse_clarification_answer",
                    "payload": {
                        "answer_text": phrase,
                        "pending_fact_keys": ["triggering_circumstances"],
                    },
                }
                res = handle_agent_1(req)
                needs = res["result"].get("proposed_needs", [])
                cats = [n["category"] for n in needs]
                self.assertIn(
                    "food_assistance", cats,
                    f"Expected food_assistance in proposed_needs for: {phrase}",
                )
    def test_lockout_threat_is_housing_not_safety_flag(self):
        req = {
            "request_id": "req-lockout-threat",
            "run_id": "run-001",
            "case_id": "case-lockout-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": "My landlord threatened to lock us out",
                "locale": "en-US",
            },
        }
        res = handle_agent_1(req)
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["result"]["safety_or_official_deadline_flags"], [])
        needs = res["result"]["proposed_needs"]
        self.assertTrue(any(n["category"] == "housing_assistance" for n in needs))

    def test_physical_harm_threat_still_raises_safety_flag(self):
        req = {
            "request_id": "req-harm-threat",
            "run_id": "run-001",
            "case_id": "case-harm-001",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {
                "story_text": "My landlord threatened to hurt us",
                "locale": "en-US",
            },
        }
        res = handle_agent_1(req)
        self.assertEqual(res["status"], "completed")
        flags = res["result"]["safety_or_official_deadline_flags"]
        self.assertTrue(any(f.get("type") == "safety" for f in flags))


if __name__ == "__main__":
    unittest.main()
