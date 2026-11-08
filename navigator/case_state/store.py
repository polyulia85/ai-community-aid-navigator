"""Case State store v0.1 (owner: Silver). Plain Python 3.11+, sqlite3 only, path-independent
(works inside Orchestrate or an external app; only the database file location differs).

Rules: every change bumps case_version and is logged in `events` (append-only); facts are never edited in place
(an update supersedes the old row); agents never write user progress; no forbidden personal fields.
Times are passed in by the caller (the Supervisor's reference clock) so tests never depend on today's date."""
import json
import os
import sqlite3

SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
# Mirrors the Supervisor's privacy check (S9): never stored as a fact.
FORBIDDEN_FIELDS = {"ssn", "social_security_number", "date_of_birth", "dob", "birth_date", "id_number",
                    "drivers_license", "bank_account", "account_number", "routing_number", "card_number"}
# User-controlled card progress (Julia, Nov 3). PROPOSED until the Plan / My case screens are final.
PROGRESS_STATUSES = ("not_started", "in_progress", "waiting", "completed", "need_help")


class CaseStateError(ValueError):
    pass


def connect(path=":memory:"):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    with open(SCHEMA, encoding="utf-8") as f:
        db.executescript(f.read())
    return db


def _log(db, case_id, at, actor, event_type, version, details=None):
    db.execute("INSERT INTO events (case_id, at, actor, event_type, case_version, details_json) VALUES (?,?,?,?,?,?)",
               (case_id, at, actor, event_type, version, json.dumps(details or {}, sort_keys=True)))


def _version(db, case_id):
    row = db.execute("SELECT current_version FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if row is None:
        raise CaseStateError(f"unknown case_id {case_id}")
    return row["current_version"]


def _bump(db, case_id, at):
    v = _version(db, case_id) + 1
    db.execute("UPDATE cases SET current_version = ?, updated_at = ? WHERE case_id = ?", (v, at, case_id))
    return v


def create_case(db, case_id, at, locale="en-US", account_id=None):
    with db:
        db.execute("INSERT INTO cases (case_id, created_at, updated_at, locale, account_id) VALUES (?,?,?,?,?)",
                   (case_id, at, at, locale, account_id))
        _log(db, case_id, at, "user", "case_created", 1)
    return 1


def add_facts(db, case_id, facts, at, actor="supervisor"):
    """Adds CaseFact dicts (contracts 3.2). A fact_id already present is superseded, never overwritten.
    Returns the new case_version."""
    for f in facts:
        if f["field"].lower() in FORBIDDEN_FIELDS:
            raise CaseStateError(f"forbidden personal field: {f['field']}")
    with db:
        v = _bump(db, case_id, at)
        for f in facts:
            db.execute("UPDATE case_facts SET confirmation_status = 'superseded' WHERE case_id = ? AND fact_id = ? "
                       "AND confirmation_status != 'superseded'", (case_id, f["fact_id"]))
            db.execute("INSERT INTO case_facts (case_id, case_version, fact_id, field, value_json, confirmation_status, "
                       "source, time_context, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                       (case_id, v, f["fact_id"], f["field"], None if f.get("value") is None else json.dumps(f["value"]),
                        f["confirmation_status"], f.get("source", "user_statement"), f.get("time_context"), at))
        _log(db, case_id, at, actor, "facts_added", v, {"fact_ids": [f["fact_id"] for f in facts]})
    return v


def current_facts(db, case_id):
    rows = db.execute("SELECT * FROM case_facts WHERE case_id = ? AND confirmation_status != 'superseded' "
                      "ORDER BY fact_id", (case_id,)).fetchall()
    return [{"fact_id": r["fact_id"], "field": r["field"],
             "value": None if r["value_json"] is None else json.loads(r["value_json"]),
             "confirmation_status": r["confirmation_status"], "source": r["source"],
             "time_context": r["time_context"]} for r in rows]


def save_needs(db, case_id, needs, at, actor="supervisor"):
    """Stores Need dicts (contracts 3.1) for a new case_version."""
    with db:
        v = _bump(db, case_id, at)
        for n in needs:
            db.execute("INSERT INTO needs (case_id, case_version, need_id, category, subcategory, description, "
                       "original_quote, confirmation_status, urgency, urgency_reason, user_priority) "
                       "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (case_id, v, n["need_id"], n["category"], n.get("subcategory"), n["description"],
                        n.get("original_quote"), n["confirmation_status"], n["urgency"], n.get("urgency_reason"),
                        n.get("user_priority")))
        _log(db, case_id, at, actor, "needs_saved", v, {"need_ids": [n["need_id"] for n in needs]})
    return v


def record_clarification(db, case_id, fact_key, question, at, answer=None, answered_at=None, skipped=False):
    with db:
        v = _version(db, case_id)
        db.execute("INSERT INTO clarifications (case_id, case_version, fact_key, question, asked_at, answer_json, "
                   "answered_at, skipped) VALUES (?,?,?,?,?,?,?,?)",
                   (case_id, v, fact_key, question, at, None if answer is None else json.dumps(answer),
                    answered_at, int(skipped)))
        _log(db, case_id, at, "user", "clarification", v, {"fact_key": fact_key, "skipped": bool(skipped)})


def save_plan(db, case_id, plan_id, plan, verdict, released, at, need_order):
    """Stores one plan version. `need_order` is the list of (need_id, urgency) in priority order, so the
    needs layer is kept separately from the action cards (Julia, Nov 3: needs first, actions second)."""
    if verdict not in ("PASS", "FLAG"):
        raise CaseStateError("verdict must be PASS or FLAG")
    with db:
        v = _version(db, case_id)
        pv = (db.execute("SELECT COALESCE(MAX(plan_version), 0) AS m FROM plan_versions WHERE case_id = ?",
                         (case_id,)).fetchone()["m"]) + 1
        db.execute("INSERT INTO plan_versions (plan_id, case_id, case_version, plan_version, created_at, verdict, "
                   "released, plan_json) VALUES (?,?,?,?,?,?,?,?)",
                   (plan_id, case_id, v, pv, at, verdict, int(released), json.dumps(plan, sort_keys=True)))
        for rank, (need_id, urgency) in enumerate(need_order, 1):
            db.execute("INSERT INTO plan_needs (plan_id, need_id, need_rank, urgency) VALUES (?,?,?,?)",
                       (plan_id, need_id, rank, urgency))
        for c in plan.get("action_cards", []):
            db.execute("INSERT INTO action_cards (plan_id, card_id, program_id, action_title, order_group, "
                       "official_deadline, user_target_date) VALUES (?,?,?,?,?,?,?)",
                       (plan_id, c["card_id"], c.get("program_id"), c["action_title"], c.get("order_group"),
                        c.get("official_deadline"), c.get("user_target_date")))
            for nid in c.get("related_need_ids", []):
                db.execute("INSERT INTO card_needs (plan_id, card_id, need_id) VALUES (?,?,?)", (plan_id, c["card_id"], nid))
        _log(db, case_id, at, "supervisor", "plan_released" if released else "plan_withheld", v,
             {"plan_id": plan_id, "plan_version": pv, "verdict": verdict})
    return pv


def plan_by_need(db, plan_id):
    """The plan as the UI should show it: needs in priority order, each with its own cards."""
    needs = db.execute("SELECT need_id, need_rank, urgency FROM plan_needs WHERE plan_id = ? ORDER BY need_rank",
                       (plan_id,)).fetchall()
    out = []
    for n in needs:
        cards = db.execute("SELECT a.card_id, a.action_title, a.order_group, a.program_id FROM action_cards a "
                           "JOIN card_needs cn ON cn.plan_id = a.plan_id AND cn.card_id = a.card_id "
                           "WHERE a.plan_id = ? AND cn.need_id = ? ORDER BY a.card_id", (plan_id, n["need_id"])).fetchall()
        out.append({"need_id": n["need_id"], "rank": n["need_rank"], "urgency": n["urgency"],
                    "cards": [dict(c) for c in cards]})
    return out


def set_card_status(db, case_id, card_id, status, at, note=None, actor="user"):
    """User-controlled progress. Only the user may change it (agents never write progress)."""
    if actor != "user":
        raise CaseStateError("only the user can change card progress")
    if status not in PROGRESS_STATUSES:
        raise CaseStateError(f"unknown status {status}")
    with db:
        v = _version(db, case_id)
        old = db.execute("SELECT status FROM card_status WHERE case_id = ? AND card_id = ?", (case_id, card_id)).fetchone()
        db.execute("INSERT INTO card_status (case_id, card_id, status, note, updated_at) VALUES (?,?,?,?,?) "
                   "ON CONFLICT(case_id, card_id) DO UPDATE SET status = excluded.status, note = excluded.note, "
                   "updated_at = excluded.updated_at", (case_id, card_id, status, note, at))
        _log(db, case_id, at, "user", "status_changed", v,
             {"card_id": card_id, "from": old["status"] if old else None, "to": status})


def history(db, case_id):
    return [dict(r) for r in db.execute("SELECT at, actor, event_type, case_version, details_json FROM events "
                                         "WHERE case_id = ? ORDER BY event_id", (case_id,)).fetchall()]
