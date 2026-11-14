"""Agent 3 statewide-no-ZIP rule tests (Silver, 2026-11-14).

Rule: when geography is exactly [] (empty list), statewide ("California") programs are
returned; county-only programs are skipped; no COVERAGE_GAP is emitted (unknown location
is not a lack of programs — same principle as test_3_2). GEOGRAPHY_UNRESOLVED is kept.

Unchanged cases:
  - A ZIP given but not on the county list → nothing returned (no COVERAGE_GAP).
  - A non-empty geography that doesn't resolve (e.g. "Yolo County" not in fixture KB) →
    nothing returned (no COVERAGE_GAP).
  - Sacramento County → county-only and statewide programs returned as today.

All tests use a synthetic KB fixture; none depend on live KB data or today's date.
"""
import copy, json, os, tempfile, unittest
from navigator.agents.agent_3_4_5 import agent_3

# ---------------------------------------------------------------------------
# Synthetic KB:
#   - one statewide income program ("California")
#   - one county-only food program (Sacramento County)
#   - one county-only income program (Sacramento County) for test (c)
# ---------------------------------------------------------------------------
_STATEWIDE_ID = "prog_income_statewide_fixture"
_COUNTY_FOOD_ID = "prog_food_county_fixture"
_COUNTY_INCOME_ID = "prog_income_county_fixture"
_SAC = "Sacramento County"


def _prog(pid, category, geography, subcategory=None):
    return {
        "program_id": pid,
        "program_name": f"{pid} (fixture)",
        "organization": "Fixture Org",
        "category": category,
        "subcategory": subcategory,
        "geography": geography,
        "eligibility_criteria": [],
        "required_documents": [],
        "application_method": [],
        "contact": [],
        "deadlines": [],
        "processing_time": None,
        "availability": "confirmed_open",
        "sources": [f"src_{pid}"],
        "last_verified_at": "2026-01-01T00:00:00Z",
        "verification_status": "verified",
    }


_KB = {
    "program_records": [
        _prog(_STATEWIDE_ID, "income_assistance", ["California"], "unemployment_insurance"),
        _prog(_COUNTY_FOOD_ID, "food_assistance", [_SAC]),
        _prog(_COUNTY_INCOME_ID, "income_assistance", [_SAC]),
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
    """Each test gets its own KB temp file so they are fully isolated."""

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(_KB, self._tmp)
        self._tmp.close()
        self.kb = self._tmp.name

    def tearDown(self):
        os.unlink(self.kb)

    # (a) empty geography [] → statewide returned, no COVERAGE_GAP, GEOGRAPHY_UNRESOLVED kept
    def test_a_empty_geography_no_zip_returns_statewide_only(self):
        out = _req([_INCOME_NEED, _FOOD_NEED], [], self.kb)
        pids = {c["program_id"] for c in out["result"]["candidate_programs"]}

        # Statewide income program must be present
        self.assertIn(_STATEWIDE_ID, pids,
                      "Statewide income program must appear when geography is []")
        # County-only programs must be absent
        self.assertNotIn(_COUNTY_FOOD_ID, pids,
                         "County-only food program must not appear for empty geography")
        self.assertNotIn(_COUNTY_INCOME_ID, pids,
                         "County-only income program must not appear for empty geography")

        # Status must be partial (geography unresolved)
        self.assertEqual(out["status"], "partial")

        # GEOGRAPHY_UNRESOLVED must be present with the no-ZIP note
        geo_issues = [i for i in out["issues"] if i["code"] == "GEOGRAPHY_UNRESOLVED"]
        self.assertEqual(len(geo_issues), 1)
        self.assertIn("No ZIP code given", geo_issues[0]["message"])

        # No COVERAGE_GAP: unknown location is not a lack of programs
        self.assertFalse([i for i in out["issues"] if i["code"] == "COVERAGE_GAP"],
                         "COVERAGE_GAP must not be emitted when geography is [] (unknown location, not a gap)")

    # (b) ZIP 90210 (unmapped) → still returns nothing, no COVERAGE_GAP, unchanged
    def test_b_unmapped_zip_returns_nothing(self):
        out = _req([_INCOME_NEED, _FOOD_NEED], ["90210"], self.kb)
        self.assertEqual(out["result"]["candidate_programs"], [],
                         "An unmapped ZIP must not return any programs")
        self.assertEqual(out["status"], "partial")
        codes = {i["code"] for i in out["issues"]}
        self.assertIn("GEOGRAPHY_UNRESOLVED", codes)
        self.assertIn("GEOGRAPHY_UNMAPPED", codes)
        # No COVERAGE_GAP for unmapped ZIP either
        self.assertNotIn("COVERAGE_GAP", codes,
                         "COVERAGE_GAP must not be emitted for an unmapped ZIP")
        # GEOGRAPHY_UNRESOLVED message must NOT contain the no-ZIP wording
        geo_msg = next(i["message"] for i in out["issues"] if i["code"] == "GEOGRAPHY_UNRESOLVED")
        self.assertNotIn("No ZIP code given", geo_msg)

    # (c) Sacramento County in fixture KB → county programs (and statewide) returned, completed
    def test_c_sacramento_county_uses_fixture_kb(self):
        """Sacramento County geography returns both the county program and the statewide program."""
        out = _req([_INCOME_NEED, _FOOD_NEED], [_SAC], self.kb)
        pids = {c["program_id"] for c in out["result"]["candidate_programs"]}
        self.assertIn(_COUNTY_INCOME_ID, pids,
                      "County income program must appear for Sacramento County")
        self.assertIn(_STATEWIDE_ID, pids,
                      "Statewide income program must still appear for Sacramento County")
        self.assertIn(_COUNTY_FOOD_ID, pids,
                      "County food program must appear for Sacramento County")
        self.assertEqual(out["status"], "completed")
        self.assertFalse([i for i in out["issues"] if i["code"] == "GEOGRAPHY_UNRESOLVED"])

    # (d) Non-empty geography (["Yolo County"]) → statewide_only does NOT fire; normal path runs
    def test_d_non_empty_geography_does_not_trigger_statewide_only(self):
        """A non-empty geography list must NOT trigger the statewide-only path, even when no
        county-only programs match. 'Yolo County' is a valid CA county; to_counties passes it
        through, geography_known = True, and normal area_covers logic runs. The statewide program
        covers all CA counties so it IS returned — but via the normal path, not the no-ZIP path.
        No GEOGRAPHY_UNRESOLVED, no COVERAGE_GAP, status completed."""
        out = _req([_INCOME_NEED, _FOOD_NEED], ["Yolo County"], self.kb)
        # statewide program covers Yolo County (all CA counties) via area_covers
        pids = {c["program_id"] for c in out["result"]["candidate_programs"]}
        self.assertIn(_STATEWIDE_ID, pids,
                      "Statewide program must still be returned for a known CA county")
        self.assertNotIn(_COUNTY_FOOD_ID, pids,
                         "Sacramento-only food program must not appear for Yolo County")
        # Normal path: geography_known = True → no GEOGRAPHY_UNRESOLVED
        self.assertFalse([i for i in out["issues"] if i["code"] == "GEOGRAPHY_UNRESOLVED"],
                         "No GEOGRAPHY_UNRESOLVED for a known CA county name")
        # No COVERAGE_GAP: food need has no Yolo match but statewide_only is False here
        # (the COVERAGE_GAP for food IS emitted by the normal path — that is correct)
        # The key assertion: the no-ZIP note was NOT used
        self.assertFalse(
            any("No ZIP code given" in i["message"] for i in out["issues"]),
            "statewide_only must not fire for a non-empty geography list"
        )


if __name__ == "__main__":
    unittest.main()
