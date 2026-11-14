# Bob sessions — Slav (Supervisor and integration)

Every Bob task Slav ran for the Supervisor (`navigator/supervisor/`), in order. Each task has its exported history (`.md`) and a screenshot of its Bob coin usage (`.png`). Local paths and anything private were removed from the exports before commit; nothing else was changed. A note at the top of an export says what happened after the task ended.

**Before Bob.** Supervisor v0.2.2 (commit `0cb59a3`, Oct 27: the cycle, checks S0–S9, contracts v1.1, 56 tests) was written before our Bob sessions started on Nov 1. Every Supervisor change after it was made in Bob or checked by Bob, as listed below.

**How we worked with Bob.** Each task had a written scope: which files to read, what not to touch, one fix at a time with the diff shown before applying. To save coins, larger review fixes were checked first on a copy of the branch and then given to Bob as exact changes; the full test suite was run by hand after every task. When a task could not finish in Bob (the 100-turn task limit) or a review found defects after the task, the remaining checked fixes were applied with a script, and the note at the top of that export says so.

| Date (MT) | File | Version | What Bob did | Outside Bob, and why | Tests after | Bob coins |
|---|---|---|---|---|---|---|
| Nov 1 | `2026-11-01_supervisor_v0.2.3` | v0.2.3 (`bf3b133`) | Repair rounds keep every card (merge of repaired cards); `ref_date` for Agent 1; `--ref-date` | — | 56 → 66 | 2.65 |
| Nov 6 | `2026-11-06_supervisor_v0.2.4_session1` | v0.2.4, FIX 1–4 (`d3f8096`) | Frozen test KB, tests independent of today's date, repair-merge edge cases | — | 92 | 8.49 |
| Nov 7 | `2026-11-07_supervisor_v0.2.4_session2` | v0.2.4, FIX 5, 6, 16 + README (`4094574`) | Per-role result fields in check S1, Agent 10 final validation in the report, `ref_date` for Agents 6, 8 and 10 | — | 112 | 21.61 |
| Nov 11–13 | `2026-11-13_supervisor-v0.2.5_sessionA_dialog` | v0.2.5 dialog mode (`dabbc47`, `2b401c4`, `5ec32df`, `81a5209`) | Ambiguity flags to Agent 2, Agent 1 answer request, county from the verified ZIP list, facts from answers, `dialog.py` start / answer / confirm | The task stopped at Bob's 100-turn limit: Bob applied review fixes 1–4; fixes 5–24 (the same text given to Bob) were applied with a script | 424 | 36.77 |
| Nov 13 | `2026-11-13_supervisor-v0.2.5_sessionB_cli_http` | v0.2.5 command line, HTTP API, 911/988 (`ff05a83`, `3abaaf2`) | Command line, local HTTP API, verified 9-1-1 and 988 contacts in the safety notice | A review after the task found 2 failing tests and 6 defects (listed in the note); the checked fixes were applied with a script | 467 | 6.72 |
| Nov 14 | `2026-11-14_supervisor-v0.2.5_sessionC_docs_review` | v0.2.5 docs + `locale` (`0b5df35`) | Checked the new README and dialog forms against the code (4 mismatches, one a code defect: the HTTP API did not pass `locale`) and applied the 25 checked changes | — | 475 | 4.07 |
| Nov 14 | `2026-11-14_supervisor-v0.2.5_sessionD1_real_agents` | v0.2.5 real-agent check | Applied 39 checked changes (skipped-ZIP note under needs with no card, `not_understood` for unreadable answers, closed HTTP error responses, quiet tests); ran the test suite and all dialog scenarios over HTTP on the team's real agents; reported the results (`docs/examples/dialog/RESULTS.md`) | The scenario tool `tools/run_dialog_scenarios.py` was written and checked outside Bob; the first scenario run hit a server started before the changes (instruction error), rerun after a restart | 485 | 6.50 |

Together 86.81 coins, as shown for each task in its screenshot (History → hover over the task: Bob coins). The account total after Session D1 was 86.85 of 150.

Dates are Mountain Time and match the commit days. The "Date" line inside an export can differ by one day (Session A shows Nov 12, Session B shows Nov 14); the file names follow the commits.
