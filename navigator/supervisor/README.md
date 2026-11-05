# Supervisor — AI Community Aid Navigator

Owner: Slav (Supervisor / Orchestrator and integration). Contract: `docs/contracts/SHARED_CONTRACTS.md` (v1.1, Oct 27, 2026). Version: v0.2.3 (Nov 1, 2026). Local Python prototype, standard library only (Python 3.11+); not yet connected to IBM watsonx Orchestrate.

## What it does

- **Runs one cycle:** Agent 1 → 2 → 3 → 4 → 5 → 6 → 8 → 10, with Agent 7 reviewing the retrieval, matching, verification and planning stages. Agents never call each other; every call is one AgentRequest and one AgentResult (contracts sections 1–2).
- **Builds every request** with only the facts that agent needs: S0 input masking before Agent 1; `ref_date` (ISO string) added to the Agent 1 payload so it can resolve relative dates in the story against a fixed reference date (PROPOSED for contracts v1.2); user confirmation turns Agent 1 claims into case facts and bumps `case_version`; county + ZIP for Agent 3; `program_criteria` for Agent 4; `programs_to_check` for Agent 5 (no confirmed mismatches); the planning package for Agents 6, 8 and 10 (availability and its evidence from the KB; program name, organization and subcategory added to each match; user dates from case facts; official deadlines only from the KB).
- **Checks every result** (S1–S9): schema, identity echo, stale version, enums, references, failed status, 30 s timeout, mock flag, privacy (SSN, bank and card numbers by value pattern and field name). A result that fails a check is rejected and reported, never treated as success.
- **Retries and repair** (contracts 5.3): 1 retry per call (none for stale or privacy results); after an Agent 10 FLAG, up to 2 repair rounds; then only cards still flagged with `blocks_release` are withheld and the rest of the plan is released. In each repair round the Supervisor sends only the blocking flags to Agent 8; if Agent 8 returns `repaired_card_ids`, the Supervisor merges only those cards back into the current plan, preserving all other cards, potential options, and coverage gaps in their original order. Agent 10 always receives the full merged plan. If the repair result contains an unknown `card_id` it is not added (`REPAIR_UNKNOWN_CARD` warning); if a listed card is missing it is kept unchanged (`REPAIR_CARD_MISSING` warning). The merge logic is in `merge_repaired_plan()` in `run.py` and is covered by unit tests. Both the merge rule and `ref_date` are PROPOSED for contracts v1.2.
- **Isolation:** each agent call runs in its own process (`spawn`, same on Windows and Linux). On a timeout the process is stopped, so a hung agent cannot keep running. `--no-isolate` runs agents in-process (faster, no hard stop).
- **Writes `run_report.json`:** every step, its issues, Agent 7 findings, the final plan, a "partially mocked" flag, and the `ref_date` used for the run.

## Files

| File | Purpose |
|---|---|
| `contract.py` | allowed values from the contract (one place to change for v1.1) |
| `checks.py` | S0 input masking and checks S1–S9 |
| `builders.py` | CaseState (the Supervisor's memory of one case) and the request for every agent |
| `run.py` | the runner, `merge_repaired_plan()` helper, and `agents.json` loader (clear one-line errors, exit code 2) |
| `../../tests/` | 66 tests: checks, builders, full cycle on fake agents, broken and hung agents, privacy, repair rounds, ref_date |

## How to run (from the repository root)

```
python -m unittest discover tests                                          # Supervisor tests
python -m navigator.supervisor.run --agents tests/agents_fake.json         # full cycle on fake agents
python -m navigator.supervisor.run --agents tests/agents_fake.json --demo-broken   # the Supervisor rejects sample 03
python -m navigator.supervisor.run --agents agents.json                    # the team's components
```

The tests and the KB-based steps read `navigator/kb/kb_sacramento.json` (Silver's KB).

## Other options

| Option | Description |
|---|---|
| `--kb PATH` | path to the KB JSON file (default: `navigator/kb/kb_sacramento.json`) |
| `--story-file PATH` | text file with the user's story (default: sample 01) |
| `--correct field=value` | user correction at confirmation, e.g. `cash_on_hand_approx=300` (repeatable) |
| `--out PATH` | output file for the run report (default: `run_report.json`) |
| `--no-isolate` | run agents inside this process (faster; a timed-out agent keeps running) |
| `--demo-broken` | replace Agent 1 with sample 03 to demonstrate rejection |
| `--ref-date YYYY-MM-DD` | reference date for Agent 1 date resolution (ISO format); defaults to today. An invalid value prints one clear error line and exits with code 2. |

## Known limits

- User confirmation and Agent 2 questions are simulated in the local run; the app will take them from the UI.
- The ZIP → county table holds only 95823 (Sacramento County); ZIPs are added only from an official source.
- `ref_date` (Agent 1 date resolution) and the repair-round merge rule (only listed cards replaced, full merged plan sent to Agent 10) are PROPOSED for contracts v1.2 and not yet part of the official shared contract.
