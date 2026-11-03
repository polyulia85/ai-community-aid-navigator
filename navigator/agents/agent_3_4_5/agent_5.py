"""Agent 5 - Resource Verification (contract 4.5 / frozen 11.6). Reports claim status from the KB.
Never edits the KB; never treats a failed check as closure; conflicting claims stay separate."""
from .common import load_kb, envelope, bad_request, check_task, issue


def handle(request, kb_path=None):
    bad = check_task(request, "agent_5")
    if bad:
        return bad
    p = request.get("payload") or {}
    if "programs_to_check" not in p:
        return bad_request(request, "agent_5", ["programs_to_check"])
    programs, evidence = load_kb(kb_path)
    known = {pr["program_id"] for pr in programs}
    checked, unresolved, issues, refs = [], [], [], []
    unknown = 0
    for item in p["programs_to_check"]:
        pid = item["program_id"]
        if pid not in known:  # an invented program must never look like an incomplete one
            unknown += 1
            issues.append(issue("UNKNOWN_PROGRAM", "critical", f"program_id '{pid}' is not in the Knowledge Base; nothing checked.", pid))
            continue
        for fp in item.get("field_paths", []):
            rows = [e for e in evidence if e["program_id"] == pid and
                    (e["field_path"] == fp or e["field_path"].startswith(fp + "["))]
            if not rows:
                checked.append({"program_id": pid, "field_path": fp, "claim_value": None,
                                "verification_status": "unverified", "evidence_refs": [], "checked_at": None,
                                "issue": "No published value on file; left empty, not guessed."})
                continue
            groups = {}
            for e in rows:
                groups.setdefault(e["field_path"], []).append(e)
            for path, evs in groups.items():
                values = {e["claim_value"] for e in evs}
                statuses = {e["verification_status"] for e in evs}
                sources = {e["source_url"] for e in evs}
                if "conflicting" in statuses or (len(values) > 1 and len(sources) > 1):
                    status, value, note = "conflicting", None, "Sources disagree; all values kept separately."
                elif len(values) > 1 and statuses == {"verified"} and len({e.get("effective_date") for e in evs}) == len(evs):
                    # Same page, statements about DIFFERENT dates (e.g. "closed now" + "reopens Nov 2"): complementary.
                    status, value, note = "verified", " | ".join(e["claim_value"] for e in evs), "Dated statements from the same source; all kept."
                elif len(values) > 1:  # same page, same date, different values: a real contradiction (e.g. SMUD form)
                    status, value, note = "conflicting", None, "The same source gives different values; all kept separately."
                elif statuses == {"verified"}:
                    status, value, note = "verified", evs[0]["claim_value"], None
                else:
                    status = "needs_review" if "needs_review" in statuses else "unverified"
                    value, note = evs[0]["claim_value"], evs[0].get("notes")
                ids = [e["evidence_id"] for e in evs]
                refs += ids
                checked.append({"program_id": pid, "field_path": path, "claim_value": value,
                                "verification_status": status, "evidence_refs": ids,
                                "checked_at": max(e["checked_at"] for e in evs), "issue": note})
                if status != "verified":
                    unresolved.append(f"{pid} {path}: {status} - confirm with the program before relying on it.")
                    issues.append(issue("CLAIM_NOT_VERIFIED", "warning", f"{path} is {status}", path))
    status = "completed" if not unknown else ("failed" if unknown == len(p["programs_to_check"]) else "partial")
    return envelope(request, "agent_5", status,
                    {"checked_claims": checked, "update_proposals": [], "unresolved_questions": unresolved},
                    issues, refs)
