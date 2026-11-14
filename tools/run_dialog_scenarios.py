#!/usr/bin/env python3
"""Run the Supervisor dialog-mode scenarios end to end on the team's agents and check the answers.

Team tool (Supervisor v0.2.5). Standard library only. Two modes, same scenarios and checks:
  HTTP (server already running: python -m navigator.supervisor.http_api --agents agents.json --no-isolate):
    python -I tools/run_dialog_scenarios.py --base-url http://127.0.0.1:8765 --out docs/examples/dialog
  Direct import (no server), from the repository root:
    python -I tools/run_dialog_scenarios.py --repo . --agents agents.json --out OUT_DIR [--no-isolate]
Options: --only J,B  --ref-date 2026-11-14  --timeout 120  --no-errors

The user's answers are chosen by the question's fact_key (the dialog is adaptive, so the order
of questions is not fixed). A question the scenario has no answer for is skipped when it can be
skipped, otherwise answered "I'm not sure." and listed as UNPLANNED (not a failure).
Every request and response is saved in OUT_DIR as a real example, with RESULTS.md (a table of
measured results) and SUMMARY.json. The stories are made up; 123-45-6789 is a made-up test number
used to check that such numbers never come back. Exit code 1 if any check FAILs.
"""
import argparse
import json
import os
import platform
import sys
import time
import urllib.error
import urllib.request

DIALOG_VERSION = "0.2"
SKIP = object()
SSN = "123-45-6789"
GEO_SENTENCE_PART = "ZIP code"

# fact_key -> answer. A tuple key means "any of these fact keys".
SCENARIOS = {
    "J": {
        "title": "Julia: housing and food, cause and details in answers (95823)",
        "story": "I have problems with housing and food. I need help.",
        "answers": {
            ("triggering_circumstances", "triggering_events", "employment_status"):
                "My hours were cut at work last month and I couldn't pay rent.",
            "zip_code": "95823",
            "household_gross_monthly_income": "About $800 a month.",
            "household_size": "There are 3 people in our household.",
        },
        "expect": {"completed": True, "cards_min": 1, "needs": ["food_assistance", "housing_assistance"]},
    },
    "J660": {
        "title": "Julia, ZIP 95660 (North Highlands, Sacramento County)",
        "story": "I have problems with housing and food. I need help.",
        "answers": {
            ("triggering_circumstances", "triggering_events", "employment_status"):
                "My hours were cut at work last month and I couldn't pay rent.",
            "zip_code": "95660",
            "household_gross_monthly_income": "About $800 a month.",
            "household_size": "There are 3 people in our household.",
        },
        "expect": {"completed": True, "cards_min": 1, "needs": ["food_assistance", "housing_assistance"],
                   "no_issue": ["COUNTY_UNKNOWN"]},
    },
    "A": {
        "title": "A: vague hardship, cause asked first (Yogesh SC-E2E-A)",
        "story": ("Hi, I need help with food and rent. I'm having financial problems and I'm worried "
                  "about how my family will get through next month."),
        "answers": {
            ("triggering_circumstances", "triggering_events", "employment_status"):
                ("My company cut my hours from 40 to 15 hours a week starting two weeks ago, "
                 "so my paycheck dropped drastically."),
            "zip_code": "We are in 95823.",
            "household_gross_monthly_income": "Our monthly income is $900.",
            "rent_amount_monthly": "Our monthly rent is $1,350.",
            "cash_on_hand_approx": "I have about $150 left in my account.",
            "household_size": "There are 3 people in our family.",
        },
        "expect": {"completed": True, "cards_min": 1, "first_fact_key": "triggering_circumstances",
                   "needs": ["food_assistance", "housing_assistance"]},
    },
    "B": {
        "title": "B: 3-day notice and lockout threat (Yogesh SC-E2E-B)",
        "story": ("My landlord gave me a 3-day notice to pay or quit yesterday and threatened to lock "
                  "us out if we don't leave."),
        "answers": {
            "eviction_notice_type": "It's a 3-day notice to pay or quit.",
            "eviction_notice_date": "The notice date is November 6, 2026.",
            ("rent_arrears_amount", "rent_amount_monthly"): "The amount due is $1,600.",
            "zip_code": "We live in 95823.",
            "household_gross_monthly_income": "Our income is $1,000.",
        },
        # Julia, Nov 11: a lockout threat is a housing and legal issue, not a safety notice.
        "expect": {"completed": True, "cards_min": 1, "needs": ["housing_assistance"], "no_safety_notice": True},
    },
    "C": {
        "title": "C: medical emergency, food need only in an answer (Yogesh SC-E2E-C, CR-014)",
        "story": ("I was doing okay until my daughter had an emergency asthma hospitalization last week, "
                  "and now the hospital bill took all my rent money."),
        "answers": {
            "household_gross_monthly_income": ("Our income is $1,200. Rent is $1,200 due on November 1st, "
                                               "and we have no groceries left for the kids."),
            "zip_code": "Our ZIP is 95823.",
            "household_size": "There are 3 people in our household.",
        },
        # food_assistance appears only via CR-014 proposed_needs: a WARN, not a FAIL, if missing.
        "expect": {"completed": True, "cards_min": 1, "needs": ["housing_assistance", "medical_health_coverage"],
                   "soft_needs": ["food_assistance"]},
    },
    "D": {
        "title": "D: income not answered (Yogesh D_income_retry_when_unanswered)",
        "story": "I lost my job yesterday and need help with rent.",
        "answers": {
            "zip_code": "I live in ZIP 95823.",
            "household_gross_monthly_income": "I'm not sure what our income is right now.",
        },
        "expect": {"completed": True, "needs": ["housing_assistance"]},
    },
    "SKIPZIP": {
        "title": "Julia story, the user skips the ZIP (limitation, not a stop)",
        "story": "I have problems with housing and food. I need help.",
        "answers": {
            ("triggering_circumstances", "triggering_events", "employment_status"):
                "My hours were cut at work last month and I couldn't pay rent.",
            "zip_code": SKIP,
            "household_gross_monthly_income": "About $800 a month.",
            "household_size": "There are 3 people in our household.",
        },
        "expect": {"completed": True, "zip_skipped": True, "issue": ["GEOGRAPHY_MISSING"], "zip_gap_note": True},
    },
    "EDIT": {
        "title": "Julia story; at the summary: remove housing, add utility (with an SSN-like number)",
        "story": "I have problems with housing and food. I need help.",
        "answers": {
            ("triggering_circumstances", "triggering_events", "employment_status"):
                "My hours were cut at work last month and I couldn't pay rent.",
            "zip_code": "95823",
            "household_gross_monthly_income": "About $800 a month.",
            "household_size": "3",
        },
        "confirm": {
            "corrections": {"household_gross_monthly_income": 1500},
            "reject_categories": ["housing_assistance"],
            "added_needs": [{"category": "utility_assistance",
                             "description": "My electric bill is overdue. My SSN is " + SSN + "."}],
        },
        "expect": {"completed": True, "rejected": ["housing_assistance"], "needs": ["utility_assistance"],
                   "no_text": [SSN]},
    },
    "PII": {
        "title": "An SSN-like number in an answer never comes back",
        "story": "I have problems with housing and food. I need help.",
        "answers": {
            ("triggering_circumstances", "triggering_events", "employment_status"):
                "My hours were cut at work. My SSN is " + SSN + ".",
            "zip_code": "95823",
            "household_gross_monthly_income": "About $800 a month.",
            "household_size": "3",
        },
        "expect": {"completed": True, "no_text": [SSN]},
    },
    "LOCKOUT": {
        "title": "Already locked out: housing and legal help, no crisis notice (Julia, Nov 11)",
        "story": ("My landlord changed the locks yesterday and locked us out of our apartment. "
                  "We have nowhere to stay and no food."),
        "answers": {
            ("triggering_circumstances", "triggering_events", "employment_status"):
                "My hours were cut at work last month and I couldn't pay rent.",
            "zip_code": "95823",
            "household_gross_monthly_income": "About $800 a month.",
            "household_size": "3",
        },
        "expect": {"completed": True, "cards_min": 1, "needs": ["housing_assistance"], "no_safety_notice": True,
                   "soft_text": ["police non-emergency"]},
    },
    "THREAT": {
        "title": "A threat of violence in the story: the safety notice with verified 9-1-1 and 988",
        "story": ("My ex-partner said he will hurt me and the kids if I don't leave the apartment. "
                  "I need help with housing."),
        "answers": {
            ("triggering_circumstances", "triggering_events", "employment_status"): "I am afraid to go back home.",
            "zip_code": "95823",
            "household_gross_monthly_income": "About $1,000 a month.",
            "household_size": "3",
        },
        "expect": {"completed": True, "safety_notice": True},
    },
}
LOOP_GUARD_TURNS = 8


# ---------- transport ----------

class Http:
    def __init__(self, base, timeout):
        self.base, self.timeout = base.rstrip("/"), timeout

    def raw(self, method, path, data=None):
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            with e:                  # close the error response (Python 3.15 warns otherwise)
                return e.code, e.read().decode("utf-8", "replace")

    def call(self, name, body):
        code, text = self.raw("POST", "/" + name, json.dumps(body).encode("utf-8"))
        try:
            return code, json.loads(text)
        except ValueError:
            return code, {"_not_json": text[:300]}


class Direct:
    def __init__(self, repo, agents_path, isolate):
        sys.path.insert(0, os.path.abspath(repo))
        from navigator.supervisor import dialog
        from navigator.supervisor.run import load_agents
        self.d = dialog
        self.agents = load_agents(agents_path)
        self.isolate = isolate

    def call(self, name, body):
        kw = dict(body)
        kw["agents"], kw["isolate"] = self.agents, self.isolate
        if name == "start":
            return 200, self.d.start(**kw)
        if name == "answer":
            return 200, self.d.answer(**kw)
        return 200, self.d.confirm(**kw)


# ---------- helpers ----------

class Report:
    def __init__(self):
        self.rows = []

    def add(self, scen, level, text):
        self.rows.append((scen, level, text))
        print(f"  [{level}] {text}")

    def failed(self):
        return any(r[1] == "FAIL" for r in self.rows)


def save(out, name, obj):
    with open(os.path.join(out, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def pick_answer(answers, fact_key):
    for k, v in answers.items():
        keys = k if isinstance(k, tuple) else (k,)
        if fact_key in keys:
            return v
    return None


def needs_of(resp):
    s = resp.get("summary") or {}
    return [n.get("category") for n in s.get("needs", [])]


def check_common(rep, scen, resp, prev_version):
    if resp.get("dialog_version") != DIALOG_VERSION:
        rep.add(scen, "FAIL", f"dialog_version is {resp.get('dialog_version')!r}, expected {DIALOG_VERSION!r}")
    for key in ("status", "case_id", "case_version", "case", "questions", "limitations", "issues"):
        if key not in resp:
            rep.add(scen, "FAIL", f"response has no '{key}'")
    if not isinstance(resp.get("limitations", []), list):
        rep.add(scen, "FAIL", "limitations is not a list")
    cv = resp.get("case_version")
    if prev_version is not None and isinstance(cv, int) and cv < prev_version:
        rep.add(scen, "FAIL", f"case_version went down: {prev_version} -> {cv}")
    if "Traceback" in json.dumps(resp):
        rep.add(scen, "FAIL", "a traceback is in the response")
    return cv


# ---------- one scenario ----------

def run_scenario(t, key, sc, out, ref_date, rep, metrics):
    print(f"\n=== {sc['title'] if sc['title'].startswith(key + ':') else key + ': ' + sc['title']}")
    exp = sc["expect"]
    texts = []                       # every response, for the 'no_text' check
    asked = []                       # fact keys in the order asked
    step = 0
    m = metrics[key] = {"title": sc["title"], "calls": 0, "seconds": 0.0, "max_call": 0.0}

    def send(name, body):
        nonlocal step
        step += 1
        save(out, f"{key}_{step:02d}_{name}_request.json", body)
        t0 = time.perf_counter()
        code, resp = t.call(name, body)
        dt = time.perf_counter() - t0
        m["calls"] += 1
        m["seconds"] += dt
        m["max_call"] = max(m["max_call"], dt)
        save(out, f"{key}_{step:02d}_{name}_response.json", resp)
        texts.append(json.dumps(resp, ensure_ascii=False))
        if code != 200:
            rep.add(key, "FAIL", f"/{name} returned HTTP {code}")
        return resp

    r = send("start", {"story_text": sc["story"], "ref_date": ref_date})
    ver = check_common(rep, key, r, None)
    notice = r.get("safety_notice")
    m["notice_at_start"] = bool(notice)
    if exp.get("safety_notice"):
        values = " ".join(c.get("value", "") for c in (notice or {}).get("contacts", []))
        if not notice:
            rep.add(key, "FAIL", "no safety_notice after a threat of violence in the story")
        elif "9-1-1" not in values or "988" not in values:
            rep.add(key, "FAIL", f"safety_notice contacts lack 9-1-1 or 988: {values[:120]}")
        else:
            rep.add(key, "PASS", "safety_notice with verified 9-1-1 and 988 at the first response")
    turns = 0
    while r.get("status") == "needs_clarification":
        turns += 1
        qs = r.get("questions") or []
        if not qs:
            rep.add(key, "FAIL", "needs_clarification with no questions")
            break
        if len(qs) > 2:
            rep.add(key, "FAIL", f"turn {turns}: {len(qs)} questions (max 2)")
        items = []
        for q in qs:
            fk = q.get("fact_key")
            for f in ("question_id", "fact_key", "text", "can_skip", "necessity_level", "reason"):
                if f not in q:
                    rep.add(key, "FAIL", f"question without '{f}'")
            if fk in asked:
                rep.add(key, "FAIL", f"question repeated: {fk}")
            asked.append(fk)
            a = pick_answer(sc["answers"], fk)
            if a is SKIP or (a is None and q.get("can_skip")):
                if a is None:
                    rep.add(key, "UNPLANNED", f"no answer planned for '{fk}': skipped")
                items.append({"question_id": q["question_id"], "skipped": True})
            else:
                if a is None:
                    rep.add(key, "UNPLANNED", f"no answer planned for required '{fk}': \"I'm not sure.\"")
                    a = "I'm not sure."
                items.append({"question_id": q["question_id"], "answer_text": a})
            print(f"  Q{turns} {fk}: {q.get('text')!r} -> {items[-1].get('answer_text', 'SKIP')!r}")
        r = send("answer", {"case": r["case"], "answers": items})
        ver = check_common(rep, key, r, ver)
        if turns > LOOP_GUARD_TURNS + 1:
            rep.add(key, "FAIL", "dialog did not stop after the loop guard")
            break

    rep.add(key, "INFO", f"{turns} question turn(s); asked: {', '.join(map(str, asked)) or 'none'}")
    m["turns"], m["asked"] = turns, list(asked)
    if exp.get("first_fact_key") and (not asked or asked[0] != exp["first_fact_key"]):
        rep.add(key, "FAIL", f"first question was {asked[:1]}, expected {exp['first_fact_key']}")
    if r.get("status") != "needs_confirmation":
        rep.add(key, "FAIL", f"expected needs_confirmation, got {r.get('status')}: "
                             f"{[i.get('code') for i in r.get('issues', [])]}")
        return
    fact_fields = [f.get("field") for f in (r.get("summary") or {}).get("facts", [])]
    if "zip_code" not in asked and "zip_code" not in fact_fields:
        rep.add(key, "FAIL", "the ZIP was never asked and is not a fact (geography guard)")
    summary_needs = needs_of(r)
    rep.add(key, "INFO", f"summary needs: {summary_needs}")
    for c in exp.get("needs", []):
        if c not in summary_needs and c not in [x["category"] for x in sc.get("confirm", {}).get("added_needs", [])]:
            rep.add(key, "FAIL", f"need {c} missing in the summary")
    for c in exp.get("soft_needs", []):
        if c not in summary_needs:
            rep.add(key, "WARN", f"need {c} not proposed from the answers (CR-014 in Agent 1?)")
    unknown = [u.get("field") for u in (r.get("summary") or {}).get("unknown", [])]
    if unknown:
        rep.add(key, "INFO", f"unknown: {unknown}")

    cf = sc.get("confirm", {})
    body = {"case": r["case"]}
    if cf.get("corrections"):
        body["corrections"] = cf["corrections"]
    if cf.get("reject_categories"):
        ids = [n["need_id"] for n in r["summary"]["needs"] if n.get("category") in cf["reject_categories"]]
        body["rejected_need_ids"] = ids
    if cf.get("added_needs"):
        body["added_needs"] = cf["added_needs"]
    r = send("confirm", body)
    check_common(rep, key, r, ver)

    st = r.get("status")
    codes = [i.get("code") for i in r.get("issues", [])]
    if exp.get("completed") and st != "completed":
        rep.add(key, "FAIL", f"expected completed, got {st}: {codes}")
        return
    cards = (r.get("plan") or {}).get("action_cards", [])
    withheld = (r.get("plan") or {}).get("withheld_card_ids", [])
    rows = r.get("plan_by_need") or []
    verdict = (r.get("final_validation") or {}).get("verdict")
    rep.add(key, "INFO", f"cards: {len(cards)} released, {len(withheld)} withheld; "
                         f"verdict {verdict}; issues {codes}")
    m.update({"needs": [row.get("label") for row in rows], "cards": len(cards), "withheld": len(withheld),
              "with_sources": sum(1 for c in cards if c.get("source_refs")), "verdict": verdict,
              "notice": bool(r.get("safety_notice")), "limitations": len(r.get("limitations") or []),
              "status": st})
    if any(not c.get("source_refs") for c in cards):
        rep.add(key, "FAIL", "a released card has no source_refs")
    if len(cards) < exp.get("cards_min", 0):
        rep.add(key, "FAIL", f"{len(cards)} cards, expected at least {exp['cards_min']}")
    # plan_by_need follows the plan's own order, never sorted by urgency (Julia, Nov 11)
    first_pos = []
    for row in rows:
        pos = [i for i, c in enumerate(cards) if c.get("card_id") in row.get("card_ids", [])]
        first_pos.append(min(pos) if pos else 10 ** 6)
    if first_pos != sorted(first_pos):
        rep.add(key, "FAIL", "plan_by_need rows are not in the plan's action order")
    for c in exp.get("needs", []):
        if c not in [row.get("category") for row in rows]:
            rep.add(key, "FAIL", f"need {c} has no plan_by_need row")
    for c in exp.get("rejected", []):
        if c not in [x.get("category") for x in r.get("rejected_needs", [])]:
            rep.add(key, "FAIL", f"rejected need {c} not listed in rejected_needs")
        if c in [row.get("category") for row in rows]:
            rep.add(key, "FAIL", f"rejected need {c} is still planned")
    lim = r.get("limitations") or []
    if exp.get("zip_skipped"):
        if not any(GEO_SENTENCE_PART in s for s in lim):
            rep.add(key, "FAIL", "ZIP skipped but no limitation sentence")
    elif lim:
        rep.add(key, "WARN", f"limitations not expected: {lim}")
    for c in exp.get("issue", []):
        if c not in codes:
            rep.add(key, "FAIL", f"issue {c} expected")
    for c in exp.get("no_issue", []):
        if c in codes:
            rep.add(key, "FAIL", f"issue {c} not expected")
    if exp.get("no_safety_notice") and (r.get("safety_notice") or m.get("notice_at_start")):
        rep.add(key, "FAIL", "safety_notice shown for a housing and legal case")
    if exp.get("zip_gap_note"):
        empty = [row for row in rows if not row.get("card_ids")]
        bad = [row.get("label") for row in empty if not (row.get("gap_notes") or [""])[0].count("ZIP code")]
        if bad:
            rep.add(key, "FAIL", f"needs with no card do not name the skipped ZIP first: {bad}")
        elif empty:
            rep.add(key, "PASS", f"{len(empty)} need(s) with no card name the skipped ZIP first")
    for txt in exp.get("soft_text", []):
        if not any(txt in s for s in texts[-1:]):
            rep.add(key, "WARN", f"the plan does not contain {txt!r} yet")
    for txt in exp.get("no_text", []):
        if any(txt in s for s in texts):
            rep.add(key, "FAIL", f"the text {txt!r} came back in a response")


# ---------- error cases ----------

def run_errors(t, out, ref_date, rep):
    key = "ERR"
    print("\n=== ERR: wrong calls (never a traceback)")
    code, r = t.call("start", {"story_text": "I have problems with housing and food. I need help.",
                               "ref_date": ref_date})
    if r.get("status") != "needs_clarification":
        rep.add(key, "WARN", f"start gave {r.get('status')}; stage checks below may not apply")
    case = r.get("case")

    code, r2 = t.call("confirm", {"case": case})
    save(out, "ERR_confirm_while_clarifying.json", r2)
    codes = [i.get("code") for i in r2.get("issues", [])]
    rep.add(key, "PASS" if "WRONG_STAGE" in codes else "FAIL", f"confirm while clarifying -> {codes}")

    code, r3 = t.call("answer", {"case": {"case_id": "x"}, "answers": []})
    save(out, "ERR_broken_case.json", r3)
    codes = [i.get("code") for i in r3.get("issues", [])]
    rep.add(key, "PASS" if "CASE_INVALID" in codes else "FAIL", f"broken case -> {codes}")

    if case and r.get("questions"):
        code, r4 = t.call("answer", {"case": case, "answers": [{"question_id": "q9-9", "answer_text": "x"}]})
        save(out, "ERR_unknown_question.json", r4)
        codes = [i.get("code") for i in r4.get("issues", [])]
        rep.add(key, "PASS" if "UNKNOWN_QUESTION_ID" in codes else "FAIL", f"unknown question_id -> {codes}")

    if not isinstance(t, Http):
        return
    code, text = t.raw("GET", "/health")
    ok = code == 200 and json.loads(text).get("dialog_version") == DIALOG_VERSION
    rep.add(key, "PASS" if ok else "FAIL", f"GET /health -> {code} {text[:80]}")
    code, text = t.raw("POST", "/start", b"{not json")
    rep.add(key, "PASS" if code == 400 and "Traceback" not in text else "FAIL", f"bad JSON -> {code}")
    code, text = t.raw("POST", "/nowhere", b"{}")
    rep.add(key, "PASS" if code == 404 else "FAIL", f"unknown path -> {code}")
    big = json.dumps({"story_text": "x" * (70 * 1024)}).encode("utf-8")
    code, text = t.raw("POST", "/start", big)
    rep.add(key, "PASS" if code == 413 else "FAIL", f"70 KB body -> {code}")


def write_results(out, metrics, rep, ref_date, mode):
    """RESULTS.md: one row per scenario, measured on this run (no estimates)."""
    lines = ["# Dialog mode: results on the team's agents", "",
             f"Run: {time.strftime('%Y-%m-%d %H:%M')} local time; reference date {ref_date}; {mode}; "
             f"Python {platform.python_version()}, {platform.system()}.",
             "Every request and response of this run is in this folder (`<scenario>_<step>_<call>_request.json` / "
             "`_response.json`). The stories are made up.", "",
             "| Scenario | Question turns | Calls | Total s | Slowest call s | Needs in the plan | Cards | "
             "Cards with sources | Withheld | Agent 10 | Safety notice | Checks |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, m in metrics.items():
        rows = [r for r in rep.rows if r[0] == key]
        fails = sum(1 for r in rows if r[1] == "FAIL")
        warns = sum(1 for r in rows if r[1] == "WARN")
        checks = "FAIL " + str(fails) if fails else ("ok, " + str(warns) + " warning(s)" if warns else "ok")
        notice = "yes" if (m.get("notice") or m.get("notice_at_start")) else "no"
        name = m["title"] if m["title"].startswith(key + ":") else f"{key}: {m['title']}"
        lines.append(f"| {name} | {m.get('turns', '-')} | {m['calls']} | {m['seconds']:.2f} | "
                     f"{m['max_call']:.2f} | {', '.join(m.get('needs') or []) or '-'} | {m.get('cards', '-')} | "
                     f"{m.get('with_sources', '-')} | {m.get('withheld', '-')} | {m.get('verdict') or '-'} | "
                     f"{notice} | {checks} |")
    err = [r for r in rep.rows if r[0] == "ERR"]
    if err:
        lines += ["", "Wrong calls (must fail cleanly, never a traceback):", ""]
        lines += [f"- {r[1]}: {r[2]}" for r in err]
    notes = [r for r in rep.rows if r[1] in ("FAIL", "WARN", "UNPLANNED")]
    lines += ["", "## Findings", ""] + ([f"- {s} {l}: {x}" for s, l, x in notes] or ["- none"])
    with open(os.path.join(out, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base-url")
    ap.add_argument("--repo")
    ap.add_argument("--agents", default="agents.json")
    ap.add_argument("--no-isolate", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only")
    ap.add_argument("--ref-date", default="2026-11-14")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--no-errors", action="store_true")
    a = ap.parse_args(argv)
    if bool(a.base_url) == bool(a.repo):
        ap.error("give exactly one of --base-url or --repo")
    os.makedirs(a.out, exist_ok=True)
    t = Http(a.base_url, a.timeout) if a.base_url else Direct(a.repo, a.agents, not a.no_isolate)
    keys = a.only.split(",") if a.only else list(SCENARIOS)
    unknown = [k for k in keys if k not in SCENARIOS]
    if unknown:
        ap.error(f"unknown scenario(s): {unknown}; known: {list(SCENARIOS)}")
    rep = Report()
    metrics = {}
    for k in keys:
        try:
            run_scenario(t, k, SCENARIOS[k], a.out, a.ref_date, rep, metrics)
        except Exception as e:  # the tool must report, not stop
            rep.add(k, "FAIL", f"the script stopped: {type(e).__name__}: {e}")
    if not a.no_errors:
        try:
            run_errors(t, a.out, a.ref_date, rep)
        except Exception as e:
            rep.add("ERR", "FAIL", f"the script stopped: {type(e).__name__}: {e}")
    save(a.out, "SUMMARY.json", [{"scenario": s, "level": l, "text": x} for s, l, x in rep.rows])
    mode = (f"HTTP {a.base_url}" if a.base_url else
            f"direct import, {'agents in this process' if a.no_isolate else 'one process per agent call'}")
    write_results(a.out, metrics, rep, a.ref_date, mode)
    print("\n=== SUMMARY")
    for level in ("FAIL", "WARN", "UNPLANNED"):
        rows = [r for r in rep.rows if r[1] == level]
        print(f"{level}: {len(rows)}")
        for s, _, x in rows:
            print(f"  {s}: {x}")
    return 1 if rep.failed() else 0


if __name__ == "__main__":
    sys.exit(main())
