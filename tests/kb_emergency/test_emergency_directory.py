"""Checks the emergency directory (owner: Silver): numbers present, every claim sourced and linked, no assumed hours."""
import json
import os
import re
import unittest

PATH = os.path.join(os.path.dirname(__file__), "..", "..", "navigator", "kb", "emergency", "emergency_directory.json")


class EmergencyDirectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PATH, encoding="utf-8") as f:
            cls.d = json.load(f)
        cls.ev = {e["evidence_id"]: e for e in cls.d["evidence_records"]}

    def contacts(self, rid):
        r = [p for p in self.d["program_records"] if p["program_id"] == rid][0]
        return " ".join(c["value"] for c in r["contact"])

    def test_all_five_numbers_from_the_protocol_are_present(self):
        self.assertIn("9-1-1", self.contacts("res_emergency_911_sac_001"))
        self.assertIn("988", self.contacts("res_crisis_988_us_001"))
        self.assertIn("(916) 920-2952", self.contacts("res_dv_weave_sac_001"))
        self.assertIn("7233", self.contacts("res_dv_hotline_us_001"))
        self.assertIn("4673", self.contacts("res_dv_fjc_sac_001"))

    def test_every_claim_has_an_https_source_and_check_date(self):
        for e in self.d["evidence_records"]:
            self.assertTrue(e["source_url"].startswith("https://"), e["evidence_id"])
            self.assertRegex(e["checked_at"], r"^\d{4}-\d\d-\d\dT")

    def test_every_claim_in_a_record_is_linked_to_its_evidence(self):
        for r in self.d["program_records"]:
            for f in ("eligibility_criteria", "application_method", "contact"):
                for c in r[f]:
                    for ref in c["evidence_refs"]:
                        self.assertEqual(self.ev[ref]["claim_value"], c["value"])
            self.assertTrue(all(s in self.ev for s in r["sources"]))

    def test_open_status_only_where_the_page_states_hours(self):
        for r in self.d["program_records"]:
            avail = [e for e in self.d["evidence_records"] if e["program_id"] == r["program_id"] and e["field_path"] == "availability"][0]
            if r["availability"] == "confirmed_open":
                self.assertTrue(re.search(r"24|seven days", avail["claim_value"]), r["program_id"])
                self.assertEqual(avail["verification_status"], "verified")
            else:
                self.assertEqual(avail["verification_status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
