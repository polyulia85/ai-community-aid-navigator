"""Tests for Agents 3-5 (Silver). Run from repo root:  python -m unittest discover tests -v"""
import copy, json, os, tempfile, unittest
from navigator.agents.agent_3_4_5 import agent_3, agent_4, agent_5
from navigator.agents.agent_3_4_5.common import build_program_criteria_from_kb

BASE = {"request_id": "req-0101", "run_id": "run-0001", "case_id": "case-demo-001", "case_version": 1,
        "correlation_id": "corr-0001", "schema_version": "1.0", "allowed_case_facts": [], "upstream_result_refs": []}
NEEDS = [  # from navigator/samples/02_agent1_result_expected.json (shared test case)
    {"need_id": "need_001", "category": "income_assistance", "subcategory": None, "description": "Lost job", "urgency": "high"},
    {"need_id": "need_002", "category": "housing_assistance", "subcategory": "rental_assistance", "description": "Rent due Nov 1", "urgency": "high"},
    {"need_id": "need_003", "category": "food_assistance", "subcategory": None, "description": "Low on food", "urgency": "immediate"}]
FACTS = [{"fact_id": "fact_001", "field": "zip_code", "value": "95823", "confirmation_status": "proposed", "source": "user_statement", "time_context": None},
         {"fact_id": "fact_002", "field": "household_size", "value": 3, "confirmation_status": "proposed", "source": "user_statement", "time_context": None}]
GEO = ["95823", "Sacramento County"]  # Supervisor maps ZIP -> county and passes both (Slav, Oct 22)
CALFRESH, UI = "prog_food_calfresh_sac_001", "prog_income_edd_ui_ca_001"
SJ, CAS = "prog_housing_saintjohns_sac_001", "prog_housing_coordaccess_sac_001"


def req(role, task, payload):
    r = copy.deepcopy(BASE); r.update(role_id=role, task_type=task, payload=payload); return r


def check_envelope(t, request, result, agent_id):
    for k in ("request_id", "run_id", "case_id", "case_version", "correlation_id"):
        t.assertEqual(result[k], request[k])
    t.assertEqual(result["agent_id"], agent_id)
    t.assertIn(result["status"], {"completed", "partial", "needs_clarification", "failed"})
    for k in ("result", "issues", "clarification_requests", "evidence_refs", "generated_at", "is_mock", "schema_version"):
        t.assertIn(k, result)


def retrieve(needs=NEEDS, geography=GEO):
    return agent_3.handle(req("agent_3", "retrieve_candidates", {"needs": needs, "geography": geography, "retrieval_constraints": []}))


def match(cands, facts):
    crit = build_program_criteria_from_kb([c["program_id"] for c in cands])  # stands in for the Supervisor
    return agent_4.handle(req("agent_4", "match_resources", {"candidate_programs": cands, "case_facts": facts, "needs": NEEDS, "program_criteria": crit}))


class T1_ClearMatch(unittest.TestCase):
    """Shared family case: all three P0 needs retrieve real KB programs, matched as potential_match."""
    def test_all_three_needs_covered(self):
        r3 = req("agent_3", "retrieve_candidates", {"needs": NEEDS, "geography": GEO, "retrieval_constraints": []})
        out3 = agent_3.handle(r3); check_envelope(self, r3, out3, "agent_3")
        by = {c["program_id"]: c["matched_need_ids"] for c in out3["result"]["candidate_programs"]}
        # These four original programs must always be present; Nov 12 adds more.
        for pid, need in ((UI, "need_001"), (SJ, "need_002"), (CAS, "need_002"), (CALFRESH, "need_003")):
            self.assertIn(pid, by, f"{pid} must be in the candidates")
            self.assertEqual(by[pid], [need], f"{pid} matched needs wrong")
        self.assertFalse([i for i in out3["issues"] if i["code"] == "COVERAGE_GAP"])
        r4cands = out3["result"]["candidate_programs"]
        out4 = match(r4cands, FACTS)
        for m in out4["result"]["matches"]:
            self.assertEqual(m["match_status"], "potential_match")  # facts only proposed -> not yet supported_match
            self.assertNotIn("you qualify", m["explanation"].lower())

    def test_supported_match_needs_no_missing_facts(self):  # decision 9 (proposed)
        cand = [{"program_id": CALFRESH, "matched_need_ids": ["need_003"]}]
        confirmed = [dict(f, confirmation_status="confirmed") for f in FACTS]
        self.assertEqual(match(cand, confirmed)["result"]["matches"][0]["match_status"], "potential_match")  # income unknown
        with_income = confirmed + [{"fact_id": "fact_009", "field": "household_gross_monthly_income", "value": 0, "confirmation_status": "confirmed"}]
        # v1.6 (Julia 4.2): CalFresh has eligibility criteria that are not evaluated yet, so it stays potential_match
        self.assertEqual(match(cand, with_income)["result"]["matches"][0]["match_status"], "potential_match")


class T2_UnknownInfo(unittest.TestCase):
    """Unknown income is never a mismatch; unknown location -> insufficient_information; confirmed outside area -> mismatch."""
    def run4(self, facts, criteria=True):
        cands = [{"program_id": CALFRESH, "matched_need_ids": ["need_003"]}]
        if criteria:
            return match(cands, facts)
        return agent_4.handle(req("agent_4", "match_resources", {"candidate_programs": cands, "case_facts": facts, "needs": NEEDS, "program_criteria": []}))

    def test_unknown_income_not_mismatch(self):
        m = self.run4(FACTS)["result"]["matches"][0]
        self.assertNotEqual(m["match_status"], "confirmed_mismatch")
        self.assertIn("household_gross_monthly_income", m["missing_case_facts"])

    def test_unknown_location(self):
        self.assertEqual(self.run4([])["result"]["matches"][0]["match_status"], "insufficient_information")

    def test_confirmed_outside_area_names_criterion(self):
        m = self.run4([{"fact_id": "f", "field": "county", "value": "Alameda County", "confirmation_status": "confirmed"}])["result"]["matches"][0]
        self.assertEqual(m["match_status"], "confirmed_mismatch")
        self.assertTrue(m["mismatch_criteria"])

    def test_missing_program_criteria_is_reported_not_guessed(self):
        out = self.run4(FACTS, criteria=False)
        self.assertEqual(out["result"]["matches"][0]["match_status"], "insufficient_information")
        self.assertIn("PROGRAM_CRITERIA_MISSING", {i["code"] for i in out["issues"]})


class T3_ConflictAndNeedsReview(unittest.TestCase):
    """Agent 5 keeps uncertainty visible: needs_review claims flagged; conflicting sources not overwritten."""
    def test_needs_review_claims(self):
        out = agent_5.handle(req("agent_5", "verify_resources", {"programs_to_check": [{"program_id": CALFRESH, "field_paths": ["eligibility_criteria", "deadlines"]}], "evidence_refs": [], "relevant_case_constraints": []}))
        by = {c["field_path"]: c for c in out["result"]["checked_claims"]}
        self.assertEqual(by["eligibility_criteria[7]"]["verification_status"], "needs_review")   # income limits
        self.assertEqual(by["eligibility_criteria[18]"]["verification_status"], "needs_review")  # SAR 7 'RCA' wording
        self.assertEqual(by["eligibility_criteria[17]"]["verification_status"], "verified")      # SAR 7 due by the 5th
        self.assertEqual(by["deadlines"]["verification_status"], "unverified")  # no published value: empty, not guessed
        self.assertIsNone(by["deadlines"]["claim_value"])
        self.assertTrue(out["result"]["unresolved_questions"])
        self.assertEqual(out["result"]["update_proposals"], [])  # Agent 5 never edits the KB

    def test_conflicting_sources_kept(self):
        # TEST FIXTURE ONLY - synthetic program, not a real KB record
        kb = {"program_records": [{"program_id": "prog_test_fixture_001"}], "evidence_records": [
            {"evidence_id": "ev_t1", "program_id": "prog_test_fixture_001", "field_path": "deadlines[0]", "claim_value": "Nov 15", "source_url": "https://example.gov/a", "checked_at": "2026-10-22T10:00:00-07:00", "verification_status": "verified"},
            {"evidence_id": "ev_t2", "program_id": "prog_test_fixture_001", "field_path": "deadlines[0]", "claim_value": "Nov 30", "source_url": "https://example.org/b", "checked_at": "2026-10-22T10:05:00-07:00", "verification_status": "verified"}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(kb, f)
        try:
            out = agent_5.handle(req("agent_5", "verify_resources", {"programs_to_check": [{"program_id": "prog_test_fixture_001", "field_paths": ["deadlines"]}]}), kb_path=f.name)
        finally:
            os.unlink(f.name)
        c = out["result"]["checked_claims"][0]
        self.assertEqual(c["verification_status"], "conflicting")
        self.assertEqual(set(c["evidence_refs"]), {"ev_t1", "ev_t2"})


class T4_BadInput(unittest.TestCase):
    """Missing payload fields -> status failed with an issue, result {} (Supervisor check S6)."""
    def test_failed(self):
        for mod, aid, task in ((agent_3, "agent_3", "retrieve_candidates"), (agent_4, "agent_4", "match_resources"), (agent_5, "agent_5", "verify_resources")):
            r = req(aid, task, {}); out = mod.handle(r); check_envelope(self, r, out, aid)
            self.assertEqual(out["status"], "failed"); self.assertEqual(out["result"], {})
            self.assertEqual(out["issues"][0]["code"], "INPUT_INCOMPLETE")


class T5_ClosedProgram(unittest.TestCase):
    """Saint John's is temporarily_closed (October funds exhausted). Retrieval still returns it (Agent 3 does not
    judge availability); Agent 5 reports the closure evidence and the reopening date."""
    def test_closed_program_evidence_visible(self):
        self.assertIn(SJ, {c["program_id"] for c in retrieve()["result"]["candidate_programs"]})
        out = agent_5.handle(req("agent_5", "verify_resources", {"programs_to_check": [{"program_id": SJ, "field_paths": ["availability", "application_method"]}], "evidence_refs": [], "relevant_case_constraints": []}))
        by = {c["field_path"]: c for c in out["result"]["checked_claims"]}
        from navigator.agents.agent_3_4_5.common import load_kb
        state = {pr["program_id"]: pr["availability"] for pr in load_kb()[0]}[SJ]
        if state == "temporarily_closed":   # October state
            self.assertIn("exhausted", by["availability"]["claim_value"])
            # Slav, Oct 25: the reopening date travels with the closure (own availability row + effective_date)
            self.assertEqual(by["availability"]["verification_status"], "verified")  # same page: complementary, not conflicting
            self.assertEqual(set(by["availability"]["evidence_refs"]), {"ev_sjhap_019", "ev_sjhap_022"})
            kb_ev = {e["evidence_id"]: e for e in load_kb()[1]}
            self.assertEqual(kb_ev["ev_sjhap_022"]["effective_date"], "2026-11-02")
            self.assertIn("November 2nd", kb_ev["ev_sjhap_022"]["claim_value"])
        else:                               # after the Nov 2 publish
            self.assertEqual(state, "confirmed_open"); self.assertIn("APPLY HERE", by["availability"]["claim_value"])
            self.assertEqual({e["evidence_id"]: e for e in load_kb()[1]}["ev_sjhap_021"]["effective_date"], "2026-11-02")
            self.assertIn("wkf.ms", by["application_method[0]"]["claim_value"])  # online form link appeared Nov 2
            return
        self.assertEqual(by["application_method[1]"]["verification_status"], "verified")  # 'February' resolved Oct 25


class T6_GeographyAndCategories(unittest.TestCase):
    def test_statewide_program_covers_any_california_county_only(self):
        income = [NEEDS[0]]
        self.assertEqual([c["program_id"] for c in retrieve(income, ["Alameda County"])["result"]["candidate_programs"]], [UI])
        self.assertEqual(retrieve(income, ["Washoe County"])["result"]["candidate_programs"], [])  # Nevada

    def test_zip_only_still_works_locally(self):
        # 11 programs in KB as of Nov 12, 2026 (4 original + 7 new food/housing records)
        self.assertEqual(len(retrieve(geography=["95823"])["result"]["candidate_programs"]), 11)

    def test_subcategory_orders_but_does_not_filter(self):
        ids = [c["program_id"] for c in retrieve([NEEDS[1]])["result"]["candidate_programs"]]
        # rental_assistance subcategory programs come before eviction_prevention; CAS is still shown.
        # Nov 12 adds prog_housing_salvationarmy_rent_sac_001 and prog_housing_lsnc_sac_001.
        self.assertIn(SJ, ids, "Saint John's (rental_assistance) must be in results")
        self.assertIn(CAS, ids, "Coordinated Access (eviction_prevention) must be in results")
        # SJ must appear before CAS (subcategory rental_assistance sorts first)
        self.assertLess(ids.index(SJ), ids.index(CAS), "rental_assistance programs must come before CAS")

    def test_other_unlisted_is_coverage_gap(self):
        out = retrieve([{"need_id": "need_009", "category": "other_unlisted", "subcategory": None, "description": "x", "urgency": "unknown"}])
        self.assertEqual(out["result"]["candidate_programs"], [])
        self.assertEqual(out["issues"][0]["code"], "COVERAGE_GAP")


class T7_InputErrors(unittest.TestCase):
    """Slav's Oct 25 edge cases: input errors are reported as errors, never as gaps or incomplete data."""
    def test_1_unknown_category_is_input_error_not_gap(self):
        out = retrieve([{"need_id": "need_002", "category": "housing", "subcategory": None, "description": "Rent", "urgency": "high"}])
        codes = {i["code"] for i in out["issues"]}
        self.assertIn("UNKNOWN_CATEGORY", codes); self.assertNotIn("COVERAGE_GAP", codes)
        self.assertEqual(out["status"], "failed")  # the only need was invalid
        mixed = retrieve([NEEDS[2], {"need_id": "need_009", "category": "housing", "subcategory": None, "description": "Rent", "urgency": "high"}])
        self.assertEqual(mixed["status"], "partial")  # valid need still processed
        # All food programs for Sacramento County must be returned; invalid housing need is skipped.
        pids = {c["program_id"] for c in mixed["result"]["candidate_programs"]}
        self.assertIn(CALFRESH, pids, "CalFresh must be in food results")
        # Every returned program must have matched only food_assistance (the valid need_003)
        for c in mixed["result"]["candidate_programs"]:
            self.assertEqual(c["matched_need_ids"], ["need_003"], f"{c['program_id']} must match only need_003")

    def test_2_wrong_task_type_fails(self):
        for mod, aid, wrong in ((agent_3, "agent_3", "verify_resources"), (agent_4, "agent_4", "retrieve_candidates"), (agent_5, "agent_5", "match_resources")):
            r = req(aid, wrong, {"needs": NEEDS, "geography": GEO}); out = mod.handle(r); check_envelope(self, r, out, aid)
            self.assertEqual(out["status"], "failed"); self.assertEqual(out["result"], {})
            self.assertEqual(out["issues"][0]["code"], "UNSUPPORTED_TASK")

    def test_3_unknown_program_is_not_unverified(self):
        out = agent_5.handle(req("agent_5", "verify_resources", {"programs_to_check": [{"program_id": "prog_invented_999", "field_paths": ["deadlines"]}]}))
        self.assertEqual(out["status"], "failed")
        self.assertEqual(out["issues"][0]["code"], "UNKNOWN_PROGRAM")
        mixed = agent_5.handle(req("agent_5", "verify_resources", {"programs_to_check": [
            {"program_id": "prog_invented_999", "field_paths": ["deadlines"]}, {"program_id": CALFRESH, "field_paths": ["deadlines"]}]}))
        self.assertEqual(mixed["status"], "partial")
        self.assertEqual({c["program_id"] for c in mixed["result"]["checked_claims"]}, {CALFRESH})

    def test_4_zip_fallback_warns(self):
        out = retrieve(geography=["95823"])
        warn = [i for i in out["issues"] if i["code"] == "COUNTY_FROM_ZIP_FALLBACK"]
        self.assertEqual(len(warn), 1); self.assertEqual(warn[0]["severity"], "warning")
        self.assertFalse([i for i in retrieve(geography=GEO)["issues"] if i["code"] == "COUNTY_FROM_ZIP_FALLBACK"])  # county given


class T8_SamePageRule(unittest.TestCase):
    """Slav, Nov 2: on ONE page, dated statements are complementary; two values for the same field are conflicting."""
    def run5(self, rows):
        kb = {"program_records": [{"program_id": "prog_test_fixture_002"}], "evidence_records": rows}  # TEST FIXTURE ONLY
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(kb, f)
        try:
            return agent_5.handle(req("agent_5", "verify_resources", {"programs_to_check": [{"program_id": "prog_test_fixture_002", "field_paths": ["availability"]}]}), kb_path=f.name)["result"]["checked_claims"]
        finally:
            os.unlink(f.name)

    def row(self, eid, val, eff):
        return {"evidence_id": eid, "program_id": "prog_test_fixture_002", "field_path": "availability", "claim_value": val,
                "source_url": "https://example.org/one-page", "checked_at": "2026-11-02T09:00:00-08:00", "verification_status": "verified", "effective_date": eff}

    def test_closed_now_reopens_later_is_complementary(self):
        claims = self.run5([self.row("ev_a", "Funds for October are exhausted.", None), self.row("ev_b", "Applications reopen Monday, November 2nd.", "2026-11-02")])
        # v1.6 (Julia 5.3): each dated statement stays its own claim; no combined "current" value
        self.assertEqual([c["evidence_refs"] for c in claims], [["ev_a"], ["ev_b"]])
        self.assertTrue(all(c["verification_status"] == "verified" for c in claims))
        self.assertTrue(all("|" not in c["claim_value"] for c in claims))

    def test_two_values_same_field_same_page_is_conflicting(self):
        c = self.run5([self.row("ev_c", "Income documents: last 30 days.", None), self.row("ev_d", "Income documents: last 60 days.", None)])[0]
        self.assertEqual(c["verification_status"], "conflicting")
        self.assertIsNone(c["claim_value"])


class T9_AuditFixes(unittest.TestCase):
    """Julia's technical review of Agents 3-5 (Nov 3): baseline fixes, one test per finding.
    Program criteria below are TEST FIXTURES, not real KB programs."""
    PID = "prog_test_fixture_003"

    def m4(self, criteria, facts):
        crit = [{"program_id": self.PID, "field_path": "geography[0]", "value": "Sacramento County", "evidence_refs": ["ev_x"]}]
        crit += [{"program_id": self.PID, "field_path": f"eligibility_criteria[{i}]", "value": v, "evidence_refs": [f"ev_{i}"]}
                 for i, v in enumerate(criteria)]
        out = agent_4.handle(req("agent_4", "match_resources", {"candidate_programs": [{"program_id": self.PID, "matched_need_ids": ["need_001"]}],
                                                                  "case_facts": facts, "needs": NEEDS, "program_criteria": crit}))
        return out, out["result"]["matches"][0]

    CONFIRMED = [{"fact_id": "f1", "field": "county", "value": "Sacramento County", "confirmation_status": "confirmed"},
                 {"fact_id": "f2", "field": "household_size", "value": 4, "confirmation_status": "confirmed"}]
    INCOME = [{"fact_id": "f3", "field": "household_gross_monthly_income", "value": 5000, "confirmation_status": "confirmed"}]

    # --- Agent 4 (scenarios A-F from the review)
    def test_A_income_present_is_not_a_match_against_the_limit(self):
        out, m = self.m4(["Gross monthly income at or below $3,000 for a household of 4."], self.CONFIRMED + self.INCOME)
        self.assertEqual(m["match_status"], "potential_match")
        self.assertIn("CRITERIA_NOT_EVALUATED", {i["code"] for i in out["issues"]})

    def test_B_income_required_but_unknown_is_reported(self):
        out, m = self.m4(["Household income within HUD low-income guidelines."], self.CONFIRMED)
        self.assertIn("household_gross_monthly_income", m["missing_case_facts"])
        self.assertNotEqual(m["match_status"], "confirmed_mismatch")

    def test_C_income_not_relevant_does_not_downgrade(self):
        out, m = self.m4([], self.CONFIRMED)
        self.assertNotIn("household_gross_monthly_income", m["missing_case_facts"])
        self.assertEqual(m["match_status"], "supported_match")  # nothing left unevaluated
        out, m = self.m4(["Must live in Sacramento County for six months."], self.CONFIRMED)
        self.assertNotIn("household_gross_monthly_income", m["missing_case_facts"])  # no income criterion

    def test_D_dependent_children_criterion_is_not_assumed(self):
        out, m = self.m4(["Household must include a child under 18."], self.CONFIRMED)
        self.assertEqual(m["match_status"], "potential_match")

    def test_E_crisis_specific_criterion_is_not_assumed(self):
        out, m = self.m4(["Applicant must have lost a family member (bereavement)."], self.CONFIRMED)
        self.assertEqual(m["match_status"], "potential_match")
        self.assertIn("eligibility_criteria[0]", out["issues"][-1]["message"])

    def test_F_geography_ok_but_other_criterion_unproven(self):
        out, m = self.m4(["Valid lease required.", "Income below the limit."], self.CONFIRMED + self.INCOME)
        self.assertEqual(m["match_status"], "potential_match")
        self.assertIn("2 program criteria not yet evaluated", m["explanation"])

    # --- Agent 3
    def test_3_1_truncation_is_reported(self):
        r = req("agent_3", "retrieve_candidates", {"needs": [NEEDS[1]], "geography": GEO, "max_candidates": 1})
        out = agent_3.handle(r)
        self.assertEqual([c["program_id"] for c in out["result"]["candidate_programs"]], [SJ])  # ordering policy
        self.assertIn("CANDIDATES_TRUNCATED", {i["code"] for i in out["issues"]})
        # housing_assistance now has 4 programs (Nov 12); only 1 returned with max_candidates=1
        note = out["result"]["retrieval_notes"][0]
        self.assertIn("4 candidate(s) found, 1 returned", note)
        self.assertIn("CANDIDATES_TRUNCATED", {i["code"] for i in out["issues"]})

    def test_3_2_unknown_geography_is_not_a_coverage_gap(self):
        out = retrieve(geography=["90210"])
        codes = {i["code"] for i in out["issues"]}
        self.assertIn("GEOGRAPHY_UNRESOLVED", codes)
        self.assertNotIn("COVERAGE_GAP", codes)
        self.assertEqual(out["status"], "partial")

    def test_3_3_malformed_payload_is_a_structured_error(self):
        for bad in ({"needs": [{"category": "food_assistance"}], "geography": GEO},
                    {"needs": "food", "geography": GEO},
                    {"needs": NEEDS, "geography": GEO, "max_candidates": 0}):
            out = agent_3.handle(req("agent_3", "retrieve_candidates", bad))
            self.assertEqual(out["status"], "failed")
            self.assertEqual(out["issues"][0]["code"], "INPUT_INVALID")

    # --- Agent 5
    def test_5_1_missing_evidence_is_an_unresolved_question(self):
        out = agent_5.handle(req("agent_5", "verify_resources", {"programs_to_check": [{"program_id": CALFRESH, "field_paths": ["deadlines"]}]}))
        self.assertTrue(any("deadlines" in q for q in out["result"]["unresolved_questions"]))
        self.assertIn("EVIDENCE_MISSING", {i["code"] for i in out["issues"]})


class T10_EvidenceMissingNamesProgram(unittest.TestCase):
    """EVIDENCE_MISSING issues must name the program they belong to (related_ref and message)."""

    def _run5(self, kb, pids_and_fields):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(kb, f)
        try:
            return agent_5.handle(req("agent_5", "verify_resources",
                                      {"programs_to_check": [{"program_id": pid, "field_paths": fields}
                                                              for pid, fields in pids_and_fields]}),
                                  kb_path=f.name)
        finally:
            os.unlink(f.name)

    def test_each_evidence_missing_names_its_own_program(self):
        """Two programs, both missing 'deadlines' evidence: each EVIDENCE_MISSING issue names its own program."""
        kb = {
            "program_records": [
                {"program_id": "prog_fix_010"},
                {"program_id": "prog_fix_011"},
            ],
            "evidence_records": [],
        }
        out = self._run5(kb, [("prog_fix_010", ["deadlines"]), ("prog_fix_011", ["deadlines"])])
        em_issues = [i for i in out["issues"] if i["code"] == "EVIDENCE_MISSING"]
        self.assertEqual(len(em_issues), 2, f"Expected 2 EVIDENCE_MISSING issues, got {len(em_issues)}")
        refs = {i["related_ref"] for i in em_issues}
        self.assertEqual(refs, {"prog_fix_010", "prog_fix_011"})
        for i in em_issues:
            self.assertIn(i["related_ref"], i["message"],
                          f"program_id '{i['related_ref']}' must appear in message: {i['message']!r}")


RCMID = "prog_food_rivercity_midtown_sac_001"
RCARDEN = "prog_food_rivercity_arden_sac_001"
SAPANTRY = "prog_food_salvationarmy_pantry_sac_001"
SARENT = "prog_housing_salvationarmy_rent_sac_001"
SFBFS = "prog_food_sfbfs_foodfinder_sac_001"
EGFB = "prog_food_elkgrove_foodbank_sac_001"
LSNC = "prog_housing_lsnc_sac_001"

FOOD_NEED = {"need_id": "need_f01", "category": "food_assistance", "subcategory": None,
             "description": "Need food", "urgency": "high"}


class T11_EddReducedHours(unittest.TestCase):
    """Agent 4 rule: employment_status=reduced_hours (partially unemployed) must never produce a mismatch
    for EDD Unemployment Insurance. EDD explicitly covers partial unemployment; unknown employment status is
    not a mismatch reason. (Silver, Nov 12, 2026)"""

    def test_reduced_hours_is_potential_match_not_mismatch(self):
        """A case with employment_status=reduced_hours and a confirmed Sacramento County location
        must return potential_match for EDD UI, never confirmed_mismatch."""
        cand = [{"program_id": UI, "matched_need_ids": ["need_001"]}]
        facts = [
            {"fact_id": "f_loc", "field": "county", "value": "Sacramento County",
             "confirmation_status": "confirmed"},
            {"fact_id": "f_emp", "field": "employment_status", "value": "reduced_hours",
             "confirmation_status": "confirmed"},
        ]
        m = match(cand, facts)["result"]["matches"][0]
        self.assertNotEqual(m["match_status"], "confirmed_mismatch",
                            "reduced_hours (partially unemployed) must not be a mismatch for EDD UI")
        self.assertIn(m["match_status"], {"potential_match", "supported_match"},
                      "reduced_hours must yield potential_match or better for EDD UI")


class T12_Nov12Programs(unittest.TestCase):
    """Tests for the Nov 12, 2026 KB additions: food pantries, Salvation Army rent help,
    River City conflicting Nov 20 availability. (Silver, Nov 12, 2026)"""

    def test_zip_95660_food_need_returns_food_pantry_programs(self):
        """ZIP 95660 (North Highlands, Sacramento County) + food need must return the food pantry programs."""
        food_need = [FOOD_NEED]
        out = retrieve(food_need, geography=["95660"])
        pids = {c["program_id"] for c in out["result"]["candidate_programs"]}
        # All six food programs serve Sacramento County; 95660 maps to Sacramento County via ZIP fallback.
        for expected in (CALFRESH, RCMID, RCARDEN, SAPANTRY, SFBFS, EGFB):
            self.assertIn(expected, pids,
                          f"ZIP 95660 + food need should return {expected}")

    def test_salvation_army_rent_help_stays_potential_match_eviction_unknown(self):
        """Salvation Army rent help must stay potential_match when has_written_eviction_notice is unknown.
        The KB note on eligibility_criteria[1] says: if unknown, keep potential_match, never a mismatch."""
        cand = [{"program_id": SARENT, "matched_need_ids": ["need_002"]}]
        facts = [
            {"fact_id": "f_loc", "field": "county", "value": "Sacramento County",
             "confirmation_status": "confirmed"},
            # has_written_eviction_notice is intentionally absent (unknown)
        ]
        m = match(cand, facts)["result"]["matches"][0]
        self.assertNotEqual(m["match_status"], "confirmed_mismatch",
                            "Unknown eviction notice must never be a mismatch for Salvation Army rent help")
        self.assertIn(m["match_status"], {"potential_match", "supported_match"})

    def test_river_city_nov20_availability_is_conflicting(self):
        """Nov 20 availability for both River City sites must stay conflicting in Agent 5.
        The distribution page and holiday banner conflict with the calendar PDF."""
        for pid, ev_id in ((RCMID, "ev_rcfbmt_014"), (RCARDEN, "ev_rcfbar_014")):
            out = agent_5.handle(req("agent_5", "verify_resources",
                                    {"programs_to_check": [{"program_id": pid, "field_paths": ["availability"]}],
                                     "evidence_refs": [], "relevant_case_constraints": []}))
            conflicting = [c for c in out["result"]["checked_claims"]
                           if c.get("verification_status") == "conflicting"]
            self.assertTrue(conflicting,
                            f"{pid}: expected at least one conflicting availability claim (Nov 20)")
            ev_ids = {ev for c in conflicting for ev in c.get("evidence_refs", [])}
            self.assertIn(ev_id, ev_ids,
                          f"{pid}: {ev_id} must be among the conflicting evidence refs")


if __name__ == "__main__":
    unittest.main()
