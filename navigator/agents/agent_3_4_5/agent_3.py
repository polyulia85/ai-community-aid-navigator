"""Agent 3 - Resource Retrieval (contract 4.3 / frozen 11.4). Returns candidate references only:
no eligibility conclusions, no urgency ranking, no KB edits. Verified KB only for Oct 26 (external discovery is P2)."""
from .common import load_kb, to_counties, area_covers, envelope, bad_request, check_task, issue, CLAIM_FIELDS, CATEGORIES


def handle(request, kb_path=None):
    bad = check_task(request, "agent_3")
    if bad:
        return bad
    p = request.get("payload") or {}
    missing = [k for k in ("needs", "geography") if k not in p]
    if missing:
        return bad_request(request, "agent_3", missing)
    programs, _ = load_kb(kb_path)
    counties, issues = to_counties(p["geography"])
    max_n = p.get("max_candidates") or 50
    found, rejected = {}, 0
    for need in p["needs"]:
        if need.get("category") not in CATEGORIES:  # input error, not a coverage gap (taxonomy: unknown values rejected)
            rejected += 1
            issues.append(issue("UNKNOWN_CATEGORY", "critical",
                                f"Need category '{need.get('category')}' is not in the v1.0 category list; need not searched.", need.get("need_id")))
            continue
        if need.get("category") == "other_unlisted":
            issues.append(issue("COVERAGE_GAP", "info", "Need is outside the category list (other_unlisted); no KB category to search.", need["need_id"]))
            continue
        hits = [pr for pr in programs if pr["category"] == need["category"] and area_covers(pr["geography"], counties)]
        # Subcategory is a preference, not a filter: exact subcategory first, other programs in the same category after,
        # so a rent need still sees e.g. eviction-prevention routes (TD: retrieve broadly, then compare).
        sub = need.get("subcategory")
        hits.sort(key=lambda pr: 0 if sub and pr.get("subcategory") == sub else 1)
        if not hits:
            issues.append(issue("COVERAGE_GAP", "info",
                                f"No verified KB program for {need['category']} in {sorted(counties) or 'unknown area'}.", need["need_id"]))
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
    cands = list(found.values())[:max_n]
    notes = [f"Searched verified KB only (external discovery is P2). {len(cands)} candidate(s).",
             "Availability is not judged here; the Supervisor passes it on from the KB."]
    status = "completed" if not rejected else ("failed" if rejected == len(p["needs"]) else "partial")
    return envelope(request, "agent_3", status, {"candidate_programs": cands, "retrieval_notes": notes},
                    issues, [r for c in cands for r in c["source_refs"]])
