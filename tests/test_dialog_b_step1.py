"""Tests for Step 1: _emergency_contacts and _safety_notice (Supervisor v0.2.5, Session B).

Run from the repo root:  python -m unittest tests.test_dialog_b_step1 -v
"""
import os
import tempfile
import unittest

from navigator.supervisor import dialog as D

FIXTURE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "fixtures", "emergency_fixture.json"))

REAL_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "navigator", "kb", "emergency",
                 "emergency_directory.json"))


class TestEmergencyContactsFixture(unittest.TestCase):
    """_emergency_contacts() with the minimal fixture."""

    def setUp(self):
        # Clear the module-level cache so each test starts fresh.
        D._EMERGENCY_CONTACTS_CACHE.clear()

    def test_911_comes_before_988(self):
        contacts, issues = D._emergency_contacts(FIXTURE)
        self.assertEqual(issues, [])
        values = [c["value"] for c in contacts]
        idx_911 = next((i for i, v in enumerate(values) if "9-1-1" in v), None)
        idx_988 = next((i for i, v in enumerate(values) if "988" in v), None)
        self.assertIsNotNone(idx_911, "9-1-1 contact not found")
        self.assertIsNotNone(idx_988, "988 contact not found")
        self.assertLess(idx_911, idx_988, "9-1-1 must come before 988")

    def test_police_record_never_appears(self):
        contacts, issues = D._emergency_contacts(FIXTURE)
        values = [c["value"] for c in contacts]
        for v in values:
            self.assertNotIn("555-867-5309", v,
                             "local_police_non_emergency contact must not appear in safety contacts")

    def test_unverified_contact_is_excluded(self):
        """The 988 fixture has one verified and one unverified contact; only verified is returned."""
        contacts, issues = D._emergency_contacts(FIXTURE)
        # The unverified contact "Chat at 988lifeline.org." must not appear
        values = [c["value"] for c in contacts]
        for v in values:
            self.assertNotIn("988lifeline.org", v,
                             "Unverified contact (needs_review evidence) must not appear")

    def test_verified_contacts_have_expected_shape(self):
        contacts, issues = D._emergency_contacts(FIXTURE)
        for c in contacts:
            self.assertIn("name", c)
            self.assertIn("value", c)
            self.assertIsNone(c["hours"])
            self.assertRegex(c["checked_at"], r"^\d{4}-\d{2}-\d{2}$",
                             "checked_at must be YYYY-MM-DD")

    def test_missing_file_returns_empty_contacts_and_unverified_issue(self):
        contacts, issues = D._emergency_contacts("/nonexistent/path/emergency.json")
        self.assertEqual(contacts, [])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["code"], D.SAFETY_CONTACT_UNVERIFIED)
        self.assertEqual(issues[0]["severity"], "warning")
        self.assertIsNone(issues[0]["related_ref"])

    def test_invalid_json_returns_empty_contacts_and_unverified_issue(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False, encoding="utf-8") as f:
            f.write("not valid json {{{{")
            path = f.name
        try:
            contacts, issues = D._emergency_contacts(path)
            self.assertEqual(contacts, [])
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]["code"], D.SAFETY_CONTACT_UNVERIFIED)
        finally:
            os.unlink(path)

    def test_no_verified_contacts_returns_unverified_issue(self):
        """A file with no matching subcategory records → [] and SAFETY_CONTACT_UNVERIFIED."""
        import json
        data = {
            "schema_version": "1.0",
            "note": "empty",
            "program_records": [],
            "evidence_records": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            path = f.name
        try:
            contacts, issues = D._emergency_contacts(path)
            self.assertEqual(contacts, [])
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]["code"], D.SAFETY_CONTACT_UNVERIFIED)
        finally:
            os.unlink(path)

    def test_cache_returns_same_object_on_second_call(self):
        result1 = D._emergency_contacts(FIXTURE)
        result2 = D._emergency_contacts(FIXTURE)
        self.assertIs(result1, result2, "Second call must return the cached tuple")

    def test_911_name_is_program_name(self):
        contacts, _ = D._emergency_contacts(FIXTURE)
        c911 = next((c for c in contacts if "9-1-1" in c["value"]), None)
        self.assertIsNotNone(c911)
        self.assertEqual(c911["name"], "9-1-1 Emergency")


class TestSafetyNoticeInResponses(unittest.TestCase):
    """The verified contacts reach safety_notice in a dialog response; a missing directory is reported."""

    def setUp(self):
        D._EMERGENCY_CONTACTS_CACHE.clear()
        self.addCleanup(D._EMERGENCY_CONTACTS_CACHE.clear)

    def _start_with_safety(self):
        from tests.fake_agents import FIXTURE_KB, FIXTURE_ZIPS, agent_1_dialog, agent_2_dialog

        def agent_1_threat(req):
            r = agent_1_dialog(req)
            if req.get("task_type") == "understand_story":
                r["result"]["safety_or_official_deadline_flags"] = [
                    {"type": "safety", "quote": "[REDACTED]", "note": "Threat of physical harm reported"}]
            return r
        return D.start("x", ref_date="2026-11-15", kb_path=FIXTURE_KB, zips_path=FIXTURE_ZIPS,
                       isolate=False, agents={"agent_1": agent_1_threat, "agent_2": agent_2_dialog})

    def test_contacts_in_notice(self):
        r = self._start_with_safety()
        values = [c["value"] for c in r["safety_notice"]["contacts"]]
        self.assertEqual(values[0], "9-1-1")
        self.assertIn("Call or text 988.", values)
        self.assertNotIn("SAFETY_CONTACT_UNVERIFIED", {i["code"] for i in r["issues"]})

    def test_missing_directory_is_reported_in_issues(self):
        orig = D.DEFAULT_EMERGENCY
        D.DEFAULT_EMERGENCY = os.path.join(tempfile.gettempdir(), "no_such_emergency_dir.json")
        self.addCleanup(setattr, D, "DEFAULT_EMERGENCY", orig)
        r = self._start_with_safety()
        self.assertEqual(r["safety_notice"]["contacts"], [])
        self.assertIn("SAFETY_CONTACT_UNVERIFIED", {i["code"] for i in r["issues"]})

    def test_no_safety_flag_no_notice_no_warning(self):
        from tests.fake_agents import FIXTURE_KB, FIXTURE_ZIPS, agent_1_dialog, agent_2_dialog
        r = D.start("x", ref_date="2026-11-15", kb_path=FIXTURE_KB, zips_path=FIXTURE_ZIPS,
                    isolate=False, agents={"agent_1": agent_1_dialog, "agent_2": agent_2_dialog})
        self.assertIsNone(r["safety_notice"])
        self.assertNotIn("SAFETY_CONTACT_UNVERIFIED", {i["code"] for i in r["issues"]})


class TestEmergencyContactsRealDirectory(unittest.TestCase):
    """One smoke test against the real emergency directory."""

    def setUp(self):
        D._EMERGENCY_CONTACTS_CACHE.clear()

    def test_real_directory_has_911_and_988(self):
        contacts, issues = D._emergency_contacts(REAL_DIR)
        self.assertEqual(issues, [], "Real directory should load without issues")
        values = [c["value"] for c in contacts]
        has_911 = any("9-1-1" in v for v in values)
        has_988 = any("988" in v for v in values)
        self.assertTrue(has_911, f"9-1-1 not found in contacts: {values}")
        self.assertTrue(has_988, f"Call or text 988 not found in contacts: {values}")


if __name__ == "__main__":
    unittest.main()
