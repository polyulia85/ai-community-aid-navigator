# App Layer v13 — local developer preview

Start from `app_layer` with `python3 -m http.server 8765 --bind 127.0.0.1` and open http://127.0.0.1:8765/ .

Preserves the v12 appearance and intake demo. The Action Plan developer fixture selector previews 9 states through `supervisor_adapter.js` without running agents. Select a fixture and click **Load mock**. Progress is saved locally and keyed by stable card ID; Refresh Plan on a mock does not generate new programs. Use **My Case → Clear local demo case** to reset.

`NavigatorAdapter.fromEnvelope()` accepts proposed UI contract JSON; `fromSupervisorReport()` maps the current batch report's `plan.action_cards` into the UI shape but does **not** implement a live Supervisor endpoint, confirmation gate, or verification of benefits. All mock content is fictional.

Known limitations: conversation and summary fixture states are displayed as plan-state previews, not a full replay of chat; v12 intake still uses rule-based local questions; cards are demonstration content. No changes to agents or shared contracts. Existing v12 live-bridge controls remain disabled.
