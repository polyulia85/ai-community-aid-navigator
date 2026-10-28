"""Tests for Oct 24 Supervisor changes: Agent 2 need_updates, Agent 7 reviews, agents.json errors,
process isolation with a real stop on timeout. Run from the repo root:  python -m unittest -v"""
import json
import multiprocessing
import os
import tempfile
import time
import unittest
from unittest import mock

from navigator.supervisor import contract as C
from navigator.supervisor import run as R
from tests import fake_agents as F

STORY = "I was laid off. Rent is due November 1. ZIP 95823."
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run_with(**overrides):
    return R.Run(dict(F.ALL, **overrides), R.DEFAULT_KB).execute(STORY)


def codes(items):
    return {i["code"] for i in items}


class TestAgent2Updates(unittest.TestCase):
    def test_need_updates_applied(self):
        r = R.Run(dict(F.ALL, agent_2=F.agent_2), R.DEFAULT_KB)
        r.execute(STORY)
        urg = {n["need_id"]: n["urgency"] for n in r.state.needs}
        self.assertEqual(urg["need_002"], "immediate")

    def test_unknown_need_rejects_agent2_but_run_continues(self):
        r = R.Run(dict(F.ALL, agent_2=F.agent_2_unknown_need), R.DEFAULT_KB)
        rep = r.execute(STORY)
        self.assertEqual(rep["outcome"], "completed")                      # Agent 2 is a soft step
        a2 = [s for s in rep["steps"] if s["role_id"] == "agent_2"]
        self.assertFalse(any(s["accepted"] for s in a2))
        self.assertIn("UNKNOWN_REFERENCE", {i["code"] for s in a2 for i in s["issues"]})

    def test_apply_need_updates_guards(self):
        from navigator.supervisor import builders as B
        st = B.CaseState("c", "r", "x")
        st.needs = [{"need_id": "need_001", "urgency": "high"}]
        out = B.apply_need_updates(st, {"result": {"need_updates": [
            {"need_id": "need_001", "urgency": "asap"}, {"need_id": "need_404", "urgency": "high"}]}})
        self.assertEqual(st.needs[0]["urgency"], "high")
        self.assertEqual(len(out), 2)


class TestAgent7(unittest.TestCase):
    def test_agent7_reviews_four_stages_and_findings_reach_agent10(self):
        seen = {}
        def spy10(req):
            seen["open"] = req["payload"]["open_agent7_findings"]
            return F.agent_10_pass(req)
        rep = run_with(agent_7=F.agent_7, agent_10=spy10)
        self.assertEqual(rep["outcome"], "completed")
        stages = [s for s in rep["steps"] if s["role_id"] == "agent_7"]
        self.assertEqual(len(stages), 4)
        self.assertEqual([f["finding_id"] for f in seen["open"]],
                         ["F7-retrieval", "F7-matching", "F7-verification", "F7-planning"])

    def test_agent7_failure_never_blocks(self):
        rep = run_with(agent_7=F.crashing_agent)
        self.assertEqual(rep["outcome"], "completed")
        self.assertIn("AGENT_7_REVIEW_MISSING", codes(rep["supervisor_issues"]))

    def test_agent7_not_connected_is_reported_once(self):
        rep = run_with()
        self.assertEqual(sum(1 for i in rep["supervisor_issues"] if i["code"] == "AGENT_7_NOT_CONNECTED"), 1)


class TestConfigErrors(unittest.TestCase):
    def write(self, text):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir=HERE, encoding="utf-8")
        f.write(text); f.close()
        self.addCleanup(os.remove, f.name)
        return f.name

    def assertConfigError(self, text, fragment):
        with self.assertRaises(R.AgentConfigError) as cm:
            R.load_agents(self.write(text))
        self.assertIn(fragment, str(cm.exception))

    def test_missing_file(self):
        with self.assertRaises(R.AgentConfigError):
            R.load_agents(os.path.join(HERE, "no_such_file.json"))

    def test_bad_json(self):
        self.assertConfigError('{"agents": {', "not valid JSON")

    def test_missing_folder(self):
        self.assertConfigError('{"paths": ["../no_such_folder"], "agents": {}}', "does not exist")

    def test_unknown_role(self):
        self.assertConfigError('{"paths": [".."], "agents": {"agent_11": "tests.fake_agents:agent_1"}}', "Unknown role")

    def test_bad_target(self):
        self.assertConfigError('{"paths": [".."], "agents": {"agent_1": "tests.fake_agents.agent_1"}}', "module:function")

    def test_missing_module(self):
        self.assertConfigError('{"paths": [".."], "agents": {"agent_1": "tests.no_module:agent_1"}}', "not found")

    def test_missing_function_with_hint(self):
        self.assertConfigError('{"paths": [".."], "agents": {"agent_3": "tests.fake_agents:agent_33"}}',
                               "did you mean 'agent_3'")

    def test_main_prints_one_line_and_returns_2(self):
        path = self.write('{"paths": [".."], "agents": {"agent_3": "tests.fake_agents:agent_33"}}')
        with mock.patch("builtins.print") as p:
            self.assertEqual(R.main(["--agents", path, "--out", os.devnull]), 2)
        self.assertTrue(p.call_args[0][0].startswith("Cannot load agents:"))


def ref(name):
    return R.AgentRef("tests.fake_agents", name, [ROOT], [])


class TestProcessIsolation(unittest.TestCase):
    def test_full_cycle_in_processes(self):
        agents = {role: ref(fn.__name__) for role, fn in F.ALL.items()}
        rep = R.Run(agents, R.DEFAULT_KB, isolate=True).execute(STORY)
        self.assertEqual(rep["outcome"], "completed")

    def test_timeout_really_stops_the_agent(self):
        agents = {role: ref(fn.__name__) for role, fn in F.ALL.items()}
        agents["agent_3"] = ref("very_slow_agent")          # sleeps 30 s
        t0 = time.monotonic()
        with mock.patch.object(C, "TIMEOUT_SECONDS", 1):
            rep = R.Run(agents, R.DEFAULT_KB, isolate=True).execute(STORY)
        self.assertLess(time.monotonic() - t0, 20)          # 2 tries x 1 s + process start, not 2 x 30 s
        self.assertEqual(rep["outcome"], "stopped_at_agent_3")
        self.assertIn("TIMEOUT", {i["code"] for s in rep["steps"] for i in s["issues"]})
        self.assertEqual(multiprocessing.active_children(), [])   # nothing left running

    def test_crash_in_process_is_reported(self):
        agents = {role: ref(fn.__name__) for role, fn in F.ALL.items()}
        agents["agent_4"] = ref("crashing_agent")
        rep = R.Run(agents, R.DEFAULT_KB, isolate=True).execute(STORY)
        self.assertEqual(rep["outcome"], "stopped_at_agent_4")
        msgs = [i["message"] for s in rep["steps"] for i in s["issues"] if i["code"] == "AGENT_EXCEPTION"]
        self.assertTrue(msgs and "ValueError" in msgs[0])


if __name__ == "__main__":
    unittest.main()
