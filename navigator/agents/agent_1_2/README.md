# AI Community Aid Navigator — Component Slice: Agent 1 & Agent 2 (v6.2 Release)

**Component Owner:** Yogesh Kushwaha (Agents 1 & 2)  
**Contract Baseline:** Shared JSON Contracts v1.1  
**Target Pilot:** Sacramento County, California (Emergency Housing & Food Relief)

---

## 1. Overview & Architecture Boundaries (v6.2)

This component slice implements the front-line cognitive intake, crisis understanding, uncertainty-preserving slot filling, and 4-gate clarification filtering for the **AI Community Aid Navigator (Sacramento Pilot)**:

* **Agent 1 (`understand_story` & `parse_clarification_answer`):**
  * Ingests unstructured, emotional crisis narratives from residents.
  * **Rule 19.1 Strict Non-Inference:** Extracts only explicitly stated needs across standard categories (`income_assistance`, `housing_assistance`, `food_assistance`, `utility_assistance`, `medical_health_coverage`, `debt_hardship`, `material_in_kind`).
  * **Expanded Life-Safety Signal Detection:** Flags acute distress signals into `safety_or_official_deadline_flags`. Coverage includes:
    * Self-harm / suicide ideation (`"I want to kill myself"`, `"ending it all"`, `"no reason to live"`, etc.)
    * Threats from others — `he`, `she`, or `they` — including `"scared [he/she/they] will come back and hurt us"`, `"[he/she/they] will come back"`, `"[he/she/they] will hurt us"`, and `"come back and hurt us"`
    * Threats to others (`"I'm going to hurt him"`, `"might hurt someone"`)
    * Domestic violence phrases (partner hits/beats/struck the user or children)
    * Structural home-safety signals (`"unsafe at home"`, `"danger at home"`)
  * **Overdue Rent Preservation:** Named rent dates up to ~6 months in the past relative to `ref_date` stay tagged as overdue; `urgency: "immediate"` is set on the housing need.
  * **Immediate Urgency Escalation:** Overdue rent dates and affirmative eviction notices both escalate `housing_assistance` urgency to `"immediate"`.
  * **Monthly Household Income Extraction:** Extracts current monthly gross income when stated (`household_gross_monthly_income`); captures approximate values with `is_approximate: true`; captures explicit `0` when stated as zero income; preserves unknowns when unstated.
  * **`time_context: null` on `has_written_eviction_notice`:** The eviction-notice boolean fact carries `time_context: null` (not a user-stated date). Only `rent_due_date` carries `"user-stated date, not an official deadline"`.
  * **Typographic Quote Normalisation:** Curly/typographic apostrophes (`'`, `'`) and quotes (`"`, `"`) are normalised to straight ASCII before any pattern matching, ensuring safety and negation patterns fire correctly.
  * **Input Validation & Specific Issue Codes:** Rejects invalid `ref_date` values, missing payloads, or null/empty story narratives with structured `status: "failed"` envelopes.
* **Agent 2 (`clarify_case`):**
  * **4-Gate Question Filter (Rule 19.2):** Suppresses candidate questions if already known (Gate 1), already asked/declined (Gate 2 — checked immediately at the start of each candidate loop iteration), lacking a `verified_rule_ref` (Gate 3), or non-material (Gate 4).
  * **Strict Gate 2 Deduplication:** `already_asked` keys are checked before any other gate, preventing any re-ask of declined questions regardless of other conditions.
  * **Conditional Income Question:** `household_gross_monthly_income` is only asked when income is unknown, not already asked, AND no `candidate_requirements` are provided. When `candidate_requirements` are present, income appears only if the KB-verified requirement includes it.
  * **Eviction Notice Clarification Behavior:**
    * When `has_written_eviction_notice` is `True` in `case_facts` (user already confirmed receiving a notice), Agent 2 does **not** re-ask the boolean. Instead, it asks only for the document type and date: `"What type of eviction notice did you receive (such as a 3-day notice), and what date is listed on it?"` (`fact_key: "eviction_notice_type"`, `can_skip: False`).
    * When `has_written_eviction_notice` is `False`, no eviction question is asked.
  * **Approved Fact Keys Only:** Uses only approved contract keys. The unapproved key `eviction_notice_details` is not emitted; eviction follow-up uses `eviction_notice_type`.
  * **KB-Verified References Only:** `verified_rule_ref` is taken from the candidate requirement or set to `None`. Hardcoded fabricated references (`"ev_legal_evict_002"`, `"rule_eviction_timeline_01"`, `"rule_income_verification_baseline"`, `"prog_legal_aid_eviction"`) are not used. `applicable_program_ids` is `[program_id]` when a program is present, otherwise `[]`.
  * **Pacing Ceiling (§30.8):** Enforces at most 1 question cluster (≤ 2 questions) per turn.
  * **Neutral Food Check (§19.1):** Sets `optional_food_check = True` only when acute income disruption occurs and food assistance was not explicitly mentioned.

---

## 2. Test Execution

From repository root:
```bash
python -m unittest discover -s tests -t .
```
