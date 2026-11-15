# App Layer — first UI preview (Nov 7, 2026)

This is a **standalone, dependency-free frontend preview**, not the integrated MVP. Open `index.html` in a browser, or from repository root run `python3 -m http.server 8000` and open `http://localhost:8000/app_layer/`.

Implemented: responsive conversation layout, right/left messages, text input, optional browser speech recognition with editable transcript and explicit Send, action-plan example grouped by rent/food, six status options, navigation to My Case placeholder. Speech recognition depends on browser support, microphone permission, and browser speech service; it is **not** a confirmed privacy-approved STT solution. Do not enter real personal data.

Not implemented: Supervisor/API connection, Agent 1 understanding, Agent 2 clarification, source-verified recommendations, Case State persistence, audio playback/recording retention, safety alerts, accounts, email, watsonx.ai, Orchestrate, public deployment. The sample action cards are clearly illustrative. Status changes are local UI only and not saved.

Next technical integration: confirm Supervisor's turn-based API and Case State contracts with Slav, then add a Python HTTP adapter without changing Supervisor internals. The existing Supervisor README states user confirmations and Agent 2 questions are currently simulated in CLI runs.
