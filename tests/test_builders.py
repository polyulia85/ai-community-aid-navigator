"""Tests for Supervisor builders. Run from the repo root:  python -m unittest -v"""
import copy
import datetime
import json
import os
import tempfile
import unittest

from navigator.supervisor import builders as B
from navigator.supervisor import checks
from navigator.supervisor import contract as C
from tests.fake_agents import FIXTURE_KB, FIXTURE_ZIPS

ROOT = os.path.join(os.path.dirname(__file__), "..", "navigator")
KB = FIXTURE_KB


def load(name):
    with open(os.path.join(ROOT, "samples", name), encoding="utf-8") as f:
        return json.load(f)


def new_state():
    return B.CaseState("case-demo-001", "run-0001", "corr-0001")


class TestRequests(unittest.TestCase):
    def test_every_request_has_all_envelope_fields(self):
        st = new_state()
        req, _ = B.agent1_request(st, "I lost my job.", ref_date=datetime.date(2026, 11, 15))
        self.assertEqual(set(C.REQUEST_FIELDS) - set(req), set())
        self.assertEqual(req["schema_version"], "1.0")

    def test_request_ids_are_unique(self):
        st = new_state()
        a, _ = B.agent1_request(st, "x", ref_date=datetime.date(2026, 11, 15)); b = B.agent2_request(st)
        self.assertNotEqual(a["request_id"], b["request_id"])

    def test_s0_runs_before_agent1(self):
        st = new_state()
        req, issues = B.agent1_request(st, "My SSN is 123-45-6789, rent $1,450.", ref_date=datetime.date(2026, 11, 15))
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
        zip_to_county, _ = B.load_zip_county(FIXTURE_ZIPS)
        req, issues = B.agent3_request(self.st, zip_to_county)
        self.assertEqual([i["code"] for i in issues], ["COUNTY_FROM_ZIP_LIST"])
        self.assertEqual(req["payload"]["geography"], ["Sacramento County", "95823"])
        for n in req["payload"]["needs"]:
            self.assertEqual(set(n), {"need_id", "category", "description", "urgency"})

    def test_unknown_zip_gives_warning_not_guess(self):
        zip_to_county, _ = B.load_zip_county(FIXTURE_ZIPS)
        for f in self.st.case_facts:
            if f["field"] == "zip_code":
                f["value"] = "00000"
        req, issues = B.agent3_request(self.st, zip_to_county)
        self.assertEqual(req["payload"]["geography"], ["00000"])
        self.assertEqual(issues[0]["code"], "COUNTY_UNKNOWN")
        self.assertNotIn("00000", issues[0]["message"])


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
        # Shared timing/enum assertions used by both cases below.
        a4 = {"result": {"matches": []}}; a5 = {"result": {"checked_claims": []}}

        def _check_timing_and_enums(pkg):
            t = {x["program_id"]: x for x in pkg["timing"]}
            housing = t["prog_housing_saintjohns_sac_001"]
            self.assertEqual(housing["user_target_date"], "2026-11-01")   # the user's date
            self.assertIsNone(housing["official_deadline"])               # never invented
            self.assertIsNone(t["prog_income_edd_ui_ca_001"]["user_target_date"])
            self.assertIn("three weeks", t["prog_income_edd_ui_ca_001"]["estimated_processing_time"])
            self.assertEqual(checks.s4_enums({"result": pkg}), [])

        # Case A: Saint John's temporarily_closed → package reflects that
        progs_a = copy.deepcopy(self.programs)
        progs_a["prog_housing_saintjohns_sac_001"]["availability"] = "temporarily_closed"
        pkg_a = B.planning_package(self.st, progs_a, self.evidence, self.cands, a4, a5)
        avail_a = {a["program_id"]: a["availability"] for a in pkg_a["program_availability"]}
        self.assertEqual(avail_a["prog_housing_saintjohns_sac_001"], "temporarily_closed")
        _check_timing_and_enums(pkg_a)

        # Case B: Saint John's confirmed_open → package reflects that
        progs_b = copy.deepcopy(self.programs)
        progs_b["prog_housing_saintjohns_sac_001"]["availability"] = "confirmed_open"
        pkg_b = B.planning_package(self.st, progs_b, self.evidence, self.cands, a4, a5)
        avail_b = {a["program_id"]: a["availability"] for a in pkg_b["program_availability"]}
        self.assertEqual(avail_b["prog_housing_saintjohns_sac_001"], "confirmed_open")
        _check_timing_and_enums(pkg_b)

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
        req, _ = B.agent1_request(new_state(), "x", ref_date=datetime.date(2026, 11, 15))    # built at version 1
        old = dict(load("02_agent1_result_expected.json"), case_version=req["case_version"])
        self.assertIn("STALE_RESULT", {i["code"] for i in checks.s3_stale(old, self.st.case_version)})


class TestZipCounty(unittest.TestCase):
    """load_zip_county, geography, agent3_request ZIP behaviour."""

    def setUp(self):
        self.zip_to_county, self.load_issues = B.load_zip_county(FIXTURE_ZIPS)
        self.st = new_state()
        B.confirm_agent1(self.st, load("02_agent1_result_expected.json"))

    def test_listed_zip_gives_county_no_county_unknown(self):
        """95660 (in fixture) -> Sacramento County; COUNTY_FROM_ZIP_LIST info; no COUNTY_UNKNOWN."""
        # Set zip_code to 95660
        for f in self.st.case_facts:
            if f["field"] == "zip_code":
                f["value"] = "95660"
        req, issues = B.agent3_request(self.st, self.zip_to_county)
        geo = req["payload"]["geography"]
        self.assertIn("Sacramento County", geo)
        self.assertIn("95660", geo)
        codes = {i["code"] for i in issues}
        self.assertIn("COUNTY_FROM_ZIP_LIST", codes)
        self.assertNotIn("COUNTY_UNKNOWN", codes)

    def test_unlisted_zip_gives_county_unknown_no_zip_in_message(self):
        """99999 (not in fixture) -> COUNTY_UNKNOWN; '99999' not in any issue message."""
        for f in self.st.case_facts:
            if f["field"] == "zip_code":
                f["value"] = "99999"
        req, issues = B.agent3_request(self.st, self.zip_to_county)
        codes = {i["code"] for i in issues}
        self.assertIn("COUNTY_UNKNOWN", codes)
        for i in issues:
            self.assertNotIn("99999", i["message"])

    def test_user_county_fact_wins_over_list(self):
        """When the user has a 'county' fact, it is used directly; no COUNTY_FROM_ZIP_LIST."""
        self.st.case_facts.append({"fact_id": "f99", "field": "county",
                                   "value": "Placer County",
                                   "confirmation_status": "confirmed",
                                   "source": "user_confirmed", "time_context": None})
        req, issues = B.agent3_request(self.st, self.zip_to_county)
        geo = req["payload"]["geography"]
        self.assertIn("Placer County", geo)
        codes = {i["code"] for i in issues}
        self.assertNotIn("COUNTY_FROM_ZIP_LIST", codes)
        self.assertNotIn("COUNTY_UNKNOWN", codes)

    def test_unverified_list_not_used_zip_list_unavailable(self):
        """verification_status != 'verified' -> empty dict + ZIP_LIST_UNAVAILABLE."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False, encoding="utf-8") as f:
            json.dump({"county": "Sacramento County",
                       "verification_status": "needs_review",
                       "zips": ["95823"]}, f)
            tmp = f.name
        try:
            d, issues = B.load_zip_county(tmp)
            self.assertEqual(d, {})
            self.assertTrue(any(i["code"] == "ZIP_LIST_UNAVAILABLE" for i in issues))
        finally:
            os.unlink(tmp)

    def test_missing_file_no_exception_zip_list_unavailable(self):
        """A missing file -> empty dict + ZIP_LIST_UNAVAILABLE; no exception."""
        d, issues = B.load_zip_county("/nonexistent/path/zips.json")
        self.assertEqual(d, {})
        self.assertTrue(any(i["code"] == "ZIP_LIST_UNAVAILABLE" for i in issues))


class TestCaseStateSeq(unittest.TestCase):
    """CaseState.next_seq and first_seq for dialog continuity."""

    def test_next_seq_starts_at_one(self):
        st = B.CaseState("c", "r", "x")
        self.assertEqual(st.next_seq, 1)

    def test_next_seq_increments_with_ids(self):
        st = B.CaseState("c", "r", "x")
        st.next_request_id()
        st.next_request_id()
        self.assertEqual(st.next_seq, 3)

    def test_first_seq_restores_counter(self):
        st = B.CaseState("c", "r", "x", first_seq=5)
        rid = st.next_request_id()
        self.assertEqual(rid, "req-0005")
        self.assertEqual(st.next_seq, 6)

    def test_default_behaviour_unchanged(self):
        """first_seq=1 default: first id is req-0001."""
        st = B.CaseState("c", "r", "x")
        self.assertEqual(st.next_request_id(), "req-0001")


class TestAgent1AnswerRequest(unittest.TestCase):
    """agent1_answer_request: S0 masking, validation, payload shape."""

    def setUp(self):
        self.st = new_state()
        self.ref = datetime.date(2026, 11, 15)

    def test_ssn_in_answer_is_masked(self):
        req, issues = B.agent1_answer_request(
            self.st, "My number is 123-45-6789", ["zip_code"], self.ref)
        self.assertNotIn("123-45-6789", req["payload"]["answer_text"])
        self.assertTrue(any(i["code"] == "PII_MASKED" for i in issues))
        for i in issues:
            self.assertNotIn("123-45-6789", i["message"])

    def test_pending_fact_keys_in_payload(self):
        req, _ = B.agent1_answer_request(
            self.st, "95823", ["zip_code"], self.ref)
        self.assertEqual(req["payload"]["pending_fact_keys"], ["zip_code"])
        self.assertEqual(req["payload"]["ref_date"], "2026-11-15")

    def test_existing_needs_in_payload(self):
        self.st.needs = [{"need_id": "need_001", "category": "housing_assistance",
                          "confirmation_status": "proposed"}]
        req, _ = B.agent1_answer_request(self.st, "yes", ["zip_code"], self.ref)
        self.assertEqual(req["payload"]["existing_needs"],
                         [{"need_id": "need_001", "category": "housing_assistance"}])

    def test_ref_date_none_raises(self):
        with self.assertRaises(ValueError):
            B.agent1_answer_request(self.st, "x", ["zip_code"], None)

    def test_empty_pending_keys_raises(self):
        with self.assertRaises(ValueError):
            B.agent1_answer_request(self.st, "x", [], self.ref)

    def test_non_list_pending_keys_raises(self):
        with self.assertRaises(ValueError):
            B.agent1_answer_request(self.st, "x", "zip_code", self.ref)

    def test_pending_keys_with_empty_string_raises(self):
        with self.assertRaises(ValueError):
            B.agent1_answer_request(self.st, "x", ["zip_code", ""], self.ref)


class TestMergeAnswerFacts(unittest.TestCase):
    """merge_answer_facts: asked fields replaced; new fields beyond question added as proposed;
    equal value beyond question skipped silently; differing value beyond question keeps old with
    ANSWER_FACT_CONFLICT; invalid items dropped with ANSWER_FACT_INVALID."""

    def _claim(self, field, value, fact_id="f1"):
        return {"fact_id": fact_id, "field": field, "value": value,
                "confirmation_status": "proposed", "source": "user_statement",
                "time_context": None}

    def _result(self, claims):
        return {"result": {"factual_claims": claims}}

    def test_asked_field_replaces_existing(self):
        """A claim for a field in pending_fact_keys replaces the existing fact."""
        st = new_state()
        st.case_facts = [self._claim("zip_code", "00000", "f0")]
        B.merge_answer_facts(st, self._result([self._claim("zip_code", "95823")]), ["zip_code"])
        vals = [f["value"] for f in st.case_facts if f["field"] == "zip_code"]
        self.assertEqual(vals, ["95823"])
        self.assertEqual(len(st.case_facts), 1)

    def test_new_field_beyond_question_added_as_proposed(self):
        """A claim for a new field not in pending → added as proposed with ANSWER_FACT_OUTSIDE_QUESTION (info)."""
        st = new_state()
        issues = B.merge_answer_facts(st, self._result([
            self._claim("zip_code", "95823"),
            self._claim("household_size", 3),   # not in pending, not yet a fact
        ]), ["zip_code"])
        fields = {f["field"] for f in st.case_facts}
        self.assertIn("household_size", fields)
        outside = [i for i in issues if i["code"] == "ANSWER_FACT_OUTSIDE_QUESTION"]
        self.assertEqual(len(outside), 1)
        self.assertEqual(outside[0]["severity"], "info")
        self.assertEqual(outside[0]["related_ref"], "household_size")
        # message must name the field only, not the value
        self.assertNotIn("3", outside[0]["message"])

    def test_existing_field_beyond_question_keeps_old_value_with_conflict(self):
        """A claim for a field that already exists and is not in pending → ANSWER_FACT_CONFLICT (warning), old value kept."""
        st = new_state()
        st.case_facts = [self._claim("household_size", 4, "f0")]
        issues = B.merge_answer_facts(st, self._result([
            self._claim("zip_code", "95823"),
            self._claim("household_size", 3),   # conflicts with existing fact
        ]), ["zip_code"])
        vals = [f["value"] for f in st.case_facts if f["field"] == "household_size"]
        self.assertEqual(vals, [4])    # old value kept
        conflict = [i for i in issues if i["code"] == "ANSWER_FACT_CONFLICT"]
        self.assertEqual(len(conflict), 1)
        self.assertEqual(conflict[0]["severity"], "warning")
        self.assertEqual(conflict[0]["related_ref"], "household_size")
        self.assertNotIn("3", conflict[0]["message"])
        self.assertNotIn("4", conflict[0]["message"])

    def test_two_claims_for_same_new_field_first_kept_second_conflicts(self):
        """Two claims for the same new field in one answer: first is kept, second gives ANSWER_FACT_CONFLICT."""
        st = new_state()
        issues = B.merge_answer_facts(st, self._result([
            self._claim("household_size", 3, "f1"),
            self._claim("household_size", 5, "f2"),   # duplicate new field
        ]), ["zip_code"])
        vals = [f["value"] for f in st.case_facts if f["field"] == "household_size"]
        self.assertEqual(vals, [3])    # first claim kept
        outside = [i for i in issues if i["code"] == "ANSWER_FACT_OUTSIDE_QUESTION"]
        conflict = [i for i in issues if i["code"] == "ANSWER_FACT_CONFLICT"]
        self.assertEqual(len(outside), 1)
        self.assertEqual(len(conflict), 1)
        self.assertEqual(conflict[0]["related_ref"], "household_size")

    def test_income_zero_is_kept(self):
        """income '0' is a real answer (Julia's decision); it must not be dropped as falsy."""
        st = new_state()
        B.merge_answer_facts(st, self._result([
            self._claim("household_gross_monthly_income", 0)
        ]), ["household_gross_monthly_income"])
        vals = [f["value"] for f in st.case_facts
                if f["field"] == "household_gross_monthly_income"]
        self.assertEqual(vals, [0])

    def test_unanswered_key_stays_absent(self):
        """A field in pending_fact_keys that the result does not mention stays absent."""
        st = new_state()
        B.merge_answer_facts(st, self._result([]), ["zip_code", "household_size"])
        fields = {f["field"] for f in st.case_facts}
        self.assertNotIn("zip_code", fields)
        self.assertNotIn("household_size", fields)

    def test_confirmation_status_stays_proposed(self):
        st = new_state()
        B.merge_answer_facts(st, self._result([self._claim("zip_code", "95823")]), ["zip_code"])
        self.assertEqual(st.case_facts[0]["confirmation_status"], "proposed")

    def test_equal_value_beyond_question_silent(self):
        """A claim outside pending whose value equals the existing fact → silent skip, no issue."""
        st = new_state()
        st.case_facts = [self._claim("household_size", 4, "f0")]
        issues = B.merge_answer_facts(st, self._result([
            self._claim("zip_code", "95823"),
            self._claim("household_size", 4),   # same value as existing
        ]), ["zip_code"])
        vals = [f["value"] for f in st.case_facts if f["field"] == "household_size"]
        self.assertEqual(vals, [4])
        self.assertEqual(issues, [])

    def test_claim_not_a_dict_dropped_with_invalid(self):
        """A factual_claims item that is not a dict → ANSWER_FACT_INVALID (warning), case unchanged."""
        st = new_state()
        issues = B.merge_answer_facts(st, self._result(["not-a-dict"]), ["zip_code"])
        self.assertEqual(len(st.case_facts), 0)
        inv = [i for i in issues if i["code"] == "ANSWER_FACT_INVALID"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0]["severity"], "warning")
        self.assertIsNone(inv[0]["related_ref"])

    def test_claim_field_null_dropped_with_invalid(self):
        """A factual_claims item with field=null → ANSWER_FACT_INVALID (warning), case unchanged."""
        st = new_state()
        issues = B.merge_answer_facts(st, self._result([{"field": None, "value": "x",
                                                          "fact_id": "f1",
                                                          "confirmation_status": "proposed",
                                                          "source": "user_statement",
                                                          "time_context": None}]), ["zip_code"])
        self.assertEqual(len(st.case_facts), 0)
        inv = [i for i in issues if i["code"] == "ANSWER_FACT_INVALID"]
        self.assertEqual(len(inv), 1)
        self.assertIsNone(inv[0]["related_ref"])

    def test_factual_claims_null_treated_as_empty(self):
        """factual_claims=null → loop skipped, no issues, case unchanged."""
        st = new_state()
        st.case_facts = [self._claim("zip_code", "95823", "f0")]
        issues = B.merge_answer_facts(
            st, {"result": {"factual_claims": None}}, ["zip_code"])
        self.assertEqual(len(st.case_facts), 1)
        self.assertEqual(issues, [])

    def test_factual_claims_not_a_list_invalid(self):
        """factual_claims present but not a list (e.g. a dict) → ANSWER_FACT_INVALID, case unchanged."""
        st = new_state()
        st.case_facts = [self._claim("zip_code", "95823", "f0")]
        issues = B.merge_answer_facts(
            st, {"result": {"factual_claims": {"field": "zip_code", "value": "99999"}}},
            ["zip_code"])
        self.assertEqual(len(st.case_facts), 1)
        self.assertEqual(st.case_facts[0]["value"], "95823")   # unchanged
        inv = [i for i in issues if i["code"] == "ANSWER_FACT_INVALID"]
        self.assertEqual(len(inv), 1)
        self.assertIsNone(inv[0]["related_ref"])


class TestMergeAnswerNeeds(unittest.TestCase):
    """merge_answer_needs: new needs added, duplicates dropped."""

    def _need(self, nid, cat):
        return {"need_id": nid, "category": cat, "description": "d",
                "original_quote": "q", "confirmation_status": "proposed",
                "user_reported": True, "urgency": "normal",
                "urgency_reason": None, "user_priority": None}

    def _result(self, needs):
        return {"result": {"factual_claims": [], "proposed_needs": needs}}

    def test_new_food_need_added_as_proposed(self):
        st = new_state()
        st.needs = [self._need("need_001", "housing_assistance"),
                    self._need("need_002", "income_assistance")]
        issues = B.merge_answer_needs(st, self._result([
            self._need("need_003", "food_assistance")]))
        self.assertEqual(len(st.needs), 3)
        self.assertEqual(st.needs[2]["need_id"], "need_003")
        self.assertEqual(st.needs[2]["confirmation_status"], "proposed")
        self.assertEqual(issues, [])

    def test_reused_need_id_dropped_with_warning(self):
        st = new_state()
        st.needs = [self._need("need_001", "housing_assistance")]
        issues = B.merge_answer_needs(st, self._result([
            self._need("need_001", "food_assistance")]))  # same id
        self.assertEqual(len(st.needs), 1)
        dup = [i for i in issues if i["code"] == "ANSWER_NEED_DUPLICATE"]
        self.assertEqual(len(dup), 1)
        self.assertEqual(dup[0]["related_ref"], "need_001")

    def test_existing_category_dropped_with_warning(self):
        st = new_state()
        st.needs = [self._need("need_001", "housing_assistance")]
        issues = B.merge_answer_needs(st, self._result([
            self._need("need_002", "housing_assistance")]))  # same category
        self.assertEqual(len(st.needs), 1)
        dup = [i for i in issues if i["code"] == "ANSWER_NEED_DUPLICATE"]
        self.assertEqual(len(dup), 1)
        self.assertEqual(dup[0]["related_ref"], "need_002")
        self.assertIn("housing_assistance", dup[0]["message"])

    def test_no_proposed_needs_key_valid(self):
        """Result without proposed_needs is valid."""
        st = new_state()
        st.needs = [self._need("need_001", "housing_assistance")]
        issues = B.merge_answer_needs(st, {"result": {"factual_claims": []}})
        self.assertEqual(len(st.needs), 1)
        self.assertEqual(issues, [])

    def test_proposed_needs_not_a_list_warning(self):
        """proposed_needs present but not a list -> ANSWER_NEEDS_INVALID, nothing added."""
        st = new_state()
        st.needs = [self._need("need_001", "housing_assistance")]
        issues = B.merge_answer_needs(st, {"result": {"proposed_needs": {"bad": True}}})
        self.assertEqual(len(st.needs), 1)
        self.assertTrue(any(i["code"] == "ANSWER_NEEDS_INVALID" for i in issues))

    def test_item_not_a_dict_dropped(self):
        """proposed_needs item that is not a dict -> ANSWER_NEED_INVALID, related_ref None."""
        st = new_state()
        issues = B.merge_answer_needs(st, self._result(["not-a-dict"]))
        self.assertEqual(len(st.needs), 0)
        inv = [i for i in issues if i["code"] == "ANSWER_NEED_INVALID"]
        self.assertEqual(len(inv), 1)
        self.assertIsNone(inv[0]["related_ref"])

    def test_item_missing_category_dropped(self):
        """Item with need_id but no category -> ANSWER_NEED_INVALID, related_ref is the need_id."""
        st = new_state()
        issues = B.merge_answer_needs(st, self._result([{"need_id": "need_003"}]))
        self.assertEqual(len(st.needs), 0)
        inv = [i for i in issues if i["code"] == "ANSWER_NEED_INVALID"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0]["related_ref"], "need_003")

    def test_item_missing_need_id_dropped(self):
        """Item with category but no need_id -> ANSWER_NEED_INVALID, related_ref None."""
        st = new_state()
        issues = B.merge_answer_needs(st, self._result([{"category": "food_assistance"}]))
        self.assertEqual(len(st.needs), 0)
        inv = [i for i in issues if i["code"] == "ANSWER_NEED_INVALID"]
        self.assertEqual(len(inv), 1)
        self.assertIsNone(inv[0]["related_ref"])


if __name__ == "__main__":
    unittest.main()
