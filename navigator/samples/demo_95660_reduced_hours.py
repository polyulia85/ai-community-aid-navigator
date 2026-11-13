"""Demo: 'I have problems with housing and food. I need help.' with ZIP 95660 and employment reduced_hours.
Runs Agents 3-5 directly (real KB) with a hand-crafted Agent 1 output representing the example input.
Shows input story, interpreted needs/facts, and matching results.
Run from repo root: python3 navigator/samples/demo_95660_reduced_hours.py
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from navigator.agents.agent_3_4_5 import agent_3, agent_4, agent_5
from navigator.agents.agent_3_4_5.common import build_program_criteria_from_kb

# ---- INPUT -----------------------------------------------------------------
STORY = "I have problems with housing and food. I need help."
ZIP   = "95660"
EMPLOYMENT = "reduced_hours"

print("=" * 72)
print("EXAMPLE INPUT")
print("=" * 72)
print(f"  Story:             {STORY!r}")
print(f"  ZIP:               {ZIP}")
print(f"  Employment status: {EMPLOYMENT}  (partially unemployed)")
print()

# ---- SIMULATED AGENT 1 OUTPUT (hand-crafted for this story) ----------------
BASE = {"request_id": "req-demo-001", "run_id": "run-demo-001", "case_id": "case-demo-095660",
        "case_version": 1, "correlation_id": "corr-demo-001", "schema_version": "1.0",
        "allowed_case_facts": [], "upstream_result_refs": []}

NEEDS = [
    {"need_id": "need_001", "category": "housing_assistance", "subcategory": "rental_assistance",
     "description": "Behind on rent, need housing help", "urgency": "high"},
    {"need_id": "need_002", "category": "food_assistance", "subcategory": None,
     "description": "Not enough food at home", "urgency": "high"},
    {"need_id": "need_003", "category": "income_assistance", "subcategory": None,
     "description": "Hours cut (partially unemployed)", "urgency": "high"},
]
FACTS = [
    {"fact_id": "fact_001", "field": "zip_code",           "value": ZIP,
     "confirmation_status": "proposed", "source": "user_statement", "time_context": None},
    {"fact_id": "fact_002", "field": "employment_status",  "value": EMPLOYMENT,
     "confirmation_status": "proposed", "source": "user_statement", "time_context": None},
]
GEO = [ZIP, "Sacramento County"]  # Supervisor normally adds the county from the ZIP

print("INTERPRETED NEEDS (simulated Agent 1)")
for n in NEEDS:
    print(f"  [{n['need_id']}] {n['category']} — {n['description']}")
print()
print("CASE FACTS (simulated Agent 1)")
for f in FACTS:
    print(f"  {f['field']} = {f['value']}  ({f['confirmation_status']})")
print()

def req(role, task, payload):
    import copy
    r = copy.deepcopy(BASE); r.update(role_id=role, task_type=task, payload=payload); return r

# ---- AGENT 3: retrieval ----------------------------------------------------
r3 = req("agent_3", "retrieve_candidates", {"needs": NEEDS, "geography": GEO, "retrieval_constraints": []})
out3 = agent_3.handle(r3)
candidates = out3["result"]["candidate_programs"]

print("=" * 72)
print(f"AGENT 3 — RESOURCE RETRIEVAL  (status: {out3['status']})")
print("=" * 72)
for c in candidates:
    print(f"  {c['program_id']}  →  needs: {c['matched_need_ids']}")
for i in out3["issues"]:
    print(f"  [issue {i['severity']}] {i['code']}: {i['message'][:80]}")
print()

# ---- AGENT 4: matching -----------------------------------------------------
crit = build_program_criteria_from_kb([c["program_id"] for c in candidates])
r4 = req("agent_4", "match_resources",
         {"candidate_programs": candidates, "case_facts": FACTS, "needs": NEEDS, "program_criteria": crit})
out4 = agent_4.handle(r4)
matches = out4["result"]["matches"]

print("=" * 72)
print(f"AGENT 4 — RESOURCE MATCHING  (status: {out4['status']})")
print("=" * 72)
for m in matches:
    flags = ""
    if m.get("missing_case_facts"):
        flags += f"  missing: {m['missing_case_facts']}"
    print(f"  {m['program_id']}")
    print(f"    match_status: {m['match_status']}{flags}")
    print(f"    {m['explanation'][:120]}")
print()
for i in out4["issues"]:
    if i["severity"] != "info":
        print(f"  [issue {i['severity']}] {i['code']}: {i['message'][:100]}")
print()

# ---- AGENT 5: verification (all 11 programs — availability) ----------------
check_programs = [{"program_id": m["program_id"], "field_paths": ["availability"]}
                  for m in matches]
r5 = req("agent_5", "verify_resources",
         {"programs_to_check": check_programs, "evidence_refs": [], "relevant_case_constraints": []})
out5 = agent_5.handle(r5)

print("=" * 72)
print(f"AGENT 5 — AVAILABILITY VERIFICATION  (status: {out5['status']})")
print("=" * 72)
seen = set()
for c in out5["result"]["checked_claims"]:
    k = (c["program_id"], c["field_path"])
    if k not in seen:
        seen.add(k)
        val = (c.get("claim_value") or "")[:80]
        print(f"  {c['program_id']}")
        print(f"    {c['field_path']}: [{c['verification_status']}] {val}")
if out5["result"].get("unresolved_questions"):
    for q in out5["result"]["unresolved_questions"]:
        print(f"  [unresolved] {q[:100]}")
print()

print("=" * 72)
print("NOTE ON EDD + REDUCED_HOURS")
print("=" * 72)
edd_match = next((m for m in matches if m["program_id"] == "prog_income_edd_ui_ca_001"), None)
if edd_match:
    print(f"  EDD UI match_status: {edd_match['match_status']}")
    print(f"  employment_status=reduced_hours is partial unemployment;")
    print(f"  EDD UI explicitly covers partial unemployment → never a mismatch.")
print()
