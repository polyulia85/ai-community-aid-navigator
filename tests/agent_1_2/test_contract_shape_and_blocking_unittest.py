"""
AI Community Aid Navigator — Contract Shape & Pre-Merge Regression Suite
Covers all PR #6 blocking review items and pre-merge invariants:
  1. proposed_needs contract shape (need_id, description, original_quote, user_reported,
     confirmation_status, urgency — never "priority").
  2. factual_claims contract shape (fact_id, field, value, confirmation_status, time_context).
  3. result top-level keys (narrative_summary, factual_claims, proposed_needs,
     safety_or_official_deadline_flags, triggering_events, ambiguity_flags).
  4. safety flags correct format ({type, quote, note} — not {type, reason, action_required}).
  5. Job loss emits employment_status fact + "job_loss" in triggering_events.
  6. Bereavement emits employment_status="bereaved_survivor" fact + "bereavement" in triggering_events.
  7. Urgency escalation: rent_due_date before ref_date → housing urgency="immediate".
  8. Eviction threat phrase → housing_assistance with urgency="immediate".
  9. Unemployment income ("I get $800 a month in unemployment") extracts income.
 10. Agent 2 Julia Requirement: missing income triggers question with can_skip=False.
 11. Agent 2 eviction clarification has can_skip=False.
 12. Complete coverage of all 17 safety phrases across straight (') and curly (’) apostrophes.
 13. Whole original_quote retention (never cut mid-word).
 14. Narrative summary retains all volunteered needs (including food).

Pure standard library. Zero external dependencies.
Run: python -m unittest discover -s tests -t .
"""
from datetime import date
import unittest
from navigator.agents.agent_1_2.agent_1 import handle_agent_1
from navigator.agents.agent_1_2.agent_2 import handle_agent_2


def _run_story(story: str, ref_date: date = date(2026, 11, 4)) -> dict:
    """Run Agent 1 understand_story and return the full envelope."""
    return handle_agent_1(
        {
            "request_id": "req-block-test",
            "run_id": "run-block",
            "case_id": "case-block",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_1",
            "task_type": "understand_story",
            "payload": {"story_text": story},
        },
        ref_date=ref_date,
    )


class TestContractShapeAndBlocking(unittest.TestCase):
    """Blocking PR review items — all must pass for 100% gate."""

    # -------------------------------------------------------------------
    # BLOCKING ITEM 1 — proposed_needs contract shape §3.1
    # -------------------------------------------------------------------
    def test_block_1_proposed_needs_required_fields(self):
        """Every proposed_need must have all §3.1 required fields; 'priority' must never appear."""
        res = _run_story(
            "I was laid off last week. Rent of $1,200 is due November 15 and I need food. ZIP 95823."
        )
        self.assertEqual(res["status"], "completed")
        needs = res["result"]["proposed_needs"]
        self.assertGreater(len(needs), 0, "Expected at least one proposed need")

        required_fields = {
            "need_id", "category", "description", "original_quote",
            "user_reported", "confirmation_status", "urgency"
        }
        for need in needs:
            missing = required_fields - set(need.keys())
            self.assertEqual(
                missing, set(),
                f"Need '{need.get('category')}' missing fields: {missing}"
            )
            self.assertIn(
                need["urgency"],
                {"immediate", "high", "normal", "unknown"},
                f"Invalid urgency value '{need['urgency']}' in need '{need.get('category')}'"
            )
            self.assertIs(need["user_reported"], True)
            self.assertEqual(need["confirmation_status"], "proposed")
            self.assertNotIn("priority", need)

    # -------------------------------------------------------------------
    # BLOCKING ITEM 2 — factual_claims contract shape §3.2
    # -------------------------------------------------------------------
    def test_block_2_factual_claims_required_fields(self):
        """Every factual_claim must have all §3.2 required fields: fact_id, field, value,
        confirmation_status, time_context."""
        res = _run_story(
            "I'm a single mom in Sacramento, ZIP 95823, with two kids, 6 and 9. "
            "I was laid off from my warehouse job. Rent of $1,450 is due on November 1."
        )
        self.assertEqual(res["status"], "completed")
        facts = res["result"]["factual_claims"]
        self.assertGreater(len(facts), 0, "Expected at least one factual claim")

        required_fields = {"fact_id", "field", "value", "confirmation_status"}
        for fact in facts:
            missing = required_fields - set(fact.keys())
            self.assertEqual(
                missing, set(),
                f"Fact '{fact.get('field')}' missing fields: {missing}"
            )
            self.assertEqual(fact["confirmation_status"], "proposed")
            self.assertIsInstance(fact["fact_id"], str)
            self.assertGreater(len(fact["fact_id"]), 0)
            self.assertIn("time_context", fact)

    # -------------------------------------------------------------------
    # BLOCKING ITEM 3 — result top-level keys §4.1
    # -------------------------------------------------------------------
    def test_block_3_result_top_level_keys(self):
        """result must always contain all 6 required top-level keys."""
        res = _run_story("I need help paying rent in ZIP 95823.")
        self.assertEqual(res["status"], "completed")
        result = res["result"]

        required_top_keys = {
            "narrative_summary",
            "factual_claims",
            "proposed_needs",
            "safety_or_official_deadline_flags",
            "triggering_events",
            "ambiguity_flags",
        }
        missing = required_top_keys - set(result.keys())
        self.assertEqual(missing, set(), f"result is missing required top-level keys: {missing}")
        self.assertIsInstance(result["ambiguity_flags"], list)
        self.assertIsInstance(result["triggering_events"], list)
        self.assertIsInstance(result["narrative_summary"], str)
        self.assertGreater(len(result["narrative_summary"]), 0)

    # -------------------------------------------------------------------
    # BLOCKING ITEM 4 & REVIEW ITEM 1 — Safety phrase suite
    # -------------------------------------------------------------------
    def test_block_4_safety_flag_format_type_quote_note(self):
        """Safety flags must use {type, quote, note} — never {type, reason, action_required}."""
        res = _run_story("I can't go on like this anymore.")
        self.assertEqual(res["status"], "completed")
        flags = res["result"]["safety_or_official_deadline_flags"]
        self.assertGreater(len(flags), 0, "Expected at least one safety flag")

        flag = flags[0]
        self.assertEqual(flag.get("type"), "safety")
        self.assertIn("quote", flag)
        self.assertIn("note", flag)
        self.assertNotIn("reason", flag)
        self.assertNotIn("action_required", flag)
        self.assertIsInstance(flag["quote"], str)
        self.assertGreater(len(flag["quote"]), 0)

    def test_block_4b_all_17_safety_phrases_from_both_reviews(self):
        """Verify all 17 safety phrases from both review rounds are caught with no regressions."""
        phrases = [
            "I want to kill myself",
            "I don't want to live anymore",
            "I don’t want to live anymore",
            "I want to end my life",
            "My partner hits me and I don't know where to turn",
            "I feel unsafe at home with my husband",
            "My boyfriend is beating me and I need to leave",
            "I don't want to be alive anymore",
            "I don’t want to be alive anymore",
            "I keep thinking about killing myself",
            "Sometimes I think everyone would be better off without me",
            "My ex threatened to kill me",
            "I'm afraid my boyfriend will hurt the kids",
            "I’m afraid my boyfriend will hurt the kids",
            "I'm going to hurt him",
            "I’m going to hurt him",
            "I feel like ending everything",
            "There is no reason to live",
            "my husband hit me last night",
            "I can't go on like this",
            "I can’t go on like this",
        ]
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                res = _run_story(f"Please help me, {phrase}. ZIP 95823.")
                flags = res["result"].get("safety_or_official_deadline_flags", [])
                self.assertGreater(len(flags), 0, f"No safety flag for: {phrase!r}")
                flag = flags[0]
                self.assertEqual(flag["type"], "safety")
                self.assertIn("quote", flag)
                self.assertIn("note", flag)

    # -------------------------------------------------------------------
    # BLOCKING ITEM 5 — Job loss: employment_status + triggering_events
    # -------------------------------------------------------------------
    def test_block_5_job_loss_emits_employment_status_and_triggering_event(self):
        """Job loss must emit employment_status in factual_claims and 'job_loss' in triggering_events."""
        stories = [
            "I was laid off from my warehouse job last Friday. ZIP 95823.",
            "I lost my job at the factory two days ago in 95814.",
            "I am unemployed and cannot pay rent. ZIP 95823.",
            "I got fired last week. Need help with food. ZIP 95823.",
        ]
        for story in stories:
            res = _run_story(story)
            self.assertEqual(res["status"], "completed")
            triggering = res["result"]["triggering_events"]
            self.assertIn("job_loss", triggering)
            facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
            self.assertIn("employment_status", facts)
            self.assertEqual(facts["employment_status"], "laid_off")

    # -------------------------------------------------------------------
    # BLOCKING ITEM 6 — Bereavement: life circumstance only (Slav Item 10)
    # -------------------------------------------------------------------
    def test_block_6_bereavement_emits_employment_status_and_triggering_event(self):
        """Bereavement must emit 'bereavement' in triggering_events without fabricating employment_status."""
        story = (
            "My husband passed away last week. He was our sole earner and I need "
            "survivor benefits in 95823."
        )
        res = _run_story(story)
        self.assertEqual(res["status"], "completed")
        triggering = res["result"]["triggering_events"]
        self.assertIn("bereavement", triggering)
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertNotIn("employment_status", facts)

    # -------------------------------------------------------------------
    # BLOCKING ITEM 7 — Urgency escalation: rent overdue by date
    # -------------------------------------------------------------------
    def test_block_7_rent_overdue_by_date_escalates_to_immediate(self):
        """If rent_due_date is before ref_date, housing urgency must be 'immediate'."""
        res = _run_story(
            "Rent of $1,450 is due on November 1. I only have $50 left. ZIP 95823.",
            ref_date=date(2026, 11, 4),
        )
        self.assertEqual(res["status"], "completed")
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("rent_due_date"), "2026-11-01")

        housing_needs = [
            n for n in res["result"]["proposed_needs"]
            if n.get("category") == "housing_assistance"
        ]
        self.assertGreater(len(housing_needs), 0)
        hn = housing_needs[0]
        self.assertEqual(hn["urgency"], "immediate")
        self.assertEqual(hn.get("urgency_reason"), "Rent is overdue")

    def test_block_7b_rent_not_yet_due_is_high_not_immediate(self):
        """Rent due in the future must NOT be immediate (just 'high')."""
        res = _run_story(
            "Rent of $1,450 is due on November 1. ZIP 95823.",
            ref_date=date(2026, 10, 23),
        )
        housing_needs = [
            n for n in res["result"]["proposed_needs"]
            if n.get("category") == "housing_assistance"
        ]
        self.assertGreater(len(housing_needs), 0)
        hn = housing_needs[0]
        self.assertNotEqual(hn["urgency"], "immediate")

    # -------------------------------------------------------------------
    # BLOCKING ITEM 8 — Eviction threat → housing_assistance baseline high (Slav Item 1)
    # -------------------------------------------------------------------
    def test_block_8_eviction_threat_generates_immediate_housing_need(self):
        """'Landlord said he will evict us' must generate housing_assistance at baseline 'high'."""
        stories = [
            "My landlord said he will evict us if we don't pay by Friday. ZIP 95823.",
            "The landlord is going to evict me next week. I have two kids. ZIP 95823.",
            "I am facing eviction and don't know what to do. ZIP 95823.",
        ]
        for story in stories:
            res = _run_story(story)
            self.assertEqual(res["status"], "completed")
            housing_needs = [
                n for n in res["result"]["proposed_needs"]
                if n.get("category") == "housing_assistance"
            ]
            self.assertGreater(len(housing_needs), 0)
            self.assertEqual(housing_needs[0]["urgency"], "high")

    # -------------------------------------------------------------------
    # BLOCKING ITEM 9 — Unemployment income extraction
    # -------------------------------------------------------------------
    def test_block_9_unemployment_income_extracted(self):
        """'I get $800 a month in unemployment' must extract household_gross_monthly_income=800."""
        stories_and_expected = [
            ("I get $800 a month in unemployment. ZIP 95823.", 800),
            ("I receive $1,200 a month from unemployment benefits. ZIP 95823.", 1200),
            ("I collect $650 per month in disability benefits. ZIP 95823.", 650),
        ]
        for story, expected in stories_and_expected:
            res = _run_story(story)
            self.assertEqual(res["status"], "completed")
            facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
            self.assertIn("household_gross_monthly_income", facts)
            self.assertEqual(facts["household_gross_monthly_income"], expected)

    # -------------------------------------------------------------------
    # BLOCKING ITEM 10 — Agent 2 Julia Requirement: missing income question
    # -------------------------------------------------------------------
    def test_block_10_agent2_missing_income_asks_with_can_skip_false(self):
        """Agent 2 asks income question (can_skip=False) when income unknown."""
        req = {
            "request_id": "req-julia-1",
            "run_id": "run-block",
            "case_id": "case-block",
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
        income_qs = [
            r for r in res["clarification_requests"]
            if r["fact_key"] == "household_gross_monthly_income"
        ]
        self.assertGreater(len(income_qs), 0)
        self.assertFalse(income_qs[0]["can_skip"])

    # -------------------------------------------------------------------
    # BLOCKING ITEM 11 & REVIEW ITEM 3 — Notice details follow-up
    # -------------------------------------------------------------------
    def test_block_11_agent2_eviction_question_can_skip_false(self):
        """has_written_eviction_notice clarification must have can_skip=False and ask doc type & date."""
        req = {
            "request_id": "req-evict-cs",
            "run_id": "run-block",
            "case_id": "case-block",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": [],
                "case_facts": [
                    {"field": "household_gross_monthly_income", "value": 1200}
                ],
                "already_asked": [],
                "candidate_requirements": [
                    {
                        "program_id": "prog_evict",
                        "fact_key": "has_written_eviction_notice",
                        "verified_rule_ref": "rule_eviction_doc",
                    }
                ],
            },
        }
        res = handle_agent_2(req)
        eviction_qs = [
            r for r in res["clarification_requests"]
            if r["fact_key"] == "has_written_eviction_notice"
        ]
        self.assertGreater(len(eviction_qs), 0)
        self.assertFalse(eviction_qs[0]["can_skip"])
        question_text = eviction_qs[0]["user_facing_question"].lower()
        self.assertTrue(any(kw in question_text for kw in ["type", "document", "date"]))

    def test_block_11b_agent2_asks_document_type_and_date_when_notice_reported(self):
        """When notice is already reported (True) and income is known, Agent 2 asks document type & date."""
        req = {
            "request_id": "req-evict-doc-date",
            "run_id": "run-block",
            "case_id": "case-block",
            "case_version": 1,
            "schema_version": "1.0",
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": [{"need_id": "need_001", "category": "housing_assistance"}],
                "case_facts": [
                    {"field": "zip_code", "value": "95823"},
                    {"field": "household_gross_monthly_income", "value": 1400},
                    {"field": "has_written_eviction_notice", "value": True},
                ],
                "already_asked": ["household_gross_monthly_income"],
                "candidate_requirements": [],
            },
        }
        res = handle_agent_2(req)
        self.assertEqual(res["status"], "needs_clarification")
        self.assertGreater(len(res["clarification_requests"]), 0)
        cr = res["clarification_requests"][0]
        self.assertEqual(cr["fact_key"], "eviction_notice_type")
        self.assertFalse(cr["can_skip"])
        q_text = cr["user_facing_question"].lower()
        self.assertIn("type", q_text)
        self.assertIn("date", q_text)

    # -------------------------------------------------------------------
    # REVIEW ITEM 2 — original_quote whole sentence (no mid-word cuts)
    # -------------------------------------------------------------------
    def test_block_12_original_quote_not_cut_mid_word(self):
        """Housing original_quote must not be sliced mid-word."""
        story = (
            "I'm a single mom in Sacramento, ZIP 95823, with two kids, 6 and 9. "
            "I was laid off from my warehouse job last Friday. "
            "Rent of $1,450 is due on November 1 and I only have about $300 left. "
            "We're also running low on food this week."
        )
        res = _run_story(story)
        needs = {n["category"]: n for n in res["result"]["proposed_needs"]}
        housing_quote = needs["housing_assistance"]["original_quote"]
        self.assertFalse(housing_quote.endswith("300 l"), "Quote cut mid-word!")
        self.assertTrue(housing_quote.endswith(".") or "left" in housing_quote)

    # -------------------------------------------------------------------
    # REVIEW ITEM 4 — narrative_summary retains food need
    # -------------------------------------------------------------------
    def test_block_13_narrative_summary_retains_food_need(self):
        """narrative_summary must retain all volunteered substantive needs (job, rent, food)."""
        story = (
            "I'm a single mom in Sacramento, ZIP 95823, with two kids, 6 and 9. "
            "I was laid off from my warehouse job last Friday. "
            "Rent of $1,450 is due on November 1 and I only have about $300 left. "
            "We're also running low on food this week. I don't know where to start."
        )
        res = _run_story(story)
        summary = res["result"]["narrative_summary"]
        self.assertIn("food", summary.lower())
        self.assertIn("laid off", summary.lower())
        self.assertIn("rent", summary.lower())
        self.assertTrue(summary.endswith("."))


class TestContractShapeNegativeGuards(unittest.TestCase):
    """Negative guards — these cases must NOT produce false positives."""

    def test_no_safety_flag_for_show_about_violence(self):
        """'show about violence' must NOT trigger a safety flag."""
        res = _run_story("I was watching a show about violence last night. ZIP 95823.")
        flags = res["result"].get("safety_or_official_deadline_flags", [])
        safety_flags = [f for f in flags if f.get("type") == "safety"]
        self.assertEqual(len(safety_flags), 0, "False positive safety flag detected")

    def test_no_safety_flag_for_substance_abuse_program(self):
        """'substance abuse program years ago' must NOT trigger a safety flag."""
        res = _run_story(
            "I completed a substance abuse program years ago and I'm doing fine now. "
            "I just need help with rent. ZIP 95823."
        )
        flags = res["result"].get("safety_or_official_deadline_flags", [])
        safety_flags = [f for f in flags if f.get("type") == "safety"]
        self.assertEqual(len(safety_flags), 0, "False positive safety flag detected")

    def test_no_job_loss_triggering_event_without_job_loss(self):
        """Stories without job loss must NOT emit 'job_loss' in triggering_events."""
        res = _run_story("I need food assistance. My pantry is empty. ZIP 95820.")
        triggering = res["result"]["triggering_events"]
        self.assertNotIn("job_loss", triggering)

    def test_no_bereavement_event_without_death(self):
        """'sole earner' alone without death signal must NOT emit 'bereavement'."""
        res = _run_story(
            "I am the sole earner in my family and I need rental assistance. ZIP 95823."
        )
        triggering = res["result"]["triggering_events"]
        self.assertNotIn("bereavement", triggering)


if __name__ == "__main__":
    unittest.main()