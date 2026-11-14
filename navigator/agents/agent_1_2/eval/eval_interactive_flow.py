"""
eval_interactive_flow.py
Local interactive/automated multi-turn tester for Agent 1 and Agent 2.
"""
import os
import sys

# Ensure repository root is on sys.path regardless of execution directory
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from navigator.agents.agent_1_2.agent_1 import handle_agent_1
from navigator.agents.agent_1_2.agent_2 import handle_agent_2

SCENARIOS = {
    "Julia_housing_and_food": [
        "I have problems with housing and food. I need help.",
        "My hours were cut at work last month and I couldn't pay rent.",
        "My ZIP code is 95823 and our gross income is about $800 a month.",
        "There are 3 people in our household."
    ],
    "A_unspecified_hardship": [
        "Hi, I need help with food and rent. I'm having financial problems and I'm worried about how my family will get through next month.",
        "My company cut my hours from 40 to 15 hours a week starting two weeks ago, so my paycheck dropped drastically.",
        "We are in 95823. Our monthly income is $900.",
        "Our monthly rent is $1,350 and I have about $150 left in my account.",
        "There are 3 people in our family."
    ],
    "B_urgent_eviction": [
        "My landlord gave me a 3-day notice to pay or quit yesterday and threatened to lock us out if we don't leave.",
        "We live in 95823 and our income is $1,000. The notice date is November 6, 2026, and the amount due is $1,600."
    ],
    "C_unexpected_medical_expense": [
        "I was doing okay until my daughter had an emergency asthma hospitalization last week, and now the hospital bill took all my rent money.",
        "Our ZIP is 95823 and income is $1,200. Rent is $1,200 due on November 1st, and we have no groceries left for the kids.",
        "There are 3 people in our household."
    ],
    "D_income_retry_when_unanswered": [
        "I lost my job yesterday and need help with rent.",
        "I live in ZIP 95823.",  # Answers ZIP, ignores income question -> triggers single retry
        "I'm not sure what our income is right now.",  # Still doesn't provide income -> retry limit reached (1 retry), concludes
    ]
}


def run_simulation(scenario_name, user_turns):
    print("\n" + "=" * 65)
    print(f"RUNNING SCENARIO: {scenario_name}")
    print("=" * 65)

    case_facts = []
    already_asked = []
    needs = []

    for turn_idx, user_input in enumerate(user_turns, start=1):
        print(f"\n--- [Turn {turn_idx}] User Says: ---")
        print(f'"{user_input}"')

        # Step 1: Agent 1 processes user utterance
        a1_req = {
            "request_id": f"sim_a1_{turn_idx}",
            "run_id": "sim_run",
            "case_id": "sim_case",
            "case_version": turn_idx,
            "role_id": "agent_1",
            "task_type": "understand_story" if turn_idx == 1 else "parse_clarification_answer",
            "payload": {
                "story_text": user_input,
                "answer_text": user_input,
                "pending_fact_keys": list(already_asked),
            },
        }
        a1_envelope = handle_agent_1(a1_req)
        a1_res = a1_envelope.get("result", {})

        new_facts = a1_res.get("factual_claims", [])
        case_facts.extend(new_facts)
        
        # Merge proposed needs cumulatively across turns
        new_needs = a1_res.get("proposed_needs", [])
        if new_needs:
            for n in new_needs:
                cat = n.get("category")
                if not any(existing.get("category") == cat for existing in needs):
                    needs.append(n)

        safety_flags = a1_res.get("safety_or_official_deadline_flags", [])
        ambiguity_flags = a1_res.get("ambiguity_flags", [])

        facts_summary = [f"{f.get('field')}: {f.get('value')}" for f in new_facts]
        needs_summary = [n.get("category") for n in needs]
        safety_summary = [s.get("note") for s in safety_flags]

        print("\nAgent 1 Findings:")
        for n in needs:
            print(f"  • Proposed Need: {n.get('category')} (Urgency: {n.get('urgency')}, Reason: \"{n.get('urgency_reason')}\")")
        print(f"  • Triggering Events: {a1_res.get('triggering_events', [])}")
        print(f"  • Ambiguity Flags: {ambiguity_flags}")
        print(f"  • Safety Flags: {safety_summary}")
        print(f"  • Extracted Facts: {facts_summary}")

        # Step 2: Agent 2 analyzes what to ask next
        a2_req = {
            "request_id": f"sim_a2_{turn_idx}",
            "run_id": "sim_run",
            "case_id": "sim_case",
            "case_version": turn_idx,
            "role_id": "agent_2",
            "task_type": "clarify_case",
            "payload": {
                "needs": needs,
                "case_facts": case_facts,
                "already_asked": list(already_asked),
                "ambiguity_flags": ambiguity_flags,
                "candidate_requirements": [],
            },
        }
        a2_envelope = handle_agent_2(a2_req)
        clarifications = a2_envelope.get("clarification_requests", [])

        print("\nAgent 2 Output:")
        if not clarifications:
            print("  [No further clarification needed. Ready for Candidate Retrieval / Agent 3]")
            break
        else:
            for q in clarifications:
                print(f"  ▶ Question Intent: {q.get('question_intent')}")
                print(f"    Fact Key: {q.get('fact_key')}")
                print(f"    User-Facing Question: \"{q.get('user_facing_question')}\"")
                already_asked.append(q.get("fact_key"))


if __name__ == "__main__":
    for name, turns in SCENARIOS.items():
        run_simulation(name, turns)