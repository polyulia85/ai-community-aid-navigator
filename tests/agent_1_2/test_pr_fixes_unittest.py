"""
Regression test suite for PR merge blockers:
1. Negated eviction notice phrases.
2. Typographic apostrophes in safety phrases.
"""
import unittest
from navigator.agents.agent_1_2.agent_1 import handle_agent_1


class TestPRMergeBlockers(unittest.TestCase):

    def test_negated_eviction_notice_phrases(self):
        """Negation must NOT flag has_written_eviction_notice = True and must NOT escalate housing to immediate."""
        cases = [
            "I have not received any eviction notice.",
            "My landlord did not give me any eviction notice yet.",
            "No eviction notice so far.",
        ]
        for story in cases:
            req = {
                "role_id": "agent_1",
                "task_type": "understand_story",
                "request_id": "req-neg",
                "run_id": "run-001",
                "case_id": "case-001",
                "case_version": 1,
                "correlation_id": "corr-neg",
                "payload": {"story_text": story},
            }
            res = handle_agent_1(req)
            self.assertEqual(res["status"], "completed")

            facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
            # Critical check: must be either False or omitted, never True
            self.assertNotEqual(facts.get("has_written_eviction_notice"), True)

            # Urgency check: eviction must not push housing to immediate
            needs = res["result"].get("proposed_needs", [])
            for n in needs:
                if n.get("category") == "housing_assistance":
                    self.assertNotEqual(n.get("urgency"), "immediate")

    def test_typographic_apostrophes_safety_detection(self):
        """Typographic curly apostrophes (’, ‘) must be normalized and trigger safety flags."""
        cases = [
            "I can’t go on like this anymore.",
            "I don’t want to live anymore.",
        ]
        for story in cases:
            req = {
                "role_id": "agent_1",
                "task_type": "understand_story",
                "request_id": "req-typo",
                "run_id": "run-001",
                "case_id": "case-001",
                "case_version": 1,
                "correlation_id": "corr-typo",
                "payload": {"story_text": story},
            }
            res = handle_agent_1(req)
            self.assertEqual(res["status"], "completed")
            flags = res["result"].get("safety_or_official_deadline_flags", [])
            self.assertTrue(len(flags) >= 1, f"Failed to detect safety flag for: {story}")
            self.assertEqual(flags[0]["type"], "safety")


if __name__ == "__main__":
    unittest.main()