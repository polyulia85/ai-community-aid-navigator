# V16 checkpoint — confirmed case to preliminary matching

On confirmation, the app now sends the confirmed Summary to the existing local `/api/case/match` endpoint automatically and displays the Agents 3–5 preliminary matches. The confirmed Summary is assigned before the request. The case-matching button remains available for retry and after reload. The intake screen no longer exposes Go to Action Plan before confirmation processing.

**Limitations:** The example Action Plan cards remain synthetic and are **not** built from Agent 3–5 matching. This checkpoint does not connect Agents 1–2, 6–10 or the Supervisor to the user's live conversation. It does not determine eligibility. Server must be started with `python3 app_layer/server.py`. Test with fictional Sacramento case data.
