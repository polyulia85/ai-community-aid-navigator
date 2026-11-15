# App Layer ↔ Supervisor — proposed boundary contract (draft 0.1, 2026-11-08)

**Status:** DRAFT — local implementation draft; no external approval needed for mock-mode development. This is an external UI boundary, **not** a change to Shared JSON Contracts v1.1 / AgentRequest / AgentResult.

## Verified implementation baseline

- `navigator/supervisor/run.py` currently emits a batch report with `run_id`, `case_id`, `case_version`, `outcome`, `ref_date`, `partially_mocked`, `supervisor_issues`, `agent7_findings`, `steps`, `plan`, `final_validation`.
- `Run._execute_body` simulates Agent 1 confirmation via `B.confirm_agent1` before running downstream agents. It is **not** yet a live, multi-turn, user-confirmation API.
- `plan` is built from Agent 8 and has `action_cards`, `potential_options`, `coverage_gaps`, `plan_version` when available. Cards have `progress_status` initially `not_started`; only explicit user actions can update progress.
- Existing UX specification requires a single conversational interface, user-visible editable voice transcription, and user review of identified needs. Current approved user flow additionally requires an editable full Situation Summary and explicit confirmation **before** downstream processing.

## Proposed UI envelope

```json
{
  "ui_contract_version": "0.1-draft",
  "case_id": "case_demo_001",
  "case_version": 1,
  "event_id": "evt_001",
  "phase": "conversation",
  "messages": [],
  "situation_summary": null,
  "processing": null,
  "action_plan": null,
  "case_progress": [],
  "errors": []
}
```

`phase` enum (UI-only): `conversation`, `summary_review`, `processing`, `action_plan`, `my_case`, `error`. UI navigation to Conversation/My Case does not itself change backend phase.

## UI events sent to boundary adapter (proposed)

| Event | Payload | Expected behavior |
|---|---|---|
| `submit_message` | `case_id`, `case_version`, `text`, `client_message_id` | Save message; Supervisor chooses next clarification or summary readiness |
| `submit_summary_corrections` | `case_id`, `case_version`, `changes` | Reconcile edits; recompute readiness, never auto-confirm |
| `confirm_summary` | `case_id`, `case_version`, `summary_revision` | Explicitly confirm facts; only then start downstream processing |
| `get_case` | `case_id` | Restore conversation, summary, plan and user progress |
| `update_card_progress` | `case_id`, `card_id`, `progress_status` | User-initiated status change only |
| `refresh_plan` | `case_id`, `case_version` | Re-evaluate using confirmed/updated facts; preserve progress where cards match |

Speech-to-text remains a **client-side draft** until user reviews and explicitly submits the transcript. Never send an unconfirmed transcript as a user message.

## Adapter mapping

| Existing Supervisor result | UI field | Notes |
|---|---|---|
| `case_id`, `case_version` | same | Preserve exactly |
| `outcome == "completed"` + `plan` | `phase = action_plan`, `action_plan` | Only after confirmed summary in live flow; batch reports alone do not prove confirmation |
| `plan.action_cards[]` | `action_plan.cards[]` | Preserve card IDs, related needs, priority, evidence, dates, uncertainty and status |
| `plan.potential_options[]` | `action_plan.potential_options[]` | Do not present as verified matches |
| `plan.coverage_gaps[]` | `action_plan.coverage_gaps[]` | Show explicitly, never invent programs |
| `supervisor_issues[]`, `final_validation` | `errors[]`, validation metadata | Do not silently turn failures into a success state |

## Future live-integration gaps

1. What is the supported multi-turn endpoint for submit-message and clarification responses? Current `run.py` is batch-oriented.
2. What exact structure is emitted for Supervisor-approved, user-editable Situation Summary and its revision/version?
3. How is **explicit user confirmation** persisted and validated before Agents 3–10 start?
4. What mechanism returns processing status asynchronously, and how do we retrieve case state?
5. Is `refresh_plan` supported, and what are the persistence rules for user-updated card statuses?

**Integration rule:** Until these are answered, mock fixtures are UI test data, not claimed real Supervisor outputs. No internal agent contracts are changed.
