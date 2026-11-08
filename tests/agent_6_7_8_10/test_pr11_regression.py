"""
PR #11 regression tests (C-R1 through C-R6).

Load the real KB from navigator/kb/kb_sacramento.json, build checked_claims
from its evidence_records (verification_status, checked_at, evidence_refs=[evidence_id]),
and run agent_8 for the 4 programs (Saint John's, Coordinated Access, CalFresh, EDD).

Run:
    python3 -m unittest tests/agent_6_7_8_10/test_pr11_regression.py
    python3 -m unittest discover -s tests -t .
"""

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import handle, TASK_TYPES

KB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "navigator", "kb", "kb_sacramento.json"
)

PROG_SAINT_JOHNS = "prog_housing_saintjohns_sac_001"
PROG_COORD_ACCESS = "prog_housing_coordaccess_sac_001"
PROG_CALFRESH = "prog_food_calfresh_sac_001"
PROG_EDD = "prog_income_edd_ui_ca_001"
ALL_FOUR = [PROG_SAINT_JOHNS, PROG_COORD_ACCESS, PROG_CALFRESH, PROG_EDD]


def _load_kb():
    with open(KB_PATH) as f:
        return json.load(f)


def _checked_claims_from_evidence(ev_records):
    """Build the checked_claims list from KB evidence_records as described in the task."""
    claims = []
    for e in ev_records:
        claims.append({
            "program_id": e["program_id"],
            "field_path": e["field_path"],
            "claim_value": e["claim_value"],
            "verification_status": e["verification_status"],
            "evidence_refs": [e["evidence_id"]],
            "checked_at": e["checked_at"],
            "issue": None,
        })
    return claims


def _agent8_request(kb, prog_ids):
    """Build a minimal agent_8 request covering the given program IDs."""
    programs = {p["program_id"]: p for p in kb["program_records"]}
    ev_records = kb["evidence_records"]
    checked_claims = _checked_claims_from_evidence(ev_records)

    needs = []
    matches = []
    actions = []

    subcategory_map = {
        PROG_SAINT_JOHNS: "rental_assistance",
        PROG_COORD_ACCESS: "emergency_shelter",
        PROG_CALFRESH: "calfresh_benefits",
        PROG_EDD: "unemployment_insurance",
    }
    category_map = {
        PROG_SAINT_JOHNS: "housing_assistance",
        PROG_COORD_ACCESS: "housing_assistance",
        PROG_CALFRESH: "food_assistance",
        PROG_EDD: "income_support",
    }

    for i, pid in enumerate(prog_ids, 1):
        p = programs[pid]
        need_id = f"need_{i:03d}"
        needs.append({
            "need_id": need_id,
            "category": category_map[pid],
            "subcategory": subcategory_map[pid],
            "description": p["program_name"],
            "original_quote": p["program_name"],
            "confirmation_status": "confirmed",
            "user_reported": True,
            "urgency": "high",
            "urgency_reason": "stated by user",
            "user_priority": None,
        })
        # gather program-level evidence refs
        prog_ev_ids = [e["evidence_id"] for e in ev_records if e["program_id"] == pid]
        matches.append({
            "program_id": pid,
            "need_ids": [need_id],
            "match_status": "supported_match",
            "matched_criteria": [],
            "missing_case_facts": [],
            "mismatch_criteria": [],
            "evidence_refs": prog_ev_ids[:1],
            "organization": p["organization"],
            "program_name": p["program_name"],
            "subcategory": subcategory_map[pid],
        })
        actions.append({
            "action_id": f"act_{i:02d}",
            "need_id": need_id,
            "program_id": pid,
            "suggested_priority": i,
            "order_group": "parallel",
            "rationale": "x",
            "dependency_ids": [],
            "official_deadline": None,
            "user_target_date": None,
            "estimated_processing_time": None,
            "evidence_refs": prog_ev_ids[:1],
            "uncertainty_notes": [],
            "user_override_allowed": True,
        })

    base = {
        "request_id": "req_pr11_r1", "run_id": "run-pr11", "case_id": "case-pr11",
        "case_version": 1, "schema_version": "1.0", "correlation_id": "corr-pr11",
        "role_id": "agent_8", "task_type": TASK_TYPES["agent_8"],
        "upstream_result_refs": [], "allowed_case_facts": [],
    }
    base["payload"] = {
        "proposed_actions": actions,
        "needs": needs,
        "matches": matches,
        "checked_claims": checked_claims,
        "evidence_records": ev_records,
        "plan_version": "plan_pr11_v1",
    }
    return base


class TestPR11Regression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        kb = _load_kb()
        req = _agent8_request(kb, ALL_FOUR)
        result = handle(req)
        cards = result["result"]["action_cards"]
        cls.cards = {c["program_id"]: c for c in cards}

    def _card(self, pid):
        return self.cards[pid]

    # C-R1: Saint John's next_step contains the clean URL snippet and no stray )( or 4tjLVzi)
    def test_C_R1_saint_johns_next_step_url(self):
        ns = self._card(PROG_SAINT_JOHNS)["next_step"]
        self.assertIn(
            "Apply online: https://wkf.ms/4tjLVzi (checked",
            ns,
            f"next_step missing expected URL snippet; got: {ns!r}",
        )
        self.assertNotIn(")(" , ns, f"next_step contains stray )(: {ns!r}")
        self.assertNotIn("4tjLVzi)", ns, f"URL has trailing ): {ns!r}")

    # C-R2: Saint John's contacts[] has a "How to apply" item with the normalised URL value
    def test_C_R2_saint_johns_contacts_how_to_apply(self):
        contacts = self._card(PROG_SAINT_JOHNS)["contacts"]
        values = [c["value"] for c in contacts if c["label"] == "How to apply"]
        self.assertIn(
            "Apply online: https://wkf.ms/4tjLVzi",
            values,
            f"No 'How to apply' contact with clean URL value; got: {values}",
        )

    # C-R3: no EDD contacts[] item contains "must be at least 18"
    def test_C_R3_edd_no_age_rule_in_contacts(self):
        contacts = self._card(PROG_EDD)["contacts"]
        for item in contacts:
            self.assertNotIn(
                "must be at least 18",
                item["value"].lower(),
                f"EDD contacts[] contains excluded rule row: {item['value']!r}",
            )

    # C-R4: Coordinated Access contacts[] has an item containing "Call 2-1-1 and press 8"
    def test_C_R4_coord_access_211_in_contacts(self):
        contacts = self._card(PROG_COORD_ACCESS)["contacts"]
        found = any("Call 2-1-1 and press 8" in item["value"] for item in contacts)
        self.assertTrue(
            found,
            f"Coordinated Access contacts[] has no item with '2-1-1'; got: {[c['value'] for c in contacts]}",
        )

    # C-R5: every card's next_step is at most 250 characters
    def test_C_R5_next_step_max_250_chars(self):
        for pid, card in self.cards.items():
            ns = card["next_step"]
            self.assertLessEqual(
                len(ns),
                250,
                f"next_step for {pid} is {len(ns)} chars (> 250): {ns!r}",
            )

    # C-R6: every next_step ≤ 250 chars, never ends with "…", and every phone
    # number or URL it contains has "(checked" appearing after it in the text.
    def test_C_R6_next_step_no_ellipsis_and_checked_after_contacts(self):
        _url_or_phone = re.compile(
            r"https?://\S+|\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}"
        )
        for pid, card in self.cards.items():
            ns = card["next_step"]
            self.assertLessEqual(
                len(ns), 250,
                f"next_step for {pid} is {len(ns)} chars (> 250): {ns!r}",
            )
            self.assertFalse(
                ns.endswith("\u2026"),
                f"next_step for {pid} ends with '…' (was truncated): {ns!r}",
            )
            for m in _url_or_phone.finditer(ns):
                remainder = ns[m.end():]
                self.assertIn(
                    "(checked",
                    remainder,
                    f"Phone/URL {m.group()!r} in next_step for {pid} has no "
                    f"'(checked' after it.\nnext_step: {ns!r}",
                )

    # C-R7: Coordinated Access next_step contact part starts with "Call 2-1-1 and press 8"
    def test_C_R7_coord_access_next_step_starts_with_211(self):
        ns = self._card(PROG_COORD_ACCESS)["next_step"]
        self.assertIn(
            "Call 2-1-1 and press 8",
            ns,
            f"Coordinated Access next_step does not contain 'Call 2-1-1 and press 8': {ns!r}",
        )
        # The 2-1-1 snippet must appear before the Contact phone snippet
        idx_211 = ns.index("Call 2-1-1 and press 8")
        idx_tollfree = ns.find("Toll-free")
        self.assertGreater(
            idx_tollfree, idx_211,
            f"'Toll-free' appears before 'Call 2-1-1 and press 8' in next_step: {ns!r}",
        )

    # C-R8: no CalFresh contacts[] item contains "lost or stolen"
    def test_C_R8_calfresh_no_lost_or_stolen_in_contacts(self):
        contacts = self._card(PROG_CALFRESH)["contacts"]
        for item in contacts:
            self.assertNotIn(
                "lost or stolen",
                item["value"].lower(),
                f"CalFresh contacts[] contains 'lost or stolen' row: {item['value']!r}",
            )
            self.assertNotIn(
                "ebt customer service",
                item["value"].lower(),
                f"CalFresh contacts[] contains 'EBT Customer Service' row: {item['value']!r}",
            )

    # C-R9: no next_step for the 4 KB programs contains ". (checked"
    def test_C_R9_no_double_period_before_checked(self):
        for pid, card in self.cards.items():
            ns = card["next_step"]
            self.assertNotIn(
                ". (checked",
                ns,
                f"next_step for {pid} contains '. (checked' (double period): {ns!r}",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
