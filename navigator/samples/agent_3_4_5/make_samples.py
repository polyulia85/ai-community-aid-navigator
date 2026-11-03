"""Regenerates the sample request/result JSON for Agents 3-5 on the shared family case.
Run from repo root: python navigator/samples/agent_3_4_5/make_samples.py"""
import json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from navigator.agents.agent_3_4_5 import agent_3, agent_4, agent_5
from navigator.agents.agent_3_4_5.common import build_program_criteria_from_kb
from tests.agent_3_4_5.test_agents_3_4_5 import req, NEEDS, FACTS, GEO
here = os.path.dirname(os.path.abspath(__file__))
def dump(name, obj):
    json.dump(obj, open(os.path.join(here, name), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
r3 = req("agent_3", "retrieve_candidates", {"needs": NEEDS, "geography": GEO, "retrieval_constraints": [], "max_candidates": 10}); r3["request_id"] = "req-0003"
o3 = agent_3.handle(r3)
cands = o3["result"]["candidate_programs"]
# program_criteria is built by the Supervisor in the real system; build_program_criteria_from_kb stands in for it here
r4 = req("agent_4", "match_resources", {"candidate_programs": cands, "case_facts": FACTS, "needs": NEEDS,
                                         "program_criteria": build_program_criteria_from_kb([c["program_id"] for c in cands])})
r4["request_id"] = "req-0004"; r4["upstream_result_refs"] = ["req-0003"]
o4 = agent_4.handle(r4)
r5 = req("agent_5", "verify_resources", {"programs_to_check": [{"program_id": m["program_id"], "field_paths": ["eligibility_criteria", "required_documents", "application_method", "contact", "deadlines", "processing_time", "availability"]} for m in o4["result"]["matches"]], "evidence_refs": [], "relevant_case_constraints": []})
r5["request_id"] = "req-0005"; r5["upstream_result_refs"] = ["req-0004"]
o5 = agent_5.handle(r5)
for n, o in [("10_agent3_request", r3), ("11_agent3_result", o3), ("12_agent4_request", r4), ("13_agent4_result", o4), ("14_agent5_request", r5), ("15_agent5_result", o5)]:
    dump(n + ".json", o)
print("samples written")
