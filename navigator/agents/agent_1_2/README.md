# AI Community Aid Navigator — Component Slice: Agent 1 & Agent 2 (v6.1 Release)

**Component Owner:** Yogesh Kushwaha (Agents 1 & 2)  
**Contract Baseline:** Shared JSON Contracts v1.1  
**Target Pilot:** Sacramento County, California (Emergency Housing & Food Relief)

---

## 1. Overview & Architecture Boundaries

This component slice implements the front-line cognitive intake, crisis understanding, uncertainty-preserving slot filling, and 4-gate clarification filtering for the **AI Community Aid Navigator (Sacramento Pilot)**:

* **Agent 1 (`understand_story` & `parse_clarification_answer`):**
  * Ingests unstructured, emotional crisis narratives from residents.
  * **Rule 19.1 Strict Non-Inference:** Extracts only explicitly stated needs across standard categories (`income_assistance`, `housing_assistance`, `food_assistance`, `utility_assistance`, `medical_health_coverage`, `debt_hardship`, `material_in_kind`).
  * **Overdue Rent Date Preservation:** Named dates up to ~6 months in the past relative to `ref_date` stay in that past year and are designated with `time_context: "user-stated date, overdue"`.
  * **Widened Life-Safety Signal Detection:** Flags acute distress signals (suicide/self-harm ideation, domestic violence, home safety hazards, threats from/to others) into `safety_or_official_deadline_flags`.
  * **Emergency Car Sleeping Support:** Recognizes acute homelessness (e.g., `"sleeping in our car"`) as `NeedCategory.HOUSING_ASSISTANCE` with `subcategory: "emergency_shelter"` and `urgency: "immediate"`.
  * **Monthly Household Income Extraction:** Extracts current monthly gross income when stated (`household_gross_monthly_income`), captures `0` when stated as zero, and preserves unknowns when unstated.
  * **Input Validation & Specific Issue Codes:** Rejects invalid `ref_date` values, missing payloads, or null/empty story narratives with structured `status: "failed"` envelopes.
* **Agent 2 (`clarify_case`):**
  * **4-Gate Question Filter (Rule 19.2):** Suppresses candidate questions if already known (Gate 1), already asked (Gate 2), lacking a `verified_rule_ref` (Gate 3), or non-material (Gate 4).
  * **Pacing Ceiling (§30.8):** Enforces at most 1 question cluster ($\le 2$ questions) per turn.
  * **Neutral Food Check (§19.1):** Sets `optional_food_check = True` only when acute income disruption occurs and food assistance was not explicitly mentioned.

---

## 2. Test Execution

From repository root:
```bash
python -m unittest discover -s tests -t .
```
