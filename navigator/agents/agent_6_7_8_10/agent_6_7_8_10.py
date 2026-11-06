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
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{d:%b} {d.day}"  # portable day without leading zero (works on Windows too)
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
    """Official deadline only from Agent 5 evidence. Conflicts are never resolved silently.

    Treats as conflicting:
    - any claim with verification_status == "conflicting"
    - two or more verified claims with different non-None values
    - a verified claim whose claim_value is None (unknown deadline, cannot be shown)
    """
    dl = _deadline_claims(program_id, claims)
    conflicting = [c for c in dl if c["verification_status"] == "conflicting"]
    if conflicting:
        dates = []
        for c in conflicting:
            dates += re.findall(r"\d{4}-\d{2}-\d{2}", str(c["claim_value"]))
        return {"status": "conflicting", "dates": sorted(set(dates))}
    verified = [c for c in dl if c["verification_status"] == "verified"]
    # A verified claim with claim_value=None means the deadline is unknown; treat as conflict.
    if any(c["claim_value"] is None for c in verified):
        return {"status": "conflicting", "dates": []}
    # Two or more verified claims with different values: pick neither (A6-02).
    values = list(dict.fromkeys(c["claim_value"] for c in verified if c["claim_value"]))
    if len(values) >= 2:
        return {"status": "conflicting", "dates": sorted(values)}
    if values:
        return {"status": "verified", "value": values[0]}
    return None


def _program_label(match):
    """Organization and program name for card titles (v1.1 4.8), when the Supervisor passes them."""
    org, name = (match.get("organization") or "").strip(), (match.get("program_name") or "").strip()
    if org and name and not name.lower().startswith(org.lower()):
        return f"{org}, {name}"
    return name or org


_HOURS_RE = re.compile(
    r"\d{1,2}:\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)"          # HH:MM am/pm
    r"|\d{1,2}\s*(?:a\.m\.|p\.m\.)"                       # H a.m. / H p.m. (no colon)
    r"|monday|tuesday|wednesday|thursday|friday|saturday|sunday"  # named day
    r"|\d+\s+hours?\s+a\s+day",                            # "24 hours a day"
    re.I)

# application_method values that are actual ways to apply (not rules/requirements)
_APP_METHOD_RE = re.compile(
    r"https?://"                            # URL
    r"|\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}"  # phone number
    r"|\b(online|by phone|by mail|by fax|in person)\b"  # named channel
    r"|\b2-1-1\b|\b211\b"                  # 2-1-1 / 211 service line
    r"|(?:call|text)\s+\d{3,}"             # "Call 211", "Call 898-211", etc.
    r"|\b(p\.?o\.?\s*box|po box|mailing address|street address|\d+\s+\w+\s+(st|ave|blvd|dr|rd|way|lane|ln|court|ct)\b)",  # address
    re.I)

# application_method rows that state a rule or requirement, not a way to apply
_RULE_ROW_RE = re.compile(
    r"^(you must|you may|minimum required|paper application forms|applicants under|to be eligible)",
    re.I)


def _extract_hours(text):
    """Return the hours substring if the text contains a time expression, else None."""
    m = _HOURS_RE.search(str(text))
    if not m:
        return None
    # grab from the first time token to end of sentence / value
    return str(text)[m.start():].strip()


def _build_contacts(claims, program_id, evidence_records=None):
    """
    Build contacts[] for an Agent 8 card (v0.7+).
    Only verified claims with a valid checked_at and field_path starting with
    'contact' or 'application_method' are included.
    application_method rows are only included when they are actual ways to apply
    (URL, phone, address, or named channel); rules and requirements are excluded.
    When evidence_records is provided, a contacts item is only included if at
    least one of its evidence_refs exists in evidence_records for the same program_id.
    Returns a list of dicts: {label, value, hours, checked_at, evidence_refs}.
    """
    # build a set of evidence_ids scoped to this program (A8-04)
    if evidence_records is not None:
        valid_ev = {e["evidence_id"] for e in evidence_records if e.get("program_id") == program_id}
    else:
        valid_ev = None
    out = []
    for c in claims:
        if c.get("program_id") != program_id:
            continue
        if c.get("verification_status") != "verified":
            continue
        fp = str(c.get("field_path", ""))
        if not (fp.startswith("contact") or fp.startswith("application_method")):
            continue
        val = c.get("claim_value")
        if not val:
            continue
        when = str(c.get("checked_at") or "")[:10]
        try:
            datetime.strptime(when, "%Y-%m-%d")
        except ValueError:
            continue  # no valid check date — never appears
        # contact rows about lost/stolen cards or EBT account servicing are not actionable
        if fp.startswith("contact") and re.search(r"lost or stolen|EBT Customer Service", str(val), re.I):
            continue
        # application_method rows: exclude rules/requirements; must be actual ways to apply
        if fp.startswith("application_method"):
            if _RULE_ROW_RE.match(str(val)):
                continue
            if not _APP_METHOD_RE.search(str(val)):
                continue
        refs = list(c.get("evidence_refs") or [])
        # A8-04: at least one evidence_ref must be in the program's evidence records
        if valid_ev is not None and not (set(refs) & valid_ev):
            continue
        label = "How to apply" if fp.startswith("application_method") else "Contact"
        # For URL application methods, normalise value to "Apply online: <clean url>"
        raw_val = str(val).strip()
        if label == "How to apply":
            url_m = _URL_RE.search(raw_val)
            if url_m:
                raw_val = f"Apply online: {_clean_url(url_m.group(0))}"
        out.append({
            "label": label,
            "value": raw_val,
            "hours": _extract_hours(val),
            "checked_at": when,
            "evidence_refs": refs,
        })
    return out


_URL_RE = re.compile(r"https?://\S+")
_TRAIL_PUNCT_RE = re.compile(r"[\]\[)(.,;:\"']+$")


def _clean_url(raw):
    """Strip trailing punctuation characters from a URL extracted by _URL_RE."""
    return _TRAIL_PUNCT_RE.sub("", raw)


# Sentence boundary: punctuation followed by whitespace and an uppercase letter/digit
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _first_sentence(text, max_chars=120):
    """Return the first sentence of text, at most max_chars characters.

    Splits on sentence-ending punctuation followed by whitespace + uppercase/digit
    so that abbreviations like a.m., p.m., or 2-1-1 are not treated as sentence ends.
    If the first sentence exceeds max_chars, the trailing clause after the last comma
    is removed first (e.g. ", which EDD describes as…" is dropped).  Only if the result
    is still over max_chars is it cut at the last word boundary (with "…" appended).
    """
    first = _SENT_SPLIT_RE.split(text.strip(), maxsplit=1)[0]
    if len(first) <= max_chars:
        return first
    # Try dropping the trailing comma clause
    shorter = first.rsplit(",", 1)[0]
    if len(shorter) <= max_chars:
        return shorter
    # Final fallback: hard cut at word boundary
    cut = shorter[:max_chars].rsplit(None, 1)[0]
    return cut + "…"


def _next_step_contacts(contacts):
    """
    Return at most 2 contact snippets for next_step (v0.7+):
    1. First "How to apply" item that has a URL → "Apply online: <url> (checked Mon D)."
       If no URL item, the first "How to apply" item with a phone or 2-1-1 pattern.
    2. First "Contact" item with a phone pattern.
    Each non-URL item uses only the first sentence (≤ 120 chars) of the value.
    Double periods are avoided: if the sentence already ends with ".", it is stripped
    before appending " (checked Mon D).".
    """
    _phone_re = re.compile(r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}|\b2-1-1\b|\b211\b", re.I)
    # 1st snippet: URL "How to apply" first; fall back to phone/2-1-1 "How to apply"
    online_url = next((c for c in contacts if c["label"] == "How to apply" and _URL_RE.search(c["value"])), None)
    online_phone = next((c for c in contacts if c["label"] == "How to apply" and _phone_re.search(c["value"])), None)
    online = online_url or online_phone
    phone = next((c for c in contacts if c["label"] == "Contact" and _phone_re.search(c["value"])), None)
    snippets = []
    for item in [online, phone]:
        if item is None:
            continue
        d = datetime.strptime(item["checked_at"], "%Y-%m-%d")
        url_m = _URL_RE.search(item["value"]) if item["label"] == "How to apply" else None
        if url_m:
            snippets.append(f"Apply online: {_clean_url(url_m.group(0))} (checked {d:%b} {d.day}).")
        else:
            sentence = _first_sentence(item["value"])
            # Strip the trailing period so "(checked Mon D)." never follows a period
            if sentence.endswith("."):
                sentence = sentence[:-1]
            snippets.append(f"{sentence} (checked {d:%b} {d.day}).")
    return snippets


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
    "rental_assistance":     ("Ask about rent help", "offers help with rent in Sacramento", "Contact the provider to confirm requirements and whether assistance is currently available.", "Contacting this program early gives the most time to arrange help."),
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
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{d:%B} {d.day}, {d.year}"  # portable day without leading zero (works on Windows too)
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

_FAR_DATE = "9999-99-99"  # sentinel for missing dates in sort keys

# Housing subcategories that must sort before food/income actions when the case
# shows an overdue-housing signal (C-OD2).
_HOUSING_SUBS = {"rental_assistance", "eviction_prevention", "emergency_shelter",
                 "motel_voucher", "housing_legal_aid"}


def _overdue_housing_signal(facts):
    """Return True when the case facts show overdue rent, an eviction notice,
    or a utility shutoff notice (C-OD2 condition).

    Signals:
    - rent_due_date is in the past (relative to today)
    - has_written_eviction_notice / landlord_notice_exists is truthy
    - utility_shutoff_notice is truthy
    """
    today = datetime.now().date()
    rent_due = (facts.get("rent_due_date") or {}).get("value")
    if rent_due:
        try:
            if datetime.strptime(str(rent_due), "%Y-%m-%d").date() <= today:
                return True
        except (ValueError, TypeError):
            pass
    for notice_field in ("has_written_eviction_notice", "landlord_notice_exists",
                         "utility_shutoff_notice"):
        val = (facts.get(notice_field) or {}).get("value")
        if val and str(val).lower() not in ("false", "no", "0", "none", ""):
            return True
    return False


def _sort_key_6(action, housing_first):
    """Sort key for Agent 6 actions (A6-03 + C-OD2).

    Primary: order_group (first < parallel < later).
    Within group: housing sub before non-housing ONLY when housing_first is True.
    Then: earliest official_deadline, user_target_date, processing_time presence.
    """
    g = GROUP_ORDER[action["order_group"]]
    dl = action.get("official_deadline") or _FAR_DATE
    ud = action.get("user_target_date") or _FAR_DATE
    sub = action.get("_subcategory", "")
    is_non_housing = (0 if sub in _HOUSING_SUBS else 1) if housing_first else 0
    has_pt = 0 if action.get("estimated_processing_time") else 1
    return (g, is_non_housing, dl, ud, has_pt)


def agent_6(request):
    """Order actions by urgency, deadlines, dependencies and parallel work. No numeric formula (P6 rules)."""
    p = request["payload"]
    needs = {n["need_id"]: n for n in p["needs"]}
    facts = _facts(request, p)
    claims = p.get("checked_claims", [])
    actions = []

    def add(**kw):
        # A6-01: contract 4.6 allows only need_id (singular); no need_ids field.
        a = {"action_id": f"act_{len(actions) + 1:02d}", "need_id": None,
             "program_id": None, "suggested_priority": None,
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
        sub = _subcat(m, needs)
        dl = _deadline_info(m["program_id"], claims)
        timing = _timing(p, m["program_id"])
        proc_time = timing.get("estimated_processing_time")

        # A6-01: one action per need_id when the match covers multiple needs.
        for need_id in m["need_ids"]:
            need = needs[need_id]
            why = TEMPLATES.get(sub, DEFAULT)[3]
            group = {"immediate": "first", "high": "parallel", "unknown": "parallel"}.get(need["urgency"], "later")
            user_date = timing.get("user_target_date")
            if not user_date and need["category"] == "housing_assistance" and "rent_due_date" in facts:
                user_date = facts["rent_due_date"]["value"]  # the user's own date, never an official deadline
            # A6-04: only append date wording when a real date exists.
            if user_date:
                why += f" You told us your date is {_fmt_date(user_date)} (your date, not a program deadline)."
            dependency = []
            if dl and dl["status"] == "conflicting":
                # A6-02: build a readable date list; handle empty dates (when claim_value was None).
                if dl["dates"]:
                    dates_str = " and ".join(_fmt_date(d) for d in dl["dates"])
                    conflict_note = f"Official sources give different deadlines: {dates_str}. Confirm with the provider which one applies."
                    rationale_text = f"Official sources disagree on the application deadline ({dates_str}). Confirm which one applies before applying."
                else:
                    conflict_note = "The published deadline is unknown. Confirm the deadline with the provider before applying."
                    rationale_text = "The published deadline is unknown. Confirm the deadline with the provider before applying."
                closed = _availability(p).get(m["program_id"]) == "temporarily_closed"
                confirm = add(need_id=need_id, program_id=m["program_id"],
                              order_group="later" if closed else "first",
                              rationale=rationale_text,
                              evidence_refs=[r for c in _deadline_claims(m["program_id"], claims) for r in c["evidence_refs"]],
                              uncertainty_notes=[conflict_note]
                              + (["This program is temporarily closed right now. Confirm the deadline when it reopens."] if closed else []),
                              _subcategory=sub)
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
            # A6-03: if processing_time is longer than time left before target_date, say so.
            if proc_time and user_date:
                try:
                    days_left = (datetime.strptime(user_date, "%Y-%m-%d") - datetime.now()).days
                    pt_num = re.search(r"(\d+)", str(proc_time))
                    if pt_num:
                        pt_days = int(pt_num.group(1)) * 7  # weeks → days (conservative)
                        if pt_days > days_left:
                            notes.append(
                                f"The estimated processing time ({proc_time}) may be longer than the time before your "
                                f"target date ({_fmt_date(user_date)}). Starting as early as possible is important, "
                                f"but the provider decides timing and this estimate is not a guarantee."
                            )
                except (ValueError, TypeError):
                    pass
            # A6-03: include deadline in rationale when it drives ordering.
            if dl and dl["status"] == "verified":
                why += f" The official deadline is {_fmt_date(dl['value'])}."
            elif user_date and not dl:
                why += f" Acting before your date of {_fmt_date(user_date)} gives the most time."
            a = add(need_id=need_id, program_id=m["program_id"],
                    order_group=group, rationale=why,
                    dependency_ids=dependency,
                    official_deadline=dl["value"] if dl and dl["status"] == "verified" else None,
                    user_target_date=user_date, estimated_processing_time=proc_time,
                    evidence_refs=refs, uncertainty_notes=notes, _subcategory=sub)
            if sub in ("calfresh_benefits", "unemployment_insurance"):
                app_ids.append(a["action_id"])
    if app_ids:
        add(order_group="later", rationale="This depends on the applications above being submitted first.",
            dependency_ids=app_ids, _subcategory="")
    # an open program for the same need as a closed one goes first
    avail = _availability(p)
    closed_needs = {a["need_id"] for a in actions if a["program_id"] and avail.get(a["program_id"]) == "temporarily_closed"}
    for a in actions:
        if a["need_id"] in closed_needs and a["program_id"] and avail.get(a["program_id"]) != "temporarily_closed" and not a["dependency_ids"]:
            a["order_group"] = "first"
            a["rationale"] += " This is the open option for this need while another program is closed."
    # A6-03 + C-OD2: sort by group, then conditionally housing-first, then deadlines.
    housing_first = _overdue_housing_signal(facts)
    actions.sort(key=lambda a: _sort_key_6(a, housing_first))
    group_counters = {}
    for a in actions:
        g = a["order_group"]
        group_counters[g] = group_counters.get(g, 0) + 1
        a["suggested_priority"] = group_counters[g]
    # A6-01: coverage uses each action's own need_id (one per action).
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
    evidence_records = p.get("evidence_records")
    id_map = {a["action_id"]: f"card_{i:02d}" for i, a in enumerate(acts, 1)}
    # build a set of (program_id, avail) to know which programs are open (for D/A8-03)
    avail_map = _availability(p)

    # A6-01: multiple actions for the same program_id (one per need_id, from agent_6)
    # must be merged into a single card.  Group by (program_id, is_confirm) so that
    # confirm-deadline actions remain separate from the regular application action.
    def _is_confirm(a):
        r = a.get("rationale", "")
        return r.startswith("Official sources disagree") or r.startswith("The published deadline is unknown")

    # Build ordered list of (program_id, is_confirm) keys without duplicates to
    # preserve the sorted order that agent_6 produced.
    seen_groups = {}  # (pid, is_confirm) -> first action index in merged_acts
    merged_acts = []  # list of lists: each inner list is the group to merge
    for a in acts:
        key = (a.get("program_id"), _is_confirm(a))
        if key not in seen_groups:
            seen_groups[key] = len(merged_acts)
            merged_acts.append([a])
        else:
            merged_acts[seen_groups[key]].append(a)

    cards = []
    for group in merged_acts:
        # Representative action: first in the group (already in sorted order).
        a = group[0]
        m = matches.get(a["program_id"])
        is_confirm = _is_confirm(a)
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
                # A8-03: say "open option above" only if another open card exists for this need
                need_id = a.get("need_id")
                has_open = any(
                    x["program_id"] != a["program_id"]
                    and x.get("need_id") == need_id
                    and avail_map.get(x["program_id"]) != "temporarily_closed"
                    for x in acts
                )
                if has_open:
                    next_step = "Use the open option above first. Check back with this program when it reopens."
                else:
                    next_step = "Check back when this program reopens. Contact 2-1-1 for other help while you wait."
        is_closed = a["rationale"].startswith("Temporarily closed")
        claims = p.get("checked_claims", [])
        if m and not is_closed:
            contacts = _build_contacts(claims, a["program_id"], evidence_records)
            snippets = _next_step_contacts(contacts)
            for snippet in snippets:
                # Only append a snippet if the whole snippet fits within the 250-char budget
                candidate = next_step + " " + snippet
                if len(candidate) <= 250:
                    next_step = candidate
            if contacts:
                all_refs = [r for item in contacts for r in item["evidence_refs"]]
                merged_refs = list(dict.fromkeys(
                    [r for x in group for r in x["evidence_refs"]] + all_refs))
                a = dict(a, evidence_refs=merged_refs)
        else:
            contacts = []
        if not m:
            title, reason = "Follow up on your applications", "Checking in helps you catch any requests for more information."
            next_step = "After applying, watch for letters or messages and respond to any requests for documents."
        # A6-01: related_need_ids = all need_ids from the merged group (deduplicated, ordered).
        # B/A8-01: fall back to match's need_ids when action need_id is null; follow-up
        # action uses the dependency need_ids.
        if m:
            # Collect need_id from each action in the group; filter out None.
            group_need_ids = list(dict.fromkeys(
                x["need_id"] for x in group if x.get("need_id") is not None))
            if group_need_ids:
                related = group_need_ids
            else:
                related = m["need_ids"]
        else:
            related = sorted({x["need_id"] for x in acts if x["action_id"] in a["dependency_ids"]})
        # Merge evidence refs across the whole group.
        merged_ev = list(dict.fromkeys(r for x in group for r in x["evidence_refs"]))
        source_action_ids = [x["action_id"] for x in group]
        # card_id is keyed by the first action in the group.
        cards.append({
            "card_id": id_map[a["action_id"]], "source_action_ids": source_action_ids,
            "related_need_ids": related, "program_id": a["program_id"],
            "action_title": title, "reason": reason, "next_step": next_step,
            "priority_reason": a["rationale"],
            "order_group": a["order_group"],
            "dependency_card_ids": [id_map[d] for d in a["dependency_ids"]],
            "source_refs": a.get("evidence_refs", merged_ev),
            "uncertainty_notes": a["uncertainty_notes"],
            "official_deadline": a["official_deadline"], "user_target_date": a["user_target_date"],
            "processing_estimate": a["estimated_processing_time"], "progress_status": "not_started",
            "contacts": contacts,
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
    # A7-02: track whether evidence_records was provided (even if empty).
    ev_records_provided = "evidence_records" in p
    ev_ids = {e["evidence_id"] for e in p.get("evidence_records", [])}
    conflict_groups = {}
    for c in claims:
        pid, fp = c["program_id"], c["field_path"]
        crit = fp.startswith(CRITICAL_FIELDS)
        if known and pid not in known:
            add("Q6", "critical", pid, "Claim references a program that is not in the matches", "recheck_source", fp)
        # A7-02: an empty evidence_records list is never a pass — any evidence_ref must be in the list.
        if c["verification_status"] == "verified" and (
            not c.get("evidence_refs")
            or (ev_records_provided and not set(c["evidence_refs"]) <= ev_ids)
        ):
            add("Q1", "critical" if crit else "warning", pid, "Verified claim has no resolvable evidence", "omit_unsupported_claim", fp)
        if c["verification_status"] == "conflicting":
            conflict_groups.setdefault((pid, fp), []).append(c)
    for (pid, fp), group in conflict_groups.items():
        values = {str(c.get("claim_value")) for c in group if c.get("claim_value") is not None}
        # A7-03: claim_value=None in a conflict group means the value is genuinely unknown/missing;
        # treat the group as a real conflict (Q2), never as "only one value" (Q3).
        has_none_value = any(c.get("claim_value") is None for c in group)
        if not has_none_value and len(values) < 2 and not any(re.search(r"\bvs\b|\d{4}-\d{2}-\d{2}.*\d{4}-\d{2}-\d{2}", str(c.get("claim_value"))) for c in group):
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
    # A7-01: fire Q8 whenever the stage_result has a "matches" key (even when it is empty),
    # because the stage was expected to produce matches.  Do NOT fire when the key is absent
    # (e.g. an external-discovery-only stage that has no matches at all).
    has_matches_key = "matches" in sr
    for n in p.get("needs", []):
        if has_matches_key and n["need_id"] not in covered:
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
    # A10-01: build a per-program evidence text so V8 only fires when a
    # phone/URL is missing from *that program's* own evidence records.
    evidence_records = p.get("evidence_records", [])
    ev_by_program = {}
    for e in evidence_records:
        ev_by_program.setdefault(e.get("program_id"), []).append(
            str(e.get("source_url", "")) + " " + str(e.get("claim_value", "")))
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
        # A10-01: check phone/URL only against this card's program's evidence
        prog_ev_text = " ".join(ev_by_program.get(pid, []))
        for found in URL_OR_PHONE.findall(text):
            if found not in prog_ev_text:
                flag(cid, "V8", f"Contact or link not in evidence: {found}", "Remove it or use the verified contact.")
        if c.get("progress_status") != "not_started":
            flag(cid, "V10", "Progress status was set without user input", "Set progress_status to not_started.")
        if any(re.search(pat, low) for pat in PROHIBITED) and re.search(ASK_NAVIGATOR, low):
            flag(cid, "V13", "Asks for prohibited personal data (proposed rule)", "Remove the request.")

    for opt in plan.get("potential_options", []):
        if not opt.get("official_link") or not opt.get("what_needs_checking"):
            flag(None, "V11", f"Potential option {opt.get('program_id')} lacks an official link or what needs checking", "Add both.")
    # A10-02: each card's related_need_ids must only contain needs that the original match actually covers.
    for c in cards:
        pid = c.get("program_id")
        if pid and pid in matches:
            valid_need_ids = set(matches[pid]["need_ids"])
            for rn in c.get("related_need_ids", []):
                if rn not in valid_need_ids:
                    flag(c["card_id"], "V12",
                         f"Card related_need_ids contains {rn} which is not in the match's need_ids for {pid}",
                         "Set related_need_ids only to the needs the program actually matched.")
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
