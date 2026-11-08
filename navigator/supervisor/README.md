# Supervisor — AI Community Aid Navigator

Owner: Slav (Supervisor / Orchestrator and integration). Contract: `docs/contracts/SHARED_CONTRACTS.md` (v1.1, Oct 27, 2026). Version: v0.2.4 (Nov 7, 2026). Local Python prototype, standard library only (Python 3.11+); not yet connected to IBM watsonx Orchestrate.

## What it does

- **Runs one cycle:** Agent 1 → 2 → 3 → 4 → 5 → 6 → 8 → 10, with Agent 7 reviewing the retrieval, matching, verification and planning stages. Agents never call each other; every call is one AgentRequest and one AgentResult (contracts sections 1–2).
- **Builds every request** with only the facts that agent needs: S0 input masking before Agent 1; `ref_date` (ISO string, same value for the whole run) in the payloads of Agents 1, 6, 8 (including every repair round) and 10, so all four agents resolve dates against the same fixed reference (PROPOSED for contracts v1.2, approved by Julia Nov 6); `agent1_request`, `agent6_request`, `agent8_request` and `agent10_request` each raise `ValueError` if `ref_date` is `None` — the runner always supplies it, using `_today()` in `run.py` when no date is given (patchable in tests); user confirmation turns Agent 1 claims into case facts and bumps `case_version`; county + ZIP for Agent 3; `program_criteria` for Agent 4; `programs_to_check` for Agent 5 (no confirmed mismatches); the planning package for Agents 6, 8 and 10 (availability and its evidence from the KB; program name, organization and subcategory added to each match; user dates from case facts; official deadlines only from the KB).
- **Checks every result (S1–S9):** schema, identity echo, stale version, enums, references, failed status, 30 s timeout, mock flag, privacy (SSN, bank and card numbers by value pattern and field name). A result that fails a check is rejected and reported, never treated as success. S1 now also checks per-role result fields: for every `(role_id, task_type)` pair in `TASK_TYPES`, `RESULT_REQUIRED` in `contract.py` lists the required top-level `result` keys, which of those must be lists, and the required keys of each list item (from contract §4.1–4.9, §3.1–3.2). A missing key or wrong container type is `SCHEMA_INVALID` (critical), and the result is rejected and retried exactly like any other S1 failure. The check reads `role_id` and `task_type` from the **request** (not the result). A failed result (status `failed`, result `{}`) is not checked. Unknown `(role_id, task_type)` pairs also produce `SCHEMA_INVALID` (fail-closed).
- **Safety net:** in `Run._execute_body`, if any builder step raises `KeyError`, `TypeError`, `ValueError`, `AttributeError` or `IndexError`, the Supervisor records `SUPERVISOR_INPUT_ERROR` (critical) naming the stage and exception type (no user data), and returns `stopped_at_<stage>`. A run never ends with a traceback (some CLI input errors before the run starts still do; see Known limits).
- **Retries and repair** (contracts 5.3): 1 retry per call (none for stale or privacy results); after an Agent 10 FLAG, up to 2 repair rounds; then only cards still flagged with `blocks_release` are withheld and the rest of the plan is released. In each repair round the Supervisor sends only the blocking flags to Agent 8; Agent 8 must return `repaired_card_ids` (a list of strings). The Supervisor then merges only those cards back into the current plan, preserving all other cards, potential options, and coverage gaps in their original order. If `repaired_card_ids` is absent or is not a list of strings, nothing is merged, the current plan is kept, and `REPAIR_IDS_INVALID` (warning) is added to `supervisor_issues`. If the repair result has no `plan_version`, the current plan's `plan_version` is kept. Agent 10 always receives the full merged plan. If the repair result contains an unknown `card_id` it is not added (`REPAIR_UNKNOWN_CARD` warning); if a listed card is missing it is kept unchanged (`REPAIR_CARD_MISSING` warning). The merge logic is in `merge_repaired_plan()` in `run.py` and is covered by unit tests.
- **Isolation:** each agent call runs in its own process (`spawn`, same on Windows and Linux). On a timeout the process is stopped, so a hung agent cannot keep running. `--no-isolate` runs agents in-process (faster, no hard stop).
- **Writes `run_report.json`:** every step and its issues (technical errors); Agent 7 findings; `ref_date`; `final_validation` (whenever Agent 10 ran, regardless of outcome): `{verdict, repair_rounds_used, flags: [{card_id, rule_id, severity, blocks_release, reason, required_correction}], passed_card_ids}` — only these six fields, no `claim_text` or user facts; the plan with `withheld_card_ids`, `withheld_cards` (for each withheld card: `{card_id, rule_ids, reasons}` from its last blocking flags), `action_cards`, `potential_options`, `coverage_gaps`; and a `partially_mocked` flag. `steps[].issues` (technical errors) and `final_validation.flags` (content findings) are kept separate.

## Files

| File | Purpose |
|---|---|
| `contract.py` | allowed values from the contract; `RESULT_REQUIRED` table (per-role, per-task_type required result fields) |
| `checks.py` | S0 input masking and checks S1–S9; `s1_result_fields()` (S1 extension) |
| `builders.py` | `CaseState` (the Supervisor's memory of one case), `_ref_date_iso()` helper, and the request builder for every agent |
| `run.py` | the runner, `_execute_body()` / `_input_error()` safety net, `merge_repaired_plan()` helper, and `agents.json` loader (clear one-line errors, exit code 2) |
| `../../tests/` | 92 Supervisor tests (the full suite runs 112): checks, builders, full cycle on fake agents, broken and hung agents, privacy, repair rounds, ref_date, S1 per-role fields, final_validation |
| `../../tests/fixtures/kb_supervisor_fixture.json` | Frozen KB copy for Supervisor tests (Nov 6, 2026). Tests use this, not the live KB. |

## How to run (from the repository root)

```
python -I -m unittest discover -s tests -t .                               # all tests (92 Supervisor + 20 Agents 3–5)
python -m navigator.supervisor.run --agents tests/agents_fake.json --kb tests/fixtures/kb_supervisor_fixture.json               # full cycle on fake agents
python -m navigator.supervisor.run --agents tests/agents_fake.json --kb tests/fixtures/kb_supervisor_fixture.json --demo-broken   # the Supervisor rejects sample 03
python -m navigator.supervisor.run --agents agents.json                    # the team's components
```

Supervisor tests use the frozen fixture `tests/fixtures/kb_supervisor_fixture.json` (a copy of the KB as of Nov 6, 2026) so they do not depend on live KB data. The live KB `navigator/kb/kb_sacramento.json` is only used by the real end-to-end run.

## Other options

| Option | Description |
|---|---|
| `--kb PATH` | path to the KB JSON file (default: `navigator/kb/kb_sacramento.json`) |
| `--story-file PATH` | text file with the user's story (default: sample 01) |
| `--correct field=value` | user correction at confirmation, e.g. `cash_on_hand_approx=300` (repeatable) |
| `--out PATH` | output file for the run report (default: `run_report.json`) |
| `--no-isolate` | run agents inside this process (faster; a timed-out agent keeps running) |
| `--demo-broken` | replace Agent 1 with sample 03 to demonstrate rejection |
| `--ref-date YYYY-MM-DD` | reference date for Agents 1, 6, 8 and 10 (ISO format); defaults to today. An invalid value prints one clear error line and exits with code 2. |

## Known limits

- User confirmation and Agent 2 questions are simulated in the local run; the app will take them from the UI.
- The ZIP → county table holds only 95823 (Sacramento County); ZIPs are added only from an official source.
- `ref_date` for Agents 1, 6, 8 and 10 and the repair-round merge rule (only listed cards replaced, full merged plan sent to Agent 10) are PROPOSED for contracts v1.2 (approved by Julia Nov 6) and not yet part of the official shared contract.
- S1 checks that result fields are present and that lists are lists, but not the types of single values (for example `repair_round` as a number); owner: Slav, planned after Nov 16.
- Plan-level blocking flags (card_id null) are not handled yet; owner: Slav, planned after Nov 16.
- A need that ends up in no card and no coverage gap is not reported by the Supervisor yet; owner: Slav, planned after Nov 16.
- A boolean `case_version` is not rejected; owner: Slav, planned after Nov 16.
- S5 does not check references inside clarification requests; owner: Slav, planned after Nov 16.
- Asked questions are not recorded in `already_asked`; owner: Slav, planned after Nov 16.
- A `--correct` value for a fact Agent 1 did not extract is ignored; owner: Slav, planned after Nov 16.
- Some CLI input errors end with a traceback; owner: Slav, planned after Nov 16.
- `make_request` uses `assert`; owner: Slav, planned after Nov 16.
- The console summary may show wrong characters when piped on Windows; owner: Slav, planned after Nov 16.
- Safety path not implemented yet: when Agent 1 reports a safety flag, the report does not yet carry a safety warning with emergency contacts (decision Nov 7: show the warning, do not block the plan); owner: Slav, v0.2.5, planned Nov 13.
