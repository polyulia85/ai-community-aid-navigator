"""Supervisor checks S0–S9 (Shared JSON Contracts v1.1, section 5.2).

Each check returns a list of Issue dicts: {code, severity, message, related_ref}.
Empty list = the check passed. The Supervisor accepts a result only when no
check returned a critical issue.
"""
import re

from navigator.supervisor import contract as C

# ---------------------------------------------------------------- patterns
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{3} \d{2} \d{4}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
ROUTING_RE = re.compile(r"(?<![\d-])\d{9}(?![\d-])")  # 9 digits alone; ZIP+4 has a dash
REDACTED = "[REDACTED]"


def issue(code, severity, message, related_ref=None):
    return {"code": code, "severity": severity, "message": message,
            "related_ref": related_ref}


def _luhn_ok(digits):
    """Card numbers pass the Luhn checksum; random digit runs usually don't."""
    total, alt = 0, False
    for d in reversed(digits):
        n = int(d)
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        alt = not alt
    return total % 10 == 0


def find_sensitive_numbers(text):
    """Return a list of (kind, matched_text) for SSN, card and bank-routing-like numbers."""
    found = [("ssn", m.group()) for m in SSN_RE.finditer(text)]
    for m in CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            found.append(("card", m.group()))
    found += [("bank_routing", m.group()) for m in ROUTING_RE.finditer(text)]
    return found


# ---------------------------------------------------------------- S0
def mask_user_text(text):
    """S0: before any agent call, replace SSN/card/routing-like numbers in user text.

    Returns (masked_text, issues). The original text is never passed on.
    """
    masked, issues = text, []
    for kind, value in find_sensitive_numbers(text):
        masked = masked.replace(value, REDACTED)
        issues.append(issue("PII_MASKED", "warning",
                            f"A {kind.replace('_', ' ')} number was removed from user text"))
    return masked, issues


# ---------------------------------------------------------------- helpers
def _walk(obj, path=""):
    """Yield (path, key, value, parent_key) for every key in nested dicts/lists."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            yield p, k, v
            yield from _walk(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


# ---------------------------------------------------------------- S1
def s1_schema(result):
    if not isinstance(result, dict):
        return [issue("SCHEMA_INVALID", "critical", "Result is not a JSON object")]
    out = [issue("SCHEMA_INVALID", "critical", f"Missing field: {f}", f)
           for f in C.RESULT_FIELDS if f not in result]
    types = {"result": dict, "issues": list, "clarification_requests": list,
             "evidence_refs": list, "is_mock": bool, "case_version": int}
    for f, t in types.items():
        if f in result and not isinstance(result[f], t):
            out.append(issue("SCHEMA_INVALID", "critical",
                             f"Field {f} must be {t.__name__}", f))
    if result.get("schema_version") not in (None, C.SCHEMA_VERSION):
        out.append(issue("SCHEMA_VERSION", "warning",
                         f"schema_version is {result.get('schema_version')!r}, expected {C.SCHEMA_VERSION!r}",
                         "schema_version"))
    return out


# ---------------------------------------------------------------- S1 (per-role result fields)
def s1_result_fields(request, result):
    """S1 extension: per-role, per-task_type result field checks.

    Reads role_id and task_type from the REQUEST (not the result — agent_id
    is not trusted until S2).  Only called when s1_schema found no critical
    issue and status is not 'failed'.
    Fails closed: if there is no entry for this (role_id, task_type) pair,
    returns one critical SCHEMA_INVALID so the result is rejected.
    Never raises.
    """
    role = request.get("role_id")
    task = request.get("task_type")
    entry = C.RESULT_REQUIRED.get(role, {}).get(task)
    if entry is None:
        return [issue("SCHEMA_INVALID", "critical",
                      f"no result rules for {role}/{task}", None)]
    res = result.get("result", {})
    out = []
    # 1. Required top-level result keys (and list-type check in the same pass)
    for key in entry.get("result", []):
        if key not in res:
            out.append(issue("SCHEMA_INVALID", "critical",
                             f"result.{key} is missing", key))
        elif key in entry.get("lists", []) and not isinstance(res[key], list):
            out.append(issue("SCHEMA_INVALID", "critical",
                             f"result.{key} must be a list", key))
    # 2. Required item keys within each list
    for list_key, item_keys in entry.items():
        if list_key in ("result", "lists"):
            continue
        items = res.get(list_key)
        if not isinstance(items, list):
            continue   # wrong container type already reported above; skip items
        for i, item in enumerate(items):
            ref_prefix = f"{list_key}[{i}]"
            if not isinstance(item, dict):
                out.append(issue("SCHEMA_INVALID", "critical",
                                 f"{ref_prefix} must be an object", ref_prefix))
                continue
            for k in item_keys:
                if k not in item:
                    out.append(issue("SCHEMA_INVALID", "critical",
                                     f"{ref_prefix}.{k} is missing",
                                     f"{ref_prefix}.{k}"))
    return out


# ---------------------------------------------------------------- S2
def s2_identity(request, result):
    out = [issue("IDENTITY_MISMATCH", "critical",
                 f"{f} is {result.get(f)!r}, request has {request.get(f)!r}", f)
           for f in C.ECHO_FIELDS if result.get(f) != request.get(f)]
    if result.get("agent_id") != request.get("role_id"):
        out.append(issue("IDENTITY_MISMATCH", "critical",
                         f"agent_id {result.get('agent_id')!r} does not match role_id {request.get('role_id')!r}",
                         "agent_id"))
    return out


# ---------------------------------------------------------------- S3
def s3_stale(result, current_case_version):
    if result.get("case_version") != current_case_version:
        return [issue("STALE_RESULT", "critical",
                      f"case_version {result.get('case_version')} is not the current {current_case_version}",
                      "case_version")]
    return []


# ---------------------------------------------------------------- S4
def s4_enums(result):
    out = []
    for path, key, value in _walk(result):
        if key not in C.ENUMS or not isinstance(value, str):
            continue
        only_in = C.ENUM_ONLY_IN.get(key)
        if only_in and not any(part in path for part in only_in):
            continue
        if value not in C.ENUMS[key]:
            out.append(issue("UNKNOWN_ENUM", "critical",
                             f"{path} = {value!r} is not an allowed {key}", path))
    return out


# ---------------------------------------------------------------- S5
def s5_references(result, known):
    """known = {"need_id": set(), "program_id": set(), "evidence_id": set()}.

    Only the kinds supplied are checked. program_id may be null (contract 4.6, 4.8).
    """
    out = []
    ref_keys = {
        "need_id": "need_id", "need_ids": "need_id", "matched_need_ids": "need_id",
        "related_need_ids": "need_id",
        "program_id": "program_id",
        "evidence_refs": "evidence_id", "source_refs": "evidence_id",
    }
    for path, key, value in _walk(result.get("result", {})):
        kind = ref_keys.get(key)
        if kind is None or kind not in known:
            continue
        values = value if isinstance(value, list) else [value]
        for v in values:
            if v is None:
                continue
            if v not in known[kind]:
                out.append(issue("UNKNOWN_REFERENCE", "critical",
                                 f"{path} refers to unknown {kind} {v!r}", path))
    return out


# ---------------------------------------------------------------- S6
def s6_failed(result):
    if result.get("status") == "failed":
        return [issue("AGENT_FAILED", "critical",
                      "Agent reported failed; dependents must not be marked completed")]
    return []


# ---------------------------------------------------------------- S7 (used by the runner)
def s7_timeout(seconds_taken):
    if seconds_taken is None or seconds_taken > C.TIMEOUT_SECONDS:
        return [issue("TIMEOUT", "critical",
                      f"No result within {C.TIMEOUT_SECONDS} seconds")]
    return []


# ---------------------------------------------------------------- S8
def s8_mock(result):
    if result.get("is_mock") is True:
        return [issue("MOCK_COMPONENT", "info", "Result comes from a mock component")]
    return []


# ---------------------------------------------------------------- S9
def s9_privacy(result):
    out = []
    for path, key, _ in _walk(result):
        if key.lower() in C.FORBIDDEN_FIELDS:
            out.append(issue("PRIVACY_VIOLATION", "critical",
                             f"Forbidden field {path}", path))
    for text in _strings(result):
        for kind, value in find_sensitive_numbers(text):
            out.append(issue("PRIVACY_VIOLATION", "critical",
                             f"Text contains a {kind.replace('_', ' ')}-like number"))
    return out


# ---------------------------------------------------------------- all together
def check_result(request, result, current_case_version, known=None, seconds_taken=0.0):
    """Run S1–S9 on one result. Returns (accepted: bool, issues: list)."""
    issues = s1_schema(result)
    if any(i["severity"] == "critical" for i in issues):
        return False, issues            # can't trust the rest of the envelope
    # S1 extension: per-role result fields (FIX 5); a failed result carries result {}
    if result.get("status") != "failed":
        issues += s1_result_fields(request, result)
    if any(i["severity"] == "critical" for i in issues):
        return False, issues
    issues += s2_identity(request, result)
    issues += s3_stale(result, current_case_version)
    issues += s4_enums(result)
    issues += s5_references(result, known or {})
    issues += s6_failed(result)
    issues += s7_timeout(seconds_taken)
    issues += s8_mock(result)
    issues += s9_privacy(result)
    accepted = not any(i["severity"] == "critical" for i in issues)
    return accepted, issues
