"""Agent 3 statewide-no-ZIP rule tests (Silver, 2026-11-14).

Rule: when geography is [] AND no ZIP was given, return only statewide programs ("California");
county-only programs stay out; GEOGRAPHY_UNRESOLVED is kept.
Unchanged: a ZIP given but not on the county list → still returns nothing.
Unchanged: Sacramento County → same as the existing shared test.

These tests use a synthetic KB fixture so they do not depend on live KB data or today's date.
"""
import copy, json, os, tempfile, unittest
from navigator.agents.agent_3_4_5 import agent_3

# ---------------------------------------------------------------------------
# Minimal synthetic KB: one statewide income program, one county-only food
# program. Geography is deterministic; no dates, no availability logic needed.
# ---------------------------------------------------------------------------
_STATEWIDE_ID = "prog_income_edd_ui_ca_001_fixture"
_COUNTY_ID = "prog_food_county_only_fixture"
_SAC_GEO = "Sacramento County"

_KB = {
    "program_records": [
        {
            "program_id": _STATEWIDE_ID,
            "program_name": "Statewide Income Program (fixture)",
            "organization": "Fixture Org",
            "category": "income_assistance",
            "subcategory": "unemployment_insurance",
            "geography": ["California"],
            "eligibility_criteria": [],
            "required_documents": [],
            "application_method": [],
            "contact": [],
            "deadlines": [],
            "processing_time": None,
            "availability": "confirmed_open",
            "sources": ["src_fixture_01"],
            "last_verified_at": "2026-01-01T00:00:00Z",
            "verification_status": "verified",
        },
        {
            "program_id": _COUNTY_ID,
            "program_name": "County Food Program (fixture)",
            "organization": "Fixture Org",
            "category": "food_assistance",
            "subcategory": None,
            "geography": [_SAC_GEO],
            "eligibility_criteria": [],
            "required_documents": [],
            "application_method": [],
            "contact": [],
            "deadlines": [],
            "processing_time": None,
            "availability": "confirmed_open",
            "sources": ["src_fixture_02"],
            "last_verified_at": "2026-01-01T00:00:00Z",
            "verification_status": "verified",
        },
    ],
    "evidence_records": [],
}

_BASE = {
    "request_id": "req-statewide-t", "run_id": "run-statewide-t",
    "case_id": "case-statewide-t", "case_version": 1,
    "correlation_id": "corr-statewide-t", "schema_version": "1.0",
    "allowed_case_facts": [], "upstream_result_refs": [],
    "role_id": "agent_3", "task_type": "retrieve_candidates",
}

_INCOME_NEED = {"need_id": "need_i01", "category": "income_assistance", "subcategory": None,
                "description": "Lost job", "urgency": "high"}
_FOOD_NEED = {"need_id": "need_f01", "category": "food_assistance", "subcategory": None,
              "description": "Need food", "urgency": "high"}


def _req(needs, geography, kb_path):
    r = copy.deepcopy(_BASE)
    r["payload"] = {"needs": needs, "geography": geography, "retrieval_constraints": []}
    return agent_3.handle(r, kb_path=kb_path)


class TestStatewideNoZip(unittest.TestCase):
    """Tests are isolated: each creates its own KB temp file."""

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(_KB, self._tmp)
        self._tmp.close()
        self.kb = self._tmp.name

    def tearDown(self):
        os.unlink(self.kb)

    # (a) empty geography, no ZIP → statewide program returned, GEOGRAPHY_UNRESOLVED kept
    def test_a_empty_geography_no_zip_returns_statewide_only(self):
        out = _req([_INCOME_NEED, _FOOD_NEED], [], self.kb)
        pids = {c["program_id"] for c in out["result"]["candidate_programs"]}
        # Statewide income program must be present
        self.assertIn(_STATEWIDE_ID, pids,
                      "Statewide income program must appear when geography is empty and no ZIP given")
        # County-only food program must be absent
        self.assertNotIn(_COUNTY_ID, pids,
                         "County-only food program must not appear when no ZIP/county given")
        # Status must be partial (geography unresolved)
        self.assertEqual(out["status"], "partial")
        # GEOGRAPHY_UNRESOLVED must be present with the no-ZIP note
        geo_issues = [i for i in out["issues"] if i["code"] == "GEOGRAPHY_UNRESOLVED"]
        self.assertEqual(len(geo_issues), 1)
        self.assertIn("No ZIP code given", geo_issues[0]["message"])

    # (b) ZIP 90210 → still returns nothing (unchanged)
    def test_b_unmapped_zip_returns_nothing(self):
        out = _req([_INCOME_NEED, _FOOD_NEED], ["90210"], self.kb)
        self.assertEqual(out["result"]["candidate_programs"], [],
                         "An unmapped ZIP must not return any programs")
        self.assertEqual(out["status"], "partial")
        codes = {i["code"] for i in out["issues"]}
        self.assertIn("GEOGRAPHY_UNRESOLVED", codes)
        self.assertIn("GEOGRAPHY_UNMAPPED", codes)
        # GEOGRAPHY_UNRESOLVED message must NOT contain the no-ZIP wording
        geo_msg = next(i["message"] for i in out["issues"] if i["code"] == "GEOGRAPHY_UNRESOLVED")
        self.assertNotIn("No ZIP code given", geo_msg)

    # (c) Sacramento County → same as today (uses real KB via default path)
    def test_c_sacramento_county_uses_real_kb(self):
        """Sacramento County geography returns programs from the real KB unchanged."""
        r = copy.deepcopy(_BASE)
        r["payload"] = {
            "needs": [_INCOME_NEED],
            "geography": ["Sacramento County"],
            "retrieval_constraints": [],
        }
        # No kb_path → uses the real KB
        out = agent_3.handle(r)
        pids = {c["program_id"] for c in out["result"]["candidate_programs"]}
        self.assertIn("prog_income_edd_ui_ca_001", pids,
                      "EDD UI must still appear for Sacramento County (real KB)")
        self.assertEqual(out["status"], "completed")
        self.assertFalse([i for i in out["issues"] if i["code"] == "GEOGRAPHY_UNRESOLVED"])


if __name__ == "__main__":
    unittest.main()
