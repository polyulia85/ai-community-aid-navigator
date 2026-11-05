"""Tests for the Supervisor runner with fake agents. Run from the repo root:  python -m unittest -v"""
import datetime
import unittest
from unittest import mock

from navigator.supervisor import contract as C
from navigator.supervisor import run as R
from tests import fake_agents as F

STORY = "I was laid off. Rent is due November 1. ZIP 95823."


def run_with(**overrides):
    agents = dict(F.ALL, **overrides)
    return R.Run(agents, R.DEFAULT_KB).execute(STORY)


def codes(rep):
    return {i["code"] for s in rep["steps"] for i in s["issues"]}


def sup_codes(rep):
    return {i["code"] for i in rep["supervisor_issues"]}


class TestRunner(unittest.TestCase):
    def test_full_cycle_completes(self):
        rep = run_with()
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual([s["role_id"] for s in rep["steps"]],
                         ["agent_1", "agent_3", "agent_4", "agent_5", "agent_6", "agent_8", "agent_10"])
        self.assertEqual(len(rep["plan"]["action_cards"]), 2)
        self.assertTrue(rep["partially_mocked"])
        self.assertEqual(rep["case_version"], 2)   # bumped at user confirmation

    def test_broken_agent_1_stops_the_run(self):
        rep = run_with(agent_1=R.broken_agent_1)
        self.assertEqual(rep["outcome"], "stopped_at_agent_1")
        self.assertIn("IDENTITY_MISMATCH", codes(rep))
        self.assertEqual(len(rep["steps"]), 2)     # original call + 1 retry

    def test_crash_is_reported_not_raised(self):
        rep = run_with(agent_4=F.crashing_agent)
        self.assertEqual(rep["outcome"], "stopped_at_agent_4")
        self.assertIn("AGENT_EXCEPTION", codes(rep))

    def test_timeout(self):
        with mock.patch.object(C, "TIMEOUT_SECONDS", 0.5):
            rep = run_with(agent_3=F.slow_agent)
        self.assertEqual(rep["outcome"], "stopped_at_agent_3")
        self.assertIn("TIMEOUT", codes(rep))

    def test_missing_agent(self):
        agents = dict(F.ALL); del agents["agent_5"]
        rep = R.Run(agents, R.DEFAULT_KB).execute(STORY)
        self.assertEqual(rep["outcome"], "stopped_at_agent_5")
        self.assertIn("AGENT_NOT_CONNECTED", codes(rep))

    def test_privacy_violation_is_not_retried(self):
        rep = run_with(agent_3=F.agent_with_ssn)
        self.assertIn("PRIVACY_VIOLATION", codes(rep))
        self.assertEqual(sum(1 for s in rep["steps"] if s["role_id"] == "agent_3"), 1)

    def test_s0_masks_story_before_agent_1(self):
        seen = {}
        def spy(req):
            seen["text"] = req["payload"]["story_text"]; return F.agent_1(req)
        rep = R.Run(dict(F.ALL, agent_1=spy), R.DEFAULT_KB).execute(STORY + " SSN 123-45-6789")
        self.assertNotIn("123-45-6789", seen["text"])
        self.assertIn("PII_MASKED", {i["code"] for i in rep["supervisor_issues"]})

    def test_flagged_card_withheld_after_two_repair_rounds(self):
        rep = run_with(agent_10=F.agent_10_always_flags_card_02)
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(rep["plan"]["withheld_card_ids"], ["card_02"])
        self.assertEqual([c["card_id"] for c in rep["plan"]["action_cards"]], ["card_01"])  # the rest is released
        self.assertEqual(sum(1 for s in rep["steps"] if s["role_id"] == "agent_10"), 3)    # round 0, 1, 2

    # ---------------------------------------------------------------- Fix 1 tests (repair rounds)

    def test_repair_round_keeps_all_cards_when_only_one_flagged(self):
        """Test 1: Agent 10 flags card_02 once, passes on repair; Agent 8 repair returns only card_02
        with repaired_card_ids.  Final plan must have ALL original cards in original order,
        card_02 with the new text, nothing withheld."""
        rep = run_with(agent_8=F.agent_8_repair_card02,
                       agent_10=F.agent_10_flags_card02_once)
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(rep["plan"]["withheld_card_ids"], [])
        card_ids = [c["card_id"] for c in rep["plan"]["action_cards"]]
        self.assertEqual(card_ids, ["card_01", "card_02"])   # both cards, original order
        # card_02 must have the repaired text
        card02 = next(c for c in rep["plan"]["action_cards"] if c["card_id"] == "card_02")
        self.assertEqual(card02["action_title"], "Contact the program (repaired)")

    def test_repair_round_withholds_only_flagged_card_after_max_rounds(self):
        """Test 2: Agent 10 always flags card_02; Agent 8 repair returns only card_02.
        After 2 repair rounds card_02 is withheld and card_01 is released."""
        rep = run_with(agent_8=F.agent_8_repair_card02,
                       agent_10=F.agent_10_always_flags_card_02)
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(rep["plan"]["withheld_card_ids"], ["card_02"])
        card_ids = [c["card_id"] for c in rep["plan"]["action_cards"]]
        self.assertEqual(card_ids, ["card_01"])   # only card_01 released, card_02 withheld

    def test_repair_no_repaired_card_ids_field_is_full_replacement(self):
        """Test 3: Agent 8 repair returns a full plan without repaired_card_ids.
        Existing test test_flagged_card_withheld_after_two_repair_rounds covers this;
        confirm the merge helper treats absence of repaired_card_ids as a full replacement."""
        current = {"plan_version": "1", "action_cards": [{"card_id": "card_01"}, {"card_id": "card_02"}],
                   "potential_options": ["opt"], "coverage_gaps": ["gap"]}
        repair_result = {"result": {"plan_version": "2", "action_cards": [{"card_id": "card_03"}],
                                    "potential_options": [], "coverage_gaps": []}}
        new_plan, issues = R.merge_repaired_plan(current, repair_result)
        self.assertEqual(issues, [])
        self.assertEqual([c["card_id"] for c in new_plan["action_cards"]], ["card_03"])

    def test_repair_agent10_receives_full_merged_plan(self):
        """Test 4: In repair rounds, the request sent to Agent 10 contains all cards of the merged plan."""
        seen_cards = {}
        original_a10 = F.agent_10_flags_card02_once
        def spy_a10(req):
            round_ = req["payload"]["repair_round"]
            seen_cards[round_] = [c["card_id"] for c in req["payload"]["action_cards"]]
            return original_a10(req)
        rep = run_with(agent_8=F.agent_8_repair_card02, agent_10=spy_a10)
        self.assertEqual(rep["outcome"], "completed")
        # Round 0: both cards present
        self.assertIn("card_01", seen_cards[0])
        self.assertIn("card_02", seen_cards[0])
        # Round 1 (repair): Agent 10 still sees both cards (merged plan)
        self.assertIn("card_01", seen_cards[1])
        self.assertIn("card_02", seen_cards[1])

    def test_repair_unknown_card_id_not_added_issue_raised(self):
        """Test 5: Repair result with an unknown card_id → card not added, REPAIR_UNKNOWN_CARD warning."""
        rep = run_with(agent_8=F.agent_8_repair_unknown_card,
                       agent_10=F.agent_10_flags_card02_once)
        self.assertEqual(rep["outcome"], "completed")
        # card_99 must NOT appear in the plan
        card_ids = [c["card_id"] for c in rep["plan"]["action_cards"]]
        self.assertNotIn("card_99", card_ids)
        self.assertIn("REPAIR_UNKNOWN_CARD", sup_codes(rep))

    def test_repair_missing_listed_card_keeps_old_card_issue_raised(self):
        """Test 6: Repair result missing a card listed in repaired_card_ids → old card kept,
        REPAIR_CARD_MISSING warning in supervisor_issues."""
        rep = run_with(agent_8=F.agent_8_repair_missing_listed_card,
                       agent_10=F.agent_10_flags_card02_once)
        self.assertEqual(rep["outcome"], "completed")
        card_ids = [c["card_id"] for c in rep["plan"]["action_cards"]]
        self.assertIn("card_02", card_ids)   # old card_02 kept
        self.assertIn("REPAIR_CARD_MISSING", sup_codes(rep))

    def test_merge_helper_order_and_replacement(self):
        """Test 7: Unit-test merge_repaired_plan directly — order kept, only listed cards replaced."""
        current = {
            "plan_version": "1",
            "action_cards": [
                {"card_id": "card_01", "action_title": "Original 01"},
                {"card_id": "card_02", "action_title": "Original 02"},
                {"card_id": "card_03", "action_title": "Original 03"},
            ],
            "potential_options": ["opt_a"],
            "coverage_gaps": ["gap_x"],
        }
        repair_result = {
            "result": {
                "plan_version": "2",
                "action_cards": [{"card_id": "card_02", "action_title": "Repaired 02"}],
                "repaired_card_ids": ["card_02"],
            }
        }
        new_plan, issues = R.merge_repaired_plan(current, repair_result)
        self.assertEqual(issues, [])
        self.assertEqual(new_plan["plan_version"], "2")
        # Order preserved
        self.assertEqual([c["card_id"] for c in new_plan["action_cards"]],
                         ["card_01", "card_02", "card_03"])
        # Only card_02 replaced
        titles = {c["card_id"]: c["action_title"] for c in new_plan["action_cards"]}
        self.assertEqual(titles["card_01"], "Original 01")
        self.assertEqual(titles["card_02"], "Repaired 02")
        self.assertEqual(titles["card_03"], "Original 03")
        # potential_options and coverage_gaps taken from current plan
        self.assertEqual(new_plan["potential_options"], ["opt_a"])
        self.assertEqual(new_plan["coverage_gaps"], ["gap_x"])

    # ---------------------------------------------------------------- Fix 2 tests (ref_date)

    def test_ref_date_passed_to_run_appears_in_agent1_payload_and_report(self):
        """Test 8: ref_date passed to Run → Agent 1 payload has exactly that date; report has it."""
        fixed = datetime.date(2026, 12, 1)
        seen = {}
        def spy(req):
            seen["ref_date"] = req["payload"].get("ref_date"); return F.agent_1(req)
        rep = R.Run(dict(F.ALL, agent_1=spy), R.DEFAULT_KB, ref_date=fixed).execute(STORY)
        self.assertEqual(seen["ref_date"], "2026-12-01")
        self.assertEqual(rep["ref_date"], "2026-12-01")

    def test_no_ref_date_uses_todays_date(self):
        """Test 9: No ref_date given → Agent 1 payload contains today's ISO date."""
        today = datetime.date.today().isoformat()
        seen = {}
        def spy(req):
            seen["ref_date"] = req["payload"].get("ref_date"); return F.agent_1(req)
        R.Run(dict(F.ALL, agent_1=spy), R.DEFAULT_KB).execute(STORY)
        self.assertEqual(seen["ref_date"], today)

    def test_cli_invalid_ref_date_exits_code_2(self):
        """Test 10: CLI --ref-date 2026-13-40 → exit code 2 and a one-line error."""
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = R.main(["--agents", "tests/agents_fake.json", "--ref-date", "2026-13-40",
                         "--no-isolate", "--out", "test_invalid_date_report.json"])
        self.assertEqual(rc, 2)
        output = buf.getvalue().strip()
        self.assertTrue(output.count("\n") == 0, f"Expected one line, got: {output!r}")
        self.assertIn("2026-13-40", output)


if __name__ == "__main__":
    unittest.main()
