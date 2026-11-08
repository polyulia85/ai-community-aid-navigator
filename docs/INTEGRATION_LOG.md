# Integration log — AI Community Aid Navigator

Who did what, by date. Kept by Slav (integration and Supervisor). Facts only: commits, PRs, reviews, decisions, test runs. Times are Mountain Time (MT) unless noted.

## How credit is recorded

- Every entry names the person who did the work and links the commit or PR.
- When a review finding leads to a fix in someone else's code, the fix commit may carry a trailer line `Suggested-by: <name>`. Code written together carries `Co-authored-by: <name> <email>` (GitHub noreply addresses are fine).
- Decisions are recorded with the person who made them and the date.
- Anyone can propose a correction to this file through a PR.

---

## Fri, Nov 6, 2026

**Julia** — decisions (direct message, 12:26 PT):
- Eviction threat: Agent 1 treats it as a possible housing need; Agent 2 asks for details through the Supervisor (written notice, court judgment, a specific date, illegal eviction or lock change); priority follows real urgency.
- Unresolved needs do not block the plan; each one gets a plain explanation and is kept by the Supervisor.
- Stable `need_id` / `card_id` across agents, case updates and returning users.
- One reference date for Agents 6, 8 and 10.
- Crisis subtypes: Agent 1 proposes, Agent 2 clarifies; internal only.

**Slav**
- Supervisor v0.2.4, session 1 — commit `d3f8096` (PR #12): frozen test KB for Supervisor tests, patchable today's date, repair-merge edge cases. 92 tests pass.
- Reviews: #13 and #9 and #14 (request changes), #11, #15, #16 (comments).
- Integration run of all open PRs together (main + #9 + #14 + #11 + #13 + #12 + #15 + #16 + #6): no merge conflicts, 204 tests; full cycle with everyone's real agents, 12 of 12 steps accepted, 5 cards.
- Safety check reported to Julia: Agent 1 raises a safety flag, but the Supervisor does not use it yet (planned v0.2.5).

**Hisham** — Agents 6, 7, 8, 10: PR #11 (`dbf7f54`) and PR #13 (`42de372`, builds on #11).

**Silver** — PR #9 KB v1.5 (`8b77eec`), PR #14 Agents 3–5 v1.6 (`5f79c85`), PR #15 Case State v0.1, PR #16 emergency resources (Draft).

**Yogesh** — Agents 1–2: PR #6, commit `162304d`.

## Sat, Nov 7, 2026

**Yogesh** — PR #6, Agents 1–2 v6.2:
- `515d3fb` six pre-submission fixes; `5b621d8` restored `tests/test_builders.py` to main (removed the conflict with PR #12).
- Safety pattern, one commit per review round: `96dcc4e` fewer false positives on everyday sentences; `bcee749` direct threats caught again; `dd6ecc8` threats to objects no longer flagged, noun subjects ("the landlord") caught; `49ef03d` people and pets as targets; `39577b0` word boundary for subjects (no match inside "headache").
- Change request CR-012: eviction notice type and date as new case facts (for the contracts v1.2 draft).

**Slav**
- Reviews of the PR #6 commits above (tests, safety probe sentences, comparison with the previous commit).
- Supervisor v0.2.4, session 2 — commit `4094574` (PR #12, ready for review):
  - S1 checks every agent's result fields against one table (`RESULT_REQUIRED`, contract v1.1 sections 3–4); a run never ends with a traceback (`SUPERVISOR_INPUT_ERROR`).
  - `final_validation` in the run report whenever Agent 10 ran; `plan.withheld_cards`.
  - `ref_date` in the payloads of Agents 6, 8 and 10 (decision Nov 6).
  - README v0.2.4 with known limits. 112 tests pass on Windows and Linux.

**Julia** — decisions (Slack, Nov 7):
- Card progress statuses: the six from contract section 3.6 (not_started, in_progress, contacted_applied, waiting_for_response, completed_received, unsuccessful); "need help" is a separate feature. Users update their own progress.
- The field name stays `ref_date` for Agents 1, 6, 8 and 10 in contracts v1.2.
- Safety path: show a warning with emergency contacts; do not block the action plan automatically.
- Sources: keep verified facts with links and check dates; no protected content copied.
- Housing priority: by urgency, the user's situation and confirmed availability; emergency or legal help first under an immediate eviction threat; first / parallel / later stays.
- Email sending is not required for the MVP (Nov 22); no simulated "sent" message.
- watsonx.ai is used first of all in Agent 1; programs, conditions and priorities stay with the agents and the KB.
- Orchestrate integration: Slav. Julia takes the App Layer, voice interface, demo scenario, README/STATUS, contracts v1.2, video script, the two submission texts and the public prototype link.
