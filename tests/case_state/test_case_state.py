"""Tests for Case State v0.1 (owner: Silver). Fixed timestamps; nothing depends on today's date."""
import json
import sqlite3
import unittest

from navigator.case_state import store

T0, T1, T2, T3 = "2026-11-06T10:00:00-08:00", "2026-11-06T10:05:00-08:00", "2026-11-06T10:10:00-08:00", "2026-11-06T10:15:00-08:00"
FACTS = [{"fact_id": "fact_001", "field": "zip_code", "value": "95823", "confirmation_status": "proposed", "source": "user_statement"},
         {"fact_id": "fact_002", "field": "household_size", "value": 3, "confirmation_status": "proposed", "source": "user_statement"},
         {"fact_id": "fact_003", "field": "household_gross_monthly_income", "value": None, "confirmation_status": "proposed", "source": "user_statement"}]
NEEDS = [{"need_id": "need_001", "category": "income_assistance", "description": "Lost job", "confirmation_status": "proposed", "urgency": "high"},
         {"need_id": "need_002", "category": "housing_assistance", "subcategory": "rental_assistance", "description": "Rent due",
          "confirmation_status": "proposed", "urgency": "immediate"},
         {"need_id": "need_003", "category": "food_assistance", "description": "Low on food", "confirmation_status": "proposed", "urgency": "immediate"}]
PLAN = {"plan_version": 1, "action_cards": [
    {"card_id": "card_01", "program_id": "prog_housing_coordaccess_sac_001", "action_title": "Call 2-1-1 and press 8", "order_group": "first", "related_need_ids": ["need_002"]},
    {"card_id": "card_02", "program_id": "prog_food_calfresh_sac_001", "action_title": "Apply for CalFresh", "order_group": "first", "related_need_ids": ["need_003"]},
    {"card_id": "card_03", "program_id": "prog_income_edd_ui_ca_001", "action_title": "Apply for unemployment", "order_group": "parallel", "related_need_ids": ["need_001"]}]}


class CaseStateTests(unittest.TestCase):
    def setUp(self):
        self.db = store.connect()
        store.create_case(self.db, "case-001", T0)

    def test_every_change_bumps_the_version_and_is_logged(self):
        self.assertEqual(store.add_facts(self.db, "case-001", FACTS, T1), 2)
        self.assertEqual(store.save_needs(self.db, "case-001", NEEDS, T2), 3)
        types = [e["event_type"] for e in store.history(self.db, "case-001")]
        self.assertEqual(types, ["case_created", "facts_added", "needs_saved"])

    def test_unknown_stays_unknown(self):
        store.add_facts(self.db, "case-001", FACTS, T1)
        income = [f for f in store.current_facts(self.db, "case-001") if f["field"] == "household_gross_monthly_income"][0]
        self.assertIsNone(income["value"])  # never 0 or false

    def test_changed_fact_supersedes_instead_of_overwriting(self):
        store.add_facts(self.db, "case-001", FACTS, T1)
        store.add_facts(self.db, "case-001", [dict(FACTS[1], value=4, confirmation_status="confirmed", source="user_confirmed")], T2)
        size = [f for f in store.current_facts(self.db, "case-001") if f["field"] == "household_size"]
        self.assertEqual(len(size), 1)
        self.assertEqual((size[0]["value"], size[0]["confirmation_status"]), (4, "confirmed"))
        rows = self.db.execute("SELECT confirmation_status FROM case_facts WHERE fact_id = 'fact_002' ORDER BY row_id").fetchall()
        self.assertEqual([r[0] for r in rows], ["superseded", "confirmed"])  # old value kept as history

    def test_forbidden_personal_fields_are_rejected(self):
        with self.assertRaises(store.CaseStateError):
            store.add_facts(self.db, "case-001", [{"fact_id": "f9", "field": "ssn", "value": "x", "confirmation_status": "proposed"}], T1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM case_facts").fetchone()[0], 0)

    def test_plan_keeps_the_needs_layer(self):
        store.save_needs(self.db, "case-001", NEEDS, T1)
        store.save_plan(self.db, "case-001", "plan-001", PLAN, "PASS", True, T2,
                        need_order=[("need_002", "immediate"), ("need_003", "immediate"), ("need_001", "high")])
        view = store.plan_by_need(self.db, "plan-001")
        self.assertEqual([n["need_id"] for n in view], ["need_002", "need_003", "need_001"])
        self.assertEqual([c["card_id"] for c in view[0]["cards"]], ["card_01"])
        stored = json.loads(self.db.execute("SELECT plan_json FROM plan_versions").fetchone()[0])
        self.assertEqual(stored, PLAN)  # exactly as delivered

    def test_plan_versions_count_up_and_old_plans_are_kept(self):
        store.save_plan(self.db, "case-001", "plan-001", PLAN, "PASS", True, T1, [])
        self.assertEqual(store.save_plan(self.db, "case-001", "plan-002", PLAN, "FLAG", False, T2, []), 2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM plan_versions").fetchone()[0], 2)
        self.assertEqual(store.history(self.db, "case-001")[-1]["event_type"], "plan_withheld")

    def test_only_the_user_sets_progress_and_history_shows_it(self):
        store.set_card_status(self.db, "case-001", "card_02", "in_progress", T1)
        store.set_card_status(self.db, "case-001", "card_02", "completed", T2)
        with self.assertRaises(store.CaseStateError):
            store.set_card_status(self.db, "case-001", "card_02", "not_started", T3, actor="agent_8")
        with self.assertRaises(store.CaseStateError):
            store.set_card_status(self.db, "case-001", "card_02", "approved", T3)
        changes = [json.loads(e["details_json"]) for e in store.history(self.db, "case-001") if e["event_type"] == "status_changed"]
        self.assertEqual([(c["from"], c["to"]) for c in changes], [(None, "in_progress"), ("in_progress", "completed")])

    def test_skipped_question_stays_unknown(self):
        store.record_clarification(self.db, "case-001", "has_written_eviction_notice", "Did you get a written notice?", T1, skipped=True)
        row = self.db.execute("SELECT answer_json, skipped FROM clarifications").fetchone()
        self.assertEqual((row[0], row[1]), (None, 1))

    def test_history_is_append_only(self):
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute("DELETE FROM events")
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute("UPDATE events SET actor = 'x'")

    def test_unknown_case_is_an_error(self):
        with self.assertRaises(store.CaseStateError):
            store.add_facts(self.db, "case-404", FACTS, T1)


if __name__ == "__main__":
    unittest.main()
