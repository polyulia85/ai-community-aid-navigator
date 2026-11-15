"""Agent 8 receives the confirmed case facts (Supervisor, PROPOSED for contracts v1.2).

Run from the repo root:  python -m unittest tests.test_agent8_case_facts -v
"""
import unittest

from navigator.supervisor import run as R
from tests import fake_agents as F
from tests.fake_agents import FIXTURE_KB, FIXTURE_ZIPS

STORY = "I was laid off. Rent is due November 1. ZIP 95823."


class TestAgent8CaseFacts(unittest.TestCase):
    def _run(self, agent_10):
        seen = []

        def agent_8(req):
            seen.append(req)
            return F.agent_8_repair_card02(req)
        rep = R.Run(dict(F.ALL, agent_8=agent_8, agent_10=agent_10), FIXTURE_KB,
                    zips_path=FIXTURE_ZIPS).execute(STORY)
        return rep, seen

    def test_build_plan_request_carries_the_confirmed_facts(self):
        rep, seen = self._run(F.agent_10_pass)
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(len(seen), 1)
        facts = seen[0]["allowed_case_facts"]
        self.assertEqual({f["field"] for f in facts}, {"zip_code", "rent_due_date"})
        self.assertTrue(all(f["confirmation_status"] == "confirmed" and f["source"] == "user_confirmed"
                            for f in facts))

    def test_repair_round_request_carries_the_same_facts(self):
        rep, seen = self._run(F.agent_10_flags_card02_once)
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(len(seen), 2)
        self.assertIn("repair_flags", seen[1]["payload"])
        self.assertEqual(seen[1]["allowed_case_facts"], seen[0]["allowed_case_facts"])


if __name__ == "__main__":
    unittest.main()
