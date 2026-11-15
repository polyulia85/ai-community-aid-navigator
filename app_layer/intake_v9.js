/* v9 Context Intake Test: transparent, deterministic fact/gap engine.
   Not an LLM, live Supervisor, eligibility assessment or program matcher. */
(function(){
const $=id=>document.getElementById(id);
const INTAKE_KEY='navigator_intake_v1';
const state={facts:{},needs:[],pending:null,stage:'story',story:'',confirmed:false,history:[]};
try {const saved=JSON.parse(localStorage.getItem(INTAKE_KEY)||'null');if(saved&&Array.isArray(saved.history)&&saved.facts&&Array.isArray(saved.needs)){Object.assign(state,{facts:saved.facts,needs:saved.needs,pending:saved.pending||null,stage:saved.stage||'story',story:saved.story||'',confirmed:!!saved.confirmed,history:saved.history.slice(-100)});}}catch(e){}
function persist(){try{localStorage.setItem(INTAKE_KEY,JSON.stringify(state))}catch(e){}}
function remember(role,text){state.history.push({role,text});if(state.history.length>100)state.history.shift();persist()}

const questions={cause:'Could you tell me a little more about your situation? For example, have there been any recent changes in your work, income, or family circumstances?',needs:'Are you looking for rent assistance, food assistance, or both?',household_count:'How many people live at your address?',household_relation:'Are these people one family or multiple families sharing the address?',food_group:'How many people buy and prepare food together?',income:'What is the total monthly income from all household members, including work and benefits? You can say unknown.',income_sources:'Does anyone else in your household receive wages, unemployment, benefits, or other income?',assets:'Do you have money available for immediate expenses, such as cash or savings? You may say unknown. This is separate from monthly income.',rent_amount:'What is your monthly rent amount?',rent_due:'When is your next rent payment due?',rent_shortfall:'How much of the upcoming rent can you currently pay?',eviction:'Have you received an eviction notice or any warning from your landlord?',location:'What is your city and ZIP code? (You can give them separately.)',city:'What city do you live in?',zip:'What is your five-digit ZIP code?'};
const yes=/^(yes|yeah|yep|correct|right|i have|we have)\b/i,no=/^(no|nope|not yet|never|none)\b/i;
const unknown=/^(unknown|not sure|i don.t know|unsure|prefer not to say)$/i;
function addFact(k,v){if(v!==undefined&&v!==null&&String(v).trim())state.facts[k]=String(v).trim()}
function needsFrom(s){
 // A negated mention is context, not an affirmative request for assistance.
 const n=[];
 const housing=/(rent|landlord|housing|evict|apartment|behind on (my |the )?payment)/i;
 const food=/(food|grocery|groceries|hungry|meals|calfresh)/i;
 const negateHousing=/\b(?:do not|don't|dont|not|no|never)\s+(?:need|want|require|seek|looking for)\s+(?:any\s+)?(?:rent|housing|eviction|landlord|apartment)\s*(?:assistance|help)?/i;
 const negateFood=/\b(?:do not|don't|dont|not|no|never)\s+(?:need|want|require|seek|looking for)\s+(?:any\s+)?(?:food|grocery|groceries|meal|calfresh)\s*(?:assistance|help)?/i;
 if(housing.test(s)&&!negateHousing.test(s))n.push('housing');
 if(food.test(s)&&!negateFood.test(s))n.push('food');
 return n;
}
function extract(text,context){const s=text.trim(), f=state.facts;
 const found=needsFrom(s);if(found.length)state.needs=[...new Set([...state.needs,...found])];
 if(/laid off|lost (my |our )?job|fired|unemploy|lost work|hospital|illness|injur|death|passed away/i.test(s)&&!f.cause)addFact('cause',s);
 const count=s.match(/(?:family of|household of|there are|we are|live with|living with)\s+(\d{1,2})\b/i);if(count)addFact('household_count',count[1]);
 const zip=s.match(/\b\d{5}\b/);if(zip&&(!context||['location','zip'].includes(context)))addFact('zip',zip[0]);
 const inc=s.match(/(?:income|earn|make)\s*(?:is|of|about|around)?\s*\$?([\d,]+)\s*(?:per month|monthly|a month)/i);if(inc)addFact('income',inc[1]);
 if(/no income|zero income|income is \$?0\b/i.test(s))addFact('income','0');
 const rent=s.match(/(?:rent is|monthly rent is|pay \$)\s*\$?([\d,]+)/i);if(rent)addFact('rent_amount',rent[1]);
 const due=s.match(/\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b/i);if(due&&(!context||['rent_due','rent_amount'].includes(context)))addFact('rent_due',due[0]);
 if(/\b(eviction notice|notice to quit|pay or quit notice|written warning)\b/i.test(s)&&!/\b(no eviction notice|no notice from|haven.t received (an? )?eviction notice)\b/i.test(s))addFact('eviction','yes — '+s);
 if(/\b(no eviction notice|no notice from (my |the )?landlord|haven.t received (an? )?eviction notice)\b/i.test(s))addFact('eviction','no');
}
function setPending(k,s){if(!k||!Object.prototype.hasOwnProperty.call(questions,k))return;if(unknown.test(s)){if(k!=='needs')addFact(k,'unknown');return}
 if(k==='needs'){const n=needsFrom(s);if(/\bboth\b|\bboth of them\b|\ball two\b/i.test(s))state.needs=['housing','food'];else if(n.length)state.needs=[...new Set([...state.needs,...n])];return}
 if(k==='eviction'){if(no.test(s)||/\b(no eviction notice|no notice from|haven.t received (an? )?eviction notice)\b/i.test(s))addFact(k,'no');else if(yes.test(s)||/notice|warning/i.test(s))addFact(k,'yes — '+s);return}
 if(k==='income_sources'){if(no.test(s))addFact(k,'no other sources reported');else if(yes.test(s)||/benefit|unemploy|wage|work|salary|social security|disability|income/i.test(s))addFact(k,s);return}
 if(k==='household_count'||k==='food_group'){const m=s.match(/\b(\d{1,2})\b/);if(m)addFact(k,m[1]);else if(/^(?:just|only) (?:me|myself)|^i live alone$|^one person$/i.test(s))addFact(k,'1');return}
 if(k==='income'||k==='rent_amount'||k==='rent_shortfall'){const m=s.match(/\$?([\d,]+(?:\.\d{1,2})?)/);if(m)addFact(k,m[1]);else if(k==='rent_shortfall'&&no.test(s))addFact(k,'0');return}
 if(k==='zip'){const m=s.match(/\b\d{5}\b/);if(m)addFact(k,m[0]);return}
 if(k==='rent_due'){const m=s.match(/\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b/i);if(m)addFact(k,m[0]);return}
 if(k==='city'&&/^\d{5}$/.test(s))return;
 addFact(k,s)
}
function missing(){const f=state.facts;const keys=['cause','needs','household_count','household_relation'];if(state.needs.includes('food'))keys.push('food_group');keys.push('income','income_sources','assets');if(state.needs.includes('housing'))keys.push('rent_amount','rent_due','rent_shortfall','eviction');keys.push('location');
 for(const k of keys){if(k==='needs'){if(!state.needs.length)return 'needs';continue}if(k==='location'){if(!f.city)return 'city';if(!f.zip)return 'zip';continue}if(!f[k])return k}return null}
function reply(s){const b=document.createElement('div');b.className='bubble navigator';const small=document.createElement('small');small.textContent='Navigator';const p=document.createElement('p');p.textContent=s;b.append(small,p);$('thread').append(b);$('thread').scrollTop=$('thread').scrollHeight;remember('navigator',s)}
function sayUser(s){const b=document.createElement('div');b.className='bubble user';const small=document.createElement('small');small.textContent='You';const p=document.createElement('p');p.textContent=s;b.append(small,p);$('thread').append(b);remember('user',s)}
function showSummary(restoring=false){state.stage='summary';state.pending=null;persist();const area=$('summary-area');area.replaceChildren();area.classList.remove('hidden');const h=document.createElement('h2');h.textContent='Situation Summary — review and edit';area.append(h);const note=document.createElement('p');note.textContent='This is a fact review, not eligibility verification. City/ZIP and program service areas are NOT validated by this prototype.';area.append(note);
 const rows=[['needs','Assistance needed',state.needs.join(', ')],...Object.entries(state.facts).map(([k,v])=>[k,k.replaceAll('_',' '),v])];for(const [k,label,value] of rows){const l=document.createElement('label');l.className='summary-field';l.textContent=label;const t=document.createElement('textarea');t.rows=k==='cause'?3:1;t.dataset.key=k;t.value=value;l.append(t);area.append(l)}
 const back=document.createElement('button');back.className='quiet';back.textContent='Back to Conversation';back.onclick=()=>{area.classList.add('hidden');state.stage='questions';state.pending=missing();persist();reply('You can add or correct details here. When you are ready, we will review your updated summary.');if(state.pending)reply(questions[state.pending]||'Could you clarify?');else{const review=document.createElement('button');review.className='quiet';review.textContent='Review Situation Summary';review.onclick=()=>{review.remove();showSummary()};$('thread').append(review)}};area.append(back);
 const b=document.createElement('button');b.className='primary';b.textContent='Confirm information';b.onclick=()=>{for(const t of area.querySelectorAll('textarea')){if(!t.value.trim()&&t.dataset.key==='needs'){reply('Please specify at least one supported need.');return}}for(const t of area.querySelectorAll('textarea')){if(t.dataset.key==='needs')state.needs=[...new Set(t.value.split(',').map(x=>x.trim().toLowerCase()).filter(x=>['housing','food','income'].includes(x)))];else if(t.value.trim())addFact(t.dataset.key,t.value);else delete state.facts[t.dataset.key]}if(!state.needs.length){reply('Please select a supported need: housing, food, or income.');return}state.confirmed=true;persist();window.__confirmedCaseSummary={confirmed:true,needs:[...state.needs],facts:{...state.facts}};state.stage='confirmed';area.classList.add('hidden');reply('Your information is confirmed. I am preparing an Action Plan from your confirmed facts. You can review and edit the information again if needed.');$('plan-state').textContent='Intake confirmed locally. Program eligibility and personalized planning are not connected.';$('go-plan').classList.add('hidden');window.dispatchEvent(new CustomEvent('navigator:confirmed',{detail:window.__confirmedCaseSummary}))};area.append(b);if(!restoring)reply('I have the minimum facts for this context intake test. Please review and correct your Situation Summary.');}
async function next(){
 const k=missing();
 if(!k){showSummary();return}
 // The Supervisor intake coordinator invokes Agent 1 and Agent 2. It may
 // prioritize a verified Agent 2 question; unsupported keys stay local.
 let chosen=k, wording=questions[k];
 try{
  const r=await fetch('/api/supervisor/intake',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({story:state.story,facts:state.facts,needs:state.needs,already_asked:Object.keys(state.facts)})});
  if(r.ok){const data=await r.json();
   const proposals=data.agent1?.proposed_needs||[];
   const mapped=proposals.map(n=>({housing_assistance:'housing',food_assistance:'food'}[n.category])).filter(Boolean);
   const added=mapped.filter(n=>!state.needs.includes(n));
   if(added.length){state.needs=[...new Set([...state.needs,...added])];persist();}
   const q=(data.agent2?.clarification_requests||[]).find(x=>x.fact_key==='household_gross_monthly_income'&&k==='income');
   if(q&&typeof q.user_facing_question==='string')wording=q.user_facing_question;
  }
 }catch(e){console.warn('Supervisor intake coordinator unavailable:',e.message)}
 if(state.stage!=='questions')return;
 // A response may have arrived while the request was in flight.
 chosen=missing();if(!chosen){showSummary();return}
 state.pending=chosen;persist();reply(chosen===k?wording:questions[chosen]);
}
// Agent 1 is an additional, explicitly provisional signal; never silently confirm facts.
async function understandStory(story){
 try {
  const response=await fetch('/api/intake/understand',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({story_text:story})});
  if(!response.ok)throw new Error('HTTP '+response.status);
  const data=await response.json();
  if(state.story!==story||state.confirmed||state.stage==='summary')return;
  const proposed=Array.isArray(data.result?.proposed_needs)?data.result.proposed_needs:[];
  const mapped=proposed.map(n=>({housing_assistance:'housing',food_assistance:'food'}[n.category])).filter(Boolean);
  const newNeeds=mapped.filter(n=>!state.needs.includes(n));
  if(newNeeds.length){state.needs=[...new Set([...state.needs,...newNeeds])];persist();
   reply('I also noticed a possible need for '+newNeeds.join(' and ')+' assistance. Please review and correct this in your Situation Summary.');}
  // Proposed claims and safety flags are not treated as confirmed facts.
 } catch(error){console.warn('Agent 1 unavailable; continuing local intake:',error.message)}
}
function submit(s){s=s.trim();if(!s)return;sayUser(s);$('message').value='';$('transcript').value='';$('review').classList.add('hidden');if(state.stage==='story'){state.story=s;extract(s);state.stage='questions';persist();if(state.needs.length)reply('Thank you for sharing that. Let’s look at what support may be available and work through a few details together.');next();return}if(state.stage==='questions'){const pending=state.pending;if(!pending){extract(s);persist();next();return}setPending(pending,s);extract(s,pending);if(pending==='needs'&&!state.needs.length){reply('Could you tell me whether you need help with rent, food, or both?');return}persist();if(!state.facts[pending]&&pending!=='needs'&&pending!=='location'&&pending!==null){reply('I could not reliably interpret that answer. '+questions[pending]);return}next();return}if(state.stage==='summary'){reply('Please edit the Situation Summary above, then confirm.');return}reply('Your information is confirmed. You can view your Action Plan or return here to review the conversation.');}
window.addEventListener('navigator:edit-summary',()=>{if(window.__confirmedCaseSummary){const prior=window.__confirmedCaseSummary;state.needs=[...prior.needs];state.facts={...prior.facts};state.confirmed=false;persist();showSummary()}});
// Restore the visible conversation and the current stage after a page reload.
if(state.history.length){for(const item of [...state.history]){const b=document.createElement('div');b.className='bubble '+(item.role==='user'?'user':'navigator');const small=document.createElement('small');small.textContent=item.role==='user'?'You':'Navigator';const para=document.createElement('p');para.textContent=item.text;b.append(small,para);$('thread').append(b)}if(state.stage==='summary')showSummary(true);else if(state.stage==='questions'&&state.pending){const last=state.history[state.history.length-1];if(last?.role==='user')reply(questions[state.pending]||'Could you clarify?')}}
$('send').onclick=()=>submit($('message').value);$('send-reviewed').onclick=()=>submit($('transcript').value);$('go-plan').onclick=()=>document.querySelector('nav button[data-view="plan"]').click();
window.__intakeV9={state,missing,extract,setPending,needsFrom};
})();
