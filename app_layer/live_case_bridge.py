"""Local preview: confirmed summary -> real Agents 3/4/5. No Agent 1/2 or eligibility decision."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from navigator.agents.agent_3_4_5 import agent_3,agent_4,agent_5
from navigator.agents.agent_3_4_5.common import build_program_criteria_from_kb,load_kb

def run(summary):
    if not isinstance(summary,dict) or summary.get('confirmed') is not True: raise ValueError('Confirmed summary required')
    facts=summary.get('facts') or {}; labels=summary.get('needs') or []
    if not isinstance(facts,dict) or not isinstance(labels,list): raise ValueError('Invalid summary structure')
    mapping={'housing':'housing_assistance','food':'food_assistance','income':'income_assistance'}
    needs=[{'need_id':f'need_{i+1:03}','category':mapping[x],'subcategory':None,'description':f'User-confirmed {x} need','urgency':'high'} for i,x in enumerate(labels) if x in mapping]
    if not needs: raise ValueError('No supported confirmed needs')
    zip_code=str(facts.get('zip','')).strip(); county=str(facts.get('county','')).strip()
    if not county and zip_code not in {str(z) for z in range(95811,95839)}:
        raise ValueError('County must be confirmed; ZIP is outside the limited Sacramento lookup. No location guessed.')
    geography=[v for v in (zip_code, (county if county.lower().endswith('county') else county+' County') if county else '') if v]
    env={'request_id':'local-confirmed-summary','run_id':'local-run','case_id':'local-case','case_version':1,'correlation_id':'local-correlation','schema_version':'1.0','allowed_case_facts':[],'upstream_result_refs':[]}
    def call(agent,role,task,payload):
        r=agent.handle({**env,'role_id':role,'task_type':task,'payload':payload})
        if r['status']=='failed': raise ValueError(f'{role} failed: {r.get("issues")}')
        return r
    a3=call(agent_3,'agent_3','retrieve_candidates',{'needs':needs,'geography':geography,'retrieval_constraints':[],'max_candidates':30})
    candidates=a3['result']['candidate_programs']; ids=[x['program_id'] for x in candidates]
    case_facts=[]
    for key,value in [('zip_code',zip_code),('county',(county if county.lower().endswith('county') else county+' County') if county else ''),('household_size',facts.get('household_count')),('household_gross_monthly_income',facts.get('income'))]:
        if value not in (None,'','unknown'):
            case_facts.append({'field':key,'value':value,'confirmation_status':'confirmed'})
    a4=call(agent_4,'agent_4','match_resources',{'candidate_programs':candidates,'case_facts':case_facts,'needs':needs,'program_criteria':build_program_criteria_from_kb(ids)})
    a5=call(agent_5,'agent_5','verify_resources',{'programs_to_check':[{'program_id':pid,'field_paths':['eligibility_criteria','required_documents','application_method','contact','deadlines','availability']} for pid in ids],'evidence_refs':[],'relevant_case_constraints':[]}) if ids else None
    programs,_=load_kb(); byid={p['program_id']:p for p in programs}
    matches=[{**m,'program_name':byid[m['program_id']]['program_name'],'availability':byid[m['program_id']].get('availability')} for m in a4['result']['matches']]
    # Feed the same confirmed case and live matching outputs into the downstream
    # local agents. Do not substitute any synthetic fixture or make up evidence.
    from navigator.agents.agent_6_7_8_10.agent_6_7_8_10 import handle as downstream
    kb = json.loads((ROOT / 'navigator/kb/kb_sacramento.json').read_text(encoding='utf-8'))
    availability = {pid: (p.get('availability') if isinstance(p.get('availability'), str) else (p.get('availability') or {}).get('status', 'unknown')) for pid,p in byid.items()}
    base = {'needs': needs, 'case_facts': case_facts, 'matches': matches,
            'checked_claims': a5['result'].get('checked_claims',[]) if a5 else [],
            'availability': availability, 'evidence_records': kb.get('evidence_records',[])}
    def downstream_call(role,task,payload):
        output=downstream({**env,'role_id':role,'task_type':task,'payload':payload})
        if output.get('status') != 'completed':
            raise ValueError(f'{role} did not complete: {output.get("issues",[])}')
        return output
    a7=downstream_call('agent_7','review_stage',{'stage':'verification',
        'stage_result':{'matches':matches,'checked_claims':base['checked_claims']},
        'needs':needs,'evidence_records':base['evidence_records']})
    a6=downstream_call('agent_6','prioritize_actions',base)
    a8=downstream_call('agent_8','build_plan',{**base,'proposed_actions':a6['result'].get('proposed_actions',[])})
    a10=downstream_call('agent_10','validate_plan',{**base,'plan':a8['result']})
    return {'mode':'confirmed_case_local_agents_3_to_8_and_10',
        'limitations':'Local deterministic pipeline, not conversational Supervisor orchestration. Program availability and eligibility require official verification.',
        'agent3':a3,'agent4':a4,'agent5':a5,'agent6':a6,'agent7':a7,'agent8':a8,'agent10':a10,
        'validation':a10['result'],'cards':a8['result'].get('action_cards',[]),
        'program_details':byid,'matches':matches,'candidate_count':len(ids)}

if __name__=='__main__': print(json.dumps(run(json.load(sys.stdin)),ensure_ascii=False))
