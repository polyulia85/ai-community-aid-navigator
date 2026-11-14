"""
PR #2 and PR #13 audit regression tests (A6-01, A6-02, A6-03, A6-04,
A7-01, A7-02, A7-03, A10-02, C-OD2, and PR #13 items 1–12).

One test per audit item.  All tests are self-contained (no fixtures loaded
from disk) so they run independently.

Run:
    python3 -m unittest tests/agent_6_7_8_10/test_pr2_regression.py
    python3 -m unittest discover -s tests -t .
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import handle, TASK_TYPES

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_BASE = {
    "request_id": "req_pr2_test",
    "run_id": "run-pr2",
    "case_id": "case-pr2",
    "case_version": 1,
    "schema_version": "1.0",
    "correlation_id": "corr-pr2",
    "allowed_case_facts": [],
    "upstream_result_refs": [],
}


def _req(role, payload):
    r = dict(_BASE)
    r["role_id"] = role
    r["task_type"] = TASK_TYPES[role]
    r["payload"] = payload
    return r


def _need(need_id, category="food_assistance", subcategory="food_pantry",
          urgency="high"):
    return {
        "need_id": need_id,
        "category": category,
        "subcategory": subcategory,
        "description": need_id,
        "original_quote": need_id,
        "confirmation_status": "confirmed",
        "user_reported": True,
        "urgency": urgency,
        "urgency_reason": "test",
        "user_priority": None,
    }


def _match(program_id, need_ids, subcategory="food_pantry"):
    return {
        "program_id": program_id,
        "need_ids": list(need_ids),
        "match_status": "supported_match",
        "matched_criteria": [],
        "missing_case_facts": [],
        "mismatch_criteria": [],
        "evidence_refs": [],
        "subcategory": subcategory,
    }


def _open_avail(program_id):
    return {"program_id": program_id, "availability": "confirmed_open",
            "evidence_refs": []}


def _run6(needs, matches, checked_claims=None, program_availability=None,
          evidence_records=None, timing=None, ref_date=None, case_facts=None):
    payload = {
        "needs": needs,
        "matches": matches,
        "checked_claims": checked_claims or [],
        "program_availability": program_availability or [
            _open_avail(m["program_id"]) for m in matches],
        "evidence_records": evidence_records or [],
        "timing": timing or [],
    }
    if ref_date is not None:
        payload["ref_date"] = ref_date
    if case_facts is not None:
        payload["case_facts"] = case_facts
    return handle(_req("agent_6", payload))["result"]["proposed_actions"]


def _run7(stage_result, needs, evidence_records=None):
    payload = {
        "stage": "verification",
        "stage_result": stage_result,
        "needs": needs,
    }
    if evidence_records is not None:
        payload["evidence_records"] = evidence_records
    return handle(_req("agent_7", payload))["result"]["findings"]


def _run10(plan, needs, matches, checked_claims=None, evidence_records=None,
           availability=None):
    payload = {
        "plan": plan,
        "needs": needs,
        "matches": matches,
        "checked_claims": checked_claims or [],
        "availability": availability or {},
        "evidence_records": evidence_records or [],
    }
    return handle(_req("agent_10", payload))["result"]


# ---------------------------------------------------------------------------
# A6-01: Multiple needs – one resource serves several need_ids
# ---------------------------------------------------------------------------

def _run6_and_8(needs, matches, checked_claims=None, program_availability=None,
                evidence_records=None, timing=None, ref_date=None):
    """Run agent_6 then agent_8 and return (actions, cards)."""
    acts = _run6(needs, matches, checked_claims=checked_claims,
                 program_availability=program_availability,
                 evidence_records=evidence_records, timing=timing,
                 ref_date=ref_date)
    payload = {
        "proposed_actions": acts,
        "needs": needs,
        "matches": matches,
        "checked_claims": checked_claims or [],
        "evidence_records": evidence_records or [],
        "plan_version": "plan_test",
    }
    result = handle(_req("agent_8", payload))["result"]
    return acts, result["action_cards"]


class TestA601MultipleNeeds(unittest.TestCase):
    """A resource serving need_A and need_B must:
    - produce one action per need_id in agent_6 (no need_ids key on any action)
    - produce one merged card in agent_8 with both needs in related_need_ids
    - coverage must be the same when input order is reversed
    """

    def _run(self, need_ids_order):
        needs = [
            _need("need_A", category="food_assistance", subcategory="food_pantry"),
            _need("need_B", category="food_assistance", subcategory="calfresh_benefits"),
        ]
        matches = [_match("PROG-MULTI", need_ids_order, subcategory="food_pantry")]
        acts, cards = _run6_and_8(needs, matches)
        # Coverage from actions (each has a single need_id per contract 4.6).
        covered_by_actions = {a["need_id"] for a in acts if a.get("need_id")}
        # Coverage from the merged card's related_need_ids.
        covered_by_card = {n for c in cards for n in c.get("related_need_ids", [])}
        return acts, cards, covered_by_actions, covered_by_card

    def test_no_need_ids_field_on_actions(self):
        """Contract 4.6: actions must not carry a need_ids (plural) field."""
        needs = [
            _need("need_A", category="food_assistance", subcategory="food_pantry"),
            _need("need_B", category="food_assistance", subcategory="calfresh_benefits"),
        ]
        matches = [_match("PROG-MULTI", ["need_A", "need_B"], subcategory="food_pantry")]
        acts = _run6(needs, matches)
        for a in acts:
            self.assertNotIn("need_ids", a,
                             f"Action {a['action_id']} must not have a need_ids field: {list(a)}")

    def test_card_lists_both_needs_forward(self):
        """Agent 8 merges the two actions into one card with both need_ids."""
        _, cards, _, covered_by_card = self._run(["need_A", "need_B"])
        self.assertIn("need_A", covered_by_card)
        self.assertIn("need_B", covered_by_card)

    def test_card_lists_both_needs_reversed(self):
        _, cards, _, covered_by_card = self._run(["need_B", "need_A"])
        self.assertIn("need_A", covered_by_card)
        self.assertIn("need_B", covered_by_card)

    def test_forward_order_covers_both_needs_via_actions(self):
        _, _, covered_by_actions, _ = self._run(["need_A", "need_B"])
        self.assertIn("need_A", covered_by_actions)
        self.assertIn("need_B", covered_by_actions)

    def test_reversed_order_covers_both_needs_via_actions(self):
        _, _, covered_by_actions, _ = self._run(["need_B", "need_A"])
        self.assertIn("need_A", covered_by_actions)
        self.assertIn("need_B", covered_by_actions)

    def test_same_coverage_regardless_of_order(self):
        _, _, cov_fwd, card_fwd = self._run(["need_A", "need_B"])
        _, _, cov_rev, card_rev = self._run(["need_B", "need_A"])
        self.assertEqual(cov_fwd, cov_rev,
                         "Action coverage must not change when need_ids order is reversed")
        self.assertEqual(card_fwd, card_rev,
                         "Card coverage must not change when need_ids order is reversed")


# ---------------------------------------------------------------------------
# A6-02: Conflicting deadlines
# ---------------------------------------------------------------------------

class TestA602ConflictingDeadlines(unittest.TestCase):
    """Two different verified deadlines or claim_value=None must produce a
    'confirm' action with both evidence refs and no empty () or None in text."""

    def _claims_two_verified(self, pid):
        return [
            {"program_id": pid, "field_path": "deadlines[0]",
             "claim_value": "2026-11-04",
             "verification_status": "verified",
             "evidence_refs": ["EV-A1"], "checked_at": "2026-10-21T15:00:00Z",
             "issue": None},
            {"program_id": pid, "field_path": "deadlines[0]",
             "claim_value": "2026-12-10",
             "verification_status": "verified",
             "evidence_refs": ["EV-A2"], "checked_at": "2026-10-21T15:00:00Z",
             "issue": None},
        ]

    def _claims_none_value(self, pid):
        return [
            {"program_id": pid, "field_path": "deadlines[0]",
             "claim_value": None,
             "verification_status": "verified",
             "evidence_refs": ["EV-B1"], "checked_at": "2026-10-21T15:00:00Z",
             "issue": None},
        ]

    def _run_with_claims(self, claims):
        pid = "PROG-DL"
        needs = [_need("need_001", category="housing_assistance",
                        subcategory="rental_assistance")]
        matches = [_match(pid, ["need_001"], subcategory="rental_assistance")]
        ev_records = [{"evidence_id": r, "program_id": pid,
                       "field_path": "deadlines[0]", "claim_value": "x",
                       "source_url": "", "checked_at": "2026-10-21T15:00:00Z",
                       "verification_status": "verified"}
                      for r in ["EV-A1", "EV-A2", "EV-B1"]]
        acts = _run6(needs, matches, checked_claims=claims,
                     evidence_records=ev_records)
        return acts

    def test_two_verified_deadlines_produce_confirm_action(self):
        """Two verified deadlines must produce a 'confirm deadline' action."""
        acts = self._run_with_claims(self._claims_two_verified("PROG-DL"))
        confirm = next((a for a in acts
                        if "Official sources disagree" in a["rationale"]
                        or "confirm" in a["rationale"].lower()), None)
        self.assertIsNotNone(confirm,
                             "Expected a confirm-deadline action for two verified deadlines")

    def test_two_verified_deadlines_no_empty_parens_or_none(self):
        """The confirm action must not contain '()' or 'None' in user-visible text."""
        acts = self._run_with_claims(self._claims_two_verified("PROG-DL"))
        for a in acts:
            for field in ("rationale", "uncertainty_notes"):
                text = str(a.get(field, ""))
                self.assertNotIn("()", text,
                                 f"Empty () found in action field {field!r}: {text!r}")
                self.assertNotIn("None", text,
                                 f"'None' found in action field {field!r}: {text!r}")

    def test_claim_value_none_produces_confirm_action(self):
        """A verified claim with claim_value=None must produce a confirm action."""
        acts = self._run_with_claims(self._claims_none_value("PROG-DL"))
        confirm = next((a for a in acts
                        if "confirm" in a["rationale"].lower()
                        or "unknown" in a["rationale"].lower()), None)
        self.assertIsNotNone(confirm,
                             "Expected a confirm action when deadline claim_value is None")

    def test_claim_value_none_no_empty_parens_or_none(self):
        """The confirm action for a None-value claim must not show () or None."""
        acts = self._run_with_claims(self._claims_none_value("PROG-DL"))
        for a in acts:
            for field in ("rationale",):
                text = str(a.get(field, ""))
                self.assertNotIn("()", text,
                                 f"Empty () found in rationale: {text!r}")
                self.assertNotIn("None", text,
                                 f"'None' found in rationale: {text!r}")


# ---------------------------------------------------------------------------
# A6-03: Time-based ordering
# ---------------------------------------------------------------------------

class TestA603TimeBasedOrdering(unittest.TestCase):
    """With equal urgency, Nov 4 deadline sorts before Dec 10, regardless of
    input order."""

    def _run(self, matches_order):
        needs = [
            _need("need_A", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
            _need("need_B", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        timing = [
            {"program_id": "PROG-NOV4", "need_id": "need_A",
             "official_deadline": "2026-11-04",
             "user_target_date": None,
             "estimated_processing_time": None},
            {"program_id": "PROG-DEC10", "need_id": "need_B",
             "official_deadline": "2026-12-10",
             "user_target_date": None,
             "estimated_processing_time": None},
        ]
        verified_claims = [
            {"program_id": "PROG-NOV4", "field_path": "deadlines[0]",
             "claim_value": "2026-11-04", "verification_status": "verified",
             "evidence_refs": ["EV-N4"], "checked_at": "2026-10-21T15:00:00Z",
             "issue": None},
            {"program_id": "PROG-DEC10", "field_path": "deadlines[0]",
             "claim_value": "2026-12-10", "verification_status": "verified",
             "evidence_refs": ["EV-D10"], "checked_at": "2026-10-21T15:00:00Z",
             "issue": None},
        ]
        avail = [_open_avail("PROG-NOV4"), _open_avail("PROG-DEC10")]
        ev = [{"evidence_id": r, "program_id": p,
               "field_path": "deadlines[0]", "claim_value": d,
               "source_url": "", "checked_at": "2026-10-21T15:00:00Z",
               "verification_status": "verified"}
              for (r, p, d) in [("EV-N4", "PROG-NOV4", "2026-11-04"),
                                 ("EV-D10", "PROG-DEC10", "2026-12-10")]]
        acts = _run6(needs, matches_order, checked_claims=verified_claims,
                     program_availability=avail, evidence_records=ev,
                     timing=timing)
        return acts

    def test_nov4_before_dec10_natural_order(self):
        matches = [
            _match("PROG-NOV4", ["need_A"], subcategory="rental_assistance"),
            _match("PROG-DEC10", ["need_B"], subcategory="rental_assistance"),
        ]
        acts = self._run(matches)
        pids = [a["program_id"] for a in acts if a["program_id"]]
        nov4_idx = pids.index("PROG-NOV4")
        dec10_idx = pids.index("PROG-DEC10")
        self.assertLess(nov4_idx, dec10_idx,
                        f"PROG-NOV4 must come before PROG-DEC10; got order {pids}")

    def test_nov4_before_dec10_reversed_input(self):
        """Nov 4 deadline sorts before Dec 10 even when matches are given reversed."""
        matches = [
            _match("PROG-DEC10", ["need_B"], subcategory="rental_assistance"),
            _match("PROG-NOV4", ["need_A"], subcategory="rental_assistance"),
        ]
        acts = self._run(matches)
        pids = [a["program_id"] for a in acts if a["program_id"]]
        nov4_idx = pids.index("PROG-NOV4")
        dec10_idx = pids.index("PROG-DEC10")
        self.assertLess(nov4_idx, dec10_idx,
                        f"Nov 4 deadline must sort before Dec 10 regardless of input order; got {pids}")


# ---------------------------------------------------------------------------
# A6-04: Unsupported urgency – no dates in, no urgency words out
# ---------------------------------------------------------------------------

class TestA604UnsupportedUrgency(unittest.TestCase):
    """If no deadline or target date is present, the rationale must not say
    'approaching', 'is close', or 'deadline' in a time-pressuring way."""

    _URGENCY_WORDS = ("approaching", "is close", "is near", "running out",
                      "before the deadline")

    def test_no_dates_means_no_urgency_wording(self):
        needs = [_need("need_001", category="housing_assistance",
                        subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-RA", ["need_001"], subcategory="rental_assistance")]
        # No timing, no facts with dates, no deadline claims.
        acts = _run6(needs, matches, checked_claims=[], evidence_records=[],
                     timing=[])
        for a in acts:
            rationale = (a.get("rationale") or "").lower()
            for word in self._URGENCY_WORDS:
                self.assertNotIn(
                    word, rationale,
                    f"Urgency word {word!r} found in rationale without any date: "
                    f"{rationale!r}",
                )


# ---------------------------------------------------------------------------
# A7-01: Q8 fires only when stage_result has BOTH matches and coverage_gaps
#        (Fix 1 — Nov 12 2026 regression fix)
# ---------------------------------------------------------------------------

class TestA701EmptyMatches(unittest.TestCase):
    """Q8 fires only when stage_result contains BOTH 'matches' AND 'coverage_gaps'."""

    def test_empty_matches_no_coverage_gaps_no_q8(self):
        """At matching/verification stage no coverage_gaps key → Q8 must stay silent."""
        needs = [
            _need("need_001"),
            _need("need_002"),
            _need("need_003"),
        ]
        stage_result = {"matches": [], "checked_claims": []}
        findings = _run7(stage_result, needs)
        q8_needs = {f["need_id"] for f in findings if f["rule_id"] == "Q8"}
        self.assertEqual(q8_needs, set(),
            "Q8 must NOT fire at matching stage (no coverage_gaps key in stage_result)")

    def test_empty_matches_with_coverage_gaps_key_fires_q8(self):
        """When stage_result has coverage_gaps key and need is in neither → Q8 fires."""
        needs = [
            _need("need_001"),
            _need("need_002"),
        ]
        stage_result = {
            "matches": [],
            "checked_claims": [],
            "coverage_gaps": [],  # key present, but need not in it
        }
        findings = _run7(stage_result, needs)
        q8_needs = {f["need_id"] for f in findings if f["rule_id"] == "Q8"}
        self.assertIn("need_001", q8_needs)
        self.assertIn("need_002", q8_needs)


# ---------------------------------------------------------------------------
# A7-02: Every evidence_ref must exist in evidence_records; empty list ≠ pass
# ---------------------------------------------------------------------------

class TestA702EvidenceRefs(unittest.TestCase):
    """An empty evidence_records list must NOT pass a verified claim that cites
    an evidence_ref."""

    def test_empty_evidence_records_fails_verified_claim_with_ref(self):
        needs = [_need("need_001")]
        claims = [{
            "program_id": "PROG-X",
            "field_path": "contact[0]",
            "claim_value": "Call 555-0100",
            "verification_status": "verified",
            "evidence_refs": ["EV-DOES-NOT-EXIST"],
            "checked_at": "2026-10-21T15:00:00Z",
            "issue": None,
        }]
        matches = [_match("PROG-X", ["need_001"])]
        stage_result = {"matches": matches, "checked_claims": claims}
        # Pass an EMPTY evidence_records list (not absent — present but empty).
        findings = _run7(stage_result, needs, evidence_records=[])
        q1_rules = [f["rule_id"] for f in findings if f["rule_id"] == "Q1"]
        self.assertGreater(
            len(q1_rules), 0,
            "Q1 must fire when evidence_records is empty and a claim cites a ref",
        )


# ---------------------------------------------------------------------------
# A7-03: claim_value None + contradictory evidence → severity from SEVERITY table
# ---------------------------------------------------------------------------

class TestA703NoneValueConflict(unittest.TestCase):
    """A conflicting claim with claim_value=None must produce Q2 (not Q3).
    The severity must match the current table in the code (critical for
    deadline/contact/availability fields, warning for others)."""

    def test_none_value_conflict_on_deadline_gives_q2_critical(self):
        """Deadline field with conflicting + claim_value=None → Q2 critical."""
        needs = [_need("need_001")]
        claims = [{
            "program_id": "PROG-Y",
            "field_path": "deadlines[0]",
            "claim_value": None,
            "verification_status": "conflicting",
            "evidence_refs": ["EV-C1"],
            "checked_at": "2026-10-21T15:00:00Z",
            "issue": "Deadline not published on any source",
        }]
        matches = [_match("PROG-Y", ["need_001"])]
        stage_result = {"matches": matches, "checked_claims": claims}
        findings = _run7(stage_result, needs)
        non_info = [f for f in findings if f["severity"] != "info"]
        rule_ids = [f["rule_id"] for f in non_info]
        self.assertIn("Q2", rule_ids, f"Expected Q2 for None-value conflict; got {rule_ids}")
        self.assertNotIn("Q3", rule_ids, f"Q3 must not fire for None-value conflict")
        q2 = next(f for f in non_info if f["rule_id"] == "Q2")
        self.assertEqual(
            q2["severity"], "critical",
            f"Q2 on a deadline field must be critical per the SEVERITY table; got {q2['severity']}",
        )

    def test_none_value_conflict_on_non_critical_field_gives_q2_warning(self):
        """Non-critical field with conflicting + claim_value=None → Q2 warning."""
        needs = [_need("need_001")]
        claims = [{
            "program_id": "PROG-Z",
            "field_path": "income_limit[0]",
            "claim_value": None,
            "verification_status": "conflicting",
            "evidence_refs": ["EV-D1"],
            "checked_at": "2026-10-21T15:00:00Z",
            "issue": None,
        }]
        matches = [_match("PROG-Z", ["need_001"])]
        stage_result = {"matches": matches, "checked_claims": claims}
        findings = _run7(stage_result, needs)
        non_info = [f for f in findings if f["severity"] != "info"]
        rule_ids = [f["rule_id"] for f in non_info]
        self.assertIn("Q2", rule_ids, f"Expected Q2 for None-value conflict on non-critical field; got {rule_ids}")
        q2 = next(f for f in non_info if f["rule_id"] == "Q2")
        self.assertEqual(
            q2["severity"], "warning",
            f"Q2 on a non-critical field must be warning; got {q2['severity']}",
        )


# ---------------------------------------------------------------------------
# A10-02: False coverage – related_need_ids must match the original match's need_ids
# ---------------------------------------------------------------------------

class TestA1002FalseCoverage(unittest.TestCase):
    """A food card claiming need_housing in related_need_ids must flag V12."""

    def test_food_card_claiming_housing_need_fails(self):
        needs = [
            _need("need_food", category="food_assistance", subcategory="food_pantry"),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance"),
        ]
        matches = [_match("PROG-FOOD", ["need_food"], subcategory="food_pantry")]
        # Card incorrectly claims need_housing (which the food program does not serve).
        cards = [{
            "card_id": "CARD-001",
            "program_id": "PROG-FOOD",
            "action_title": "Visit a food pantry",
            "reason": "Food help",
            "next_step": "Visit during open hours.",
            "priority_reason": "Food is needed.",
            "order_group": "parallel",
            "dependency_card_ids": [],
            "source_refs": [],
            "uncertainty_notes": [],
            "official_deadline": None,
            "user_target_date": None,
            "processing_estimate": None,
            "progress_status": "not_started",
            "related_need_ids": ["need_food", "need_housing"],  # need_housing is wrong
            "contacts": [],
        }]
        plan = {"action_cards": cards, "potential_options": [], "coverage_gaps": []}
        result = _run10(plan, needs, matches,
                        availability={"PROG-FOOD": "confirmed_open"})
        v12_flags = [f for f in result["flags"] if f["rule_id"] == "V12"]
        self.assertGreater(len(v12_flags), 0,
                           "V12 must fire when a card's related_need_ids includes "
                           "a need the program does not match")
        self.assertFalse(result["verdict"] == "PASS",
                         "Verdict must not be PASS when false coverage is present")


# ---------------------------------------------------------------------------
# C-OD2: §15.2 overdue rent / eviction ordering
#         Overdue rent does NOT force housing first (rule 4).
#         Confirmed late legal stage (sheriff etc.) forces housing first (rule 3).
# ---------------------------------------------------------------------------

class TestCOD2OverdueRentFoodOrdering(unittest.TestCase):
    """§15.2 rules 3 & 4:
    - Overdue rent (past or today) does NOT place housing above food.
    - Confirmed late legal stage (sheriff, writ, court judgment) → housing first.
    - Without any signal the normal sort order applies.
    """

    def _make_needs_matches(self):
        needs = [
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency="immediate"),
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
        ]
        matches = [
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
        ]
        avail = [_open_avail("PROG-HOUSING"), _open_avail("PROG-FOOD")]
        return needs, matches, avail

    def test_overdue_rent_does_NOT_put_housing_first(self):
        """§15.2 rule 4: overdue rent (past rent_due_date) must NOT place housing
        above food.  Food stays first (or at least equal)."""
        needs, matches, avail = self._make_needs_matches()
        overdue_facts = [{"fact_id": "f1", "field": "rent_due_date",
                          "value": "2026-10-01",  # before ref_date → overdue
                          "confirmation_status": "confirmed",
                          "source": "user_statement", "time_context": None}]
        payload = {
            "needs": needs,
            "matches": [matches[1], matches[0]],  # food first in input
            "checked_claims": [],
            "program_availability": avail,
            "evidence_records": [],
            "timing": [],
            "case_facts": overdue_facts,
            "ref_date": "2026-11-01",
        }
        acts = handle(_req("agent_6", payload))["result"]["proposed_actions"]
        pids = [a["program_id"] for a in acts if a["program_id"]]
        housing_idx = pids.index("PROG-HOUSING")
        food_idx = pids.index("PROG-FOOD")
        # Overdue rent must NOT flip order; food stays first (or tied).
        self.assertLessEqual(
            food_idx, housing_idx,
            f"Overdue rent must not place housing before food (§15.2 rule 4); got {pids}",
        )

    def test_no_overdue_signal_does_not_force_housing_first(self):
        """Without any housing signal, housing does NOT jump ahead of food."""
        needs, matches, avail = self._make_needs_matches()
        # No case_facts with rent_due_date or notice fields → no overdue signal.
        acts = _run6(
            needs,
            [matches[1], matches[0]],  # food first in input
            program_availability=avail,
        )
        pids = [a["program_id"] for a in acts if a["program_id"]]
        # With equal urgency and no dates, order should follow input (stable sort).
        # The key assertion: housing must NOT be forced ahead of food.
        # (Both are "immediate" → both land in "first"; without the signal the
        #  sort key treats them equally, so input order is preserved.)
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        self.assertLess(
            food_idx, housing_idx,
            f"Without a housing signal, food-first input must stay food-first; got {pids}",
        )


# ---------------------------------------------------------------------------
# PR #13 Item 1: "no double periods" — a.m./p.m. must stay intact
# ---------------------------------------------------------------------------

class TestPR13Item1NoDoublePeriods(unittest.TestCase):
    """_strip_trailing_period must NOT strip the period that is part of 'a.m.' or 'p.m.'"""

    def test_strip_trailing_period_keeps_abbrev_period(self):
        """'8 a.m. to 5 p.m.' ends with 'p.m.' — the period must NOT be stripped."""
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _strip_trailing_period
        result = _strip_trailing_period("8 a.m. to 5 p.m.")
        self.assertEqual(result, "8 a.m. to 5 p.m.",
                         f"Abbreviation period was incorrectly stripped: {result!r}")

    def test_strip_trailing_period_strips_plain_sentence_period(self):
        """A sentence ending with a true period has the period stripped."""
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _strip_trailing_period
        result = _strip_trailing_period("Call during office hours.")
        self.assertEqual(result, "Call during office hours",
                         f"Plain sentence period was not stripped: {result!r}")

    def test_am_pm_sentence_no_double_period_in_next_step(self):
        """EDD example: contact value ending with 'p.m.' must not produce
        a double period '.. (checked' in next_step.
        The correct output is '... p.m. (checked Oct 22).' — one period from
        the abbreviation, space, then (checked ...).
        """
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _next_step_contacts
        # The value must contain a phone pattern so it is selected as the Contact snippet.
        contacts = [{
            "label": "Contact",
            "value": "Call 916-263-3750, Mon-Fri 8 a.m. to 5 p.m.",
            "hours": "8 a.m. to 5 p.m.",
            "checked_at": "2026-10-22",
            "evidence_refs": ["EV-AM1"],
        }]
        snippets = _next_step_contacts(contacts)
        self.assertEqual(len(snippets), 1, f"Expected 1 snippet; got {snippets!r}")
        sn = snippets[0]
        # Must NOT have a DOUBLE period before (checked …).
        self.assertNotIn(".. (checked", sn,
                         f"Double period found in snippet: {sn!r}")
        # The a.m. / p.m. abbreviations must be intact inside the snippet.
        self.assertIn("a.m.", sn, f"a.m. was mangled: {sn!r}")
        self.assertIn("p.m.", sn, f"p.m. was mangled: {sn!r}")
        # The snippet ends with exactly one final period.
        self.assertTrue(sn.endswith(")."), f"Snippet should end with ').' : {sn!r}")

    def test_plain_sentence_period_is_stripped(self):
        """A sentence ending with a true period must NOT produce a double period."""
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _next_step_contacts
        contacts = [{
            "label": "Contact",
            "value": "Call 916-875-5437.",
            "hours": None,
            "checked_at": "2026-10-22",
            "evidence_refs": ["EV-PL1"],
        }]
        snippets = _next_step_contacts(contacts)
        self.assertEqual(len(snippets), 1)
        sn = snippets[0]
        self.assertNotIn(". (checked", sn,
                         f"Double period found: {sn!r}")


# ---------------------------------------------------------------------------
# PR #13 Item 2: same phone in "How to apply" and "Contact" shown only once
# ---------------------------------------------------------------------------

class TestPR13Item2PhoneDedup(unittest.TestCase):
    """CalFresh 1-800-560-0976: if both How-to-apply and Contact carry the same
    phone number, it must appear in the next_step exactly once."""

    def _make_contacts(self, phone="1-800-560-0976"):
        return [
            {
                "label": "How to apply",
                "value": f"Apply by phone: {phone}",
                "hours": None,
                "checked_at": "2026-10-22",
                "evidence_refs": ["EV-CF1"],
            },
            {
                "label": "Contact",
                "value": f"Call {phone} for help.",
                "hours": None,
                "checked_at": "2026-10-22",
                "evidence_refs": ["EV-CF2"],
            },
        ]

    def test_same_phone_appears_once(self):
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _next_step_contacts
        contacts = self._make_contacts()
        snippets = _next_step_contacts(contacts)
        combined = " ".join(snippets)
        # Count occurrences of the phone number in the combined snippets.
        count = combined.count("1-800-560-0976")
        self.assertEqual(count, 1,
                         f"Phone appeared {count} times (expected 1): {combined!r}")

    def test_different_phones_both_appear(self):
        """When the phones differ, both snippets must be included."""
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _next_step_contacts
        contacts = [
            {
                "label": "How to apply",
                "value": "Apply by phone: 1-800-560-0976",
                "hours": None,
                "checked_at": "2026-10-22",
                "evidence_refs": ["EV-CF1"],
            },
            {
                "label": "Contact",
                "value": "Call 916-875-5437 for info.",
                "hours": None,
                "checked_at": "2026-10-22",
                "evidence_refs": ["EV-CF2"],
            },
        ]
        snippets = _next_step_contacts(contacts)
        self.assertEqual(len(snippets), 2,
                         f"Expected 2 snippets for different phones; got {snippets!r}")


# ---------------------------------------------------------------------------
# PR #13 Item 3: _subcategory (and any "_" key) must NOT appear in Agent 6 output
# ---------------------------------------------------------------------------

class TestPR13Item3NoPrivateKeys(unittest.TestCase):
    """Every action returned by Agent 6 must have exactly the contract 4.6 keys;
    no key starting with '_' is allowed."""

    _CONTRACT_KEYS = frozenset({
        "action_id", "need_id", "program_id", "suggested_priority",
        "order_group", "rationale", "dependency_ids", "official_deadline",
        "user_target_date", "estimated_processing_time", "evidence_refs",
        "uncertainty_notes", "user_override_allowed",
    })

    def test_no_private_keys_in_actions(self):
        needs = [
            _need("need_A", category="food_assistance", subcategory="food_pantry"),
            _need("need_B", category="housing_assistance", subcategory="rental_assistance"),
        ]
        matches = [
            _match("PROG-A", ["need_A"], subcategory="food_pantry"),
            _match("PROG-B", ["need_B"], subcategory="rental_assistance"),
        ]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        for a in acts:
            private = [k for k in a if k.startswith("_")]
            self.assertEqual(private, [],
                             f"Action {a['action_id']} has private keys: {private}")

    def test_action_keys_are_exactly_contract_keys(self):
        needs = [_need("need_A", category="food_assistance", subcategory="food_pantry")]
        matches = [_match("PROG-A", ["need_A"], subcategory="food_pantry")]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        for a in acts:
            extra = set(a) - self._CONTRACT_KEYS
            self.assertEqual(extra, set(),
                             f"Action {a['action_id']} has extra keys: {extra}")


# ---------------------------------------------------------------------------
# PR #13 Item 4: ref_date used; missing ref_date → issue added, no overdue decision
# ---------------------------------------------------------------------------

class TestPR13Item4RefDate(unittest.TestCase):
    """When ref_date is absent, Agent 6 must add a MISSING_REF_DATE issue and
    must NOT make any overdue / time-left decision."""

    def test_missing_ref_date_adds_issue(self):
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-A", ["need_A"], subcategory="rental_assistance")]
        # No ref_date in payload.
        payload = {
            "needs": needs,
            "matches": matches,
            "checked_claims": [],
            "program_availability": [_open_avail("PROG-A")],
            "evidence_records": [],
            "timing": [],
        }
        result = handle(_req("agent_6", payload))
        codes = [i["code"] for i in result["issues"]]
        self.assertIn("MISSING_REF_DATE", codes,
                      f"Expected MISSING_REF_DATE issue; got {codes}")

    def test_missing_ref_date_skips_overdue_housing_signal(self):
        """Without ref_date the MISSING_REF_DATE issue must be present and
        housing-first must not be activated by the overdue-rent logic.
        We verify by checking: both actions land in the same order_group and
        PROG-HOUSING does NOT have housing-first priority boosting."""
        needs = [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency="immediate"),
        ]
        matches = [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
        ]
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        # Sheriff-type notice in case_facts but NO ref_date → overdue logic must be skipped.
        # Without ref_date, even a late-stage eviction_notice_type must not trigger housing-first.
        facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                  "value": "Sheriff's notice to vacate",
                  "confirmation_status": "confirmed",
                  "source": "user_statement", "time_context": None}]
        payload = {
            "needs": needs,
            "matches": [matches[0], matches[1]],  # food first
            "checked_claims": [],
            "program_availability": avail,
            "evidence_records": [],
            "timing": [],
            "case_facts": facts,
            # no ref_date
        }
        result = handle(_req("agent_6", payload))
        # The MISSING_REF_DATE issue must appear.
        codes = [i["code"] for i in result["issues"]]
        self.assertIn("MISSING_REF_DATE", codes,
                      f"MISSING_REF_DATE issue must be present; got {codes}")
        # Without ref_date, both needs are "immediate" → both in "first" group.
        acts = result["result"]["proposed_actions"]
        for a in acts:
            if a.get("program_id"):
                self.assertEqual(a["order_group"], "first",
                                 f"{a['program_id']} must be in 'first' group for immediate urgency")

    def test_processing_time_note_skipped_without_ref_date(self):
        """Without ref_date, no 'processing time may exceed' note must appear."""
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-A", ["need_A"], subcategory="rental_assistance")]
        timing = [{"program_id": "PROG-A", "need_id": "need_A",
                   "official_deadline": None,
                   "user_target_date": "2026-11-05",
                   "estimated_processing_time": "30 days"}]
        # No ref_date → processing note must be skipped.
        acts = _run6(needs, matches, timing=timing)  # no ref_date
        for a in acts:
            for note in a.get("uncertainty_notes", []):
                self.assertNotIn("processing time", note.lower(),
                                 f"Processing-time note appeared without ref_date: {note!r}")


# ---------------------------------------------------------------------------
# PR #13 Item 5: ordering — eviction notice alone vs. sheriff in 2 days
# ---------------------------------------------------------------------------

class TestPR13Item5OrderingRules(unittest.TestCase):
    """§15.2 ordering tests:
    - food tomorrow + 30-day notice → food first
    - rent due today (not overdue) + food tomorrow → food first
    - sheriff in 2 days → housing first
    - utility shutoff notice alone → does NOT force housing first
    """

    def _needs_food_housing(self, food_urg="high", housing_urg="high"):
        return [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency=food_urg),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency=housing_urg),
        ]

    def _matches_food_housing(self):
        return [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
        ]

    def test_food_tomorrow_plus_30day_notice_puts_food_first(self):
        """food tomorrow + 30-day eviction notice (early stage) → food first.
        The notice type is known (30-day) so EVICTION_STAGE_UNKNOWN is NOT raised."""
        needs = self._needs_food_housing()
        matches = self._matches_food_housing()
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        ref = "2026-11-01"
        # 30-day notice: early stage — eviction_notice_type tells us the type.
        case_facts = [
            {"fact_id": "f1", "field": "has_written_eviction_notice",
             "value": True,
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
            {"fact_id": "f2", "field": "eviction_notice_type",
             "value": "30-day notice to vacate",
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        timing = [
            {"program_id": "PROG-FOOD", "need_id": "need_food",
             "official_deadline": None,
             "user_target_date": "2026-11-02",   # food tomorrow
             "estimated_processing_time": None},
        ]
        acts = _run6(needs, matches, program_availability=avail,
                     timing=timing, case_facts=case_facts, ref_date=ref)
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        self.assertLess(food_idx, housing_idx,
                        f"food tomorrow + 30-day notice: food must come first; got {pids}")

    def test_rent_due_today_not_overdue_no_housing_first_flag(self):
        """rent due today (ref_date == rent_due_date) must NOT trigger the housing-first flag.
        Verified by checking that neither action has order_group elevated from 'parallel'
        to 'first' by the overdue logic — both stay in their normal urgency group."""
        needs = self._needs_food_housing(food_urg="high", housing_urg="high")
        matches = self._matches_food_housing()
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        ref = "2026-11-01"
        # rent_due_date == ref_date → NOT overdue (strictly past means rd < today)
        case_facts = [
            {"fact_id": "f1", "field": "rent_due_date",
             "value": "2026-11-01",   # same as ref_date → not "strictly past"
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        acts = _run6(needs, matches, program_availability=avail,
                     case_facts=case_facts, ref_date=ref)
        # Both needs are "high" urgency → both should land in "parallel" group.
        # If housing-first triggered, the housing action would be in "first".
        # Verify housing is NOT in an elevated group relative to what its urgency warrants.
        housing_action = next(a for a in acts if a["program_id"] == "PROG-HOUSING")
        self.assertEqual(housing_action["order_group"], "parallel",
                         f"Rent due today must not elevate housing to 'first'; "
                         f"got {housing_action['order_group']}")

    def test_sheriff_in_2_days_puts_housing_first(self):
        """Sheriff notice (eviction_notice_type text) → housing first."""
        needs = self._needs_food_housing(food_urg="immediate", housing_urg="immediate")
        matches = self._matches_food_housing()
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        ref = "2026-11-01"
        case_facts = [
            {"fact_id": "f1", "field": "eviction_notice_type",
             "value": "Sheriff's notice to vacate",
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        # food first in input; sheriff must override to housing first
        acts = _run6(needs, [matches[0], matches[1]],
                     program_availability=avail,
                     case_facts=case_facts, ref_date=ref)
        pids = [a["program_id"] for a in acts if a["program_id"]]
        housing_idx = pids.index("PROG-HOUSING")
        food_idx = pids.index("PROG-FOOD")
        self.assertLess(housing_idx, food_idx,
                        f"Sheriff notice: housing must come first; got {pids}")

    def test_utility_shutoff_alone_does_not_force_housing_first(self):
        """Utility shutoff notice alone must NOT force housing before food."""
        needs = self._needs_food_housing(food_urg="immediate", housing_urg="immediate")
        matches = self._matches_food_housing()
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        ref = "2026-11-01"
        case_facts = [
            {"fact_id": "f1", "field": "utility_shutoff_notice",
             "value": True,
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        # food first in input; utility shutoff must NOT reorder
        acts = _run6(needs, [matches[0], matches[1]],
                     program_availability=avail,
                     case_facts=case_facts, ref_date=ref)
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        self.assertLessEqual(food_idx, housing_idx,
                             f"Utility shutoff alone must not force housing first; got {pids}")


# ---------------------------------------------------------------------------
# PR #13 Item 6 (revised §15.2 rule 5): user_priority must NOT change order_group
# ---------------------------------------------------------------------------

class TestPR13Item6UserPriority(unittest.TestCase):
    """§15.2 rule 5: need.user_priority must NOT change order_group or urgency.
    A 'high' urgency need with user_priority=1 stays in 'parallel' (its urgency
    group), not promoted to 'first'.  User preference is kept separate from
    action ordering."""

    def test_user_priority_1_does_not_change_order_group(self):
        """§15.2 rule 5: user_priority=1 on a 'high' urgency need must NOT
        promote it to 'first'; it stays in 'parallel'."""
        needs = [
            dict(_need("need_A", category="food_assistance",
                       subcategory="food_pantry", urgency="high"),
                 user_priority=1),
            _need("need_B", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        matches = [
            _match("PROG-A", ["need_A"], subcategory="food_pantry"),
            _match("PROG-B", ["need_B"], subcategory="rental_assistance"),
        ]
        avail = [_open_avail("PROG-A"), _open_avail("PROG-B")]
        acts = _run6(needs, matches, program_availability=avail, ref_date="2026-11-01")
        a_action = next(a for a in acts if a["program_id"] == "PROG-A")
        # 'high' urgency → 'parallel' group regardless of user_priority.
        self.assertEqual(a_action["order_group"], "parallel",
                         f"user_priority=1 must NOT promote 'high' urgency to 'first'; "
                         f"got {a_action['order_group']}")


# ---------------------------------------------------------------------------
# PR #13 Item 7: urgency wording — "Food is running low" only when immediate
# ---------------------------------------------------------------------------

class TestPR13Item7UrgencyWording(unittest.TestCase):
    """'Food is running low' must appear in the rationale only when urgency is
    'immediate'; for 'high' or 'normal' food needs, use neutral wording."""

    def test_food_immediate_urgency_has_urgency_wording(self):
        needs = [_need("need_food", category="food_assistance",
                       subcategory="food_pantry", urgency="immediate")]
        matches = [_match("PROG-FOOD", ["need_food"], subcategory="food_pantry")]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        rationale = next(a["rationale"] for a in acts if a["program_id"] == "PROG-FOOD")
        self.assertIn("Food is running low", rationale,
                      f"Immediate food urgency must include 'Food is running low': {rationale!r}")

    def test_food_high_urgency_no_urgency_wording(self):
        needs = [_need("need_food", category="food_assistance",
                       subcategory="food_pantry", urgency="high")]
        matches = [_match("PROG-FOOD", ["need_food"], subcategory="food_pantry")]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        rationale = next(a["rationale"] for a in acts if a["program_id"] == "PROG-FOOD")
        self.assertNotIn("Food is running low", rationale,
                         f"Non-immediate food must not say 'Food is running low': {rationale!r}")

    def test_calfresh_immediate_has_urgency_wording(self):
        needs = [_need("need_food", category="food_assistance",
                       subcategory="calfresh_benefits", urgency="immediate")]
        matches = [_match("PROG-CF", ["need_food"], subcategory="calfresh_benefits")]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        rationale = next(a["rationale"] for a in acts if a["program_id"] == "PROG-CF")
        self.assertIn("Food is running low", rationale,
                      f"Immediate calfresh must include urgency wording: {rationale!r}")

    def test_calfresh_high_urgency_no_running_low(self):
        needs = [_need("need_food", category="food_assistance",
                       subcategory="calfresh_benefits", urgency="high")]
        matches = [_match("PROG-CF", ["need_food"], subcategory="calfresh_benefits")]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        rationale = next(a["rationale"] for a in acts if a["program_id"] == "PROG-CF")
        self.assertNotIn("Food is running low", rationale,
                         f"Non-immediate calfresh must not say 'Food is running low': {rationale!r}")


# ---------------------------------------------------------------------------
# PR #13 Item 8: no action with program_id None in Agent 6 output
# ---------------------------------------------------------------------------

class TestPR13Item8NoFollowUpAction(unittest.TestCase):
    """The generic 'Follow up on your applications' action (program_id None)
    must not appear in Agent 6's proposed_actions."""

    def test_no_action_with_none_program_id(self):
        needs = [
            _need("need_A", category="food_assistance", subcategory="calfresh_benefits",
                  urgency="high"),
            _need("need_B", category="income_support",
                  subcategory="unemployment_insurance", urgency="high"),
        ]
        matches = [
            _match("PROG-CF", ["need_A"], subcategory="calfresh_benefits"),
            _match("PROG-UI", ["need_B"], subcategory="unemployment_insurance"),
        ]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        none_program = [a for a in acts if a.get("program_id") is None]
        self.assertEqual(none_program, [],
                         f"No action with program_id None should exist; got {none_program}")

    def test_agent_8_no_followup_card(self):
        """Agent 8 must not produce a 'Follow up' card (program_id None)."""
        needs = [
            _need("need_A", category="food_assistance", subcategory="calfresh_benefits",
                  urgency="high"),
        ]
        matches = [_match("PROG-CF", ["need_A"], subcategory="calfresh_benefits")]
        _, cards = _run6_and_8(needs, matches, ref_date="2026-11-01")
        followup_cards = [c for c in cards if c.get("program_id") is None]
        self.assertEqual(followup_cards, [],
                         f"Agent 8 must not produce a follow-up card; got {followup_cards}")


# ---------------------------------------------------------------------------
# PR #13 Item 9: no duplicate date in rationale
# ---------------------------------------------------------------------------

class TestPR13Item9NoDuplicateDate(unittest.TestCase):
    """The same formatted date must not appear twice in a single rationale."""

    def test_user_date_appears_at_most_once(self):
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-RA", ["need_A"], subcategory="rental_assistance")]
        timing = [{"program_id": "PROG-RA", "need_id": "need_A",
                   "official_deadline": None,
                   "user_target_date": "2026-11-01",
                   "estimated_processing_time": None}]
        acts = _run6(needs, matches, timing=timing, ref_date="2026-11-01")
        for a in acts:
            rationale = a.get("rationale", "")
            # "November 1" must appear at most once in the rationale.
            count = rationale.count("November 1")
            self.assertLessEqual(count, 1,
                                 f"Date 'November 1' appears {count} times in rationale: {rationale!r}")


# ---------------------------------------------------------------------------
# PR #13 Item 10: processing time unit parsing — "30 days" is 30 days
# ---------------------------------------------------------------------------

class TestPR13Item10ProcessingTimeUnit(unittest.TestCase):
    """'30 days' must be parsed as 30 days, not 30*7=210 days."""

    def test_30_days_does_not_warn_when_32_days_available(self):
        """30-day processing time + user date 32 days away → no warning note."""
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-RA", ["need_A"], subcategory="rental_assistance")]
        ref = "2026-11-01"
        # target date is 32 days after ref_date → 30 days processing fits
        timing = [{"program_id": "PROG-RA", "need_id": "need_A",
                   "official_deadline": None,
                   "user_target_date": "2026-12-03",  # 32 days after 2026-11-01
                   "estimated_processing_time": "30 days"}]
        acts = _run6(needs, matches, timing=timing, ref_date=ref)
        for a in acts:
            for note in a.get("uncertainty_notes", []):
                self.assertNotIn("processing time", note.lower(),
                                 f"30-day processing with 32 days available should not warn: {note!r}")

    def test_30_days_warns_when_only_20_days_available(self):
        """30-day processing time + only 20 days left → warning note."""
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-RA", ["need_A"], subcategory="rental_assistance")]
        ref = "2026-11-01"
        # target date is only 20 days away
        timing = [{"program_id": "PROG-RA", "need_id": "need_A",
                   "official_deadline": None,
                   "user_target_date": "2026-11-21",  # 20 days after 2026-11-01
                   "estimated_processing_time": "30 days"}]
        acts = _run6(needs, matches, timing=timing, ref_date=ref)
        found_note = False
        for a in acts:
            for note in a.get("uncertainty_notes", []):
                if "processing time" in note.lower():
                    found_note = True
        self.assertTrue(found_note,
                        "30-day processing time with only 20 days left must produce a warning note")

    def test_4_weeks_parses_as_28_days(self):
        """'4 weeks' must be parsed as 28 days (not 4 days)."""
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _parse_processing_days
        self.assertEqual(_parse_processing_days("4 weeks"), 28)

    def test_30_days_parses_as_30(self):
        """'30 days' must be parsed as 30 days."""
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _parse_processing_days
        self.assertEqual(_parse_processing_days("30 days"), 30)

    def test_2_months_parses_as_60(self):
        """'2 months' must be parsed as 60 days."""
        from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import _parse_processing_days
        self.assertEqual(_parse_processing_days("2 months"), 60)


# ---------------------------------------------------------------------------
# PR #13 Item 11: Agent 8 dependency_card_ids valid + notes merged; Agent 10 flags missing
# ---------------------------------------------------------------------------

class TestPR13Item11DependencyCardIds(unittest.TestCase):
    """Agent 8: every dependency_card_id must point to a card that exists;
    merged card keeps uncertainty notes from all its actions.
    Agent 10: flags dependency_card_ids pointing to a missing card."""

    def test_agent8_no_dangling_dependency_card_ids(self):
        """All dependency_card_ids in Agent 8 output must point to existing cards."""
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-RA", ["need_A"], subcategory="rental_assistance")]
        # Conflicting deadlines force a confirm action with a dependency.
        claims = [
            {"program_id": "PROG-RA", "field_path": "deadlines[0]",
             "claim_value": "2026-11-04", "verification_status": "verified",
             "evidence_refs": ["EV-X1"], "checked_at": "2026-10-21T15:00:00Z",
             "issue": None},
            {"program_id": "PROG-RA", "field_path": "deadlines[0]",
             "claim_value": "2026-12-10", "verification_status": "verified",
             "evidence_refs": ["EV-X2"], "checked_at": "2026-10-21T15:00:00Z",
             "issue": None},
        ]
        ev = [{"evidence_id": "EV-X1", "program_id": "PROG-RA",
               "field_path": "deadlines[0]", "claim_value": "2026-11-04",
               "source_url": "", "checked_at": "2026-10-21T15:00:00Z",
               "verification_status": "verified"},
              {"evidence_id": "EV-X2", "program_id": "PROG-RA",
               "field_path": "deadlines[0]", "claim_value": "2026-12-10",
               "source_url": "", "checked_at": "2026-10-21T15:00:00Z",
               "verification_status": "verified"}]
        _, cards = _run6_and_8(needs, matches, checked_claims=claims,
                               evidence_records=ev, ref_date="2026-11-01")
        card_ids = {c["card_id"] for c in cards}
        for c in cards:
            for dep in c.get("dependency_card_ids", []):
                self.assertIn(dep, card_ids,
                              f"Card {c['card_id']} has dangling dep {dep}; "
                              f"existing cards: {card_ids}")

    def test_agent8_merged_card_keeps_notes_from_all_actions(self):
        """When a program covers two needs, the merged card must carry
        uncertainty notes from both actions."""
        needs = [
            _need("need_A", category="food_assistance", subcategory="food_pantry"),
            _need("need_B", category="food_assistance", subcategory="calfresh_benefits"),
        ]
        matches = [_match("PROG-MULTI", ["need_A", "need_B"], subcategory="food_pantry")]
        # Add a missing_case_facts that produces an uncertainty note for each action.
        matches[0]["missing_case_facts"] = ["current_monthly_income"]
        _, cards = _run6_and_8(needs, matches, ref_date="2026-11-01")
        self.assertEqual(len(cards), 1, f"Expected 1 merged card; got {len(cards)}")
        notes = cards[0]["uncertainty_notes"]
        # At least one note should mention income.
        self.assertTrue(any("income" in n.lower() for n in notes),
                        f"Merged card must include income uncertainty note; got {notes}")

    def test_agent10_flags_missing_dependency_card(self):
        """Agent 10 must flag V12 when dependency_card_ids points to a non-existent card."""
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance")]
        matches = [_match("PROG-RA", ["need_A"], subcategory="rental_assistance")]
        cards = [{
            "card_id": "card_01",
            "program_id": "PROG-RA",
            "action_title": "Ask about rent help",
            "reason": "Offers rental assistance.",
            "next_step": "Contact the provider.",
            "priority_reason": "Acting early helps.",
            "order_group": "first",
            "dependency_card_ids": ["card_99"],  # does not exist
            "source_refs": [],
            "uncertainty_notes": [],
            "official_deadline": None,
            "user_target_date": None,
            "processing_estimate": None,
            "progress_status": "not_started",
            "related_need_ids": ["need_A"],
            "contacts": [],
        }]
        plan = {"action_cards": cards, "potential_options": [], "coverage_gaps": []}
        result = _run10(plan, needs, matches, availability={"PROG-RA": "confirmed_open"})
        v12_flags = [f for f in result["flags"] if f["rule_id"] == "V12"
                     and "dependency" in f["reason"].lower()]
        self.assertGreater(len(v12_flags), 0,
                           f"V12 must fire for missing dependency_card_ids; flags: {result['flags']}")


# ---------------------------------------------------------------------------
# PR #13 Item 12: A6-05 "Use an open option first" only when open option exists
# ---------------------------------------------------------------------------

class TestPR13Item12OpenOptionFirst(unittest.TestCase):
    """When a program is temporarily closed and there is NO open alternative for
    the same need, the rationale must NOT say 'Use an open option first.'"""

    def _closed_avail(self, program_id, reopen_date="2026-12-01"):
        return [{"program_id": program_id, "availability": "temporarily_closed",
                 "evidence_refs": []}]

    def test_no_open_option_means_no_open_option_wording(self):
        """Single closed program for a need → no 'Use an open option first'."""
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-CLOSED", ["need_A"], subcategory="rental_assistance")]
        avail = self._closed_avail("PROG-CLOSED")
        ev = [{"evidence_id": "EV-RO1", "program_id": "PROG-CLOSED",
               "field_path": "availability.reopen_date",
               "claim_value": "2026-12-01",
               "source_url": "", "checked_at": "2026-10-21T15:00:00Z",
               "verification_status": "verified",
               "effective_date": "2026-12-01"}]
        acts = _run6(needs, matches, program_availability=avail,
                     evidence_records=ev, ref_date="2026-11-01")
        for a in acts:
            rationale = a.get("rationale", "")
            self.assertNotIn("Use an open option first", rationale,
                             f"No open alternative — must not say 'Use an open option first': {rationale!r}")

    def test_open_option_exists_wording_appears(self):
        """Closed program + open alternative for the same need → 'Use an open option first'."""
        needs = [_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [
            _match("PROG-CLOSED", ["need_A"], subcategory="rental_assistance"),
            _match("PROG-OPEN", ["need_A"], subcategory="rental_assistance"),
        ]
        avail = [
            {"program_id": "PROG-CLOSED", "availability": "temporarily_closed",
             "evidence_refs": []},
            _open_avail("PROG-OPEN"),
        ]
        ev = [{"evidence_id": "EV-RO2", "program_id": "PROG-CLOSED",
               "field_path": "availability.reopen_date",
               "claim_value": "2026-12-01",
               "source_url": "", "checked_at": "2026-10-21T15:00:00Z",
               "verification_status": "verified",
               "effective_date": "2026-12-01"}]
        acts = _run6(needs, matches, program_availability=avail,
                     evidence_records=ev, ref_date="2026-11-01")
        closed_action = next((a for a in acts if a["program_id"] == "PROG-CLOSED"), None)
        self.assertIsNotNone(closed_action, "Expected a PROG-CLOSED action")
        self.assertIn("Use an open option first", closed_action["rationale"],
                      f"Open alternative exists — must say 'Use an open option first': "
                      f"{closed_action['rationale']!r}")


# ---------------------------------------------------------------------------
# §15.2 New tests: undated notice + food tomorrow keeps food first + EVICTION_STAGE_UNKNOWN
# ---------------------------------------------------------------------------

class TestEvictionStageUnknown(unittest.TestCase):
    """§15.2 rule 2: eviction notice with no date or unknown stage must NOT put
    housing first; Agent 6 must raise EVICTION_STAGE_UNKNOWN (warning) and order
    the housing action as a normal need."""

    def _needs_food_housing(self, food_urg="immediate", housing_urg="high"):
        return [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency=food_urg),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency=housing_urg),
        ]

    def _matches_food_housing(self):
        return [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
        ]

    def test_undated_notice_plus_food_tomorrow_keeps_food_first(self):
        """§15.2 rule 2: eviction notice with no date + food running out tomorrow
        must keep food at least equal to housing and raise EVICTION_STAGE_UNKNOWN."""
        needs = self._needs_food_housing(food_urg="immediate", housing_urg="high")
        matches = self._matches_food_housing()
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        case_facts = [
            {"fact_id": "f1", "field": "has_written_eviction_notice",
             "value": True,   # notice exists but no eviction_date
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        timing = [
            {"program_id": "PROG-FOOD", "need_id": "need_food",
             "official_deadline": None,
             "user_target_date": "2026-11-02",   # food tomorrow
             "estimated_processing_time": None},
        ]
        result = handle(_req("agent_6", {
            "needs": needs,
            "matches": [matches[0], matches[1]],
            "checked_claims": [],
            "program_availability": avail,
            "evidence_records": [],
            "timing": timing,
            "case_facts": case_facts,
            "ref_date": "2026-11-01",
        }))
        acts = result["result"]["proposed_actions"]
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        # Food must stay first (or tied) — undated notice must NOT override food urgency.
        self.assertLessEqual(food_idx, housing_idx,
                             f"Undated notice + food tomorrow: food must stay first; got {pids}")
        # EVICTION_STAGE_UNKNOWN issue must be raised.
        codes = [i["code"] for i in result["issues"]]
        self.assertIn("EVICTION_STAGE_UNKNOWN", codes,
                      f"Expected EVICTION_STAGE_UNKNOWN issue; got {codes}")

    def test_undated_notice_raises_eviction_stage_unknown(self):
        """§15.2 rule 2: any eviction notice without confirmed late stage raises
        EVICTION_STAGE_UNKNOWN asking for notice type, date, court case, judgment."""
        needs = self._needs_food_housing()
        matches = self._matches_food_housing()
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        case_facts = [
            {"fact_id": "f1", "field": "has_written_eviction_notice",
             "value": True,
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        result = handle(_req("agent_6", {
            "needs": needs,
            "matches": [matches[0], matches[1]],
            "checked_claims": [],
            "program_availability": avail,
            "evidence_records": [],
            "timing": [],
            "case_facts": case_facts,
            "ref_date": "2026-11-01",
        }))
        codes = [i["code"] for i in result["issues"]]
        self.assertIn("EVICTION_STAGE_UNKNOWN", codes,
                      f"Expected EVICTION_STAGE_UNKNOWN for undated notice; got {codes}")
        # The issue message must ask the Supervisor for clarification details.
        ev_issue = next(i for i in result["issues"] if i["code"] == "EVICTION_STAGE_UNKNOWN")
        msg = ev_issue["message"].lower()
        self.assertIn("notice type", msg,
                      f"Issue message must mention 'notice type': {msg!r}")
        self.assertIn("court", msg,
                      f"Issue message must mention 'court': {msg!r}")


# ---------------------------------------------------------------------------
# §15.2 New: 3-day notice (early stage) + food tomorrow keeps food first
# ---------------------------------------------------------------------------

class TestEarlyStageEvictionFoodFirst(unittest.TestCase):
    """§15.2: a 3-day pay-or-quit notice (early eviction stage) + food
    running out tomorrow must keep food first, NOT trigger housing-first,
    and must NOT raise EVICTION_STAGE_UNKNOWN (type is known)."""

    def test_3day_notice_early_stage_food_first(self):
        """eviction_notice_type '3-day pay or quit' + food tomorrow → food stays first,
        no EVICTION_STAGE_UNKNOWN (type is present)."""
        needs = [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        matches = [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
        ]
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        # 3-day pay-or-quit: early stage — type is known, not a late stage keyword.
        case_facts = [
            {"fact_id": "f1", "field": "has_written_eviction_notice",
             "value": True,
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
            {"fact_id": "f2", "field": "eviction_notice_type",
             "value": "3-day pay or quit",
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        timing = [
            {"program_id": "PROG-FOOD", "need_id": "need_food",
             "official_deadline": None,
             "user_target_date": "2026-11-02",   # food tomorrow
             "estimated_processing_time": None},
        ]
        result = handle(_req("agent_6", {
            "needs": needs,
            "matches": [matches[0], matches[1]],
            "checked_claims": [],
            "program_availability": avail,
            "evidence_records": [],
            "timing": timing,
            "case_facts": case_facts,
            "ref_date": "2026-11-01",
        }))
        acts = result["result"]["proposed_actions"]
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        # food is "immediate" → "first" group; housing is "high" → "parallel".
        self.assertLess(food_idx, housing_idx,
                        f"3-day pay-or-quit + food tomorrow: food must stay first; got {pids}")
        # eviction_notice_type is present → no EVICTION_STAGE_UNKNOWN
        codes = [i["code"] for i in result["issues"]]
        self.assertNotIn("EVICTION_STAGE_UNKNOWN", codes,
                         f"3-day notice type is known — must not raise EVICTION_STAGE_UNKNOWN; got {codes}")


# ---------------------------------------------------------------------------
# §15.2 New: sheriff/lockout notice puts emergency shelter and legal help first
# ---------------------------------------------------------------------------

class TestSheriffLockoutShelterLegalFirst(unittest.TestCase):
    """§15.2 rule 3: a sheriff/lockout notice must put emergency shelter and
    housing legal aid first (not rental assistance), and mark them as not
    guaranteed."""

    def test_sheriff_notice_shelter_legal_first_not_rental(self):
        """eviction_notice_type 'Sheriff's notice to vacate, lockout Nov 11' →
        emergency_shelter and housing_legal_aid go first (not rental assistance).
        Help is not guaranteed (uncertainty note on shelter/legal).
        No EVICTION_STAGE_UNKNOWN (type is known)."""
        needs = [
            _need("need_shelter", category="housing_assistance",
                  subcategory="emergency_shelter", urgency="immediate"),
            _need("need_legal", category="housing_assistance",
                  subcategory="housing_legal_aid", urgency="immediate"),
            _need("need_rental", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        matches = [
            _match("PROG-SHELTER", ["need_shelter"], subcategory="emergency_shelter"),
            _match("PROG-LEGAL", ["need_legal"], subcategory="housing_legal_aid"),
            _match("PROG-RENTAL", ["need_rental"], subcategory="rental_assistance"),
        ]
        avail = [_open_avail("PROG-SHELTER"), _open_avail("PROG-LEGAL"), _open_avail("PROG-RENTAL")]
        case_facts = [
            {"fact_id": "f1", "field": "eviction_notice_type",
             "value": "Sheriff's notice to vacate, lockout Nov 11",
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        result = handle(_req("agent_6", {
            "needs": needs,
            "matches": [matches[2], matches[1], matches[0]],  # rental first in input
            "checked_claims": [],
            "program_availability": avail,
            "evidence_records": [],
            "timing": [],
            "case_facts": case_facts,
            "ref_date": "2026-11-01",
        }))
        acts = result["result"]["proposed_actions"]
        pids = [a["program_id"] for a in acts if a["program_id"]]
        shelter_idx = pids.index("PROG-SHELTER")
        legal_idx = pids.index("PROG-LEGAL")
        rental_idx = pids.index("PROG-RENTAL")
        # shelter and legal must come before rental
        self.assertLess(shelter_idx, rental_idx,
                        f"Sheriff notice: PROG-SHELTER must precede PROG-RENTAL; got {pids}")
        self.assertLess(legal_idx, rental_idx,
                        f"Sheriff notice: PROG-LEGAL must precede PROG-RENTAL; got {pids}")
        # emergency shelter action must carry a "not guaranteed" uncertainty note
        shelter_action = next(a for a in acts if a["program_id"] == "PROG-SHELTER")
        notes_text = " ".join(shelter_action.get("uncertainty_notes", []))
        self.assertIn("not guaranteed", notes_text,
                      f"Shelter action must say help is not guaranteed; got notes: {notes_text!r}")
        # eviction_notice_type is present → no EVICTION_STAGE_UNKNOWN
        codes = [i["code"] for i in result["issues"]]
        self.assertNotIn("EVICTION_STAGE_UNKNOWN", codes,
                         f"Type is known — must not raise EVICTION_STAGE_UNKNOWN; got {codes}")


# ---------------------------------------------------------------------------
# §15.2 New: rent due today + food tomorrow does not put rent first
# ---------------------------------------------------------------------------

class TestRentDueTodayFoodNotDisplaced(unittest.TestCase):
    """§15.2 rule 4: rent due today (ref_date == rent_due_date) plus food running
    out tomorrow must NOT list rent first.  Food stays at least equal."""

    def test_rent_due_today_food_tomorrow_food_not_displaced(self):
        """Rent due today + food tomorrow: food must appear before or equal to housing."""
        needs = [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        matches = [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
        ]
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        case_facts = [
            {"fact_id": "f1", "field": "rent_due_date",
             "value": "2026-11-01",   # same as ref_date → due today, NOT overdue
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        timing = [
            {"program_id": "PROG-FOOD", "need_id": "need_food",
             "official_deadline": None,
             "user_target_date": "2026-11-02",   # food tomorrow
             "estimated_processing_time": None},
        ]
        acts = _run6(
            needs, [matches[0], matches[1]],
            program_availability=avail,
            timing=timing,
            case_facts=case_facts,
            ref_date="2026-11-01",
        )
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        # food (immediate) → "first" group; housing (high) → "parallel".
        # Rent due today must not elevate housing above food.
        self.assertLess(food_idx, housing_idx,
                        f"Rent due today + food tomorrow: food must not be displaced; got {pids}")


# ---------------------------------------------------------------------------
# §15.2 New: user_priority=1 does not change order_group (standalone)
# ---------------------------------------------------------------------------

class TestUserPriorityDoesNotChangeOrderGroup(unittest.TestCase):
    """§15.2 rule 5 (standalone): user_priority=1 must never change order_group.
    A 'high' urgency need with user_priority=1 stays in 'parallel'.
    An 'immediate' urgency need is in 'first' purely because of urgency, not priority."""

    def test_priority_1_high_urgency_stays_parallel(self):
        """user_priority=1 + urgency 'high' → order_group must be 'parallel'."""
        needs = [
            dict(_need("need_A", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high"),
                 user_priority=1),
        ]
        matches = [_match("PROG-A", ["need_A"], subcategory="rental_assistance")]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        action = next(a for a in acts if a["program_id"] == "PROG-A")
        self.assertEqual(action["order_group"], "parallel",
                         f"user_priority=1 must not change 'high' urgency group to 'first'; "
                         f"got {action['order_group']}")

    def test_priority_1_immediate_urgency_is_first_due_to_urgency(self):
        """user_priority=1 + urgency 'immediate' → 'first' because of urgency, not priority."""
        needs = [
            dict(_need("need_A", category="food_assistance",
                       subcategory="food_pantry", urgency="immediate"),
                 user_priority=1),
            _need("need_B", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        matches = [
            _match("PROG-A", ["need_A"], subcategory="food_pantry"),
            _match("PROG-B", ["need_B"], subcategory="rental_assistance"),
        ]
        acts = _run6(needs, matches, ref_date="2026-11-01")
        a_action = next(a for a in acts if a["program_id"] == "PROG-A")
        b_action = next(a for a in acts if a["program_id"] == "PROG-B")
        # A is first due to urgency; B is parallel due to urgency.
        self.assertEqual(a_action["order_group"], "first",
                         f"Immediate urgency must be 'first': {a_action['order_group']}")
        self.assertEqual(b_action["order_group"], "parallel",
                         f"High urgency must be 'parallel': {b_action['order_group']}")


# ---------------------------------------------------------------------------
# §15.2 Follow-up: three required new scenarios
# ---------------------------------------------------------------------------

class TestFollowUpNewScenarios(unittest.TestCase):
    """Three new test scenarios required by the §15.2 follow-up:
    1. eviction_notice_type 'Sheriff's notice to vacate, lockout Nov 11' → shelter/legal
       first with not-guaranteed note, no EVICTION_STAGE_UNKNOWN.
    2. eviction_notice_type '3-day pay or quit' → food first, no EVICTION_STAGE_UNKNOWN.
    3. rent_due_date Dec 1 shows as user_target_date on housing card, does not reorder
       ahead of food.
    """

    def test_sheriff_notice_type_shelter_legal_first_no_unknown_issue(self):
        """§15.2 follow-up scenario 1: eviction_notice_type 'Sheriff's notice to vacate,
        lockout Nov 11' puts shelter/legal first with not-guaranteed note.
        No EVICTION_STAGE_UNKNOWN (type is known)."""
        needs = [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
            _need("need_shelter", category="housing_assistance",
                  subcategory="emergency_shelter", urgency="immediate"),
            _need("need_legal", category="housing_assistance",
                  subcategory="housing_legal_aid", urgency="immediate"),
        ]
        matches = [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-SHELTER", ["need_shelter"], subcategory="emergency_shelter"),
            _match("PROG-LEGAL", ["need_legal"], subcategory="housing_legal_aid"),
        ]
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-SHELTER"), _open_avail("PROG-LEGAL")]
        case_facts = [
            {"fact_id": "f1", "field": "eviction_notice_type",
             "value": "Sheriff's notice to vacate, lockout Nov 11",
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        result = handle(_req("agent_6", {
            "needs": needs,
            "matches": [matches[0], matches[1], matches[2]],  # food first in input
            "checked_claims": [],
            "program_availability": avail,
            "evidence_records": [],
            "timing": [],
            "case_facts": case_facts,
            "ref_date": "2026-11-01",
        }))
        acts = result["result"]["proposed_actions"]
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        shelter_idx = pids.index("PROG-SHELTER")
        legal_idx = pids.index("PROG-LEGAL")
        # shelter and legal must come before food (late-stage housing-first)
        self.assertLess(shelter_idx, food_idx,
                        f"Sheriff notice type: shelter must precede food; got {pids}")
        self.assertLess(legal_idx, food_idx,
                        f"Sheriff notice type: legal must precede food; got {pids}")
        # shelter must carry a not-guaranteed note
        shelter_action = next(a for a in acts if a["program_id"] == "PROG-SHELTER")
        notes_text = " ".join(shelter_action.get("uncertainty_notes", []))
        self.assertIn("not guaranteed", notes_text,
                      f"Shelter action must say help not guaranteed; notes: {notes_text!r}")
        # no EVICTION_STAGE_UNKNOWN — type is known
        codes = [i["code"] for i in result["issues"]]
        self.assertNotIn("EVICTION_STAGE_UNKNOWN", codes,
                         f"Type is known — no EVICTION_STAGE_UNKNOWN; got {codes}")

    def test_3day_pay_or_quit_food_first_no_unknown_issue(self):
        """§15.2 follow-up scenario 2: eviction_notice_type '3-day pay or quit' +
        food tomorrow → food stays first (early stage, not late stage).
        No EVICTION_STAGE_UNKNOWN (type is present)."""
        needs = [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        matches = [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
        ]
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        case_facts = [
            {"fact_id": "f1", "field": "has_written_eviction_notice",
             "value": True,
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
            {"fact_id": "f2", "field": "eviction_notice_type",
             "value": "3-day pay or quit",
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        timing = [
            {"program_id": "PROG-FOOD", "need_id": "need_food",
             "official_deadline": None,
             "user_target_date": "2026-11-02",   # food tomorrow
             "estimated_processing_time": None},
        ]
        result = handle(_req("agent_6", {
            "needs": needs,
            "matches": [matches[0], matches[1]],
            "checked_claims": [],
            "program_availability": avail,
            "evidence_records": [],
            "timing": timing,
            "case_facts": case_facts,
            "ref_date": "2026-11-01",
        }))
        acts = result["result"]["proposed_actions"]
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        # food (immediate → first group) must stay before housing (high → parallel)
        self.assertLess(food_idx, housing_idx,
                        f"3-day pay or quit + food tomorrow: food must stay first; got {pids}")
        # no EVICTION_STAGE_UNKNOWN — type is present
        codes = [i["code"] for i in result["issues"]]
        self.assertNotIn("EVICTION_STAGE_UNKNOWN", codes,
                         f"Type is known — no EVICTION_STAGE_UNKNOWN; got {codes}")

    def test_rent_due_dec1_shows_as_user_target_date_does_not_reorder(self):
        """§15.2 follow-up scenario 3: rent_due_date Dec 1 must appear as
        user_target_date on the housing action card but must NOT reorder the
        housing action ahead of food (food urgency 'immediate', housing 'high')."""
        needs = [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        matches = [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
        ]
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        case_facts = [
            {"fact_id": "f1", "field": "rent_due_date",
             "value": "2026-12-01",
             "confirmation_status": "confirmed",
             "source": "user_statement", "time_context": None},
        ]
        acts = _run6(
            needs, [matches[0], matches[1]],
            program_availability=avail,
            case_facts=case_facts,
            ref_date="2026-11-01",
        )
        housing_action = next(a for a in acts if a["program_id"] == "PROG-HOUSING")
        food_action = next(a for a in acts if a["program_id"] == "PROG-FOOD")
        # rent_due_date must appear as user_target_date on the housing card
        self.assertEqual(housing_action["user_target_date"], "2026-12-01",
                         f"rent_due_date must be set as user_target_date; "
                         f"got {housing_action['user_target_date']!r}")
        # food (immediate) must still come before housing (high) in the list
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        self.assertLess(food_idx, housing_idx,
                        f"rent_due_date Dec 1 must not reorder housing before food; got {pids}")


# ---------------------------------------------------------------------------
# Follow-up: rent "was due" vs "is due" and emergency_shelter neutral wording
# ---------------------------------------------------------------------------

class TestRentDueWording(unittest.TestCase):
    """rent_due_date before ref_date → 'was due'; on or after ref_date → 'is due'."""

    def _housing_action(self, rent_due_date, ref_date):
        needs = [_need("need_h", category="housing_assistance",
                       subcategory="rental_assistance", urgency="high")]
        matches = [_match("PROG-H", ["need_h"], subcategory="rental_assistance")]
        case_facts = [{"fact_id": "f1", "field": "rent_due_date",
                       "value": rent_due_date,
                       "confirmation_status": "confirmed",
                       "source": "user_statement", "time_context": None}]
        acts = _run6(needs, matches, case_facts=case_facts, ref_date=ref_date)
        return next(a for a in acts if a["program_id"] == "PROG-H")

    def test_rent_overdue_says_was_due(self):
        """rent_due_date strictly before ref_date → rationale says 'was due'."""
        a = self._housing_action("2026-10-01", "2026-11-01")
        self.assertIn("was due", a["rationale"],
                      f"Overdue rent must say 'was due'; rationale: {a['rationale']!r}")
        self.assertNotIn("is due", a["rationale"],
                         f"Overdue rent must not say 'is due'; rationale: {a['rationale']!r}")

    def test_rent_due_today_says_is_due(self):
        """rent_due_date == ref_date (today) → rationale says 'is due'."""
        a = self._housing_action("2026-11-01", "2026-11-01")
        self.assertIn("is due", a["rationale"],
                      f"Rent due today must say 'is due'; rationale: {a['rationale']!r}")
        self.assertNotIn("was due", a["rationale"],
                         f"Rent due today must not say 'was due'; rationale: {a['rationale']!r}")

    def test_rent_due_future_says_is_due(self):
        """rent_due_date after ref_date (future) → rationale says 'is due'."""
        a = self._housing_action("2026-12-01", "2026-11-01")
        self.assertIn("is due", a["rationale"],
                      f"Future rent date must say 'is due'; rationale: {a['rationale']!r}")
        self.assertNotIn("was due", a["rationale"],
                         f"Future rent date must not say 'was due'; rationale: {a['rationale']!r}")


class TestEmergencyShelterWording(unittest.TestCase):
    """emergency_shelter rationale 'comes first' only on confirmed late legal stage.
    Neutral wording when stage is unknown or no housing signal."""

    def _shelter_rationale(self, case_facts, ref_date="2026-11-01"):
        needs = [_need("need_s", category="housing_assistance",
                       subcategory="emergency_shelter", urgency="immediate")]
        matches = [_match("PROG-S", ["need_s"], subcategory="emergency_shelter")]
        acts = _run6(needs, matches, case_facts=case_facts, ref_date=ref_date)
        return next(a for a in acts if a["program_id"] == "PROG-S")["rationale"]

    def test_undated_notice_shelter_uses_neutral_wording(self):
        """has_written_eviction_notice=True (no eviction_notice_type) + shelter match
        must NOT say 'comes first'; neutral wording required."""
        case_facts = [{"fact_id": "f1", "field": "has_written_eviction_notice",
                       "value": True, "confirmation_status": "confirmed",
                       "source": "user_statement", "time_context": None}]
        rationale = self._shelter_rationale(case_facts)
        self.assertNotIn("comes first", rationale,
                         f"Undated notice: shelter must not say 'comes first'; got {rationale!r}")
        self.assertIn("not guaranteed", rationale,
                      f"Neutral shelter wording must mention 'not guaranteed'; got {rationale!r}")

    def test_no_housing_signal_shelter_uses_neutral_wording(self):
        """No housing signal at all → neutral wording on emergency_shelter action."""
        rationale = self._shelter_rationale([])
        self.assertNotIn("comes first", rationale,
                         f"No signal: shelter must not say 'comes first'; got {rationale!r}")

    def test_confirmed_late_stage_shelter_says_comes_first(self):
        """Confirmed late legal stage (sheriff notice type) → shelter rationale
        says 'comes first' and carries not-guaranteed note."""
        case_facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                       "value": "Sheriff's notice to vacate",
                       "confirmation_status": "confirmed",
                       "source": "user_statement", "time_context": None}]
        rationale = self._shelter_rationale(case_facts)
        self.assertIn("comes first", rationale,
                      f"Sheriff notice: shelter must say 'comes first'; got {rationale!r}")


# ---------------------------------------------------------------------------
# TD 20.5 H3: date in eviction_notice_type → user_target_date on housing actions
# ---------------------------------------------------------------------------

class TestNoticeTypeDateAsUserTargetDate(unittest.TestCase):
    """TD 20.5 H3: when eviction_notice_type contains a date (e.g. 'sheriff lockout Nov 11'),
    that date becomes user_target_date on housing actions (user-stated, never official_deadline),
    and is mentioned once in the rationale as 'The date you gave is …'.
    The date must NOT reorder housing before food."""

    def _run_with_notice_type(self, notice_type_value, ref_date="2026-11-01"):
        needs = [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
            _need("need_shelter", category="housing_assistance",
                  subcategory="emergency_shelter", urgency="immediate"),
        ]
        matches = [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-SHELTER", ["need_shelter"], subcategory="emergency_shelter"),
        ]
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-SHELTER")]
        case_facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                       "value": notice_type_value,
                       "confirmation_status": "confirmed",
                       "source": "user_statement", "time_context": None}]
        acts = _run6(needs, [matches[0], matches[1]],
                     program_availability=avail, case_facts=case_facts, ref_date=ref_date)
        return acts

    def test_writ_with_nov11_sets_user_target_date(self):
        """'Writ of possession, sheriff lockout Nov 11' → shelter action has
        user_target_date 2026-11-11 and rationale mentions 'The date you gave'."""
        acts = self._run_with_notice_type("Writ of possession, sheriff lockout Nov 11")
        shelter = next(a for a in acts if a["program_id"] == "PROG-SHELTER")
        self.assertEqual(shelter["user_target_date"], "2026-11-11",
                         f"Parsed date must be 2026-11-11; got {shelter['user_target_date']!r}")
        self.assertIn("date you gave", shelter["rationale"],
                      f"Rationale must mention 'The date you gave'; got {shelter['rationale']!r}")

    def test_notice_date_is_never_official_deadline(self):
        """The date from eviction_notice_type must not appear as official_deadline."""
        acts = self._run_with_notice_type("Writ of possession, sheriff lockout Nov 11")
        shelter = next(a for a in acts if a["program_id"] == "PROG-SHELTER")
        self.assertIsNone(shelter["official_deadline"],
                          f"Notice date must never be official_deadline; "
                          f"got {shelter['official_deadline']!r}")

    def test_notice_date_does_not_reorder_housing_before_food(self):
        """Even with a parsed notice date, housing must not be reordered before food
        by the cross-need sort key (date is excluded from sort key, §15.2 rule 4 analogy)."""
        # Both are "immediate" so both are in "first" group.  Within the group,
        # housing_first=True (writ keyword) means housing subs sort before food.
        # That is intentional — housing_first is active.  What must NOT happen is
        # the parsed notice date moving housing ahead when housing_first is False.
        # Use a non-late-stage notice with a date to verify the date doesn't reorder.
        needs = [
            _need("need_food", category="food_assistance",
                  subcategory="food_pantry", urgency="immediate"),
            _need("need_housing", category="housing_assistance",
                  subcategory="rental_assistance", urgency="high"),
        ]
        matches = [
            _match("PROG-FOOD", ["need_food"], subcategory="food_pantry"),
            _match("PROG-HOUSING", ["need_housing"], subcategory="rental_assistance"),
        ]
        avail = [_open_avail("PROG-FOOD"), _open_avail("PROG-HOUSING")]
        # "30-day notice Nov 25" — early stage, date present, housing urgency=high
        case_facts = [{"fact_id": "f1", "field": "eviction_notice_type",
                       "value": "30-day notice Nov 25",
                       "confirmation_status": "confirmed",
                       "source": "user_statement", "time_context": None}]
        acts = _run6(needs, [matches[0], matches[1]],
                     program_availability=avail, case_facts=case_facts, ref_date="2026-11-01")
        pids = [a["program_id"] for a in acts if a["program_id"]]
        food_idx = pids.index("PROG-FOOD")
        housing_idx = pids.index("PROG-HOUSING")
        # food (immediate → first) must still come before housing (high → parallel)
        self.assertLess(food_idx, housing_idx,
                        f"Notice date must not reorder housing before food; got {pids}")
        # date must still appear as user_target_date on the housing card
        housing_action = next(a for a in acts if a["program_id"] == "PROG-HOUSING")
        self.assertEqual(housing_action["user_target_date"], "2026-11-25",
                         f"Parsed notice date must be user_target_date; "
                         f"got {housing_action['user_target_date']!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
