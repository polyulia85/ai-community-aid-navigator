"""Tests for Supervisor builders. Run from the repo root:  python -m unittest -v"""
import json
import os
import unittest

from navigator.supervisor import builders as B
from navigator.supervisor import checks
from navigator.supervisor import contract as C

ROOT = os.path.join(os.path.dirname(__file__), "..", "navigator")
KB = os.path.join(ROOT, "kb", "kb_sacramento.json")


def load(name):
    with open(os.path.join(ROOT, "samples", name), encoding="utf-8") as f:
        return json.load(f)


def new_state():
    return B.CaseState("case-demo-001", "run-0001", "corr-0001")


class TestRequests(unittest.TestCase):
    def test_every_request_has_all_envelope_fields(self):
        st = new_state()
        req, _ = B.agent1_request(st, "I lost my job.")
        self.assertEqual(set(C.REQUEST_FIELDS) - set(req), set())
        self.assertEqual(req["schema_version"], "1.0")

    def test_request_ids_are_unique(self):
        st = new_state()
        a, _ = B.agent1_request(st, "x"); b = B.agent2_request(st)
        self.assertNotEqual(a["request_id"], b["request_id"])

    def test_s0_runs_before_agent1(self):
        st = new_state()
        req, issues = B.agent1_request(st, "My SSN is 123-45-6789, rent $1,450.")
        self.assertNotIn("123-45-6789", req["payload"]["story_text"])
        self.assertIn("$1,450", req["payload"]["story_text"])
        self.assertEqual(issues[0]["code"], "PII_MASKED")

    def test_wrong_task_type_is_refused(self):
        with self.assertRaises(AssertionError):
            B.make_request(new_state(), "agent_4", "verify_resources", {})


class TestFromAgent1(unittest.TestCase):
    def setUp(self):
        self.st = new_state()
        B.confirm_agent1(self.st, load("02_agent1_result_expected.json"),
                         corrections={"cash_on_hand_approx": 300})

    def test_confirm_bumps_version_and_confirms(self):
        self.assertEqual(self.st.case_version, 2)
        self.assertTrue(all(n["confirmation_status"] == "confirmed" for n in self.st.needs))
        self.assertTrue(all(f["source"] == "user_confirmed" for f in self.st.case_facts))
        self.assertEqual(self.st.fact("cash_on_hand_approx"), 300)

    def test_agent3_gets_four_need_fields_and_county_plus_zip(self):
        req, issues = B.agent3_request(self.st)
        self.assertEqual(issues, [])
        self.assertEqual(req["payload"]["geography"], ["Sacramento County", "95823"])
        for n in req["payload"]["needs"]:
            self.assertEqual(set(n), {"need_id", "category", "description", "urgency"})

    def test_unknown_zip_gives_warning_not_guess(self):
        for f in self.st.case_facts:
            if f["field"] == "zip_code":
                f["value"] = "00000"
        req, issues = B.agent3_request(self.st)
        self.assertEqual(req["payload"]["geography"], ["00000"])
        self.assertEqual(issues[0]["code"], "COUNTY_UNKNOWN")


class TestWithKB(unittest.TestCase):
    def setUp(self):
        self.programs, self.evidence = B.load_kb(KB)
        self.st = new_state()
        B.confirm_agent1(self.st, load("02_agent1_result_expected.json"))
        self.cands = {"result": {"candidate_programs": [
            {"program_id": p, "matched_need_ids": [n], "retrieval_reason": "test",
             "source_refs": [], "missing_fields": []}
            for p, n in (("prog_housing_saintjohns_sac_001", "need_002"),
                         ("prog_income_edd_ui_ca_001", "need_001"))]}}

    def test_program_criteria_from_kb(self):
        crit = B.program_criteria(self.programs, self.evidence, ["prog_income_edd_ui_ca_001"])
        self.assertIn({"program_id": "prog_income_edd_ui_ca_001", "field_path": "geography[0]",
                       "value": "California"}, [{k: c[k] for k in ("program_id", "field_path", "value")} for c in crit])
        for c in crit:
            for e in c["evidence_refs"]:
                self.assertIn(e, self.evidence)

    def test_agent5_skips_confirmed_mismatch(self):
        a4 = {"result": {"matches": [
            {"program_id": "p_ok", "match_status": "potential_match"},
            {"program_id": "p_no", "match_status": "confirmed_mismatch"}]}}
        req = B.agent5_request(self.st, {"request_id": "req-0004"}, a4)
        self.assertEqual([p["program_id"] for p in req["payload"]["programs_to_check"]], ["p_ok"])

    def test_planning_package_availability_and_timing(self):
        a4 = {"result": {"matches": []}}; a5 = {"result": {"checked_claims": []}}
        pkg = B.planning_package(self.st, self.programs, self.evidence, self.cands, a4, a5)
        avail = {a["program_id"]: a["availability"] for a in pkg["program_availability"]}
        self.assertEqual(avail["prog_housing_saintjohns_sac_001"], "temporarily_closed")
        t = {x["program_id"]: x for x in pkg["timing"]}
        housing = t["prog_housing_saintjohns_sac_001"]
        self.assertEqual(housing["user_target_date"], "2026-11-01")   # the user's date
        self.assertIsNone(housing["official_deadline"])               # never invented
        self.assertIsNone(t["prog_income_edd_ui_ca_001"]["user_target_date"])
        self.assertIn("three weeks", t["prog_income_edd_ui_ca_001"]["estimated_processing_time"])
        # the package itself must pass the Supervisor's own privacy and enum checks
        self.assertEqual(checks.s4_enums({"result": pkg}), [])

    def test_planning_package_passes_availability_evidence(self):
        """Availability rows (e.g. a closure or reopening note) reach Agents 6, 8 and 10 (fix Oct 25)."""
        a4 = {"result": {"matches": []}}; a5 = {"result": {"checked_claims": []}}
        pkg = B.planning_package(self.st, self.programs, self.evidence, self.cands, a4, a5)
        passed = {e["evidence_id"] for e in pkg["evidence_records"]}
        for a in pkg["program_availability"]:
            for ref in a["evidence_refs"]:
                self.assertIn(ref, passed)

    def test_planning_package_adds_program_name_and_subcategory(self):
        """Contracts v1.1: matches in the package carry program_name and subcategory from the KB."""
        a4 = {"result": {"matches": [{"program_id": "prog_housing_saintjohns_sac_001", "need_ids": ["need_002"],
                                      "match_status": "potential_match"}]}}
        a5 = {"result": {"checked_claims": []}}
        pkg = B.planning_package(self.st, self.programs, self.evidence, self.cands, a4, a5)
        m = pkg["matches"][0]
        self.assertEqual(m["program_name"], self.programs["prog_housing_saintjohns_sac_001"]["program_name"])
        self.assertEqual(m["subcategory"], "rental_assistance")
        self.assertEqual(m["organization"], self.programs["prog_housing_saintjohns_sac_001"]["organization"])
        self.assertNotIn("program_name", a4["result"]["matches"][0])   # Agent 4 result untouched

    def test_stale_result_after_confirmation(self):
        req, _ = B.agent1_request(new_state(), "x")    # built at version 1
        old = dict(load("02_agent1_result_expected.json"), case_version=req["case_version"])
        self.assertIn("STALE_RESULT", {i["code"] for i in checks.s3_stale(old, self.st.case_version)})


if __name__ == "__main__":
    unittest.main()
