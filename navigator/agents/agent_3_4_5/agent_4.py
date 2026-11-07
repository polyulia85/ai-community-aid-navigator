"""Agent 4 - Resource Matching (contract 4.4 / frozen 11.5). Preliminary fit only, never an eligibility decision.
Reads ONLY its inputs: program_criteria[] is built by the Supervisor from the KB (Slav, Oct 22).
Rules (v1.6, after Julia's review of Nov 3):
- confirmed location outside the program's service area -> confirmed_mismatch (names criterion + fact)
- location unknown, or no service-area criteria supplied -> insufficient_information
- inside the service area -> potential_match
- supported_match ONLY when location and household size are confirmed, no needed case fact is missing,
  AND every criterion was evaluated. Text eligibility criteria are not evaluated yet (structured criteria are
  proposed for contracts v1.2), so a program with any eligibility criteria stays potential_match and the
  unevaluated criteria are reported (CRITERIA_NOT_EVALUATED). A confirmed fact is not a confirmed match.
- income is asked for only when the program's own criteria mention income; unknown income is NEVER a mismatch.
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
        other = [c for c in crit if not c["field_path"].startswith("geography")]
        income_relevant = any("income" in str(c.get("value", "")).lower() for c in other)
        if income_relevant and m["match_status"] != "confirmed_mismatch":
            for f in INCOME_FACTS:
                if facts.get(f, {}).get("value") is None:
                    m["missing_case_facts"].append(f)
        if m["match_status"] in ("potential_match", "supported_match") and other:
            issues.append(issue("CRITERIA_NOT_EVALUATED", "info",
                                f"{len(other)} eligibility criteria not evaluated yet: "
                                + ", ".join(c["field_path"] for c in other) + ". Only the program can decide.", pid))
        if m["match_status"] == "supported_match" and (m["missing_case_facts"] or other):
            m["match_status"] = "potential_match"
            why = []
            if m["missing_case_facts"]:
                why.append(", ".join(m["missing_case_facts"]) + " still unknown")
            if other:
                why.append(f"{len(other)} program criteria not yet evaluated")
            m["explanation"] += " Not yet a supported match: " + "; ".join(why) + "."
        refs += m["evidence_refs"]
        matches.append(m)
    return envelope(request, "agent_4", "completed", {"matches": matches}, issues, refs)
