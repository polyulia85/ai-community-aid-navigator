# App Layer v15 — local UI prototype

Based on v14. Adds larger structured Action Plan cards, four in-card accordion sections, a Full Program Guide disclosure, and emergency contact access (911/988/211). Corrects the post-confirmation ready notification and Go to Action Plan visibility for non-empty example plans. No agents, Supervisor or Knowledge Base modified.

All program content comes from the existing mock/bridge fields; missing requirements, documents, contacts and legal sources are explicitly marked unavailable, not fabricated. This is not eligibility advice or emergency response.

Run from the `app_layer` folder with `python3 -m http.server 8765 --bind 127.0.0.1` and visit http://127.0.0.1:8765/index.html.
