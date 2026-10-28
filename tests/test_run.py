"""Tests for the Supervisor runner with fake agents. Run from the repo root:  python -m unittest -v"""
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


if __name__ == "__main__":
    unittest.main()
