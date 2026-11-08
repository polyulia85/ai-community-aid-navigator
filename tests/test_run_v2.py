"""Tests for Oct 24 Supervisor changes: Agent 2 need_updates, Agent 7 reviews, agents.json errors,
process isolation with a real stop on timeout. Run from the repo root:  python -m unittest -v"""
import datetime
import json
import multiprocessing
import os
import tempfile
import time
import unittest
from unittest import mock

from navigator.supervisor import checks
from navigator.supervisor import contract as C
from navigator.supervisor import run as R
from tests import fake_agents as F
from tests.fake_agents import FIXTURE_KB

STORY = "I was laid off. Rent is due November 1. ZIP 95823."
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run_with(**overrides):
    return R.Run(dict(F.ALL, **overrides), FIXTURE_KB).execute(STORY)


def codes(items):
    return {i["code"] for i in items}


class TestAgent2Updates(unittest.TestCase):
    def test_need_updates_applied(self):
        r = R.Run(dict(F.ALL, agent_2=F.agent_2), FIXTURE_KB)
        r.execute(STORY)
        urg = {n["need_id"]: n["urgency"] for n in r.state.needs}
        self.assertEqual(urg["need_002"], "immediate")

    def test_unknown_need_rejects_agent2_but_run_continues(self):
        r = R.Run(dict(F.ALL, agent_2=F.agent_2_unknown_need), FIXTURE_KB)
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
            self.assertEqual(R.main(["--agents", path, "--kb", FIXTURE_KB, "--out", os.devnull]), 2)
        self.assertTrue(p.call_args[0][0].startswith("Cannot load agents:"))


def ref(name):
    return R.AgentRef("tests.fake_agents", name, [ROOT], [])


class TestProcessIsolation(unittest.TestCase):
    def test_full_cycle_in_processes(self):
        agents = {role: ref(fn.__name__) for role, fn in F.ALL.items()}
        rep = R.Run(agents, FIXTURE_KB, isolate=True).execute(STORY)
        self.assertEqual(rep["outcome"], "completed")

    def test_timeout_really_stops_the_agent(self):
        agents = {role: ref(fn.__name__) for role, fn in F.ALL.items()}
        agents["agent_3"] = ref("very_slow_agent")          # sleeps 30 s
        t0 = time.monotonic()
        with mock.patch.object(C, "TIMEOUT_SECONDS", 1):
            rep = R.Run(agents, FIXTURE_KB, isolate=True).execute(STORY)
        self.assertLess(time.monotonic() - t0, 20)          # 2 tries x 1 s + process start, not 2 x 30 s
        self.assertEqual(rep["outcome"], "stopped_at_agent_3")
        self.assertIn("TIMEOUT", {i["code"] for s in rep["steps"] for i in s["issues"]})
        self.assertEqual(multiprocessing.active_children(), [])   # nothing left running

    def test_crash_in_process_is_reported(self):
        agents = {role: ref(fn.__name__) for role, fn in F.ALL.items()}
        agents["agent_4"] = ref("crashing_agent")
        rep = R.Run(agents, FIXTURE_KB, isolate=True).execute(STORY)
        self.assertEqual(rep["outcome"], "stopped_at_agent_4")
        msgs = [i["message"] for s in rep["steps"] for i in s["issues"] if i["code"] == "AGENT_EXCEPTION"]
        self.assertTrue(msgs and "ValueError" in msgs[0])


class TestFix5SchemaInvalidStops(unittest.TestCase):
    """FIX 5 run-level regression: per-role S1 failure stops the run."""

    # (a) Agent 1 returns a need without need_id
    def test_agent1_need_missing_need_id_stops_run(self):
        def bad_agent_1(req):
            r = F.agent_1(req)
            del r["result"]["proposed_needs"][0]["need_id"]
            return r
        rep = run_with(agent_1=bad_agent_1)
        self.assertEqual(rep["outcome"], "stopped_at_agent_1")
        a1_steps = [s for s in rep["steps"] if s["role_id"] == "agent_1"]
        all_issues = [i for s in a1_steps for i in s["issues"]]
        self.assertIn("SCHEMA_INVALID", {i["code"] for i in all_issues})
        refs = {i["related_ref"] for i in all_issues if i["code"] == "SCHEMA_INVALID"}
        self.assertIn("proposed_needs[0].need_id", refs)

    # (b) Agent 8 returns a card without card_id
    def test_agent8_card_missing_card_id_stops_run(self):
        def bad_agent_8(req):
            r = F.agent_8(req)
            del r["result"]["action_cards"][0]["card_id"]
            return r
        rep = run_with(agent_8=bad_agent_8)
        self.assertEqual(rep["outcome"], "stopped_at_agent_8")

    # (c) Agent 10 returns flags as an object
    def test_agent10_flags_not_list_stops_run(self):
        def bad_agent_10(req):
            r = F.agent_10_pass(req)
            r["result"]["flags"] = {"card_id": "card_01"}
            return r
        rep = run_with(agent_10=bad_agent_10)
        self.assertEqual(rep["outcome"], "stopped_at_agent_10")


class TestFix5InputError(unittest.TestCase):
    """FIX 5: SUPERVISOR_INPUT_ERROR safety net in Run._execute_body."""

    def test_builder_keyerror_gives_input_error_no_exception(self):
        """Patching B.agent4_request to raise KeyError('need_id') ->
        outcome stopped_at_agent_4, SUPERVISOR_INPUT_ERROR in supervisor_issues,
        message contains 'KeyError' and 'need_id', nothing from the story.
        """
        from navigator.supervisor import builders as B
        with mock.patch.object(B, "agent4_request",
                               side_effect=KeyError("need_id")):
            rep = run_with()
        self.assertEqual(rep["outcome"], "stopped_at_agent_4")
        codes_ = {i["code"] for i in rep["supervisor_issues"]}
        self.assertIn("SUPERVISOR_INPUT_ERROR", codes_)
        msg = next(i["message"] for i in rep["supervisor_issues"]
                   if i["code"] == "SUPERVISOR_INPUT_ERROR")
        self.assertIn("KeyError", msg)
        self.assertIn("need_id", msg)
        # story text must not appear in the message
        self.assertNotIn("laid off", msg)
        self.assertNotIn("ZIP", msg)


class TestFix5FakeAgentsPassS1(unittest.TestCase):
    """FIX 5 (d): every fake agent's result passes s1_result_fields for its role/task_type.

    Excluded (broken on purpose): crashing_agent, slow_agent, very_slow_agent,
    agent_with_ssn -- these are designed to fail or never return a valid result.
    """

    def _spy(self, fn, calls):
        """Wrap fn so every (request, result) it produces is appended to calls."""
        def wrapper(req):
            result = fn(req)
            calls.append((req, result))
            return result
        return wrapper

    def _run(self, agents):
        return R.Run(agents, FIXTURE_KB,
                     ref_date=datetime.date(2026, 11, 15)).execute(STORY)

    def test_all_listed_fake_agents_pass(self):
        targets = {
            "agent_1":                            F.agent_1,
            "agent_2":                            F.agent_2,
            "agent_2_unknown_need":               F.agent_2_unknown_need,
            "agent_3":                            F.agent_3,
            "agent_4":                            F.agent_4,
            "agent_5":                            F.agent_5,
            "agent_6":                            F.agent_6,
            "agent_7":                            F.agent_7,
            "agent_8":                            F.agent_8,
            "agent_10_pass":                      F.agent_10_pass,
            "agent_10_always_flags_card_02":      F.agent_10_always_flags_card_02,
            "agent_10_flags_card02_once":         F.agent_10_flags_card02_once,
            "agent_8_repair_card02":              F.agent_8_repair_card02,
            "agent_8_repair_unknown_card":        F.agent_8_repair_unknown_card,
            "agent_8_repair_missing_listed_card": F.agent_8_repair_missing_listed_card,
            "agent_8_repair_card02_no_ids":       F.agent_8_repair_card02_no_ids,
        }

        calls = {name: [] for name in targets}
        spies = {name: self._spy(fn, calls[name]) for name, fn in targets.items()}

        # Run 1: exercises agent_1, agent_2, agent_3, agent_4, agent_5, agent_6,
        # agent_7, agent_8_repair_card02, agent_10_flags_card02_once.
        # agent_8_repair_card02 handles both normal and repair calls.
        # agent_10_flags_card02_once flags on round 0, passes on round 1,
        # so it is called with repair_round 0 and repair_round 1.
        self._run({
            "agent_1": spies["agent_1"],
            "agent_2": spies["agent_2"],
            "agent_3": spies["agent_3"],
            "agent_4": spies["agent_4"],
            "agent_5": spies["agent_5"],
            "agent_6": spies["agent_6"],
            "agent_7": spies["agent_7"],
            "agent_8": spies["agent_8_repair_card02"],
            "agent_10": spies["agent_10_flags_card02_once"],
        })

        # Runs 2a, 2b, 2c: one run per repair fake, paired with
        # agent_10_always_flags_card_02 (always flags -> triggers 2 full repair rounds).
        # Also exercises agent_2_unknown_need and the three remaining repair fakes.
        for repair_fn in ("agent_8_repair_unknown_card",
                          "agent_8_repair_missing_listed_card",
                          "agent_8_repair_card02_no_ids"):
            self._run({
                "agent_1": spies["agent_1"],
                "agent_2": spies["agent_2_unknown_need"],
                "agent_3": spies["agent_3"],
                "agent_4": spies["agent_4"],
                "agent_5": spies["agent_5"],
                "agent_6": spies["agent_6"],
                "agent_8": spies[repair_fn],
                "agent_10": spies["agent_10_always_flags_card_02"],
            })

        # Run 3: plain happy path -- exercises agent_8 (no repair) and agent_10_pass.
        self._run({
            "agent_1": spies["agent_1"],
            "agent_3": spies["agent_3"],
            "agent_4": spies["agent_4"],
            "agent_5": spies["agent_5"],
            "agent_6": spies["agent_6"],
            "agent_8": spies["agent_8"],
            "agent_10": spies["agent_10_pass"],
        })

        # Every listed function must have been called at least once.
        for name in targets:
            self.assertGreater(len(calls[name]), 0,
                               f"{name} was never called -- not covered")

        # The four repair fakes must have been called with repair_flags in payload
        # at least once (proving the repair branch ran, not just the normal branch).
        for name in ("agent_8_repair_card02", "agent_8_repair_unknown_card",
                     "agent_8_repair_missing_listed_card", "agent_8_repair_card02_no_ids"):
            repair_calls = [req for req, _ in calls[name]
                            if "repair_flags" in req.get("payload", {})]
            self.assertGreater(len(repair_calls), 0,
                               f"{name} was never called with repair_flags")

        # agent_10_flags_card02_once must have been called with repair_round 0 and 1.
        rounds_seen = {req["payload"]["repair_round"]
                       for req, _ in calls["agent_10_flags_card02_once"]}
        self.assertIn(0, rounds_seen,
                      "agent_10_flags_card02_once never called with repair_round 0")
        self.assertIn(1, rounds_seen,
                      "agent_10_flags_card02_once never called with repair_round 1")

        # Every captured result must pass s1_result_fields.
        for name in targets:
            for req, result in calls[name]:
                issues = checks.s1_result_fields(req, result)
                schema_invalid = [i for i in issues if i["code"] == "SCHEMA_INVALID"]
                self.assertEqual(schema_invalid, [],
                                 f"{name} produced SCHEMA_INVALID: {schema_invalid}")


if __name__ == "__main__":
    unittest.main()
