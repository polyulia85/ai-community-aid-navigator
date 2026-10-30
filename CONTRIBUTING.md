# How we work in this repository

## Folder structure

```
ai-community-aid-navigator/
├── README.md                    project overview (Julia)
├── CONTRIBUTING.md              this file
├── STATUS.md                    what is real, what is mock, what is not built yet
├── agents.json                  wiring: which module handles which agent role
├── docs/
│   ├── architecture/            Solution Blueprint, RAG Technical Architecture, Technical Design, Decision Register
│   ├── contracts/               SHARED_CONTRACTS.md (v1.1; v1.0 frozen Oct 23)
│   └── SUBMISSION_PLAN.md       weeks 7–10 plan and final submission checklist
├── navigator/                   the Python package
│   ├── supervisor/              Slav: orchestration, checks S0–S9, run.py
│   ├── agents/
│   │   ├── agent_1_2/           Yogesh: Agents 1, 2
│   │   ├── agent_3_4_5/         Silver: Agents 3, 4, 5
│   │   └── agent_6_7_8_10/      Hisham: Agents 6, 7, 8, 10
│   ├── kb/                      Silver: the single Knowledge Base file and its tools
│   └── samples/                 shared test case JSON (contracts section 6)
├── tests/                       integration and Supervisor tests
│   ├── agent_1_2/               Yogesh's tests
│   ├── agent_3_4_5/             Silver's tests
│   └── agent_6_7_8_10/          Hisham's tests
└── bob_sessions/                exported IBM Bob task sessions (required for judging)
```

## Rules

1. **Your folder is yours.** Commit your component to your own folder under `navigator/agents/` and your tests to `tests/<your folder>/`. Change someone else's folder only after asking them.
2. **Shared folders change through the team.** `docs/contracts/`, `navigator/samples/`, `navigator/kb/` and `agents.json` affect everyone. Open a pull request and post it in the channel. Contract changes after the v1.0 freeze go through a change request: what, why, who is affected, timeline.
3. **One Knowledge Base.** There is exactly one KB file: `navigator/kb/kb_sacramento.json`. The Supervisor and Agents 3–5 both read it. No private copies.
4. **One entry point per component.** Each package exposes `handle(request: dict) -> dict` (contracts section 7). The module path goes into `agents.json`.
5. **Label mocks.** Every result from mock or unfinished logic sets `is_mock: true`, and `STATUS.md` says what is real and what is mock. Do not describe mock behavior as working functionality.
6. **The repository is public.** Never commit API keys, tokens, passwords, `.env` files, real user data or real people's names from interviews or research. Test stories are synthetic. If a secret is committed by mistake, tell the team at once: deleting the file is not enough, because the secret stays in the history and has to be revoked.
7. **No local clutter.** No `venv/`, `__pycache__/`, `.qodo/`, editor caches or run reports (see `.gitignore`).
8. **Before you push:** your own tests pass, and the full cycle still runs:
   ```
   python -m unittest discover tests
   python -m navigator.supervisor.run --agents agents.json
   ```

## Moving an existing package into this layout

- **Yogesh:** package folder → `navigator/agents/agent_1_2/`. Your shared enums can stay in `navigator/contracts/`. The helper `navigator/supervisor/validators.py` should move into your tests or your agent folder, because `navigator/supervisor/` is the Supervisor's folder. Keep `pydantic` in `requirements.txt` while `navigator/contracts/` imports it.
- **Silver:** `agents/agent_3_4_5/` → `navigator/agents/agent_3_4_5/`; `kb/` → `navigator/kb/`; tests → `tests/agent_3_4_5/` (imports become `navigator.agents.agent_3_4_5`).
- **Hisham:** `agent_6_7_8_10.py` → `navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py`; `run_tests.py` and fixtures → `tests/agent_6_7_8_10/` (the import becomes `navigator.agents.agent_6_7_8_10.agent_6_7_8_10`).

This layout has already been checked: with all three current packages placed this way, a full cycle through the Supervisor completes (12 of 12 steps accepted).
