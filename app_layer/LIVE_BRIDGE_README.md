# Local synthetic bridge v4

This version adds a button to **Action plan** that starts a new Python execution of Agents 7, 6, 8, and 10, using fixed synthetic fixture inputs. It does NOT process chat messages, run Agents 1–5 live, determine eligibility, or save cases. Agents' outputs can still contain `is_mock: true`; this is not a full real-user end-to-end flow.

To run on Mac (Python 3.11 installed), extract this ZIP into a NEW folder and, from its repository root, run:

```bash
python3.11 app_layer/server.py
```

Open http://127.0.0.1:8765 and click **Action plan** → **Run local agent bridge (synthetic)**. Stop any previous server on port 8765 first (Ctrl+C in its Terminal window). Do not open `index.html` directly; the API requires the local server.

Tested: live subprocess HTTP endpoint returns PASS and four cards. Existing repository unit tests: 75 pass, one known Saint John's availability fixture mismatch. No modifications to original GitHub repo or archives. Do not deploy this server publicly.
