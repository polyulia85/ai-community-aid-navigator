"""
Unit tests and real Input/Output verification for Slav & Julia's 12 review items + follow-up items.
Run via unittest: python -m unittest tests/agent_1_2/test_slav_12_items.py -v
Run for real I/O log: python -m tests.agent_1_2.test_slav_12_items
"""
import unittest

from navigator.agents.agent_1_2.agent_1 import handle_agent_1
from navigator.agents.agent_1_2.agent_2 import handle_agent_2


def _req_a1(story_text: str, ref_date: str = "2026-11-01") -> dict:
    return {
        "request_id": "req-test-a1",
        "run_id": "run-test",
        "case_id": "case-test",
        "case_version": 1,
        "schema_version": "1.0",
        "role_id": "agent_1",
        "task_type": "understand_story",
        "payload": {
            "story_text": story_text,
            "locale": "en-US",
            "ref_date": ref_date,
        },
    }


def _req_clarify(
    answer_text: str,
    pending_fact_keys: list,
    existing_needs: list | None = None,
    ref_date: str = "2026-11-01",
) -> dict:
    return {
        "request_id": "req-test-clarify",
        "run_id": "run-test",
        "case_id": "case-test",
        "case_version": 1,
        "schema_version": "1.0",
        "role_id": "agent_1",
        "task_type": "parse_clarification_answer",
        "payload": {
            "answer_text": answer_text,
            "pending_fact_keys": pending_fact_keys,
            "existing_needs": existing_needs or [],
            "ref_date": ref_date,
        },
    }


def _req_a2(
    needs: list,
    case_facts: list | None = None,
    already_asked: list | None = None,
) -> dict:
    return {
        "request_id": "req-test-a2",
        "run_id": "run-test",
        "case_id": "case-test",
        "case_version": 1,
        "schema_version": "1.0",
        "role_id": "agent_2",
        "task_type": "clarify_case",
        "payload": {
            "needs": needs,
            "case_facts": case_facts or [],
            "already_asked": already_asked or [],
            "candidate_requirements": [],
            "ambiguity_flags": [],
        },
    }


class TestSlavTwelveItems(unittest.TestCase):
    def test_01_lockout_threat_stays_high_not_immediate(self):
        for phrase in [
            "My landlord threatened to lock us out if we don't pay rent.",
            "My landlord said he will change the locks tomorrow.",
        ]:
            res = handle_agent_1(_req_a1(phrase))
            needs = res["result"]["proposed_needs"]
            self.assertEqual(len(needs), 1)
            self.assertEqual(needs[0]["category"], "housing_assistance")
            self.assertEqual(needs[0]["urgency"], "high")
            self.assertEqual(res["result"]["safety_or_official_deadline_flags"], [])

    def test_02_agent_2_asks_julia_threat_clarifying_questions(self):
        a1 = handle_agent_1(_req_a1("My landlord threatened to lock us out if we don't pay rent."))
        # Turn 1 (ZIP and income unknown)
        a2_t1 = handle_agent_2(_req_a2(a1["result"]["proposed_needs"], a1["result"]["factual_claims"]))
        self.assertLessEqual(len(a2_t1["clarification_requests"]), 2)
        # Turn 2 (after ZIP and income are answered, Agent 2 asks up to 2 of Julia's 4 threat questions)
        facts = [
            {"field": "zip_code", "value": "95823"},
            {"field": "household_gross_monthly_income", "value": 1000},
        ]
        a2_t2 = handle_agent_2(
            _req_a2(
                a1["result"]["proposed_needs"],
                facts,
                ["zip_code", "household_gross_monthly_income"],
            )
        )
        q_keys = [q["fact_key"] for q in a2_t2["clarification_requests"]]
        self.assertEqual(q_keys, ["has_written_eviction_notice", "has_court_writ_or_judgment"])

    def test_03_and_04_actual_lockout_without_us_me_and_eviction_notice_type_lockout(self):
        for phrase in [
            "We were locked out of our apartment yesterday.",
            "I got locked out of my apartment by the landlord.",
        ]:
            res = handle_agent_1(_req_a1(phrase))
            needs = res["result"]["proposed_needs"]
            facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
            self.assertEqual(needs[0]["urgency"], "immediate")
            self.assertIn("locked out", needs[0]["urgency_reason"].lower())
            self.assertEqual(facts.get("eviction_notice_type"), "lockout")

    def test_05_landlord_threat_to_hurt_raises_safety_and_housing_need(self):
        res = handle_agent_1(_req_a1("My landlord threatened to hurt us if we don't leave."))
        flags = res["result"]["safety_or_official_deadline_flags"]
        needs = res["result"]["proposed_needs"]
        self.assertTrue(any(f["type"] == "safety" for f in flags))
        self.assertTrue(
            any(n["category"] == "housing_assistance" and n["urgency"] == "high" for n in needs)
        )

    def test_06_and_07_vague_food_and_housing_baseline_high_and_plain_descriptions(self):
        res_food = handle_agent_1(_req_a1("I have problems with food."))
        food_need = res_food["result"]["proposed_needs"][0]
        self.assertEqual(food_need["urgency"], "high")
        self.assertEqual(food_need["description"], "Food problem reported")
        self.assertEqual(food_need["urgency_reason"], "Food problem reported")

        res_acute = handle_agent_1(_req_a1("We have no food left and the kids are hungry."))
        self.assertEqual(res_acute["result"]["proposed_needs"][0]["urgency"], "immediate")

        res_house = handle_agent_1(_req_a1("I have problems with housing."))
        house_need = res_house["result"]["proposed_needs"][0]
        self.assertEqual(house_need["urgency"], "high")
        self.assertEqual(house_need["description"], "Housing problem reported")
        self.assertEqual(house_need["urgency_reason"], "Housing problem reported")

    def test_08_parse_clarification_grounds_food_urgency(self):
        res_vague = handle_agent_1(_req_clarify("We are also having problems with food.", ["zip_code"]))
        self.assertEqual(res_vague["result"]["proposed_needs"][0]["urgency"], "high")
        self.assertEqual(
            res_vague["result"]["proposed_needs"][0]["urgency_reason"], "Food problem reported"
        )

        res_acute = handle_agent_1(_req_clarify("We have no groceries left for the kids.", ["zip_code"]))
        self.assertEqual(res_acute["result"]["proposed_needs"][0]["urgency"], "immediate")

    def test_09_false_food_need_suppressed_when_no_need_signal(self):
        res = handle_agent_1(
            _req_clarify(
                "We got some food from the food bank last week, income is $900.",
                ["household_gross_monthly_income"],
            )
        )
        self.assertEqual(res["result"]["proposed_needs"], [])
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("household_gross_monthly_income"), 900)

    def test_10_bereavement_is_triggering_event_only_not_employment_or_income_need(self):
        res = handle_agent_1(_req_a1("My husband passed away last month and we need help with rent."))
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        needs = [n["category"] for n in res["result"]["proposed_needs"]]
        self.assertIn("bereavement", res["result"]["triggering_events"])
        self.assertNotIn("employment_status", facts)
        self.assertNotIn("income_assistance", needs)
        self.assertIn("housing_assistance", needs)

    def test_11_rent_due_date_extracted_from_clarification_answer(self):
        res = handle_agent_1(
            _req_clarify(
                "Our ZIP is 95823 and income is $1,200. Rent is $1,200 due on November 1st.",
                ["zip_code", "household_gross_monthly_income"],
                ref_date="2026-10-25",
            )
        )
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("rent_amount_monthly"), 1200)
        self.assertEqual(facts.get("rent_due_date"), "2026-11-01")

    def test_12_income_and_extra_facts_extracted_even_when_not_in_pending_fact_keys(self):
        res = handle_agent_1(
            _req_clarify(
                "We live in 95823 and our income is $1,000. The notice date is November 6, 2026, and the amount due is $1,600.",
                ["zip_code"],
            )
        )
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("zip_code"), "95823")
        self.assertEqual(facts.get("household_gross_monthly_income"), 1000)
        self.assertEqual(facts.get("eviction_notice_date"), "2026-11-06")
        self.assertEqual(facts.get("rent_arrears_amount"), 1600)

    # -------------------------------------------------------------------
    # FOLLOW-UP ITEMS FROM SLAV'S INTEGRATION RUNS
    # -------------------------------------------------------------------
    def test_13_followup_1_move_out_date_stored_as_specific_move_out_date(self):
        """Follow-up Item 1: 'He said we must leave by November 30.' stores specific_move_out_date, never eviction_notice_date."""
        res = handle_agent_1(
            _req_clarify(
                "He said we must leave by November 30.",
                ["specific_move_out_date"],
                ref_date="2026-11-01",
            )
        )
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        self.assertEqual(facts.get("specific_move_out_date"), "2026-11-30")
        self.assertNotIn("eviction_notice_date", facts)

    def test_14_followup_2_yes_answers_set_eviction_notice_type_and_agent_2_need_updates(self):
        """Follow-up Item 2: 'Yes' on court judgment or active lockout sets eviction_notice_type and raises housing urgency via need_updates."""
        a1_threat = handle_agent_1(_req_a1("My landlord threatened to lock us out if we don't pay rent."))
        housing_need = a1_threat["result"]["proposed_needs"][0]

        # Case A: Court judgment -> eviction_notice_type='judgment' + Agent 2 need_updates urgency='immediate'
        ans_court = handle_agent_1(
            _req_clarify("Yes, there is a court judgment.", ["has_court_writ_or_judgment"])
        )
        court_facts = {f["field"]: f["value"] for f in ans_court["result"]["factual_claims"]}
        self.assertIs(court_facts.get("has_court_writ_or_judgment"), True)
        self.assertEqual(court_facts.get("eviction_notice_type"), "judgment")

        a2_court = handle_agent_2(
            _req_a2(
                [housing_need],
                ans_court["result"]["factual_claims"],
                ["has_court_writ_or_judgment"],
            )
        )
        updates_court = a2_court["result"].get("need_updates", [])
        self.assertTrue(
            any(
                u["need_id"] == housing_need["need_id"] and u["urgency"] == "immediate"
                for u in updates_court
            )
        )

        # Case B: Changing locks right now -> eviction_notice_type='lockout' + Agent 2 need_updates urgency='immediate'
        ans_lock = handle_agent_1(
            _req_clarify("Yes, he is changing the locks right now.", ["imminent_removal_in_progress"])
        )
        lock_facts = {f["field"]: f["value"] for f in ans_lock["result"]["factual_claims"]}
        self.assertIs(lock_facts.get("imminent_removal_in_progress"), True)
        self.assertEqual(lock_facts.get("eviction_notice_type"), "lockout")

        a2_lock = handle_agent_2(
            _req_a2(
                [housing_need],
                ans_lock["result"]["factual_claims"],
                ["imminent_removal_in_progress"],
            )
        )
        updates_lock = a2_lock["result"].get("need_updates", [])
        self.assertTrue(
            any(
                u["need_id"] == housing_need["need_id"] and u["urgency"] == "immediate"
                for u in updates_lock
            )
        )

        # Case C: "No" or "I'm not sure" -> no eviction_notice_type, no urgency escalation
        ans_unsure = handle_agent_1(_req_clarify("I'm not sure.", ["has_court_writ_or_judgment"]))
        unsure_facts = {f["field"]: f["value"] for f in ans_unsure["result"]["factual_claims"]}
        self.assertNotIn("eviction_notice_type", unsure_facts)
        a2_unsure = handle_agent_2(
            _req_a2(
                [housing_need],
                ans_unsure["result"]["factual_claims"],
                ["has_court_writ_or_judgment"],
            )
        )
        self.assertFalse(
            any(u.get("urgency") == "immediate" for u in a2_unsure["result"].get("need_updates", []))
        )

    def test_15_followup_3_agent_2_header_reverted_to_v1_1(self):
        """Follow-up Item 3: agent_2.py docstring header must reference Contracts v1.1 (v1.2 is still draft)."""
        import navigator.agents.agent_1_2.agent_2 as a2_mod

        self.assertIn("v1.1", a2_mod.__doc__ or "")
        self.assertNotIn("v1.2", a2_mod.__doc__ or "")

    def test_16_followup_4_neutral_safety_flag_note(self):
        """Follow-up Item 4: Landlord harm threat must use a neutral safety note, not DV/988 hotline instructions."""
        res = handle_agent_1(_req_a1("My landlord threatened to hurt us if we don't leave."))
        flags = res["result"]["safety_or_official_deadline_flags"]
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["note"], "Threat of physical harm reported")
        self.assertNotIn("domestic violence", flags[0]["note"].lower())
        self.assertNotIn("988", flags[0]["note"])

    def test_17_followup_5_threat_questions_are_skippable_and_helpful(self):
        """Follow-up Item 5: All 4 threat clarification questions must have can_skip=True and necessity_level='helpful'."""
        a1 = handle_agent_1(_req_a1("My landlord threatened to lock us out if we don't pay rent."))
        base_facts = [
            {"field": "zip_code", "value": "95823"},
            {"field": "household_gross_monthly_income", "value": 1000},
        ]
        # Turn 2: first 2 threat questions
        a2_t2 = handle_agent_2(
            _req_a2(
                a1["result"]["proposed_needs"],
                base_facts,
                ["zip_code", "household_gross_monthly_income"],
            )
        )
        for q in a2_t2["clarification_requests"]:
            self.assertIs(q["can_skip"], True)
            self.assertEqual(q["necessity_level"], "helpful")

        # Turn 3 (after skipping first 2): next 2 threat questions
        a2_t3 = handle_agent_2(
            _req_a2(
                a1["result"]["proposed_needs"],
                base_facts,
                [
                    "zip_code",
                    "household_gross_monthly_income",
                    "has_written_eviction_notice",
                    "has_court_writ_or_judgment",
                ],
            )
        )
        self.assertEqual(len(a2_t3["clarification_requests"]), 2)
        for q in a2_t3["clarification_requests"]:
            self.assertIs(q["can_skip"], True)
            self.assertEqual(q["necessity_level"], "helpful")

    def test_18_followup_6_reduced_hours_proposes_income_assistance(self):
        """Follow-up Item 6: Reduced work hours or pay cut must propose income_assistance (urgency='high', reason='Work hours reduced')."""
        res = handle_agent_1(_req_a1("My hours were cut at work last month and I can't pay rent."))
        needs = res["result"]["proposed_needs"]
        income_needs = [n for n in needs if n["category"] == "income_assistance"]
        self.assertEqual(len(income_needs), 1)
        self.assertEqual(income_needs[0]["urgency"], "high")
        self.assertEqual(income_needs[0]["urgency_reason"], "Work hours reduced")

    def test_19_income_question_never_repeated_once_in_already_asked(self):
        """Commit 2 Item 3: household_gross_monthly_income is never asked again once present in already_asked."""
        needs = [{"need_id": "need_001", "category": "housing_assistance", "urgency": "high"}]
        facts = [{"field": "zip_code", "value": "95823"}]
        a2 = handle_agent_2(_req_a2(needs, facts, ["zip_code", "household_gross_monthly_income"]))
        q_keys = [q["fact_key"] for q in a2["clarification_requests"]]
        self.assertNotIn("household_gross_monthly_income", q_keys)
        self.assertEqual(a2["status"], "completed")

    def test_20_pay_cut_by_half_emits_reduced_hours_and_income_assistance(self):
        """Commit 2 Item 4: 'My pay was cut by half.' emits reduced_hours fact/triggering_event and income_assistance need."""
        res = handle_agent_1(_req_a1("My pay was cut by half."))
        facts = {f["field"]: f["value"] for f in res["result"]["factual_claims"]}
        needs = res["result"]["proposed_needs"]
        self.assertEqual(facts.get("employment_status"), "reduced_hours")
        self.assertIn("reduced_hours", res["result"]["triggering_events"])
        self.assertTrue(
            any(n["category"] == "income_assistance" and n["urgency"] == "high" for n in needs)
        )

    def test_21_need_updates_emitted_only_when_urgency_changes(self):
        """Commit 2 Item 5: Agent 2 must emit need_updates only when urgency actually changes."""
        food_need = [
            {
                "need_id": "need_001",
                "category": "food_assistance",
                "urgency": "high",
                "urgency_reason": "Food problem reported",
            }
        ]
        facts = [
            {"field": "zip_code", "value": "95823"},
            {"field": "household_gross_monthly_income", "value": 900},
            {"field": "household_size", "value": 3},
        ]
        a2_food = handle_agent_2(
            _req_a2(food_need, facts, ["zip_code", "household_gross_monthly_income", "household_size"])
        )
        self.assertEqual(a2_food["result"]["need_updates"], [])

        already_imm = [{"need_id": "need_001", "category": "housing_assistance", "urgency": "immediate"}]
        a2_imm = handle_agent_2(
            _req_a2(
                already_imm,
                facts + [{"field": "eviction_notice_type", "value": "judgment"}],
                ["zip_code", "household_gross_monthly_income"],
            )
        )
        self.assertEqual(a2_imm["result"]["need_updates"], [])


def _format_a1_readable(label: str, req: dict, out: dict) -> str:
    payload = req["payload"]
    res = out["result"]
    user_text = payload.get("story_text") or payload.get("answer_text") or ""
    lines = [
        "=================================================================",
        f"{label}",
        "=================================================================",
        f"Input Type : {req['task_type']} (ref_date: {payload.get('ref_date')})",
        f'User Input : "{user_text}"',
    ]
    if "pending_fact_keys" in payload:
        lines.append(f"Pending Keys: {payload['pending_fact_keys']}")

    lines.append("\nActual Output:")

    if "narrative_summary" in res:
        lines.append(f"  * Narrative Summary : {res['narrative_summary']}")

    needs = res.get("proposed_needs", [])
    if needs:
        lines.append("  * Proposed Needs    :")
        for n in needs:
            lines.append(
                f"      - [{n['category']}] urgency={n['urgency']} | "
                f"desc=\"{n['description']}\" | reason=\"{n['urgency_reason']}\""
            )
    else:
        lines.append("  * Proposed Needs    : [] (None)")

    facts = res.get("factual_claims", [])
    if facts:
        lines.append("  * Extracted Facts   :")
        for f in facts:
            tc = f" (time_context: {f['time_context']})" if f.get("time_context") else ""
            lines.append(f"      - {f['field']} = {repr(f['value'])}{tc}")
    else:
        lines.append("  * Extracted Facts   : [] (None)")

    flags = res.get("safety_or_official_deadline_flags", [])
    if flags:
        lines.append("  * Safety Flags      :")
        for fl in flags:
            lines.append(
                f"      - type={fl['type']} | quote=\"{fl['quote']}\" | note=\"{fl['note']}\""
            )
    else:
        lines.append("  * Safety Flags      : [] (None)")

    lines.append(f"  * Triggering Events : {res.get('triggering_events', [])}")
    amb = res.get("ambiguity_flags", [])
    amb_notes = [a.get("note") for a in amb if isinstance(a, dict)]
    lines.append(f"  * Ambiguity Flags   : {amb_notes}")

    return "\n".join(lines)


def _format_a2_readable(label: str, req: dict, out: dict) -> str:
    payload = req["payload"]
    reqs = out.get("clarification_requests", [])
    known = {f["field"]: f["value"] for f in payload.get("case_facts", [])}
    lines = [
        "=================================================================",
        f"{label}",
        "=================================================================",
        "Input Type : clarify_case",
        f"Known Facts: {known}",
        f"Already Asked: {payload.get('already_asked', [])}",
        f"\nActual Output (Status: {out['status']}):",
    ]
    updates = out.get("result", {}).get("need_updates", [])
    if updates:
        lines.append("  * Need Updates:")
        for u in updates:
            lines.append(
                f"      - {u['need_id']} -> urgency={u['urgency']} | reason=\"{u['urgency_reason']}\""
            )
    else:
        lines.append("  * Need Updates: [] (None)")
    if reqs:
        for idx, q in enumerate(reqs, 1):
            lines.append(
                f"  {idx}. [{q['fact_key']}] (can_skip={q['can_skip']}, necessity_level={q['necessity_level']})\n"
                f"     Question: \"{q['user_facing_question']}\"\n"
                f"     Reason  : {q['reason']}"
            )
    elif not updates:
        lines.append("  * No further clarification questions.")
    return "\n".join(lines)


if __name__ == "__main__":
    print("REAL INPUT / OUTPUT VERIFICATION FOR SLAV & JULIA (12 ITEMS)\n")

    samples = [
        (
            "Item 1a — Verbal Lockout Threat (Urgency = high, No Safety Flag)",
            _req_a1("My landlord threatened to lock us out if we don't pay rent."),
        ),
        (
            "Item 1b — Lock Change Threat (Urgency = high)",
            _req_a1("My landlord said he will change the locks tomorrow."),
        ),
        (
            "Item 3 & 4a — Actual Lockout ('We were locked out' -> eviction_notice_type='lockout')",
            _req_a1("We were locked out of our apartment yesterday."),
        ),
        (
            "Item 3 & 4b — Actual Lockout ('I got locked out' -> eviction_notice_type='lockout')",
            _req_a1("I got locked out of my apartment by the landlord."),
        ),
        (
            "Item 5 — Landlord Harm Threat (Raises Safety Flag + Housing Need)",
            _req_a1("My landlord threatened to hurt us if we don't leave."),
        ),
        (
            "Item 6 & 7a — Vague Food Problem (Urgency = high, Plain Description)",
            _req_a1("I have problems with food."),
        ),
        (
            "Item 6 & 7b — Vague Housing Problem (Urgency = high, Plain Description)",
            _req_a1("I have problems with housing."),
        ),
        (
            "Item 8 & 9 — Food Bank Mention Without Need Signal (No False Food Need)",
            _req_clarify(
                "We got some food from the food bank last week, income is $900.",
                ["household_gross_monthly_income"],
            ),
        ),
        (
            "Item 10 — Bereavement (Triggering Event Only, No employment_status or Income Need)",
            _req_a1("My husband passed away last month and we need help with rent."),
        ),
        (
            "Item 11 — Rent Due Date Extracted From Clarification Answer",
            _req_clarify(
                "Our ZIP is 95823 and income is $1,200. Rent is $1,200 due on November 1st.",
                ["zip_code"],
                ref_date="2026-10-25",
            ),
        ),
        (
            "Item 12 — Extra Stated Facts Extracted When Only ZIP Was Pending",
            _req_clarify(
                "We live in 95823 and our income is $1,000. The notice date is November 6, 2026, and the amount due is $1,600.",
                ["zip_code"],
            ),
        ),
    ]

    for label, req in samples:
        out = handle_agent_1(req)
        print(_format_a1_readable(label, req, out))
        print()

    a1_threat = handle_agent_1(_req_a1("My landlord threatened to lock us out if we don't pay rent."))
    a2_req = _req_a2(
        a1_threat["result"]["proposed_needs"],
        [
            {"field": "zip_code", "value": "95823"},
            {"field": "household_gross_monthly_income", "value": 1000},
        ],
        ["zip_code", "household_gross_monthly_income"],
    )
    a2_out = handle_agent_2(a2_req)
    print(
        _format_a2_readable(
            "Item 2 — Agent 2 Threat Clarifying Questions (Max 2 Unknowns, Skippable)",
            a2_req,
            a2_out,
        )
    )

    print("\nREAL INPUT / OUTPUT VERIFICATION FOR SLAV'S FOLLOW-UP ITEMS\n")

    followup_samples = [
        (
            "Follow-up 1 — Move-Out Date Stored in specific_move_out_date (Not eviction_notice_date)",
            _req_clarify(
                "He said we must leave by November 30.",
                ["specific_move_out_date"],
                ref_date="2026-11-01",
            ),
        ),
        (
            "Follow-up 2a — 'Yes' to Court Judgment Sets eviction_notice_type='judgment'",
            _req_clarify("Yes, there is a court judgment.", ["has_court_writ_or_judgment"]),
        ),
        (
            "Follow-up 2b — 'Yes' to Active Lock Change Sets eviction_notice_type='lockout'",
            _req_clarify(
                "Yes, he is changing the locks right now.", ["imminent_removal_in_progress"]
            ),
        ),
        (
            "Follow-up 4 — Neutral Safety Note on Landlord Harm Threat",
            _req_a1("My landlord threatened to hurt us if we don't leave."),
        ),
        (
            "Follow-up 6 — Reduced Work Hours Proposes income_assistance (urgency='high')",
            _req_a1("My hours were cut at work last month and I can't pay rent."),
        ),
        (
            "Commit 2 Item 4 — 'My pay was cut by half.' Emits reduced_hours + income_assistance",
            _req_a1("My pay was cut by half."),
        ),
    ]
    for label, req in followup_samples:
        out = handle_agent_1(req)
        print(_format_a1_readable(label, req, out))
        print()

    ans_court = handle_agent_1(
        _req_clarify("Yes, there is a court judgment.", ["has_court_writ_or_judgment"])
    )
    a2_escalate_req = _req_a2(
        a1_threat["result"]["proposed_needs"],
        [
            {"field": "zip_code", "value": "95823"},
            {"field": "household_gross_monthly_income", "value": 1000},
        ]
        + ans_court["result"]["factual_claims"],
        [
            "zip_code",
            "household_gross_monthly_income",
            "has_written_eviction_notice",
            "has_court_writ_or_judgment",
        ],
    )
    print(
        _format_a2_readable(
            "Follow-up 2c — Agent 2 need_updates Escalates Housing to 'immediate'",
            a2_escalate_req,
            handle_agent_2(a2_escalate_req),
        )
    )
    print()

    a2_no_repeat_req = _req_a2(
        [{"need_id": "need_001", "category": "housing_assistance", "urgency": "high"}],
        [{"field": "zip_code", "value": "95823"}],
        ["zip_code", "household_gross_monthly_income"],
    )
    print(
        _format_a2_readable(
            "Commit 2 Items 3 & 5 — Income Never Repeated & need_updates Empty When Unchanged",
            a2_no_repeat_req,
            handle_agent_2(a2_no_repeat_req),
        )
    )