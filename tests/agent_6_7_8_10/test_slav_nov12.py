"""
Hisham — Slav Nov 12 test suite.
Tests for:
  Fix 1: Q8 false warning (scenario C, no Q8 at matching stage without coverage_gaps)
  Fix 2: Lockout detection — police contacts, housing card sentence, no-legal-aid gap note
  Fix 3: Pantry closures — River City Food Bank closure uncertainty notes
  Fix 4: contacts[] label normalization (Address, Hours)
  Agent 10 passes lockout and closure plans with no flags

All tests use fixtures and ref_date 2026-11-13. No live KB, no system date.
"""
import copy
import os
import sys
import unittest

# Ensure repo root is on the path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import navigator.agents.agent_6_7_8_10.agent_6_7_8_10 as agent_mod
from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import (
    handle,
    TASK_TYPES,
    _build_contacts,
    _closure_rows_for_card,
    _police_contacts_from_directory,
    _contact_label,
)

REF_DATE = "2026-11-13"

# ---------------------------------------------------------------------------
# Small fixture helpers
# ---------------------------------------------------------------------------

def _base_req(role, payload, case_id="case-nov12", n=1):
    return {
        "request_id": f"req_nov12_{n:02d}",
        "run_id": "run-nov12",
        "case_id": case_id,
        "case_version": 1,
        "schema_version": "1.0",
        "role_id": role,
        "task_type": TASK_TYPES[role],
        "task_scope": "all_needs",
        "upstream_result_refs": [],
        "source_policy": "verified_kb_only",
        "correlation_id": "corr-nov12",
        "allowed_case_facts": [],
        "payload": payload,
    }


def _need(need_id, category, subcategory=None, description="x", original_quote=None,
          urgency="high"):
    return {
        "need_id": need_id,
        "category": category,
        "subcategory": subcategory,
        "description": description,
        "original_quote": original_quote,
        "confirmation_status": "confirmed",
        "user_reported": True,
        "urgency": urgency,
        "urgency_reason": None,
        "user_priority": None,
    }


def _match(program_id, need_ids, subcategory=None, match_status="supported_match",
           organization=None, program_name=None):
    m = {
        "program_id": program_id,
        "need_ids": need_ids,
        "match_status": match_status,
        "matched_criteria": [],
        "missing_case_facts": [],
        "mismatch_criteria": [],
        "evidence_refs": [],
    }
    if subcategory:
        m["subcategory"] = subcategory
    if organization:
        m["organization"] = organization
    if program_name:
        m["program_name"] = program_name
    return m


def _action(action_id, need_id, program_id, order_group="parallel", rationale="x"):
    return {
        "action_id": action_id,
        "need_id": need_id,
        "program_id": program_id,
        "suggested_priority": 1,
        "order_group": order_group,
        "rationale": rationale,
        "dependency_ids": [],
        "official_deadline": None,
        "user_target_date": None,
        "estimated_processing_time": None,
        "evidence_refs": [],
        "uncertainty_notes": [],
        "user_override_allowed": True,
    }


# ---------------------------------------------------------------------------
# Minimal police directory fixture (5 records: 4 verified, 1 not)
# Only the Sheriff has a verified availability row.
# ---------------------------------------------------------------------------

_POLICE_DIR_FIXTURE = {
    "schema_version": "1.0",
    "note": "fixture",
    "program_records": [
        {
            "program_id": "er_police_sacpd_001",
            "program_name": "Sacramento PD Non-Emergency",
            "organization": "Sacramento Police Department",
            "category": "emergency_crisis",
            "subcategory": "local_police_non_emergency",
            "geography": ["City of Sacramento"],
            "eligibility_criteria": [],
            "required_documents": [],
            "application_method": [],
            "contact": [{"value": "916-808-5471", "evidence_refs": ["ev_sacpd_001"],
                         "verification_status": "verified", "checked_at": "2026-11-12T10:30:00-08:00"}],
            "deadlines": [],
            "processing_time": None,
            "availability": "unknown",
            "sources": ["ev_sacpd_001", "ev_sacpd_002"],
            "last_verified_at": "2026-11-12T10:30:00-08:00",
            "verification_status": "verified",
        },
        {
            "program_id": "er_police_sheriff_001",
            "program_name": "Sacramento Sheriff Non-Emergency",
            "organization": "Sacramento County Sheriff's Office",
            "category": "emergency_crisis",
            "subcategory": "local_police_non_emergency",
            "geography": ["Sacramento County"],
            "eligibility_criteria": [],
            "required_documents": [],
            "application_method": [],
            "contact": [{"value": "916-874-5115", "evidence_refs": ["ev_sheriff_001"],
                         "verification_status": "verified", "checked_at": "2026-11-12T10:30:00-08:00"}],
            "deadlines": [],
            "processing_time": None,
            "availability": "confirmed_open",
            "sources": ["ev_sheriff_001", "ev_sheriff_002"],
            "last_verified_at": "2026-11-12T10:30:00-08:00",
            "verification_status": "verified",
        },
        # Unverified record — must NOT appear in output.
        {
            "program_id": "er_police_fake_001",
            "program_name": "Fake PD",
            "organization": "Fake Police",
            "category": "emergency_crisis",
            "subcategory": "local_police_non_emergency",
            "geography": ["Faketown"],
            "eligibility_criteria": [],
            "required_documents": [],
            "application_method": [],
            "contact": [{"value": "000-000-0000", "evidence_refs": [],
                         "verification_status": "unverified", "checked_at": "2026-11-12T10:30:00-08:00"}],
            "deadlines": [],
            "processing_time": None,
            "availability": "unknown",
            "sources": [],
            "last_verified_at": "2026-11-12T10:30:00-08:00",
            "verification_status": "unverified",  # NOT included
        },
    ],
    "evidence_records": [
        {"evidence_id": "ev_sacpd_001", "program_id": "er_police_sacpd_001",
         "field_path": "contact[0]", "claim_value": "916-808-5471",
         "source_url": "https://example.org/sacpd", "checked_at": "2026-11-12T10:30:00-08:00",
         "verification_status": "verified", "source_title": "SACPD", "source_authority_scope": "local_government",
         "effective_date": None, "notes": None},
        {"evidence_id": "ev_sacpd_002", "program_id": "er_police_sacpd_001",
         "field_path": "availability", "claim_value": "Hours not stated.",
         "source_url": "https://example.org/sacpd", "checked_at": "2026-11-12T10:30:00-08:00",
         "verification_status": "needs_review", "source_title": "SACPD", "source_authority_scope": "local_government",
         "effective_date": None, "notes": None},
        {"evidence_id": "ev_sheriff_001", "program_id": "er_police_sheriff_001",
         "field_path": "contact[0]", "claim_value": "916-874-5115",
         "source_url": "https://example.org/sheriff", "checked_at": "2026-11-12T10:30:00-08:00",
         "verification_status": "verified", "source_title": "Sheriff", "source_authority_scope": "local_government",
         "effective_date": None, "notes": None},
        {"evidence_id": "ev_sheriff_002", "program_id": "er_police_sheriff_001",
         "field_path": "availability", "claim_value": "24 hours/7 days",
         "source_url": "https://example.org/sheriff", "checked_at": "2026-11-12T10:30:00-08:00",
         "verification_status": "verified", "source_title": "Sheriff FAQ", "source_authority_scope": "local_government",
         "effective_date": None, "notes": None},
    ],
}

# ---------------------------------------------------------------------------
# River City Arden evidence_records fixture (the 6 availability rows from KB).
# _closure_rows_for_card now reads from evidence_records, not checked_claims.
# A single merged checked_claims item is provided to simulate Agent 5 output.
# ---------------------------------------------------------------------------

_RCFB_ARDEN_PROG = "prog_food_rivercity_arden_sac_001"

# The single merged checked_claims item that Agent 5 produces (conflicting, no date).
_RCFB_ARDEN_MERGED_CLAIM = {
    "program_id": _RCFB_ARDEN_PROG,
    "field_path": "availability",
    "claim_value": None,          # merged — no useful text
    "verification_status": "conflicting",
    "evidence_refs": ["ev_rcfbar_012", "ev_rcfbar_013", "ev_rcfbar_014",
                      "ev_rcfbar_015", "ev_rcfbar_016", "ev_rcfbar_017"],
    "checked_at": "2026-11-12T10:30:00-08:00",
    "issue": None,
}

# The 6 individual EvidenceRecord rows (copied from KB).
_RCFB_ARDEN_EV_RECORDS = [
    # General availability — no date, should be skipped.
    {"evidence_id": "ev_rcfbar_012", "program_id": _RCFB_ARDEN_PROG,
     "field_path": "availability",
     "claim_value": "These sites are open four days a week to provide healthy, nutritious food.",
     "source_url": "https://rivercityfoodbank.org/emergency-food-distribution/",
     "checked_at": "2026-11-12T10:30:00-08:00",
     "verification_status": "verified", "source_title": "RCFB",
     "source_authority_scope": "local_provider_operating_intake",
     "effective_date": None, "notes": None},
    # Nov 11 — past, skip.
    {"evidence_id": "ev_rcfbar_013", "program_id": _RCFB_ARDEN_PROG,
     "field_path": "availability",
     "claim_value": "November 11 - Veterans Day (closed)",
     "source_url": "https://rivercityfoodbank.org/emergency-food-distribution/",
     "checked_at": "2026-11-12T10:30:00-08:00",
     "verification_status": "verified", "source_title": "RCFB",
     "source_authority_scope": "local_provider_operating_intake",
     "effective_date": "2026-11-11", "notes": None},
    # Nov 20 — conflicting.
    {"evidence_id": "ev_rcfbar_014", "program_id": _RCFB_ARDEN_PROG,
     "field_path": "availability",
     "claim_value": "November 20 - Closed",
     "source_url": "https://rivercityfoodbank.org/emergency-food-distribution/",
     "checked_at": "2026-11-12T10:30:00-08:00",
     "verification_status": "conflicting", "source_title": "RCFB",
     "source_authority_scope": "local_provider_operating_intake",
     "effective_date": "2026-11-20", "notes": None},
    # Nov 25-27 — Thanksgiving closure.
    {"evidence_id": "ev_rcfbar_015", "program_id": _RCFB_ARDEN_PROG,
     "field_path": "availability",
     "claim_value": "November 25-27 - Thanksgiving Holiday (closed)",
     "source_url": "https://rivercityfoodbank.org/emergency-food-distribution/",
     "checked_at": "2026-11-12T10:30:00-08:00",
     "verification_status": "verified", "source_title": "RCFB",
     "source_authority_scope": "local_provider_operating_intake",
     "effective_date": "2026-11-25", "notes": None},
    # Dec 24 - Jan 1, 2027.
    {"evidence_id": "ev_rcfbar_016", "program_id": _RCFB_ARDEN_PROG,
     "field_path": "availability",
     "claim_value": "Thursday, December 24 through Friday, January 1, 2027 (holiday closure)",
     "source_url": "https://rivercityfoodbank.org/thanksgivingfood2026/",
     "checked_at": "2026-11-12T10:26:00-08:00",
     "verification_status": "verified", "source_title": "RCFB Holiday",
     "source_authority_scope": "local_provider_operating_intake",
     "effective_date": "2026-12-24", "notes": None},
    # Nov 21 (Sat) extra distribution — Arden site.
    {"evidence_id": "ev_rcfbar_017", "program_id": _RCFB_ARDEN_PROG,
     "field_path": "availability",
     "claim_value": "Holiday distribution: Saturday, November 21, 2026, 10:30am - 1:30pm, Arden Distribution",
     "source_url": "https://rivercityfoodbank.org/thanksgivingfood2026/",
     "checked_at": "2026-11-12T10:26:00-08:00",
     "verification_status": "verified", "source_title": "RCFB Holiday",
     "source_authority_scope": "local_provider_operating_intake",
     "effective_date": "2026-11-21", "notes": None},
]

# Keep old midtown name for backward compat in a couple of old tests (now unused by _get_notes).
_RCFB_PROG = _RCFB_ARDEN_PROG


# ---------------------------------------------------------------------------
# Inject the police directory fixture into the agent module.
# ---------------------------------------------------------------------------

def _install_police_fixture():
    agent_mod._EMERGENCY_DIR_LOADER = lambda: _POLICE_DIR_FIXTURE


def _remove_police_fixture():
    agent_mod._EMERGENCY_DIR_LOADER = None


# ---------------------------------------------------------------------------
# Helper: build a minimal Agent 8 plan with given matches/needs/actions
# ---------------------------------------------------------------------------

def _build_plan(needs, matches, actions, checked_claims=None, ref_date=REF_DATE,
                allowed_case_facts=None, evidence_records=None):
    payload = {
        "proposed_actions": actions,
        "needs": needs,
        "matches": matches,
        "checked_claims": checked_claims or [],
        "program_availability": [],
        "evidence_records": evidence_records or [],
        "ref_date": ref_date,
        "plan_version": "plan_v1",
    }
    base = _base_req("agent_8", payload, n=99)
    if allowed_case_facts:
        base["allowed_case_facts"] = allowed_case_facts
    return handle(base)


# ===========================================================================
# Fix 1 — Q8 false warning (scenario C)
# ===========================================================================

class TestQ8FalseWarning(unittest.TestCase):
    """
    Root cause: Q8 fires at matching/verification stages (before coverage_gaps exists),
    even when a need has no match yet — that is expected at those stages.
    Fix: Q8 fires only when stage_result has BOTH 'matches' AND 'coverage_gaps'.
    """

    def _a7_req(self, stage_result, needs=None):
        return _base_req("agent_7", {
            "stage": "matching",
            "stage_result": stage_result,
            "needs": needs or [_need("need_food", "food_assistance", "food_pantry",
                                     description="the hospital bill took all my rent money ... no groceries left")],
            "evidence_records": [],
        }, n=1)

    def test_q8_no_fire_at_matching_stage_no_coverage_gaps(self):
        """Scenario C: need_food has no match at matching stage — no Q8."""
        # stage_result has 'matches' but no 'coverage_gaps' (normal at matching stage)
        sr = {"matches": []}  # food need not covered
        result = handle(self._a7_req(sr))
        rule_ids = [f["rule_id"] for f in result["result"]["findings"]]
        self.assertNotIn("Q8", rule_ids,
            "Q8 must NOT fire when stage_result has 'matches' but no 'coverage_gaps'")

    def test_q8_fires_when_coverage_gaps_present_and_need_absent(self):
        """Q8 fires when stage_result has both matches and coverage_gaps, need in neither."""
        needs = [_need("need_food", "food_assistance", "food_pantry")]
        sr = {
            "matches": [],
            "coverage_gaps": [],  # need_food is NOT in coverage_gaps either
        }
        result = handle(self._a7_req(sr, needs=needs))
        rule_ids = [f["rule_id"] for f in result["result"]["findings"]]
        self.assertIn("Q8", rule_ids,
            "Q8 MUST fire when stage_result has coverage_gaps and need is absent from both")

    def test_q8_no_fire_when_need_in_coverage_gaps(self):
        """Q8 does NOT fire when need is in coverage_gaps."""
        needs = [_need("need_food", "food_assistance", "food_pantry")]
        sr = {
            "matches": [],
            "coverage_gaps": [{"need_id": "need_food", "note": "No program found."}],
        }
        result = handle(self._a7_req(sr, needs=needs))
        rule_ids = [f["rule_id"] for f in result["result"]["findings"]]
        self.assertNotIn("Q8", rule_ids,
            "Q8 must NOT fire when need is already in coverage_gaps")


# ===========================================================================
# Fix 2 — Lockout detection
# ===========================================================================

class TestLockoutDetection(unittest.TestCase):

    def setUp(self):
        _install_police_fixture()

    def tearDown(self):
        _remove_police_fixture()

    def _lockout_plan(self, needs, matches, actions, allowed_case_facts=None,
                      checked_claims=None, evidence_records=None):
        return _build_plan(needs, matches, actions,
                           checked_claims=checked_claims,
                           allowed_case_facts=allowed_case_facts,
                           evidence_records=evidence_records)

    def test_lockout_via_fact_adds_police_sentence_to_legal_aid_card(self):
        """Lockout fact → police sentence in housing_legal_aid card's next_step."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        result = self._lockout_plan(needs, matches, actions, allowed_case_facts=facts)
        self.assertEqual(result["status"], "completed")
        cards = result["result"]["action_cards"]
        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertIn("locked out", card["next_step"].lower(),
                      "Police sentence must appear in next_step")
        self.assertIn("police non-emergency", card["next_step"].lower())

    def test_lockout_via_need_text_adds_police_sentence(self):
        """Lockout detected from need description (no fact) → police sentence."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid",
                       description="The landlord changed the locks on me")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        result = self._lockout_plan(needs, matches, actions)
        card = result["result"]["action_cards"][0]
        self.assertIn("locked out", card["next_step"].lower())

    def test_lockout_original_quote_trigger(self):
        """Lockout detected from original_quote."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid",
                       original_quote="they locked me out already")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        result = self._lockout_plan(needs, matches, actions)
        card = result["result"]["action_cards"][0]
        self.assertIn("locked out", card["next_step"].lower())

    def test_lockout_with_verified_police_record_adds_contacts(self):
        """Lockout + verified police records → contacts[] has police entries."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        result = self._lockout_plan(needs, matches, actions, allowed_case_facts=facts)
        card = result["result"]["action_cards"][0]
        police_contacts = [c for c in card.get("contacts", [])
                           if "police non-emergency" in c["label"].lower()]
        self.assertGreater(len(police_contacts), 0, "Police contacts must be in contacts[]")
        # Verify label format "Police non-emergency (<geography>)"
        for pc in police_contacts:
            self.assertRegex(pc["label"], r"Police non-emergency \(.+\)")
            # value: "<org>: <phone>"
            self.assertIn(":", pc["value"])
        # unverified record (Fake Police) must NOT appear
        values = [c["value"] for c in police_contacts]
        self.assertFalse(any("Fake" in v for v in values))

    def test_lockout_sheriff_has_verified_hours(self):
        """Sheriff availability row is verified → hours populated."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        result = self._lockout_plan(needs, matches, actions, allowed_case_facts=facts)
        card = result["result"]["action_cards"][0]
        sheriff = next((c for c in card.get("contacts", [])
                        if "Sacramento County" in c["label"]), None)
        self.assertIsNotNone(sheriff, "Sheriff contact must be present")
        self.assertIsNotNone(sheriff["hours"], "Sheriff hours must be populated (verified availability)")
        self.assertIn("24", sheriff["hours"])

    def test_lockout_sacpd_hours_none(self):
        """SACPD availability row is not verified → hours is None."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        result = self._lockout_plan(needs, matches, actions, allowed_case_facts=facts)
        card = result["result"]["action_cards"][0]
        sacpd = next((c for c in card.get("contacts", [])
                      if "City of Sacramento" in c["label"]), None)
        self.assertIsNotNone(sacpd, "SACPD contact must be present")
        self.assertIsNone(sacpd["hours"], "SACPD hours must be None (availability not verified)")

    def test_lockout_no_legal_aid_uses_first_housing_card(self):
        """No housing_legal_aid match → police sentence goes to first late-stage housing card."""
        needs = [_need("need_h", "housing_assistance", "emergency_shelter")]
        matches = [_match("PROG-SHELTER", ["need_h"], subcategory="emergency_shelter")]
        actions = [_action("act_01", "need_h", "PROG-SHELTER")]
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        result = self._lockout_plan(needs, matches, actions, allowed_case_facts=facts)
        card = result["result"]["action_cards"][0]
        self.assertIn("locked out", card["next_step"].lower())

    def test_lockout_no_housing_match_gap_note(self):
        """No housing_legal_aid matched → coverage_gap note is plain, no search promise."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid"),
                 _need("need_f", "food_assistance", "food_pantry")]
        matches = [_match("PROG-FOOD", ["need_f"], subcategory="food_pantry")]
        actions = [_action("act_01", "need_f", "PROG-FOOD")]
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        result = self._lockout_plan(needs, matches, actions, allowed_case_facts=facts)
        gaps = result["result"]["coverage_gaps"]
        legal_gap = next((g for g in gaps if g["need_id"] == "need_h"), None)
        self.assertIsNotNone(legal_gap)
        note = legal_gap["note"]
        # Plain note — no "search is going on" promise
        self.assertIn("No legal-help program was found yet", note)
        self.assertNotIn("search", note.lower())
        # Police sentence in the gap note
        self.assertIn("locked out", note.lower())
        self.assertIn("police non-emergency", note.lower())

    def test_no_lockout_no_police_sentence(self):
        """No lockout signal → police sentence never added."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        result = self._lockout_plan(needs, matches, actions)
        card = result["result"]["action_cards"][0]
        self.assertNotIn("locked out", card["next_step"].lower())

    def test_lockout_from_allowed_case_facts_only(self):
        """Lockout detected from allowed_case_facts only; need text says 'nowhere to stay tonight'
        (a displaced-now keyword, not a lockout keyword) — still fires via the fact."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid",
                       description="nowhere to stay tonight")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        # Lockout comes only from allowed_case_facts (eviction_notice_type = "lockout")
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        result = self._lockout_plan(needs, matches, actions, allowed_case_facts=facts)
        card = result["result"]["action_cards"][0]
        self.assertIn("locked out", card["next_step"].lower(),
                      "Police sentence must appear: lockout detected from allowed_case_facts")
        # Verify it was NOT triggered by the need text alone — repeat without the fact
        result_no_fact = self._lockout_plan(needs, matches, actions)
        card_no_fact = result_no_fact["result"]["action_cards"][0]
        self.assertNotIn("locked out", card_no_fact["next_step"].lower(),
                         "'nowhere to stay tonight' alone must NOT trigger lockout")


# ===========================================================================
# Fix 3 — Pantry closures (River City)
# ===========================================================================

class TestPantryClosures(unittest.TestCase):
    """
    Fix: for each card, read individual EvidenceRecord rows with field_path "availability"
    that contain a date.  Agent 5 merges them into one merged checked_claims item so the
    dated rows only survive in evidence_records.
    """

    def _get_notes(self, ev_records=None):
        return _closure_rows_for_card(
            ev_records if ev_records is not None else _RCFB_ARDEN_EV_RECORDS,
            _RCFB_ARDEN_PROG, REF_DATE)

    def test_nov25_27_closure_shown(self):
        notes = self._get_notes()
        matching = [n for n in notes if "Nov 25" in n and "27" in n]
        self.assertTrue(matching, f"Nov 25-27 closure must be in notes; got: {notes}")
        self.assertIn("thanksgiving", matching[0].lower())
        self.assertIn("checked Nov 12", matching[0])

    def test_dec24_jan1_closure_shown(self):
        notes = self._get_notes()
        matching = [n for n in notes if "Dec 24" in n and "Jan 1" in n]
        self.assertTrue(matching, f"Dec 24-Jan 1 closure must be in notes; got: {notes}")
        self.assertIn("holiday closure", matching[0])
        self.assertIn("checked Nov 12", matching[0])

    def test_nov11_past_skipped(self):
        """Nov 11 is before ref_date 2026-11-13 → must be skipped."""
        notes = self._get_notes()
        self.assertFalse(any("Nov 11" in n for n in notes),
                         f"Nov 11 (past) must NOT appear; got: {notes}")

    def test_nov20_conflict_note(self):
        """Nov 20 conflict → 'Sources differ … Call before you go.'"""
        notes = self._get_notes()
        matching = [n for n in notes if "Nov 20" in n]
        self.assertTrue(matching, f"Nov 20 conflict note must appear; got: {notes}")
        self.assertIn("Sources differ", matching[0])
        self.assertIn("Call before you go", matching[0])

    def test_nov21_extra_distribution_arden(self):
        """Arden Nov 21 (Sat) extra distribution → 'Extra holiday distribution: Sat Nov 21 ...'"""
        notes = self._get_notes()
        matching = [n for n in notes if "Nov 21" in n]
        self.assertTrue(matching, f"Nov 21 distribution must appear; got: {notes}")
        self.assertIn("Extra holiday distribution", matching[0])
        self.assertIn("Sat", matching[0])
        self.assertIn("10:30am", matching[0])
        self.assertIn("checked Nov 12", matching[0])

    def test_no_date_row_skipped(self):
        """EvidenceRecord with no date → skipped."""
        no_date_ev = {
            "evidence_id": "ev_x", "program_id": _RCFB_ARDEN_PROG,
            "field_path": "availability",
            "claim_value": "Open four days a week.",
            "source_url": "https://example.org", "checked_at": "2026-11-12T10:30:00-08:00",
            "verification_status": "verified", "source_title": "x",
            "source_authority_scope": "local_provider_operating_intake",
            "effective_date": None, "notes": None,
        }
        notes = _closure_rows_for_card([no_date_ev], _RCFB_ARDEN_PROG, REF_DATE)
        self.assertEqual(notes, [], f"Row with no date must be skipped; got: {notes}")

    def test_merged_claim_in_checked_claims_does_not_produce_notes(self):
        """When only the merged claim (no dated rows) is in checked_claims, closure notes
        come from evidence_records; passing only the merged claim as evidence_records
        (it has no parseable date) must yield no notes."""
        # Feed the merged claim as the only "evidence record" — it has no date.
        no_date_ev = {
            "evidence_id": "ev_merged", "program_id": _RCFB_ARDEN_PROG,
            "field_path": "availability",
            "claim_value": None,
            "source_url": "https://example.org", "checked_at": "2026-11-12T10:30:00-08:00",
            "verification_status": "conflicting", "source_title": "x",
            "source_authority_scope": "local_provider_operating_intake",
            "effective_date": None, "notes": None,
        }
        notes = _closure_rows_for_card([no_date_ev], _RCFB_ARDEN_PROG, REF_DATE)
        self.assertEqual(notes, [], "Merged claim with no date must produce no notes")

    def test_closure_notes_in_card_via_agent8(self):
        """Full Agent 8 integration: evidence_records drives closure notes (not checked_claims).
        checked_claims holds only the merged item; evidence_records holds the 6 Arden rows."""
        needs = [_need("need_f", "food_assistance", "food_pantry")]
        matches = [_match(_RCFB_ARDEN_PROG, ["need_f"], subcategory="food_pantry",
                           organization="River City Food Bank",
                           program_name="Emergency Food Distribution (Arden-Arcade)")]
        actions = [_action("act_01", "need_f", _RCFB_ARDEN_PROG)]
        result = _build_plan(needs, matches, actions,
                             checked_claims=[_RCFB_ARDEN_MERGED_CLAIM],
                             evidence_records=_RCFB_ARDEN_EV_RECORDS)
        cards = result["result"]["action_cards"]
        self.assertEqual(len(cards), 1)
        notes = cards[0]["uncertainty_notes"]
        self.assertTrue(any("Nov 25" in n for n in notes), f"Nov 25 closure missing; notes={notes}")
        self.assertTrue(any("Dec 24" in n for n in notes), f"Dec 24 closure missing; notes={notes}")
        self.assertFalse(any("Nov 11" in n for n in notes), f"Nov 11 must be skipped; notes={notes}")
        self.assertTrue(any("Sources differ" in n for n in notes), f"Nov 20 conflict missing; notes={notes}")
        self.assertTrue(any("Nov 21" in n for n in notes), f"Nov 21 distribution missing; notes={notes}")

    def test_next_step_unchanged_by_closure_notes(self):
        """Closure notes must NOT modify next_step."""
        needs = [_need("need_f", "food_assistance", "food_pantry")]
        matches = [_match(_RCFB_ARDEN_PROG, ["need_f"], subcategory="food_pantry")]
        actions = [_action("act_01", "need_f", _RCFB_ARDEN_PROG)]
        result = _build_plan(needs, matches, actions,
                             checked_claims=[_RCFB_ARDEN_MERGED_CLAIM],
                             evidence_records=_RCFB_ARDEN_EV_RECORDS)
        card = result["result"]["action_cards"][0]
        self.assertIn("hours", card["next_step"].lower(),
                      "next_step must keep the original template text")
        self.assertNotIn("Closed", card["next_step"])
        self.assertNotIn("Sources differ", card["next_step"])


# ===========================================================================
# Fix 4 — contacts[] label normalization
# ===========================================================================

# Salvation Army pantry contact rows (from KB ev_sapantry_006 – ev_sapantry_009)
_SA_PANTRY_PROG = "prog_food_salvationarmy_pantry_sac_001"
_SA_PANTRY_CLAIMS = [
    {"program_id": _SA_PANTRY_PROG, "field_path": "contact[0]",
     "claim_value": "Location: 3213 Orange Grove Ave., North Highlands, CA 95660",
     "verification_status": "verified", "evidence_refs": ["ev_sapantry_006"],
     "checked_at": "2026-11-12T10:30:00-08:00", "issue": None},
    {"program_id": _SA_PANTRY_PROG, "field_path": "contact[1]",
     "claim_value": "Food Pantry Schedule: Tuesday, Wednesday, Thursday 9AM - 1PM",
     "verification_status": "verified", "evidence_refs": ["ev_sapantry_007"],
     "checked_at": "2026-11-12T10:30:00-08:00", "issue": None},
    {"program_id": _SA_PANTRY_PROG, "field_path": "contact[2]",
     "claim_value": "North Highlands Family Services: (916) 678-4010",
     "verification_status": "verified", "evidence_refs": ["ev_sapantry_008"],
     "checked_at": "2026-11-12T10:26:00-08:00", "issue": None},
    {"program_id": _SA_PANTRY_PROG, "field_path": "contact[3]",
     "claim_value": "Food for Seniors: 60 years old +, 4th Monday & Thursday, 9AM - 1PM",
     "verification_status": "verified", "evidence_refs": ["ev_sapantry_009"],
     "checked_at": "2026-11-12T10:26:00-08:00", "issue": None},
]


class TestContactLabels(unittest.TestCase):
    """
    Fix: street address / "Location:" prefix → "Address";
         schedule text ("Schedule:", "4th Monday & Thursday, 9AM...") → "Hours";
         phone / generic → "Contact".
    """

    # --- River City style (address number, hours by day) ---
    def test_address_label(self):
        self.assertEqual(_contact_label("contact[0]", "1800 28th St. Sacramento, CA 95816"), "Address")

    def test_address_label_with_location_name(self):
        self.assertEqual(
            _contact_label("contact[0]", "(The Center at St. Matthew's) 2300 Edison Ave. Sacramento, CA 95821"),
            "Address")

    def test_hours_label(self):
        self.assertEqual(_contact_label("contact[1]", "Tuesday & Thursday: 10:30am - 1:30pm"), "Hours")

    def test_hours_label_wed_fri(self):
        self.assertEqual(_contact_label("contact[1]", "Wednesday & Friday: 10:30am - 1:30pm"), "Hours")

    def test_phone_stays_contact(self):
        self.assertEqual(_contact_label("contact[2]", "Phone: 916-446-2627"), "Contact")

    def test_application_method_stays_how_to_apply(self):
        self.assertEqual(_contact_label("application_method[0]", "Apply online at https://example.org"), "How to apply")

    # --- Salvation Army style ---
    def test_location_prefix_is_address(self):
        """'Location: 3213 Orange Grove Ave.' → Address."""
        self.assertEqual(
            _contact_label("contact[0]",
                           "Location: 3213 Orange Grove Ave., North Highlands, CA 95660"),
            "Address")

    def test_schedule_prefix_is_hours(self):
        """'Food Pantry Schedule: Tuesday, Wednesday, Thursday 9AM - 1PM' → Hours."""
        self.assertEqual(
            _contact_label("contact[1]",
                           "Food Pantry Schedule: Tuesday, Wednesday, Thursday 9AM - 1PM"),
            "Hours")

    def test_fourth_day_schedule_is_hours(self):
        """'Food for Seniors: 60 years old +, 4th Monday & Thursday, 9AM - 1PM' → Hours."""
        self.assertEqual(
            _contact_label("contact[3]",
                           "Food for Seniors: 60 years old +, 4th Monday & Thursday, 9AM - 1PM"),
            "Hours")

    def test_phone_with_name_stays_contact(self):
        """'North Highlands Family Services: (916) 678-4010' → Contact (has phone)."""
        self.assertEqual(
            _contact_label("contact[2]",
                           "North Highlands Family Services: (916) 678-4010"),
            "Contact")

    def test_salvation_army_build_contacts_labels(self):
        """_build_contacts assigns Address / Hours / Contact for all 4 SA pantry rows."""
        contacts = _build_contacts(_SA_PANTRY_CLAIMS, _SA_PANTRY_PROG)
        # contact[0]: Location → Address
        c0 = next(c for c in contacts if "Orange Grove" in c["value"])
        self.assertEqual(c0["label"], "Address")
        # contact[1]: Schedule → Hours
        c1 = next(c for c in contacts if "Schedule" in c["value"])
        self.assertEqual(c1["label"], "Hours")
        # contact[2]: phone → Contact
        c2 = next(c for c in contacts if "916" in c["value"])
        self.assertEqual(c2["label"], "Contact")
        # contact[3]: 4th Monday schedule → Hours
        c3 = next(c for c in contacts if "4th Monday" in c["value"])
        self.assertEqual(c3["label"], "Hours")

    def test_build_contacts_produces_address_and_hours_labels(self):
        """_build_contacts produces Address and Hours labels for RCFB-like claims."""
        claims = [
            {"program_id": "PROG-X", "field_path": "contact[0]",
             "claim_value": "1800 28th St. Sacramento, CA 95816",
             "verification_status": "verified", "evidence_refs": ["ev_x_01"],
             "checked_at": "2026-11-12T10:30:00-08:00", "issue": None},
            {"program_id": "PROG-X", "field_path": "contact[1]",
             "claim_value": "Tuesday & Thursday: 10:30am - 1:30pm",
             "verification_status": "verified", "evidence_refs": ["ev_x_02"],
             "checked_at": "2026-11-12T10:30:00-08:00", "issue": None},
            {"program_id": "PROG-X", "field_path": "contact[2]",
             "claim_value": "Phone: 916-446-2627",
             "verification_status": "verified", "evidence_refs": ["ev_x_03"],
             "checked_at": "2026-11-12T10:30:00-08:00", "issue": None},
        ]
        contacts = _build_contacts(claims, "PROG-X")
        # Address
        self.assertEqual(contacts[0]["label"], "Address")
        # Hours
        self.assertEqual(contacts[1]["label"], "Hours")
        # Contact (phone)
        self.assertEqual(contacts[2]["label"], "Contact")

    def test_next_step_phone_lookup_still_works(self):
        """Phone-labelled contacts still appear in next_step (label change must not break lookup)."""
        claims = [
            {"program_id": "PROG-Y", "field_path": "contact[0]",
             "claim_value": "(916) 555-1234",
             "verification_status": "verified", "evidence_refs": ["ev_y_01"],
             "checked_at": "2026-11-12T10:30:00-08:00", "issue": None},
        ]
        contacts = _build_contacts(claims, "PROG-Y")
        self.assertEqual(contacts[0]["label"], "Contact")
        # The _next_step_contacts helper uses a phone-RE pattern, not the label —
        # so it must still pick up the phone number.
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _next_step_contacts
        snippets = _next_step_contacts(contacts)
        self.assertTrue(any("916" in s for s in snippets), "Phone must still appear in next_step snippets")


# ===========================================================================
# Agent 10 — passes lockout and closure plans with no flags
# ===========================================================================

class TestAgent10AcceptsLockoutAndClosure(unittest.TestCase):

    def setUp(self):
        _install_police_fixture()

    def tearDown(self):
        _remove_police_fixture()

    def _validate(self, plan, needs, matches, checked_claims=None, availability=None,
                  evidence_records=None):
        payload = {
            "plan": plan,
            "needs": needs,
            "matches": matches,
            "checked_claims": checked_claims or [],
            "program_availability": availability or [],
            "evidence_records": evidence_records or [],
            "repair_round": 0,
        }
        return handle(_base_req("agent_10", payload, n=50))

    def test_agent10_passes_lockout_plan_no_v8(self):
        """Police sentence added to next_step has no phone → no V8 flag."""
        needs = [_need("need_h", "housing_assistance", "housing_legal_aid")]
        matches = [_match("PROG-LEGAL", ["need_h"], subcategory="housing_legal_aid")]
        actions = [_action("act_01", "need_h", "PROG-LEGAL")]
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "lockout", "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        plan_result = _build_plan(needs, matches, actions, allowed_case_facts=facts)
        plan = plan_result["result"]
        result = self._validate(plan, needs, matches,
                                availability=[{"program_id": "PROG-LEGAL",
                                               "availability": "confirmed_open",
                                               "evidence_refs": []}])
        flags = result["result"]["flags"]
        v8_flags = [f for f in flags if f["rule_id"] == "V8"]
        self.assertEqual(v8_flags, [], f"V8 must not fire for police sentence; flags={flags}")

    def test_agent10_passes_closure_plan_no_flags(self):
        """Closure notes in uncertainty_notes do not trigger any flag."""
        needs = [_need("need_f", "food_assistance", "food_pantry")]
        matches = [_match(_RCFB_ARDEN_PROG, ["need_f"], subcategory="food_pantry")]
        actions = [_action("act_01", "need_f", _RCFB_ARDEN_PROG)]
        plan_result = _build_plan(needs, matches, actions,
                                  checked_claims=[_RCFB_ARDEN_MERGED_CLAIM],
                                  evidence_records=_RCFB_ARDEN_EV_RECORDS)
        plan = plan_result["result"]
        result = self._validate(plan, needs, matches,
                                checked_claims=[_RCFB_ARDEN_MERGED_CLAIM],
                                evidence_records=_RCFB_ARDEN_EV_RECORDS,
                                availability=[{"program_id": _RCFB_ARDEN_PROG,
                                               "availability": "confirmed_open",
                                               "evidence_refs": []}])
        flags = result["result"]["flags"]
        blocking = [f for f in flags if f["blocks_release"]]
        self.assertEqual(blocking, [], f"No blocking flags for closure plan; flags={flags}")


if __name__ == "__main__":
    unittest.main()
