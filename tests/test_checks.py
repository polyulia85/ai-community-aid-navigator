"""Tests for Supervisor checks S0–S9. Run from the repo root:  python -m unittest -v"""
import copy
import json
import os
import unittest

from navigator.supervisor import checks

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "navigator", "samples")


def load(name):
    with open(os.path.join(SAMPLES, name), encoding="utf-8") as f:
        return json.load(f)


def codes(issues):
    return {i["code"] for i in issues}


class TestWithSamples(unittest.TestCase):
    def setUp(self):
        self.req = load("01_agent1_request.json")
        self.good = load("02_agent1_result_expected.json")
        self.bad = load("03_invalid_result_for_supervisor_test.json")

    def test_expected_result_is_accepted(self):
        ok, issues = checks.check_result(self.req, self.good, self.req["case_version"])
        self.assertTrue(ok, issues)
        self.assertIn("MOCK_COMPONENT", codes(issues))   # S8 is info, not a block

    def test_broken_result_is_rejected(self):
        ok, issues = checks.check_result(self.req, self.bad, self.req["case_version"])
        self.assertFalse(ok)
        self.assertIn("IDENTITY_MISMATCH", codes(issues))  # wrong request_id
        self.assertIn("UNKNOWN_ENUM", codes(issues))       # category "housing"


class TestEachCheck(unittest.TestCase):
    def setUp(self):
        self.req = load("01_agent1_request.json")
        self.good = load("02_agent1_result_expected.json")

    def test_s1_missing_field(self):
        r = copy.deepcopy(self.good); del r["status"]
        ok, issues = checks.check_result(self.req, r, 1)
        self.assertFalse(ok); self.assertIn("SCHEMA_INVALID", codes(issues))

    def test_s1_old_schema_version_is_warning_only(self):
        r = copy.deepcopy(self.good); r["schema_version"] = "0.1"
        ok, issues = checks.check_result(self.req, r, self.req["case_version"])
        self.assertTrue(ok); self.assertIn("SCHEMA_VERSION", codes(issues))

    def test_s2_wrong_agent_id(self):
        r = copy.deepcopy(self.good); r["agent_id"] = "agent_2"
        self.assertIn("IDENTITY_MISMATCH", codes(checks.s2_identity(self.req, r)))

    def test_s3_stale_version(self):
        self.assertIn("STALE_RESULT", codes(checks.s3_stale(self.good, self.good["case_version"] + 1)))

    def test_s4_bad_urgency(self):
        r = copy.deepcopy(self.good); r["result"]["proposed_needs"][0]["urgency"] = "urgent"
        self.assertIn("UNKNOWN_ENUM", codes(checks.s4_enums(r)))

    def test_s4_availability_text_in_claim_is_allowed(self):
        # Agent 5 claim for field_path "availability" carries evidence text — not an enum
        r = {"result": {"checked_claims": [{"field_path": "availability",
             "claim_value": "All of the funds for October 2026 have been exhausted."}]}}
        self.assertEqual(checks.s4_enums(r), [])

    def test_s4_availability_enum_checked_in_program_availability(self):
        r = {"result": {"program_availability": [{"program_id": "p1", "availability": "closed"}]}}
        self.assertIn("UNKNOWN_ENUM", codes(checks.s4_enums(r)))

    def test_s5_unknown_need(self):
        r = {"result": {"matches": [{"program_id": "p1", "need_ids": ["need_999"]}]}}
        out = checks.s5_references(r, {"need_id": {"need_001"}, "program_id": {"p1"}})
        self.assertIn("UNKNOWN_REFERENCE", codes(out))

    def test_s5_null_program_id_allowed(self):
        r = {"result": {"proposed_actions": [{"program_id": None, "need_id": None}]}}
        self.assertEqual(checks.s5_references(r, {"program_id": {"p1"}, "need_id": set()}), [])

    def test_s6_failed(self):
        r = copy.deepcopy(self.good); r["status"] = "failed"
        ok, issues = checks.check_result(self.req, r, self.req["case_version"])
        self.assertFalse(ok); self.assertIn("AGENT_FAILED", codes(issues))

    def test_s7_timeout(self):
        self.assertIn("TIMEOUT", codes(checks.s7_timeout(31)))
        self.assertEqual(checks.s7_timeout(2.5), [])


class TestPrivacy(unittest.TestCase):
    def test_s0_masks_ssn_card_routing(self):
        text = "My SSN is 123-45-6789, card 4111 1111 1111 1111, routing 021000021."
        masked, issues = checks.mask_user_text(text)
        for secret in ("123-45-6789", "4111 1111 1111 1111", "021000021"):
            self.assertNotIn(secret, masked)
        self.assertEqual(len(issues), 3)

    def test_s0_keeps_ordinary_numbers(self):
        text = ("ZIP 95823 (or 95823-1234), rent $1,450 due 2026-11-01, "
                "call (208) 202-9004, kids 6 and 9.")
        masked, issues = checks.mask_user_text(text)
        self.assertEqual(masked, text); self.assertEqual(issues, [])

    def test_s9_ok_to_mention_social_security_card(self):
        r = {"result": {"next_step": "Bring ID; the county may ask for your Social Security card.",
                        "classname": "x"}}
        self.assertEqual(checks.s9_privacy(r), [])

    def test_s9_forbidden_field_name(self):
        self.assertIn("PRIVACY_VIOLATION", codes(checks.s9_privacy({"result": {"ssn": None}})))

    def test_s9_number_in_text(self):
        r = {"result": {"narrative_summary": "Her number is 123-45-6789"}}
        self.assertIn("PRIVACY_VIOLATION", codes(checks.s9_privacy(r)))


class TestS1ResultFields(unittest.TestCase):
    """FIX 5: per-role result field checks in S1 (check_result level)."""

    def setUp(self):
        self.req  = load("01_agent1_request.json")   # role_id=agent_1, task_type=understand_story
        self.good = load("02_agent1_result_expected.json")

    def _req(self, role_id, task_type):
        r = copy.deepcopy(self.req)
        r["role_id"] = role_id
        r["task_type"] = task_type
        return r

    def _envelope(self, role_id, result_body):
        r = copy.deepcopy(self.good)
        r["agent_id"] = role_id
        r["result"] = result_body
        return r

    # missing top-level result key
    def test_missing_top_level_key(self):
        req = self._req("agent_1", "understand_story")
        result = copy.deepcopy(self.good)
        del result["result"]["narrative_summary"]
        ok, issues = checks.check_result(req, result, req["case_version"])
        self.assertFalse(ok)
        refs = {i["related_ref"] for i in issues if i["code"] == "SCHEMA_INVALID"}
        self.assertIn("narrative_summary", refs)

    # list item that is not an object
    def test_list_item_not_an_object(self):
        req = self._req("agent_1", "understand_story")
        result = copy.deepcopy(self.good)
        result["result"]["proposed_needs"][0] = "not-a-dict"
        ok, issues = checks.check_result(req, result, req["case_version"])
        self.assertFalse(ok)
        refs = {i["related_ref"] for i in issues if i["code"] == "SCHEMA_INVALID"}
        self.assertIn("proposed_needs[0]", refs)

    # parse_clarification_answer with only factual_claims — accepted
    def test_parse_clarification_answer_accepted(self):
        req = self._req("agent_1", "parse_clarification_answer")
        result = self._envelope("agent_1", {"factual_claims": [
            {"fact_id": "f1", "field": "zip_code", "value": "95823",
             "confirmation_status": "confirmed", "source": "user_statement",
             "time_context": None}]})
        ok, issues = checks.check_result(req, result, req["case_version"])
        self.assertTrue(ok, issues)

    # parse_clarification_answer fact missing time_context — rejected
    def test_parse_clarification_answer_missing_time_context(self):
        req = self._req("agent_1", "parse_clarification_answer")
        result = self._envelope("agent_1", {"factual_claims": [
            {"fact_id": "f1", "field": "zip_code", "value": "95823",
             "confirmation_status": "confirmed", "source": "user_statement"}]})
             # time_context absent
        ok, issues = checks.check_result(req, result, req["case_version"])
        self.assertFalse(ok)
        refs = {i["related_ref"] for i in issues if i["code"] == "SCHEMA_INVALID"}
        self.assertIn("factual_claims[0].time_context", refs)

    # failed result with empty result{} — no SCHEMA_INVALID from new check
    def test_failed_result_not_checked(self):
        req = self._req("agent_1", "understand_story")
        result = copy.deepcopy(self.good)
        result["status"] = "failed"
        result["result"] = {}
        ok, issues = checks.check_result(req, result, req["case_version"])
        # S6 fires AGENT_FAILED; S1 extension must NOT fire
        self.assertIn("AGENT_FAILED", {i["code"] for i in issues})
        self.assertNotIn("SCHEMA_INVALID", {i["code"] for i in issues})

    # unknown task_type — rejected, no exception
    def test_unknown_task_type_rejected_no_exception(self):
        req = self._req("agent_1", "do_magic")
        ok, issues = checks.check_result(req, self.good, req["case_version"])
        self.assertFalse(ok)
        self.assertIn("SCHEMA_INVALID", {i["code"] for i in issues})


class TestResultRequiredConsistency(unittest.TestCase):
    """FIX 5: RESULT_REQUIRED table is internally consistent."""

    # every (role, task_type) in TASK_TYPES has an entry
    def test_every_task_type_has_an_entry(self):
        from navigator.supervisor import contract as C
        for role, tasks in C.TASK_TYPES.items():
            for task in tasks:
                entry = C.RESULT_REQUIRED.get(role, {}).get(task)
                self.assertIsNotNone(
                    entry, f"RESULT_REQUIRED missing entry for {role}/{task}")

    # every key in "lists" is also in "result"
    def test_every_lists_key_is_in_result(self):
        from navigator.supervisor import contract as C
        for role, tasks in C.RESULT_REQUIRED.items():
            for task, entry in tasks.items():
                result_keys = set(entry.get("result", []))
                for lk in entry.get("lists", []):
                    self.assertIn(
                        lk, result_keys,
                        f"{role}/{task}: lists key {lk!r} not in result")

    # every item-key entry names a key that is in "lists" or "optional_lists"
    def test_every_item_key_entry_names_a_lists_key(self):
        from navigator.supervisor import contract as C
        for role, tasks in C.RESULT_REQUIRED.items():
            for task, entry in tasks.items():
                all_list_keys = set(entry.get("lists", [])) | set(entry.get("optional_lists", []))
                for k in entry:
                    if k in ("result", "lists", "optional_lists"):
                        continue
                    self.assertIn(
                        k, all_list_keys,
                        f"{role}/{task}: item-key entry {k!r} not in lists or optional_lists")

    # no optional_lists key overlaps with "result" or "lists"; each has an item-key entry
    def test_optional_lists_not_in_result(self):
        from navigator.supervisor import contract as C
        for role, tasks in C.RESULT_REQUIRED.items():
            for task, entry in tasks.items():
                result_keys = set(entry.get("result", []))
                list_keys   = set(entry.get("lists", []))
                for k in entry.get("optional_lists", []):
                    self.assertNotIn(k, result_keys,
                        f"{role}/{task}: optional_lists key {k!r} must not be in result")
                    self.assertNotIn(k, list_keys,
                        f"{role}/{task}: optional_lists key {k!r} must not be in lists")
                    self.assertIn(k, entry,
                        f"{role}/{task}: optional_lists key {k!r} has no item-key entry")


class TestS1OptionalLists(unittest.TestCase):
    """optional_lists: present-must-be-list, absent-is-fine, items are checked."""

    def _req(self, task_type="parse_clarification_answer"):
        req = load("01_agent1_request.json")
        req["role_id"] = "agent_1"
        req["task_type"] = task_type
        return req

    def _envelope(self, result_body):
        r = load("02_agent1_result_expected.json")
        r["agent_id"] = "agent_1"
        r["result"] = result_body
        return r

    def test_proposed_needs_absent_is_accepted(self):
        """proposed_needs absent -> accepted (it is optional)."""
        req = self._req()
        result = self._envelope({"factual_claims": [
            {"fact_id": "f1", "field": "zip_code", "value": "95823",
             "confirmation_status": "proposed", "source": "user_statement",
             "time_context": None}]})
        ok, issues = checks.check_result(req, result, req["case_version"])
        self.assertTrue(ok, issues)

    def test_proposed_needs_not_a_list_schema_invalid(self):
        """proposed_needs = {} (not a list) -> SCHEMA_INVALID with related_ref 'proposed_needs'."""
        req = self._req()
        result = self._envelope({"factual_claims": [], "proposed_needs": {}})
        ok, issues = checks.check_result(req, result, req["case_version"])
        self.assertFalse(ok)
        refs = {i["related_ref"] for i in issues if i["code"] == "SCHEMA_INVALID"}
        self.assertIn("proposed_needs", refs)

    def test_proposed_needs_item_missing_category_schema_invalid(self):
        """proposed_needs item without category -> SCHEMA_INVALID."""
        req = self._req()
        result = self._envelope({"factual_claims": [], "proposed_needs": [
            {"need_id": "need_003", "description": "d", "original_quote": "q",
             "confirmation_status": "proposed", "user_reported": True,
             "urgency": "normal", "urgency_reason": None, "user_priority": None}
            # category missing
        ]})
        ok, issues = checks.check_result(req, result, req["case_version"])
        self.assertFalse(ok)
        refs = {i["related_ref"] for i in issues if i["code"] == "SCHEMA_INVALID"}
        self.assertIn("proposed_needs[0].category", refs)

    def test_optional_lists_key_not_treated_as_list_key(self):
        """'optional_lists' in the result body is never iterated as a list of items."""
        req = self._req()
        result = self._envelope({"factual_claims": [], "optional_lists": ["not-a-dict"]})
        ok, issues = checks.check_result(req, result, req["case_version"])
        msgs = [i["message"] for i in issues if i["code"] == "SCHEMA_INVALID"]
        self.assertFalse(any("optional_lists" in m for m in msgs), msgs)


class TestS5ProposedNeedsNotReference(unittest.TestCase):
    """S5: proposed_needs[*].need_id is a definition, not a reference."""

    def _req(self):
        req = load("01_agent1_request.json")
        req["role_id"] = "agent_1"
        req["task_type"] = "parse_clarification_answer"
        return req

    def _envelope(self, result_body):
        r = load("02_agent1_result_expected.json")
        r["agent_id"] = "agent_1"
        r["result"] = result_body
        return r

    def test_new_need_id_in_proposed_needs_accepted(self):
        """Full check_result on parse_clarification_answer with proposed_needs[0].need_id
        unknown in the known set -> accepted, no UNKNOWN_REFERENCE."""
        req = self._req()
        result = self._envelope({"factual_claims": [], "proposed_needs": [
            {"need_id": "need_009", "category": "food_assistance", "description": "d",
             "original_quote": "q", "confirmation_status": "proposed",
             "user_reported": True, "urgency": "normal",
             "urgency_reason": None, "user_priority": None}]})
        ok, issues = checks.check_result(req, result, req["case_version"],
                                         known={"need_id": {"need_001"}})
        self.assertTrue(ok, issues)
        self.assertNotIn("UNKNOWN_REFERENCE", {i["code"] for i in issues})

    def test_deeper_nested_need_id_still_checked(self):
        """A need_id one level deeper (proposed_needs[0].extra.need_id) -> UNKNOWN_REFERENCE."""
        result = {"result": {"proposed_needs": [{"need_id": "need_009",
                                                  "extra": {"need_id": "need_404"}}]}}
        out = checks.s5_references(result, {"need_id": {"need_001"}})
        flagged = {i["related_ref"] for i in out if i["code"] == "UNKNOWN_REFERENCE"}
        self.assertIn("proposed_needs[0].extra.need_id", flagged)
        self.assertNotIn("proposed_needs[0].need_id", flagged)

    def test_need_updates_need_id_still_checked(self):
        """agent_2 need_updates[0].need_id 'need_404' -> UNKNOWN_REFERENCE."""
        result = {"result": {"need_updates": [{"need_id": "need_404"}]}}
        out = checks.s5_references(result, {"need_id": {"need_001"}})
        self.assertIn("UNKNOWN_REFERENCE", {i["code"] for i in out})


if __name__ == "__main__":
    unittest.main()
