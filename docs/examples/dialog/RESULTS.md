# Dialog mode: results on the team's agents

Run: 2026-11-14 12:35 local time; reference date 2026-11-14; HTTP http://127.0.0.1:8765; Python 3.12.10, Windows.
Every request and response of this run is in this folder (`<scenario>_<step>_<call>_request.json` / `_response.json`). The stories are made up.

| Scenario | Question turns | Calls | Total s | Slowest call s | Needs in the plan | Cards | Cards with sources | Withheld | Agent 10 | Safety notice | Checks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J: Julia: housing and food, cause and details in answers (95823) | 3 | 5 | 0.26 | 0.12 | Food, Income, Housing | 11 | 11 | 0 | PASS | no | ok |
| J660: Julia, ZIP 95660 (North Highlands, Sacramento County) | 3 | 5 | 0.14 | 0.09 | Food, Income, Housing | 11 | 11 | 0 | PASS | no | ok |
| A: vague hardship, cause asked first (Yogesh SC-E2E-A) | 3 | 5 | 0.14 | 0.07 | Food, Income, Housing | 11 | 11 | 0 | PASS | no | ok |
| B: 3-day notice and lockout threat (Yogesh SC-E2E-B) | 1 | 3 | 0.09 | 0.05 | Housing | 4 | 4 | 0 | PASS | no | ok |
| C: medical emergency, food need only in an answer (Yogesh SC-E2E-C, CR-014) | 2 | 4 | 0.15 | 0.07 | Food, Housing, Health care | 10 | 10 | 0 | PASS | no | ok |
| D: income not answered (Yogesh D_income_retry_when_unanswered) | 1 | 3 | 0.09 | 0.04 | Income, Housing | 5 | 5 | 0 | PASS | no | ok |
| SKIPZIP: Julia story, the user skips the ZIP (limitation, not a stop) | 3 | 5 | 0.10 | 0.03 | Food, Housing, Income | 0 | 0 | 0 | PASS | no | ok |
| EDIT: Julia story; at the summary: remove housing, add utility (with an SSN-like number) | 3 | 5 | 0.15 | 0.06 | Food, Income, Utilities | 7 | 7 | 0 | PASS | no | ok |
| PII: An SSN-like number in an answer never comes back | 3 | 5 | 0.13 | 0.07 | Food, Income, Housing | 11 | 11 | 0 | PASS | no | ok |
| LOCKOUT: Already locked out: housing and legal help, no crisis notice (Julia, Nov 11) | 3 | 5 | 0.15 | 0.08 | Housing, Food, Income | 11 | 11 | 0 | PASS | no | ok, 1 warning(s) |
| THREAT: A threat of violence in the story: the safety notice with verified 9-1-1 and 988 | 2 | 4 | 0.09 | 0.04 | Housing | 4 | 4 | 0 | PASS | yes | ok |

Wrong calls (must fail cleanly, never a traceback):

- PASS: confirm while clarifying -> ['WRONG_STAGE']
- PASS: broken case -> ['CASE_INVALID']
- PASS: unknown question_id -> ['UNKNOWN_QUESTION_ID']
- PASS: GET /health -> 200 {"status": "ok", "dialog_version": "0.2"}
- PASS: bad JSON -> 400
- PASS: unknown path -> 404
- PASS: 70 KB body -> 413

## Findings

- LOCKOUT WARN: the plan does not contain 'police non-emergency' yet
