# AI Community Aid Navigator — Local App Layer v12

Run locally (Mac):

```bash
cd app_layer
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/

Demo path: type a **fictional** story about rent and/or food needs, answer context questions, edit and confirm Situation Summary, wait for local mock processing, click Go to Action Plan, change progress, open My Case, refresh, reload to check local persistence. Browser speech recognition (when supported) offers an editable transcript before submission.

**Limits:** Rule-based intake, not LLM-driven or connected to Supervisor. The action cards are example *categories of next steps*, not KB-verified program matches, eligibility decisions or actual agent output. Progress is browser-local and user-controlled; no automatic agency tracking. Do not enter real personal information. Python integration demo endpoints require full repository and are not used in this standalone version.

Mock fixtures in mock_ui/ and APP_SUPERVISOR_CONTRACT_DRAFT.md are reference documents; the working UI uses a small in-browser adapter in workflow_v12.js.
