"""Tests for the Supervisor runner with fake agents. Run from the repo root:  python -m unittest -v"""
import datetime
import unittest
from unittest import mock

from navigator.supervisor import contract as C
from navigator.supervisor import run as R
from tests import fake_agents as F
from tests.fake_agents import FIXTURE_KB

STORY = "I was laid off. Rent is due November 1. ZIP 95823."


def run_with(**overrides):
    agents = dict(F.ALL, **overrides)
    return R.Run(agents, FIXTURE_KB).execute(STORY)


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
        rep = R.Run(agents, FIXTURE_KB).execute(STORY)
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
        rep = R.Run(dict(F.ALL, agent_1=spy), FIXTURE_KB).execute(STORY + " SSN 123-45-6789")
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

    def test_repair_without_repaired_card_ids_keeps_current_plan(self):
        """FIX 4: merge helper — no repaired_card_ids → current plan kept, REPAIR_IDS_INVALID raised."""
        current = {"plan_version": "1", "action_cards": [{"card_id": "card_01"}, {"card_id": "card_02"}],
                   "potential_options": ["opt"], "coverage_gaps": ["gap"]}
        repair_result = {"result": {"plan_version": "2", "action_cards": [{"card_id": "card_03"}],
                                    "potential_options": [], "coverage_gaps": []}}
        new_plan, issues = R.merge_repaired_plan(current, repair_result)
        self.assertEqual([c["card_id"] for c in new_plan["action_cards"]], ["card_01", "card_02"])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], "REPAIR_IDS_INVALID")
        self.assertEqual(issues[0]["severity"], "warning")

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

    def test_merge_missing_plan_version_keeps_current(self):
        """FIX 3.1: repair result with no plan_version → merged plan keeps current plan_version."""
        current = {"plan_version": "v1", "action_cards": [{"card_id": "card_01"}],
                   "potential_options": [], "coverage_gaps": []}
        repair = {"result": {"action_cards": [{"card_id": "card_01"}],
                             "repaired_card_ids": ["card_01"]}}   # no plan_version key
        new_plan, issues = R.merge_repaired_plan(current, repair)
        self.assertEqual(new_plan["plan_version"], "v1")
        self.assertEqual(issues, [])

    def test_merge_repaired_ids_bare_string_keeps_plan(self):
        """FIX 3.2: repaired_card_ids is a bare string → REPAIR_IDS_INVALID, plan unchanged."""
        current = {"plan_version": "v1", "action_cards": [{"card_id": "card_01"}, {"card_id": "card_02"}],
                   "potential_options": [], "coverage_gaps": []}
        repair = {"result": {"plan_version": "v2", "action_cards": [], "repaired_card_ids": "card_02"}}
        new_plan, issues = R.merge_repaired_plan(current, repair)
        self.assertEqual([c["card_id"] for c in new_plan["action_cards"]], ["card_01", "card_02"])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], "REPAIR_IDS_INVALID")
        self.assertEqual(issues[0]["severity"], "warning")

    def test_merge_repaired_ids_number_keeps_plan(self):
        """FIX 3.2: repaired_card_ids is a number → REPAIR_IDS_INVALID, plan unchanged."""
        current = {"plan_version": "v1", "action_cards": [{"card_id": "card_01"}, {"card_id": "card_02"}],
                   "potential_options": [], "coverage_gaps": []}
        repair = {"result": {"plan_version": "v2", "action_cards": [], "repaired_card_ids": 5}}
        new_plan, issues = R.merge_repaired_plan(current, repair)
        self.assertEqual([c["card_id"] for c in new_plan["action_cards"]], ["card_01", "card_02"])
        self.assertEqual(issues[0]["code"], "REPAIR_IDS_INVALID")

    def test_merge_repaired_ids_list_with_nonstring_keeps_plan(self):
        """FIX 3.2: repaired_card_ids contains a non-string → REPAIR_IDS_INVALID, plan unchanged."""
        current = {"plan_version": "v1", "action_cards": [{"card_id": "card_01"}, {"card_id": "card_02"}],
                   "potential_options": [], "coverage_gaps": []}
        repair = {"result": {"plan_version": "v2", "action_cards": [], "repaired_card_ids": ["card_02", 7]}}
        new_plan, issues = R.merge_repaired_plan(current, repair)
        self.assertEqual([c["card_id"] for c in new_plan["action_cards"]], ["card_01", "card_02"])
        self.assertEqual(issues[0]["code"], "REPAIR_IDS_INVALID")

    def test_repair_no_repaired_card_ids_full_cycle(self):
        """FIX 4 full-cycle: Agent 10 flags card_02 on round 0 only; repair Agent 8 returns
        only card_02 with no repaired_card_ids → merge keeps current plan; final plan has
        card_01 and card_02, REPAIR_IDS_INVALID in supervisor_issues."""
        rep = run_with(agent_8=F.agent_8_repair_card02_no_ids,
                       agent_10=F.agent_10_flags_card02_once)
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(rep["plan"]["withheld_card_ids"], [])
        card_ids = [c["card_id"] for c in rep["plan"]["action_cards"]]
        self.assertEqual(card_ids, ["card_01", "card_02"])
        self.assertIn("REPAIR_IDS_INVALID",
                      {i["code"] for i in rep["supervisor_issues"]})
        card02 = next(c for c in rep["plan"]["action_cards"] if c["card_id"] == "card_02")
        self.assertNotEqual(card02["action_title"], "Contact the program (no-ids repair)")

    # ---------------------------------------------------------------- Fix 2 tests (ref_date)

    def test_ref_date_passed_to_run_appears_in_agent1_payload_and_report(self):
        """Test 8: ref_date passed to Run → Agent 1 payload has exactly that date; report has it."""
        fixed = datetime.date(2026, 12, 1)
        seen = {}
        def spy(req):
            seen["ref_date"] = req["payload"].get("ref_date"); return F.agent_1(req)
        rep = R.Run(dict(F.ALL, agent_1=spy), FIXTURE_KB, ref_date=fixed).execute(STORY)
        self.assertEqual(seen["ref_date"], "2026-12-01")
        self.assertEqual(rep["ref_date"], "2026-12-01")

    def test_no_ref_date_uses_todays_date(self):
        """Test 9: No ref_date given → _today() is used; patching it gives a deterministic result."""
        frozen = datetime.date(2026, 11, 15)
        seen = {}
        def spy(req):
            seen["ref_date"] = req["payload"].get("ref_date"); return F.agent_1(req)
        with mock.patch("navigator.supervisor.run._today", return_value=frozen):
            rep = R.Run(dict(F.ALL, agent_1=spy), FIXTURE_KB).execute(STORY)
        self.assertEqual(seen["ref_date"], "2026-11-15")
        self.assertEqual(rep["ref_date"], "2026-11-15")

    def test_agent1_request_no_ref_date_raises(self):
        """Test 11: agent1_request called with ref_date=None raises ValueError."""
        from navigator.supervisor import builders as B
        with self.assertRaises(ValueError):
            B.agent1_request(B.CaseState("c", "r", "x"), "some story", ref_date=None)

    def test_cli_invalid_ref_date_exits_code_2(self):
        """Test 10: CLI --ref-date 2026-13-40 → exit code 2 and a one-line error."""
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = R.main(["--agents", "tests/agents_fake.json",
                         "--kb", FIXTURE_KB,
                         "--ref-date", "2026-13-40",
                         "--no-isolate", "--out", "test_invalid_date_report.json"])
        self.assertEqual(rc, 2)
        output = buf.getvalue().strip()
        self.assertTrue(output.count("\n") == 0, f"Expected one line, got: {output!r}")
        self.assertIn("2026-13-40", output)

    # ---------------------------------------------------------------- Fix 16 tests (ref_date in agents 6, 8, 10)

    def test_ref_date_in_agents_6_8_10_payloads(self):
        """In a full fake run with ref_date 2026-11-15:
        Agents 1, 6, 8 (x2: normal + repair), and 10 (x2: rounds 0 and 1)
        all carry ref_date='2026-11-15' in their payloads.
        agent_8_repair_card02 handles both the normal and repair Agent 8 calls.
        agent_10_flags_card02_once flags on round 0, passes on round 1.
        """
        fixed = datetime.date(2026, 11, 15)
        seen = {}
        def spy(role, fn):
            def wrapper(req):
                seen.setdefault(role, []).append(req["payload"])
                return fn(req)
            return wrapper
        agents = dict(F.ALL,
                      agent_1=spy("agent_1", F.agent_1),
                      agent_6=spy("agent_6", F.agent_6),
                      agent_8=spy("agent_8", F.agent_8_repair_card02),
                      agent_10=spy("agent_10", F.agent_10_flags_card02_once))
        rep = R.Run(agents, FIXTURE_KB, ref_date=fixed).execute(STORY)
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(rep["ref_date"], "2026-11-15")
        # agent_1: exactly one call, ref_date correct
        self.assertEqual(len(seen["agent_1"]), 1)
        self.assertEqual(seen["agent_1"][0]["ref_date"], "2026-11-15")
        # agent_6: exactly one call
        self.assertEqual(len(seen["agent_6"]), 1)
        self.assertEqual(seen["agent_6"][0]["ref_date"], "2026-11-15")
        # agent_8: exactly 2 calls (normal + 1 repair), both with correct ref_date
        self.assertEqual(len(seen["agent_8"]), 2)
        for p in seen["agent_8"]:
            self.assertEqual(p["ref_date"], "2026-11-15")
        # exactly one of the two Agent 8 calls has repair_flags
        repair_calls = [p for p in seen["agent_8"] if "repair_flags" in p]
        self.assertEqual(len(repair_calls), 1)
        # agent_10: exactly 2 calls (repair_round 0 and 1), both with correct ref_date
        self.assertEqual(len(seen["agent_10"]), 2)
        for p in seen["agent_10"]:
            self.assertEqual(p["ref_date"], "2026-11-15")
        rounds = [p["repair_round"] for p in seen["agent_10"]]
        self.assertIn(0, rounds)
        self.assertIn(1, rounds)

    def test_ref_date_none_raises_in_builders(self):
        """agent6_request, agent8_request and agent10_request each raise ValueError
        when ref_date is None (keyword-only argument)."""
        from navigator.supervisor import builders as B
        st = B.CaseState("c", "r", "x")
        dummy_pkg = {"needs": [], "matches": [], "checked_claims": [],
                     "program_availability": [], "evidence_records": [],
                     "agent7_findings": []}
        dummy_r6 = {"result": {"proposed_actions": []}}
        dummy_req = {"request_id": "req-0001"}
        dummy_plan = {"plan_version": "1", "action_cards": [],
                      "potential_options": [], "coverage_gaps": []}
        with self.assertRaises(ValueError):
            B.agent6_request(st, dummy_pkg, [], ref_date=None)
        with self.assertRaises(ValueError):
            B.agent8_request(st, dummy_pkg, dummy_req, dummy_r6, ref_date=None)
        with self.assertRaises(ValueError):
            B.agent10_request(st, dummy_pkg, dummy_req, dummy_plan, ref_date=None)


class TestFix6FinalValidation(unittest.TestCase):
    """FIX 6: final_validation in report; withheld_cards in plan."""

    # Passing run: PASS verdict, 0 repair rounds, empty flags and withheld_cards
    def test_final_validation_pass(self):
        rep = run_with()
        fv = rep["final_validation"]
        self.assertIsNotNone(fv)
        self.assertEqual(fv["verdict"], "PASS")
        self.assertEqual(fv["repair_rounds_used"], 0)
        self.assertEqual(fv["flags"], [])
        self.assertEqual(rep["plan"]["withheld_cards"], [])

    # Withheld run: FLAG verdict, 2 repair rounds, correct flags shape, withheld_cards
    def test_final_validation_withheld_card(self):
        rep = run_with(agent_10=F.agent_10_always_flags_card_02)
        fv = rep["final_validation"]
        self.assertIsNotNone(fv)
        self.assertEqual(fv["verdict"], "FLAG")
        self.assertEqual(fv["repair_rounds_used"], 2)
        # Each flag has exactly the six required keys, no user data
        expected_keys = {"card_id", "rule_id", "severity",
                         "blocks_release", "reason", "required_correction"}
        for f in fv["flags"]:
            self.assertEqual(set(f.keys()), expected_keys)
        self.assertIn("V1", [f["rule_id"] for f in fv["flags"]])
        # plan.withheld_cards carries rule_ids and reasons
        self.assertEqual(rep["plan"]["withheld_cards"],
                         [{"card_id": "card_02", "rule_ids": ["V1"],
                           "reasons": ["guarantee"]}])
        self.assertEqual(rep["plan"]["withheld_card_ids"], ["card_02"])

    # Agent 10 flagged card_02, then repair Agent 8 crashes:
    # outcome stopped_at_agent_8_repair but final_validation is still present
    def test_final_validation_present_after_stopped_at_repair(self):
        """Agent 10 ran and set _last_r10; repair Agent 8 then crashes.
        final_validation must still be in the report (verdict FLAG)."""
        def agent_8_crashes_on_repair(req):
            if "repair_flags" in req.get("payload", {}):
                raise ValueError("repair crashed")
            return F.agent_8(req)
        rep = run_with(agent_8=agent_8_crashes_on_repair,
                       agent_10=F.agent_10_flags_card02_once)
        self.assertEqual(rep["outcome"], "stopped_at_agent_8_repair")
        fv = rep["final_validation"]
        self.assertIsNotNone(fv)
        self.assertEqual(fv["verdict"], "FLAG")

    # Stop before Agent 10: final_validation is None
    def test_final_validation_none_when_agent10_did_not_run(self):
        rep = run_with(agent_3=F.crashing_agent)
        self.assertEqual(rep["outcome"], "stopped_at_agent_3")
        self.assertIsNone(rep["final_validation"])


if __name__ == "__main__":
    unittest.main()
