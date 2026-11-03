"""Agent 4 - Resource Matching (contract 4.4 / frozen 11.5). Preliminary fit only, never an eligibility decision.
Reads ONLY its inputs: program_criteria[] is built by the Supervisor from the KB (Slav, Oct 22).
Basic rules for Oct 23:
- confirmed location outside the program's service area -> confirmed_mismatch (names criterion + fact)
- location inside service area -> potential_match
- location and household size confirmed AND no case fact missing (e.g. income) -> supported_match (decision 9, proposed)
- unknown income is NEVER a mismatch; it goes to missing_case_facts
- no location known, or no service-area criteria supplied -> insufficient_information
"""
from .common import to_counties, area_covers, envelope, bad_request, check_task, issue

INCOME_FACTS = ("household_gross_monthly_income",)


def handle(request, kb_path=None):  # kb_path kept for a uniform signature; Agent 4 does not read the KB
    bad = check_task(request, "agent_4")
    if bad:
        return bad
    p = request.get("payload") or {}
    missing = [k for k in ("candidate_programs", "case_facts", "needs", "program_criteria") if k not in p]
    if missing:
        return bad_request(request, "agent_4", missing)
    facts = {f["field"]: f for f in p["case_facts"] if f.get("confirmation_status") != "superseded"}
    loc = facts.get("county") or facts.get("zip_code")
    counties, issues = to_counties([loc["value"]] if loc and loc.get("value") else [])
    matches, refs = [], []
    for cand in p["candidate_programs"]:
        pid = cand["program_id"]
        crit = [c for c in p["program_criteria"] if c["program_id"] == pid]
        geo = [c for c in crit if c["field_path"].startswith("geography")]
        area = [c["value"] for c in geo if c.get("value")]
        m = {"program_id": pid, "need_ids": cand["matched_need_ids"], "matched_criteria": [],
             "missing_case_facts": [], "mismatch_criteria": [],
             "evidence_refs": sorted({r for c in geo for r in c.get("evidence_refs", [])}), "explanation": ""}
        if not area:
            m["match_status"] = "insufficient_information"
            m["explanation"] = "No service-area criteria were supplied for this program, so location cannot be compared."
            issues.append(issue("PROGRAM_CRITERIA_MISSING", "warning", "program_criteria has no geography for this program.", pid))
        elif not counties:
            m["match_status"] = "insufficient_information"
            m["missing_case_facts"].append("zip_code")
            m["explanation"] = "Location unknown, so service area cannot be compared."
        elif not area_covers(area, counties):
            if loc.get("confirmation_status") == "confirmed":
                m["match_status"] = "confirmed_mismatch"
                m["mismatch_criteria"].append(f"geography: serves {', '.join(sorted(area))}; confirmed location {loc['value']}")
                m["explanation"] = "Confirmed location is outside this program's service area."
            else:
                m["match_status"] = "insufficient_information"
                m["explanation"] = "Location is proposed, not confirmed, and outside the service area; needs confirmation."
        else:
            m["matched_criteria"] += [f"geography: {', '.join(sorted(area))}", "need category matches"]
            confirmed = loc.get("confirmation_status") == "confirmed" and \
                facts.get("household_size", {}).get("confirmation_status") == "confirmed"
            m["match_status"] = "supported_match" if confirmed else "potential_match"
            m["explanation"] = ("May fit this need; this is a preliminary match, not an eligibility decision. "
                                "Only the program can decide eligibility.")
        for f in INCOME_FACTS:
            if facts.get(f, {}).get("value") is None and m["match_status"] != "confirmed_mismatch":
                m["missing_case_facts"].append(f)
        # Decision 9 (Silver's proposal, pending team agreement): supported_match requires that no case fact the
        # match depends on is missing. Unknown income keeps it at potential_match (still never a mismatch).
        if m["match_status"] == "supported_match" and m["missing_case_facts"]:
            m["match_status"] = "potential_match"
            m["explanation"] += " Not yet a supported match: " + ", ".join(m["missing_case_facts"]) + " still unknown."
        refs += m["evidence_refs"]
        matches.append(m)
    return envelope(request, "agent_4", "completed", {"matches": matches}, issues, refs)
