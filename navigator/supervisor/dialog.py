"""Dialog mode: start / answer / confirm (Supervisor v0.2.5, Session A).

Three public functions for the App Layer:
  start(story_text, ref_date, locale, agents, kb_path, zips_path, isolate)
  answer(case, answers, agents, kb_path, zips_path, isolate)
  confirm(case, corrections, rejected_need_ids, added_needs, agents, kb_path, zips_path, isolate)

Dialog version: "0.2". No file writes. No reads from the current directory.
Paths are built from __file__ so this module is safe on a read-only file system.
Requires Python 3.11+. Standard library only.
"""
import datetime
import json
import os

from navigator.supervisor import builders as B
from navigator.supervisor import checks
from navigator.supervisor import run as R

# ---------------------------------------------------------------- constants
DIALOG_VERSION = "0.2"

# Protects against an agent defect, not a design limit.
LOOP_GUARD_TURNS = 8

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
_DEFAULT_AGENTS_JSON = os.path.join(_REPO_ROOT, "agents.json")
DEFAULT_EMERGENCY = os.path.join(_HERE, "..", "kb", "emergency", "emergency_directory.json")

# Exception types that dialog functions catch (same as Run.execute)
_CATCH_EXC = R._INPUT_EXC + (R.AgentConfigError, OSError)

# ---------------------------------------------------------------- label tables
FACT_LABELS = {
    # §3.2 fact keys (contracts v1.1)
    "zip_code":                         "ZIP code",
    "county":                           "County",
    "household_size":                   "People in your household",
    "children_ages":                    "Ages of your children",
    "employment_status":                "Work situation",
    "rent_amount_monthly":              "Monthly rent",
    "rent_due_date":                    "Rent due date",
    "cash_on_hand_approx":              "Money available now",
    "has_written_eviction_notice":      "Written eviction notice received",
    "household_gross_monthly_income":   "Monthly household income (before taxes)",
    # CR-012 / CR-013 (proposed v1.2)
    "eviction_notice_type":             "Type of eviction notice",
    "eviction_notice_date":             "Date on the eviction notice",
    "triggering_circumstances":         "What happened",
    # PR #6 (proposed v1.2)
    "has_court_writ_or_judgment":       "Court judgment or writ",
    "specific_move_out_date":           "Move-out date named by the landlord",
    "imminent_removal_in_progress":     "Landlord is trying to remove you now",
    "rent_arrears_amount":              "Rent owed",
}

CATEGORY_LABELS = {
    "food_assistance":          "Food",
    "housing_assistance":       "Housing",
    "income_assistance":        "Income",
    "utility_assistance":       "Utilities",
    "medical_health_coverage":  "Health care",
    "debt_hardship":            "Debt",
    "material_in_kind":         "Clothing, furniture, essentials",
    "crowdfunding_guidance":    "Crowdfunding guidance",
    "other_unlisted":           "Other need",
}

# Money fact fields: displayed as $1,800
_MONEY_FIELDS = {
    "rent_amount_monthly", "cash_on_hand_approx",
    "household_gross_monthly_income", "rent_arrears_amount",
}

# Date fact fields: displayed as "Nov 30, 2026"
_DATE_FIELDS = {
    "rent_due_date", "eviction_notice_date",
    "specific_move_out_date",
}

# Yes/no fact fields: a correction must be true or false
_BOOL_FIELDS = {
    "has_written_eviction_notice", "has_court_writ_or_judgment",
    "imminent_removal_in_progress",
}

# Valid category values (§3.4)
_VALID_CATEGORIES = set(CATEGORY_LABELS)

# ---------------------------------------------------------------- helpers

def _fact_label(field):
    """Return (label, issues). Falls back to capitalised key with FACT_LABEL_MISSING (info)."""
    if field in FACT_LABELS:
        return FACT_LABELS[field], []
    label = field.replace("_", " ").capitalize()
    return label, [{"code": "FACT_LABEL_MISSING", "severity": "info",
                    "message": f"No label defined for fact key {field!r}; using key as label",
                    "related_ref": field}]


def _display_value(field, value):
    """Format a fact value for display. No user data in returned issues."""
    if value is None:
        return None
    if field in _MONEY_FIELDS:
        try:
            return f"${int(value):,}"
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if field in _DATE_FIELDS and isinstance(value, str):
        # Parse ISO date YYYY-MM-DD and format as "Nov 30, 2026"
        # Built without platform-specific strftime codes (no %-d).
        _MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        try:
            d = datetime.date.fromisoformat(value)
            return f"{_MONTHS[d.month - 1]} {d.day}, {d.year}"
        except (ValueError, AttributeError):
            pass
    if isinstance(value, str):
        return value.replace("_", " ")
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _normalise_correction(field, value):
    """Check one correction value by the fact's type. Returns (ok, value).

    Money: a number >= 0, or a string such as "1500" or "1,500" (int, float if it has cents).
    Dates: a string YYYY-MM-DD. Yes/no fields: true or false.
    Other fields: a string or a number (not a list or object).
    """
    if field in _MONEY_FIELDS:
        if isinstance(value, bool):
            return False, value
        if isinstance(value, str):
            text = value.strip().replace(",", "").lstrip("$")
            try:
                value = float(text) if "." in text else int(text)
            except ValueError:
                return False, value
        if not isinstance(value, (int, float)) or value < 0:
            return False, value
        return True, value
    if field in _DATE_FIELDS:
        if not isinstance(value, str):
            return False, value
        try:
            datetime.date.fromisoformat(value.strip())
        except ValueError:
            return False, value
        return True, value.strip()
    if field in _BOOL_FIELDS:
        return isinstance(value, bool), value
    if isinstance(value, bool) or isinstance(value, (str, int, float)):
        return True, value
    return False, value


def _load_defaults(agents, kb_path, zips_path):
    """Return (agents_dict, kb_path, zips_path) with defaults applied.

    agents.json is at the repository root (two levels up from navigator/supervisor/).
    Default kb and zips paths come from run.py and builders.py constants.
    Never reads from the current directory.
    """
    if agents is None:
        agents = R.load_agents(_DEFAULT_AGENTS_JSON)
    if kb_path is None:
        kb_path = R.DEFAULT_KB
    if zips_path is None:
        zips_path = B.DEFAULT_ZIPS
    return agents, kb_path, zips_path


def _make_run(agents, kb_path, zips_path, isolate, ref_date, ids=None):
    """Create a Run with the given parameters."""
    return R.Run(agents, kb_path, ids=ids, isolate=isolate,
                 ref_date=ref_date, zips_path=zips_path)


def _restore_run(case, agents, kb_path, zips_path, isolate):
    """Build a Run and restore CaseState from a case dict.

    Returns the Run with state populated from the case. The request counter
    is restored from next_request_seq so IDs never repeat across calls.
    """
    ref_date = datetime.date.fromisoformat(case["ref_date"])
    ids = (case["case_id"], case["run_id"], case["correlation_id"])
    first_seq = case.get("next_request_seq", 1)
    run = R.Run(agents, kb_path, ids=ids, isolate=isolate,
                ref_date=ref_date, zips_path=zips_path)
    # Rebuild CaseState with the restored counter
    old_state = run.state
    from navigator.supervisor.builders import CaseState
    st = CaseState(old_state.case_id, old_state.run_id, old_state.correlation_id,
                   first_seq=first_seq)
    st.case_version  = case["case_version"]
    st.needs         = list(case.get("needs", []))
    st.case_facts    = list(case.get("case_facts", []))
    st.already_asked = list(case.get("already_asked", []))
    run.state = st
    return run


def _make_case(run, stage, turn, ambiguity_flags, safety_flags,
               narrative_summary, pending_questions, limitations, skipped_keys=None):
    """Serialise CaseState + dialog metadata into the opaque case dict."""
    st = run.state
    return {
        "case_id":          st.case_id,
        "run_id":           st.run_id,
        "correlation_id":   st.correlation_id,
        "case_version":     st.case_version,
        "stage":            stage,
        "turn":             turn,
        "ref_date":         run.ref_date.isoformat(),
        "next_request_seq": st.next_seq,
        "narrative_summary": narrative_summary,
        "needs":            list(st.needs),
        "case_facts":       list(st.case_facts),
        "already_asked":    list(st.already_asked),
        "ambiguity_flags":  ambiguity_flags or [],
        "safety_flags":     safety_flags or [],
        "pending_questions": list(pending_questions or []),
        "limitations":      list(limitations or []),
        "skipped_keys":     list(skipped_keys or []),
    }


def _failed(case, issues, user_message=None, questions=None):
    """Build a failed response. Always returns the last good case.

    A case that is not a dict is never echoed back (case None).
    The safety notice of a valid case stays visible (forms 5).
    questions: the same questions again (SKIP_NOT_ALLOWED), else [].
    """
    if user_message is None:
        user_message = ("Something went wrong on our side. "
                        "Your answers are saved. Please try again.")
    good = case if isinstance(case, dict) else None
    lims = good.get("limitations") if good else None
    flags = good.get("safety_flags") if good else None
    return {
        "dialog_version": DIALOG_VERSION,
        "status":         "failed",
        "case_id":        good.get("case_id") if good else None,
        "case_version":   good.get("case_version") if good else None,
        "turn":           good.get("turn", 0) if good else 0,
        "limitations":    list(lims) if isinstance(lims, list) else [],
        "questions":      list(questions or []),
        "summary":        None,
        "plan":           None,
        "plan_by_need":   None,
        "final_validation": None,
        "rejected_needs": [],
        "safety_notice":  _safety_notice(flags if isinstance(flags, list) else []),
        "user_message":   user_message,
        "issues":         issues,
        "case":           good,
    }


# ---------------------------------------------------------------- DIALOG 6: case check

_CASE_REQUIRED = {
    "case_id": str, "run_id": str, "correlation_id": str,
    "case_version": int, "stage": str, "turn": int, "ref_date": str,
    "next_request_seq": int,
    "needs": list, "case_facts": list, "already_asked": list,
    "ambiguity_flags": list, "safety_flags": list,
    "pending_questions": list, "limitations": list,
    "skipped_keys": list,
}


def _check_case(case, expected_stage):
    """Validate the case dict and stage. Returns issues (empty = ok)."""
    if not isinstance(case, dict):
        return [{"code": "CASE_INVALID", "severity": "critical",
                 "message": "case is not an object", "related_ref": None}]
    for key, typ in _CASE_REQUIRED.items():
        if key not in case:
            return [{"code": "CASE_INVALID", "severity": "critical",
                     "message": f"case is missing required field {key!r}",
                     "related_ref": key}]
        if not isinstance(case[key], typ):
            return [{"code": "CASE_INVALID", "severity": "critical",
                     "message": f"case field {key!r} has wrong type",
                     "related_ref": key}]
    stage = case.get("stage")
    if stage != expected_stage:
        return [{"code": "WRONG_STAGE", "severity": "critical",
                 "message": f"expected stage {expected_stage!r}, got {stage!r}",
                 "related_ref": "stage"}]
    return []


# ---------------------------------------------------------------- DIALOG 5: questions

def _make_questions(clarification_requests, turn, already_asked_set,
                    existing_fact_fields, supervisor_issues_out):
    """Map Agent 2 ClarificationRequests to Question dicts.

    - Drops requests with empty fact_key (QUESTION_DROPPED, related_ref None).
    - Drops a second request for the same fact_key in one turn (QUESTION_DROPPED).
    - Drops any request whose fact_key is already a fact or in already_asked_set
      (Supervisor merge rule, contract §3.3) with QUESTION_DROPPED (info).
    - Keeps at most 2 per turn (Agent 2's cluster rule).
    Returns list of Question dicts (at most 2).
    """
    questions = []
    seen_keys = set()
    for cr in (clarification_requests or []):
        fk = cr.get("fact_key", "")
        if not fk:
            supervisor_issues_out.append({
                "code": "QUESTION_DROPPED", "severity": "info",
                "message": "ClarificationRequest has empty fact_key; dropped",
                "related_ref": None})
            continue
        if fk in seen_keys:
            supervisor_issues_out.append({
                "code": "QUESTION_DROPPED", "severity": "info",
                "message": f"Duplicate fact_key {fk!r} in this turn; dropped",
                "related_ref": fk})
            continue
        seen_keys.add(fk)
        if fk in already_asked_set or fk in existing_fact_fields:
            supervisor_issues_out.append({
                "code": "QUESTION_DROPPED", "severity": "info",
                "message": f"Question for {fk!r} dropped: already answered or in case facts",
                "related_ref": fk})
            continue
        questions.append({
            "question_id":      f"q{turn}-{len(questions) + 1}",
            "fact_key":         fk,
            "text":             cr.get("user_facing_question", ""),
            "can_skip":         cr.get("can_skip", True),
            "necessity_level":  cr.get("necessity_level", "helpful"),
            "reason":           cr.get("reason", ""),
        })
        if len(questions) == 2:
            break
    return questions


def _geography_question(turn):
    """The Supervisor's own ZIP question when Agent 2 returns nothing."""
    return {
        "question_id":     f"q{turn}-1",
        "fact_key":        "zip_code",
        "text":            "What is your ZIP code? It helps us find programs near you.",
        "can_skip":        True,
        "necessity_level": "required_for_decision",
        "reason":          "Programs depend on where you live.",
    }


_GEO_LIMITATION = ("We could not look for local programs without your ZIP code, "
                   "so some options may be missing. "
                   "You can add your ZIP code at any time.")


# ---------------------------------------------------------------- DIALOG 5: Agent 2 call

def _run_agent2(run, ambiguity_flags):
    """Soft Agent 2 call. Applies need_updates. Returns (clarification_requests, issues)."""
    r2 = run.call(B.agent2_request(run.state, ambiguity_flags=ambiguity_flags or None))
    if r2 is None:
        return [], [{"code": "AGENT_FAILED", "severity": "warning",
                     "message": "Agent 2 did not return a valid result; continuing without clarification",
                     "related_ref": None}]
    run.supervisor_issues += B.apply_need_updates(run.state, r2)
    return r2.get("clarification_requests") or [], []


# ---------------------------------------------------------------- summary builder

def _summary(run, narrative_summary, unknown_fields):
    """Build the needs_confirmation summary dict."""
    issues = []
    needs_out = []
    for n in run.state.needs:
        cat = n.get("category", "")
        needs_out.append({
            "need_id":        n.get("need_id"),
            "category":       cat,
            "label":          CATEGORY_LABELS.get(cat, cat),
            "description":    n.get("description"),
            "urgency":        n.get("urgency"),
            "urgency_reason": n.get("urgency_reason"),
            "original_quote": n.get("original_quote"),
        })

    facts_out = []
    for f in run.state.case_facts:
        field = f.get("field", "")
        value = f.get("value")
        label, lbl_issues = _fact_label(field)
        issues += lbl_issues
        facts_out.append({
            "field":         field,
            "label":         label,
            "value":         value,
            "display_value": _display_value(field, value),
        })

    unknown_out = []
    for uf in unknown_fields:
        field = uf["field"]
        label, lbl_issues = _fact_label(field)
        issues += lbl_issues
        unknown_out.append({
            "field": field,
            "label": label,
            "why":   uf.get("why", "not_answered"),
        })

    run.supervisor_issues += issues
    return {
        "narrative": narrative_summary or "",
        "needs":     needs_out,
        "facts":     facts_out,
        "unknown":   unknown_out,
    }


# ---------------------------------------------------------------- plan_by_need builder

def _plan_by_need(plan, needs):
    """Build plan_by_need rows ordered by the plan's action order.

    Row order: position of each need's first released card in plan.action_cards;
    needs with no card come last (in summary order).
    Urgency is a label only, never used for sorting.
    Coverage gaps use g["need_id"] and g["note"] (contract §4.8 Agent 8 shape).
    A need with no released card and no coverage gap gets a user-facing message in
    gap_notes and a NEED_NOT_IN_PLAN warning (developer issue).
    """
    issues = []
    cards = plan.get("action_cards", [])
    gaps  = plan.get("coverage_gaps", [])

    # Build need_id -> gap notes (contract §4.8: gap has need_id and note)
    gap_notes_by_need = {}
    for g in gaps:
        nid = g.get("need_id")
        if nid:
            gap_notes_by_need.setdefault(nid, []).append(g.get("note", ""))

    # Order: index of first released card per need
    _ORDER_GROUP = {"first": 0, "parallel": 1, "later": 2}
    first_card_pos = {}
    for pos, card in enumerate(cards):
        for nid in (card.get("related_need_ids") or []):
            if nid not in first_card_pos:
                first_card_pos[nid] = pos

    rows = []
    for need in needs:
        nid = need.get("need_id")
        cat = need.get("category", "")
        # Cards for this need, ordered first → parallel → later, then by card order
        need_cards = [c for c in cards if nid in (c.get("related_need_ids") or [])]
        need_cards.sort(key=lambda c: (_ORDER_GROUP.get(c.get("order_group", "later"), 2),
                                       cards.index(c)))
        card_ids  = [c["card_id"] for c in need_cards]
        need_gaps = gap_notes_by_need.get(nid, [])

        if not card_ids and not need_gaps:
            need_gaps = ["We have not found a verified program for this need yet."]
            issues.append({"code": "NEED_NOT_IN_PLAN", "severity": "warning",
                           "message": f"Need {nid!r} ({cat}) has no released card and no coverage gap",
                           "related_ref": nid})

        rows.append({
            "need_id":        nid,
            "category":       cat,
            "label":          CATEGORY_LABELS.get(cat, cat),
            "urgency":        need.get("urgency"),
            "urgency_reason": need.get("urgency_reason"),
            "card_ids":       card_ids,
            "gap_notes":      need_gaps,
        })

    # Sort rows by plan action order (needs with no card come last)
    rows.sort(key=lambda r: first_card_pos.get(r["need_id"], len(cards)))
    return rows, issues


# ---------------------------------------------------------------- need edits at confirm

def _next_need_id(needs):
    """Return the next free need_xxx id not in the current needs list."""
    existing = {n.get("need_id", "") for n in needs}
    i = 1
    while True:
        nid = f"need_{i:03d}"
        if nid not in existing:
            return nid
        i += 1


def _new_need(nid, item, masked_description):
    """Build a Need dict for an added_needs item (all contract §3.1 fields)."""
    return {
        "need_id":             nid,
        "category":            item["category"],
        "subcategory":         None,
        "description":         masked_description[:200],
        "original_quote":      masked_description[:200],
        "confirmation_status": "confirmed",
        "user_reported":       True,
        "urgency":             "normal",
        "urgency_reason":      "Added by the user on the summary.",
        "user_priority":       None,
    }


def _apply_need_edits(state, rejected_need_ids, added_needs, supervisor_issues_out):
    """Apply rejected_need_ids and added_needs to state.

    Returns (error_issues, ok) where ok=False means validation failed.
    """
    rejected_need_ids = rejected_need_ids or []
    added_needs = added_needs or []

    # Validate rejected_need_ids
    known_ids = {n["need_id"] for n in state.needs}
    for nid in rejected_need_ids:
        if nid not in known_ids:
            return [{"code": "UNKNOWN_NEED_ID", "severity": "critical",
                     "message": "Rejected need id is not in this case",
                     "related_ref": nid}], False

    # Validate added_needs categories
    existing_cats = {n["category"] for n in state.needs}
    for item in added_needs:
        cat = item.get("category", "")
        if cat not in _VALID_CATEGORIES:
            return [{"code": "UNKNOWN_ENUM", "severity": "critical",
                     "message": "Category is not one of the 9 known categories",
                     "related_ref": cat}], False
        if cat in existing_cats:
            return [{"code": "NEED_ALREADY_PRESENT", "severity": "critical",
                     "message": "A need with that category already exists",
                     "related_ref": cat}], False
        existing_cats.add(cat)   # prevent duplicates within added_needs itself

    # Apply rejections: mark as disputed
    for nid in rejected_need_ids:
        for n in state.needs:
            if n["need_id"] == nid:
                n["confirmation_status"] = "disputed"

    # Apply additions
    for item in added_needs:
        raw_desc = item.get("description", "")
        masked_desc, mask_issues = checks.mask_user_text(raw_desc)
        supervisor_issues_out += mask_issues
        nid = _next_need_id(state.needs)
        state.needs.append(_new_need(nid, item, masked_desc))

    return [], True


# ---------------------------------------------------------------- shared Agent 2 → questions logic

def _agent2_and_questions(run, ambiguity_flags, turn):
    """Run Agent 2 and return the question list for the next response.

    Applies need_updates, filters already-answered/known keys,
    and applies the geography guard if Agent 2 returns nothing.
    """
    # A flag whose field is already a fact, or was already asked (answered or skipped), is settled:
    # forwarding it makes Agent 2 keep its "find the cause" branch and not ask income.
    settled = ({f.get("field") for f in run.state.case_facts} | set(run.state.already_asked))
    active_flags = [f for f in (ambiguity_flags or [])
                    if not (isinstance(f, dict) and f.get("field") in settled)]
    clarification_requests, a2_issues = _run_agent2(run, active_flags)
    run.supervisor_issues += a2_issues

    existing_fact_fields = {f.get("field") for f in run.state.case_facts}
    already_set = set(run.state.already_asked)

    questions = _make_questions(
        clarification_requests, turn,
        already_set, existing_fact_fields,
        run.supervisor_issues)

    # Geography guard: if Agent 2 asks nothing and ZIP is unknown and not yet asked → ask once
    if not questions:
        zip_known = any(f.get("field") == "zip_code" for f in run.state.case_facts)
        zip_asked = "zip_code" in already_set
        if not zip_known and not zip_asked:
            questions = [_geography_question(turn)]

    return questions


# ---------------------------------------------------------------- safety contacts (DIALOG 8)

_EMERGENCY_CONTACTS_CACHE: dict = {}   # path -> (contacts, issues)

_SAFETY_SUBCATEGORIES = ("emergency_services", "mental_health_crisis")
_SUBCATEGORY_ORDER = {s: i for i, s in enumerate(_SAFETY_SUBCATEGORIES)}

SAFETY_CONTACT_UNVERIFIED = "SAFETY_CONTACT_UNVERIFIED"


def _emergency_contacts(path=None):
    """Load verified safety contacts from the emergency directory.

    Returns (contacts, issues).  Loads once per process (cached by path).
    contacts: list of {name, value, hours, checked_at} for verified contact items
              from emergency_services and mental_health_crisis records only,
              9-1-1 first, then 988.
    issues: [] on success; [SAFETY_CONTACT_UNVERIFIED warning] on any failure.
    Never raises.
    """
    if path is None:
        path = DEFAULT_EMERGENCY
    path = os.path.normpath(path)
    if path in _EMERGENCY_CONTACTS_CACHE:
        return _EMERGENCY_CONTACTS_CACHE[path]

    _unverified_issue = {
        "code":        SAFETY_CONTACT_UNVERIFIED,
        "severity":    "warning",
        "message":     "Emergency contacts could not be loaded from the emergency directory",
        "related_ref": None,
    }

    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except Exception:
        result = ([], [_unverified_issue])
        _EMERGENCY_CONTACTS_CACHE[path] = result
        return result

    try:
        programs = data.get("program_records", [])
        evidence = {e["evidence_id"]: e for e in data.get("evidence_records", [])}

        # Select only the two allowed subcategories
        selected = [p for p in programs
                    if p.get("subcategory") in _SAFETY_SUBCATEGORIES]
        # Sort: emergency_services (9-1-1) first, then mental_health_crisis (988)
        selected.sort(key=lambda p: _SUBCATEGORY_ORDER.get(p.get("subcategory", ""), 99))

        contacts = []
        for prog in selected:
            name = prog.get("program_name", "")
            for item in prog.get("contact", []):
                # Accept item only if every evidence_ref points to a verified evidence row
                # with a field_path that starts with "contact"
                refs = item.get("evidence_refs") or []
                if not refs:
                    continue
                verified = all(
                    evidence.get(ref, {}).get("verification_status") == "verified"
                    and evidence.get(ref, {}).get("field_path", "").startswith("contact")
                    for ref in refs
                )
                if not verified:
                    continue
                # checked_at: take the date part from the first evidence ref
                ev0 = evidence.get(refs[0], {})
                checked_at_full = ev0.get("checked_at", "")
                checked_at = checked_at_full[:10] if checked_at_full else None
                contacts.append({
                    "name":       name,
                    "value":      item.get("value"),
                    "hours":      None,
                    "checked_at": checked_at,
                })

        if not contacts:
            result = ([], [_unverified_issue])
            _EMERGENCY_CONTACTS_CACHE[path] = result
            return result

        result = (contacts, [])
        _EMERGENCY_CONTACTS_CACHE[path] = result
        return result

    except Exception:
        result = ([], [_unverified_issue])
        _EMERGENCY_CONTACTS_CACHE[path] = result
        return result


# ---------------------------------------------------------------- safety notice

def _safety_notice(safety_flags, _emergency_path=None):
    """Build a SafetyNotice dict or None. A safety risk shows a warning, never blocks the plan.

    Shape follows forms §5: {risk_type, message, contacts, blocks_plan}.
    The user's flag text is never copied into the notice.
    contacts comes from the verified emergency directory (DIALOG 8).
    """
    if not any(isinstance(f, dict) and f.get("type") == "safety"
               for f in (safety_flags or [])):
        return None
    contacts, _issues = _emergency_contacts(_emergency_path)
    return {
        "risk_type":   "safety",
        "message":     ("If you or someone with you is in danger right now, call 9-1-1. "
                        "You can keep going with your plan below."),
        "contacts":    contacts,
        "blocks_plan": False,
    }


def _merge_safety_flags(existing, new_flags):
    """Add new safety flags without duplicates (deduplicated by quote+type)."""
    seen = {(f.get("quote", ""), f.get("type", "")) for f in existing}
    result = list(existing)
    for f in (new_flags or []):
        key = (f.get("quote", ""), f.get("type", ""))
        if key not in seen:
            result.append(f)
            seen.add(key)
    return result


# ---------------------------------------------------------------- unknown facts helpers

def _unknown_facts_with_skipped(state, skipped_keys_set):
    """Build unknown list: facts that were asked but not settled.

    skipped_keys_set: set of fact keys the user explicitly skipped (from case["skipped_keys"]).
    Keys in already_asked but not in case_facts are listed; why = "skipped" if in
    skipped_keys_set, else "not_answered".
    """
    fact_fields = {f.get("field") for f in state.case_facts}
    result = []
    seen = set()
    for fk in state.already_asked:
        if fk not in fact_fields and fk not in seen:
            seen.add(fk)
            why = "skipped" if fk in skipped_keys_set else "not_answered"
            result.append({"field": fk, "why": why})
    return result


def _add_to_already_asked(state, fact_key):
    """Append fact_key to already_asked only if not already present (fix 12)."""
    if fact_key not in state.already_asked:
        state.already_asked.append(fact_key)


# ---------------------------------------------------------------- public: start

def start(story_text, ref_date=None, locale="en-US",
          agents=None, kb_path=None, zips_path=None, isolate=False):
    """Start a new dialog: Agent 1 understand_story → Agent 2 → first questions or confirmation.

    Returns a dialog response dict (needs_clarification, needs_confirmation, or failed).
    Never raises.
    """
    run = None
    try:
        agents, kb_path, zips_path = _load_defaults(agents, kb_path, zips_path)
        if ref_date is None:
            ref_date = R._today()
        elif isinstance(ref_date, str):
            ref_date = datetime.date.fromisoformat(ref_date)

        run = _make_run(agents, kb_path, zips_path, isolate, ref_date)
        st = run.state

        # Agent 1: understand_story
        run._stage = "agent_1"
        q1, s0_issues = B.agent1_request(st, story_text, locale=locale, ref_date=ref_date)
        run.supervisor_issues += s0_issues
        r1 = run.call(q1)
        if r1 is None:
            return _failed(None, run.supervisor_issues + [
                {"code": "AGENT_FAILED", "severity": "critical",
                 "message": "Agent 1 did not return a valid result",
                 "related_ref": None}])

        res1 = r1["result"]
        # Store proposed needs and facts (all proposed until confirm)
        st.needs = [dict(n, confirmation_status="proposed")
                    for n in res1.get("proposed_needs", [])]
        for f in res1.get("factual_claims", []):
            st.case_facts.append(dict(f, confirmation_status="proposed"))

        ambiguity_flags   = res1.get("ambiguity_flags") or []
        safety_flags      = res1.get("safety_or_official_deadline_flags") or []
        narrative_summary = res1.get("narrative_summary", "")

        # Agent 2 → questions
        turn = 1
        limitations: list = []
        questions = _agent2_and_questions(run, ambiguity_flags, turn)

        # Store full Question objects in pending_questions so SKIP_NOT_ALLOWED can return them
        case = _make_case(run, "clarifying" if questions else "awaiting_confirmation",
                          turn if questions else 0,
                          ambiguity_flags, safety_flags, narrative_summary,
                          questions,   # full Question dicts
                          limitations, skipped_keys=[])

        safety_notice = _safety_notice(safety_flags)
        if safety_notice is not None:
            run.supervisor_issues += _emergency_contacts()[1]

        if questions:
            return _clarification_response(run, questions, case, turn, limitations, safety_notice)
        else:
            unknown = _unknown_facts_with_skipped(st, set())
            summ = _summary(run, narrative_summary, unknown)
            return _confirmation_response(run, case, 0, limitations, safety_notice, summ)

    except _CATCH_EXC as exc:
        issues = (run.supervisor_issues if run is not None else []) + [
            {"code": "SUPERVISOR_INPUT_ERROR", "severity": "critical",
             "message": f"start: {type(exc).__name__}", "related_ref": None}]
        return _failed(None, issues)


# ---------------------------------------------------------------- public: answer

def answer(case, answers, agents=None, kb_path=None, zips_path=None, isolate=False):
    """Process one turn of answers.

    answers: list of {question_id, answer_text} or {question_id, skipped: true}.
    Returns needs_clarification, needs_confirmation, or failed. Never raises.
    """
    try:
        err = _check_case(case, "clarifying")
        if err:
            return _failed(case, err)

        agents, kb_path, zips_path = _load_defaults(agents, kb_path, zips_path)
        run = _restore_run(case, agents, kb_path, zips_path, isolate)
        st = run.state

        ambiguity_flags   = case.get("ambiguity_flags", [])
        safety_flags      = list(case.get("safety_flags", []))
        narrative_summary = case.get("narrative_summary", "")
        limitations       = list(case.get("limitations", []))
        pending_questions = case.get("pending_questions", [])  # full Question dicts
        old_turn          = case.get("turn", 1)
        skipped_keys      = list(case.get("skipped_keys", []))

        # Build a map question_id -> pending_question (full dict)
        pq_by_id = {pq["question_id"]: pq for pq in pending_questions}
        answers_by_id = {ans.get("question_id"): ans for ans in (answers or [])}

        # Validate: every answer must refer to a known question_id
        for ans in (answers or []):
            qid = ans.get("question_id")
            if qid not in pq_by_id:
                return _failed(case, [{"code": "UNKNOWN_QUESTION_ID", "severity": "critical",
                                        "message": "Unknown question_id in answers",
                                        "related_ref": qid}])

        # Validate: can_skip=false questions must not be skipped
        for qid, pq in pq_by_id.items():
            ans = answers_by_id.get(qid, {})
            if ans.get("skipped") and not pq.get("can_skip", True):
                # Return same questions (full text) and failed status, case unchanged
                return _failed(case, [{"code": "SKIP_NOT_ALLOWED", "severity": "critical",
                                        "message": "A required question cannot be skipped",
                                        "related_ref": qid}],
                               questions=pending_questions)

        # Process each question
        for qid, pq in pq_by_id.items():
            fact_key = pq["fact_key"]
            ans = answers_by_id.get(qid, {})
            if ans.get("skipped"):
                # Skipped: record but no issue (QUESTION_DROPPED is for agent questions only)
                _add_to_already_asked(st, fact_key)
                if fact_key not in skipped_keys:
                    skipped_keys.append(fact_key)
            else:
                answer_text = ans.get("answer_text", "")
                if isinstance(answer_text, (int, float)) and not isinstance(answer_text, bool):
                    answer_text = str(answer_text)   # the app may send income 0 as a number
                if not isinstance(answer_text, str) or not answer_text.strip():
                    # Unanswered: record as not_answered, do not call Agent 1
                    _add_to_already_asked(st, fact_key)
                    continue
                req, s0_issues = B.agent1_answer_request(
                    st, answer_text, [fact_key], run.ref_date)
                run.supervisor_issues += s0_issues
                r1a = run.call(req)
                if r1a is None:
                    # Agent 1 failed: return failed with the ORIGINAL case, nothing changed
                    return _failed(case, run.supervisor_issues + [
                        {"code": "AGENT_FAILED", "severity": "critical",
                         "message": "Agent 1 did not return a valid result for the answer",
                         "related_ref": fact_key}])
                run.supervisor_issues += B.merge_answer_facts(st, r1a, [fact_key])
                run.supervisor_issues += B.merge_answer_needs(st, r1a)
                # Merge any safety flags from parse_clarification_answer
                new_safety = r1a.get("result", {}).get(
                    "safety_or_official_deadline_flags") or []
                safety_flags = _merge_safety_flags(safety_flags, new_safety)
                _add_to_already_asked(st, fact_key)

        # ZIP skipped → add geography limitation
        zip_known = any(f.get("field") == "zip_code" for f in st.case_facts)
        if not zip_known and "zip_code" in st.already_asked:
            if _GEO_LIMITATION not in limitations:
                limitations.append(_GEO_LIMITATION)

        # Bump case_version
        st.case_version += 1
        new_turn = old_turn + 1

        # Loop guard
        answered_turns = new_turn - 1
        if answered_turns >= LOOP_GUARD_TURNS:
            run.supervisor_issues.append({
                "code": "QUESTION_LOOP_GUARD", "severity": "warning",
                "message": f"Reached {LOOP_GUARD_TURNS} answered turns; going to summary",
                "related_ref": None})
            unknown = _unknown_facts_with_skipped(st, set(skipped_keys))
            summ = _summary(run, narrative_summary, unknown)
            case_out = _make_case(run, "awaiting_confirmation", answered_turns,
                                  ambiguity_flags, safety_flags, narrative_summary,
                                  [], limitations, skipped_keys=skipped_keys)
            _loop_notice = _safety_notice(safety_flags)
            if _loop_notice is not None:
                run.supervisor_issues += _emergency_contacts()[1]
            return _confirmation_response(run, case_out, answered_turns, limitations,
                                          _loop_notice, summ)

        # Agent 2 → next questions
        questions = _agent2_and_questions(run, ambiguity_flags, new_turn)

        safety_notice = _safety_notice(safety_flags)
        if safety_notice is not None:
            run.supervisor_issues += _emergency_contacts()[1]

        if questions:
            case_out = _make_case(run, "clarifying", new_turn,
                                  ambiguity_flags, safety_flags, narrative_summary,
                                  questions,   # full Question dicts
                                  limitations, skipped_keys=skipped_keys)
            return _clarification_response(run, questions, case_out, new_turn,
                                           limitations, safety_notice)
        else:
            unknown = _unknown_facts_with_skipped(st, set(skipped_keys))
            summ = _summary(run, narrative_summary, unknown)
            case_out = _make_case(run, "awaiting_confirmation", new_turn - 1,
                                  ambiguity_flags, safety_flags, narrative_summary,
                                  [], limitations, skipped_keys=skipped_keys)
            return _confirmation_response(run, case_out, new_turn - 1,
                                          limitations, safety_notice, summ)

    except _CATCH_EXC as exc:
        issues = [{"code": "SUPERVISOR_INPUT_ERROR", "severity": "critical",
                   "message": f"answer: {type(exc).__name__}", "related_ref": None}]
        return _failed(case, issues)


# ---------------------------------------------------------------- public: confirm

def confirm(case, corrections=None, rejected_need_ids=None, added_needs=None,
            agents=None, kb_path=None, zips_path=None, isolate=False):
    """Confirm the summary and run the planning cycle.

    corrections: {field: value} for facts to change.
    rejected_need_ids: list of need_ids to mark disputed (not planned).
    added_needs: [{category, description}] of new needs to add.
    Returns completed or failed. Never raises.
    """
    try:
        err = _check_case(case, "awaiting_confirmation")
        if err:
            return _failed(case, err)

        agents, kb_path, zips_path = _load_defaults(agents, kb_path, zips_path)
        run = _restore_run(case, agents, kb_path, zips_path, isolate)
        st = run.state

        ambiguity_flags   = case.get("ambiguity_flags", [])
        safety_flags      = case.get("safety_flags", [])
        narrative_summary = case.get("narrative_summary", "")
        limitations       = list(case.get("limitations", []))
        skipped_keys      = set(case.get("skipped_keys", []))

        # Apply corrections
        corrections = corrections or {}
        known_fields = ({f["field"] for f in st.case_facts}
                        | {uf["field"] for uf in _unknown_facts_with_skipped(st, skipped_keys)})
        if not isinstance(corrections, dict):
            return _failed(case, [{"code": "FACT_VALUE_INVALID", "severity": "critical",
                                    "message": "corrections must be an object",
                                    "related_ref": None}])
        normalised = {}
        for field, value in corrections.items():
            if field not in known_fields:
                return _failed(case, [{"code": "UNKNOWN_FACT_KEY", "severity": "critical",
                                        "message": "Correction references an unknown fact field",
                                        "related_ref": field}])
            ok, value = _normalise_correction(field, value)
            if not ok:
                return _failed(case, [{"code": "FACT_VALUE_INVALID", "severity": "critical",
                                        "message": "Correction value has the wrong type or format",
                                        "related_ref": field}])
            normalised[field] = value
        corrections = normalised

        # Apply need edits (rejected / added)
        edit_issues, ok = _apply_need_edits(st, rejected_need_ids, added_needs,
                                             run.supervisor_issues)
        if not ok:
            return _failed(case, edit_issues)

        # Check that at least one non-disputed need remains
        confirmed_needs = [n for n in st.needs if n.get("confirmation_status") != "disputed"]
        if not confirmed_needs:
            return _failed(case, [{"code": "NO_NEEDS_LEFT", "severity": "critical",
                                    "message": "All needs were rejected; nothing to plan",
                                    "related_ref": None}])

        # Confirm facts (apply corrections): confirmation_status "confirmed", source "user_confirmed"
        for f in st.case_facts:
            f["confirmation_status"] = "confirmed"
            f["source"] = "user_confirmed"
            if f["field"] in corrections:
                f["value"] = corrections[f["field"]]

        # Also add any corrected fact that was in unknown (not yet in case_facts)
        for field, value in corrections.items():
            if not any(f["field"] == field for f in st.case_facts):
                st.case_facts.append({
                    "fact_id": f"cf-{field}",
                    "field": field,
                    "value": value,
                    "confirmation_status": "confirmed",
                    "source": "user_confirmed",
                    "time_context": None,
                })

        # Confirm non-disputed needs
        for n in st.needs:
            if n.get("confirmation_status") != "disputed":
                n["confirmation_status"] = "confirmed"

        # Geography missing warning (if ZIP was never provided)
        zip_known = any(f.get("field") == "zip_code" for f in st.case_facts)
        if not zip_known and "zip_code" in st.already_asked:
            run.supervisor_issues.append({
                "code": "GEOGRAPHY_MISSING", "severity": "warning",
                "message": "No ZIP code was provided; local program search may be incomplete",
                "related_ref": "zip_code"})

        st.case_version += 1

        # Planning: only confirmed needs reach Agents 3-10
        all_needs = st.needs
        st.needs = confirmed_needs
        run._stage = "agent_3"
        try:
            plan_report = run._plan_body()
        finally:
            st.needs = all_needs   # restore so the case reflects the full picture

        plan     = plan_report.get("plan")
        final_validation = plan_report.get("final_validation")
        outcome  = plan_report.get("outcome", "completed")

        # Collect rejected needs for the response
        rejected = [{"need_id": n["need_id"],
                     "category": n["category"],
                     "label": CATEGORY_LABELS.get(n["category"], n["category"])}
                    for n in st.needs if n.get("confirmation_status") == "disputed"]

        # Case for the completed response (stage "completed")
        case_out = _make_case(run, "completed", case.get("turn", 0),
                              ambiguity_flags, safety_flags, narrative_summary,
                              [], limitations, skipped_keys=list(skipped_keys))

        if outcome != "completed" or plan is None:
            # Return failed with the ORIGINAL case (stage awaiting_confirmation) so the app can retry
            stopped_at = str(plan_report.get("outcome") or "unknown").replace("stopped_at_", "")
            step_issues = [i for s in run.steps if not s.get("accepted")
                           for i in s.get("issues", [])]
            return _failed(case, run.supervisor_issues + step_issues + [
                {"code": "AGENT_FAILED", "severity": "critical",
                 "message": f"Planning stopped at {stopped_at}",
                 "related_ref": None}],
                "Planning could not be completed. Your answers are saved. Please try again.")

        # Build plan_by_need (confirmed needs only), only for a completed plan
        pbn, pbn_issues = _plan_by_need(plan, confirmed_needs)
        run.supervisor_issues += pbn_issues

        return {
            "dialog_version":   DIALOG_VERSION,
            "status":           "completed",
            "case_id":          st.case_id,
            "case_version":     st.case_version,
            "turn":             case.get("turn", 0),
            "limitations":      limitations,
            "questions":        [],
            "summary":          None,
            "plan":             plan,
            "plan_by_need":     pbn,
            "final_validation": final_validation,
            "rejected_needs":   rejected,
            "safety_notice":    _safety_notice(safety_flags),
            "user_message":     None,
            "issues":           run.supervisor_issues + (
                                    _emergency_contacts()[1]
                                    if any(isinstance(f, dict) and f.get("type") == "safety"
                                           for f in (safety_flags or []))
                                    else []),
            "case":             case_out,
        }

    except _CATCH_EXC as exc:
        issues = [{"code": "SUPERVISOR_INPUT_ERROR", "severity": "critical",
                   "message": f"confirm: {type(exc).__name__}", "related_ref": None}]
        return _failed(case, issues)


# ---------------------------------------------------------------- response builders

def _clarification_response(run, questions, case, turn, limitations,
                             safety_notice, extra_issues=None):
    return {
        "dialog_version": DIALOG_VERSION,
        "status":         "needs_clarification",
        "case_id":        run.state.case_id,
        "case_version":   run.state.case_version,
        "turn":           turn,
        "limitations":    list(limitations),
        "questions":      questions,
        "summary":        None,
        "plan":           None,
        "plan_by_need":   None,
        "final_validation": None,
        "rejected_needs": [],
        "safety_notice":  safety_notice,
        "user_message":   None,
        "issues":         run.supervisor_issues + (extra_issues or []),
        "case":           case,
    }


def _confirmation_response(run, case, turn, limitations, safety_notice, summary):
    return {
        "dialog_version": DIALOG_VERSION,
        "status":         "needs_confirmation",
        "case_id":        run.state.case_id,
        "case_version":   run.state.case_version,
        "turn":           turn,
        "limitations":    list(limitations),
        "questions":      [],
        "summary":        summary,
        "plan":           None,
        "plan_by_need":   None,
        "final_validation": None,
        "rejected_needs": [],
        "safety_notice":  safety_notice,
        "user_message":   None,
        "issues":         run.supervisor_issues,
        "case":           case,
    }


# ---------------------------------------------------------------- command-line interface

def main(argv=None):
    """Entry point: python -m navigator.supervisor.dialog start|answer|confirm ...

    start  --story-file F [--ref-date YYYY-MM-DD] --out R.json
    answer --case-in PREV.json --answers-file A.json --out R.json
    confirm --case-in PREV.json [--corrections-file C.json]
            [--rejected need_002 ...] [--added-file N.json] --out R.json

    All three accept: [--agents agents.json] [--kb PATH] [--zips PATH] [--no-isolate]
    Exit 0 on success, 1 when status is "failed", 2 for argument/input errors.
    """
    import argparse
    import sys

    def _err(msg):
        print(msg)
        return 2

    ap = argparse.ArgumentParser(prog="python -m navigator.supervisor.dialog",
                                 description="Dialog mode command-line interface")
    ap.add_argument("command", choices=["start", "answer", "confirm"])
    # shared optional args
    ap.add_argument("--agents",    default=None, metavar="PATH",
                    help="agents.json (default: agents.json at repo root)")
    ap.add_argument("--kb",        default=None, metavar="PATH")
    ap.add_argument("--zips",      default=None, metavar="PATH")
    ap.add_argument("--no-isolate", action="store_true")
    ap.add_argument("--out",       required=True, metavar="PATH",
                    help="output JSON file")
    # start
    ap.add_argument("--story-file", metavar="PATH")
    ap.add_argument("--ref-date",   metavar="YYYY-MM-DD")
    # answer / confirm
    ap.add_argument("--case-in",    metavar="PATH")
    # answer
    ap.add_argument("--answers-file", metavar="PATH")
    # confirm
    ap.add_argument("--corrections-file", metavar="PATH")
    ap.add_argument("--rejected",   nargs="*", metavar="NEED_ID", default=None)
    ap.add_argument("--added-file", metavar="PATH")

    a = ap.parse_args(argv)
    isolate = not a.no_isolate

    # Load agents (optional — defaults handled inside start/answer/confirm)
    agents = None
    if a.agents:
        try:
            agents = R.load_agents(a.agents)
        except R.AgentConfigError as exc:
            return _err(f"Cannot load agents: {exc}")

    # Shared kwargs
    kw = dict(agents=agents, kb_path=a.kb, zips_path=a.zips, isolate=isolate)

    # ---- start ----
    if a.command == "start":
        if not a.story_file:
            return _err("--story-file is required for start")
        try:
            with open(a.story_file, encoding="utf-8-sig") as f:
                story_text = f.read()
        except OSError as exc:
            return _err(f"Cannot read story file: {exc}")
        ref_date = None
        if a.ref_date:
            try:
                ref_date = datetime.date.fromisoformat(a.ref_date)
            except ValueError:
                return _err(f"--ref-date {a.ref_date!r} is not a valid ISO date (YYYY-MM-DD)")
        resp = start(story_text, ref_date=ref_date, **kw)

    # ---- answer ----
    elif a.command == "answer":
        if not a.case_in:
            return _err("--case-in is required for answer")
        if not a.answers_file:
            return _err("--answers-file is required for answer")
        try:
            with open(a.case_in, encoding="utf-8-sig") as f:
                prev = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            return _err(f"Cannot read case-in file: {exc}")
        try:
            with open(a.answers_file, encoding="utf-8-sig") as f:
                answers = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            return _err(f"Cannot read answers file: {exc}")
        if not isinstance(prev, dict):
            return _err("case-in file must hold a JSON object (a previous response)")
        case = prev.get("case")
        resp = answer(case, answers, **kw)

    # ---- confirm ----
    else:  # confirm
        if not a.case_in:
            return _err("--case-in is required for confirm")
        try:
            with open(a.case_in, encoding="utf-8-sig") as f:
                prev = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            return _err(f"Cannot read case-in file: {exc}")
        if not isinstance(prev, dict):
            return _err("case-in file must hold a JSON object (a previous response)")
        case = prev.get("case")
        corrections = None
        if a.corrections_file:
            try:
                with open(a.corrections_file, encoding="utf-8-sig") as f:
                    corrections = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                return _err(f"Cannot read corrections file: {exc}")
        added_needs = None
        if a.added_file:
            try:
                with open(a.added_file, encoding="utf-8-sig") as f:
                    added_needs = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                return _err(f"Cannot read added-needs file: {exc}")
        resp = confirm(case, corrections=corrections,
                       rejected_need_ids=a.rejected,
                       added_needs=added_needs, **kw)

    # Write output
    try:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(resp, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        return _err(f"Cannot write output file: {exc}")

    # Print one summary line
    status = resp.get("status", "unknown")
    turn   = resp.get("turn", 0)
    if status == "needs_clarification":
        detail = f"{len(resp.get('questions', []))} question(s)"
    elif status == "needs_confirmation":
        detail = f"{len((resp.get('summary') or {}).get('needs', []))} need(s)"
    elif status == "completed":
        detail = f"{len((resp.get('plan') or {}).get('action_cards', []))} card(s)"
    else:
        detail = ""
    print(f"status={status} turn={turn}" + (f" {detail}" if detail else ""))

    return 0 if status != "failed" else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
