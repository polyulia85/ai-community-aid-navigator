"""Tests for Supervisor v0.2.6 (Session E): S1 types of single values, S5 in clarification
requests, plan-level Agent 10 flags, the one-shot run's missing-need report and corrections,
and command-line input errors without a traceback.

Run from the repo root:  python -m unittest tests.test_supervisor_v026 -v
"""
import contextlib
import copy
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

from navigator.supervisor import builders as B
from navigator.supervisor import checks
from navigator.supervisor import contract as C
from navigator.supervisor import dialog as D
from navigator.supervisor import http_api as H
from navigator.supervisor import run as R
from tests import fake_agents as F
from tests.fake_agents import FIXTURE_KB, FIXTURE_ZIPS

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE_AGENTS_JSON = os.path.join(HERE, "agents_fake.json")
FAKE_DIALOG_AGENTS_JSON = os.path.join(HERE, "agents_fake_dialog.json")
STORY = "I was laid off. Rent is due November 1. ZIP 95823."
SECRET = 987654321          # a value that must never appear in an issue message


def codes(issues):
    return {i["code"] for i in issues}


def _state():
    return B.CaseState("case-t", "run-t", "corr-t")


def _check(role, task, result_body, envelope=None, known=None):
    """Build a request and a fake agent result, change it, and run all checks."""
    req = B.make_request(_state(), role, task, {})
    res = F._env(req, result_body)
    for k, v in (envelope or {}).items():
        res[k] = v
    return checks.check_result(req, res, req["case_version"], known=known)


def _flag(card_id, blocks=True, rule="V1"):
    return {"flag_id": "FLAG-001", "card_id": card_id, "rule_id": rule,
            "severity": "critical" if blocks else "warning", "claim_text": "", "reason": "r",
            "evidence_refs": [], "required_correction": "fix", "blocks_release": blocks}


def _agent10_body(flags, passed=("card_01",)):
    return {"verdict": "FLAG" if flags else "PASS", "repair_round": 0,
            "flags": flags, "passed_card_ids": list(passed)}


def _clar(**changes):
    cr = {"fact_key": "zip_code", "question_intent": "zip", "user_facing_question": "What is your ZIP?",
          "reason": "local programs", "applicable_program_ids": [], "verified_rule_ref": None,
          "necessity_level": "required_for_decision", "can_skip": True}
    cr.update(changes)
    return cr


def _agent2_body():
    return {"need_updates": [], "optional_food_check": False}


# ---------------------------------------------------------------- S1: types of single values
class TestS1Types(unittest.TestCase):
    def setUp(self):
        req = B.make_request(_state(), "agent_1", "understand_story", {})
        self.agent1_body = copy.deepcopy(F.agent_1(req)["result"])

    def test_fake_agents_still_pass(self):
        ok, issues = _check("agent_1", "understand_story", self.agent1_body)
        self.assertTrue(ok, issues)

    def test_case_version_true_is_rejected(self):
        ok, issues = _check("agent_1", "understand_story", self.agent1_body, {"case_version": True})
        self.assertFalse(ok)
        self.assertIn("Field case_version must be int", [i["message"] for i in issues])

    def test_enum_value_that_is_not_text_is_rejected(self):
        # S4 checks only text values; a number in category would pass S4 unseen
        self.agent1_body["proposed_needs"][0]["category"] = SECRET
        ok, issues = _check("agent_1", "understand_story", self.agent1_body)
        self.assertFalse(ok)
        self.assertIn("result.proposed_needs[0].category must be str",
                      [i["message"] for i in issues])
        self.assertFalse(any(str(SECRET) in i["message"] for i in issues))   # no values in messages

    def test_yes_no_field_must_be_true_or_false(self):
        self.agent1_body["proposed_needs"][1]["user_reported"] = "yes"
        ok, issues = _check("agent_1", "understand_story", self.agent1_body)
        self.assertFalse(ok)
        self.assertIn("result.proposed_needs[1].user_reported must be bool",
                      [i["message"] for i in issues])

    def test_or_null_field_accepts_null_and_rejects_a_list(self):
        self.agent1_body["proposed_needs"][0]["urgency_reason"] = None
        self.assertTrue(_check("agent_1", "understand_story", self.agent1_body)[0])
        self.agent1_body["proposed_needs"][0]["urgency_reason"] = ["x"]
        ok, issues = _check("agent_1", "understand_story", self.agent1_body)
        self.assertFalse(ok)
        self.assertIn("result.proposed_needs[0].urgency_reason must be str or null",
                      [i["message"] for i in issues])

    def test_list_of_texts_with_an_object_is_rejected(self):
        self.agent1_body["triggering_events"] = ["job_loss", {"x": 1}]
        ok, issues = _check("agent_1", "understand_story", self.agent1_body)
        self.assertFalse(ok)
        self.assertIn("result.triggering_events[1] must be str", [i["message"] for i in issues])

    def test_agent10_blocks_release_as_text_is_rejected(self):
        flag = _flag("card_01"); flag["blocks_release"] = "false"   # truthy text: would withhold
        ok, issues = _check("agent_10", "validate_plan", _agent10_body([flag], passed=()))
        self.assertFalse(ok)
        self.assertIn("result.flags[0].blocks_release must be bool", [i["message"] for i in issues])

    def test_agent10_repair_round_true_is_rejected(self):
        body = _agent10_body([]); body["repair_round"] = True
        ok, issues = _check("agent_10", "validate_plan", body)
        self.assertFalse(ok)
        self.assertIn("result.repair_round must be int", [i["message"] for i in issues])

    def test_agent10_plan_level_flag_card_id_null_is_accepted(self):
        ok, issues = _check("agent_10", "validate_plan", _agent10_body([_flag(None, blocks=False, rule="V11")]))
        self.assertTrue(ok, issues)

    def test_agent8_card_id_must_be_text(self):
        req6 = B.make_request(_state(), "agent_6", "prioritize_actions", {})
        actions = F.agent_6(dict(req6, payload={"matches": [
            {"program_id": "p1", "need_ids": ["need_001"]}]}))["result"]["proposed_actions"]
        req8 = B.make_request(_state(), "agent_8", "build_plan", {"proposed_actions": actions})
        body = F.agent_8(req8)["result"]
        body["action_cards"][0]["card_id"] = ["card_01"]
        ok, issues = _check("agent_8", "build_plan", body)
        self.assertFalse(ok)
        self.assertIn("result.action_cards[0].card_id must be str", [i["message"] for i in issues])

    def test_clarification_request_not_an_object(self):
        ok, issues = _check("agent_2", "clarify_case", _agent2_body(), {"clarification_requests": ["zip?"]})
        self.assertFalse(ok)
        self.assertIn("clarification_requests[0] must be an object", [i["message"] for i in issues])

    def test_clarification_request_can_skip_as_text(self):
        ok, issues = _check("agent_2", "clarify_case", _agent2_body(),
                            {"clarification_requests": [_clar(can_skip="no")]})
        self.assertFalse(ok)
        self.assertIn("clarification_requests[0].can_skip must be bool", [i["message"] for i in issues])

    def test_valid_clarification_request_passes(self):
        ok, issues = _check("agent_2", "clarify_case", _agent2_body(), {"clarification_requests": [_clar()]})
        self.assertTrue(ok, issues)


class TestResultTypesTable(unittest.TestCase):
    """RESULT_TYPES uses only roles, tasks and result keys that RESULT_REQUIRED knows."""

    def test_every_path_starts_at_a_known_result_key(self):
        for role, tasks in C.RESULT_TYPES.items():
            for task, types in tasks.items():
                entry = C.RESULT_REQUIRED[role][task]
                keys = set(entry["result"]) | set(entry.get("optional_lists", []))
                for path, spec in types.items():
                    first = path.split(".")[0].removesuffix("[]")
                    self.assertIn(first, keys, f"{role}/{task}: {path}")
                    self.assertTrue(set(spec.split("|")) <= {"str", "int", "bool", "list", "null"}, spec)

    def test_every_type_path_of_a_list_item_names_a_required_item_key(self):
        for role, tasks in C.RESULT_TYPES.items():
            for task, types in tasks.items():
                entry = C.RESULT_REQUIRED[role][task]
                for path in types:
                    parts = path.split(".")
                    if len(parts) == 2 and parts[0].endswith("[]") and parts[0][:-2] in entry:
                        # the two truly optional keys (contract 3.1, 4.6)
                        if parts[1] not in ("subcategory", "suggested_priority"):
                            self.assertIn(parts[1].removesuffix("[]"), entry[parts[0][:-2]], f"{role}/{task}: {path}")

    def test_clarification_types_cover_contract_3_3(self):
        fields = {p.split(".")[1] for p in C.CLARIFICATION_TYPES}
        self.assertEqual(fields, {"fact_key", "question_intent", "user_facing_question", "reason",
                                  "applicable_program_ids", "verified_rule_ref", "necessity_level",
                                  "can_skip"})


# ---------------------------------------------------------------- S5
class TestS5Clarification(unittest.TestCase):
    KNOWN = {"program_id": {"prog_a"}, "evidence_id": {"ev_a"}}

    def test_unknown_program_in_clarification_is_rejected(self):
        ok, issues = _check("agent_2", "clarify_case", _agent2_body(),
                            {"clarification_requests": [_clar(applicable_program_ids=["prog_x"])]},
                            known=self.KNOWN)
        self.assertFalse(ok)
        self.assertIn("clarification_requests[0].applicable_program_ids refers to unknown program_id 'prog_x'",
                      [i["message"] for i in issues])

    def test_unknown_rule_evidence_is_rejected(self):
        ok, issues = _check("agent_2", "clarify_case", _agent2_body(),
                            {"clarification_requests": [_clar(verified_rule_ref="ev_x")]}, known=self.KNOWN)
        self.assertFalse(ok)
        self.assertIn("UNKNOWN_REFERENCE", codes(issues))

    def test_known_references_pass(self):
        ok, issues = _check("agent_2", "clarify_case", _agent2_body(),
                            {"clarification_requests": [_clar(applicable_program_ids=["prog_a"],
                                                              verified_rule_ref="ev_a")]},
                            known=self.KNOWN)
        self.assertTrue(ok, issues)

    def test_reference_that_is_not_text_is_rejected_without_a_crash(self):
        body = {"matches": [{"program_id": "prog_a", "need_ids": [["need_001"]],
                             "match_status": "potential_match", "matched_criteria": [],
                             "missing_case_facts": [], "mismatch_criteria": [],
                             "evidence_refs": [], "explanation": "e"}]}
        ok, issues = _check("agent_4", "match_resources", body,
                            known={"need_id": {"need_001"}, "program_id": {"prog_a"}})
        self.assertFalse(ok)
        self.assertIn("matches[0].need_ids must hold need_id strings", [i["message"] for i in issues])


# ---------------------------------------------------------------- plan-level Agent 10 flags
def _run(**overrides):
    return R.Run(dict(F.ALL, **overrides), FIXTURE_KB, zips_path=FIXTURE_ZIPS).execute(STORY)


def _agent10_with(extra_flags, flag_card_02=False):
    def agent_10(req):
        r = (F.agent_10_always_flags_card_02 if flag_card_02 else F.agent_10_pass)(req)
        r["result"]["flags"] = r["result"]["flags"] + extra_flags
        r["result"]["verdict"] = "FLAG"
        return r
    return agent_10


class TestPlanLevelFlags(unittest.TestCase):
    def test_blocking_plan_level_flag_releases_all_cards(self):
        rep = _run(agent_10=_agent10_with([_flag(None, rule="V12")]))
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(len(rep["plan"]["action_cards"]), 2)
        self.assertEqual(rep["plan"]["withheld_card_ids"], [])
        roles = [s["role_id"] for s in rep["steps"]]
        self.assertEqual(roles.count("agent_8"), 1)          # no repair round for a plan-level flag
        self.assertIn("PLAN_FLAG_NOT_REPAIRED", codes(rep["supervisor_issues"]))
        self.assertIn(None, [f["card_id"] for f in rep["final_validation"]["flags"]])

    def test_plan_level_flag_next_to_a_card_flag(self):
        # before v0.2.6: sorted({"card_02", None}) raised TypeError
        rep = _run(agent_10=_agent10_with([_flag(None, rule="V12")], flag_card_02=True))
        self.assertEqual(rep["outcome"], "completed")
        self.assertEqual(rep["plan"]["withheld_card_ids"], ["card_02"])
        self.assertEqual([c["card_id"] for c in rep["plan"]["action_cards"]], ["card_01"])

    def test_warning_plan_level_flag_is_not_reported(self):
        rep = _run(agent_10=_agent10_with([_flag(None, blocks=False, rule="V11")]))
        self.assertEqual(rep["outcome"], "completed")
        self.assertNotIn("PLAN_FLAG_NOT_REPAIRED", codes(rep["supervisor_issues"]))


# ---------------------------------------------------------------- one-shot run: needs and corrections
class TestOneShotNeeds(unittest.TestCase):
    def test_need_with_no_card_and_no_gap_is_reported(self):
        def agent_8_first_only(req):
            r = F.agent_8(req)
            r["result"]["action_cards"] = r["result"]["action_cards"][:1]
            return r
        rep = _run(agent_8=agent_8_first_only)
        found = [i for i in rep["supervisor_issues"] if i["code"] == "NEED_NOT_IN_PLAN"]
        self.assertEqual([i["related_ref"] for i in found], ["need_002"])

    def test_need_with_a_coverage_gap_is_not_reported(self):
        def agent_8_gap(req):
            r = F.agent_8(req)
            r["result"]["action_cards"] = r["result"]["action_cards"][:1]
            r["result"]["coverage_gaps"] = [{"need_id": "need_002", "note": "No program found."}]
            return r
        rep = _run(agent_8=agent_8_gap)
        self.assertNotIn("NEED_NOT_IN_PLAN", codes(rep["supervisor_issues"]))

    def test_full_plan_reports_nothing(self):
        self.assertNotIn("NEED_NOT_IN_PLAN", codes(_run()["supervisor_issues"]))


class TestOneShotCorrections(unittest.TestCase):
    def _facts_after(self, corrections):
        st = _state()
        req = B.make_request(st, "agent_1", "understand_story", {})
        B.confirm_agent1(st, F.agent_1(req), corrections)
        return {f["field"]: f for f in st.case_facts}

    def test_correction_of_an_extracted_fact(self):
        facts = self._facts_after({"zip_code": "95824"})
        self.assertEqual(facts["zip_code"]["value"], "95824")

    def test_correction_of_a_fact_agent1_did_not_extract_is_added(self):
        facts = self._facts_after({"household_size": 3})
        self.assertEqual(facts["household_size"],
                         {"fact_id": "cf-household_size", "field": "household_size", "value": 3,
                          "confirmation_status": "confirmed", "source": "user_confirmed",
                          "time_context": None})


class TestMakeRequest(unittest.TestCase):
    def test_unknown_role_is_a_value_error(self):
        with self.assertRaises(ValueError):
            B.make_request(_state(), "agent_9", "anything", {})


# ---------------------------------------------------------------- command lines: no traceback
class _Quiet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.out = io.StringIO()
        self.enterContext(contextlib.redirect_stdout(self.out))
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))

    def write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "wb") as f:
            f.write(data)
        return path


class TestOneShotCommandLine(_Quiet):
    def main(self, *extra):
        report = os.path.join(self.tmp, "report.json")
        return R.main(["--agents", FAKE_AGENTS_JSON, "--kb", FIXTURE_KB, "--zips", FIXTURE_ZIPS,
                       "--no-isolate", "--out", report] + list(extra))

    def test_correct_without_equals_sign(self):
        self.assertEqual(self.main("--correct", "household_size"), 2)
        self.assertIn("must look like field=value", self.out.getvalue())

    def test_correct_without_field_name(self):
        self.assertEqual(self.main("--correct", "=5"), 2)

    def test_missing_story_file(self):
        self.assertEqual(self.main("--story-file", os.path.join(self.tmp, "none.txt")), 2)
        self.assertIn("Cannot read story file", self.out.getvalue())

    def test_story_file_not_utf8(self):
        self.assertEqual(self.main("--story-file", self.write("s.txt", b"\xff\xfe\x00bad")), 2)
        self.assertIn("Cannot read story file", self.out.getvalue())

    def test_missing_kb(self):
        rc = R.main(["--agents", FAKE_AGENTS_JSON, "--kb", os.path.join(self.tmp, "none.json"),
                     "--out", os.path.join(self.tmp, "r.json")])
        self.assertEqual(rc, 2)
        self.assertIn("Cannot load the knowledge base", self.out.getvalue())

    def test_kb_without_program_records(self):
        rc = R.main(["--agents", FAKE_AGENTS_JSON, "--kb", self.write("kb.json", b"{}"),
                     "--out", os.path.join(self.tmp, "r.json")])
        self.assertEqual(rc, 2)

    def test_report_cannot_be_written(self):
        rc = R.main(["--agents", FAKE_AGENTS_JSON, "--kb", FIXTURE_KB, "--zips", FIXTURE_ZIPS,
                     "--no-isolate", "--out", os.path.join(self.tmp, "no_dir", "r.json")])
        self.assertEqual(rc, 2)
        self.assertIn("Cannot write the report", self.out.getvalue())

    def test_correction_values(self):
        seen = {}
        original = R.Run.execute

        def spy(run, story, corrections=None):
            seen.update(corrections)
            return original(run, story, corrections)
        with mock.patch.object(R.Run, "execute", spy):
            rc = self.main("--correct", "zip_code=01234", "--correct", "household_size=3",
                           "--correct", "rent_amount_monthly=1450.50",
                           "--correct", "has_written_eviction_notice=true",
                           "--correct", "employment_status=laid_off", "--correct", "note=007")
        self.assertIn(rc, (0, 1))
        self.assertEqual(seen, {"zip_code": "01234", "household_size": 3, "rent_amount_monthly": 1450.5,
                                "has_written_eviction_notice": True, "employment_status": "laid_off",
                                "note": "007"})


class TestDialogCommandLineEncoding(_Quiet):
    """A file that is not UTF-8 gives exit 2 and a one-line message, never a traceback."""

    def flags(self):
        return ["--agents", FAKE_DIALOG_AGENTS_JSON, "--kb", FIXTURE_KB, "--zips", FIXTURE_ZIPS,
                "--no-isolate", "--out", os.path.join(self.tmp, "out.json")]

    def test_story_file(self):
        bad = self.write("s.txt", b"\xff\xfe\x00bad")
        self.assertEqual(D.main(["start", "--story-file", bad] + self.flags()), 2)
        self.assertIn("Cannot read story file", self.out.getvalue())

    def test_answer_files(self):
        bad = self.write("b.json", b"\xff\xfe\x00bad")
        good = self.write("a.json", b"[]")
        self.assertEqual(D.main(["answer", "--case-in", bad, "--answers-file", good] + self.flags()), 2)
        prev = self.write("p.json", b'{"case": null}')
        self.assertEqual(D.main(["answer", "--case-in", prev, "--answers-file", bad] + self.flags()), 2)

    def test_confirm_files(self):
        bad = self.write("b.json", b"\xff\xfe\x00bad")
        prev = self.write("p.json", b'{"case": null}')
        self.assertEqual(D.main(["confirm", "--case-in", bad] + self.flags()), 2)
        self.assertEqual(D.main(["confirm", "--case-in", prev, "--corrections-file", bad] + self.flags()), 2)
        self.assertEqual(D.main(["confirm", "--case-in", prev, "--added-file", bad] + self.flags()), 2)


class TestHttpCommandLine(_Quiet):
    def test_missing_kb_stops_at_start(self):
        rc = H.main(["--agents", FAKE_DIALOG_AGENTS_JSON, "--kb", os.path.join(self.tmp, "none.json")])
        self.assertEqual(rc, 2)
        self.assertIn("Cannot load the knowledge base", self.out.getvalue())

    def test_port_in_use(self):
        with mock.patch.object(H, "make_server", side_effect=OSError("address already in use")):
            rc = H.main(["--agents", FAKE_DIALOG_AGENTS_JSON, "--kb", FIXTURE_KB])
        self.assertEqual(rc, 2)
        self.assertIn("Cannot listen on 127.0.0.1:8765", self.out.getvalue())


if __name__ == "__main__":
    unittest.main()
