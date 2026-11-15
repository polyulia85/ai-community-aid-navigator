# App Layer / Supervisor integration checkpoint (Nov 7)

This is a **local technical smoke test**, not a user-facing production integration.

## Start

From repository root:

```bash
python3 app_layer/server.py
```

Open http://127.0.0.1:8765 and click **Action plan → Run Supervisor integration test (synthetic data)**.

The endpoint uses `tests/agents_fake.json` and the Supervisor's built-in synthetic story. It **never transmits the user's chat text**. The generated report is temporary and deleted after the response. Browser chat and status changes remain local and are not persisted.

## Confirmed limitation

Current `navigator.supervisor.run.Run.execute` is one-shot and **simulates user confirmation and Agent 2 follow-up**. It cannot yet implement the approved multi-turn UX. Do not label the test result as real personalized recommendations. `agent_7` may be absent from the fake-agent fixture.

## Needed from Supervisor team

Agree on an incremental API contract (start_case, submit_story, confirm_needs, answer_clarification, get_plan, update_status, refresh_plan), with case/version IDs, safety flag and typed errors. Preserve six statuses. This integration layer should wrap Supervisor, not change its existing internals without coordination.

## Safety

Localhost only. No authentication, persistent case storage, production security controls or real emergency response. Do not deploy publicly or enter real personal information.
