# Integration log — AI Community Aid Navigator

Technical log of the integration: integration runs, merges and test results, with the commits involved. Kept by Slav (Supervisor and integration). Times are Mountain Time (MT) unless noted.

This is not a report of each member's contribution; an overall contribution report will be prepared separately at the end of the project.

## Fri, Nov 6, 2026

**Integration run** — main + #9 + #14 + #11 + #13 + #12 + #15 + #16 + #6:
- No merge conflicts; 204 tests.
- Full cycle with the real agents: 12 of 12 steps accepted, 5 cards.
- Found: Agent 1 raises a safety flag, but the Supervisor does not use it yet (planned v0.2.5).

**Commits in open PRs**
- #12 Supervisor v0.2.4, session 1: `d3f8096` (frozen test KB, patchable date, repair-merge edge cases; 92 tests).
- #11 / #13 Agents 6, 7, 8, 10: `dbf7f54`, `42de372`.
- #9 KB v1.5: `8b77eec`. #14 Agents 3–5 v1.6: `5f79c85`. #15 Case State v0.1. #16 emergency resources (Draft).
- #6 Agents 1–2: `162304d`.

## Sat, Nov 7, 2026

**Commits in open PRs**
- #6 Agents 1–2 v6.2: `515d3fb` (six pre-submission fixes), `5b621d8` (`tests/test_builders.py` restored to main); safety pattern rounds `96dcc4e`, `bcee749`, `dd6ecc8`, `49ef03d`, `39577b0`. Change request CR-012 (eviction notice type and date).
- #12 Supervisor v0.2.4, session 2: `4094574` (per-role result checks in S1, `SUPERVISOR_INPUT_ERROR`, `final_validation` and `withheld_cards` in the report, `ref_date` for Agents 6, 8, 10, README v0.2.4). 112 tests pass on Windows and Linux.

**Test branch** `integration/2026-11-07` = main + #14 + #13 + #12 + #15 + #16 + #6 (top commit `0b73acc`), for App Layer testing only:
- 225 tests OK.
- Full cycle with the real agents (ref-date 2026-11-04): completed (partially mocked), 12 of 12 accepted, 5 cards, none withheld.

## Mon, Nov 9 – Tue, Nov 10, 2026

**Commits in open PRs**
- #13: `f5f3c43` (review fixes, `ref_date` in Agent 6), `90b35e1` (prioritization update).
- #6: `457f253`, `7d10980`, `19a9f5c`, `f7cd729` (context-first clarification, multi-turn test matrix, ZIP and household size questions, CR-013, test outputs).
- #9: `a6458b4`. #14: `38ce9c5`.

**Integration run 1 (Nov 10)** — main + #9 `a6458b4` + #14 `38ce9c5` + #13 `90b35e1` + #12 + #15 + #16 + #6 `f7cd729`:
- No merge conflicts; 283 tests OK.
- Demo story: 12 of 12 steps, 4 cards; the #13 fixes ("p.m." period, one CalFresh phone) confirmed.

**Integration run 2 (Nov 10)** — free-form test story "I have problems with housing and food. I need help.":
- Full cycle stops at Agent 1: `ambiguity_flags` items are strings, contract §4.1 requires objects `{field, quote, note}` (S1 `SCHEMA_INVALID`).
- Agent 1 creates only the food need; housing is lost.
- ZIP is asked only in the first question turn, which is taken by the "what happened" question, so no ZIP and 0 cards.
- A ZIP given as the answer to the income question is stored as income.
- If the flag remains after "what happened" was asked, Agent 2 ends with no questions.
- "hours were cut" is not recognized as a cause.
- ZIP 95660 → county unknown, 0 cards; the same story with 95823 → 4 cards.
- Answers given in the expected order are parsed correctly.
- Supervisor side (v0.2.5): pass `ambiguity_flags` to Agent 2; ask for a ZIP when there is none; one county ZIP list from the KB.

**Merges into main (Nov 10, ≈20:27–20:40, merge commits)**
- #9 (`1e2fd98`), #14 (`20b1e23`), #13 into the #11 branch (`9c5d2f8`), #12 (`f4ed319`), #11 (`f727a21`); #8 and #10 closed with #11.
- main after the merges: 123 tests, all passing. The full cycle on main needs #6 (Agents 1–2).
- Open: #6, #15, #16, #17.
