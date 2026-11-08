"""Supervisor runner: one end-to-end cycle, Agent 1 → 10 (Shared JSON Contracts v1.1, sections 1 and 5).

Usage (from the repo root):
    python -m navigator.supervisor.run --agents agents.json
    python -m navigator.supervisor.run --agents agents.json --demo-broken      # Supervisor rejects sample 03
Options: --kb PATH  --story-file PATH  --correct field=value  --out run_report.json  --no-isolate
"""
import argparse
import concurrent.futures
import copy
import datetime
import difflib
import importlib
import json
import multiprocessing
import os
import sys
import time
import uuid
from dataclasses import dataclass, field

from navigator.supervisor import builders as B
from navigator.supervisor import checks
from navigator.supervisor import contract as C

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KB = os.path.join(HERE, "..", "kb", "kb_sacramento.json")
SAMPLES = os.path.join(HERE, "..", "samples")
MAX_RETRIES = 1          # contract 5.3: 1 retry per agent call
MAX_REPAIR_ROUNDS = 2    # contract 5.3: 2 repair rounds after an Agent 10 FLAG


def merge_repaired_plan(current_plan, repair_result):
    """Merge a repair-round Agent 8 result into the current plan.

    repaired_card_ids must be present and be a list of strings.  If it is
    absent or is not a list of strings (e.g. a bare string, a number, or a
    list containing a non-string), nothing is merged, the current plan is
    kept unchanged, and REPAIR_IDS_INVALID (warning) is added to issues.

    When merging: replace only the listed cards in the current plan (keeping
    original order); leave all other cards, potential_options and coverage_gaps
    unchanged.  If the repair result has no plan_version, keep the current
    plan's plan_version.

    Returns (new_plan, issues).  Issues use codes REPAIR_UNKNOWN_CARD,
    REPAIR_CARD_MISSING, and REPAIR_IDS_INVALID (all severity warning).
    """
    res = repair_result.get("result", {})
    repaired_ids = res.get("repaired_card_ids")

    # repaired_card_ids absent or not a list of strings → keep current plan unchanged
    if repaired_ids is None or not (
            isinstance(repaired_ids, list) and all(isinstance(i, str) for i in repaired_ids)):
        msg = ("Repair result has no repaired_card_ids; current plan kept"
               if repaired_ids is None else
               f"repaired_card_ids is not a list of strings "
               f"({type(repaired_ids).__name__}); current plan kept")
        return current_plan, [checks.issue("REPAIR_IDS_INVALID", "warning", msg)]

    issues = []
    returned_by_id = {c["card_id"]: c for c in res.get("action_cards", [])}
    current_by_id = {c["card_id"]: c for c in current_plan.get("action_cards", [])}

    # Check for cards returned that are not in the current plan
    for cid in returned_by_id:
        if cid not in current_by_id:
            issues.append(checks.issue(
                "REPAIR_UNKNOWN_CARD", "warning",
                f"Repair result returned unknown card_id {cid!r}; not added to plan",
                cid))

    # Build the new card list: replace listed cards, keep others in order
    new_cards = []
    for card in current_plan.get("action_cards", []):
        cid = card["card_id"]
        if cid in repaired_ids:
            if cid in returned_by_id:
                new_cards.append(returned_by_id[cid])   # replaced with repaired version
            else:
                # Listed in repaired_card_ids but missing from returned cards
                issues.append(checks.issue(
                    "REPAIR_CARD_MISSING", "warning",
                    f"Card {cid!r} listed in repaired_card_ids but missing from repair result; keeping old card",
                    cid))
                new_cards.append(card)                  # keep old card
        else:
            new_cards.append(card)                      # untouched

    new_plan = {
        "plan_version": res.get("plan_version") if res.get("plan_version") is not None
                        else current_plan.get("plan_version"),
        "action_cards": new_cards,
        "potential_options": current_plan.get("potential_options", []),
        "coverage_gaps": current_plan.get("coverage_gaps", []),
    }
    return new_plan, issues


# ---------------------------------------------------------------- loading team components
class AgentConfigError(Exception):
    """agents.json is wrong. The message says exactly what to fix."""


@dataclass
class AgentRef:
    """Where an agent lives: module + function name, plus the folders needed to import it.

    Kept as names (not only the function) so the agent can be started in its own process (see call()).
    """
    module: str
    func: str
    paths: list = field(default_factory=list)       # extra sys.path folders
    nav_paths: list = field(default_factory=list)   # extra navigator/ package folders

    def load(self):
        _extend_paths(self.paths, self.nav_paths)
        return getattr(importlib.import_module(self.module), self.func)


def _extend_paths(paths, nav_paths):
    import navigator
    for p in nav_paths:
        if p not in navigator.__path__:
            navigator.__path__.append(p)
    for p in paths:
        if p not in sys.path:
            sys.path.append(p)


def load_agents(config_path):
    """agents.json: {"paths": [folders], "agents": {"agent_1": "module:function", ...}}.

    Folders that contain a navigator/ package are merged into one navigator package,
    the same layout as the shared repository (contract 7.4).
    Every problem is reported as AgentConfigError with a one-line explanation.
    """
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        raise AgentConfigError(f"File not found: {config_path}")
    except json.JSONDecodeError as e:
        raise AgentConfigError(f"{config_path} is not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}")

    base = os.path.dirname(os.path.abspath(config_path))
    paths, nav_paths = [], []
    for p in cfg.get("paths", []):
        full = os.path.normpath(os.path.join(base, p))
        if not os.path.isdir(full):
            raise AgentConfigError(f"Folder in \"paths\" does not exist: {p} (resolved to {full})")
        paths.append(full)
        if os.path.isdir(os.path.join(full, "navigator")):
            nav_paths.append(os.path.join(full, "navigator"))
    _extend_paths(paths, nav_paths)

    agents = {}
    for role, target in cfg.get("agents", {}).items():
        if role not in C.ROLES:
            raise AgentConfigError(f"Unknown role {role!r} in agents.json; allowed: {', '.join(C.ROLES)}")
        if not isinstance(target, str) or target.count(":") != 1:
            raise AgentConfigError(f"{role}: {target!r} must look like \"module:function\"")
        module, func = target.split(":")
        try:
            mod = importlib.import_module(module)
        except ModuleNotFoundError as e:
            raise AgentConfigError(f"Cannot connect {role}: module {module!r} not found ({e}). Check \"paths\".")
        except Exception as e:
            raise AgentConfigError(f"Cannot connect {role}: importing {module!r} failed — {type(e).__name__}: {e}")
        if not callable(getattr(mod, func, None)):
            names = [n for n in dir(mod) if callable(getattr(mod, n, None)) and not n.startswith("_")]
            hint = difflib.get_close_matches(func, names, n=1)
            raise AgentConfigError(f"Cannot connect {role}: {module} has no function {func!r}"
                                   + (f" — did you mean {hint[0]!r}?" if hint else ""))
        agents[role] = AgentRef(module, func, paths, nav_paths)
    return agents


# ---------------------------------------------------------------- agent call in its own process
def _child(ref, request, conn):
    """Runs in a separate process: import the agent, call it, send back JSON text or the error."""
    try:
        handle = ref.load()
        conn.send(("ok", json.dumps(handle(request), default=str)))
    except BaseException as e:   # report everything, including SystemExit from an agent
        conn.send(("error", f"{type(e).__name__}: {e}"))
    finally:
        conn.close()


def _call_in_process(ref, request, timeout):
    """Returns (result | None, error_text | None, timed_out: bool).

    On timeout the agent's process is terminated, so a hung agent does not keep running.
    "spawn" is used everywhere (it is the Windows default), so behaviour is the same on every OS.
    """
    ctx = multiprocessing.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_child, args=(ref, request, child), daemon=True)
    proc.start()
    child.close()
    try:
        if not parent.poll(timeout):
            return None, None, True
        kind, payload = parent.recv()
        if kind == "ok":
            return json.loads(payload), None, False
        return None, payload, False
    except EOFError:
        return None, f"agent process ended without a result (exit code {proc.exitcode})", False
    finally:
        if proc.is_alive():
            proc.terminate()
        proc.join(5)
        parent.close()


def _call_in_thread(fn, request, timeout):
    """Same contract as _call_in_process for plain functions (used by tests and fake agents)."""
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(fn, request)
        return json.loads(json.dumps(future.result(timeout=timeout), default=str)), None, False
    except concurrent.futures.TimeoutError:
        return None, None, True
    except Exception as e:
        return None, f"{type(e).__name__}: {e}", False
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _today():
    """Return today's date.  Replaced by tests via unittest.mock.patch."""
    return datetime.date.today()


# Exception types that indicate a malformed accepted result (FIX 5 safety net).
_INPUT_EXC = (KeyError, TypeError, ValueError, AttributeError, IndexError)


# ---------------------------------------------------------------- one checked call
class Run:
    def __init__(self, agents, kb_path, ids=None, isolate=False, ref_date=None):
        """agents: role -> AgentRef (from agents.json) or a plain function (tests).

        isolate=True runs every AgentRef in its own process (a timeout really stops it).
        ref_date: a datetime.date used as the reference date for Agents 1, 6, 8 and 10.  Defaults
        to today's date at the moment the run starts.
        """
        self.agents = agents
        self.isolate = isolate
        self.programs, self.evidence = B.load_kb(kb_path)
        rid = uuid.uuid4().hex[:8]
        case_id, run_id, corr_id = ids or (f"case-{rid}", f"run-{rid}", f"corr-{rid}")
        self.state = B.CaseState(case_id, run_id, corr_id)
        self.steps = []        # run report rows
        self.supervisor_issues = []
        self.agent7_findings = []
        self._loaded = {}
        self._last_r10 = None        # last accepted Agent 10 result (FIX 6)
        self._last_r10_round = None  # repair_round index of that result
        # Use the supplied date or today; fixed for the whole run (Fix 2)
        self.ref_date = ref_date if ref_date is not None else _today()

    def known_refs(self):
        known = {"program_id": set(self.programs), "evidence_id": set(self.evidence)}
        if self.state.needs:
            known["need_id"] = {n["need_id"] for n in self.state.needs}
        return known

    def _invoke(self, role, request):
        agent = self.agents[role]
        if isinstance(agent, AgentRef):
            if self.isolate:
                return _call_in_process(agent, request, C.TIMEOUT_SECONDS)
            if role not in self._loaded:
                self._loaded[role] = agent.load()
            return _call_in_thread(self._loaded[role], request, C.TIMEOUT_SECONDS)
        return _call_in_thread(agent, request, C.TIMEOUT_SECONDS)

    def call(self, req):
        """Call one agent with timeout, check the result (S1–S9), retry once. Returns result or None."""
        role = req["role_id"]
        if role not in self.agents:
            self.steps.append({"request_id": req["request_id"], "role_id": role, "accepted": False,
                               "status": None, "issues": [checks.issue("AGENT_NOT_CONNECTED", "critical",
                                                                       f"No component registered for {role}")]})
            return None
        for attempt in range(1 + MAX_RETRIES):
            t0 = time.monotonic()
            result, error, timed_out = self._invoke(role, copy.deepcopy(req))   # agents never get our objects
            seconds = time.monotonic() - t0
            if timed_out:
                ok, issues, seconds = False, checks.s7_timeout(None), None
            elif error:
                ok, issues = False, [checks.issue("AGENT_EXCEPTION", "critical", error)]
            else:
                ok, issues = checks.check_result(req, result, self.state.case_version,
                                                 self.known_refs(), seconds)
            self.steps.append({"request_id": req["request_id"], "role_id": role, "attempt": attempt + 1,
                               "status": (result or {}).get("status"), "accepted": ok,
                               "is_mock": (result or {}).get("is_mock"),
                               "seconds": round(seconds, 3) if seconds is not None else None,
                               "issues": issues})
            if ok:
                self.state.results[req["request_id"]] = result
                return result
            if any(i["code"] in ("STALE_RESULT", "PRIVACY_VIOLATION") for i in issues):
                break           # a retry would not fix these
        return None

    def _input_error(self, stage, exc):
        """Record SUPERVISOR_INPUT_ERROR for a builder exception.

        No user data in the message: only the exception type and, for KeyError
        with a non-empty string key, the key name.
        """
        exc_type = type(exc).__name__
        if isinstance(exc, KeyError) and exc.args and isinstance(exc.args[0], str):
            detail = f"{exc_type}: {exc.args[0]}"
        else:
            detail = exc_type
        self.supervisor_issues.append(checks.issue(
            "SUPERVISOR_INPUT_ERROR", "critical",
            f"{stage} input could not be processed: {detail}", None))

    def review(self, stage, req, result):
        """Agent 7 reviews a stage (contract 4.7). It never blocks: a missing or failed review is reported only."""
        if "agent_7" not in self.agents:
            if not any(i["code"] == "AGENT_7_NOT_CONNECTED" for i in self.supervisor_issues):
                self.supervisor_issues.append(checks.issue(
                    "AGENT_7_NOT_CONNECTED", "warning", "Stages were not reviewed by Agent 7"))
            return
        r7 = self.call(B.agent7_request(self.state, stage, result["result"], self.evidence, req["request_id"]))
        if r7 is None:
            self.supervisor_issues.append(checks.issue(
                "AGENT_7_REVIEW_MISSING", "warning", f"Agent 7 review of the {stage} stage was not accepted"))
            return
        self.agent7_findings += r7["result"].get("findings", [])

    # ---------------------------------------------------------------- the cycle
    def execute(self, story_text, corrections=None):
        """One end-to-end cycle.  Any builder exception is caught once here."""
        self._stage = "agent_1"   # always set before the try so the handler has a stage
        try:
            return self._execute_body(story_text, corrections)
        except _INPUT_EXC as exc:
            self._input_error(self._stage, exc)
            return self.report(f"stopped_at_{self._stage}")

    def _execute_body(self, story_text, corrections=None):
        """Cycle body; sets self._stage before every builder step."""
        st = self.state
        self._stage = "agent_1"
        q1, s0 = B.agent1_request(st, story_text, ref_date=self.ref_date)
        self.supervisor_issues += s0
        r1 = self.call(q1)
        if r1 is None:
            return self.report("stopped_at_agent_1")
        self._stage = "agent_1"        # confirm_agent1 reads r1
        B.confirm_agent1(st, r1, corrections)            # user confirms the summary (simulated here)

        self._stage = "agent_2"
        if "agent_2" in self.agents:                     # soft step: it improves data, nothing depends on it
            r2 = self.call(B.agent2_request(st))
            if r2:
                self.supervisor_issues += B.apply_need_updates(st, r2)
                if r2.get("clarification_requests"):
                    self.supervisor_issues.append(checks.issue(
                        "CLARIFICATION_PENDING", "info",
                        f"{len(r2['clarification_requests'])} question(s) for the user; demo continues without an answer"))

        self._stage = "agent_3"
        q3, geo_issues = B.agent3_request(st)
        self.supervisor_issues += geo_issues
        r3 = self.call(q3)
        if r3 is None:
            return self.report("stopped_at_agent_3")
        self.review("retrieval", q3, r3)
        self._stage = "agent_4"
        q4 = B.agent4_request(st, q3, r3, self.programs, self.evidence)
        r4 = self.call(q4)
        if r4 is None:
            return self.report("stopped_at_agent_4")
        self.review("matching", q4, r4)
        self._stage = "agent_5"
        q5 = B.agent5_request(st, q4, r4)
        r5 = self.call(q5)
        if r5 is None:
            return self.report("stopped_at_agent_5")
        self.review("verification", q5, r5)

        self._stage = "agent_6"
        pkg = B.planning_package(st, self.programs, self.evidence, r3, r4, r5, self.agent7_findings)
        q6 = B.agent6_request(st, pkg, [q3["request_id"], q4["request_id"], q5["request_id"]],
                              ref_date=self.ref_date)
        r6 = self.call(q6)
        if r6 is None:
            return self.report("stopped_at_agent_6")
        self.review("planning", q6, r6)
        self._stage = "agent_8"
        pkg["agent7_findings"] = self.agent7_findings
        q8 = B.agent8_request(st, pkg, q6, r6, ref_date=self.ref_date)
        r8 = self.call(q8)
        if r8 is None:
            return self.report("stopped_at_agent_8")

        # Agent 10 + repair rounds (contract 5.3)
        # Keep the "current plan" so a repair round that returns only the fixed
        # cards does not erase the rest (Fix 1 / contracts v1.2 proposal).
        self._stage = "agent_8"        # building current_plan reads r8
        current_plan = {
            "plan_version": r8["result"].get("plan_version"),
            "action_cards": r8["result"].get("action_cards", []),
            "potential_options": r8["result"].get("potential_options", []),
            "coverage_gaps": r8["result"].get("coverage_gaps", []),
        }
        withheld = []
        for repair_round in range(MAX_REPAIR_ROUNDS + 1):
            self._stage = "agent_10"
            q10 = B.agent10_request(st, pkg, q8, current_plan, repair_round,
                                    ref_date=self.ref_date)
            r10 = self.call(q10)
            if r10 is None:
                return self.report("stopped_at_agent_10")
            self._last_r10 = r10          # remember last accepted Agent 10 result
            self._last_r10_round = repair_round
            self._stage = "agent_10"   # reading flags from r10
            flags = [f for f in r10["result"].get("flags", []) if f.get("blocks_release")]
            if not flags:
                break
            if repair_round == MAX_REPAIR_ROUNDS:
                self._stage = "agent_10"
                withheld = sorted({f["card_id"] for f in flags})
                break
            # Send blocking flags to Agent 8 so it can repair those cards only
            self._stage = "agent_8_repair"
            q8_repair = B.agent8_request(st, pkg, q6, r6, ref_date=self.ref_date)
            q8_repair["payload"]["repair_flags"] = flags
            r8_repair = self.call(q8_repair)
            if r8_repair is None:
                return self.report("stopped_at_agent_8_repair")
            self._stage = "agent_8_repair"
            # Merge repair result into the current plan (Fix 1)
            current_plan, merge_issues = merge_repaired_plan(current_plan, r8_repair)
            self.supervisor_issues += merge_issues
            # Update q8 so the next Agent 10 request references the repair call
            q8 = q8_repair

        self._stage = "agent_10"       # final card filter reads withheld / current_plan
        cards = [c for c in current_plan["action_cards"] if c["card_id"] not in withheld]

        # Build withheld_cards: {card_id, rule_ids, reasons} from last blocking flags (FIX 6)
        withheld_cards = []
        if withheld and self._last_r10 is not None:
            last_flags = self._last_r10["result"].get("flags", [])
            for cid in withheld:
                blocking = [f for f in last_flags
                            if f.get("card_id") == cid and f.get("blocks_release")]
                withheld_cards.append({
                    "card_id": cid,
                    "rule_ids": [f["rule_id"] for f in blocking],
                    "reasons":  [f["reason"]  for f in blocking],
                })

        plan = {"plan_version": current_plan["plan_version"], "action_cards": cards,
                "potential_options": current_plan["potential_options"],
                "coverage_gaps": current_plan["coverage_gaps"],
                "withheld_card_ids": withheld,
                "withheld_cards": withheld_cards}
        return self.report("completed", plan)

    def report(self, outcome, plan=None):
        # Build final_validation from last accepted Agent 10 result (FIX 6).
        # Included whenever Agent 10 ran, regardless of outcome.
        final_validation = None
        if self._last_r10 is not None:
            r10res = self._last_r10["result"]
            final_validation = {
                "verdict":            r10res.get("verdict"),
                "repair_rounds_used": self._last_r10_round,
                "flags": [
                    {k: f[k] for k in ("card_id", "rule_id", "severity",
                                       "blocks_release", "reason",
                                       "required_correction")}
                    for f in r10res.get("flags", [])
                ],
                "passed_card_ids": r10res.get("passed_card_ids", []),
            }
        return {
            "run_id": self.state.run_id, "case_id": self.state.case_id,
            "case_version": self.state.case_version, "outcome": outcome,
            "ref_date": self.ref_date.isoformat(),
            "partially_mocked": any(s.get("is_mock") for s in self.steps),
            "supervisor_issues": self.supervisor_issues,
            "agent7_findings": self.agent7_findings,
            "steps": self.steps,
            "plan": plan,
            "final_validation": final_validation,
        }


# ---------------------------------------------------------------- demo: a deliberately broken agent
def broken_agent_1(request):
    """Returns sample 03 (wrong request_id, unknown category) — the Supervisor must reject it."""
    with open(os.path.join(SAMPLES, "03_invalid_result_for_supervisor_test.json"), encoding="utf-8") as f:
        return json.load(f)


def print_summary(rep):
    print(f"\nRun {rep['run_id']} — outcome: {rep['outcome']}"
          f"{' (partially mocked)' if rep['partially_mocked'] else ''}")
    for s in rep["steps"]:
        mark = "ACCEPTED" if s["accepted"] else "REJECTED"
        notes = [f"{i['code']}: {i['message']}" for i in s["issues"] if i["severity"] != "info"]
        print(f"  {s['request_id']}  {s['role_id']:<9} try {s.get('attempt', 1)}  "
              f"{str(s['status']):<12} {mark}  " + ("; ".join(notes)[:150] if notes else ""))
    for i in rep["supervisor_issues"]:
        print(f"  supervisor: {i['code']} — {i['message']}")
    real = [f for f in rep.get("agent7_findings", []) if f.get("severity") != "info"]
    if rep.get("agent7_findings"):
        print(f"  agent 7: {len(rep['agent7_findings'])} finding(s), {len(real)} warning/critical")
        for f in real:
            print(f"    {f.get('rule_id')} {f.get('severity')}: {f.get('program_id')} — {f.get('description')}")
    if rep["plan"]:
        print(f"\nPlan: {len(rep['plan']['action_cards'])} card(s), withheld: {rep['plan']['withheld_card_ids'] or 'none'}")
        for c in rep["plan"]["action_cards"]:
            print(f"  [{c['order_group']}] {c['action_title']} — {c.get('program_id')} — {c['next_step']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run one Supervisor cycle")
    ap.add_argument("--agents", required=True, help="agents.json with paths and module:function per role")
    ap.add_argument("--kb", default=DEFAULT_KB)
    ap.add_argument("--story-file", help="text file with the user's story (default: sample 01)")
    ap.add_argument("--correct", action="append", default=[],
                    help="user correction at confirmation, e.g. cash_on_hand_approx=300")
    ap.add_argument("--demo-broken", action="store_true", help="replace Agent 1 with sample 03")
    ap.add_argument("--no-isolate", action="store_true",
                    help="run agents inside this process (faster; a timed-out agent keeps running)")
    ap.add_argument("--ref-date", metavar="YYYY-MM-DD",
                    help="reference date for Agents 1, 6, 8 and 10 (ISO format); defaults to today")
    ap.add_argument("--out", default="run_report.json")
    a = ap.parse_args(argv)

    # Validate --ref-date before doing any file loading
    ref_date = None
    if a.ref_date:
        try:
            ref_date = datetime.date.fromisoformat(a.ref_date)
        except ValueError:
            print(f"--ref-date {a.ref_date!r} is not a valid ISO date (YYYY-MM-DD)")
            return 2

    try:
        agents = load_agents(a.agents)
    except AgentConfigError as e:
        print(f"Cannot load agents: {e}")
        return 2
    if a.demo_broken:
        agents["agent_1"] = AgentRef("navigator.supervisor.run", "broken_agent_1")
    if a.story_file:
        with open(a.story_file, encoding="utf-8") as f:
            story = f.read()
    else:
        with open(os.path.join(SAMPLES, "01_agent1_request.json"), encoding="utf-8") as f:
            story = json.load(f)["payload"]["story_text"]
    corrections = {}
    for c in a.correct:
        k, v = c.split("=", 1)
        corrections[k] = json.loads(v) if v.replace(".", "", 1).isdigit() else v

    # Demo uses the IDs of sample 01, so only the two planted faults of sample 03 show
    ids = ("case-demo-001", "run-0001", "corr-0001") if a.demo_broken else None
    rep = Run(agents, a.kb, ids, isolate=not a.no_isolate, ref_date=ref_date).execute(story, corrections)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    print_summary(rep)
    print(f"\nFull report: {a.out}")
    return 0 if rep["outcome"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
