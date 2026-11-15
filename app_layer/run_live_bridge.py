"""Run a fixed, synthetic integration fixture through available Python agents."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import handle

def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def main():
    fixture = load('tests/agent_6_7_8_10/mock_input_v0.2.json')
    a4 = load('navigator/samples/agent_3_4_5/13_agent4_result.json')
    a5 = load('navigator/samples/agent_3_4_5/15_agent5_result.json')
    kb = load('navigator/kb/kb_sacramento.json')
    programs = {p['program_id']: p for p in kb['program_records']}
    needs = fixture['needs']
    matches = a4['result']['matches']
    for match in matches:
        program = programs.get(match['program_id'], {})
        match['program_name'] = program.get('program_name', '')
        match['organization'] = program.get('organization', '')
    availability = {
        pid: (p.get('availability') if isinstance(p.get('availability'), str)
              else (p.get('availability') or {}).get('status', 'unknown'))
        for pid, p in programs.items()
    }
    base = {'needs': needs, 'case_facts': fixture['case_facts'], 'matches': matches,
            'checked_claims': a5['result']['checked_claims'],
            'availability': availability, 'evidence_records': kb['evidence_records']}
    ids = {'request_id': 'local-bridge', 'run_id': 'local-bridge-run',
           'case_id': a4['case_id'], 'case_version': a4['case_version'],
           'correlation_id': 'local-bridge-corr'}
    def call(role, task, payload):
        return handle({**ids, 'role_id': role, 'task_type': task, 'payload': payload})
    a7 = call('agent_7', 'review_stage', {'stage': 'verification',
               'stage_result': {'matches': matches, 'checked_claims': base['checked_claims']},
               'needs': needs, 'evidence_records': kb['evidence_records']})
    a6 = call('agent_6', 'prioritize_actions', base)
    if a6['status'] != 'completed':
        raise RuntimeError('Agent 6 did not complete')
    a8 = call('agent_8', 'build_plan', {**base, 'proposed_actions': a6['result'].get('proposed_actions', [])})
    if a8['status'] != 'completed':
        raise RuntimeError('Agent 8 did not complete')
    a10 = call('agent_10', 'validate_plan', {**base, 'plan': a8['result']})
    output = {'source': 'Fixed synthetic fixtures; live local Python execution; NOT end-to-end',
              'agent7': a7, 'agent6': a6, 'agent8': a8, 'agent10': a10, 'program_details': {pid: {key: record.get(key, []) for key in ('program_name', 'eligibility_criteria', 'required_documents', 'application_method', 'contact')} for pid, record in programs.items()}}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == '__main__':
    main()
