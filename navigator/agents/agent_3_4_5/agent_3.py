"""Agent 3 - Resource Retrieval (contract 4.3 / frozen 11.4). Returns candidate references only:
no eligibility conclusions, no urgency ranking, no KB edits. Verified KB only (external discovery is P2).

Ordering policy (deterministic, documented for Julia's review 3.1): needs in request order; within a need,
programs whose subcategory matches first, then by program_id. When more candidates are found than
max_candidates, the result is truncated and says so (CANDIDATES_TRUNCATED) - it never looks exhaustive.
Unknown geography is reported as GEOGRAPHY_UNRESOLVED, never as a coverage gap (Julia's review 3.2).
No-ZIP rule: when geography is exactly [] (empty list), statewide programs are searched; county-only
programs are skipped; no COVERAGE_GAP is emitted (unknown location, not a lack of programs). Any
non-empty geography that does not resolve is unchanged (nothing returned, no COVERAGE_GAP)."""
from .common import load_kb, to_counties, area_covers, envelope, bad_request, check_task, issue, CLAIM_FIELDS, CATEGORIES, STATEWIDE

DEFAULT_MAX = 50


def _validate(p):
    """Structure checks for the payload (Julia's review 3.3). Returns a list of problems."""
    errs = []
    needs, geo, mx = p.get("needs"), p.get("geography"), p.get("max_candidates")
    if not isinstance(needs, list):
        errs.append("needs must be a list")
    else:
        for i, n in enumerate(needs):
            if not isinstance(n, dict):
                errs.append(f"needs[{i}] must be an object")
            elif not isinstance(n.get("need_id"), str) or not n["need_id"]:
                errs.append(f"needs[{i}].need_id missing")
            elif not isinstance(n.get("category"), str) or not n["category"]:
                errs.append(f"needs[{i}].category missing")
    if not isinstance(geo, list):
        errs.append("geography must be a list")
    if mx is not None and (isinstance(mx, bool) or not isinstance(mx, int) or mx < 1):
        errs.append("max_candidates must be a positive integer")
    return errs


def handle(request, kb_path=None):
    bad = check_task(request, "agent_3")
    if bad:
        return bad
    p = request.get("payload") or {}
    missing = [k for k in ("needs", "geography") if k not in p]
    if missing:
        return bad_request(request, "agent_3", missing)
    errs = _validate(p)
    if errs:
        return envelope(request, "agent_3", "failed", {}, [issue("INPUT_INVALID", "critical", "; ".join(errs))])
    programs, evidence = load_kb(kb_path)
    mortgage_programs = {
        item["program_id"] for item in evidence
        if item.get("verification_status") == "verified"
        and item.get("field_path") == "program_name"
        and "mortgage payments" in str(item.get("claim_value", "")).lower()
    }
    raw_geo = p["geography"]
    counties, issues = to_counties(raw_geo)
    max_n = p.get("max_candidates") or DEFAULT_MAX
    geography_known = bool(counties)
    # statewide_only: geography list was exactly empty ([]). Any non-empty list that doesn't
    # resolve (unknown ZIP, unrecognised county name) is a different case and returns nothing.
    statewide_only = not geography_known and raw_geo == []
    if not geography_known:
        note = ("No ZIP code given: only statewide programs were searched; local programs need a ZIP code."
                if statewide_only else
                "No county could be resolved from the request; programs could not be compared by area. "
                "This is unknown location, not a lack of programs.")
        issues.append(issue("GEOGRAPHY_UNRESOLVED", "warning", note, None))
    found, rejected = {}, 0
    for need in p["needs"]:
        if need["category"] not in CATEGORIES:  # input error, not a coverage gap (taxonomy: unknown values rejected)
            rejected += 1
            issues.append(issue("UNKNOWN_CATEGORY", "critical",
                                f"Need category '{need['category']}' is not in the v1.0 category list; need not searched.", need["need_id"]))
            continue
        if need["category"] == "other_unlisted":
            issues.append(issue("COVERAGE_GAP", "info", "Need is outside the category list (other_unlisted); no KB category to search.", need["need_id"]))
            continue
        if not geography_known and not statewide_only:
            continue  # ZIP given but unmapped: cannot compare areas; reported once above, never as a coverage gap
        sub = need.get("subcategory")
        if statewide_only:
            hits = [pr for pr in programs if pr["category"] == need["category"] and STATEWIDE in pr["geography"]]
        else:
            hits = [pr for pr in programs if pr["category"] == need["category"] and area_covers(pr["geography"], counties)]
        if sub == "mortgage_assistance":
            hits = [pr for pr in hits if pr["program_id"] in mortgage_programs]
        # Subcategory is a preference, not a filter: exact subcategory first, then the rest of the category.
        hits.sort(key=lambda pr: (0 if sub and pr.get("subcategory") == sub else 1, pr["program_id"]))
        if not hits and not statewide_only:
            issues.append(issue("COVERAGE_GAP", "info",
                                f"No verified KB program for {need['category']} in {sorted(counties)}.", need["need_id"]))
        for pr in hits:
            reason = f"Category {pr['category']}"
            if sub and pr.get("subcategory") == sub:
                reason += f" (subcategory {sub})"
            reason += f" and service area {', '.join(pr['geography'])} match the stated need and location."
            c = found.setdefault(pr["program_id"], {
                "program_id": pr["program_id"], "matched_need_ids": [], "retrieval_reason": reason,
                "source_refs": pr["sources"],
                "missing_fields": [f for f in CLAIM_FIELDS if not pr[f]] + ([] if pr["processing_time"] else ["processing_time"])})
            if need["need_id"] not in c["matched_need_ids"]:
                c["matched_need_ids"].append(need["need_id"])
    total = len(found)
    cands = list(found.values())[:max_n]
    notes = [f"Searched verified KB only (external discovery is P2). {total} candidate(s) found, {len(cands)} returned.",
             "Availability is not judged here; the Supervisor passes it on from the KB."]
    if total > len(cands):
        issues.append(issue("CANDIDATES_TRUNCATED", "warning",
                            f"{total} candidates found; only the first {len(cands)} are returned (max_candidates). "
                            "The list is not exhaustive.", None))
    if rejected == len(p["needs"]) and p["needs"]:
        status = "failed"
    elif rejected or not geography_known:
        status = "partial"
    else:
        status = "completed"
    return envelope(request, "agent_3", status, {"candidate_programs": cands, "retrieval_notes": notes},
                    issues, [r for c in cands for r in c["source_refs"]])
