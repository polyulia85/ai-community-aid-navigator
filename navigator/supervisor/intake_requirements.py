"""Evidence-backed prompts for pilot programs retrieved during intake."""

_PROGRAM_FIELDS = {
    "prog_food_calfresh_sac_001": (
        ("household_gross_monthly_income", "ev_calfresh_005"),
        ("household_size", "ev_calfresh_010"),
        ("cash_on_hand_approx", "ev_calfresh_015"),
        ("student_employability_program", "ev_calfresh_021"),
    ),
    "prog_housing_saintjohns_sac_001": (
        ("has_rental_agreement", "ev_sjhap_008"),
        ("household_gross_monthly_income", "ev_sjhap_005"),
    ),
    "prog_housing_salvationarmy_rent_sac_001": (
        ("has_written_eviction_notice", "ev_sarent_005"),
        ("household_gross_monthly_income", "ev_sarent_006"),
    ),
}
_HOUSING_TENANCY_FACTS = {"has_rental_agreement", "has_written_eviction_notice"}


def candidate_requirements(state, candidates, evidence):
    """Return applicable prompts backed by this candidate's verified KB criteria."""
    requirements = []
    no_shelter = any(n.get("subcategory") == "emergency_shelter" for n in state.needs)
    mortgage_only = any(n.get("subcategory") == "mortgage_assistance" for n in state.needs) and all(
        n.get("subcategory") == "mortgage_assistance"
        for n in state.needs if n.get("category") == "housing_assistance"
    )
    income = state.fact("household_gross_monthly_income")
    food_urgent = state.fact("food_needed_by_tomorrow") is True or any(n.get("category") == "food_assistance" and n.get("urgency") == "immediate"
                      for n in state.needs)
    for candidate in candidates:
        program_id = candidate["program_id"]
        for field, ref in _PROGRAM_FIELDS.get(program_id, ()):
            record = evidence.get(ref, {})
            if (record.get("program_id") != program_id
                    or record.get("verification_status") != "verified"
                    or not record.get("field_path", "").startswith("eligibility_criteria")):
                continue
            if field in _HOUSING_TENANCY_FACTS and (no_shelter or mortgage_only):
                continue
            if field == "cash_on_hand_approx" and not (food_urgent or (isinstance(income, (int, float)) and income < 150)):
                continue
            if field == "student_employability_program" and state.fact("is_college_student") is not True:
                continue
            requirements.append({"program_id": program_id, "fact_key": field,
                                 "verified_rule_ref": ref, "can_skip": True})
    return requirements
