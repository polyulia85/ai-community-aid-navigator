# Agents 3, 4, 5: Retrieval, Matching, Verification (owner: Silver) — v1.5

Shared JSON Contracts v1.1 (agent results still carry schema_version "1.0", as in v1.0); task_type retrieve_candidates / match_resources / verify_resources. Python 3.11+, standard library only.

| File | Agent | What it does |
|---|---|---|
| `agent_3.py` | 3 Retrieval | Finds KB programs whose category matches each need and whose service area covers the person's county. Subcategory orders results but does not filter them. Empty results are reported as `COVERAGE_GAP`; it never invents programs. Verified KB only (external discovery is P2). |
| `agent_4.py` | 4 Matching | Preliminary fit: `potential_match` / `supported_match` / `confirmed_mismatch` / `insufficient_information`. Reads only its inputs: `program_criteria[]` comes from the Supervisor. Unknown income is never a mismatch; it is listed in `missing_case_facts`, and (decision 9, proposed) keeps the result at `potential_match`. |
| `agent_5.py` | 5 Verification | Reports each claim's status from the EvidenceRecords. Missing values come back `unverified` and empty, conflicting sources stay separate, and it never edits the KB. |

Each module exposes `handle(request: dict) -> dict` (AgentRequest in, AgentResult out). `is_mock` is `true` until the logic is final.

**Run the tests** (from repo root): `python -m unittest discover tests -v` (20 tests)
**Regenerate samples:** `python navigator/samples/agent_3_4_5/make_samples.py`
**Rebuild / check the KB:** `python navigator/kb/tools/build_kb.py` then `python navigator/kb/tools/validate_kb.py`
**Review spreadsheet (optional):** `python navigator/kb/tools/make_sheet.py out.xlsx` needs `openpyxl`; it is not needed to run the agents.

**Knowledge Base (navigator/kb/kb_sacramento.json): 4 records, 113 EvidenceRecords (published Nov 2, 2026)**
| program_id | category / subcategory | availability |
|---|---|---|
| prog_food_calfresh_sac_001 | food_assistance / calfresh_benefits | confirmed_open |
| prog_income_edd_ui_ca_001 | income_assistance / unemployment_insurance | confirmed_open |
| prog_housing_saintjohns_sac_001 | housing_assistance / rental_assistance | confirmed_open (reopened Nov 2; online form via the page's APPLY HERE link) |
| prog_housing_coordaccess_sac_001 | housing_assistance / eviction_prevention | confirmed_open (2-1-1 press 8 access route; help not guaranteed) |

**Geography:** records use service areas ("Sacramento County"); statewide programs use "California" and cover all 58 California counties. The Supervisor passes ZIP and county; a ZIP-only request falls back to a local Sacramento ZIP stub.

**Input errors (Slav, Oct 25)** are reported as errors, never as gaps or incomplete data:
| Issue code | When | Status |
|---|---|---|
| `UNKNOWN_CATEGORY` (Agent 3) | need category not in the v1.0 list, e.g. "housing" | `partial`, or `failed` if no valid need |
| `UNSUPPORTED_TASK` (Agents 3-5) | wrong task_type for the agent | `failed` |
| `UNKNOWN_PROGRAM` (Agent 5) | program_id not in the KB | `partial`, or `failed` if none known |
| `COUNTY_FROM_ZIP_FALLBACK` (Agents 3-4) | ZIP given without a county; county taken from the local fallback | warning only |

**Nov 2 update (Saint John's reopening):** published Nov 2, 2026 after checking the official pages and built in permanently by `build_kb.py`; replaced rows are in `navigator/kb/history/superseded_evidence.json` (rebuilt each run, no duplicates). Claim values quote the page verbatim; conclusions drawn from them (e.g. Saint John's `confirmed_open`) are labeled as inferences in `notes`.

**Changes in v1.5 (Nov 3):** ev_sjhap_020/021 claim values are verbatim page text, inference moved to notes; ev_calfresh_020 source is the CDSS page with the 2026–2027 waiver list; KB header says contracts v1.1; staged Nov 2 draft and checklist removed (done).

**Same-page rule (Nov 2):** on one source page, statements about different dates (e.g. "closed now" + "reopens Nov 2") are complementary; two different values for the same field with no date difference are `conflicting`.

**Known limits:**
- Agent 4 does not compare income against limits; dollar thresholds must not be hard-coded (TD 24.1).
- `build_program_criteria_from_kb()` in `common.py` is for local tests only; it stands in for the Supervisor.
