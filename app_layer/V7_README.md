# v7 Situation Summary + Confirmation (local UI test)

After four fixed intake questions, a structured editable summary appears. Confirm Information validates nonempty fields, saves them in browser memory for this page only, and displays a **Go to Action Plan (preview)** navigation button. The plan screen truthfully reports that no personalized plan has been generated. Existing synthetic bridge diagnostics remain separate.

**Not connected:** live Supervisor, Agent 1/2, eligibility checks, personalized planning, persistent case storage. Do not enter real sensitive information.

Run: `python3.11 app_layer/server.py` then open `http://127.0.0.1:8765`. Stop any older server first.
