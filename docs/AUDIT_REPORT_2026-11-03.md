# Independent Architecture, Contract, and Code Audit
## AI Community Aid Navigator — IBM SkillsBuild
**Audit date:** 2026-11-03  
**Auditor:** Bob (IBM SkillsBuild AI Experiential Learning Lab — independent, read-only)  
**Type:** Full architecture, contract, and code audit with live test execution  
**Workspace:** `<local clone>/ai-community-aid-navigator-main`  

---

## 1. Audit Scope, Repository Snapshot, and Documentation Inventory

### 1.1 Repository Snapshot

| Item | Value |
|---|---|
| Repository path | `<local clone>/ai-community-aid-navigator-main` |
| Git repository | **No `.git/` directory found** — this is a ZIP snapshot; no branch, commit hash, or uncommitted-change status can be reported |
| Snapshot source | Local extracted archive |
| README contract baseline | "Shared JSON Contracts v1.0 (Frozen Baseline)" |
| STATUS.md last updated | October 27, 2026 |

**Uncommitted changes:** Cannot be determined — no Git metadata present.  
**Active branch / HEAD commit:** Unknown — no Git metadata present.

### 1.2 Architecture Reference Package

The architecture documents are embedded within the repository's `docs/` tree rather than under a separate `architecture_reference/` directory. All documents were located and read:

| Document | Location | Status |
|---|---|---|
| Solution Blueprint v1.1 | `docs/architecture/Solution_Blueprint_v1.1.md` | Present (19,777 bytes) |
| Technical Design (includes Baseline) | `docs/architecture/Technical_Design.md` | Present — very large; full Final Consolidation Baseline (Part A–F, Sections 11–30) found within |
| Shared JSON Contracts v1.0 | Referenced in README and contract header of v1.1 file | **Not a separate file** — v1.1 supersedes it in place |
| Shared JSON Contracts **v1.1** | `docs/contracts/SHARED_CONTRACTS.md` | **Present** — contrary to the audit brief's note that v1.1 was missing from the package; it is the only contracts file in the repository and is self-labeled v1.1 (published Oct 27, built on v1.0 frozen Oct 23) |
| RAG Technical Architecture | `docs/architecture/RAG_Technical_Architecture.md` | Present (11,618 bytes) |
| Decision Register 2026-10-15 | `docs/architecture/Decision_Register_2026-10-15.md` | Present (7,721 bytes; historical, not an approved requirement) |
| TEAM UPDATE — MASTER DEVELOPMENT PLAN (Pages file) | **Not present in repository** | Cannot be read; see §9 |
| MVP Technical Breakdown (Nov 1, 2026) | **Not present in repository** | Cannot be read; see §9 |
| Integration Run report (Oct 23, 2026) | **Not a separate file** — described in `STATUS.md` (Oct 27 run, not Oct 23); no standalone report found | Historical context only |
| Repository Readiness Audit | `docs/REPOSITORY_READINESS_AUDIT.md` | Present — an earlier static-inspection audit by Bob (no tests executed); this report supersedes it with live test results |
| Submission Plan | `docs/SUBMISSION_PLAN.md` | Present |

**Shared JSON Contracts v1.1 finding:** The audit brief identified v1.1 as missing. It is present at `docs/contracts/SHARED_CONTRACTS.md`. Its header states it is v1.1, published October 27, 2026, built on v1.0 (frozen October 23). The contract status section (§0) confirms that ACCEPTED changes are now binding; PROPOSED changes in v1.1 are still pending team replies.

### 1.3 Project Component Inventory

| Component | Path | Present |
|---|---|---|
| Supervisor orchestration | `navigator/supervisor/` | ✅ |
| Agent 1 (Crisis Understanding) | `navigator/agents/agent_1_2/` | ❌ README only — no Python |
| Agent 2 (Case Clarification) | `navigator/agents/agent_1_2/` | ❌ README only — no Python |
| Agents 3, 4, 5 (Retrieval, Matching, Verification) | `navigator/agents/agent_3_4_5/` | ✅ (mock) |
| Agents 6, 7, 8, 10 (Planning, QC, Plan Build, Validation) | `navigator/agents/agent_6_7_8_10/` | ✅ (mock) |
| Agent 9 (Personal Navigation) | — | ❌ Not built |
| Knowledge Base (Sacramento) | `navigator/kb/` | ✅ (Nov 2 update published) |
| Supervisor + component tests | `tests/` | ✅ (see §8) |
| Agent 1/2 tests | `tests/agent_1_2/` | ❌ README only |
| UI, accounts, database, email | — | ❌ Not built |
| IBM watsonx Orchestrate integration | — | ❌ Not built |
| Public prototype link | — | ❌ Not available |
| `requirements.txt` / CI configuration | — | ❌ Not present |

---

## 2. Source Precedence and Unresolved Document Conflicts

### 2.1 Precedence Applied in This Audit

Per Section A of the Baseline and Section 0 of Shared Contracts v1.1:

1. Final Consolidation Baseline (`Technical_Design.md`, Parts A–F, front chapter) — highest authority
2. Section 30 APPROVED rules and other explicitly APPROVED domain rules
3. Section 11 frozen contracts (unless superseded by Part D or the Baseline front chapter)
4. Sections 12–29 (historical working proposals, reference only)
5. RAG Technical Architecture
6. Solution Blueprint v1.1

PROPOSED in v1.1 (awaiting replies) applies as default for the build but not as a final product decision. PENDING JULIA items (decisions 2, 6, 7, 8, 11, 12) remain open.

### 2.2 Status of Key Contract Items

| Item | Status | Audit impact |
|---|---|---|
| Six ProgressStatus values (snake_case wire) | PENDING JULIA (decision 11) | Code uses six values — correct default |
| Evidence freshness window (Q7) | PENDING JULIA (decision 12) | Agent 7 reports age as info only — correct default |
| `subcategory` optional | PENDING JULIA (decision 6) | Implemented as optional — correct default |
| Silver's taxonomy + `other_unlisted` | PENDING JULIA (decisions 2, 6) | Implemented — correct default |
| Card title wording with program name | PROPOSED (v1.1) | Implemented (C-NAME and C-EVP checks pass) |
| `repair_flags[]` in Agent 8 | PROPOSED (v1.1) | Implemented — see Defect D-01 |
| Agent 5 same-source contradiction rule | OPEN (v1.1, decision in progress) | Silver's approach implemented; test T8 passes |

### 2.3 Unresolved Document Conflicts

**Conflict C-1 — KB state vs. test expectation (confirmed defect — see D-02):**  
The Baseline and Contracts v1.1 Section 6 explicitly provide for the Saint John's Nov 2 KB update. The update has been published (kb_sacramento.json now shows `confirmed_open`, `ev_sjhap_019` and `ev_sjhap_022` superseded). However, `tests/test_builders.py` line 105 hard-codes the pre-update `temporarily_closed` expectation without the conditional logic present in `tests/agent_3_4_5/test_agents_3_4_5.py`. This creates one failing test.

**Conflict C-2 — MVP Technical Breakdown not available:**  
The audit brief notes this document as PROPOSED. Because it is not in the repository, no approved technologies, estimates, or owners drawn from it are relied upon in this report.

**Conflict C-3 — Master Development Plan (Pages file) not available:**  
The Pages file cannot be read on this platform. Owner assignments in this report rely on the responsibility map provided in the audit brief and on `README.md` + `STATUS.md`, not on the Pages file.

---

## 3. Component Implementation Matrix

| Role | Agent(s) | Owner | Version | State | Mock flag | Contract compliance | Notes |
|---|---|---|---|---|---|---|---|
| Crisis Understanding | 1 | Yogesh | (v3.1 claimed) | **ABSENT — not committed** | — | — | agents.json broken; no `__init__.py` or source file |
| Case Clarification | 2 | Yogesh | (v3.1 claimed) | **ABSENT — not committed** | — | — | Same directory as Agent 1 |
| Resource Retrieval | 3 | Silver | v1.3 | Mock | `is_mock: true` | v1.0 compliant | All tests pass |
| Resource Matching | 4 | Silver | v1.3 | Mock | `is_mock: true` | v1.0 compliant | All tests pass |
| Resource Verification | 5 | Silver | v1.3 | Mock | `is_mock: true` | v1.0/v1.1 compliant | Same-source rule implemented |
| Action Prioritization | 6 | Hisham | v0.5 | Mock | `is_mock: true` | v1.1 compliant | Defect D-03 (multi-need coverage check) |
| Quality & Uncertainty | 7 | Hisham | v0.5 | Mock | `is_mock: true` | v1.1 compliant | All 54 checks pass; Q rules Q1–Q10 implemented |
| Plan Builder | 8 | Hisham | v0.5 | Mock | `is_mock: true` | v1.1 mostly compliant | **Defect D-01** (repair merge) |
| Personal Navigation | 9 | Yogesh | — | **NOT BUILT** | — | — | Contracts Section 8: not in v1.0 scope |
| Plan Validation | 10 | Hisham | v0.5 | Mock | `is_mock: true` | v1.1 compliant | V rules V1–V13 implemented |
| Supervisor / Orchestration | — | Slav | v0.2.2 | Working | marks run as partially_mocked | v1.1 compliant | Defect D-01 in repair merge |
| Knowledge Base (Sacramento) | — | Silver | v1.0 schema | Published | — | v1.0 schema compliant | Nov 2 update published; 4 programs, 113 evidence records |
| UI / user layer | — | — | — | **NOT BUILT** | — | — | |
| Application Layer | — | — | — | **NOT BUILT** | — | — | SQL, session persistence not implemented |
| IBM watsonx Orchestrate | — | — | — | **NOT INTEGRATED** | — | — | Local Python prototype only |
| agents.json end-to-end run | — | — | — | **BROKEN** | — | — | Agent 1/2 module missing; `load_agents()` raises error before any step |

---

## 4. Confirmed Defects — Prioritized by Severity

### D-01 — P0 — Critical: Supervisor loses passing Action Cards when repair succeeds before maximum rounds

**Requirement:** Contracts v1.1 §5.3: "After an Agent 10 FLAG: only the flagged cards go back to Agent 8, maximum 2 repair rounds. If a card is still flagged, only that card is withheld; the other cards are released."  
**Baseline §B:** "One continuous Case and one evolving Action Plan per registered user."

**File / function / line:** `navigator/supervisor/run.py`, `Run.execute()`, lines 304–315.

**Root cause:** When `repair_flags` is set, Agent 8 (by design, `agent_6_7_8_10.py` lines 315–337) returns **only the repaired cards** in `action_cards`. The Supervisor then builds the final plan from `r8["result"].get("action_cards", [])` (line 311) **without merging** the cards that passed Agent 10 in round 0. Those passing cards are permanently lost from the plan.

**Exact input conditions:** Any run where (a) Agent 10 flags at least one card on round 0 but not all cards, (b) the repair succeeds (Agent 10 is satisfied on round 1 or 2 before max rounds), and (c) Agent 8 correctly returns only the repaired cards.

**Expected behavior:** Final plan contains all passing cards (from round 0) plus all successfully repaired cards (from repair Agent 8 response).

**Actual behavior:** Final plan contains **only the repaired cards**; all cards that passed Agent 10 in round 0 are silently dropped.

**Reproduction (executed during this audit):**
```python
# Run with real agent_8 (handle from agent_6_7_8_10.py) and a custom agent_10
# that flags card_02 on round 0, passes everything on round 1
rep = R.Run(dict(F.ALL, agent_8=real_handle, agent_10=agent_10_flag_then_pass), R.DEFAULT_KB).execute(STORY)
# Result: rep['plan']['action_cards'] has ['card_02'] only; card_01 is MISSING
```

**Severity:** P0 — Critical MVP blocker. In any session where at least one card triggers a repair and the repair succeeds, the delivered plan is silently incomplete. Users receive fewer action options than they should. T08, T10 in the Baseline acceptance suite would fail.

**Recommended correction:**
In `run.py` `execute()`, before the repair loop, save the cards that passed Agent 10 on round 0. After a successful repair, merge: final cards = passing cards + repaired cards (deduplicated by card_id).

```python
# Save passing cards from round 0 before any repair
passing_cards = {}   # card_id -> card (maintained across rounds)
for repair_round in range(MAX_REPAIR_ROUNDS + 1):
    q10 = B.agent10_request(st, pkg, q8, r8, repair_round)
    r10 = self.call(q10)
    ...
    flags = [f for f in r10["result"].get("flags", []) if f.get("blocks_release")]
    # Record newly passed cards
    for c in r8["result"].get("action_cards", []):
        if c["card_id"] in r10["result"].get("passed_card_ids", []):
            passing_cards[c["card_id"]] = c
    if not flags:
        break
    ...

# Final plan: all passing cards + no withheld cards
all_cards = list(passing_cards.values())
cards = [c for c in all_cards if c["card_id"] not in withheld]
```

**Required regression coverage:** Add a `unittest` test to `tests/test_run.py` that uses the real `agent_8.handle` (or a fake that correctly returns only flagged cards on repair) and verifies that passing cards are preserved after a successful repair round.

**Note:** The `test_flagged_card_withheld_after_two_repair_rounds` test in `test_run.py` uses a fake `agent_8` that always returns all cards regardless of `repair_flags`, so it does **not** catch this defect. The defect is only exposed with the real `agent_6_7_8_10.handle`.

---

### D-02 — P1 — High: One test is broken due to stale KB expectation after Nov 2 publish

**Requirement:** Contracts v1.1 §6: the Nov 2 KB publish was planned; `T5_ClosedProgram` in agent_3_4_5 tests correctly handles both states. The corresponding `test_builders` test does not.

**File / function / line:** `tests/test_builders.py`, `TestWithKB.test_planning_package_availability_and_timing`, line 105.

```python
self.assertEqual(avail["prog_housing_saintjohns_sac_001"], "temporarily_closed")
```

**Root cause:** The KB was correctly published on Nov 2 (`kb_sacramento.json` now shows Saint John's as `confirmed_open`). The test was not updated to match, unlike `tests/agent_3_4_5/test_agents_3_4_5.py` line 137 which uses a conditional `if state == "temporarily_closed"`.

**Test execution result (this audit):**
```
FAIL: test_planning_package_availability_and_timing
AssertionError: 'confirmed_open' != 'temporarily_closed'
```

**Severity:** P1. The test failure does not indicate a production defect — the KB and Supervisor behavior are correct. However, it breaks the test suite (`Ran 76 tests, 1 FAILED`), blocking CI verification of the Supervisor.

**Recommended correction:** Replace line 105 in `test_builders.py` with a conditional that mirrors `T5_ClosedProgram`:
```python
state = avail["prog_housing_saintjohns_sac_001"]
self.assertIn(state, ("temporarily_closed", "confirmed_open"))
```
Or add a full conditional block. Also adjust line 108–110 if they depend on the temporarily-closed timing values.

**Required regression coverage:** Ensure both pre-Nov 2 and post-Nov 2 states are testable without changing the test file again.

---

### D-03 — P2 — Medium: Agent 6 coverage check emits spurious COVERAGE_GAP when one program covers multiple needs

**Requirement:** Contracts v1.1 §4.3 Agent 3: `matched_need_ids[]` may contain multiple need IDs for one program (one program returned for two housing subcategory needs). Agent 6 §4.6: every need should appear in an action or be flagged as a gap.

**File / function / line:** `navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py`, `agent_6()`, line 267.

```python
covered = {a["need_id"] for a in actions}
```

**Root cause:** `a["need_id"]` is set to `m["need_ids"][0]` (the first need ID only). If a program match has `need_ids = ["need_001", "need_002"]`, the action covers `need_001` but not `need_002` in this set. If no other program covers `need_002`, Agent 6 raises `COVERAGE_GAP` for `need_002` even though the same program's action will include both needs in `related_need_ids` (populated correctly in Agent 8 from `m["need_ids"]`).

**Verified reproduction:**
```python
# Two housing sub-needs → both KB housing programs return matched_need_ids=['need_001','need_002']
# Agent 6 coverage check: covered = {'need_001'} (only first need_id)
# Result: spurious COVERAGE_GAP warning for need_002
```

**Severity:** P2. Agent 7 and Agent 10 (using `related_need_ids` from Agent 8) correctly show full need coverage; the spurious warning in Agent 6 would confuse downstream consumers of the Agent 6 result and the run report, but does not cause data loss or an incorrect plan. V12 will not fire incorrectly.

**Recommended correction:**
```python
covered = {n for a in actions for n in ([a["need_id"]] if a["need_id"] else [])}
# Or: look up matched need_ids from the match object for each action
```

---

### D-04 — P0 — Critical: Agents 1 and 2 are absent; agents.json is broken; no end-to-end run is possible

**Requirement:** Baseline Part C: Agent 1 (Crisis Understanding) and Agent 2 (Case Clarification) are mandatory roles. `STATUS.md` claims v3.1 implementation. Contracts §7: each owner's package exposes `handle(request: dict) -> dict`.

**File / evidence:**
- `navigator/agents/agent_1_2/` — contains only `README.md`; no `__init__.py`, no `.py` source, no `handle` function
- `agents.json` lines 2–3: declare `navigator.agents.agent_1_2:handle` for both agent_1 and agent_2

**Execution evidence (this audit):**
```
$ python3 -m navigator.supervisor.run --agents agents.json
Cannot load agents: Cannot connect agent_1: navigator.agents.agent_1_2 has no function 'handle'
Return code: 2
```
The Supervisor never starts. No pipeline step executes.

**Severity:** P0 — Critical MVP blocker. The primary integration path (`python -m navigator.supervisor.run --agents agents.json`) fails immediately. The demo, acceptance tests T01–T12, and end-to-end validation cannot run with this configuration.

**Recommended correction:** Commit the Agent 1/2 implementation (keyword/pattern rules described as v3.1 in `STATUS.md`) to `navigator/agents/agent_1_2/` with a proper `__init__.py` and `handle` function. Until then, update `agents.json` to point to `tests.fake_agents:agent_1` and `tests.fake_agents:agent_2` as a documented placeholder.

**Required regression coverage:** Add tests to `tests/agent_1_2/` covering the Baseline acceptance fixtures from §16, §19, §22 (story parsing, need extraction, clarification requests, no inferred needs).

---

### D-05 — P2 — Medium: Agent 8 repair response loses `potential_options` and `coverage_gaps` from the original plan

**Requirement:** Contracts §4.8: Agent 8 output includes `action_cards[]`, `potential_options[]`, and `coverage_gaps[]`. Supervisor §5.3: repair affects only flagged cards; unaffected parts of the plan should be preserved.

**File / function / line:** `navigator/agents/agent_6_7_8_10/agent_6_7_8_10.py`, `agent_8()`, lines 335–336:
```python
result = {"plan_version": ..., "action_cards": cards,
          "potential_options": [], "coverage_gaps": [], ...}
```

**Root cause:** The repair path hard-codes empty `potential_options` and `coverage_gaps` regardless of what the original plan had. The Supervisor at `run.py` line 313–314 uses `r8["result"].get("potential_options", [])` and `r8["result"].get("coverage_gaps", [])` — so these are also lost on successful repair.

**Severity:** P2. `potential_options` (Government programs with missing eligibility facts — §30.5) and `coverage_gaps` are informational outputs. Their loss from a repaired plan may hide valid program hints and unmet needs from the user. In the current KB (no `potential_options` generated by mock agents), this is latent.

**Recommended correction:** Pass the original plan's `potential_options` and `coverage_gaps` through the repair response, or have the Supervisor preserve and reattach them.

---

### D-06 — P1 — High: Agent 2 candidate_requirements never populated in the current runner

**Requirement:** Contracts §4.2: Agent 2 may receive `candidate_requirements[]` (optional, after retrieval) for more targeted clarification questions. Baseline §B: "Supervisor merges duplicate/overlapping questions, checks existing Case facts, asks once and distributes the answer."

**File / function / line:** `navigator/supervisor/run.py`, `Run.execute()`, lines 253–260:
```python
if "agent_2" in self.agents:
    r2 = self.call(B.agent2_request(st))   # no candidate_requirements
```
Agent 2 is called before Agent 3; `candidate_requirements` from Agent 3's result can never be passed because Agent 3 has not run yet.

**Root cause:** The pipeline sequence (Agent 2 → Agent 3) does not allow a post-retrieval Agent 2 pass. The contract allows for a second Agent 2 call with candidate_requirements, but no such second call is implemented. This also means program-specific clarification questions (e.g., questions that only make sense once specific program candidates are known) are never generated.

**Severity:** P1. Affects quality of clarification for all cases where retrieval candidates would inform Agent 2's questions. Not a data safety issue, but reduces the quality of the clarification dialogue relative to the approved design.

**Recommended correction:** Add a second Agent 2 call after Agent 3, passing `candidate_requirements` built from Agent 3 candidates.

---

### D-07 — P1 — High: Clarification deduplication not implemented

**Requirement:** Baseline §B and §30.8 APPROVED: "Supervisor checks existing Case facts, consolidates duplicate or overlapping requests, asks each necessary question once via the application UI, and distributes the centrally recorded answer to every relevant agent."

**File / function / line:** `navigator/supervisor/run.py`, lines 257–260:
```python
if r2.get("clarification_requests"):
    self.supervisor_issues.append(checks.issue("CLARIFICATION_PENDING", "info", ...))
```

**Root cause:** Clarification requests from Agent 2 (and potentially other agents) are only logged as `CLARIFICATION_PENDING` supervisor issues. There is no deduplication logic, no check against existing case facts, no ask-once mechanism, no answer distribution, and no `already_asked` list update. The demo proceeds without answering any clarification questions.

**Severity:** P1. Without deduplication and routing, multiple agents could ask the same question (e.g., household income) in parallel. The user experience would be incorrect. The approved architecture boundary (§30.8) is not yet implemented. This is a design gap rather than a runtime defect in the current mock-only system, but it must be addressed before any UI layer can be connected.

---

## 5. Architectural Risks Requiring Verification

### AR-01 — Architectural boundary: No Application Layer exists

**Requirement:** Baseline §B, §D, §30.3: "Application Layer alone commits approved Case/plan changes in SQL after validation and version checks." §30.7: "Optional email registration saves relevant facts under user_id/case_id in SQL."

**Finding:** No Application Layer, SQL schema, or persistence implementation exists anywhere in the repository. `CaseState` in `builders.py` is in-memory only (no SQL write). Session data is lost when the process ends.

**Risk:** Any SQL implementation built later must be verified to (a) check `case_version` before committing, (b) never overwrite user-entered `progress_status`, and (c) preserve all user-set action statuses during reassessment. These are baseline requirements (T04, T09) that cannot be validated without an Application Layer.

**Owner verification needed:** Slav (Supervisor/integration) — no Application Layer owner is identified.

---

### AR-02 — Architectural boundary: Status-only changes must not trigger reassessment

**Requirement:** Baseline §B: "A user edit that changes relevant case facts is a reported change. Status-only updates do not trigger reassessment."

**Finding:** Not testable in the current system (no UI, no Application Layer). The `CaseState.bump_version()` method is called only in `confirm_agent1()`. No path exists yet where a user `progress_status` update reaches the Supervisor. The risk is that a future UI/Application Layer implementation inadvertently bumps the `case_version` on status-only changes, triggering unnecessary re-runs.

---

### AR-03 — Architectural boundary: Agent 2 `already_asked` list is populated in tests but not persisted

**Requirement:** Contracts §4.2: `already_asked[]` prevents re-asking answered or declined questions. Baseline §B: "no new intake or automatic full reassessment solely because the user logs in."

**Finding:** `CaseState.already_asked` is populated in `agent2_request()` from `state.already_asked`, but nothing in the runner updates `state.already_asked` after a clarification is asked or answered. The list is never written back. On a returning-user scenario, `already_asked` would always be empty, causing repeated questions.

**Risk:** Without Application Layer persistence for `already_asked`, returning users will be re-asked questions they already answered. This directly violates the Baseline approval for resumed sessions.

---

### AR-04 — Source policy not enforced at Agent 3

**Requirement:** Contracts §4.3: `source_policy = verified_kb_only` until Oct 26; `kb_plus_external` from Oct 27 (Julia's plan). Agent 3 contract explicitly states "external discovery is P2."

**Finding:** `source_policy` is passed in the envelope but Agent 3 (`agent_3.py`) never reads or enforces it. Agent 3 always reads the verified KB only. This is correct behavior for the current state (external discovery is not built) but creates a risk: a future Agent 3 version that does external discovery must check `source_policy`. There is no runtime gate preventing an Agent 3 with `source_policy = verified_kb_only` from performing external discovery.

**Risk:** Medium. In the current mock-only system this is benign. Needs a check when external discovery is added.

---

### AR-05 — IBM watsonx Orchestrate integration absent

**Requirement:** `STATUS.md` (Oct 27): "A local prototype does not count as completed IBM integration." IBM submission requires IBM technology use to be visible. The Technology Statement must describe where IBM Bob and watsonx.ai / watsonx Orchestrate were used.

**Finding:** No IBM Orchestrate integration, no IBM Granite model calls, and no watsonx.ai API integration is present. All agents are pure Python keyword/rule-based mocks. Bob sessions are present for Hisham and Silver (`bob_sessions/`); no Yogesh or Slav sessions are visible.

**Risk:** High submission risk. If the "clear use of IBM technology" judging criterion requires demonstrated Orchestrate/watsonx use beyond IBM Bob development sessions, the current state may not satisfy it.

---

## 6. Missing Components and Integration Gaps

| Component | Status | Contract reference | Impact |
|---|---|---|---|
| Agent 1 (Crisis Understanding) | Not committed | Contracts §4.1, Baseline Part C | P0 blocker — no end-to-end run possible |
| Agent 2 (Case Clarification) | Not committed | Contracts §4.2, Baseline Part C | P0 blocker (in agents.json) |
| Agent 9 (Personal Navigation) | Not built | Contracts §8 (deferred) | Deferred by design; no end-user navigation support |
| UI layer | Not built | Baseline §D, §B | Users cannot interact with the system |
| Application Layer / SQL | Not built | Baseline §D, §30.3, §30.7 | No persistence, no case recovery, no status preservation |
| Email / account flows | Not built | Contracts §8 (deferred) | Registered-user case recovery not possible |
| IBM watsonx Orchestrate integration | Not started | Baseline §H gate 3, STATUS.md explicit | Affects submission score |
| Public prototype link | Not available | SUBMISSION_PLAN.md §2 item 4 | Required submission deliverable |
| `requirements.txt` / CI | Not present | Contracts §7 integration instructions | No reproducible test command |
| tests/agent_1_2/ | Empty | Contracts §7 (tests per owner) | Zero coverage for Agent 1/2 |
| Baseline acceptance tests T01–T12 | Not covered by existing tests | Baseline §H | Build gate 4 not achieved |

### Agent 9 specific note
Agent 9's contract is explicitly deferred to "the next phase" (Contracts §8, "Not in v1.0"). Its role — supporting user navigation of the existing plan without rewriting it — depends on the Application Layer and UI not yet built. This is an **approved deferral**, not a defect.

---

## 7. Approved Limitations and Deferred Functionality

| Item | Basis | Current state |
|---|---|---|
| Agent 9 not built | Contracts §8: "follow after Oct 26 when owners are assigned" | Correctly absent from agents.json |
| All agents mock (`is_mock: true`) | Contracts §7 §3: "until your logic is ready, return a fixed result with is_mock: true" | Correctly flagged; run report marks `partially_mocked` |
| External discovery (Agent 3, `kb_plus_external`) | Contracts §4.3: "external discovery not built"; PROPOSED P2 | Correctly deferred |
| `source_policy` enforcement | Contracts §4.3: verified_kb_only is the current policy | KB-only is enforced by Agent 3 (though policy not explicitly checked) |
| Progress statuses 5 vs 6 | Decision 11: PENDING JULIA | Six values implemented as default; correct |
| Evidence freshness window Q7 | Decision 12: PENDING JULIA | Age reported as info only; correct |
| Funeral/burial assistance | Decision 7: P2, PENDING JULIA | Not in KB; correct |
| One-time charity emergency grants | Decision 8: P2, PENDING JULIA | Not in KB; correct |
| IBM Orchestrate integration | STATUS.md explicit deferral | Local prototype acknowledged as insufficient |

---

## 8. Tests Executed — Passed and Failed Results

All tests were executed on the Nov 3 snapshot of the repository. No test files were modified.

### 8.1 Python unittest suite (`python3 -m unittest discover tests -v`)

**Result: 75 passed, 1 FAILED (of 76 total)**

| Test file | Tests | Pass | Fail |
|---|---|---|---|
| `tests/agent_3_4_5/test_agents_3_4_5.py` | 20 | 20 | 0 |
| `tests/test_builders.py` | 13 | 12 | **1** |
| `tests/test_checks.py` | 15 | 15 | 0 |
| `tests/test_run.py` | 8 | 8 | 0 |
| `tests/test_run_v2.py` | 20 | 20 | 0 |

**Failing test:**
```
FAIL: test_planning_package_availability_and_timing (test_builders.TestWithKB)
AssertionError: 'confirmed_open' != 'temporarily_closed'
```
Root cause: See Defect D-02. Test expects pre-Nov 2 KB state; KB was correctly updated.

### 8.2 Agent 6/7/8/10 script (`python3 tests/agent_6_7_8_10/run_tests.py`)

**Result: 54 of 54 checks PASSED**

Parts A, B, and C all pass, including:
- A6-1 through A6-11: Agent 6 ordering, deadlines, eligibility wording
- A8/A10: plan passes Agent 10
- A10-1 through A10-4: guarantee flagging, card release
- A7-1: Q2 critical for conflicting deadline
- B-H1 through B-H8: Agent 10 V1–V10 rule coverage
- C-CL6/8/10a/10b: temporarily-closed program handling
- C-NAME, C-EVP: v1.1 card title with organization and eviction_prevention wording
- C-REP: repair round — flagged card rebuilt, flag addressed
- C-CON1–3: verified contacts in next_step with check date

### 8.3 Reproduction cases executed during this audit

| Case | Finding | Result |
|---|---|---|
| Repair-merge defect with real agent_8.handle | D-01 confirmed: card_01 lost from plan | **Confirmed defect** |
| agents.json end-to-end run | D-04 confirmed: AgentConfigError before any step | **Confirmed defect** |
| Nov 2 KB state | Saint John's `confirmed_open`; ev_sjhap_019/022 superseded | KB state verified |
| S4 enum check in program_availability | `closed` value correctly rejected | Passes |
| S9 privacy patterns | SSN, card, routing patterns masked / rejected | Passes |
| Clarification deduplication | run.py only logs CLARIFICATION_PENDING | D-07 confirmed |
| Multi-need coverage check | Agent 6 `covered` set uses only `need_ids[0]` | D-03 confirmed |
| Agent 9 absence | Correctly absent, not referenced in agents.json | OK — deferred |
| `already_asked` persistence | CaseState never written back after answers | AR-03 confirmed |
| Guarantee detection in templates | No guarantee language in any TEMPLATES entry | Passes |
| V9: user date vs official deadline | Builders correctly separate the two | Passes |

### 8.4 Tests NOT executed

- `tests/agent_1_2/`: no test files exist (see D-04).
- Baseline acceptance tests T01–T12: not implemented as automated tests.
- IBM Orchestrate / watsonx integration tests: infrastructure not available.
- End-to-end run with real Agents 1 and 2: code does not exist.
- Performance / load testing: out of scope.

---

## 9. Missing Documents and Their Effect on Audit Confidence

| Document | Status | Conclusions affected |
|---|---|---|
| TEAM UPDATE — MASTER DEVELOPMENT PLAN (Pages file) | **Unavailable** (Pages format not readable in this environment) | Owner assignments beyond those in README.md, STATUS.md, and Contracts are unverified. The responsibility map from the audit brief was used. |
| MVP Technical Breakdown (Nov 1, 2026) | **Not present in repository** | Technology choices, owner names, estimates, and schedule items from that document cannot be verified. Per audit brief, it is PROPOSED and not treated as approved requirements here. |
| Shared JSON Contracts v1.0 (as a standalone document) | Not a separate file — v1.1 is the current file | v1.0 frozen baseline is embedded in v1.1 via Section 9 change log and FROZEN annotations. No conclusions depend on the separate v1.0 document. |
| Approved acceptance of specific v1.1 PROPOSED items | No separate acceptance record in the repository | Items marked PROPOSED in v1.1 are treated as defaults pending explicit acceptance or rejection. Their implementation in code is noted. |
| Integration Run report (Oct 23, 2026) | No standalone report; STATUS.md describes an Oct 27 run instead | Historical execution claims from before Nov 2 cannot be independently reproduced because the KB now reflects the Nov 2 state. |

---

## 10. Prioritized Correction Plan

### Immediate (P0 — before any further development or submission work)

**P0-1 — Commit Agent 1 and Agent 2 modules** (Owner: Yogesh)  
Create `navigator/agents/agent_1_2/__init__.py` and at minimum an `agent_1.py` and `agent_2.py` exposing `handle(request: dict) -> dict`. The v3.1 keyword/pattern implementation described in `STATUS.md` is the target content. As an immediate bridge, update `agents.json` to point to `tests.fake_agents:agent_1` and `tests.fake_agents:agent_2` so the end-to-end demo can run today.  
Add tests to `tests/agent_1_2/` covering Baseline fixtures from §16, §19, §22 (no inferred needs, no invented needs, correct need extraction, Agent 2 clarification policies, `already_asked` logic).

**P0-2 — Fix repair-merge defect in Supervisor** (Owner: Slav)  
Implement the card-merge logic in `navigator/supervisor/run.py` `execute()` so that passing cards from round 0 are preserved after a successful repair. Add a regression test using real agent_8 handle or a faithful fake. See D-01 for the recommended correction.

### High Priority (P1 — before Nov 8 readiness milestone)

**P1-1 — Fix stale test in test_builders.py** (Owner: Slav)  
Update `test_planning_package_availability_and_timing` to handle both `temporarily_closed` and `confirmed_open` states. See D-02.

**P1-2 — Implement second Agent 2 call with candidate_requirements** (Owner: Slav)  
After Agent 3, call Agent 2 again with `candidate_requirements` built from Agent 3 candidates. Update `agent2_request()` builder and the runner flow. See D-06.

**P1-3 — Implement clarification deduplication in Supervisor** (Owner: Slav)  
Replace the `CLARIFICATION_PENDING` log entry with: check existing case facts, merge overlapping requests, ask once, record in `already_asked`, distribute answer. See D-07.

**P1-4 — Persist `already_asked` list** (Owner: Slav)  
On any clarification interaction, update `state.already_asked` so returning users are not re-asked answered questions. See AR-03.

### Medium Priority (P2 — before Nov 22 submission)

**P2-1 — Fix Agent 6 multi-need coverage check** (Owner: Hisham)  
Expand `covered` set to include all `need_ids` from each action's match, not just `need_ids[0]`. See D-03.

**P2-2 — Preserve potential_options and coverage_gaps through repair** (Owner: Hisham)  
In Agent 8 repair path, carry forward `potential_options` and `coverage_gaps` from the original plan payload, not empty lists. See D-05.

**P2-3 — Add repair handlers for V3, V6, and V13** (Owner: Hisham)  
Currently unhandled repair rules cause immediate card withheld after max rounds. Adding specific repair logic (remove confirmed-mismatch card from recommendations, add a next_step, remove prohibited navigation request) would improve plan quality.

### Architecture / Design Work (before submission)

**A-1 — Design and implement Application Layer skeleton** (Owner: TBD)  
Even a minimal in-memory Application Layer with a version check stub would allow T04 (stale case version) and T09 (status-only change) to be demonstrated as passing.

**A-2 — Define IBM integration path** (Owner: Julia decision)  
Clarify which components will use IBM Granite / watsonx.ai for the demo video, and which will use IBM watsonx Orchestrate. Document clearly for the Technology Statement. The current system uses no IBM AI model calls.

**A-3 — Add `requirements.txt` and CI test command** (Owner: Slav)  
Create `requirements.txt` (even if empty for standard-library-only code) and a Makefile or `.github/workflows/` entry so any reviewer can reproduce the test results with one command.

**A-4 — Run Baseline acceptance tests T01–T12** (Owner: Julia)  
These are the approved integration gates. None are currently automated. They should be formalized as tests in `tests/` and shown as passing before Nov 8.

---

## Appendix: Architecture Boundary Verification Summary

| Boundary | Status | Evidence |
|---|---|---|
| Applicant manually controls Action Card progress | ✅ Implemented | Agent 8 always sets `progress_status = "not_started"`; Agent 10 V10 flags any other value; test B-H8 passes |
| Agents do not automatically mark actions complete | ✅ Implemented | No agent writes `progress_status` other than `not_started` |
| Agents do not submit applications, send reminders, track progress | ✅ Implemented | No such logic in any agent or Supervisor |
| Agent 9 does not independently rewrite the plan | ✅ N/A (Agent 9 not built) | Correctly deferred |
| Supervisor coordinates agents and controlled revisions | ✅ Implemented | run.py orchestrates all agent calls |
| All clarification requests route through Supervisor | ⚠️ Partially implemented | Agents do not directly contact users; but deduplication and ask-once not yet built (D-07) |
| Supervisor checks existing facts before asking | ❌ Not implemented | See D-07 |
| Agents do not write to SQL or Knowledge Base | ✅ Implemented | No SQL writes anywhere; Agent 5 `update_proposals[]` is advisory only, not written |
| Application Layer validates and persists changes | ❌ Not built | See AR-01 |
| One continuing Case and plan | ⚠️ In-memory only | CaseState is in-memory; no persistence yet |
| Status-only changes do not trigger reassessment | ⚠️ Not testable | No UI or Application Layer to test T09 |
| Evidence, eligibility, availability kept separate | ✅ Implemented | Three separate fields enforced in ProgramRecord; contract S4 checks enums; Agent 6 reads `effective_date` for reopening |
| Unknown facts not converted to rejection | ✅ Implemented | Agent 4: unknown income → `missing_case_facts`, never `confirmed_mismatch`; test T2 passes |
| No fabricated programs or hallucinated resources | ✅ Implemented | Agent 3 KB-only; Agent 10 V8 flags invented programs; test B-H5 passes |
| User dates never shown as official deadlines | ✅ Implemented | Builders separate `user_target_date` and `official_deadline`; Agent 10 V9 flags violations; test B-H6 passes |
| SSN/PII not captured by Navigator | ✅ Implemented | S0 masking before Agent 1; S9 rejects results containing PII patterns |
| Closed programs not presented as current help | ✅ Implemented | Agent 6 moves temporarily_closed to `later`; Agent 10 V4 flags violations; tests C-CL6/10 pass |

---

*This report was produced by live code inspection, test execution, and targeted reproduction cases. No project source files, tests, or configuration files were modified during this audit. All findings are based on the Nov 3 snapshot; conclusions about approved statuses are based on document evidence available in the repository.*
