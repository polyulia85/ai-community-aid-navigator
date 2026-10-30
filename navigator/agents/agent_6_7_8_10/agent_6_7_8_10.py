"""
Hisham's component: Agents 6, 7, 8 and 10 (mock component, contracts v1.1).
Entry point for the Supervisor (Slav's integration instructions):  handle(request) -> result
Rule IDs follow Slav's Agent_7_10_IO_Contracts_Proposal (Q1-Q10 for Agent 7, V1-V13 for Agent 10).
Python standard library only.
"""
import re
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"
IS_MOCK = True  # wording templates and data are mock until Silver's records are connected

# ================================================================ envelope

def _envelope(request, status, result, issues=None, evidence_refs=None):
    """AgentResult that echoes the request (Supervisor check S2)."""
    return {
        "request_id": request["request_id"], "run_id": request["run_id"],
        "case_id": request["case_id"], "case_version": request["case_version"],
        "correlation_id": request["correlation_id"], "agent_id": request["role_id"],
        "schema_version": SCHEMA_VERSION, "status": status, "result": result,
        "issues": issues or [], "clarification_requests": [],
        "evidence_refs": evidence_refs or [],
        "generated_at": datetime.now(timezone.utc).isoformat(), "is_mock": IS_MOCK,
    }


def _issue(code, severity, message, related_ref=None):
    return {"code": code, "severity": severity, "message": message, "related_ref": related_ref}


TASK_TYPES = {"agent_6": "prioritize_actions", "agent_7": "review_stage", "agent_8": "build_plan", "agent_10": "validate_plan"}


def handle(request):
    """Single entry point. Routes by role_id."""
    role = request.get("role_id")
    handlers = {"agent_6": agent_6, "agent_7": agent_7, "agent_8": agent_8, "agent_10": agent_10}
    if role not in handlers:
        return _envelope(request, "failed", {}, [_issue("UNSUPPORTED_ROLE", "critical", f"Role {role} is not handled here")])
    expected = TASK_TYPES[role]
    if request.get("task_type") != expected:
        return _envelope(request, "failed", {}, [_issue("UNSUPPORTED_TASK", "critical",
                         f"{role} handles task_type '{expected}', got '{request.get('task_type')}'")])
    try:
        return handlers[role](request)
    except (KeyError, TypeError) as e:  # missing or null input field (for example needs: null)
        return _envelope(request, "partial", {}, [_issue("INPUT_INCOMPLETE", "critical", f"Missing or empty input field: {e}")])

# ================================================================ input helpers (accept both layouts)

def _availability(p):
    if isinstance(p.get("availability"), dict):
        return p["availability"]
    return {a["program_id"]: a["availability"] for a in p.get("program_availability", [])}


def _reopen_date(p, program_id):
    """Reopening date of a temporarily_closed program, only if an evidence record states it (contract 4.6)."""
    for e in p.get("evidence_records", []):
        if e.get("program_id") == program_id and str(e.get("field_path", "")).startswith("availability"):
            eff = str(e.get("effective_date") or "")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", eff):
                return eff, e["evidence_id"]  # KB stores the reopening date here
            m = re.search(r"\d{4}-\d{2}-\d{2}", str(e.get("claim_value", "")))  # fallback: ISO date in the text
            if m:
                return m.group(0), e["evidence_id"]
    return None, None


def _short_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %-d")
    except (ValueError, TypeError):
        return str(iso)


def _timing(p, program_id):
    for t in p.get("timing", []):
        if t.get("program_id") == program_id:
            return t
    return {}


def _facts(request, p):
    facts = list(request.get("allowed_case_facts", [])) + list(p.get("case_facts", []))
    return {f["field"]: f for f in facts}


def _deadline_claims(program_id, claims):
    return [c for c in claims if c["program_id"] == program_id and c["field_path"].startswith("deadlines")]


def _deadline_info(program_id, claims):
    """Official deadline only from Agent 5 evidence. Conflicts are never resolved silently."""
    dl = _deadline_claims(program_id, claims)
    conflicting = [c for c in dl if c["verification_status"] == "conflicting"]
    if conflicting:
        dates = []
        for c in conflicting:
            dates += re.findall(r"\d{4}-\d{2}-\d{2}", str(c["claim_value"]))
        return {"status": "conflicting", "dates": sorted(set(dates))}
    verified = [c for c in dl if c["verification_status"] == "verified" and c["claim_value"]]
    if verified:
        return {"status": "verified", "value": verified[0]["claim_value"]}
    return None


def _program_label(match):
    """Organization and program name for card titles (v1.1 4.8), when the Supervisor passes them."""
    org, name = (match.get("organization") or "").strip(), (match.get("program_name") or "").strip()
    if org and name and not name.lower().startswith(org.lower()):
        return f"{org}, {name}"
    return name or org


def _subcat(match, needs):
    if match.get("subcategory"):
        return match["subcategory"]
    n = needs.get(match["need_ids"][0], {})
    return n.get("subcategory")

# ================================================================ wording (Technical Design 14.2 templates)

TEMPLATES = {
    #                        title                          offers                                         next step                                                                                                     why it is ordered here
    "food_pantry":           ("Visit a local food pantry", "offers free food in your area", "Check the posted hours and visit during an open time.", "Food is running low, and a pantry is usually the fastest way to get food."),
    "calfresh_benefits":     ("Check food benefits", "provides ongoing help buying food", "Contact the provider or apply through the official site. They decide eligibility based on your household.", "Food is running low this week, and benefits take time, so starting now helps."),
    "unemployment_insurance":("Apply for unemployment benefits", "can replace part of lost wages after a layoff", "Start the online application. Have your last employer's details and last day worked ready.", "Income replacement supports your other needs, and payments take time to start, so file early."),
    "rental_assistance":     ("Ask about rent help", "offers help with rent in Sacramento", "Contact the provider to confirm requirements and whether assistance is currently available.", "Your rent date is close, so contacting this program early gives the most time."),
    "eviction_prevention":   ("Ask about help to stay in your home", "helps tenants at risk of losing their housing", "Contact the provider to ask what help is available and what documents to bring, such as any notice from your landlord.", "Acting before a housing deadline gives you the most options."),
    "emergency_shelter":     ("Ask about emergency housing", "connects people to emergency shelter and housing help", "Contact the provider to ask about current openings and how to get connected.", "A safe place to stay comes first if your housing is at risk."),
    "motel_voucher":         ("Ask about a short-term motel stay", "may offer short-term motel stays in some situations", "Contact the provider to ask whether motel help is available and who can get it.", "Short-term housing can bridge the gap while other help starts."),
    "housing_legal_aid":     ("Get free legal advice about your housing", "offers legal help with housing problems", "Contact the provider to ask for advice about your housing situation.", "Legal advice early can protect your options."),
    "cash_aid":              ("Ask about cash aid", "may provide cash help for families with children", "Contact the county or apply through the official site. They decide eligibility based on your household.", "Cash help can cover basics while other income is restored."),
    "disability_family_leave": ("Check disability or family leave benefits", "can replace part of your pay if you cannot work for health or family reasons", "Check the official site for how to apply and what records are needed.", "Starting early helps, since payments take time."),
    "employment_services":   ("Get help finding work", "offers free job search help and training", "Contact the provider or visit the official site to see what services are available.", "Finding new work supports all your other needs."),
}
DEFAULT = ("Contact the organization", "may help with this need", "Contact the organization directly to confirm requirements and current availability.", "This addresses one of the needs you described.")
FACT_LABELS = {
    "current_monthly_income": "Your current monthly income",
    "current_household_monthly_income": "Your current household income",
    "landlord_notice_exists": "Whether you have received a written notice from your landlord",
    "household_gross_monthly_income": "Your household's current gross monthly income",  # v1.1 name
    "has_written_eviction_notice": "Whether you have received a written notice from your landlord",  # v1.1 name (change request 2)
}
GROUP_ORDER = {"first": 0, "parallel": 1, "later": 2}


def _fmt_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %-d, %Y")
    except (ValueError, TypeError):
        return str(iso)


def _uncertainty(match, p):
    pid, notes = match["program_id"], []
    for fact in match.get("missing_case_facts", []):
        label = FACT_LABELS.get(fact, f"This detail ({fact.replace('_', ' ')})")
        notes.append(f"{label} is not known yet. Please confirm with the provider; they decide eligibility.")
    if _availability(p).get(pid) == "unknown":
        notes.append("Current availability of this program is unknown. Confirm with the provider.")
    dl = _deadline_info(pid, p.get("checked_claims", []))
    if dl and dl["status"] == "conflicting":
        dates = " and ".join(_fmt_date(d) for d in dl["dates"])
        notes.append(f"Official sources give different deadlines: {dates}. Confirm with the provider before relying on either.")
    return notes

# ================================================================ Agent 6: prioritization

def agent_6(request):
    """Order actions by urgency, deadlines, dependencies and parallel work. No numeric formula (P6 rules)."""
    p = request["payload"]
    needs = {n["need_id"]: n for n in p["needs"]}
    facts = _facts(request, p)
    claims = p.get("checked_claims", [])
    actions = []

    def add(**kw):
        a = {"action_id": f"act_{len(actions) + 1:02d}", "need_id": None, "program_id": None, "suggested_priority": None,
             "order_group": "parallel", "rationale": "", "dependency_ids": [], "official_deadline": None,
             "user_target_date": None, "estimated_processing_time": None, "evidence_refs": [],
             "uncertainty_notes": [], "user_override_allowed": True}
        a.update(kw)
        actions.append(a)
        return a

    app_ids = []
    for m in p["matches"]:
        if m["match_status"] == "confirmed_mismatch":
            continue  # never recommended
        need = needs[m["need_ids"][0]]
        sub = _subcat(m, needs)
        why = TEMPLATES.get(sub, DEFAULT)[3]
        group = {"immediate": "first", "high": "parallel", "unknown": "parallel"}.get(need["urgency"], "later")
        timing = _timing(p, m["program_id"])
        user_date = timing.get("user_target_date")
        if not user_date and need["category"] == "housing_assistance" and "rent_due_date" in facts:
            user_date = facts["rent_due_date"]["value"]  # the user's own date, never an official deadline
        if user_date:
            why += f" You told us your date is {_fmt_date(user_date)} (your date, not a program deadline)."
        dl = _deadline_info(m["program_id"], claims)
        dependency = []
        if dl and dl["status"] == "conflicting":
            dates = " and ".join(_fmt_date(d) for d in dl["dates"])
            closed = _availability(p).get(m["program_id"]) == "temporarily_closed"
            confirm = add(need_id=need["need_id"], program_id=m["program_id"], order_group="later" if closed else "first",
                          rationale=f"Official sources disagree on the application deadline ({dates}). Confirm which one applies before applying.",
                          evidence_refs=[r for c in _deadline_claims(m["program_id"], claims) for r in c["evidence_refs"]],
                          uncertainty_notes=[f"Official sources give different deadlines: {dates}. Confirm with the provider which one applies."]
                          + (["This program is temporarily closed right now. Confirm the deadline when it reopens."] if closed else []))
            dependency = [confirm["action_id"]]
        notes = _uncertainty(m, p)
        refs = list(m["evidence_refs"])
        if _availability(p).get(m["program_id"]) == "temporarily_closed":
            group = "later"  # never presented as current help (contract 4.6)
            reopen, ev = _reopen_date(p, m["program_id"])
            if reopen:
                after = f", after your {_short_date(user_date)} date" if user_date and reopen > user_date else ""
                why = f"Temporarily closed. Reopens {_short_date(reopen)}{after}. Use an open option first."
                notes.append(f"This program is temporarily closed and reopens {_fmt_date(reopen)}{after}.")
                refs.append(ev)
            else:
                why = "Temporarily closed. No reopening date is published. Use an open option first."
                notes.append("This program is temporarily closed. No reopening date was found; check with the provider later.")
        a = add(need_id=need["need_id"], program_id=m["program_id"], order_group=group, rationale=why,
                dependency_ids=dependency,
                official_deadline=dl["value"] if dl and dl["status"] == "verified" else None,
                user_target_date=user_date, estimated_processing_time=timing.get("estimated_processing_time"),
                evidence_refs=refs, uncertainty_notes=notes)
        if sub in ("calfresh_benefits", "unemployment_insurance"):
            app_ids.append(a["action_id"])
    if app_ids:
        add(order_group="later", rationale="This depends on the applications above being submitted first.", dependency_ids=app_ids)
    # an open program for the same need as a closed one goes first
    avail = _availability(p)
    closed_needs = {a["need_id"] for a in actions if a["program_id"] and avail.get(a["program_id"]) == "temporarily_closed"}
    for a in actions:
        if a["need_id"] in closed_needs and a["program_id"] and avail.get(a["program_id"]) != "temporarily_closed" and not a["dependency_ids"]:
            a["order_group"] = "first"
            a["rationale"] += " This is the open option for this need while another program is closed."
    actions.sort(key=lambda a: GROUP_ORDER[a["order_group"]])
    group_counters = {}
    for a in actions:
        g = a["order_group"]
        group_counters[g] = group_counters.get(g, 0) + 1
        a["suggested_priority"] = group_counters[g]
    covered = {a["need_id"] for a in actions}
    issues = [_issue("COVERAGE_GAP", "warning", f"No action found for {n}", n) for n in needs if n not in covered]
    return _envelope(request, "completed", {"proposed_actions": actions}, issues)

# ================================================================ Agent 8: plan builder

def agent_8(request):
    """Turn ordered actions into Action Cards. No new claims (B8 rules)."""
    p = request["payload"]
    matches = {m["program_id"]: m for m in p["matches"]}
    needs = {n["need_id"]: n for n in p["needs"]}
    acts = p["proposed_actions"]
    id_map = {a["action_id"]: f"card_{i:02d}" for i, a in enumerate(acts, 1)}
    cards = []
    for a in acts:
        m = matches.get(a["program_id"])
        is_confirm = a["rationale"].startswith("Official sources disagree")
        if m and is_confirm:
            title, reason = "Confirm the application deadline", "The program's published deadline is not clear."
            next_step = "Call or check with the provider which deadline applies."
        elif m:
            title, offers, next_step, _ = TEMPLATES.get(_subcat(m, needs), DEFAULT)
            label = _program_label(m)
            if label:
                title = f"{title}: {label}"
            reason = f"This program may be relevant to your situation because it {offers}."
            if a["rationale"].startswith("Temporarily closed"):
                reopen = re.search(r"Reopens ([A-Z][a-z]{2} \d+(?:, after your [A-Z][a-z]{2} \d+ date)?)", a["rationale"])
                title = f"{title} (reopens {reopen.group(1)})" if reopen else f"{title} (closed for now)"
                reason = f"This program is temporarily closed right now. It may be relevant later because it {offers}."
                next_step = "Use the open option above first. Check back with this program when it reopens."
        else:
            title, reason = "Follow up on your applications", "Checking in helps you catch any requests for more information."
            next_step = "After applying, watch for letters or messages and respond to any requests for documents."
        related = m["need_ids"] if m else sorted({x["need_id"] for x in acts if x["action_id"] in a["dependency_ids"]})
        cards.append({
            "card_id": id_map[a["action_id"]], "source_action_ids": [a["action_id"]], "related_need_ids": related, "program_id": a["program_id"],
            "action_title": title, "reason": reason, "next_step": next_step, "priority_reason": a["rationale"],
            "order_group": a["order_group"], "dependency_card_ids": [id_map[d] for d in a["dependency_ids"]],
            "source_refs": a["evidence_refs"], "uncertainty_notes": a["uncertainty_notes"],
            "official_deadline": a["official_deadline"], "user_target_date": a["user_target_date"],
            "processing_estimate": a["estimated_processing_time"], "progress_status": "not_started",
        })
    repair = p.get("repair_flags")
    if repair:
        flagged = {f["card_id"] for f in repair if f.get("card_id")}
        cards = [c for c in cards if c["card_id"] in flagged]
        for c in cards:
            for f in (f for f in repair if f.get("card_id") == c["card_id"]):
                rule = f.get("rule_id")
                if rule in ("V1", "V2"):  # guarantees or shaky facts in wording
                    c["processing_estimate"] = None
                    c["uncertainty_notes"].append("The provider decides eligibility and timing.")
                elif rule in ("V5", "V9"):  # wrong or chosen official deadline
                    c["official_deadline"] = None
                    if rule == "V5":
                        c["uncertainty_notes"].append("Official sources give different deadlines. Confirm with the provider which one applies.")
                elif rule == "V8":  # contact or link not in evidence
                    for k in ("action_title", "reason", "next_step"):
                        c[k] = URL_OR_PHONE.sub("the provider's official contact", c[k])
                elif rule == "V4":  # closed or unknown shown as open
                    c["order_group"] = "later" if "closed" in " ".join(c["uncertainty_notes"]).lower() else c["order_group"]
                elif rule == "V10":
                    c["progress_status"] = "not_started"
        result = {"plan_version": str(p.get("plan_version", "plan_v1")), "action_cards": cards,
                  "potential_options": [], "coverage_gaps": [], "repaired_card_ids": sorted(flagged)}
        return _envelope(request, "completed", result, evidence_refs=sorted({r for c in cards for r in c["source_refs"]}))
    covered = {n for c in cards for n in c["related_need_ids"]}
    gaps = [{"need_id": n, "note": "We have not found a verified program for this need yet. We will not suggest anything we cannot support."}
            for n in needs if n not in covered]
    result = {"plan_version": str(p.get("plan_version", "plan_v1")), "action_cards": cards, "potential_options": [], "coverage_gaps": gaps}
    return _envelope(request, "completed", result, evidence_refs=sorted({r for c in cards for r in c["source_refs"]}))

# ================================================================ Agent 7: intermediate quality

CRITICAL_FIELDS = ("deadlines", "contact", "availability")
INJECTION = re.compile(r"ignore (all |any )?(previous|prior|above) instructions|disregard (the |all )?(previous|above)|"
                       r"you are now|system prompt|mark this program (as )?verified|act as (an? )?(admin|assistant)", re.I)


def _strings(obj, path="stage_result"):
    """Walk every text value in a result, so retrieved content can be screened (Q9)."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _strings(v, f"{path}[{i}]")


def agent_7(request):
    """Review a stage result (Agents 3-5). Reports findings, never deletes (Q rules)."""
    p = request["payload"]
    sr = p["stage_result"]
    findings = []

    def add(rule, sev, pid, desc, action, field=None, refs=None, need=None):
        findings.append({"finding_id": f"F7-{len(findings) + 1:03d}", "rule_id": rule, "severity": sev,
                         "program_id": pid, "need_id": need, "field_path": field, "evidence_refs": refs or [],
                         "description": desc, "recommended_action": action})

    matches = sr.get("matches", [])
    known = {m["program_id"] for m in matches}
    need_of = {m["program_id"]: m["need_ids"][0] for m in matches}
    claims = sr.get("checked_claims", [])
    ev_ids = {e["evidence_id"] for e in p.get("evidence_records", [])}
    conflict_groups = {}
    for c in claims:
        pid, fp = c["program_id"], c["field_path"]
        crit = fp.startswith(CRITICAL_FIELDS)
        if known and pid not in known:
            add("Q6", "critical", pid, "Claim references a program that is not in the matches", "recheck_source", fp)
        if c["verification_status"] == "verified" and (not c.get("evidence_refs") or (ev_ids and not set(c["evidence_refs"]) <= ev_ids)):
            add("Q1", "critical" if crit else "warning", pid, "Verified claim has no resolvable evidence", "omit_unsupported_claim", fp)
        if c["verification_status"] == "conflicting":
            conflict_groups.setdefault((pid, fp), []).append(c)
    for (pid, fp), group in conflict_groups.items():
        values = {str(c.get("claim_value")) for c in group if c.get("claim_value") is not None}
        if len(values) < 2 and not any(re.search(r"\bvs\b|\d{4}-\d{2}-\d{2}.*\d{4}-\d{2}-\d{2}", str(c.get("claim_value"))) for c in group):
            add("Q3", "warning", pid, f"{fp} is labeled conflicting but only one published value exists (missing information is unknown, not conflicting)",
                "recheck_source", fp, [r for c in group for r in c["evidence_refs"]], need_of.get(pid))
            continue
        refs = [r for c in group for r in c["evidence_refs"]]
        add("Q2", "critical" if fp.startswith(CRITICAL_FIELDS) else "warning", pid,
            f"Sources give different values for {fp}", "show_conflict_and_add_provider_confirmation", fp, refs, need_of.get(pid))
    # Q4: closure inferred from a failed website check
    failed = {c["program_id"] for c in claims if re.search(r"fail|timeout|timed out|unreachable|could not (load|reach)", str(c.get("issue") or ""), re.I)}
    for pid, status in _availability(sr).items():
        if status == "temporarily_closed" and pid in failed:
            add("Q4", "critical", pid, "Program marked temporarily_closed, but the only signal is a failed website check",
                "recheck_source", "availability")
    # Q9: instructions hidden in retrieved content (treated as data, never followed)
    for path, text in _strings(sr):
        if INJECTION.search(text):
            add("Q9", "critical", None, f"Retrieved content contains instructions to the AI at {path}; ignored",
                "omit_unsupported_claim", path)
    # Q10: external discovery candidate presented as a Knowledge Base entry
    for cand in sr.get("candidate_programs", []):
        scope = cand.get("search_scope", sr.get("search_scope"))
        if scope == "external_discovery" and (cand.get("verification_status") == "verified" or cand.get("kb_record") is True):
            add("Q10", "warning", cand["program_id"], "External discovery candidate labeled as a verified Knowledge Base entry",
                "recheck_source")
    for m in matches:
        pid = m["program_id"]
        if m["match_status"] == "confirmed_mismatch" and not m.get("mismatch_criteria"):
            add("Q5", "critical", pid, "Confirmed mismatch without a named rule", "request_clarification")
        elif m["match_status"] == "confirmed_mismatch" and m.get("missing_case_facts"):
            add("Q5", "critical", pid, "Confirmed mismatch while needed facts are still unknown (unknown is never a mismatch, e.g. unknown income)",
                "request_clarification")
        elif m["match_status"] == "supported_match" and m.get("missing_case_facts"):
            add("Q5", "warning", pid, "supported_match while required facts are missing: " + ", ".join(m["missing_case_facts"]),
                "request_clarification")
    # Q7: evidence age. Without an agreed window, report the age only (info); with a window, warn when older.
    window = p.get("recency_window_days")
    now = datetime.now(timezone.utc)
    oldest = {}
    for c in claims:
        try:
            ts = datetime.fromisoformat(str(c.get("checked_at")).replace("Z", "+00:00"))
        except ValueError:
            continue
        age = (now - ts).days
        if c["program_id"] not in oldest or age > oldest[c["program_id"]][0]:
            oldest[c["program_id"]] = (age, c["field_path"], c.get("checked_at"))
    for pid, (age, fp, when) in oldest.items():
        if window is None:
            add("Q7", "info", pid, f"Oldest evidence checked {age} day(s) ago ({when}); freshness window not agreed yet", "no_action", fp)
        elif age > window:
            add("Q7", "warning", pid, f"Evidence is {age} day(s) old, older than the {window}-day window", "recheck_source", fp)
    covered = {n for m in matches for n in m["need_ids"]}
    for n in p.get("needs", []):
        if matches and n["need_id"] not in covered:
            add("Q8", "warning", None, f"Need {n['need_id']} has no candidate or coverage gap", "report_coverage_gap", need=n["need_id"])
    real = [f for f in findings if f["severity"] != "info"]  # info findings (evidence age) do not change the assessment
    result = {"stage": p["stage"], "stage_assessment": "issues_found" if real else "clear", "findings": findings}
    issues = [_issue(f["rule_id"], f["severity"], f["description"], f["program_id"]) for f in findings]
    return _envelope(request, "completed", result, issues)

# ================================================================ Agent 10: final validation

GUARANTEES = ["you will receive", "you will definitely", "you will get", "you qualify", "you are eligible",
              "guaranteed", "you have been approved", "you will be approved"]
# V13 only fires when the card asks the user to give the data to the Navigator itself.
# "The county may ask for your Social Security card" is a normal program requirement and passes.
ASK_NAVIGATOR = r"\b(enter|type|share|send|give|provide|upload|paste)\b[^.]*\b(here|with us|to us|this app|the app|this chat|the chat|navigator)\b"
PROHIBITED = [r"\bssn\b", r"social security number", r"bank account", r"card number", r"routing number"]
URL_OR_PHONE = re.compile(r"https?://\S+|\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}")
CONFIRMED_WORDS = re.compile(r"\b(is|are|has been|have been|was)\s+(verified|confirmed)\b|\bconfirmed (open|available|deadline)\b", re.I)
MISSING_FROM_SITE = re.compile(r"(website|site|page) (does not|doesn't|did not) (list|show|mention|include)|not (listed|published) on (the|their) (website|site|page)", re.I)
notes_all = lambda c: " ".join(c.get("uncertainty_notes", [])).lower()
SEVERITY = {"V1": "critical", "V2": "critical", "V3": "critical", "V4": "critical", "V5": "critical",
            "V6": "warning", "V7": "warning", "V8": "critical", "V9": "warning", "V10": "critical",
            "V11": "warning", "V12": "warning", "V13": "critical"}


def agent_10(request):
    """Final PASS/FLAG review. Flags only the affected cards (Proposal #6)."""
    p = request["payload"]
    plan = p.get("plan", p)  # accepts {"plan": {...}} or the plan fields at payload level
    cards = plan["action_cards"]
    matches = {m["program_id"]: m for m in p["matches"]}
    claims = p.get("checked_claims", [])
    avail = _availability(p)
    evidence_text = " ".join(str(e.get("source_url", "")) + " " + str(e.get("claim_value", "")) for e in p.get("evidence_records", []))
    flags = []

    def flag(card, rule, reason, fix, claim=""):
        sev = SEVERITY[rule]
        flags.append({"flag_id": f"FLAG-{len(flags) + 1:03d}", "card_id": card, "rule_id": rule, "severity": sev,
                      "claim_text": claim, "reason": reason, "evidence_refs": [], "required_correction": fix,
                      "blocks_release": sev == "critical"})

    for c in cards:
        cid, pid = c["card_id"], c.get("program_id")
        fields = [c.get("action_title", ""), c.get("reason", ""), c.get("next_step", ""), c.get("priority_reason", "")]
        if isinstance(c.get("processing_estimate"), str):
            fields.append(c["processing_estimate"])
        text = " ".join(fields)
        low = text.lower()

        hit = next((g for g in GUARANTEES if g in low), None)
        if hit:
            sentence = next((s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if hit in s.lower()), hit)
            flag(cid, "V1", f"Unsupported guarantee: '{hit}'", "Remove the guarantee; describe the program as possibly relevant and say the provider decides.", sentence)
        if pid is not None and pid not in matches:
            flag(cid, "V8", f"Program {pid} is not in the evidence", "Remove the card or use a real candidate from Agents 3-5.")
        if pid in matches and matches[pid]["match_status"] == "confirmed_mismatch":
            flag(cid, "V3", "Confirmed mismatch shown as a recommendation", "Remove from recommended cards.")
        if pid in matches and avail.get(pid) != "confirmed_open" and re.search(r"\b(is open|currently open|accepting applications)\b", low):
            flag(cid, "V4", "Program shown as open without evidence", "Say availability must be confirmed with the provider.")
        if pid and avail.get(pid) == "temporarily_closed":
            said = (low + " " + notes_all(c)).lower()
            if c.get("order_group") != "later" or not re.search(r"closed|reopen", said):
                flag(cid, "V4", "Temporarily closed program shown as current help",
                     "Move to later and say it is closed (with the reopening date only if in evidence); put an open option first.")
        # V2: unknown, unverified or conflicting information described as confirmed
        shaky = [x for x in claims if x["program_id"] == pid and x["verification_status"] in ("conflicting", "unverified", "needs_review")]
        if pid and (shaky or avail.get(pid) == "unknown") and CONFIRMED_WORDS.search(low):
            flag(cid, "V2", "Information that is unknown or not verified is described as confirmed",
                 "Describe it as unconfirmed and add a confirm-with-provider step.", CONFIRMED_WORDS.search(text).group(0))
        # V7: says a website lacks information when the website could not be reached
        unreachable = any(x["program_id"] == pid and re.search(r"fail|timeout|timed out|unreachable|could not (load|reach)", str(x.get("issue") or ""), re.I) for x in claims)
        if unreachable and MISSING_FROM_SITE.search(low + " " + notes_all(c)):
            flag(cid, "V7", "Says the website lacks information, but the website could not be reached",
                 "Use neutral wording: current details need to be confirmed with the provider.")
        dl = c.get("official_deadline")
        dl_value = dl.get("value") if isinstance(dl, dict) else dl
        info = _deadline_info(pid, claims) if pid else None
        notes = " ".join(c.get("uncertainty_notes", [])).lower()
        if info and info["status"] == "conflicting":
            if dl_value or "confirm" not in notes:
                flag(cid, "V5", "Conflicting deadline is hidden or one date was chosen", "Show both dates and add a confirm-with-provider step.")
        elif dl_value and not (info and info["status"] == "verified"):
            flag(cid, "V9", "A date is shown as an official deadline without verified evidence (for example the user's own date)",
                 "Show user dates as the user's date, never as an official deadline.")
        if not c.get("next_step", "").strip():
            flag(cid, "V6", "Card has no grounded next step", "Add a concrete next step.")
        for found in URL_OR_PHONE.findall(text):
            if found not in evidence_text:
                flag(cid, "V8", f"Contact or link not in evidence: {found}", "Remove it or use the verified contact.")
        if c.get("progress_status") != "not_started":
            flag(cid, "V10", "Progress status was set without user input", "Set progress_status to not_started.")
        if any(re.search(pat, low) for pat in PROHIBITED) and re.search(ASK_NAVIGATOR, low):
            flag(cid, "V13", "Asks for prohibited personal data (proposed rule)", "Remove the request.")

    for opt in plan.get("potential_options", []):
        if not opt.get("official_link") or not opt.get("what_needs_checking"):
            flag(None, "V11", f"Potential option {opt.get('program_id')} lacks an official link or what needs checking", "Add both.")
    covered = {n for c in cards for n in c.get("related_need_ids", [])} | {g["need_id"] for g in plan.get("coverage_gaps", [])}
    for n in p["needs"]:
        if n["need_id"] not in covered:
            flag(None, "V12", f"Need {n['need_id']} is missing from the plan with no coverage gap", "Add a card or a coverage-gap note.")

    issues, unchecked = [], set()
    if "evidence_records" in p:  # only checkable when evidence was passed in
        known_ev = {e["evidence_id"] for e in p["evidence_records"]}
        for c in cards:
            missing = [r for r in c.get("source_refs", []) if r not in known_ev]
            if missing:
                unchecked.add(c["card_id"])
                issues.append(_issue("INPUT_INCOMPLETE", "warning",
                                     f"Card cites evidence that was not passed in: {', '.join(missing)}; card not checked", c["card_id"]))
    blocked = {f["card_id"] for f in flags if f["blocks_release"] and f["card_id"]}
    result = {"verdict": "FLAG" if flags else "PASS", "repair_round": p.get("repair_round", 0), "flags": flags,
              "passed_card_ids": [c["card_id"] for c in cards if c["card_id"] not in blocked | unchecked]}
    return _envelope(request, "partial" if unchecked else "completed", result, issues)
