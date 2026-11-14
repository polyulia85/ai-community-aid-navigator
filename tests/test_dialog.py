"""Tests for dialog mode: start / answer / confirm (Supervisor v0.2.5, Session A).

Run from the repo root:  python -m unittest tests.test_dialog -v
Fake agents only; no network; uses FIXTURE_KB and FIXTURE_ZIPS.
"""
import datetime
import os
import tempfile
import unittest

from navigator.supervisor import dialog as D
from tests.fake_agents import (
    FIXTURE_KB, FIXTURE_ZIPS,
    agent_1_dialog, agent_2_dialog, agent_2_dialog_no_questions,
    agent_2_dialog_repeats_asked, agent_2_dialog_always_new,
    agent_1_dialog_with_safety, agent_8_dialog_with_gap,
    agent_1_dialog_fails_on_answer,
    agent_3_dialog, agent_4, agent_5, agent_6, agent_8, agent_10_pass,
    agent_3,
)

REF_DATE = datetime.date(2026, 11, 15)
STORY = "I have problems with housing and food. I need help."


def _agents(**overrides):
    base = {
        "agent_1": agent_1_dialog,
        "agent_2": agent_2_dialog,
        "agent_3": agent_3_dialog,
        "agent_4": agent_4,
        "agent_5": agent_5,
        "agent_6": agent_6,
        "agent_8": agent_8,
        "agent_10": agent_10_pass,
    }
    base.update(overrides)
    return base


def _start(**kw):
    kw.setdefault("ref_date", REF_DATE)
    kw.setdefault("kb_path", FIXTURE_KB)
    kw.setdefault("zips_path", FIXTURE_ZIPS)
    kw.setdefault("isolate", False)
    return D.start(STORY, **kw)


def _answer(case, answers, **kw):
    kw.setdefault("kb_path", FIXTURE_KB)
    kw.setdefault("zips_path", FIXTURE_ZIPS)
    kw.setdefault("isolate", False)
    return D.answer(case, answers, **kw)


def _confirm(case, **kw):
    kw.setdefault("kb_path", FIXTURE_KB)
    kw.setdefault("zips_path", FIXTURE_ZIPS)
    kw.setdefault("isolate", False)
    return D.confirm(case, **kw)


class TestFullDialog(unittest.TestCase):
    """Full start → answer → answer → confirm with fake agents."""

    def test_case_version_increments(self):
        """case_version goes 1 → 2 → 3 → 4 across the full dialog."""
        r1 = _start(agents=_agents())
        self.assertEqual(r1["case_version"], 1)
        self.assertEqual(r1["status"], "needs_clarification")

        # Turn 1: answer triggering_circumstances
        q1 = r1["questions"][0]
        r2 = _answer(r1["case"],
                     [{**{"question_id": q1["question_id"]}, "answer_text": "My work hours were cut"}],
                     agents=_agents())
        self.assertEqual(r2["case_version"], 2)

        # Turn 2: answer zip + income
        questions2 = r2["questions"]
        answers2 = []
        for q in questions2:
            if q["fact_key"] == "zip_code":
                answers2.append({"question_id": q["question_id"], "answer_text": "95823"})
            elif q["fact_key"] == "household_gross_monthly_income":
                answers2.append({"question_id": q["question_id"], "answer_text": "0"})
            else:
                answers2.append({"question_id": q["question_id"], "skipped": True})
        r3 = _answer(r2["case"], answers2, agents=_agents())
        self.assertEqual(r3["case_version"], 3)
        self.assertEqual(r3["status"], "needs_confirmation")

        # Confirm
        r4 = _confirm(r3["case"], agents=_agents())
        self.assertEqual(r4["case_version"], 4)
        self.assertEqual(r4["status"], "completed")

    def test_income_zero_shown_as_dollar_zero(self):
        """income 0 is kept and displayed as $0 (Julia: 0 is a real answer)."""
        r1 = _start(agents=_agents())
        q1 = r1["questions"][0]
        r2 = _answer(r1["case"],
                     [{"question_id": q1["question_id"], "answer_text": "hours cut"}],
                     agents=_agents())
        questions2 = r2["questions"]
        answers2 = []
        for q in questions2:
            if q["fact_key"] == "zip_code":
                answers2.append({"question_id": q["question_id"], "answer_text": "95823"})
            else:
                answers2.append({"question_id": q["question_id"], "answer_text": "0"})
        r3 = _answer(r2["case"], answers2, agents=_agents())
        income_fact = next(
            (f for f in r3["summary"]["facts"]
             if f["field"] == "household_gross_monthly_income"), None)
        self.assertIsNotNone(income_fact)
        self.assertEqual(income_fact["value"], 0)
        self.assertEqual(income_fact["display_value"], "$0")

    def test_agent2_receives_ambiguity_flag_in_every_turn(self):
        """Agent 2 payload carries the ambiguity flag from start in every turn."""
        received = []

        def spy2(req):
            received.append(req["payload"].get("ambiguity_flags", []))
            return agent_2_dialog(req)

        r1 = _start(agents=_agents(agent_2=spy2))
        self.assertTrue(len(received) >= 1)
        for flags in received:
            self.assertTrue(any(f.get("field") == "triggering_circumstances" for f in flags),
                            f"Flag missing from Agent 2 payload: {flags}")

    def test_same_ref_date_in_all_agent_payloads(self):
        """ref_date is the same in every payload of Agents 1, 6, 8 and 10 (the agents that take it)."""
        seen_dates = {}

        def spy(role, fn):
            def w(req):
                seen_dates.setdefault(role, set()).add(req["payload"].get("ref_date"))
                return fn(req)
            return w

        agents = _agents(
            agent_1=spy("agent_1", agent_1_dialog),
            agent_6=spy("agent_6", agent_6),
            agent_8=spy("agent_8", agent_8),
            agent_10=spy("agent_10", agent_10_pass),
        )
        r = _start(agents=agents, ref_date=REF_DATE)
        while r["status"] == "needs_clarification":
            r = _answer(r["case"], [{"question_id": q["question_id"],
                                     "answer_text": "95823" if q["fact_key"] == "zip_code" else "0"}
                                    for q in r["questions"]], agents=agents)
        r = _confirm(r["case"], agents=agents)
        self.assertEqual(r["status"], "completed")
        self.assertEqual(set(seen_dates), {"agent_1", "agent_6", "agent_8", "agent_10"})
        for role, dates in seen_dates.items():
            self.assertEqual(dates, {"2026-11-15"}, f"ref_date mismatch for {role}: {dates}")

    def test_isolate_false_after_chdir_to_empty_temp(self):
        """start → answer → confirm works with isolate=False after os.chdir to an empty temp folder."""
        orig = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                r1 = _start(agents=_agents(), isolate=False)
                self.assertIn(r1["status"], ("needs_clarification", "needs_confirmation"))
                if r1["status"] == "needs_clarification":
                    q = r1["questions"][0]
                    r2 = _answer(r1["case"],
                                 [{"question_id": q["question_id"], "answer_text": "hours cut"}],
                                 agents=_agents(), isolate=False)
                    # Drive to summary
                    while r2["status"] == "needs_clarification":
                        ans = [{"question_id": q2["question_id"],
                                "answer_text": "95823" if q2["fact_key"] == "zip_code" else "0"}
                               for q2 in r2["questions"]]
                        r2 = _answer(r2["case"], ans, agents=_agents(), isolate=False)
                    r3 = _confirm(r2["case"], agents=_agents(), isolate=False)
                else:
                    r3 = _confirm(r1["case"], agents=_agents(), isolate=False)
                self.assertEqual(r3["status"], "completed")
            finally:
                os.chdir(orig)   # leave the folder before it is removed (Windows)


class TestDialogV(unittest.TestCase):
    """dialog_version field."""

    def test_dialog_version_in_every_response(self):
        r = _start(agents=_agents())
        self.assertEqual(r["dialog_version"], "0.2")


class TestSkipAllowed(unittest.TestCase):
    """Skipping can_skip=true vs can_skip=false."""

    def test_skip_can_skip_true_allowed_and_listed_in_unknown(self):
        """Skipping a can_skip=true question → never asked again, listed in unknown."""
        r1 = _start(agents=_agents())
        q1 = r1["questions"][0]
        self.assertTrue(q1["can_skip"])
        r2 = _answer(r1["case"],
                     [{"question_id": q1["question_id"], "skipped": True}],
                     agents=_agents())
        # Eventually get to summary and check unknown
        while r2["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else "0"}
                       for q in r2["questions"]]
            r2 = _answer(r2["case"], answers, agents=_agents())
        self.assertEqual(r2["status"], "needs_confirmation")
        unknown_fields = {u["field"] for u in r2["summary"]["unknown"]}
        self.assertIn(q1["fact_key"], unknown_fields)
        # fact_key must not appear as a question in a later turn
        for q in r2.get("questions", []):
            self.assertNotEqual(q["fact_key"], q1["fact_key"])

    def test_skip_can_skip_false_returns_failed_case_unchanged(self):
        """Skipping a can_skip=false question → failed SKIP_NOT_ALLOWED, case unchanged."""
        # Drive to turn 2 where household_gross_monthly_income (can_skip=false) appears
        r1 = _start(agents=_agents())
        q1 = r1["questions"][0]
        r2 = _answer(r1["case"],
                     [{"question_id": q1["question_id"], "answer_text": "hours cut"}],
                     agents=_agents())
        # Find the can_skip=false question
        req_q = next((q for q in r2["questions"] if not q["can_skip"]), None)
        self.assertIsNotNone(req_q, "Expected a can_skip=false question in turn 2")
        # Try to skip it
        skip_answers = [{"question_id": q["question_id"],
                          "skipped": True} for q in r2["questions"]]
        r_fail = _answer(r2["case"], skip_answers, agents=_agents())
        self.assertEqual(r_fail["status"], "failed")
        codes = {i["code"] for i in r_fail["issues"]}
        self.assertIn("SKIP_NOT_ALLOWED", codes)
        # Case must be unchanged (same version)
        self.assertEqual(r_fail["case"]["case_version"], r2["case"]["case_version"])

    def test_skipped_in_turn1_still_why_skipped_in_summary(self):
        """A key skipped in turn 1 still shows why='skipped' in the summary after turn 2."""
        r1 = _start(agents=_agents())
        q1 = r1["questions"][0]
        tc_key = q1["fact_key"]
        r2 = _answer(r1["case"],
                     [{"question_id": q1["question_id"], "skipped": True}],
                     agents=_agents())
        # Answer turn 2 normally
        while r2["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else "0"}
                       for q in r2["questions"]]
            r2 = _answer(r2["case"], answers, agents=_agents())
        self.assertEqual(r2["status"], "needs_confirmation")
        unknown = {u["field"]: u["why"] for u in r2["summary"]["unknown"]}
        self.assertIn(tc_key, unknown)
        self.assertEqual(unknown[tc_key], "skipped")


class TestGeographyGuard(unittest.TestCase):
    """Geography guard: Supervisor asks ZIP when Agent 2 never does."""

    def test_supervisor_asks_zip_when_agent2_silent(self):
        """Agent 2 that never asks → Supervisor asks zip_code once."""
        r1 = _start(agents=_agents(agent_2=agent_2_dialog_no_questions))
        self.assertEqual(r1["status"], "needs_clarification")
        self.assertEqual(len(r1["questions"]), 1)
        self.assertEqual(r1["questions"][0]["fact_key"], "zip_code")

    def test_zip_skipped_geography_missing_at_confirm(self):
        """ZIP skipped → limitations carry geography sentence; GEOGRAPHY_MISSING at confirm."""
        r1 = _start(agents=_agents(agent_2=agent_2_dialog_no_questions))
        q = r1["questions"][0]
        self.assertEqual(q["fact_key"], "zip_code")
        r2 = _answer(r1["case"],
                     [{"question_id": q["question_id"], "skipped": True}],
                     agents=_agents(agent_2=agent_2_dialog_no_questions))
        # Should go to summary (no more questions from agent_2_dialog_no_questions)
        while r2["status"] == "needs_clarification":
            ans = [{"question_id": q2["question_id"], "skipped": True}
                   for q2 in r2["questions"]]
            r2 = _answer(r2["case"], ans,
                          agents=_agents(agent_2=agent_2_dialog_no_questions))
        self.assertIn(D._GEO_LIMITATION, r2["limitations"])
        r3 = _confirm(r2["case"], agents=_agents(agent_2=agent_2_dialog_no_questions))
        geo_codes = {i["code"] for i in r3["issues"]}
        self.assertIn("GEOGRAPHY_MISSING", geo_codes)

    def test_with_zip_limitations_empty(self):
        """When ZIP is provided, limitations is an empty list."""
        r = _start(agents=_agents())
        while r["status"] == "needs_clarification":
            r = _answer(r["case"], [{"question_id": q["question_id"],
                                     "answer_text": {"zip_code": "95823",
                                                     "household_gross_monthly_income": "0"
                                                     }.get(q["fact_key"], "hours cut")}
                                    for q in r["questions"]], agents=_agents())
        self.assertEqual(r["status"], "needs_confirmation")
        self.assertIn("zip_code", {f["field"] for f in r["summary"]["facts"]})
        self.assertEqual(r["limitations"], [])


class TestQuestionDropped(unittest.TestCase):
    """QUESTION_DROPPED: already-answered key is dropped."""

    def test_already_answered_key_dropped_goes_to_summary(self):
        """Agent 2 that asks an already-answered key → QUESTION_DROPPED → summary."""
        # Answer turn 1 (triggering_circumstances)
        r1 = _start(agents=_agents())
        q1 = r1["questions"][0]
        tc_key = q1["fact_key"]
        r2 = _answer(r1["case"],
                     [{"question_id": q1["question_id"], "answer_text": "hours cut"}],
                     agents=_agents(agent_2=agent_2_dialog_repeats_asked))
        # agent_2_dialog_repeats_asked asks triggering_circumstances again → dropped → summary
        self.assertEqual(r2["status"], "needs_confirmation")
        dropped = [i for i in r2["issues"] if i["code"] == "QUESTION_DROPPED"]
        self.assertTrue(any(i["related_ref"] == tc_key for i in dropped))


class TestLoopGuard(unittest.TestCase):
    """LOOP_GUARD_TURNS: after 8 answered turns, go to summary."""

    def test_loop_guard_triggers_after_8_turns(self):
        """Agent 2 that always asks a new key → needs_confirmation after 8 answered turns."""
        r = _start(agents=_agents(agent_2=agent_2_dialog_always_new))
        turn = 0
        while r["status"] == "needs_clarification":
            if turn >= 10:
                self.fail("Loop guard did not trigger after 10 turns")
            answers = [{"question_id": q["question_id"],
                        "answer_text": "some answer"}
                       for q in r["questions"]]
            r = _answer(r["case"], answers,
                        agents=_agents(agent_2=agent_2_dialog_always_new))
            turn += 1
        self.assertEqual(r["status"], "needs_confirmation")
        guard_issues = [i for i in r["issues"] if i["code"] == "QUESTION_LOOP_GUARD"]
        self.assertEqual(len(guard_issues), 1)
        self.assertLessEqual(turn, D.LOOP_GUARD_TURNS)

    def test_normal_dialog_never_triggers_loop_guard(self):
        """A normal dialog with agent_2_dialog never triggers QUESTION_LOOP_GUARD."""
        r = _start(agents=_agents())
        while r["status"] == "needs_clarification":
            answers = []
            for q in r["questions"]:
                if q["fact_key"] == "zip_code":
                    answers.append({"question_id": q["question_id"], "answer_text": "95823"})
                else:
                    answers.append({"question_id": q["question_id"], "answer_text": "hours cut"})
            r = _answer(r["case"], answers, agents=_agents())
        codes = {i["code"] for i in r["issues"]}
        self.assertNotIn("QUESTION_LOOP_GUARD", codes)


class TestConfirmEdits(unittest.TestCase):
    """confirm: corrections, rejected needs, added needs."""

    def _get_summary_case(self):
        r = _start(agents=_agents())
        while r["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else "hours cut"}
                       for q in r["questions"]]
            r = _answer(r["case"], answers, agents=_agents())
        return r["case"]

    def test_reject_one_need_plan_only_for_other(self):
        """Reject need_002 → only need_001 in plan; rejected_needs listed."""
        case = self._get_summary_case()
        r = _confirm(case, rejected_need_ids=["need_002"], agents=_agents())
        self.assertEqual(r["status"], "completed")
        self.assertTrue(any(rn["need_id"] == "need_002" for rn in r["rejected_needs"]))
        # need_002 must not appear in plan_by_need
        pbn_ids = [row["need_id"] for row in r["plan_by_need"]]
        self.assertNotIn("need_002", pbn_ids)

    def test_reject_all_needs_no_needs_left(self):
        """Reject all needs → failed NO_NEEDS_LEFT."""
        case = self._get_summary_case()
        need_ids = [n["need_id"] for n in case["needs"]]
        r = _confirm(case, rejected_need_ids=need_ids, agents=_agents())
        self.assertEqual(r["status"], "failed")
        codes = {i["code"] for i in r["issues"]}
        self.assertIn("NO_NEEDS_LEFT", codes)

    def test_unknown_need_id_fails(self):
        """Unknown rejected need_id → failed UNKNOWN_NEED_ID, nothing changed."""
        case = self._get_summary_case()
        r = _confirm(case, rejected_need_ids=["need_999"], agents=_agents())
        self.assertEqual(r["status"], "failed")
        codes = {i["code"] for i in r["issues"]}
        self.assertIn("UNKNOWN_NEED_ID", codes)

    def test_add_utility_assistance_third_need(self):
        """Add utility_assistance → a third confirmed need reaches Agent 3."""
        received_needs = {}

        def spy3(req):
            received_needs["needs"] = [n["need_id"] for n in req["payload"]["needs"]]
            return agent_3(req)

        case = self._get_summary_case()
        r = _confirm(case,
                     added_needs=[{"category": "utility_assistance",
                                   "description": "Help with electricity bill"}],
                     agents=_agents(agent_3=spy3))
        self.assertEqual(r["status"], "completed")
        self.assertIn("need_003", received_needs.get("needs", []))

    def test_add_existing_category_fails(self):
        """Adding a category that already exists → failed NEED_ALREADY_PRESENT."""
        case = self._get_summary_case()
        r = _confirm(case,
                     added_needs=[{"category": "housing_assistance",
                                   "description": "More housing help"}],
                     agents=_agents())
        self.assertEqual(r["status"], "failed")
        codes = {i["code"] for i in r["issues"]}
        self.assertIn("NEED_ALREADY_PRESENT", codes)

    def test_ssn_in_added_need_description_masked(self):
        """SSN-like number in added_need description is masked before storage."""
        case = self._get_summary_case()
        r = _confirm(case,
                     added_needs=[{"category": "utility_assistance",
                                   "description": "My SSN is 123-45-6789 help with bills"}],
                     agents=_agents())
        self.assertEqual(r["status"], "completed")
        # The SSN must not appear in the completed case's needs
        for n in r["case"]["needs"]:
            self.assertNotIn("123-45-6789", n.get("description", ""))

    def test_correction_replaces_fact_reaches_planning(self):
        """A correction of income replaces the value; Agent 4 receives the corrected value."""
        received = {}

        def spy4(req):
            received["facts"] = {f["field"]: f["value"]
                                  for f in req["payload"].get("case_facts", [])}
            return agent_4(req)

        # Drive to summary with income 0
        r1 = _start(agents=_agents())
        while r1["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else
                        "0" if q["fact_key"] == "household_gross_monthly_income" else "hours cut"}
                       for q in r1["questions"]]
            r1 = _answer(r1["case"], answers, agents=_agents())
        r2 = _confirm(r1["case"],
                      corrections={"household_gross_monthly_income": 1500},
                      agents=_agents(agent_4=spy4))
        self.assertEqual(r2["status"], "completed")
        self.assertEqual(received.get("facts", {}).get("household_gross_monthly_income"), 1500)

    def test_unknown_fact_key_in_correction_fails(self):
        """Correction of an unknown field → failed UNKNOWN_FACT_KEY, nothing changed."""
        case = self._get_summary_case()
        r = _confirm(case,
                     corrections={"nonexistent_field": "value"},
                     agents=_agents())
        self.assertEqual(r["status"], "failed")
        codes = {i["code"] for i in r["issues"]}
        self.assertIn("UNKNOWN_FACT_KEY", codes)
        # Case must be unchanged
        self.assertEqual(r["case"]["stage"], "awaiting_confirmation")


class TestCoverageGap(unittest.TestCase):
    """plan_by_need: coverage gaps reach gap_notes; NEED_NOT_IN_PLAN when neither card nor gap."""

    def test_coverage_gap_reaches_gap_notes(self):
        """Agent 8 with a coverage gap for need_002 → gap_notes not empty; no NEED_NOT_IN_PLAN."""
        r1 = _start(agents=_agents())
        while r1["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else "hours cut"}
                       for q in r1["questions"]]
            r1 = _answer(r1["case"], answers, agents=_agents())
        r2 = _confirm(r1["case"], agents=_agents(agent_8=agent_8_dialog_with_gap))
        self.assertEqual(r2["status"], "completed")
        row2 = next((r for r in r2["plan_by_need"] if r["need_id"] == "need_002"), None)
        self.assertIsNotNone(row2)
        self.assertTrue(len(row2["gap_notes"]) > 0)
        need_not_in_plan = [i for i in r2["issues"] if i["code"] == "NEED_NOT_IN_PLAN"]
        self.assertEqual(len(need_not_in_plan), 0)

    def test_need_not_in_plan_warning_when_no_card_no_gap(self):
        """A need with no card and no gap → NEED_NOT_IN_PLAN warning, gap_notes has user message."""
        # agent_8 returns cards for need_001 and need_002 normally;
        # inject a fake need_003 that no card covers and no gap mentions
        from navigator.supervisor import builders as B

        def agent_8_extra_need(req):
            r = agent_8(req)
            # need_003 has no card; no coverage_gaps for it
            return r

        r1 = _start(agents=_agents())
        while r1["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else "hours cut"}
                       for q in r1["questions"]]
            r1 = _answer(r1["case"], answers, agents=_agents())
        # Add a third need directly to the case before confirm
        case = dict(r1["case"])
        case["needs"] = list(case["needs"]) + [{
            "need_id": "need_003", "category": "utility_assistance",
            "description": "d", "original_quote": "q",
            "confirmation_status": "proposed", "user_reported": True,
            "urgency": "normal", "urgency_reason": None, "user_priority": None,
        }]
        r2 = _confirm(case, agents=_agents(agent_8=agent_8_extra_need))
        self.assertEqual(r2["status"], "completed")
        not_in_plan = [i for i in r2["issues"] if i["code"] == "NEED_NOT_IN_PLAN"]
        self.assertTrue(len(not_in_plan) > 0)
        row3 = next((r for r in r2["plan_by_need"] if r["need_id"] == "need_003"), None)
        self.assertIsNotNone(row3)
        self.assertIn("We have not found", row3["gap_notes"][0])


class TestPlanStopped(unittest.TestCase):
    """Planning stopped → failed with the ORIGINAL case (stage awaiting_confirmation)."""

    def test_planning_stopped_returns_original_case(self):
        """If Agent 3 fails, confirm returns failed with case stage=awaiting_confirmation."""
        from tests.fake_agents import crashing_agent

        r1 = _start(agents=_agents())
        while r1["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else "hours cut"}
                       for q in r1["questions"]]
            r1 = _answer(r1["case"], answers, agents=_agents())
        confirmation_case = r1["case"]
        r2 = _confirm(confirmation_case, agents=_agents(agent_3=crashing_agent))
        self.assertEqual(r2["status"], "failed")
        # The returned case must still be the awaiting_confirmation case
        self.assertEqual(r2["case"]["stage"], "awaiting_confirmation")
        codes = {i["code"] for i in r2["issues"]}
        self.assertIn("AGENT_FAILED", codes)


class TestAgent1FailsOnAnswer(unittest.TestCase):
    """Agent 1 failing on parse_clarification_answer → failed with original case."""

    def test_agent1_fail_on_answer_returns_original_case(self):
        r1 = _start(agents=_agents(agent_1=agent_1_dialog_fails_on_answer))
        self.assertEqual(r1["status"], "needs_clarification")
        q1 = r1["questions"][0]
        original_case = r1["case"]
        r2 = _answer(r1["case"],
                     [{"question_id": q1["question_id"], "answer_text": "hours cut"}],
                     agents=_agents(agent_1=agent_1_dialog_fails_on_answer))
        self.assertEqual(r2["status"], "failed")
        codes = {i["code"] for i in r2["issues"]}
        self.assertIn("AGENT_FAILED", codes)
        # Case must be the same as before the answer (same version, same stage)
        self.assertEqual(r2["case"]["case_version"], original_case["case_version"])
        self.assertEqual(r2["case"]["stage"], "clarifying")


class TestCaseCheck(unittest.TestCase):
    """CASE_INVALID, WRONG_STAGE."""

    def test_confirm_on_clarifying_case_wrong_stage(self):
        """Calling confirm on a clarifying case → WRONG_STAGE, no exception."""
        r1 = _start(agents=_agents())
        self.assertEqual(r1["status"], "needs_clarification")
        r2 = _confirm(r1["case"], agents=_agents())
        self.assertEqual(r2["status"], "failed")
        codes = {i["code"] for i in r2["issues"]}
        self.assertIn("WRONG_STAGE", codes)

    def test_answer_with_broken_case_case_invalid(self):
        """answer() with a broken case dict → CASE_INVALID, no exception."""
        r = _answer({"case_id": "x"}, [], agents=_agents())
        self.assertEqual(r["status"], "failed")
        codes = {i["code"] for i in r["issues"]}
        self.assertIn("CASE_INVALID", codes)

    def test_answer_with_non_dict_case_case_invalid(self):
        """answer() with a non-dict case → CASE_INVALID, no exception."""
        r = _answer("not-a-case", [], agents=_agents())
        self.assertEqual(r["status"], "failed")
        codes = {i["code"] for i in r["issues"]}
        self.assertIn("CASE_INVALID", codes)

    def test_unknown_question_id_fails(self):
        """answer() with unknown question_id → UNKNOWN_QUESTION_ID, no exception."""
        r1 = _start(agents=_agents())
        r2 = _answer(r1["case"],
                     [{"question_id": "q99-1", "answer_text": "x"}],
                     agents=_agents())
        self.assertEqual(r2["status"], "failed")
        codes = {i["code"] for i in r2["issues"]}
        self.assertIn("UNKNOWN_QUESTION_ID", codes)


class TestPrivacy(unittest.TestCase):
    """Privacy: SSN in an answer never reaches Agent 1 and not in the case."""

    def test_ssn_in_answer_masked_before_agent1(self):
        seen = {}

        def spy1(req):
            seen["text"] = req["payload"].get("answer_text", "")
            return agent_1_dialog(req)

        r1 = _start(agents=_agents())
        q1 = r1["questions"][0]
        _answer(r1["case"],
                [{"question_id": q1["question_id"],
                  "answer_text": "My SSN is 123-45-6789 and hours were cut"}],
                agents=_agents(agent_1=spy1))
        self.assertNotIn("123-45-6789", seen.get("text", ""))


class TestSafetyNotice(unittest.TestCase):
    """safety_notice shape and safety flags merged from answers."""

    def test_safety_notice_shape(self):
        """safety_notice has the §5 fields: risk_type, message, contacts, blocks_plan."""
        r1 = _start(agents=_agents())
        # Inject a safety flag into the case
        case = dict(r1["case"])
        case["safety_flags"] = [{"type": "safety", "quote": "[REDACTED]", "note": "test"}]
        # Drive to summary
        while r1["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"], "answer_text": "hours cut"}
                       for q in r1["questions"]]
            r1 = _answer(r1["case"], answers, agents=_agents())
            r1 = dict(r1)
            r1["case"] = dict(r1["case"])
            r1["case"]["safety_flags"] = case["safety_flags"]
        r2 = _confirm(r1["case"], agents=_agents())
        self.assertIsNotNone(r2["safety_notice"])
        if r2.get("safety_notice"):
            sn = r2["safety_notice"]
            self.assertEqual(sn["risk_type"], "safety")
            self.assertIn("risk_type", sn)
            self.assertIn("message", sn)
            self.assertIn("contacts", sn)
            self.assertIn("blocks_plan", sn)
            self.assertFalse(sn["blocks_plan"])

    def test_safety_flag_in_answer_merges_into_later_responses(self):
        """Safety flag returned by Agent 1 on an answer appears in the safety_notice."""
        r1 = _start(agents=_agents(agent_1=agent_1_dialog_with_safety))
        q1 = r1["questions"][0]
        r2 = _answer(r1["case"],
                     [{"question_id": q1["question_id"],
                       "answer_text": "someone tried to hurt me hours cut"}],
                     agents=_agents(agent_1=agent_1_dialog_with_safety))
        # The safety flag should now appear
        self.assertTrue(len(r2["case"]["safety_flags"]) > 0)
        self.assertIsNotNone(r2["safety_notice"])
        self.assertNotIn("hurt", str(r2["safety_notice"]))   # no user words in the notice


def _to_summary(agents=None):
    """Drive a dialog to the summary: ZIP 95823, income 0, other answers "hours cut"."""
    agents = agents or _agents()
    r = _start(agents=agents)
    while r["status"] == "needs_clarification":
        r = _answer(r["case"], [{"question_id": q["question_id"],
                                 "answer_text": {"zip_code": "95823",
                                                 "household_gross_monthly_income": "0"
                                                 }.get(q["fact_key"], "hours cut")}
                                for q in r["questions"]], agents=agents)
    return r


class TestFailedResponses(unittest.TestCase):
    """D1, D2, D4: what a failed response carries."""

    def test_non_dict_case_gives_case_none(self):
        r = _answer("not-a-case", [], agents=_agents())
        self.assertEqual(r["status"], "failed")
        self.assertIsNone(r["case"])
        self.assertIsNone(r["case_id"])
        self.assertEqual(r["limitations"], [])

    def test_failed_keeps_safety_notice(self):
        r1 = _start(agents=_agents())
        case = dict(r1["case"], safety_flags=[{"type": "safety", "quote": "[REDACTED]",
                                              "note": "Threat of physical harm reported"}])
        r = _answer(case, [{"question_id": "q9-9", "answer_text": "x"}], agents=_agents())
        self.assertEqual(r["status"], "failed")
        self.assertIsNotNone(r["safety_notice"])

    def test_skip_not_allowed_returns_same_questions_with_text(self):
        r = _start(agents=_agents())
        while r["status"] == "needs_clarification" and all(q["can_skip"] for q in r["questions"]):
            r = _answer(r["case"], [{"question_id": q["question_id"],
                                     "answer_text": "95823" if q["fact_key"] == "zip_code" else "hours cut"}
                                    for q in r["questions"]], agents=_agents())
        self.assertEqual(r["status"], "needs_clarification")
        asked = r["questions"]
        bad = _answer(r["case"], [{"question_id": q["question_id"], "skipped": True} for q in asked],
                      agents=_agents())
        self.assertEqual(bad["status"], "failed")
        self.assertIn("SKIP_NOT_ALLOWED", {i["code"] for i in bad["issues"]})
        self.assertEqual(bad["questions"], asked)
        self.assertTrue(all(q["text"] for q in bad["questions"]))

    def test_stopped_plan_shows_cause_and_no_need_not_in_plan(self):
        # agent_3 (not agent_3_dialog) still returns need_002 after it is rejected,
        # so S5 rejects Agent 3 with UNKNOWN_REFERENCE and planning stops.
        r = _to_summary()
        stop = _confirm(r["case"], rejected_need_ids=["need_002"], agents=_agents(agent_3=agent_3))
        self.assertEqual(stop["status"], "failed")
        codes = [i["code"] for i in stop["issues"]]
        self.assertIn("UNKNOWN_REFERENCE", codes)
        self.assertNotIn("NEED_NOT_IN_PLAN", codes)
        msg = next(i["message"] for i in stop["issues"] if i["code"] == "AGENT_FAILED")
        self.assertEqual(msg, "Planning stopped at agent_3")
        self.assertEqual(stop["case"]["stage"], "awaiting_confirmation")


class TestSafetyNoticeTypes(unittest.TestCase):
    """D3: only a "safety" flag shows the 9-1-1 notice."""

    def test_official_deadline_flag_alone_gives_no_notice(self):
        self.assertIsNone(D._safety_notice([{"type": "official_deadline", "quote": "x", "note": "y"}]))

    def test_safety_flag_gives_notice(self):
        sn = D._safety_notice([{"type": "official_deadline", "quote": "x", "note": "y"},
                               {"type": "safety", "quote": "x", "note": "y"}])
        self.assertEqual(sn["risk_type"], "safety")
        self.assertFalse(sn["blocks_plan"])


class TestAnswerValues(unittest.TestCase):
    """D5: an answer sent as a number."""

    def test_income_zero_as_number(self):
        r = _start(agents=_agents())
        while r["status"] == "needs_clarification":
            r = _answer(r["case"], [{"question_id": q["question_id"],
                                     "answer_text": {"zip_code": "95823",
                                                     "household_gross_monthly_income": 0
                                                     }.get(q["fact_key"], "hours cut")}
                                    for q in r["questions"]], agents=_agents())
        self.assertEqual(r["status"], "needs_confirmation")
        facts = {f["field"]: f["value"] for f in r["summary"]["facts"]}
        self.assertEqual(facts.get("household_gross_monthly_income"), 0)


class TestCorrectionValues(unittest.TestCase):
    """D6: corrections are checked and normalised before any change."""

    def test_money_string_with_comma_becomes_number(self):
        seen = {}

        def spy4(req):
            seen.update({f["field"]: f["value"] for f in req["payload"]["case_facts"]})
            return agent_4(req)
        r = _to_summary()
        done = _confirm(r["case"], corrections={"household_gross_monthly_income": "1,500"},
                        agents=_agents(agent_4=spy4))
        self.assertEqual(done["status"], "completed")
        self.assertEqual(seen["household_gross_monthly_income"], 1500)

    def test_bad_values_fail_and_change_nothing(self):
        r = _to_summary()
        for corr in ({"household_gross_monthly_income": "abc"},
                     {"household_gross_monthly_income": -5},
                     {"zip_code": ["95823"]}):
            bad = _confirm(r["case"], corrections=corr, agents=_agents())
            self.assertEqual(bad["status"], "failed", corr)
            self.assertIn("FACT_VALUE_INVALID", {i["code"] for i in bad["issues"]}, corr)
            self.assertEqual(bad["case"], r["case"], corr)
            self.assertNotIn("abc", str(bad["issues"]))

    def test_date_check_function(self):
        self.assertEqual(D._normalise_correction("rent_due_date", "2026-11-30"), (True, "2026-11-30"))
        self.assertFalse(D._normalise_correction("rent_due_date", "next week")[0])
        self.assertFalse(D._normalise_correction("has_court_writ_or_judgment", "yes")[0])
        self.assertEqual(D._normalise_correction("has_court_writ_or_judgment", True), (True, True))
        self.assertEqual(D._normalise_correction("rent_amount_monthly", "$1,200.50"), (True, 1200.5))


class TestSettledFlags(unittest.TestCase):
    """D7: an ambiguity flag is not forwarded to Agent 2 once its field is answered or skipped."""

    def _run(self, first_answer):
        seen = []

        def spy2(req):
            seen.append([f.get("field") for f in req["payload"].get("ambiguity_flags", [])])
            return agent_2_dialog(req)
        r = _start(agents=_agents(agent_2=spy2))
        q = next(q for q in r["questions"] if q["fact_key"] == "triggering_circumstances")
        _answer(r["case"], [dict({"question_id": q["question_id"]}, **first_answer)],
                agents=_agents(agent_2=spy2))
        return seen

    def test_flag_sent_first_then_dropped_after_answer(self):
        seen = self._run({"answer_text": "hours cut"})
        self.assertEqual(seen[0], ["triggering_circumstances"])
        self.assertEqual(seen[1], [])

    def test_flag_dropped_after_skip(self):
        seen = self._run({"skipped": True})
        self.assertEqual(seen[1], [])

    def test_case_keeps_the_flag(self):
        r = _start(agents=_agents())
        self.assertEqual([f["field"] for f in r["case"]["ambiguity_flags"]], ["triggering_circumstances"])


class TestDisplayValue(unittest.TestCase):
    """D8: display_value is always text."""

    def test_number_list_and_bool(self):
        self.assertEqual(D._display_value("household_size", 3), "3")
        self.assertEqual(D._display_value("children_ages", [4, 7]), "4, 7")
        self.assertEqual(D._display_value("has_court_writ_or_judgment", False), "No")
        self.assertEqual(D._display_value("specific_move_out_date", "2026-11-30"), "Nov 30, 2026")
        self.assertEqual(D._display_value("household_gross_monthly_income", 0), "$0")


class TestPlanByNeed(unittest.TestCase):
    """plan_by_need rows and ordering."""

    def _get_completed(self):
        r1 = _start(agents=_agents())
        while r1["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else "hours cut"}
                       for q in r1["questions"]]
            r1 = _answer(r1["case"], answers, agents=_agents())
        return _confirm(r1["case"], agents=_agents())

    def test_plan_by_need_has_both_needs(self):
        r = self._get_completed()
        self.assertEqual(r["status"], "completed")
        pbn_ids = {row["need_id"] for row in r["plan_by_need"]}
        self.assertIn("need_001", pbn_ids)
        self.assertIn("need_002", pbn_ids)

    def test_rejected_need_not_in_plan_by_need(self):
        r1 = _start(agents=_agents())
        while r1["status"] == "needs_clarification":
            answers = [{"question_id": q["question_id"],
                        "answer_text": "95823" if q["fact_key"] == "zip_code" else "hours cut"}
                       for q in r1["questions"]]
            r1 = _answer(r1["case"], answers, agents=_agents())
        r2 = _confirm(r1["case"], rejected_need_ids=["need_002"], agents=_agents())
        self.assertEqual(r2["status"], "completed")
        pbn_ids = [row["need_id"] for row in r2["plan_by_need"]]
        self.assertNotIn("need_002", pbn_ids)


if __name__ == "__main__":
    unittest.main()
