"""Supervisor builders: the inputs for each agent (Shared JSON Contracts v1.0, sections 4 and 5.1).

Agents never call each other. The Supervisor keeps one CaseState and builds every
AgentRequest from it, passing each agent only what it needs.
"""
import itertools
import json

from navigator.supervisor import contract as C
from navigator.supervisor.checks import mask_user_text

# ZIP -> county for the demo area. The Supervisor adds the county (contract 3.2).
# Extend only with ZIPs checked against an official source.
ZIP_TO_COUNTY = {"95823": "Sacramento County"}

# Fields the plan shows; Agent 5 verifies them (contract 4.5)
FIELDS_TO_VERIFY = ("eligibility_criteria", "required_documents", "application_method",
                    "contact", "deadlines", "availability")


# ---------------------------------------------------------------- KB
def load_kb(path):
    """Verified KB file (Silver's format): {"program_records": [...], "evidence_records": [...]}."""
    with open(path, encoding="utf-8") as f:
        kb = json.load(f)
    programs = {p["program_id"]: p for p in kb["program_records"]}
    evidence = {e["evidence_id"]: e for e in kb["evidence_records"]}
    return programs, evidence


# ---------------------------------------------------------------- case state
class CaseState:
    """Everything the Supervisor knows about one case. Only the Supervisor writes here."""

    def __init__(self, case_id, run_id, correlation_id, source_policy="verified_kb_only"):
        self.case_id = case_id
        self.run_id = run_id
        self.correlation_id = correlation_id
        self.source_policy = source_policy
        self.case_version = 1
        self.needs = []            # Need objects (contract 3.1)
        self.case_facts = []       # CaseFact objects (contract 3.2), confirmed by the user
        self.already_asked = []    # fact_keys asked, including skipped or declined
        self.results = {}          # request_id -> accepted AgentResult
        self._counter = itertools.count(1)

    def next_request_id(self):
        return f"req-{next(self._counter):04d}"

    def fact(self, field):
        for f in self.case_facts:
            if f["field"] == field:
                return f.get("value")
        return None

    def bump_version(self):
        """Call when the user changes or confirms facts: older results become stale (S3)."""
        self.case_version += 1


def make_request(state, role_id, task_type, payload, task_scope="all_needs",
                 allowed_case_facts=None, upstream_result_refs=None):
    assert task_type in C.TASK_TYPES[role_id], f"{task_type} is not a task of {role_id}"
    return {
        "request_id": state.next_request_id(),
        "run_id": state.run_id,
        "case_id": state.case_id,
        "case_version": state.case_version,
        "schema_version": C.SCHEMA_VERSION,
        "role_id": role_id,
        "task_type": task_type,
        "task_scope": task_scope,
        "allowed_case_facts": allowed_case_facts or [],
        "upstream_result_refs": upstream_result_refs or [],
        "source_policy": state.source_policy,
        "correlation_id": state.correlation_id,
        "payload": payload,
    }


# ---------------------------------------------------------------- Agent 1, 2
def agent1_request(state, story_text, locale="en-US"):
    """S0 runs here: the story is masked before Agent 1 sees it."""
    masked, issues = mask_user_text(story_text)
    req = make_request(state, "agent_1", "understand_story",
                       {"story_text": masked, "locale": locale}, task_scope="full_story")
    return req, issues


def confirm_agent1(state, agent1_result, corrections=None):
    """The user confirms the summary (contract 5.1). Proposed needs and claims become confirmed.

    corrections = {"cash_on_hand_approx": 300, ...} replaces values the user corrected.
    In the local demo the confirmation is simulated; in the app it comes from the UI.
    """
    corrections = corrections or {}
    res = agent1_result["result"]
    state.needs = [dict(n, confirmation_status="confirmed") for n in res.get("proposed_needs", [])]
    facts = []
    for f in res.get("factual_claims", []):
        f = dict(f, confirmation_status="confirmed", source="user_confirmed")
        if f["field"] in corrections:
            f["value"] = corrections[f["field"]]
        facts.append(f)
    state.case_facts = facts
    state.bump_version()


def agent2_request(state, candidate_requirements=None):
    payload = {"needs": state.needs, "case_facts": state.case_facts,
               "already_asked": state.already_asked}
    if candidate_requirements:
        payload["candidate_requirements"] = candidate_requirements
    return make_request(state, "agent_2", "clarify_case", payload)


def apply_need_updates(state, agent2_result):
    """Contract 4.2: Agent 2 may update urgency of existing needs. Only known need_ids and allowed values.

    Returns issues for updates that were skipped (unknown need, unknown urgency).
    """
    issues = []
    by_id = {n["need_id"]: n for n in state.needs}
    for u in agent2_result.get("result", {}).get("need_updates", []) or []:
        need = by_id.get(u.get("need_id"))
        if need is None:
            issues.append({"code": "NEED_UPDATE_SKIPPED", "severity": "warning",
                           "message": f"Agent 2 updated unknown need {u.get('need_id')!r}", "related_ref": u.get("need_id")})
            continue
        if u.get("urgency") not in C.ENUMS["urgency"]:
            issues.append({"code": "NEED_UPDATE_SKIPPED", "severity": "warning",
                           "message": f"Agent 2 sent urgency {u.get('urgency')!r} for {need['need_id']}", "related_ref": need["need_id"]})
            continue
        need["urgency"] = u["urgency"]
        need["urgency_reason"] = u.get("urgency_reason")
    return issues


def agent7_request(state, stage, stage_result, evidence, upstream_request_id):
    """Contract 4.7: Agent 7 reviews one stage result, passed unchanged. Only referenced evidence and facts."""
    payload = {"stage": stage, "stage_result": stage_result,
               "evidence_records": _referenced_evidence(evidence, stage_result),
               "case_facts": state.case_facts, "needs": state.needs}
    return make_request(state, "agent_7", "review_stage", payload,
                        upstream_result_refs=[upstream_request_id])


# ---------------------------------------------------------------- Agent 3, 4, 5
def geography(state):
    """County + ZIP (contract 3.2). Returns (list, issues)."""
    zip_code = state.fact("zip_code")
    county = state.fact("county")
    if not county and zip_code:
        county = ZIP_TO_COUNTY.get(str(zip_code))
    geo, issues = [], []
    if county:
        geo.append(county)
    if zip_code:
        geo.append(str(zip_code))
    if zip_code and not county:
        issues.append({"code": "COUNTY_UNKNOWN", "severity": "warning",
                       "message": f"No county on file for ZIP {zip_code}", "related_ref": "zip_code"})
    return geo, issues


def agent3_request(state):
    needs = [{k: n.get(k) for k in ("need_id", "category", "description", "urgency")}
             for n in state.needs]
    geo, issues = geography(state)
    req = make_request(state, "agent_3", "retrieve_candidates",
                       {"needs": needs, "geography": geo, "retrieval_constraints": []})
    return req, issues


def program_criteria(programs, evidence, program_ids):
    """Contract 4.4: {program_id, field_path, value, evidence_refs} for geography and eligibility."""
    out = []
    for pid in program_ids:
        p = programs.get(pid)
        if not p:
            continue
        geo_refs = [e["evidence_id"] for e in evidence.values()
                    if e["program_id"] == pid and e["field_path"].startswith("geography")]
        for i, g in enumerate(p.get("geography", [])):
            out.append({"program_id": pid, "field_path": f"geography[{i}]", "value": g,
                        "evidence_refs": geo_refs})
        for i, c in enumerate(p.get("eligibility_criteria", [])):
            out.append({"program_id": pid, "field_path": f"eligibility_criteria[{i}]",
                        "value": c["value"], "evidence_refs": c.get("evidence_refs", [])})
    return out


def agent4_request(state, agent3_req, agent3_result, programs, evidence):
    cands = agent3_result["result"]["candidate_programs"]
    payload = {"candidate_programs": cands, "case_facts": state.case_facts, "needs": state.needs,
               "program_criteria": program_criteria(programs, evidence, [c["program_id"] for c in cands])}
    return make_request(state, "agent_4", "match_resources", payload,
                        upstream_result_refs=[agent3_req["request_id"]])


def agent5_request(state, agent4_req, agent4_result):
    """Contract 4.5: from Agent 4 matches, excluding confirmed_mismatch."""
    pids = []
    for m in agent4_result["result"]["matches"]:
        if m["match_status"] != "confirmed_mismatch" and m["program_id"] not in pids:
            pids.append(m["program_id"])
    payload = {"programs_to_check": [{"program_id": p, "field_paths": list(FIELDS_TO_VERIFY)} for p in pids],
               "evidence_refs": [], "relevant_case_constraints": []}
    return make_request(state, "agent_5", "verify_resources", payload,
                        upstream_result_refs=[agent4_req["request_id"]])


# ---------------------------------------------------------------- Agent 6, 8, 10
def _referenced_evidence(evidence, *objs):
    ids = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("evidence_refs", "source_refs") and isinstance(v, list):
                    ids.update(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for o in objs:
        walk(o)
    return [evidence[i] for i in sorted(ids) if i in evidence]


def planning_package(state, programs, evidence, agent3_result, agent4_result, agent5_result,
                     agent7_findings=None):
    """The Supervisor's package for Agent 6 (contract 4.6); reused for Agents 8 and 10."""
    cands = agent3_result["result"]["candidate_programs"]
    # Contracts v1.1: the Supervisor adds program_name, subcategory and organization from the KB to each match,
    # so Agents 6, 8 and 10 can name the program on the card. Agent 4's own result is not changed.
    matches = []
    for m in agent4_result["result"]["matches"]:
        m = dict(m)
        rec = programs.get(m.get("program_id"), {})
        if rec.get("program_name"):
            m["program_name"] = rec["program_name"]
        if rec.get("subcategory"):
            m["subcategory"] = rec["subcategory"]
        if rec.get("organization"):
            m["organization"] = rec["organization"]
        matches.append(m)
    claims = agent5_result["result"]["checked_claims"]
    pids = [c["program_id"] for c in cands]

    availability = [{"program_id": p, "availability": programs[p].get("availability", "unknown"),
                     "evidence_refs": [e["evidence_id"] for e in evidence.values()
                                       if e["program_id"] == p and e["field_path"].startswith("availability")]}
                    for p in pids if p in programs]

    # timing: user dates from case facts, official deadlines only from the KB, never invented
    rent_date = state.fact("rent_due_date")
    timing = []
    for c in cands:
        p = programs.get(c["program_id"], {})
        deadlines = p.get("deadlines") or []
        proc = p.get("processing_time")
        for nid in c["matched_need_ids"]:
            need = next((n for n in state.needs if n["need_id"] == nid), {})
            timing.append({
                "need_id": nid, "program_id": c["program_id"],
                "official_deadline": deadlines[0]["value"] if len(deadlines) == 1 else None,
                "user_target_date": rent_date if need.get("category") == "housing_assistance" else None,
                "estimated_processing_time": proc.get("value") if isinstance(proc, dict) else None,
            })

    return {
        "needs": state.needs,
        "candidate_programs": cands,
        "matches": matches,
        "checked_claims": claims,
        "program_availability": availability,
        "timing": timing,
        "evidence_records": _referenced_evidence(evidence, cands, matches, claims, availability),
        "agent7_findings": agent7_findings or [],
    }


def agent6_request(state, package, upstream):
    return make_request(state, "agent_6", "prioritize_actions", package,
                        upstream_result_refs=upstream)


def agent8_request(state, package, agent6_req, agent6_result):
    payload = {k: package[k] for k in ("needs", "matches", "checked_claims",
                                        "program_availability", "evidence_records", "agent7_findings")}
    payload["proposed_actions"] = agent6_result["result"]["proposed_actions"]
    return make_request(state, "agent_8", "build_plan", payload,
                        upstream_result_refs=[agent6_req["request_id"]])


def agent10_request(state, package, agent8_req, agent8_result, repair_round=0):
    plan = agent8_result["result"]
    payload = {
        "plan_version": plan.get("plan_version"),
        "repair_round": repair_round,
        "action_cards": plan.get("action_cards", []),
        "potential_options": plan.get("potential_options", []),
        "coverage_gaps": plan.get("coverage_gaps", []),
        "needs": package["needs"],
        "matches": package["matches"],
        "checked_claims": package["checked_claims"],
        "program_availability": package["program_availability"],
        "evidence_records": package["evidence_records"],
        "open_agent7_findings": package["agent7_findings"],
    }
    return make_request(state, "agent_10", "validate_plan", payload,
                        allowed_case_facts=state.case_facts,
                        upstream_result_refs=[agent8_req["request_id"]])
