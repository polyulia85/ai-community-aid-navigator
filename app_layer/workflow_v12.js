/* V12: local mock adapter, not live Supervisor or AI. */
(function(){
const $=id=>document.getElementById(id);
const KEY='navigator_v12_demo_case';
const statuses=[['not_started','Not started'],['in_progress','In progress'],['contacted_applied','Contacted / applied'],['waiting_for_response','Waiting for response'],['completed_received','Completed / received'],['unsuccessful','Unsuccessful']];
let saved=null;
try {saved=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){}
function store(){try{localStorage.setItem(KEY,JSON.stringify(saved))}catch(e){console.warn('Local storage unavailable',e)}}
function normalize(summary){return {confirmed:true,needs:Array.isArray(summary.needs)?summary.needs:[],facts:summary.facts||{}}}
function card(id,title,priority,next,reason){return {id,title,priority,next,reason,progress:'not_started',details:{conditions:['This is an example action, not a verified program match.'],documents:[],steps:[next],contacts:[]}}}
function build(summary){const needs=summary.needs.map(n=>String(n).toLowerCase());let list=[];
 if(needs.some(n=>/housing|rent/.test(n))){list.push(card('housing_urgency','Review housing urgency','IMMEDIATE','Check any written notice and its stated deadline; seek qualified local housing guidance.','Housing need reported in your confirmed summary.'));list.push(card('housing_options','Explore rent assistance','HIGH','Review current Sacramento-area government and community rent assistance resources; verify availability and eligibility with each provider.','Potential resource search; no verified match has been performed.'))}
 if(needs.some(n=>/food/.test(n))){list.push(card('food_options','Explore food assistance','HIGH','Check current Sacramento food pantry and CalFresh information; confirm requirements and availability with the provider.','Food need reported in your confirmed summary.'))}
 return list;
}
function view(id){document.querySelector('nav button[data-view="'+id+'"]').click()}
function caseRender(){const host=$('case-view');let panel=$('local-case-panel');if(!panel){panel=document.createElement('div');panel.id='local-case-panel';host.append(panel)}panel.replaceChildren();if(!saved){panel.textContent='No confirmed case yet. Start in Conversation.';return}
 const h=document.createElement('h2');h.textContent='Your case progress';panel.append(h);
 const edit=document.createElement('button');edit.className='quiet';edit.textContent='Review / edit confirmed information';edit.onclick=()=>{view('chat');window.dispatchEvent(new Event('navigator:edit-summary'))};panel.append(edit);
 const info=document.createElement('p');info.textContent='Needs: '+saved.summary.needs.join(', ')+'. Saved in this browser only. You update each action status yourself.';panel.append(info);
 saved.cards.forEach((c,i)=>{const label=document.createElement('label');label.className='summary-field';label.textContent=c.title;const sel=document.createElement('select');statuses.forEach(([value,title])=>{const opt=document.createElement('option');opt.value=value;opt.textContent=title;sel.append(opt)});sel.value=c.progress;sel.onchange=()=>{saved.cards[i].progress=sel.value;store();syncCards();caseRender()};label.append(sel);panel.append(label)});
 const refresh=document.createElement('button');refresh.className='primary';refresh.textContent='Refresh Plan';refresh.onclick=refreshPlan;panel.append(refresh);
 const reset=document.createElement('button');reset.className='quiet';reset.textContent='Clear local demo case';reset.onclick=()=>{if(!confirm('Clear this local demo case and restart?'))return;++requestNumber;localStorage.removeItem(KEY);localStorage.removeItem('navigator_intake_v1');location.reload()};panel.append(reset);
}
function syncCards(){
 cards=saved?saved.cards.map(c=>({...c})):[];renderCards();
 const ready=!!(saved&&saved.phase==='ready'&&saved.cards.length);
 $('refresh-plan').classList.toggle('hidden',!saved||saved.mock);
 $('go-plan').classList.toggle('hidden',!ready);
 $('go-plan').textContent='Go to Action Plan';
 $('plan-state').textContent=!saved?'Confirm your Situation Summary first.':saved.phase==='processing'?'Processing your confirmed information…':saved.phase==='error'?'Plan could not be prepared. Retry using Refresh Plan.':saved.phase==='ready'?'Locally generated action steps from confirmed information. Eligibility and availability are not confirmed.':'No supported program matches were found in the local KB.';
 $('bridge-status').textContent=saved?.phase==='ready'?'Local confirmed-case pipeline: Agents 3–8 and 10; not a conversational Supervisor run.':'No completed personalized plan.';
}
function matchToCard(m,prior,details={}){
 const status=m.match_status||'unknown';const missing=m.missing_case_facts||[];
 return {id:m.program_id,title:m.program_name||'Program option',priority:'REVIEW — PRELIMINARY',next:'Contact the program to check current availability, eligibility and application instructions.',reason:(m.explanation||'Program may be relevant to a confirmed need.')+(missing.length?' Missing information: '+missing.join(', ')+'.':''),progress:prior[m.program_id]||'not_started',uncertainty:[`Match status: ${status}. No eligibility decision.`,...missing.map(x=>'Unknown: '+x)],details:{conditions:details.eligibility_criteria||[],documents:details.required_documents||[],steps:details.application_method||[],contacts:details.contact||[]}};
}
function actionToCard(action,prior,programs){
 const p=programs[action.program_id]||{};
 const id=action.card_id||action.program_id;
 return {id,title:action.action_title||p.program_name||'Follow up',priority:(action.order_group||'later').toUpperCase(),next:action.next_step||'Review the current program instructions.',reason:action.reason||'',progress:prior[id]||'not_started',uncertainty:action.uncertainty_notes||[],details:{conditions:p.eligibility_criteria||[],documents:p.required_documents||[],steps:p.application_method||[],contacts:action.contacts||p.contact||[]}};
}
let requestNumber=0;
async function processConfirmed(summary, preserve=true){
 const token=++requestNumber;
 const prior=preserve?Object.fromEntries((saved?.cards||[]).map(c=>[c.id,c.progress])):{};
 // Keep progress through failed refreshes, but never present stale cards as a ready plan.
 const previousCards=preserve?(saved?.cards||[]):[];
 saved={version:'0.5-integrated',case_id:'local-demo',summary,cards:previousCards,phase:'processing',confirmed_at:new Date().toISOString()};
 store();syncCards();caseRender();
 try{
  const response=await fetch('/api/case/match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(summary)});
  const result=await response.json();if(!response.ok)throw Error(result.error||'Matching request failed');
  if(token!==requestNumber)return;
  const options=(result.matches||[]).filter(m=>m.match_status!=='confirmed_mismatch');
  if(result.validation?.verdict!=='PASS')throw Error('Agent 10 validation did not pass; no plan published');
  saved.cards=(result.cards||[]).map(a=>actionToCard(a,prior,result.program_details||{}));
  saved.phase=saved.cards.length?'ready':'empty';saved.match_result={candidate_count:result.candidate_count,limitations:result.limitations};
  store();syncCards();caseRender();
  const bubble=document.createElement('div');bubble.className='bubble navigator';const p=document.createElement('p');p.textContent=options.length?`I prepared ${saved.cards.length} action steps from your confirmed information. Agent 10 validation passed. Eligibility and current availability still need verification.`:'No suitable program options were found in this limited local knowledge base. This does not mean assistance is unavailable.';bubble.append(p);$('thread').append(bubble);
 }catch(error){if(token!==requestNumber)return;saved.phase='error';saved.error=String(error.message);store();syncCards();caseRender();$('plan-state').textContent='Matching failed: '+saved.error;}
}
function refreshPlan(){if(!saved||saved.mock)return;processConfirmed(saved.summary,true)}
window.addEventListener('navigator:confirmed',e=>{const summary=normalize(e.detail);window.__confirmedCaseSummary=summary;processConfirmed(summary,true)});
window.addEventListener('navigator:progress',e=>{if(!saved)return;const c=saved.cards[e.detail.index];if(c){c.progress=e.detail.status;store();caseRender()}});
window.addEventListener('navigator:mock-loaded',e=>{
 const result=e.detail;
 const prior=saved?.cards||[];
 const progress=Object.fromEntries(prior.map(c=>[c.id,c.progress]));
 const summary={needs:(result.summary?.needs||[]).map(n=>typeof n==='string'?n:(n.category||n.description||'other')),facts:result.summary?.facts||{}};
 saved={version:'0.2-mock',mock:true,case_id:result.case_id,summary,
  cards:result.cards.map(c=>({...c,progress:progress[c.id]||c.progress})),confirmed_at:new Date().toISOString()};
 store();syncCards();caseRender();
 const issue=result.errors.map(x=>x.message||x.code||String(x)).join('; ');
 $('plan-state').textContent=issue?'Mock error: '+issue:result.phase==='processing'?'Mock processing in progress…':result.phase==='summary_review'?'Mock summary review state — no plan ready.':result.cards.length?`Mock ${result.phase}: ${result.cards.length} actions displayed.`:'No verified program matches in this mock response. No actions invented.';
 $('bridge-status').textContent='Developer fixture, not a personalized Supervisor result.';
 if(result.phase==='error'||result.phase==='processing'||result.phase==='summary_review'||result.phase==='conversation'){$('go-plan').classList.add('hidden');}
 view('plan');
});
$('refresh-plan').onclick=refreshPlan;
if(saved){window.__confirmedCaseSummary=saved.summary;if(saved.phase==='processing')saved.phase='error';syncCards();caseRender();const thread=$('thread');const b=document.createElement('div');b.className='bubble navigator';const p=document.createElement('p');p.textContent='Your locally saved example case is ready. Select Action Plan or My Case to continue. To start a new fictional scenario, clear the demo case under My Case.';b.append(p);thread.append(b)}else{cards=[];renderCards();caseRender()}
})();