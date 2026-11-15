import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawn } from 'node:child_process';

const origin = process.argv[2] || 'http://127.0.0.1:8765';
const browserPath = process.argv[3] || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const profile = await mkdtemp(join(tmpdir(), 'navigator-chrome-'));
const chrome = spawn(browserPath, [
  '--headless', '--remote-debugging-port=0', '--user-data-dir='+profile,
  '--no-first-run', '--disable-background-networking', '--no-default-browser-check',
  '--window-size=1440,1000', 'about:blank'
], {stdio:'ignore'});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (await fn()) return;
    await delay(100);
  }
  throw Error('Browser or expected page state timed out.');
}
let ws;
try {
  let port;
  await until(async () => {
    try { port = (await readFile(profile+'/DevToolsActivePort','utf8')).split('\n')[0]; return true; }
    catch { return false; }
  });
  const pages = await (await fetch('http://127.0.0.1:'+port+'/json/list')).json();
  ws = new WebSocket(pages.find(page => page.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, {once:true});
    ws.addEventListener('error', reject, {once:true});
  });
  const pending = new Map();
  const errors = [];
  let id = 0;
  ws.addEventListener('message', event => {
    const data = JSON.parse(event.data);
    if (data.method === 'Runtime.exceptionThrown') errors.push(data.params.exceptionDetails);
    if (data.id) pending.get(data.id)?.(data);
  });
  const cdp = async (method, params={}) => {
    const current = ++id;
    const response = new Promise(resolve => pending.set(current, resolve));
    ws.send(JSON.stringify({id:current,method,params}));
    const result = await response;
    pending.delete(current);
    if (result.error) throw Error(JSON.stringify(result.error));
    return result.result;
  };
  const js = async expression => {
    const result = await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const see = condition => until(() => js(condition)).catch(() => { throw Error('Expected page state: ' + condition); });
  const submit = text => js(`document.querySelector('#message').value=${JSON.stringify(text)}; document.querySelector('#send').click()`);
  const nav = view => js(`document.querySelector('nav [data-view="${view}"]').click()`);
  const state = 'JSON.parse(sessionStorage.getItem("navigator-local-case-v1"))';
  await cdp('Runtime.enable');
  await cdp('Page.enable');
  await cdp('Page.navigate',{url: origin + '/'});
  await see("typeof setView === 'function' && document.readyState === 'complete'");
  assert(await js("document.querySelector('#thread').textContent.includes('Hello. I can help you')"));
  await submit("I paid the rent yesterday. My manager took me off the schedule this week, and my next paycheck won’t come until Friday. I’ve been skipping dinner so my kids can eat. I’m not sure how long we can stretch what’s left. Where should I start?");
  const paidRentAnswers = {
    triggering_circumstances: "I’m still employed, but my manager didn’t give me any shifts this week. I used most of my last paycheck to cover rent, so there’s very little left for groceries until I get paid on Friday.",
    zip_code: '95814',
    household_gross_monthly_income: '1200',
    household_size: '3',
    food_needed_by_tomorrow: 'Yes, we need food tomorrow morning.',
    cash_on_hand_approx: '300',
  };
  const paidRentAsked = [];
  for (let turn = 0; turn <= Object.keys(paidRentAnswers).length; turn++) {
    await see("document.querySelector('#summary-area h2') || (!document.querySelector('#send').disabled && " + state + "?.response?.questions?.length)");
    if (await js("Boolean(document.querySelector('#summary-area h2'))")) break;
    const key = await js(state + ".response.questions[0].fact_key");
    assert(Object.hasOwn(paidRentAnswers, key), 'Unexpected question in paid-rent case: ' + key);
    assert(!paidRentAsked.includes(key), 'Repeated question in paid-rent case: ' + key);
    paidRentAsked.push(key);
    await submit(paidRentAnswers[key]);
    await see(state + "?.response?.questions?.[0]?.fact_key !== " + JSON.stringify(key));
  }
  assert(paidRentAsked.includes('food_needed_by_tomorrow'));
  await see("document.querySelector('#summary-area h2')?.textContent === 'Situation Summary'");
  assert(!await js("document.querySelector('#thread').textContent.includes('formal written notice')"));
  await js("[...document.querySelectorAll('#summary-area button')].find(b=>b.textContent==='Confirm Information').click()");
  await see("!document.querySelector('#go-plan')?.classList.contains('hidden')");
  await js("document.querySelector('#go-plan').click()");
  assert.deepEqual(await js("[...document.querySelectorAll('.plan-sections button')].map(b=>b.textContent)"), ['Food Bank', 'CalFresh']);
  assert.equal(await js("document.querySelector('.priority-pill').textContent"), 'Do first');
  console.log('Chrome E2E: ZIP 95814 paid rent case passed with Food Bank first and no tenancy questions.');
  await nav('case');
  await js("document.querySelector('#reset-case').click()");

  await submit('I live in Sacramento ZIP code 95823 with my two children. I lost my job. I need food this week and help paying $1,450 rent.');
  await see("document.querySelector('#thread').textContent.includes('gross monthly household income')");
  assert(await js("!document.querySelector('#skip').classList.contains('hidden')"));
  await submit('My household gross monthly income is $900.');
  await see("document.querySelector('#thread').lastChild.textContent.includes('How many people')");
  assert(await js("!document.querySelector('#skip').classList.contains('hidden')"));
  await cdp('Page.reload');
  await see("document.querySelector('#thread')?.lastChild?.textContent.includes('How many people')");
  await submit('There are 3 people in my household.');
  await see("document.querySelector('#thread').lastChild.textContent.includes('written rental or lease agreement')");
  await submit('Yes');
  await see("document.querySelector('#thread').lastChild.textContent.includes('formal written notice')");
  await submit('No');
  await see("document.querySelector('#thread').lastChild.textContent.includes('short for rent')");
  await submit('400');
  await see("document.querySelector('#thread').lastChild.textContent.includes('date is your rent due')");
  await submit('2026-12-01');
  await see("document.querySelector('#thread').lastChild.textContent.includes('run out of food today or tomorrow')");
  await submit('Yes');
  await see("document.querySelector('#thread').lastChild.textContent.includes('money can your household use now')");
  await submit('20');
  await see("document.querySelector('#summary-area h2')?.textContent === 'Situation Summary'");
  await js(`{
    const label = [...document.querySelectorAll('#summary-area label')].find(e=>e.textContent.includes('Monthly household income'));
    const field = label.querySelector('input');
    field.value='950'; field.dispatchEvent(new Event('input',{bubbles:true}));
  }`);
  await cdp('Page.reload');
  await see("Array.from(document.querySelectorAll('#summary-area input')).some(i=>i.value==='950')");
  await js("Array.from(document.querySelectorAll('#summary-area button')).find(b=>b.textContent==='Confirm Information').click()");
  await see("!document.querySelector('#go-plan')?.classList.contains('hidden')");
  await js("document.querySelector('#go-plan').click()");
  assert(await js("document.querySelector('#search-scope').textContent.includes('local Sacramento program database')"));
  const menuItems = await js("Array.from(document.querySelectorAll('.plan-sections button'), e=>e.textContent)");
  assert.deepEqual(menuItems.slice(0, 2), ['Food Bank', 'CalFresh']);
  assert.deepEqual(menuItems.slice(2).sort(), ['Housing', 'Income']);
  const activeGroup = "document.querySelector('.need-group')";
  const jump = label => js(`[...document.querySelectorAll('.plan-sidebar button')].find(b=>b.textContent.endsWith('${label}')).click()`);
  assert.equal(await js(activeGroup+".querySelectorAll('.provider-options button').length"), 5);
  assert(await js(activeGroup+".querySelector('.featured-head .illustration.food') !== null"));
  assert(await js("document.querySelector('.plan-start').textContent.includes('Your household reported an immediate need for food')"));
  assert.equal(await js(activeGroup+".querySelector('.priority-pill').textContent"), 'Do first');
  await jump('Housing');
  assert.equal(await js(activeGroup+".querySelector('h2').textContent"), 'Housing');
  assert.equal(await js(activeGroup+".querySelectorAll('.provider-options button').length"), 4);
  assert(await js(activeGroup+".querySelector('.featured-head .illustration.housing') !== null"));
  await js("document.querySelector('.plan-start button').click()");
  assert.equal(await js(activeGroup+".querySelector('h2').textContent"), 'Food Bank');
  assert.equal(await js(activeGroup+".querySelector('.priority-pill').textContent"), 'Do first');
  await jump('CalFresh');
  for (const label of ['CalFresh','Housing']) {
    await jump(label);
    assert(await js(activeGroup+".querySelectorAll('.program-panel-body li').length > 3"));
    assert(await js(activeGroup+".querySelector('.document-checklist input') !== null"));
    assert(await js(activeGroup+".querySelector('.full-guide a') !== null"));
  }
  await jump('Food Bank');
  const pantryCardId = await js(activeGroup + ".querySelector('select').dataset.cardId");
  await js(`{
    const select = ${activeGroup}.querySelector('select');
    select.value='in_progress'; select.dispatchEvent(new Event('change'));
  }`);
  const pantryProgress = `document.querySelector('.progress-group[data-label="Food Bank"] .progress-status-list')`;
  assert(await js(pantryProgress + ".textContent.includes('Elk Grove')"));
  assert(await js(pantryProgress + ".textContent.includes('In progress')"));
  await jump('CalFresh');
  await js(`{
    const group = ${activeGroup};
    group.querySelector('.document-checklist input').click();
    const select = group.querySelector('select');
    select.value='contacted_applied'; select.dispatchEvent(new Event('change'));
  }`);
  const calFreshProgress = "document.querySelector('.progress-group[data-label=CalFresh] .progress-status')";
  assert.equal(await js(calFreshProgress + '.textContent'), 'Contacted / applied');
  assert(await js(pantryProgress + ".textContent.includes('In progress')"));
  await js(`{
    const select = ${activeGroup}.querySelector('select');
    select.value='completed_received'; select.dispatchEvent(new Event('change'));
  }`);
  assert(await js("document.querySelector('.plan-sidebar .progress-count').textContent.includes('1 of 11')"));
  await nav('case');
  assert(await js("document.querySelector('#case-view').textContent.includes('1 of 11 options completed')"));
  assert(await js("document.querySelector('#case-view').textContent.includes('950')"));
  assert(await js("document.querySelector('.case-facts').textContent.includes('$950')"));
  assert.equal(await js("document.querySelectorAll('.case-action-row').length"), 11);
  assert.deepEqual(await js("[...document.querySelectorAll('.case-group-heading h3')].map(h=>h.textContent).sort()"),
    ['Food','Housing','Income']);
  assert.equal(await js("document.querySelector('.case-progress-meter').value"), 1);
  if (process.env.NAVIGATOR_CHECK_SCREENSHOT_DIR) {
    await js('window.scrollTo(0, 0)');
    const desktop = await cdp('Page.captureScreenshot', {format:'png'});
    await writeFile(join(process.env.NAVIGATOR_CHECK_SCREENSHOT_DIR, 'my-case-desktop.png'),
      Buffer.from(desktop.data,'base64'));
    await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    assert(await js("document.documentElement.scrollWidth <= window.innerWidth"));
    const mobile = await cdp('Page.captureScreenshot', {format:'png'});
    await writeFile(join(process.env.NAVIGATOR_CHECK_SCREENSHOT_DIR, 'my-case-mobile.png'),
      Buffer.from(mobile.data,'base64'));
    await cdp('Emulation.clearDeviceMetricsOverride');
  }
  await js(`{
    const card = ${state}.response.plan.action_cards.find(item => item.card_id === ${JSON.stringify(pantryCardId)});
    const select = [...document.querySelectorAll('#live-case-panel select')]
      .find(el => el.getAttribute('aria-label') === 'Progress for ' + card.action_title);
    select.value='waiting_for_response'; select.dispatchEvent(new Event('change'));
  }`);
  await cdp('Page.reload');
  await see("document.querySelector('#case-view')?.textContent.includes('1 of 11 options completed')");
  await nav('plan');
  assert(await js(activeGroup+".querySelector('.document-checklist input').checked"));
  assert.equal(await js(activeGroup+".querySelector('select').value"), 'completed_received');
  assert(await js(pantryProgress + ".textContent.includes('Waiting for response')"));
  assert.equal(await js(calFreshProgress + '.textContent'), 'Completed / received');
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  assert(await js("document.documentElement.scrollWidth <= window.innerWidth"));
  await js("document.querySelector('.plan-sections button').click()");
  await js(activeGroup+".querySelectorAll('.provider-options button')[2].click()");
  await cdp('Page.reload');
  await see(activeGroup+"?.querySelectorAll('.provider-options button')[2]?.getAttribute('aria-pressed') === 'true'");
  await nav('case');
  await js("document.querySelector('#reset-case').click()");
  assert.equal(await js(state+'.response'), null);
  assert.equal(await js("document.querySelectorAll('.need-group').length"), 0);

  await submit('I am struggling to pay rent and need food.');
  await see(state+"?.response?.questions?.[0]?.fact_key === 'triggering_circumstances'");
  const missingLocation = {
    triggering_circumstances: 'My employer cut my hours from 40 to 15 hours per week.',
    household_gross_monthly_income: '$900 per month',
    household_size: '3 people',
    has_rental_agreement: 'Yes',
    has_written_eviction_notice: 'No',
    rent_shortfall_amount: '400', rent_due_date: '2026-12-01',
    food_needed_by_tomorrow: 'No', cash_on_hand_approx: '20'
  };
  for (let turn = 0; turn < 12; turn++) {
    const r = await js(state);
    if (r.response.status === 'needs_confirmation') break;
    const question = r.response.questions[r.answers.length];
    let skip = question.fact_key === 'zip_code' && question.can_skip;
    if (skip) await js("document.querySelector('#skip').click()");
    else await submit(missingLocation[question.fact_key] || 'I do not know.');
    await see(`${state}.answers.length !== ${r.answers.length} || ${state}.response.case_version !== ${r.response.case_version}`);
  }
  assert.equal(await js(state + '.response.status'), 'needs_confirmation');
  assert(await js(state+'.response.case.skipped_keys.includes("zip_code")'));
  await js("Array.from(document.querySelectorAll('#summary-area button')).find(b=>b.textContent==='Confirm Information').click()");
  await see(state+".response.status === 'completed'");
  assert(await js(state+'.response.limitations.length > 0'));
  await nav('case');
  await js("document.querySelector('#reset-case').click()");
  await submit("My parents just passed out and I'm a freshman university student, I have no money and home.");
  await see("document.querySelector('#thread').lastChild.textContent.includes('safe place to stay tonight')");
  await submit('No');
  await see("document.querySelector('#thread').lastChild.textContent.includes('ZIP code')");
  await submit('95814');
  await see("document.querySelector('#thread').lastChild.textContent.includes('gross monthly household income')");
  await submit('0');
  await see("document.querySelector('#thread').lastChild.textContent.includes('need help getting food')");
  await js("document.querySelector('#skip').click()");
  await see("document.querySelector('#summary-area h2')?.textContent === 'Situation Summary'");
  const selectedNeeds = "[...document.querySelectorAll('#summary-area fieldset input:checked')].map(e=>e.value)";
  for (const category of ['food_assistance','income_assistance']) {
    await js(`document.querySelector('#summary-area fieldset input[value="${category}"]').click()`);
  }
  await cdp('Page.reload');
  await see(selectedNeeds + '.length === 2');
  await js("Array.from(document.querySelectorAll('#summary-area button')).find(b=>b.textContent==='Confirm Information').click()");
  await see(state+".response.status === 'completed'");
  assert.deepEqual(await js(state+".response.case.needs.map(n=>n.category).sort()"),
    ['food_assistance','housing_assistance','income_assistance']);
  await nav('case');
  await js("document.querySelector('#reset-case').click()");
  await submit("I lost my job, and I have two children.");
  for (const [prompt, answer] of [
    ['ZIP code', '95814'], ['gross monthly household income', '0'],
    ['need help getting food', 'Yes'], ['pay for housing', 'Yes'],
    ['How many people', '3'], ['money can your household use now', '20'],
    ['written rental or lease agreement', 'Yes'], ['formal written notice', 'No'],
    ['short for rent', '400'], ['date is your rent due', 'December 1'],
    ['run out of food today or tomorrow', 'Tomorrow']
  ]) {
    await see(`document.querySelector('#thread').lastChild.textContent.includes(${JSON.stringify(prompt)})`);
    await submit(answer);
  }
  await see("document.querySelector('#summary-area h2')?.textContent === 'Situation Summary'");
  assert.deepEqual(await js(state+".response.summary.needs.map(n=>n.category).sort()"),
    ['food_assistance','housing_assistance','income_assistance']);
  await js("Array.from(document.querySelectorAll('#summary-area button')).find(b=>b.textContent==='Confirm Information').click()");
  await see(state+".response.status === 'completed'");
  assert.deepEqual(await js(state+".response.plan_by_need.map(n=>n.category).sort()"),
    ['food_assistance','housing_assistance','income_assistance']);
  assert(await js(state+".response.plan.action_cards.some(c=>c.user_target_date?.endsWith('-12-01') && !c.official_deadline)"));
  assert(await js(state+".response.case.case_facts.some(f=>f.field==='rent_shortfall_amount' && f.value===400)"));
  await nav('plan');
  assert(await js("document.querySelector('.post-plan-choices').textContent.includes('Email me a copy')"));
  const openChoice = label => js(`[...document.querySelectorAll('.post-plan-choices summary')].find(e=>e.textContent===${JSON.stringify(label)}).click()`);
  await openChoice('Email me a copy');
  await openChoice('Preview the email');
  assert(await js("document.querySelector('.email-preview').open"));
  assert(await js("document.querySelector('.email-preview').textContent.includes('Do first')"));
  assert(await js("document.querySelector('.email-preview').textContent.includes('Your target date:')"));
  assert(await js("document.querySelector('.email-preview a[href^=https]') !== null"));
  assert(await js("!document.querySelector('.email-preview').textContent.includes('I lost my job, and I have two children.')"));

  const emailInput = "document.querySelector('.post-plan-choices input[type=email]')";
  assert.equal(await js(emailInput + '.checkValidity()'), false);
  const callsBefore = await js("performance.getEntriesByType('resource').length");
  await js(emailInput + ".value='family@example.com'; document.querySelector('.post-plan-choices form').requestSubmit()");
  await see("document.querySelector('.post-plan-choices [role=status]').textContent.includes('No email was sent')");
  assert(await js("document.querySelector('.email-preview').textContent.includes('CalFresh')"));
  assert.equal(await js(emailInput + '.value'), '');
  assert.equal(await js("performance.getEntriesByType('resource').length"), callsBefore);
  assert.equal(await js("sessionStorage.getItem('navigator-local-case-v1').includes('family@example.com')"), false);
  await openChoice('Create an account');
  assert(await js("document.querySelector('.post-plan-choices details:nth-of-type(2)').open"));
  const finish = js("[...document.querySelectorAll('.post-plan-choices button')].find(b=>b.textContent==='Finish without saving').click()");
  await delay(150);
  await cdp('Page.handleJavaScriptDialog', {accept:true});
  await finish;
  await see(state + '.response === null');

  await submit("My husband hits me. I want to leave with my two children, but I don't have any money.");
  const safetyOpen = "document.querySelector('#safety-alert').matches(':modal')";
  await see(safetyOpen);
  assert.equal(await js(state+'.response.safety_notice.blocks_plan'), false);
  assert(await js(`{
    const banner = document.querySelector('#safety-alert');
    const thread = document.querySelector('#thread');
    thread.scrollTop = thread.scrollHeight;
    banner.getBoundingClientRect().top >= 0 &&
      banner.getBoundingClientRect().bottom <= window.innerHeight &&
      !thread.contains(banner)
  }`));
  await js("document.querySelector('.safety-close').click()");
  await see("!" + safetyOpen);
  await see(state + '.safetyDismissed === true');
  assert.equal(await js(state+'.response.status'), 'needs_clarification');
  for (const [prompt, answer] of [
    ['safe place to stay tonight', 'No'], ['ZIP code', '95814'],
    ['gross monthly household income', '0'], ['need help getting food', 'No']
  ]) {
    await see(`document.querySelector('#thread').lastChild.textContent.includes(${JSON.stringify(prompt)})`);
    await submit(answer);
  }
  await see("document.querySelector('#summary-area').textContent.includes('Needs a safe place to stay')");
  await js("Array.from(document.querySelectorAll('#summary-area button')).find(b=>b.textContent==='Confirm Information').click()");
  await see(state+".response.status === 'completed'");
  assert.equal(await js(safetyOpen), false);
  await js("document.querySelector('.mobile-emergency').open=true; document.querySelector('.mobile-emergency [data-open-safety]').click()");
  await see(safetyOpen);
  await js("document.querySelector('#safety-alert .primary').click()");
  await see("!" + safetyOpen);
  await js("document.querySelector('#go-plan').click()");
  assert.equal(await js("document.querySelector('.need-group h2').textContent"), 'Housing');
  assert(await js("document.querySelector('.featured-plan h2').textContent.includes('Sacramento')"));

  await nav('case');
  await js("document.querySelector('#reset-case').click()");
  await submit('My landlord threatened to change the locks. I need help with rent.');
  await see(state+".response?.status === 'needs_clarification'");
  assert.equal(await js(state+'.response.safety_notice'), null);
  await nav('case');
  await js("document.querySelector('#reset-case').click()");
  await submit('I lost my job, and I have two children.');
  await see(state + ".response?.questions?.length === 2");
  await submit("My husband hits me. I'm in ZIP 95814.");
  await see(safetyOpen);
  assert.equal(await js(state + ".response.questions[0].fact_key"), 'household_gross_monthly_income');
  await js("document.querySelector('.safety-close').click()");
  await see(state + '.safetyDismissed === true');
  await cdp('Page.reload');
  await see("typeof setView === 'function' && !" + safetyOpen);
  assert(await js("!document.querySelector('.mobile-emergency [data-open-safety]').classList.contains('hidden')"));
  assert.deepEqual(errors, []);
  console.log('Chrome E2E: Sacramento plan, evidence panels, groups, edits, reloads, progress, checklist, reset, mobile width, and missing ZIP passed.');
} finally {
  ws?.close();
  chrome.kill();
}
