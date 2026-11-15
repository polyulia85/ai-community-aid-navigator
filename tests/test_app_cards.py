"""Regression coverage for the local UI's Supervisor response."""
import unittest

from navigator.supervisor import dialog
from navigator.supervisor.card_details import for_released_cards


class TestCardDetails(unittest.TestCase):
    def test_verified_sacramento_dialog(self):
        result = dialog.start(
            "I live in Sacramento ZIP code 95823 with my two children. "
            "I lost my job. I need food this week and help paying $1,450 rent.",
            ref_date="2026-11-14",
        )
        answers = {
            "household_gross_monthly_income": "My household gross monthly income is $900.",
            "household_size": "There are 3 people in my household.",
            "has_rental_agreement": "Yes",
            "has_written_eviction_notice": "No",
            "rent_shortfall_amount": "400",
            "rent_due_date": "December 1",
            "food_needed_by_tomorrow": "Yes",
            "cash_on_hand_approx": "20",
        }
        asked = {}
        while result["status"] == "needs_clarification":
            for q in result["questions"]:
                self.assertNotIn(q["fact_key"], asked)
                asked[q["fact_key"]] = q["verified_rule_ref"]
            result = dialog.answer(result["case"], [
                {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                for q in result["questions"]
            ])
        self.assertEqual(asked, {
            "household_gross_monthly_income": "ev_calfresh_005",
            "household_size": "ev_calfresh_010",
            "has_rental_agreement": "ev_sjhap_008",
            "has_written_eviction_notice": "ev_sarent_005",
            "rent_shortfall_amount": None,
            "rent_due_date": None,
            "food_needed_by_tomorrow": None,
            "cash_on_hand_approx": "ev_calfresh_015",
        })
        self.assertEqual(result["status"], "needs_confirmation")
        rent_facts = {f["field"]: f["value"] for f in result["summary"]["facts"]}
        self.assertEqual(rent_facts["rent_shortfall_amount"], 400)
        self.assertEqual(rent_facts["rent_due_date"], "2026-12-01")
        self.assertNotIn("eviction_notice_date", rent_facts)
        result = dialog.confirm(result["case"], corrections={"household_gross_monthly_income": 950})
        self.assertEqual(result["status"], "completed", result["issues"])
        self.assertEqual(result["final_validation"]["verdict"], "PASS")
        self.assertEqual(next(f["value"] for f in result["case"]["case_facts"]
                              if f["field"] == "household_gross_monthly_income"), 950)
        cards = result["plan"]["action_cards"]
        by_id = {card["card_id"]: card for card in cards}
        self.assertEqual(set(by_id), {cid for need in result["plan_by_need"] for cid in need["card_ids"]})
        food = next(need for need in result["plan_by_need"] if need["category"] == "food_assistance")
        self.assertGreater(len(food["card_ids"]), 1)
        for card_id, details in result["card_details"].items():
            self.assertTrue(all(source["program_id"] == by_id[card_id]["program_id"]
                                for source in details["sources"]))
        for title in ("CalFresh", "Sacramento Steps Forward"):
            card = next(card for card in cards if title in card["action_title"])
            details = result["card_details"][card["card_id"]]
            for section in ("conditions", "documents", "steps", "contacts", "sources"):
                self.assertTrue(details[section], (title, section))
            for section in ("conditions", "documents", "steps", "contacts"):
                source_ids = {source["evidence_id"] for source in details["sources"]}
                for item in details[section]:
                    self.assertTrue(item["evidence_refs"])
                    self.assertLessEqual(set(item["evidence_refs"]), source_ids)

    def test_student_without_shelter_gets_an_optional_food_question(self):
        result = dialog.start("My parents just passed out and I'm a freshman university "
                              "student, I have no money and home.", ref_date="2026-11-14")
        self.assertEqual(result["questions"][0]["fact_key"], "has_safe_place_tonight")
        basic = {
            "has_safe_place_tonight": "No", "zip_code": "95814",
            "household_gross_monthly_income": "0",
        }
        while result["questions"][0]["fact_key"] != "needs_food_help":
            result = dialog.answer(result["case"], [
                {"question_id": q["question_id"], "answer_text": basic[q["fact_key"]]}
                for q in result["questions"]
            ])
        question = result["questions"][0]
        self.assertTrue(question["can_skip"])
        for answer in ("Yes", "No, I don't need help with food."):
            follow = dialog.answer(result["case"], [
                {"question_id": question["question_id"], "answer_text": answer}
            ])
            asked = set()
            while follow["status"] == "needs_clarification":
                values = {"household_size": "1", "cash_on_hand_approx": "20",
                          "student_employability_program": "No", "food_needed_by_tomorrow": "Yes"}
                asked.update(q["fact_key"] for q in follow["questions"])
                follow = dialog.answer(follow["case"], [
                    {"question_id": q["question_id"], "answer_text": values[q["fact_key"]]}
                    for q in follow["questions"]
                ])
            self.assertEqual(follow["status"], "needs_confirmation")
            needs = {n["category"]: n for n in follow["summary"]["needs"]}
            facts = {f["field"]: f["value"] for f in follow["summary"]["facts"]}
            self.assertEqual(needs["housing_assistance"]["description"], "No stable overnight shelter")
            self.assertIs(facts["has_safe_place_tonight"], False)
            self.assertEqual("food_assistance" in needs, answer == "Yes")
            if answer == "Yes":
                self.assertEqual(asked, {"household_size", "cash_on_hand_approx",
                                         "student_employability_program", "food_needed_by_tomorrow"})
                self.assertEqual(facts["cash_on_hand_approx"], 20)
            else:
                self.assertFalse(asked)

    def test_food_only_does_not_ask_about_rent_or_tax_returns(self):
        result = dialog.start("I lost my job. I need food. My ZIP code is 95823.",
                              ref_date="2026-11-14")
        answers = {"household_size": "1", "household_gross_monthly_income": "0",
                   "cash_on_hand_approx": "90,000", "needs_housing_help": "No",
                   "food_needed_by_tomorrow": "No"}
        asked = set()
        while result["status"] == "needs_clarification":
            for q in result["questions"]:
                self.assertNotIn(q["fact_key"], asked)
                asked.add(q["fact_key"])
            result = dialog.answer(result["case"], [
                {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                for q in result["questions"]
            ])
        self.assertEqual(result["status"], "needs_confirmation")
        self.assertEqual(asked, set(answers))
        facts = {f["field"]: f["value"] for f in result["summary"]["facts"]}
        self.assertEqual(facts["cash_on_hand_approx"], 90000)
        self.assertEqual(facts["household_gross_monthly_income"], 0)
        self.assertEqual(facts["zip_code"], "95823")

    def test_short_job_loss_story_discovers_food_and_housing(self):
        for answer in ("Yes", "No"):
            result = dialog.start("I lost my job, and I have two children.", ref_date="2026-11-14")
            answers = {
                "zip_code": "95814", "household_gross_monthly_income": "0",
                "needs_food_help": answer, "needs_housing_help": answer, "household_size": "3",
                "cash_on_hand_approx": "20", "has_rental_agreement": "Yes",
                "has_written_eviction_notice": "No", "rent_shortfall_amount": "400",
                "rent_due_date": "December 1", "food_needed_by_tomorrow": "Yes",
            }
            asked = []
            while result["status"] == "needs_clarification":
                asked.extend(q["fact_key"] for q in result["questions"])
                result = dialog.answer(result["case"], [
                    {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                    for q in result["questions"]
                ])
            self.assertEqual(result["status"], "needs_confirmation")
            self.assertEqual(asked[:4], list(answers)[:4])
            self.assertEqual(len(asked), len(set(asked)))
            expected = {"income_assistance"}
            if answer == "Yes":
                expected |= {"food_assistance", "housing_assistance"}
                self.assertEqual(set(asked), set(answers))
            else:
                self.assertEqual(len(asked), 4)
            self.assertEqual({n["category"] for n in result["summary"]["needs"]}, expected)
            result = dialog.confirm(result["case"])
            self.assertEqual(result["status"], "completed")
            self.assertEqual({g["category"] for g in result["plan_by_need"]}, expected)

    def test_rent_shortfall_and_due_date_are_preserved_without_reasking(self):
        result = dialog.start("I was laid off. My rent is due December 1 and I am $450.50 short.",
                              ref_date="2026-11-15")
        answers = {"zip_code": "95814", "household_gross_monthly_income": "0",
                   "needs_food_help": "No", "has_rental_agreement": "Yes",
                   "has_written_eviction_notice": "No"}
        while result["status"] == "needs_clarification":
            result = dialog.answer(result["case"], [
                {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                for q in result["questions"]
            ])
        self.assertEqual(result["status"], "needs_confirmation")
        facts = {f["field"]: f for f in result["summary"]["facts"]}
        self.assertEqual(facts["rent_shortfall_amount"]["value"], 450.5)
        self.assertEqual(facts["rent_shortfall_amount"]["display_value"], "$450.50")
        self.assertEqual(facts["rent_due_date"]["value"], "2026-12-01")
        self.assertNotIn("rent_amount_monthly", facts)
        self.assertNotIn("eviction_notice_date", facts)
        result = dialog.confirm(result["case"])
        self.assertEqual(result["status"], "completed")
        housing = next(g for g in result["plan_by_need"] if g["category"] == "housing_assistance")
        self.assertTrue(housing["card_ids"])
        for card in result["plan"]["action_cards"]:
            if card["card_id"] in housing["card_ids"]:
                self.assertEqual(card["user_target_date"], "2026-12-01")
                self.assertNotEqual(card["official_deadline"], "2026-12-01")

    def test_demo_plan_starts_with_food_distribution_while_benefits_run_in_parallel(self):
        result = dialog.start(
            "I'm a single mother in Sacramento ZIP code 95823 with two kids, ages 6 and 9. "
            "I was laid off from my warehouse job on Friday. Rent of $1,450 is due December 1. "
            "I have about $300 left and we're running low on food.",
            ref_date="2026-11-15",
        )
        answers = {"household_gross_monthly_income": "0", "has_rental_agreement": "Yes",
                   "has_written_eviction_notice": "No", "rent_shortfall_amount": "1150",
                   "food_needed_by_tomorrow": "Yes"}
        while result["status"] == "needs_clarification":
            result = dialog.answer(result["case"], [
                {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                for q in result["questions"]
            ])
        self.assertEqual(result["status"], "needs_confirmation", result["issues"])
        result = dialog.confirm(result["case"])
        self.assertEqual(result["status"], "completed", result["issues"])
        self.assertEqual(result["final_validation"]["verdict"], "PASS")
        cards = result["plan"]["action_cards"]
        self.assertEqual(len(cards), 11)
        self.assertEqual(sum(card["order_group"] == "first" for card in cards), 1)
        self.assertEqual(cards[0]["order_group"], "first")
        self.assertEqual(result["card_details"][cards[0]["card_id"]]["subcategory"], "food_pantry")
        self.assertIn("immediate need for food", cards[0]["priority_reason"])
        self.assertEqual(cards[0]["official_deadline"], None)
        self.assertTrue(all(c["order_group"] == "parallel" for c in cards[1:]))

    def test_paid_rent_and_skipped_meals_route_to_food(self):
        result = dialog.start(
            "I paid the rent yesterday. My manager took me off the schedule this week, "
            "and my next paycheck won’t come until Friday. I’ve been skipping dinner so my kids can eat. "
            "I’m not sure how long we can stretch what’s left. Where should I start?",
            ref_date="2026-11-15",
        )
        answers = {
            "triggering_circumstances": "I'm still employed. I used most of my last paycheck "
                                        "to cover rent, so there's very little left for groceries.",
            "zip_code": "95814", "household_gross_monthly_income": "1200", "household_size": "3",
            "food_needed_by_tomorrow": "Yes, we need food tomorrow morning.", "cash_on_hand_approx": "50",
        }
        asked = set()
        for _ in range(len(answers)):
            if result["status"] != "needs_clarification":
                break
            asked.update(q["fact_key"] for q in result["questions"])
            result = dialog.answer(result["case"], [
                {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                for q in result["questions"]
            ])
        self.assertIn("food_needed_by_tomorrow", asked)
        self.assertEqual(result["status"], "needs_confirmation")
        self.assertEqual([n["category"] for n in result["summary"]["needs"]], ["food_assistance"])
        result = dialog.confirm(result["case"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["final_validation"]["verdict"], "PASS")
        first = result["plan"]["action_cards"][0]
        self.assertEqual(first["order_group"], "first")
        self.assertEqual(result["card_details"][first["card_id"]]["subcategory"], "food_pantry")

    def test_mortgage_plan_uses_relevant_evidence_and_notice_priority(self):
        for notice, expected_group in (("Yes", "first"), ("No", "parallel")):
            with self.subTest(notice=notice):
                result = dialog.start("I won't be able to make my next mortgage payment.",
                                      ref_date="2026-11-15")
                answers = {
                    "zip_code": "95823",
                    "household_gross_monthly_income": "900",
                    "mortgage_due_date": "2026-12-01",
                    "mortgage_payment_overdue": "No",
                    "has_written_mortgage_notice": notice,
                }
                asked = set()
                for _ in range(len(answers)):
                    if result["status"] != "needs_clarification":
                        break
                    asked.update(q["fact_key"] for q in result["questions"])
                    result = dialog.answer(result["case"], [
                        {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                        for q in result["questions"]
                    ])
                self.assertEqual(asked, set(answers))
                self.assertEqual(result["status"], "needs_confirmation")
                result = dialog.confirm(result["case"])
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["final_validation"]["verdict"], "PASS")
                card, = result["plan"]["action_cards"]
                self.assertEqual(card["program_id"], "prog_housing_saintjohns_sac_001")
                self.assertIn("mortgage payment help", card["action_title"])
                self.assertIn("ev_sjhap_001", card["source_refs"])
                self.assertEqual(card["order_group"], expected_group)
                self.assertEqual(card["user_target_date"], "2026-12-01")
                self.assertIsNone(card["official_deadline"])
                details = result["card_details"][card["card_id"]]
                self.assertEqual(details["subcategory"], "mortgage_assistance")
                self.assertNotIn("rental or lease agreement", str(details))

    def test_house_payment_hardship_survives_unknown_food_timing(self):
        result = dialog.start(
            "Hello, I have a big family of 3 kids and I have financial problems such as "
            "lack of money to pay for house and food. What do I do?",
            ref_date="2026-11-15",
        )
        answers = {
            "triggering_circumstances": "I don't know",
            "zip_code": "95823",
            "household_gross_monthly_income": "900",
            "household_size": "3",
            "has_rental_agreement": "Yes",
            "has_written_eviction_notice": "No",
            "rent_shortfall_amount": "400",
            "rent_due_date": "2026-12-01",
            "food_needed_by_tomorrow": "I don't know",
        }
        asked = set()
        for _ in range(len(answers)):
            if result["status"] != "needs_clarification":
                break
            asked.update(q["fact_key"] for q in result["questions"])
            result = dialog.answer(result["case"], [
                {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                for q in result["questions"]
            ])
        self.assertEqual(result["status"], "needs_confirmation", result["issues"])
        self.assertEqual(asked, set(answers))
        self.assertEqual({n["category"] for n in result["summary"]["needs"]},
                         {"food_assistance", "housing_assistance"})
        self.assertIn("food_needed_by_tomorrow",
                      {item["field"] for item in result["summary"]["unknown"]})
        result = dialog.confirm(result["case"])
        self.assertEqual(result["status"], "completed", result["issues"])
        self.assertEqual(result["final_validation"]["verdict"], "PASS")
        cards = result["plan"]["action_cards"]
        self.assertTrue(any("Food Bank" in card["action_title"] for card in cards))
        self.assertTrue(any("rent help" in card["action_title"] for card in cards))
        self.assertFalse(any(card["order_group"] == "first" for card in cards))

    def test_food_timing_changes_which_action_is_first(self):
        for response, expected in (("Tomorrow", "first"), ("No, we have enough for three weeks.", "parallel")):
            with self.subTest(response=response):
                result = dialog.start("I lost my job and need help with groceries. ZIP 95823.",
                                      ref_date="2026-11-15")
                answers = {"household_gross_monthly_income": "900", "household_size": "3",
                           "needs_housing_help": "No", "food_needed_by_tomorrow": response}
                asked = []
                while result["status"] == "needs_clarification":
                    asked.extend(q["fact_key"] for q in result["questions"])
                    result = dialog.answer(result["case"], [
                        {"question_id": q["question_id"], "answer_text": answers.get(q["fact_key"], "20")}
                        for q in result["questions"]
                    ])
                self.assertEqual(result["status"], "needs_confirmation", result["issues"])
                self.assertEqual(asked.count("food_needed_by_tomorrow"), 1)
                result = dialog.confirm(result["case"])
                self.assertEqual(result["status"], "completed", result["issues"])
                cards = result["plan"]["action_cards"]
                if expected == "first":
                    self.assertEqual(cards[0]["order_group"], "first")
                    self.assertEqual(result["card_details"][cards[0]["card_id"]]["subcategory"], "food_pantry")
                else:
                    self.assertFalse(any(c["order_group"] == "first" for c in cards))
                cal_fresh = next(c for c in cards if "CalFresh" in c["action_title"])
                self.assertEqual(cal_fresh["order_group"], "parallel")

    def test_safety_banner_and_explicit_safe_shelter_need_can_reach_plan(self):
        for story in (
            "My partner hits me. I need help finding a safe place to stay.",
            "My husband hits me. I want to leave with my two children, but I don't have any money.",
        ):
            with self.subTest(story=story):
                result = dialog.start(story, ref_date="2026-11-15")
                self.assertEqual(result["questions"][0]["fact_key"], "has_safe_place_tonight")
                answers = {"has_safe_place_tonight": "No", "zip_code": "95814",
                           "household_gross_monthly_income": "0", "needs_food_help": "No"}
                while result["status"] == "needs_clarification":
                    self.assertFalse(result["safety_notice"]["blocks_plan"])
                    result = dialog.answer(result["case"], [
                        {"question_id": q["question_id"], "answer_text": answers[q["fact_key"]]}
                        for q in result["questions"]
                    ])
                self.assertEqual(result["status"], "needs_confirmation", result["issues"])
                self.assertEqual(result["summary"]["needs"][0]["description"], "Needs a safe place to stay")
                self.assertEqual(result["summary"]["needs"][0]["urgency"], "immediate")
                result = dialog.confirm(result["case"])
                self.assertEqual(result["status"], "completed", result["issues"])
                self.assertFalse(result["safety_notice"]["blocks_plan"])
                self.assertEqual(result["final_validation"]["verdict"], "PASS")
                self.assertTrue(result["plan_by_need"][0]["card_ids"])

    def test_late_safety_signal_is_returned_before_the_other_question(self):
        result = dialog.start("I lost my job, and I have two children.", ref_date="2026-11-15")
        self.assertIsNone(result["safety_notice"])
        self.assertEqual(len(result["questions"]), 2)
        first, second = result["questions"]
        after = dialog.answer(result["case"], [{
            "question_id": first["question_id"],
            "answer_text": "My husband hits me. I'm in ZIP 95814.",
        }], keep_pending=True)
        self.assertEqual(after["status"], "needs_clarification")
        self.assertEqual(after["turn"], result["turn"])
        self.assertEqual(after["questions"], [second])
        self.assertNotIn(second["fact_key"], after["case"]["already_asked"])
        self.assertFalse(after["safety_notice"]["blocks_plan"])

    def test_excludes_unverified_and_cross_program_claims(self):
        path = "required_documents[0]"
        evidence = {
            "scoped": {"program_id": "p", "field_path": path, "claim_value": "ID",
                       "verification_status": "verified"},
            "other": {"program_id": "other", "field_path": path, "claim_value": "ID",
                      "verification_status": "verified"},
        }
        claim = {"program_id": "p", "field_path": path, "claim_value": "ID", "checked_at": "2026-11-01"}
        details = for_released_cards(
            [{"card_id": "card", "program_id": "p"}],
            [
                dict(claim, verification_status="needs_review", evidence_refs=["scoped"]),
                dict(claim, verification_status="verified", evidence_refs=["other"]),
            ],
            {"p": {}}, evidence,
        )
        self.assertEqual(details["card"]["documents"], [])
        self.assertEqual(details["card"]["sources"], [])
