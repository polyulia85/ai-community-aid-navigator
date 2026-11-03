"""Checks navigator/kb/kb_sacramento.json against contracts v1.0 section 3.4 / 3.5. Run: python navigator/kb/tools/validate_kb.py"""
import json, os, re, sys
from datetime import datetime

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "kb_sacramento.json")
d = json.load(open(path, encoding="utf-8"))
VS = {"verified", "needs_review", "conflicting", "unverified"}
AV = {"confirmed_open", "temporarily_closed", "unknown"}
SUB = {"food_assistance": {"calfresh_benefits", "food_pantry"},
       "housing_assistance": {"emergency_shelter", "motel_voucher", "rental_assistance", "eviction_prevention", "housing_legal_aid"},
       "income_assistance": {"unemployment_insurance", "cash_aid", "disability_family_leave", "employment_services"},
       "utility_assistance": {"bill_credit_grant", "income_based_discount", "arrears_disconnection_prevention", "payment_arrangement", "water_sewer_trash"},
       "medical_health_coverage": {"health_coverage", "medical_care_access", "prescription_assistance", "medical_bill_assistance"},
       "debt_hardship": {"credit_counseling", "consumer_protection_legal_aid", "court_self_help", "mortgage_housing_counseling"},
       "material_in_kind": {"furniture_household", "clothing", "hygiene_essentials", "children_essentials"},
       "crowdfunding_guidance": {"platform_guidance"}}  # other_unlisted is needs-only: never valid here
REQ_P = ["program_id", "program_name", "organization", "category", "geography", "eligibility_criteria", "required_documents",
         "application_method", "contact", "deadlines", "processing_time", "availability", "sources", "last_verified_at", "verification_status"]
REQ_E = ["evidence_id", "program_id", "field_path", "claim_value", "source_url", "checked_at", "verification_status"]
ARR = ["eligibility_criteria", "required_documents", "application_method", "contact", "deadlines"]
err = []
ev = {}
for e in d["evidence_records"]:
    if e["evidence_id"] in ev: err.append("duplicate evidence_id " + e["evidence_id"])
    ev[e["evidence_id"]] = e
    for k in REQ_E:
        if e.get(k) in (None, ""): err.append(f"{e['evidence_id']} missing {k}")
    if e["verification_status"] not in VS: err.append("bad status " + e["evidence_id"])
    if not e["source_url"].startswith("https://"): err.append("non-https source " + e["evidence_id"])
    datetime.fromisoformat(e["checked_at"])
pids = set()
for p in d["program_records"]:
    pid = p["program_id"]; pids.add(pid)
    for k in REQ_P:
        if k not in p: err.append(f"{pid} missing {k}")
    if p["category"] not in SUB: err.append(f"{pid} category not allowed: {p['category']}")
    if p.get("subcategory") is not None and p["subcategory"] not in SUB.get(p["category"], set()): err.append(f"{pid} subcategory not in its category")
    if p["availability"] not in AV or p["verification_status"] not in VS: err.append(f"{pid} bad enum")
    if not p["geography"]: err.append(f"{pid} geography empty")
    for s in p["sources"]:
        if s not in ev or ev[s]["program_id"] != pid: err.append(f"{pid} bad source ref {s}")
    for f in ARR:
        for i, c in enumerate(p[f]):
            for r in c["evidence_refs"]:
                e = ev.get(r)
                if not e or e["field_path"] != f"{f}[{i}]" or e["claim_value"] != c["value"] or e["verification_status"] != c["verification_status"]:
                    err.append(f"{pid} claim mismatch {f}[{i}]")
    # reverse check: every array evidence row is linked into its ProgramRecord (Slav's Oct 22 required_documents finding)
    for e in ev.values():
        if e["program_id"] != pid: continue
        m = re.match(r"(\w+)\[(\d+)\]$", e["field_path"])
        if m and m.group(1) in ARR:
            arr, i = p[m.group(1)], int(m.group(2))
            if i >= len(arr) or e["evidence_id"] not in arr[i]["evidence_refs"]:
                err.append(f"{e['evidence_id']} ({e['field_path']}) not linked in ProgramRecord")
    banned = re.compile(r"\byou (will )?(definitely )?qualify\b|\bguarantee", re.I)
    for e in ev.values():
        if e["program_id"] == pid and banned.search(e["claim_value"]): err.append(f"promise wording in {e['evidence_id']}")
for e in ev.values():
    if e["program_id"] not in pids: err.append(f"{e['evidence_id']} points to unknown program")
print("ERRORS:", err or "none")
for p in d["program_records"]:
    rows = [e for e in ev.values() if e["program_id"] == p["program_id"]]
    print(f"  {p['program_id']}: {len(rows)} evidence | " + ", ".join(f"{s}={sum(e['verification_status'] == s for e in rows)}" for s in sorted(VS)))
sys.exit(1 if err else 0)
