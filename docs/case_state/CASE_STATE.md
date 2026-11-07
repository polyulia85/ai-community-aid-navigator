# Case State — what we store (v0.1, owner: Silver)

**Code:** `navigator/case_state/schema.sql` (tables), `navigator/case_state/store.py` (functions), `tests/case_state/` (10 tests).
**Tech:** SQLite through Python's built-in `sqlite3`, so there are no extra packages. The same code works on both integration paths (A: inside Orchestrate, B: external app). Only where the database file lives changes.

## The five things we store

| # | What | Table(s) | Why |
|---|---|---|---|
| 1 | **The case** | `cases` | One person's situation: id, created/updated time, `current_version`, active/closed, language, optional account (P1). |
| 2 | **Facts** the person told us and confirmed | `case_facts`, `needs`, `clarifications` | Contracts 3.1–3.3. Unknown stays `NULL` (never 0 or false). A changed fact **supersedes** the old row, which is kept as history. Skipped questions stay unknown. |
| 3 | **Plan versions** | `plan_versions`, `plan_needs`, `action_cards`, `card_needs` | Every plan exactly as delivered (`plan_json`), plus Agent 10's PASS/FLAG and whether it was released. `plan_needs` keeps the **needs layer in priority order**, and `card_needs` links each card to its needs, so the UI can show *need → its actions* (Julia, Nov 3). |
| 4 | **User statuses** | `card_status` | Progress on each card, set **only by the user**: `not_started`, `in_progress`, `waiting`, `completed`, `need_help`. Agents never write here. |
| 5 | **History** | `events` | Append-only log (case created, facts added, needs saved, clarification, plan released/withheld, status changed). The database blocks edits and deletes. |

## Rules built in

- Every change to facts or needs creates a new `case_version` (contracts §30.2: results from an older version are discarded).
- **Privacy:** location is ZIP or county only. Fields like SSN, date of birth, ID, bank or card numbers are rejected (same list as Supervisor check S9). No raw story text is stored; needs keep only the short `original_quote`.
- Times are passed in by the caller (the Supervisor's reference clock), so tests never depend on today's date.

## How the Supervisor would use it (one cycle)

`create_case` → `add_facts` / `save_needs` (Agents 1–2) → `record_clarification` (answers) → `save_plan` (after Agent 10, with need order from Agent 6) → the UI reads `plan_by_need` → the user calls `set_card_status`. `history` feeds the "My case" screen.

## Open decisions (team)

1. **Status list:** this uses Julia's five labels from Nov 3. Hisham's screens mention six, so the list needs aligning before the UI is built.
2. **Stable card IDs across plan versions** (A8-05, contracts v1.2): `card_status` is keyed by `card_id`, so progress carries over only if IDs stay stable.
3. **Raw story text:** not stored (privacy minimization). If "Something changed / Refresh plan" needs the original story, we need a consent rule first.
4. **Retention:** how long anonymous cases are kept. Proposal: delete after 30 days without activity. Not implemented yet.
5. **Hosted database:** needed only for path B. Decided together with the integration path.
