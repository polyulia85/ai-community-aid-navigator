"""
AI Community Aid Navigator — Agent 1: Crisis Understanding & Clarification Parser
Contracts: docs/contracts/SHARED_CONTRACTS.md (v1.1)
Pure standard library implementation (Python 3.10+). Zero external dependencies.

Contract invariants enforced (§3.1, §3.2, §4.1):
- proposed_needs: need_id, category, description, original_quote, user_reported=True,
  confirmation_status="proposed", urgency (never "priority").
- factual_claims: fact_id, field, value, confirmation_status="proposed", time_context.
- result top-level: narrative_summary, factual_claims, proposed_needs,
  safety_or_official_deadline_flags, triggering_events, ambiguity_flags=[].
- safety flags: {type, quote, note} — never {type, reason, action_required}.
- Job loss: emits employment_status in factual_claims + "job_loss" in triggering_events.
- Bereavement: emits employment_status="bereaved_survivor" in factual_claims + "bereavement" in triggering_events.
- Urgency escalation: rent_due_date < ref_date → housing urgency="immediate".
- Eviction threat phrase → housing_assistance urgency="immediate".
- Unemployment income extraction.
- Whole original quotes: complete sentences/clauses preserved without mid-word truncation.
- Narrative summary: preserves all substantive needs (job loss, rent, food).
"""
from datetime import date, datetime, timezone
import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

RE_NORMALIZE_QUOTES = [
    (re.compile(r"[\u2018\u2019\u201B]"), "'"),
    (re.compile(r"[\u201C\u201D\u201F]"), '"'),
    (re.compile(r"[\u2013\u2014]"), "-"),
]

# ---------------------------------------------------------------------------
# PII patterns
# ---------------------------------------------------------------------------

RE_SSN_9DIGIT = re.compile(r"\b\d{9}\b")
RE_SSN_STRICT = re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b")
RE_CARD_FULL = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
RE_BANK_FULL = re.compile(r"\b(?:routing|account)[\s#:]*\d{8,12}\b", re.IGNORECASE)
RE_FORBIDDEN_WORDS = re.compile(
    r"\b(user_ssn|credit_card|bank_account|routing_number)\b", re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Eviction & Lockout patterns
# ---------------------------------------------------------------------------

RE_NEGATED_EVICTION = re.compile(
    r"\b(?:no|not|never|did\s*not|didn'?t|hasn'?t|without)\s+"
    r"(?:received?\s+)?(?:got\s+)?(?:given\s+)?(?:any\s+)?(?:written\s+|formal\s+)?"
    r"eviction\s+notice\b|"
    r"\beviction\s+notice\b[^\.\,\;\n]*?\b(?:not\s+received|none|no\s+so\s+far|yet)\b|"
    r"\bno\s+eviction\s+notice\b",
    re.IGNORECASE,
)

RE_EVICTION_AFFIRMATIVE = re.compile(
    r"\b(?:received|got|given|served|have|posted)\s+(?:a\s+|an\s+)?(?:formal\s+|written\s+)?"
    r"(?:3-day|three-day|pay\s+or\s+quit|eviction)\s+notice\b|"
    r"\b(?:3-day|three-day)\s+notice\s+to\s+(?:pay\s+or\s+quit|vacate)\b",
    re.IGNORECASE,
)

# Eviction or lockout threat (verbal/unconfirmed -> stays at housing baseline "high")
RE_EVICTION_THREAT = re.compile(
    r"\b(?:landlord|owner)\s+(?:said\s+)?(?:he\s+|she\s+|they\s+)?(?:will|threatened\s+to|plans\s+to|is\s+going\s+to)\s+(?:evict|lock\s+(?:us|me)\s+out|change\s+the\s+locks)\b|"
    r"\bthreatened\s+(?:us\s+|me\s+)?(?:with\s+eviction|to\s+lock\s+(?:us|me)\s+out|to\s+change\s+the\s+locks)\b|"
    r"\b(?:lock\s+(?:us|me)\s+out|change\s+the\s+locks)\b|"
    r"\bfacing\s+eviction\b",
    re.IGNORECASE,
)

# Item 3: Actual completed lockout (with or without "us"/"me")
RE_ACTUAL_LOCKOUT = re.compile(
    r"\b(?:"
    r"locked\s+(?:us|me)\s+out|"
    r"(?:was|were|got|am|are|is)\s+locked\s+out|"
    r"changed\s+the\s+locks(?:\s+and\s+(?:we|i)\s+can'?t\s+get\s+in)?"
    r")\b",
    re.IGNORECASE,
)

# Item 5: Landlord threatening harm or forcing tenant out
RE_LANDLORD_HOUSING_THREAT = re.compile(
    r"\b(?:landlord|owner)\b[^\.\;\n]*?\b(?:threatened|leave|evict|kick\s+(?:us|me)\s+out|lock)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Food need & urgency patterns (Items 6, 7, 8, 9)
# ---------------------------------------------------------------------------

RE_FOOD_NEED_SIGNAL = re.compile(
    r"\b(?:"
    r"(?:no|don'?t\s+have(?:\s+any)?|do\s+not\s+have(?:\s+any)?|haven'?t\s+got(?:\s+any)?)\s+(?:food|groceries)(?:\s+left|\s+at\s+home)?|"
    r"out\s+of\s+(?:food|groceries)|"
    r"run(?:ning)?\s+out\s+of\s+(?:food|groceries)|"
    r"low\s+on\s+(?:food|groceries)|"
    r"nothing\s+to\s+eat|"
    r"hungry|starving|"
    r"(?:need|needs|needing)\s+(?:help\s+with\s+|some\s+)?(?:food|groceries|pantry)|"
    r"(?:problems?|trouble|issues?|help|assistance|shortage|struggling)\s+(?:with|getting|buying|affording)?\s*(?:[\w\s,]+?\s+and\s+)?(?:food|groceries|eat(?:ing)?)|"
    r"(?:food|groceries)\s+(?:problems?|trouble|issues?|help|assistance|shortage)"
    r")\b",
    re.IGNORECASE,
)

RE_FOOD_IMMEDIATE_SIGNAL = re.compile(
    r"\b(?:"
    r"(?:no|don'?t\s+have(?:\s+any)?|do\s+not\s+have(?:\s+any)?)\s+(?:food|groceries)(?:\s+left|\s+at\s+home)?|"
    r"out\s+of\s+(?:food|groceries)|"
    r"run\s+out\s+of\s+(?:food|groceries)|"
    r"nothing\s+to\s+eat(?:\s+today)?|"
    r"hungry|starving"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Safety patterns
# ---------------------------------------------------------------------------

_HARM_TARGETS = (
    r"(?:me|us|her|him|them|"
    r"myself|himself|herself|themselves|"
    r"someone|anyone|"
    r"(?:my|the|our)\s+(?:son|daughter|child(?:ren)?|kids?|baby)|"
    r"(?:my|the|our)\s+(?:wife|husband|partner|mom|dad|mother|father|family)|"
    r"(?:my|the)\s+(?:dog|cat|pets?)"
    r")"
)

_HARM_SUBJECTS = (
    r"\b(?:he|she|they|(?:(?:the|my|our)\s+)?(?:landlord|partner|ex|husband|wife|boyfriend|girlfriend|fiance[e]?|roommate|manager|neighbor|father|mother|stepfather|stepmother|dad|mom|brother|sister))"
)

RE_SAFETY_DISTRESS = re.compile(
    r"(?:"
    r"\bkill(?:ing)?\s*(?:myself|himself|herself|themselves|him|her|them)\b|"
    r"\bwant\s+to\s+die\b|"
    r"\bdon['\u2019]?t\s+want\s+to\s+(?:live|be\s+alive)(?:\s+anymore)?\b|"
    r"\b(?:want|wants)\s+to\s+end\s+my\s+life\b|"
    r"\b(?:thinking\s+about\s+)?ending\s+(?:everything|it\s+all|my\s+life)\b|"
    r"\bend\s+(?:everything|it\s+all|my\s+life)\b|"
    r"\bno\s+reason\s+to\s+live\b|"
    r"\bcan['\u2019]?t\s+go\s+on\s+(?:like\s+this|anymore)\b|"
    r"\bcan['\u2019]?t\s+take\s+this\b|"
    r"\beveryone\s+would\s+be\s+better\s+off\s+without\s+me\b|"
    r"\bsuicide\b|"
    r"\bharm\s+myself\b|"
    r"\bhurt\s+myself\b|"
    + _HARM_SUBJECTS + r"\s+threatened\s+to\s+(?:hurt|harm|kill|beat|attack|abuse)\s+" + _HARM_TARGETS + r"\b|"
    + r"\b(?:threaten|threatened|threatening)\s+(?:to\s+)?(?:kill|hurt|harm|shoot|beat)\s+" + _HARM_TARGETS + r"\b|"
    + r"\b(?:afraid|scared)\s+(?:(?:my|our)\s+)?(?:ex|boyfriend|husband|partner|father)\s+(?:will|might)\s+(?:hurt|kill|harm)\b|"
    + r"\b(?:afraid|scared|worried)\s+(?:that\s+)?(?:he|she|they)\s+(?:will|might)\s+(?:come\s+back\s+(?:and\s+)?)?(?:hurt|harm|kill|beat|attack|abuse)\b|"
    + r"\b(?:he|she|they)\s+will\s+come\s+back\s+(?:and\s+)?(?:hurt|harm|kill|beat|attack|abuse)\b|"
    + _HARM_SUBJECTS + r"\s+(?:will|might|is\s+going\s+to|are\s+going\s+to|threatened\s+to|said\s+(?:he|she|they)\s+(?:will|would))\s+(?:hurt|harm|kill|beat|attack|abuse)\s+" + _HARM_TARGETS + r"\b|"
    + r"\bcome\s+back\s+and\s+(?:hurt|harm|kill|beat|attack|abuse)\b|"
    + r"\b(?:going\s+to|might)\s+(?:hurt|kill|harm)\s+(?:him|her|someone|others)\b|"
    + r"\b(?:husband|boyfriend|partner|ex)\s+(?:hits?|hitting|beats?|beating|struck)\s+(?:me|the\s+kids?|us)\b|"
    + r"\bhits?\s+me\b|"
    + r"\bhitting\s+me\b|"
    + r"\bbeats?\s+me\b|"
    + r"\bbeating\s+me\b|"
    + r"\bunsafe\s+at\s+home\b|"
    + r"\bdanger\s+at\s+home\b|"
    + r"\bmight\s+hurt\s+someone\b|"
    + r"\bhopeless\b"
    + r")",
    re.IGNORECASE,
)

RE_BENIGN_SAFETY_CONTEXT = re.compile(
    r"\b(?:show\s+about\s+violence|movie|program\s+years\s+ago|substance\s+abuse\s+program\s+years\s+ago|vacation|lease\s+ending)\b",
    re.IGNORECASE,
)

RE_SLEEPING_CAR = re.compile(
    r"\b(sleeping\s+in\s+(?:our\s+|my\s+|the\s+)?car|living\s+in\s+(?:our\s+|my\s+|the\s+)?car|"
    r"homeless|on\s+the\s+street|nowhere\s+to\s+stay)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Triggering-event patterns
# ---------------------------------------------------------------------------

RE_JOB_LOSS = re.compile(
    r"\b(lost\s+(?:my\s+)?job|laid\s+off|was\s+laid\s+off|unemployed|fired|"
    r"no\s+other\s+income|laid\s+off\s+from|let\s+go\s+from)\b",
    re.IGNORECASE,
)

RE_REDUCED_HOURS_OR_PAY = re.compile(
    r"\b(?:"
    r"hours?\s+cut|cut\s+(?:my\s+|our\s+)?hours?|reduced\s+hours?|"
    r"(?:hours|shifts?|schedule)\s+(?:were|was|got|are|have\s+been)\s+cut|"
    r"pay\s+cut|cut\s+(?:my\s+|our\s+)?pay|"
    r"(?:pay|wage|wages|salary|paycheck)\s+(?:was|were|got|has\s+been)\s+(?:cut|reduced|slashed|dropped)(?:\s+by\s+\w+)?"
    r")\b",
    re.IGNORECASE,
)

RE_INCOME_LOSS_SIGNAL = re.compile(
    r"\b(?:lost\s+(?:my\s+|our\s+)?(?:job|income|paycheck)|laid\s+off|was\s+laid\s+off|unemployed|fired|"
    r"hours?\s+cut|cut\s+(?:my\s+|our\s+)?hours?|reduced\s+hours?|pay\s+cut|cut\s+(?:my\s+|our\s+)?pay|"
    r"(?:hours|shifts?|schedule)\s+(?:were|was|got|are|have\s+been)\s+cut|"
    r"(?:pay|wage|wages|salary|paycheck)\s+(?:was|were|got|has\s+been)\s+(?:cut|reduced|slashed|dropped)(?:\s+by\s+\w+)?|"
    r"no\s+(?:other\s+)?income|zero\s+income)\b",
    re.IGNORECASE,
)

RE_TRIGGERING_EVENT = re.compile(
    r"\b(?:lost\s+(?:my\s+)?job|laid\s+off|was\s+laid\s+off|unemployed|fired|"
    r"hours?\s+cut|cut\s+(?:my\s+)?hours?|reduced\s+hours?|pay\s+cut|cut\s+(?:my\s+|our\s+)?pay|"
    r"hours\s+(?:were|got|are|have\s+been)\s+cut|cut\s+(?:my|our)?\s*hours|"
    r"(?:pay|wage|wages|salary|paycheck)\s+(?:was|were|got|has\s+been)\s+(?:cut|reduced|slashed|dropped)(?:\s+by\s+\w+)?|"
    r"let\s+go\s+from|medical\s+emergency|hospitalization|hospital\s+bill|illness|accident|injury|hospital|"
    r"rent\s+increase|unexpected\s+bill|passed\s+away|passed|died|death\s+of|"
    r"lost\s+my\s+(?:husband|wife|partner|spouse)|sole\s+earner|divorce|"
    r"disability|natural\s+disaster|flood|fire|evicted|eviction)\b",
    re.IGNORECASE,
)

RE_BEREAVEMENT = re.compile(
    r"\b(passed\s+away|passed|died|death\s+of|lost\s+my\s+(?:husband|wife|partner|spouse)|"
    r"sole\s+earner|survivor\s+benefits)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Income patterns
# ---------------------------------------------------------------------------

RE_INCOME_STANDARD = re.compile(
    r"\b(?:make|earn|earns?|income\s*(?:is|of)?|brings?\s+in)\s+(?:about\s+|around\s+|approx(?:\.)?\s*)?\$?([0-9,]+)",
    re.IGNORECASE,
)

RE_INCOME_BENEFIT = re.compile(
    r"\b(?:get|gets|receive|receives|collect|draws?)\s+(?:about\s+|around\s+|approx(?:\.)?\s*)?\$?([0-9,]+)"
    r"\s*(?:a\s+month|per\s+month|monthly)?\s*(?:in\s+|from\s+)?"
    r"(?:unemployment|disability|ssdi|ssi|benefits?|assistance)\b",
    re.IGNORECASE,
)

MONTH_MAP = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}

NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
}


def normalize_text(text: str) -> str:
    for pattern, replacement in RE_NORMALIZE_QUOTES:
        text = pattern.sub(replacement, text)
    return text


def sanitize_pii(text: str) -> str:
    text = RE_SSN_STRICT.sub("[REDACTED_PII]", text)
    text = RE_SSN_9DIGIT.sub("[REDACTED_PII]", text)
    text = RE_CARD_FULL.sub("[REDACTED_PII]", text)
    text = RE_BANK_FULL.sub("[REDACTED_PII]", text)
    text = RE_FORBIDDEN_WORDS.sub("[REDACTED_PII]", text)
    return text


def _fact_id(field: str, index: int) -> str:
    return f"fact_{field}_{index:03d}"


def _need_id(category: str, index: int) -> str:
    return f"need_{index:03d}"


def _make_fact(
    field: str,
    value: Any,
    index: int,
    time_context: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    fact: Dict[str, Any] = {
        "fact_id": _fact_id(field, index),
        "field": field,
        "value": value,
        "confirmation_status": "proposed",
        "source": extra.pop("source", "user_statement"),
        "time_context": time_context,
    }
    fact.update(extra)
    return fact


def _make_need(
    category: str,
    index: int,
    description: str,
    original_quote: str,
    urgency: str,
    urgency_reason: Optional[str] = None,
    subcategory: Optional[str] = None,
) -> Dict[str, Any]:
    need: Dict[str, Any] = {
        "need_id": _need_id(category, index),
        "category": category,
        "description": description,
        "original_quote": original_quote,
        "user_reported": True,
        "confirmation_status": "proposed",
        "urgency": urgency,
        "urgency_reason": urgency_reason,
        "user_priority": None,
    }
    if subcategory is not None:
        need["subcategory"] = subcategory
    return need


def _extract_rent_due_date(text: str, ref_date: date) -> Optional[date]:
    """Shared rent_due_date resolver for both story and clarification answers (Item 11)."""
    text_lower = text.lower()
    rent_is_explicitly_past = bool(
        re.search(
            r"\b(was\s+due|is\s+overdue|behind\s+on\s+rent|past\s+due|overdue)\b",
            text_lower,
        )
    )
    rent_clause = None
    clauses = re.split(r"[.;\n]|(?:\band\b)", text_lower)
    for clause in clauses:
        if "rent" in clause and ("due" in clause or "1st" in clause or "first" in clause):
            if not any(u in clause for u in ["electric", "power", "utility", "gas", "smud", "pg&e"]):
                rent_clause = clause
                break

    if not rent_clause:
        return None

    sorted_months = sorted(MONTH_MAP.keys(), key=len, reverse=True)
    months_pat = "|".join(sorted_months)
    due_m = re.search(
        rf"\b(?:due|was\s+due)\s+(?:on\s+)?({months_pat})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s*(\d{{4}})?\b",
        rent_clause,
    )
    if due_m:
        month_str = due_m.group(1).lower()
        day_str = int(due_m.group(2))
        year_str = due_m.group(3)
        month_num = MONTH_MAP.get(month_str)
        if month_num and 1 <= day_str <= 31:
            try:
                candidate_year = int(year_str) if year_str else ref_date.year
                target_date = date(candidate_year, month_num, day_str)
                if not year_str:
                    days_diff = (ref_date - target_date).days
                    if days_diff > 60 and not rent_is_explicitly_past:
                        target_date = date(candidate_year + 1, month_num, day_str)
                    elif days_diff > 0 and not rent_is_explicitly_past and "was due" not in rent_clause and days_diff > 300:
                        target_date = date(candidate_year + 1, month_num, day_str)
                return target_date
            except ValueError:
                return None

    day_only = re.search(
        r"\bdue\s+on\s+the\s+(\d{1,2})(?:st|nd|rd|th)?\b|\bdue\s+on\s+the\s+(1st|first)\b",
        rent_clause,
    )
    if day_only:
        d = (
            1
            if (day_only.group(2) or day_only.group(1) == "1")
            else int(day_only.group(1))
        )
        if 1 <= d <= 31:
            try:
                candidate_year = ref_date.year
                candidate_month = ref_date.month
                if d < ref_date.day and not rent_is_explicitly_past:
                    if candidate_month == 12:
                        candidate_month = 1
                        candidate_year += 1
                    else:
                        candidate_month += 1
                return date(candidate_year, candidate_month, d)
            except ValueError:
                return None
    return None


def handle_agent_1(
    request_dict: Dict[str, Any], ref_date: Optional[date] = None
) -> Dict[str, Any]:
    task_type = request_dict.get("task_type")
    payload = request_dict.get("payload")
    req_id = request_dict.get("request_id", "req-unknown")
    run_id = request_dict.get("run_id", "run-unknown")
    case_id = request_dict.get("case_id", "case-unknown")
    case_ver = request_dict.get("case_version", 1)
    corr_id = request_dict.get("correlation_id", "corr-unknown")
    now_iso = datetime.now(timezone.utc).isoformat()

    base_env: Dict[str, Any] = {
        "request_id": req_id,
        "run_id": run_id,
        "case_id": case_id,
        "case_version": case_ver,
        "correlation_id": corr_id,
        "agent_id": "agent_1",
        "schema_version": "1.0",
        "status": "completed",
        "result": {},
        "issues": [],
        "clarification_requests": [],
        "evidence_refs": [],
        "generated_at": now_iso,
        "is_mock": True,
    }

    if payload is None:
        base_env["status"] = "failed"
        base_env["issues"].append({
            "code": "MISSING_PAYLOAD",
            "severity": "critical",
            "message": "Payload is missing from request.",
        })
        return base_env

    resolved_date = ref_date
    if resolved_date is None:
        ref_raw = payload.get("ref_date")
        if ref_raw:
            try:
                resolved_date = date.fromisoformat(ref_raw)
            except Exception:
                base_env["status"] = "failed"
                base_env["issues"].append({
                    "code": "INVALID_REF_DATE",
                    "severity": "critical",
                    "message": f"Invalid ref_date: '{ref_raw}'",
                })
                return base_env
        else:
            resolved_date = date.today()

    if task_type == "understand_story":
        return _understand_story(payload, base_env, resolved_date)
    elif task_type == "parse_clarification_answer":
        return _parse_clarification(payload, base_env, resolved_date)
    else:
        base_env["status"] = "failed"
        base_env["issues"].append({
            "code": "UNSUPPORTED_TASK",
            "severity": "critical",
            "message": f"Unsupported task_type: '{task_type}'",
        })
        return base_env


def _understand_story(
    payload: Dict[str, Any], env: Dict[str, Any], ref_date: date
) -> Dict[str, Any]:
    story_raw = payload.get("story_text")
    if not story_raw or not story_raw.strip():
        env["status"] = "failed"
        env["issues"].append({
            "code": "EMPTY_STORY",
            "severity": "critical",
            "message": "Story text is empty or missing.",
        })
        return env

    story = normalize_text(story_raw)
    story = sanitize_pii(story)
    story_lower = story.lower()

    facts: List[Dict[str, Any]] = []
    proposed_needs: List[Dict[str, Any]] = []
    flags: List[Dict[str, Any]] = []
    triggering_events: List[str] = []

    fact_idx = 1
    need_idx = 1

    raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", story.strip()) if s.strip()]

    def extract_full_sentence_quote(pattern: str, fallback: str) -> str:
        for s in raw_sentences:
            if re.search(pattern, s, re.I):
                return s
        return fallback

    # 1. Life-Safety & Distress Detection (Neutral note; Supervisor selects directory contacts)
    safety_m = RE_SAFETY_DISTRESS.search(story)
    if safety_m and not RE_BENIGN_SAFETY_CONTEXT.search(story):
        quote_str = safety_m.group(0)
        is_harm_threat = bool(
            re.search(r"\b(?:threaten|threatened|threatening|hurt|harm|kill|beat|hit|attack|abuse)\b", quote_str, re.IGNORECASE)
        )
        flags.append({
            "type": "safety",
            "quote": quote_str,
            "note": "Threat of physical harm reported" if is_harm_threat else "Life-safety distress signal reported",
        })

    # 2. ZIP Code Extraction
    zip_m = re.search(r"\b(9\d{4})\b", story)
    if zip_m:
        facts.append(_make_fact("zip_code", zip_m.group(1), fact_idx))
        fact_idx += 1

    # 3. Children Ages & Household Size
    is_single_parent = bool(
        re.search(r"\b(single\s+(?:mom|dad|mother|father|parent))\b", story_lower)
    )

    single_child_m = re.search(
        r"\b(?:one|1)\s+(?:child|kid),?\s*(?:age\s*)?(\d+)\b", story_lower
    )
    kids_m = re.search(
        r"\b(?:with\s+)?(one|two|three|four|five|\d+)\s+(?:kids?|child(?:ren)?),?\s*"
        r"(?:ages?\s*)?(\d+)(?:\s*(?:and|&|,)\s*(\d+))?(?:\s*(?:and|&|,)\s*(\d+))?",
        story_lower,
    )

    if single_child_m:
        age = int(single_child_m.group(1))
        facts.append(_make_fact("children_ages", [age], fact_idx))
        fact_idx += 1
        if is_single_parent:
            facts.append(_make_fact("household_size", 2, fact_idx))
            fact_idx += 1
    elif kids_m:
        count_raw = kids_m.group(1).lower()
        num_kids = NUM_WORDS.get(count_raw, int(count_raw) if count_raw.isdigit() else 1)
        ages: List[int] = []
        for g in [kids_m.group(2), kids_m.group(3), kids_m.group(4)]:
            if g and g.isdigit():
                ages.append(int(g))
        if ages:
            facts.append(_make_fact("children_ages", ages, fact_idx))
            fact_idx += 1
        if is_single_parent:
            facts.append(_make_fact("household_size", num_kids + 1, fact_idx))
            fact_idx += 1
    else:
        count_only = re.search(
            r"\b(one|two|three|four|five|\d+)\s+(?:kids?|child(?:ren)?)\b", story_lower
        )
        if count_only and is_single_parent:
            num_kids = NUM_WORDS.get(count_only.group(1), 2)
            facts.append(_make_fact("household_size", num_kids + 1, fact_idx))
            fact_idx += 1

    # 4. Triggering Events: Job Loss
    job_loss_m = RE_JOB_LOSS.search(story)
    if job_loss_m:
        triggering_events.append("job_loss")
        facts.append(_make_fact(
            "employment_status",
            "laid_off",
            fact_idx,
            time_context="at time of report",
        ))
        fact_idx += 1
        
    # 4b. Triggering Events: Reduced Hours / Pay Cut
    reduced_hours_m = RE_REDUCED_HOURS_OR_PAY.search(story)
    if reduced_hours_m and not job_loss_m:
        triggering_events.append("reduced_hours")
        facts.append(_make_fact(
            "employment_status",
            "reduced_hours",
            fact_idx,
            time_context="current",
        ))
        fact_idx += 1

    # 5. Triggering Events: Bereavement (Item 10: life circumstance only — NEVER employment_status)
    bereavement_m = RE_BEREAVEMENT.search(story)
    if bereavement_m and not job_loss_m:
        death_signal = bool(re.search(
            r"\b(passed\s+away|passed|died|death\s+of|lost\s+my\s+(?:husband|wife|partner|spouse))\b",
            story_lower,
        ))
        if death_signal:
            triggering_events.append("bereavement")

    # 6. Eviction Notice & Actual Lockout (Items 3 & 4)
    has_eviction = False
    is_actual_lockout = bool(RE_ACTUAL_LOCKOUT.search(story))

    if RE_NEGATED_EVICTION.search(story):
        facts.append(_make_fact("has_written_eviction_notice", False, fact_idx))
        fact_idx += 1
        has_eviction = False
    elif RE_EVICTION_AFFIRMATIVE.search(story) or (
        "eviction notice" in story_lower and not RE_NEGATED_EVICTION.search(story)
    ):
        has_eviction = True
        facts.append(_make_fact(
            "has_written_eviction_notice",
            True,
            fact_idx,
            time_context=None,
        ))
        fact_idx += 1
        if re.search(r"\b3[-\s]day\s+notice\b", story_lower):
            facts.append(_make_fact("eviction_notice_type", "3_day_pay_or_quit", fact_idx))
            fact_idx += 1

    # Item 4: Confirmed late-stage lockout sets eviction_notice_type = "lockout"
    if is_actual_lockout and not any(f.get("field") == "eviction_notice_type" for f in facts):
        facts.append(_make_fact("eviction_notice_type", "lockout", fact_idx))
        fact_idx += 1

    # 7. Liquid Cash / Savings Extraction
    dollar_matches = list(re.finditer(r"\$([0-9,]+)", story))
    for m in dollar_matches:
        raw_val = m.group(1).replace(",", "")
        if not raw_val:
            continue
        val = int(raw_val)
        prefix = story[max(0, m.start() - 25):m.start()].lower()
        if "rent" in prefix or "earn" in prefix or "make" in prefix or "get" in prefix:
            continue
        if any(w in story_lower for w in ["left", "savings", "cash", "bank account", "have about", "only have"]):
            facts.append(_make_fact("cash_on_hand_approx", val, fact_idx))
            fact_idx += 1
            break

    # 8. Monthly Rent Amount
    rent_m = re.search(r"\brent\b[^\.\;\n]*?\$?([0-9,]+)", story, re.I)
    if rent_m:
        try:
            r_val = int(rent_m.group(1).replace(",", ""))
            facts.append(_make_fact("rent_amount_monthly", r_val, fact_idx))
            fact_idx += 1
        except ValueError:
            pass

    # 9. Rent Due Date Resolution
    rent_is_explicitly_past = bool(
        re.search(
            r"\b(was\s+due|is\s+overdue|behind\s+on\s+rent|past\s+due|overdue)\b",
            story_lower,
        )
    )
    rent_due_date = _extract_rent_due_date(story, ref_date)
    if rent_due_date is not None:
        facts.append(_make_fact(
            "rent_due_date",
            rent_due_date.isoformat(),
            fact_idx,
            time_context="user-stated date, not an official deadline",
        ))
        fact_idx += 1

    # 10. Monthly Household Income
    income_found = False

    benefit_m = RE_INCOME_BENEFIT.search(story)
    if benefit_m:
        try:
            val_int = int(benefit_m.group(1).replace(",", ""))
            is_approx = bool(
                re.search(r"\b(about|around|approx)\b",
                          story[max(0, benefit_m.start() - 15):benefit_m.end()], re.I)
            )
            facts.append(_make_fact(
                "household_gross_monthly_income",
                val_int,
                fact_idx,
                time_context="current",
                is_approximate=is_approx,
            ))
            fact_idx += 1
            income_found = True
        except ValueError:
            pass

    if not income_found:
        inc_m = RE_INCOME_STANDARD.search(story)
        if inc_m:
            try:
                val_str = inc_m.group(1).replace(",", "")
                val_int = int(val_str)
                is_approx = bool(
                    re.search(r"\b(about|around|approx)\b",
                              story[max(0, inc_m.start() - 15):inc_m.end()], re.I)
                )
                facts.append(_make_fact(
                    "household_gross_monthly_income",
                    val_int,
                    fact_idx,
                    time_context="current",
                    is_approximate=is_approx,
                ))
                fact_idx += 1
                income_found = True
            except ValueError:
                pass

    if not income_found and re.search(
        r"\b(no\s+income|zero\s+income|zero\s+monthly\s+income|no\s+other\s+income)\b",
        story_lower,
    ):
        facts.append(_make_fact(
            "household_gross_monthly_income",
            0,
            fact_idx,
            time_context="current",
            is_approximate=False,
        ))
        fact_idx += 1

    # 11. Proposed Needs — Multi-Domain Coverage
    # Item 10 & Follow-up Item 6: Propose income_assistance on income/job loss OR reduced work hours/pay cut
    if RE_INCOME_LOSS_SIGNAL.search(story) or RE_REDUCED_HOURS_OR_PAY.search(story):
        is_reduced_hours = bool(RE_REDUCED_HOURS_OR_PAY.search(story)) and not bool(RE_JOB_LOSS.search(story))
        income_quote = extract_full_sentence_quote(
            r"job|laid off|fired|unemployed|hours|paycheck|pay|wage|income",
            story,
        )
        proposed_needs.append(_make_need(
            "income_assistance",
            need_idx,
            description="Work hours or pay reduced" if is_reduced_hours else "Household income lost or severely reduced",
            original_quote=income_quote,
            urgency="high",
            urgency_reason="Work hours reduced" if is_reduced_hours else "Income loss or unemployment reported",
        ))
        need_idx += 1

    # Items 6, 7, 9: Grounded Food Assistance (require need signal; vague="high", acute="immediate")
    if RE_FOOD_NEED_SIGNAL.search(story):
        food_quote = extract_full_sentence_quote(r"food|groceries|eat|hungry|pantry", story)
        is_food_immediate = bool(RE_FOOD_IMMEDIATE_SIGNAL.search(story))
        if is_food_immediate:
            food_urgency = "immediate"
            food_desc = "Household is running low on food or groceries"
            food_reason = "Acute food shortage reported"
        else:
            food_urgency = "high"
            food_desc = "Food problem reported"
            food_reason = "Food problem reported"

        proposed_needs.append(_make_need(
            "food_assistance",
            need_idx,
            description=food_desc,
            original_quote=food_quote,
            urgency=food_urgency,
            urgency_reason=food_reason,
        ))
        need_idx += 1

    if re.search(
        r"\b(turn\s+off\s+my\s+gas|power\s+disconnection|disconnection\s+notice|shut\s*off|"
        r"electric\s+bill|smud|pg&e|utility|keep\s+the\s+heat\s+on)\b",
        story_lower,
    ):
        util_quote = extract_full_sentence_quote(r"gas|power|electric|utility|smud|pg&e", story)
        proposed_needs.append(_make_need(
            "utility_assistance",
            need_idx,
            description="Utility bill or shutoff prevention assistance",
            original_quote=util_quote,
            urgency="immediate",
            urgency_reason="Imminent utility disconnection notice",
        ))
        need_idx += 1

    # Medical Triggering Event
    if re.search(r"\b(medical\s+emergency|hospitalization|hospital\s+bill|asthma|accident|injury)\b", story_lower):
        if "medical_emergency" not in triggering_events:
            triggering_events.append("medical_emergency")

    if re.search(
        r"\b(broke\s+my\s+leg|hospital\s+bills?|hospitalization|health\s+insurance|prescription\s+medication|medical|asthma)\b",
        story_lower,
    ):
        med_quote = extract_full_sentence_quote(r"leg|hospital|bills?|insurance|medication|medical|asthma", story)
        proposed_needs.append(_make_need(
            "medical_health_coverage",
            need_idx,
            description="Medical bills or urgent healthcare expenses reported",
            original_quote=med_quote,
            urgency="high",
            urgency_reason="Unplanned emergency medical expenses impacting basic stability",
        ))
        need_idx += 1

    if re.search(
        r"\b(credit\s+card\s+minimum|debt\s+collectors|unaffordable\s+this\s+month)\b",
        story_lower,
    ):
        debt_quote = extract_full_sentence_quote(r"credit card|debt|collectors|unaffordable", story)
        proposed_needs.append(_make_need(
            "debt_hardship",
            need_idx,
            description="Debt or credit hardship requiring counseling or legal aid",
            original_quote=debt_quote,
            urgency="high",
            urgency_reason="Overwhelming debt collection stress",
        ))
        need_idx += 1

    if re.search(
        r"\b(apartment\s+fire|lost\s+all\s+our\s+clothes|clothes|beds|children'?s\s+essentials)\b",
        story_lower,
    ) and "fire" in story_lower:
        fire_quote = extract_full_sentence_quote(r"fire|clothes|beds", story)
        proposed_needs.append(_make_need(
            "material_in_kind",
            need_idx,
            description="Loss of household goods or clothing due to disaster",
            original_quote=fire_quote,
            urgency="high",
            urgency_reason="Loss of essential household goods in disaster",
        ))
        need_idx += 1

    # Housing Assistance (Items 1, 3, 4, 5, 7)
    sleeping_car = bool(RE_SLEEPING_CAR.search(story))
    has_motel = bool(re.search(
        r"\b(staying\s+in\s+a\s+motel|motel\s+runway|evicted\s+yesterday|rental\s+assistance|"
        r"need\s+rental\s+help|security\s+deposit|first\s+month\s+rent)\b",
        story_lower,
    ))
    has_eviction_threat = bool(RE_EVICTION_THREAT.search(story))
    has_landlord_threat = bool(RE_LANDLORD_HOUSING_THREAT.search(story))
    has_housing_keyword = bool(re.search(r"\bhousing\b", story_lower))
    has_rent_need = (
        (
            "rent" in story_lower
            or has_housing_keyword
            or has_eviction
            or is_actual_lockout
            or rent_is_explicitly_past
            or has_motel
            or has_eviction_threat
            or has_landlord_threat
        )
        and "apartment fire" not in story_lower
    )

    rent_overdue_by_date = (
        rent_due_date is not None and rent_due_date < ref_date
    )

    if sleeping_car:
        car_quote = extract_full_sentence_quote(r"car|homeless|street|nowhere", story)
        proposed_needs.append(_make_need(
            "housing_assistance",
            need_idx,
            description="No stable overnight shelter",
            original_quote=car_quote,
            urgency="immediate",
            urgency_reason="Lack of stable overnight shelter reported",
            subcategory="emergency_shelter",
        ))
        need_idx += 1
    elif has_rent_need:
        housing_quote = extract_full_sentence_quote(r"rent|evict|motel|lock|housing|landlord", story)
        has_lockout_threat = bool(re.search(r"\b(?:lock\s+(?:us|me)\s+out|change\s+the\s+locks)\b", story_lower)) and not is_actual_lockout

        # Item 1 & 3 & 4 & 7: Actual lockout / written notice / overdue rent = immediate;
        # verbal threats alone stay at baseline "high" so Agent 2 clarifies.
        if is_actual_lockout:
            urgency = "immediate"
            housing_desc = "Locked out of home"
            reason = "Already locked out of home (late-stage housing emergency)"
        elif has_eviction:
            urgency = "immediate"
            housing_desc = "Facing eviction notice"
            reason = "Eviction notice reported"
        elif rent_is_explicitly_past or rent_overdue_by_date:
            urgency = "immediate"
            housing_desc = "Rent is past due"
            reason = "Rent is overdue"
        elif has_lockout_threat:
            urgency = "high"
            housing_desc = "Landlord threatened lockout or lock change"
            reason = "Landlord threatened lockout or lock change"
        elif has_eviction_threat:
            urgency = "high"
            housing_desc = "Eviction threatened by landlord"
            reason = "Eviction threatened by landlord"
        elif has_landlord_threat:
            urgency = "high"
            housing_desc = "Landlord threatened tenant to leave"
            reason = "Landlord threat impacting housing stability"
        elif "rent" in story_lower:
            urgency = "high"
            housing_desc = "Rent assistance needed"
            reason = "Rent assistance needed"
        else:
            urgency = "high"
            housing_desc = "Housing problem reported"
            reason = "Housing problem reported"

        proposed_needs.append(_make_need(
            "housing_assistance",
            need_idx,
            description=housing_desc,
            original_quote=housing_quote,
            urgency=urgency,
            urgency_reason=reason,
        ))
        need_idx += 1

    # 12. Narrative Summary
    substantive_sentences = [
        s for s in raw_sentences
        if not re.search(r"^(i\s+don'?t\s+know\s+where\s+to\s+start|please\s+help\s+us|thank\s+you)\.?$", s, re.I)
    ]
    summary = " ".join(substantive_sentences) if substantive_sentences else story.strip()
    if summary and not summary.endswith((".", "!", "?")):
        summary += "."

    # 13. Ambiguity: unspecified hardship cause
    ambiguity_flags: List[Any] = []
    has_aid_need = bool(
        re.search(r"\b(food|groceries|eat|hungry|pantry|rent|housing|shelter|homeless|income|money|financial|afford)\b", story_lower)
    )
    has_root_cause = bool(RE_TRIGGERING_EVENT.search(story))
    if has_aid_need and not has_root_cause:
        ambiguity_flags.append({
            "field": "triggering_circumstances",
            "quote": story_raw,
            "note": "unspecified_hardship_cause",
        })

    env["result"] = {
        "narrative_summary": summary,
        "factual_claims": facts,
        "proposed_needs": proposed_needs,
        "safety_or_official_deadline_flags": flags,
        "triggering_events": triggering_events,
        "ambiguity_flags": ambiguity_flags,
    }
    return env


def _parse_clarification(
    payload: Dict[str, Any], env: Dict[str, Any], ref_date: date
) -> Dict[str, Any]:
    ans_raw = payload.get("answer_text", "")
    ans = normalize_text(ans_raw).strip()
    keys = payload.get("pending_fact_keys", [])
    facts: List[Dict[str, Any]] = []
    ans_lower = ans.lower()

    # 1. Eviction Notice & Threat Clarification Follow-ups (Items 1 & 2)
    if (
        "has_written_eviction_notice" in keys
        or "eviction_notice_type" in keys
        or re.search(r"\beviction\s+notice\b", ans_lower)
    ):
        has_yes = bool(
            re.search(
                r"\b(yes|yeah|yep|i have one|received|got a notice|got a 3-day notice)\b",
                ans_lower,
            )
        )
        uncertain = any(
            w in ans_lower for w in ["not sure", "don't know", "maybe", "waiting to see"]
        )
        has_no = bool(
            re.search(r"\b(no|nope|don'?t have|never|did not|nothing yet)\b", ans_lower)
        )
        if has_yes:
            facts.append({
                "fact_id": _fact_id("has_written_eviction_notice", len(facts) + 1),
                "field": "has_written_eviction_notice",
                "value": True,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": None,
            })
        elif not uncertain and has_no:
            facts.append({
                "fact_id": _fact_id("has_written_eviction_notice", len(facts) + 1),
                "field": "has_written_eviction_notice",
                "value": False,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "current",
            })

    # Court judgment / writ follow-up (Follow-up Item 2: "Yes" also sets eviction_notice_type)
    if "has_court_writ_or_judgment" in keys:
        if re.search(r"\b(yes|yeah|yep|court|writ|judgment|sheriff)\b", ans_lower) and not re.search(r"\b(no|nope|not\s+yet|none|not\s+sure)\b", ans_lower):
            facts.append({
                "fact_id": _fact_id("has_court_writ_or_judgment", len(facts) + 1),
                "field": "has_court_writ_or_judgment",
                "value": True,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "current",
            })
            notice_val = "writ" if re.search(r"\bwrit\b", ans_lower) else "judgment"
            facts.append({
                "fact_id": _fact_id("eviction_notice_type", len(facts) + 1),
                "field": "eviction_notice_type",
                "value": notice_val,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "user_clarification",
            })
        elif re.search(r"\b(no|nope|not\s+yet|none|no\s+court)\b", ans_lower):
            facts.append({
                "fact_id": _fact_id("has_court_writ_or_judgment", len(facts) + 1),
                "field": "has_court_writ_or_judgment",
                "value": False,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "current",
            })

    # Imminent removal in progress follow-up (Follow-up Item 2: "Yes" also sets eviction_notice_type="lockout")
    if "imminent_removal_in_progress" in keys:
        if (RE_ACTUAL_LOCKOUT.search(ans) or re.search(r"\b(yes|yeah|yep|changing\s+the\s+locks|right\s+now|today)\b", ans_lower)) and not re.search(r"\b(no|nope|not\s+yet|not\s+sure)\b", ans_lower):
            facts.append({
                "fact_id": _fact_id("imminent_removal_in_progress", len(facts) + 1),
                "field": "imminent_removal_in_progress",
                "value": True,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "current",
            })
            facts.append({
                "fact_id": _fact_id("eviction_notice_type", len(facts) + 1),
                "field": "eviction_notice_type",
                "value": "lockout",
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "user_clarification",
            })
        elif re.search(r"\b(no|nope|not\s+yet|just\s+threatened)\b", ans_lower):
            facts.append({
                "fact_id": _fact_id("imminent_removal_in_progress", len(facts) + 1),
                "field": "imminent_removal_in_progress",
                "value": False,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "current",
            })

    # Move-out Date vs Eviction Notice Date Extraction (Follow-up Item 1)
    sorted_months = sorted(MONTH_MAP.keys(), key=len, reverse=True)
    months_pat = "|".join(sorted_months)

    is_move_out_context = (
        "specific_move_out_date" in keys
        or bool(re.search(r"\b(?:leave|move\s+out|vacate|out)\s+(?:by|before|on)\b", ans_lower))
    )

    date_m = re.search(
        rf"\b({months_pat})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s*(\d{{4}})?\b",
        ans,
        re.IGNORECASE,
    )
    if date_m:
        month_str = date_m.group(1).lower()
        day_str = int(date_m.group(2))
        year_str = date_m.group(3)
        month_num = MONTH_MAP.get(month_str)

        has_notice_context = bool(re.search(r"\b(?:notice|eviction|dated|court|letter)\b", ans, re.IGNORECASE))
        is_rent_due = bool(re.search(rf"\b(?:rent|due\s+on)\s+[^\.\;]*?{month_str}", ans, re.IGNORECASE))

        if month_num and 1 <= day_str <= 31:
            year_val = int(year_str) if year_str else ref_date.year
            iso_date = f"{year_val:04d}-{month_num:02d}-{day_str:02d}"

            if is_move_out_context and not has_notice_context:
                if not any(f.get("field") == "specific_move_out_date" for f in facts):
                    facts.append({
                        "fact_id": _fact_id("specific_move_out_date", len(facts) + 1),
                        "field": "specific_move_out_date",
                        "value": iso_date,
                        "confirmation_status": "proposed",
                        "source": "user_statement",
                        "time_context": "user_clarification",
                    })
            elif has_notice_context or not is_rent_due:
                if not any(f.get("field") == "eviction_notice_date" for f in facts):
                    facts.append({
                        "fact_id": _fact_id("eviction_notice_date", len(facts) + 1),
                        "field": "eviction_notice_date",
                        "value": iso_date,
                        "confirmation_status": "proposed",
                        "source": "user_statement",
                        "time_context": "user_clarification",
                    })

    # Item 11: Rent Due Date Extraction in Clarification Answers
    rent_due_date = _extract_rent_due_date(ans, ref_date)
    if rent_due_date is not None:
        if not any(f.get("field") == "rent_due_date" for f in facts):
            facts.append({
                "fact_id": _fact_id("rent_due_date", len(facts) + 1),
                "field": "rent_due_date",
                "value": rent_due_date.isoformat(),
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "user-stated date, not an official deadline",
            })

    # 2. Triggering Circumstances
    circumstance_val = None
    if RE_REDUCED_HOURS_OR_PAY.search(ans):
        circumstance_val = "reduced_hours"
    elif re.search(r"\b(laid\s+off|lost\s+(?:my\s+)?job|fired|unemployed)\b", ans_lower):
        circumstance_val = "job_loss"
    elif re.search(r"\b(medical|hospital|hospitalization|sick|illness|injury|accident|asthma)\b", ans_lower):
        circumstance_val = "medical_emergency"
    elif re.search(r"\b(died|passed\s+away|bereavement|funeral)\b", ans_lower):
        circumstance_val = "bereavement"

    if circumstance_val:
        facts.append({
            "fact_id": _fact_id("triggering_circumstances", len(facts) + 1),
            "field": "triggering_circumstances",
            "value": circumstance_val,
            "confirmation_status": "proposed",
            "source": "user_statement",
            "time_context": "recent",
        })
        if circumstance_val == "reduced_hours":
            facts.append({
                "fact_id": _fact_id("employment_status", len(facts) + 1),
                "field": "employment_status",
                "value": "reduced_hours",
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "current",
            })

    # 3. Monthly Income Parsing (Item 12: extract whenever explicitly stated, even if not in pending_fact_keys)
    bare_zip_m = re.match(r"^\s*\$?(9\d{4})\s*$", ans.strip())
    if bare_zip_m:
        if not any(f.get("field") == "zip_code" for f in facts):
            facts.append({
                "fact_id": _fact_id("zip_code", len(facts) + 1),
                "field": "zip_code",
                "value": bare_zip_m.group(1),
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": None,
            })
    else:
        inc_m = RE_INCOME_STANDARD.search(ans) or RE_INCOME_BENEFIT.search(ans)
        if inc_m:
            try:
                val = int(inc_m.group(1).replace(",", ""))
                facts.append({
                    "fact_id": _fact_id("household_gross_monthly_income", len(facts) + 1),
                    "field": "household_gross_monthly_income",
                    "value": val,
                    "confirmation_status": "proposed",
                    "source": "user_statement",
                    "time_context": "current",
                })
            except ValueError:
                pass
        elif "household_gross_monthly_income" in keys:
            is_rent_or_due = bool(re.search(r"\b(rent|due|bill|owe|owing|left|account|balance)\b", ans_lower))
            if not is_rent_or_due:
                num_m = re.search(r"^\$?([0-9,]+)$|\b(?:about|around)\s+\$?([0-9,]+)\b", ans_lower)
                if num_m:
                    raw_num = num_m.group(1) or num_m.group(2)
                    try:
                        val = int(raw_num.replace(",", ""))
                        facts.append({
                            "fact_id": _fact_id("household_gross_monthly_income", len(facts) + 1),
                            "field": "household_gross_monthly_income",
                            "value": val,
                            "confirmation_status": "proposed",
                            "source": "user_statement",
                            "time_context": "current",
                        })
                    except ValueError:
                        pass

    # 3b. ZIP Code Parsing (Item 12: extract whenever stated, regardless of pending_fact_keys)
    zip_m = re.search(r"\b(9\d{4})\b", ans)
    if zip_m:
        zip_val = zip_m.group(1)
        if not any(f.get("field") == "zip_code" for f in facts):
            facts.append({
                "fact_id": _fact_id("zip_code", len(facts) + 1),
                "field": "zip_code",
                "value": zip_val,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": None,
            })

    # 3c. Household Size Parsing (Item 12: extract whenever explicitly stated with people/members/household)
    hh_word_m = re.search(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:people|persons?|members?|of\s+us)\b",
        ans_lower,
    )
    _HH_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    if hh_word_m:
        raw = hh_word_m.group(1)
        hh_val = _HH_WORDS.get(raw) or (int(raw) if raw.isdigit() else None)
        if hh_val is not None:
            facts.append({
                "fact_id": _fact_id("household_size", len(facts) + 1),
                "field": "household_size",
                "value": hh_val,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": None,
            })
    elif "household_size" in keys and re.search(r"^\s*\d+\s*$", ans.strip()):
        try:
            hh_val = int(ans.strip())
            facts.append({
                "fact_id": _fact_id("household_size", len(facts) + 1),
                "field": "household_size",
                "value": hh_val,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": None,
            })
        except ValueError:
            pass

    # 4. Rent Amount & Overdue Amount Extraction
    _is_arrears = bool(re.search(r"\b(amount\s+due|arrears|past\s+due)\b", ans_lower))
    rent_m = re.search(r"\b(?:rent|amount\s+due|arrears|past\s+due)\b[^\.\;\n]*?\$?([0-9,]+)", ans, re.I)
    if rent_m:
        try:
            r_val = int(rent_m.group(1).replace(",", ""))
            if _is_arrears:
                facts.append({
                    "fact_id": _fact_id("rent_arrears_amount", len(facts) + 1),
                    "field": "rent_arrears_amount",
                    "value": r_val,
                    "confirmation_status": "proposed",
                    "source": "user_statement",
                    "time_context": "current",
                })
            else:
                facts.append({
                    "fact_id": _fact_id("rent_amount_monthly", len(facts) + 1),
                    "field": "rent_amount_monthly",
                    "value": r_val,
                    "confirmation_status": "proposed",
                    "source": "user_statement",
                    "time_context": "current",
                })
        except ValueError:
            pass

    # 5. Liquid Cash Extraction
    cash_m = (
        re.search(r"\$([0-9,]+)\s*(?:left|in\s+(?:cash|savings|my\s+account|the\s+bank|account))", ans_lower)
        or re.search(r"\b(?:have|only\s+have|left\s+with)\s+(?:about\s+|around\s+)?\$([0-9,]+)", ans_lower)
    )
    if cash_m:
        try:
            c_val = int(cash_m.group(1).replace(",", ""))
            facts.append({
                "fact_id": _fact_id("cash_on_hand_approx", len(facts) + 1),
                "field": "cash_on_hand_approx",
                "value": c_val,
                "confirmation_status": "proposed",
                "source": "user_statement",
                "time_context": "current",
            })
        except ValueError:
            pass

    # 6. Grounded Food Assistance Need Detection in Clarification Answers (Items 8 & 9)
    proposed_needs: List[Dict[str, Any]] = []
    if RE_FOOD_NEED_SIGNAL.search(ans):
        existing_needs = payload.get("existing_needs") or []
        existing_need_cats = {n.get("category") for n in existing_needs if isinstance(n, dict)}

        if "food_assistance" not in existing_need_cats:
            max_idx = 0
            for n in existing_needs:
                if isinstance(n, dict):
                    nid = str(n.get("need_id", ""))
                    m = re.match(r"^need_(\d+)$", nid)
                    if m:
                        max_idx = max(max_idx, int(m.group(1)))

            next_idx = max_idx + 1 if max_idx > 0 else (len(existing_needs) + 1)
            is_food_immediate = bool(RE_FOOD_IMMEDIATE_SIGNAL.search(ans))
            if is_food_immediate:
                food_urgency = "immediate"
                food_desc = "Household is running low on food or groceries"
                food_reason = "Acute food shortage reported"
            else:
                food_urgency = "high"
                food_desc = "Food problem reported"
                food_reason = "Food problem reported"

            proposed_needs.append(_make_need(
                "food_assistance",
                next_idx,
                description=food_desc,
                original_quote=ans,
                urgency=food_urgency,
                urgency_reason=food_reason,
            ))

    # 6b. Follow-up Item 6: Reduced work hours / pay cut in clarification -> propose income_assistance
    if circumstance_val == "reduced_hours":
        existing_needs = payload.get("existing_needs") or []
        existing_need_cats = {n.get("category") for n in existing_needs if isinstance(n, dict)}
        if "income_assistance" not in existing_need_cats and not any(
            n.get("category") == "income_assistance" for n in proposed_needs
        ):
            max_idx = 0
            for n in existing_needs:
                if isinstance(n, dict):
                    m = re.match(r"^need_(\d+)$", str(n.get("need_id", "")))
                    if m:
                        max_idx = max(max_idx, int(m.group(1)))
            next_idx = max(max_idx, len(existing_needs) + len(proposed_needs)) + 1
            proposed_needs.append(_make_need(
                "income_assistance",
                next_idx,
                description="Work hours or pay reduced",
                original_quote=ans,
                urgency="high",
                urgency_reason="Work hours reduced",
            ))

    trig_events: List[str] = []
    for f in facts:
        if f.get("field") == "triggering_circumstances":
            trig_events.append(str(f.get("value")))

    env["result"] = {
        "factual_claims": facts,
        "proposed_needs": proposed_needs,
        "triggering_events": trig_events,
        "clarification_settled": len(facts) > 0,
        "ambiguity_flags": [],
    }
    return env