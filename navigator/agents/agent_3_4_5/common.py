"""Shared helpers for Agents 3, 4, 5 (Silver). Contracts: Shared JSON Contracts v1.0."""
import json, os
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"  # contracts v1.0 frozen Oct 23
KB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "kb", "kb_sacramento.json")
ECHO = ["request_id", "run_id", "case_id", "case_version", "correlation_id"]
CATEGORIES = {"food_assistance", "housing_assistance", "income_assistance", "utility_assistance",
              "medical_health_coverage", "debt_hardship", "material_in_kind", "crowdfunding_guidance",
              "other_unlisted"}  # other_unlisted: needs only, never on a ProgramRecord
# task_type each agent accepts (contracts v1.0); anything else -> failed + UNSUPPORTED_TASK (Slav, Oct 25)
TASK_TYPES = {"agent_3": "retrieve_candidates", "agent_4": "match_resources", "agent_5": "verify_resources"}
CLAIM_FIELDS = ["eligibility_criteria", "required_documents", "application_method", "contact", "deadlines"]

# Geography (Slav, Oct 22): records use explicit service areas ("Sacramento County"); the Supervisor maps
# ZIP -> county and passes both. Statewide programs use "California" and cover every California county.
STATEWIDE = "California"
_names = ["Alameda", "Alpine", "Amador", "Butte", "Calaveras", "Colusa", "Contra Costa", "Del Norte", "El Dorado", "Fresno",
          "Glenn", "Humboldt", "Imperial", "Inyo", "Kern", "Kings", "Lake", "Lassen", "Los Angeles", "Madera", "Marin",
          "Mariposa", "Mendocino", "Merced", "Modoc", "Mono", "Monterey", "Napa", "Nevada", "Orange", "Placer", "Plumas",
          "Riverside", "Sacramento", "San Benito", "San Bernardino", "San Diego", "San Francisco", "San Joaquin",
          "San Luis Obispo", "San Mateo", "Santa Barbara", "Santa Clara", "Santa Cruz", "Shasta", "Sierra", "Siskiyou",
          "Solano", "Sonoma", "Stanislaus", "Sutter", "Tehama", "Trinity", "Tulare", "Tuolumne", "Ventura", "Yolo", "Yuba"]
CA_COUNTIES = {f"{n} County" for n in _names}  # all 58 California counties
# Local fallback only, used when a request carries a ZIP but no county (the Supervisor normally adds the county).
SAC_COUNTY_ZIPS = {str(z) for z in range(95811, 95839)}


def load_kb(path=None):
    with open(path or KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)
    return kb["program_records"], kb["evidence_records"]


def to_counties(geography):
    """Request geography (county names and/or ZIPs) -> county names + issues.
    County names are used as given. A ZIP is only looked up when no county name was supplied."""
    items = [str(g).strip() for g in geography or [] if str(g).strip()]
    counties = {g for g in items if not (g.isdigit() and len(g) == 5)}
    issues = []
    if not counties:
        for z in (g for g in items if g.isdigit() and len(g) == 5):
            if z in SAC_COUNTY_ZIPS:
                counties.add("Sacramento County")
                issues.append(issue("COUNTY_FROM_ZIP_FALLBACK", "warning",
                                    f"No county in the request; Sacramento County taken from the local ZIP fallback for {z}.", z))
            else:
                issues.append(issue("GEOGRAPHY_UNMAPPED", "warning", f"ZIP {z} has no county in the request and is not in the local lookup; no county assumed.", z))
    return counties, issues


def area_covers(service_areas, counties):
    """True if a program's service areas cover any of the person's counties."""
    areas = set(service_areas or [])
    return bool(areas & counties) or (STATEWIDE in areas and bool(counties & CA_COUNTIES))


def issue(code, severity, message, related_ref=None):
    return {"code": code, "severity": severity, "message": message, "related_ref": related_ref}


def envelope(request, agent_id, status, result, issues=None, evidence_refs=None, clarifications=None):
    out = {k: request.get(k) for k in ECHO}
    out.update({"agent_id": agent_id, "schema_version": SCHEMA_VERSION, "status": status,
                "result": result if status != "failed" else {}, "issues": issues or [],
                "clarification_requests": clarifications or [], "evidence_refs": sorted(set(evidence_refs or [])),
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "is_mock": True})  # True until logic is final (contracts v1.0 section 7)
    return out


def check_task(request, agent_id):
    """Returns a failed envelope if task_type is not the one this agent supports, else None."""
    expected = TASK_TYPES[agent_id]
    if request.get("task_type") != expected:
        return envelope(request, agent_id, "failed", {}, [issue("UNSUPPORTED_TASK", "critical",
                        f"{agent_id} supports task_type '{expected}', got '{request.get('task_type')}'.", request.get("task_type"))])
    return None


def bad_request(request, agent_id, missing):
    return envelope(request, agent_id, "failed", {},
                    [issue("INPUT_INCOMPLETE", "critical", f"payload missing: {', '.join(missing)}")])


def build_program_criteria_from_kb(program_ids, kb_path=None):
    """LOCAL TESTING ONLY. In the real system the Supervisor builds program_criteria[] from the KB (Slav, Oct 22).
    Returns contract 4.4 items {program_id, field_path, value, evidence_refs} for geography and eligibility."""
    programs, evidence = load_kb(kb_path)
    by_id = {p["program_id"]: p for p in programs}
    out = []
    for pid in program_ids:
        p = by_id.get(pid)
        if not p:
            continue
        geo_refs = [e["evidence_id"] for e in evidence if e["program_id"] == pid and e["field_path"].startswith("geography")]
        for i, g in enumerate(p["geography"]):
            out.append({"program_id": pid, "field_path": f"geography[{i}]", "value": g, "evidence_refs": geo_refs})
        for i, c in enumerate(p["eligibility_criteria"]):
            out.append({"program_id": pid, "field_path": f"eligibility_criteria[{i}]", "value": c["value"], "evidence_refs": c["evidence_refs"]})
    return out
