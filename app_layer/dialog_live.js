(() => {
  const storageKey = 'navigator-local-case-v1';
  const categories = {
    food_assistance: 'Food', housing_assistance: 'Housing', income_assistance: 'Income',
    utility_assistance: 'Utilities', medical_health_coverage: 'Health care', debt_hardship: 'Debt',
    material_in_kind: 'Essentials', crowdfunding_guidance: 'Crowdfunding', other_unlisted: 'Other'
  };
  const fresh = () => ({
    response: null, answers: [], history: [], progress: {}, documents: {},
    edits: {}, selectedCards: {}, activePlan: null, rejected: [], added: [], view: 'chat', summaryOpen: true, safetyDismissed: false
  });
  let state = fresh();
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey));
    if (saved) {
      state = { ...state, ...saved };
      if (!Array.isArray(state.added)) state.added = state.added ? [state.added] : [];
    }
  } catch { /* The navigator can run in memory when storage is unavailable. */ }
  let busy = false;
  const greeting = $('thread').firstElementChild.cloneNode(true);

  function save() {
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(state));
    } catch {
      $('storage-status').textContent = 'This tab could not save your case. Keep it open to retain progress.';
    }
  }

  function showView(view) {
    state.view = view;
    setView(view);
    save();
  }

  function bubble(text, who = 'navigator') {
    const element = node('div', null, 'bubble ' + who);
    element.append(node('small', who === 'user' ? 'You' : 'Navigator'), node('p', text));
    return element;
  }

  const safetyDialog = $('safety-alert');
  const safetyLinks = document.querySelectorAll('[data-open-safety]');
  for (const button of safetyLinks) {
    button.onclick = () => { if (!safetyDialog.open) safetyDialog.showModal(); };
  }
  safetyDialog.addEventListener('close', () => {
    if (!state.response?.safety_notice) return;
    state.safetyDismissed = true;
    save();
  });

  function renderSafety(notice) {
    for (const button of safetyLinks) button.classList.toggle('hidden', !notice?.message);
    const body = $('safety-content');
    body.replaceChildren();
    if (!notice?.message) {
      if (safetyDialog.open) safetyDialog.close();
      return;
    }
    body.append(node('p', notice.message));
    const contacts = (notice.contacts || []).map(contact =>
      [contact.name || contact.label, contact.phone || contact.value].filter(Boolean).join(' · '));
    if (contacts.length) body.append(list(contacts));
    if (!state.safetyDismissed && !safetyDialog.open) safetyDialog.showModal();
  }

  function renderConversation() {
    const response = state.response;
    const thread = $('thread');
    thread.replaceChildren();
    renderSafety(response?.safety_notice);
    thread.append(greeting.cloneNode(true));
    for (const { text, who } of state.history) thread.append(bubble(text, who));
    const question = response?.questions?.[state.answers.length];
    if (question) thread.append(bubble(question.text));
    const reviewing = response?.status === 'needs_confirmation';
    const completed = response?.status === 'completed';
    if (reviewing && !state.summaryOpen) {
      const reopen = node('button', 'Review Situation Summary', 'primary');
      reopen.onclick = () => { state.summaryOpen = true; save(); renderConversation(); };
      thread.append(reopen);
    }
    thread.scrollTop = thread.scrollHeight;
    $('message').placeholder = question ? 'Type your answer…' : 'Type your story…';
    $('skip').classList.toggle('hidden', question?.can_skip !== true);
    document.querySelector('.composer').classList.toggle('hidden', reviewing || completed);
    $('go-plan').classList.toggle('hidden', !completed);
    $('go-plan').textContent = 'Go to Action Plan';
    renderSummary(reviewing && state.summaryOpen ? response.summary : null);
  }

  async function request(route, payload) {
    const result = await fetch('/api/dialog/' + route, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    const response = await result.json();
    if (!result.ok || response.status === 'failed') {
      throw Error(response.user_message || response.issues?.map(issue => issue.message).join(' · ') ||
        'Supervisor request failed.');
    }
    if (!response.case || !['needs_clarification', 'needs_confirmation', 'completed'].includes(response.status)) {
      throw Error('Supervisor returned an unexpected response.');
    }
    return response;
  }

  async function send(route, payload, apply) {
    busy = true;
    const controls = [...document.querySelectorAll('#summary-area input, #summary-area select, #summary-area button'),
      ...['send', 'send-reviewed', 'skip', 'reset-case', 'message', 'transcript', 'mic', 'discard', 'retry']
        .map($).filter(Boolean)];
    controls.forEach(control => { control.disabled = true; });
    $('request-status').textContent = route === 'confirm' ? 'Preparing your Action Plan…' : 'Processing…';
    try {
      const response = await request(route, payload);
      apply();
      state.response = response;
      save();
      $('request-status').textContent = '';
      renderConversation();
      renderPlan();
      renderCase();
      if (route !== 'confirm' && state.view === 'chat' && response.status === 'needs_clarification' && !safetyDialog.open) {
        $('message').focus();
      }
    } catch (error) {
      $('request-status').textContent = error.message + ' Please try again.';
    } finally {
      controls.forEach(control => { control.disabled = false; });
      busy = false;
    }
  }

  function clearComposer() {
    $('message').value = '';
    $('transcript').value = '';
    $('review').classList.add('hidden');
  }

  async function submit(value, skip = false) {
    const text = String(value || '').trim();
    if (busy || (!skip && !text)) return;
    const response = state.response;
    if (!response) {
      await send('start', { story_text: text, locale: 'en-US' }, () => {
        state.history.push({ text, who: 'user' });
        clearComposer();
      });
      return;
    }
    const question = response.questions?.[state.answers.length];
    if (response.status !== 'needs_clarification' || !question || (skip && !question.can_skip)) return;
    const item = skip ? { question_id: question.question_id, skipped: true }
      : { question_id: question.question_id, answer_text: text };
    const answers = [...state.answers, item];
    const record = () => {
      state.history.push({ text: question.text }, { text: skip ? 'I don’t know' : text, who: 'user' });
      clearComposer();
    };
    await send('answer', { case: response.case, answers, keep_pending: true }, () => {
      record();
      state.answers = [];
    });
  }

  function renderSummary(summary) {
    const area = $('summary-area');
    area.replaceChildren();
    area.classList.toggle('hidden', !summary);
    if (!summary) return;
    area.append(node('h2', 'Situation Summary'), node('p', summary.narrative));
    area.append(node('h3', 'Needs'));
    for (const need of summary.needs) {
      const row = node('label', null, 'summary-field');
      const check = node('input');
      check.type = 'checkbox';
      check.checked = !state.rejected.includes(need.need_id);
      check.onchange = () => {
        state.rejected = state.rejected.filter(id => id !== need.need_id);
        if (!check.checked) state.rejected.push(need.need_id);
        save();
      };
      row.append(check, node('span', [need.label, need.description].filter(Boolean).join(' · ')));
      area.append(row);
    }
    area.append(node('h3', 'Review or correct facts'));
    for (const fact of [...summary.facts, ...summary.unknown]) {
      const row = node('label', null, 'summary-field');
      const isBoolean = typeof fact.value === 'boolean' ||
        ['has_written_eviction_notice', 'has_court_writ_or_judgment', 'imminent_removal_in_progress', 'needs_food_help', 'needs_housing_help',
          'has_safe_place_tonight', 'has_rental_agreement', 'student_employability_program', 'food_needed_by_tomorrow'].includes(fact.field);
      const field = node(isBoolean ? 'select' : 'input');
      if (isBoolean) field.append(new Option('Unknown', ''), new Option('Yes', 'true'), new Option('No', 'false'));
      if (typeof fact.value === 'object' && fact.value !== null) field.readOnly = true;
      const original = Array.isArray(fact.value) ? fact.value.join(', ') : String(fact.value ?? '');
      field.value = state.edits[fact.field] ?? original;
      field.oninput = () => {
        if (!field.value.trim() || field.value === original) delete state.edits[fact.field];
        else state.edits[fact.field] = isBoolean ? field.value === 'true' : field.value.trim();
        save();
      };
      row.append(node('span', fact.label), field);
      area.append(row);
    }
    const extra = node('fieldset');
    extra.append(node('legend', 'Add needs'));
    for (const [id, name] of Object.entries(categories)) {
      if (summary.needs.some(need => need.category === id)) continue;
      const row = node('label', null, 'summary-field');
      const check = node('input');
      check.type = 'checkbox';
      check.value = id;
      check.checked = state.added.includes(id);
      check.onchange = () => {
        state.added = state.added.filter(category => category !== id);
        if (check.checked) state.added.push(id);
        save();
      };
      row.append(check, node('span', name));
      extra.append(row);
    }
    if (extra.children.length > 1) area.append(extra);
    const back = node('button', 'Back to Conversation', 'quiet');
    back.onclick = () => { state.summaryOpen = false; save(); renderConversation(); };
    const confirm = node('button', 'Confirm Information', 'primary');
    confirm.onclick = () => {
      if (busy) return;
      const added_needs = state.added.map(category => ({ category }));
      send('confirm', {
        case: state.response.case, corrections: state.edits, rejected_need_ids: state.rejected, added_needs
      }, () => { state.history.push({ text: 'You can open your Action Plan now.' }); });
    };
    area.append(back, confirm);
  }

  function postPlanChoices(response) {
    const section = node('section', null, 'post-plan-choices');
    section.append(node('h2', 'What would you like to do with your plan?'));

    const email = node('details', null, 'program-panel');
    email.append(node('summary', 'Email me a copy'));
    const body = node('div', null, 'program-panel-body');
    body.append(node('p', 'Get a one-time copy of the plan you see now, with your next steps, dates and source links. You can preview it below. This demo simulates sending.'));
    const preview = node('details', null, 'email-preview');
    preview.append(node('summary', 'Preview the email'));
    const message = node('div', null, 'email-preview-body');
    message.append(node('h3', 'Your Community Aid Navigator plan'));
    const cards = new Map(response.plan.action_cards.map(card => [card.card_id, card]));
    const first = [...cards.values()].find(card => card.order_group === 'first');
    if (first) message.append(node('p', 'Do first: ' + first.action_title), node('p', first.priority_reason));
    const included = new Set();
    for (const group of response.plan_by_need) {
      message.append(node('h4', group.label || group.category));
      for (const id of group.card_ids) {
        const card = cards.get(id);
        if (!card || included.has(id)) continue;
        included.add(id);
        appendEmailAction(message, card, response.card_details?.[id]);
      }
      if (group.gap_notes?.length) message.append(list(group.gap_notes));
    }
    const remaining = [...cards.values()].filter(card => !included.has(card.card_id));
    if (remaining.length) {
      message.append(node('h4', 'Additional actions'));
      for (const card of remaining) appendEmailAction(message, card, response.card_details?.[card.card_id]);
    }
    message.append(node('p', 'This copy reflects the plan at the time it is prepared. Contact the listed organizations to confirm current availability and requirements.'));
    preview.append(message);
    body.append(preview, node('p', 'Use a test address for this demo. When sending is available, use an inbox you can access privately.', 'muted'));

    const form = node('form');
    const label = node('label', 'Test email address', 'summary-field');
    const address = node('input');
    address.type = 'email';
    address.required = true;
    address.placeholder = 'family@example.com';
    address.autocomplete = 'off';
    label.append(address);
    const submit = node('button', 'Simulate sending', 'primary');
    submit.type = 'submit';
    const status = node('p');
    status.setAttribute('role', 'status');
    form.append(label, submit, status);
    form.onsubmit = event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      preview.open = true;
      status.textContent = 'Demo complete. No email was sent and no account was created.';
      address.value = '';
    };
    body.append(form);
    email.append(body);

    const registration = node('details', null, 'program-panel');
    const accountBody = node('div', null, 'program-panel-body');
    accountBody.append(
      node('p', 'With an account, you will be able to return to your plan, update your progress and tell the Navigator when your circumstances change. You can review changes before updating the plan.'),
      node('p', 'Account creation and recovery are unavailable in this local demo. Your current plan and progress stay in this browser tab.', 'muted')
    );
    registration.append(node('summary', 'Create an account'), accountBody);
    const finish = node('button', 'Finish without saving', 'quiet');
    finish.onclick = () => {
      if (window.confirm('Finish and clear this conversation, plan and progress from this tab?')) {
        $('reset-case').click();
      }
    };
    section.append(email, registration, finish);
    return section;
  }

  function appendEmailAction(message, card, details) {
    const action = node('section', null, 'email-preview-action');
    action.append(node('h5', card.action_title));
    if (card.next_step) action.append(node('p', card.next_step));
    if (card.user_target_date) action.append(node('p', 'Your target date: ' + card.user_target_date));
    if (card.official_deadline) action.append(node('p', 'Official deadline: ' + card.official_deadline));
    const sources = new Map();
    for (const source of details?.sources || []) {
      if (/^https?:\/\//i.test(source.source_url || '') && !sources.has(source.source_url)) {
        sources.set(source.source_url, source.source_title || source.source_url);
      }
    }
    if (sources.size) {
      const links = node('ul');
      for (const [url, title] of sources) {
        const link = node('a', title);
        link.href = url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        const item = node('li');
        item.append(link);
        links.append(item);
      }
      action.append(node('p', 'Sources'), links);
    }
    message.append(action);
  }

  function renderPlan() {
    const response = state.response;
    const root = $('plan-cards');
    root.replaceChildren();
    $('bridge-status').textContent = '';
    $('plan-state').textContent = 'Confirm your Situation Summary to generate a plan.';
    if (response?.status !== 'completed') return;
    const cards = new Map(response.plan.action_cards.map(card => [card.card_id, card]));
    const groups = [...response.plan_by_need];
    const assigned = new Set(groups.flatMap(group => group.card_ids));
    const remaining = [...cards.keys()].filter(id => !assigned.has(id));
    if (remaining.length) groups.push({ label: 'Additional actions', card_ids: remaining, gap_notes: [] });
    $('bridge-status').textContent = 'Agent 10: ' + (response.final_validation?.verdict || 'Unavailable');
    $('plan-state').textContent = [...(response.limitations || []),
      response.plan.withheld_card_ids?.length ? 'Some options were held back during validation.' : '']
      .filter(Boolean).join(' ');

    const sections = groups.flatMap(group => {
      if (group.category !== 'food_assistance') return [group];
      const idsFor = subcategory => group.card_ids.filter(id =>
        response.card_details?.[id]?.subcategory === subcategory);
      const pantryIds = idsFor('food_pantry');
      const calFreshIds = idsFor('calfresh_benefits');
      const foodSections = [];
      if (pantryIds.length) foodSections.push({
        ...group, need_id: group.need_id + ':pantry', label: 'Food Bank',
        card_ids: pantryIds, gap_notes: []
      });
      if (calFreshIds.length) foodSections.push({
        ...group, need_id: group.need_id + ':calfresh', label: 'CalFresh',
        card_ids: calFreshIds, gap_notes: []
      });
      const otherIds = group.card_ids.filter(id => !pantryIds.includes(id) && !calFreshIds.includes(id));
      if (otherIds.length || group.gap_notes?.length || !foodSections.length) {
        foodSections.push({ ...group, card_ids: otherIds });
      }
      return foodSections;
    });

    const priority = new Map([['first', 0], ['parallel', 1], ['later', 2]]);
    const sectionPriority = section => Math.min(3, ...section.card_ids.map(id =>
      priority.get(cards.get(id)?.order_group) ?? 3));
    sections.sort((left, right) => sectionPriority(left) - sectionPriority(right));

    if (!cards.size) root.append(node('p', 'No program cards were released.', 'empty-plan'));
    if (!sections.length) {
      root.append(postPlanChoices(response));
      return;
    }
    const layout = node('div', null, 'plan-layout restored-plan-layout');
    const primary = node('div', null, 'plan-primary');
    const sidebar = node('aside', null, 'plan-sidebar');
    const count = node('p', null, 'progress-count');
    const track = node('div', null, 'progress-track');
    const fill = node('div', null, 'progress-fill');
    track.append(fill);
    sidebar.append(node('h3', 'Your progress'), count, track);
    const journey = node('div', null, 'journey plan-sections');
    const host = node('div');
    primary.append(journey, host);
    layout.append(primary, sidebar);
    const first = [...cards.values()].find(card => card.order_group === 'first');
    const firstSection = first ? sections.findIndex(group => group.card_ids.includes(first.card_id)) : -1;
    if (firstSection >= 0) {
      const start = node('section', null, 'based-on plan-start');
      const open = node('button', 'Open first step', 'primary');
      open.onclick = () => choose(firstSection, true, first.card_id);
      start.append(node('h2', 'Start here'), node('strong', first.action_title));
      if (first.priority_reason) start.append(node('p', first.priority_reason));
      start.append(open);
      root.append(start);
    }
    root.append(layout, postPlanChoices(response));

    function updateProgress() {
      const cardStatus = card => state.progress[card.card_id] || card.progress_status || 'not_started';
      const done = [...cards.values()].filter(card => cardStatus(card) === 'completed_received').length;
      count.textContent = `${done} of ${cards.size} options completed`;
      fill.style.width = (cards.size ? 100 * done / cards.size : 0) + '%';

      for (const [index, group] of sections.entries()) {
        const { progressRows, shortcutGroup } = menus[index];
        const groupCards = group.card_ids.map(id => cards.get(id)).filter(Boolean);
        const tracked = groupCards.filter(card => cardStatus(card) !== 'not_started');
        shortcutGroup.dataset.hasProgress = String(tracked.length > 0);
        progressRows.replaceChildren();
        for (const card of groupCards.length === 1 ? groupCards : tracked) {
          const key = cardStatus(card);
          const status = statuses.find(([value]) => value === key)?.[1] || 'Not started';
          const row = node('li', null, 'progress-status-row');
          if (groupCards.length > 1) {
            const details = response.card_details?.[card.card_id] || {};
            row.append(node('span', details.program_name || card.action_title, 'progress-provider'));
          }
          const pill = node('span', status, 'progress-status');
          pill.dataset.status = key;
          row.append(pill);
          progressRows.append(row);
        }
      }
    }

    function choose(index, scroll = false, cardId = null) {
      const group = sections[index];
      const id = group.need_id || 'additional';
      state.activePlan = id;
      save();
      for (const [i, { buttons }] of menus.entries()) {
        for (const [button, activeClass] of buttons) {
          button.classList.toggle(activeClass, i === index);
          button.setAttribute('aria-pressed', String(i === index));
        }
      }
      const section = node('section', null, 'need-group');
      section.append(node('h2', group.label || group.category));
      if (group.urgency_reason) section.append(node('p', group.urgency_reason, 'muted'));
      const groupCards = group.card_ids.map(cardId => cards.get(cardId)).filter(Boolean);
      if (groupCards.length) {
        const options = node('div', null, 'journey provider-options');
        const panel = node('div');
        const tabs = groupCards.map(card => {
          const details = response.card_details?.[card.card_id] || {};
          const button = node('button', details.program_name || card.action_title, 'journey-step');
          button.onclick = () => {
            state.selectedCards[id] = card.card_id;
            save();
            tabs.forEach(tab => {
              tab.classList.toggle('active', tab === button);
              tab.setAttribute('aria-pressed', String(tab === button));
            });
            panel.replaceChildren(renderCard(card, details, cards, state, () => {
              save();
              renderCase();
              updateProgress();
            }, group.category));
            panel.querySelector('select').dataset.cardId = card.card_id;
          };
          return button;
        });
        options.append(...tabs);
        if (tabs.length > 1) section.append(options);
        section.append(panel);
        const selected = groupCards.findIndex(card =>
          card.card_id === (cardId ?? state.selectedCards[id]));
        tabs[Math.max(selected, 0)].click();
      }
      if (group.gap_notes?.length) section.append(list(group.gap_notes));
      host.replaceChildren(section);
      if (scroll && journey.getBoundingClientRect().top < 0) {
        journey.scrollIntoView({ block: 'start' });
      }
    }

    const menus = sections.map((group, index) => {
      const label = group.label || group.category;
      const tab = node('button', label, 'journey-step ' + planTheme(group.category));
      const shortcut = node('button', null, 'progress-item');
      shortcut.append(planEmblem(group.category), node('span', label));
      tab.onclick = () => choose(index);
      shortcut.onclick = () => choose(index, true);
      journey.append(tab);
      const shortcutGroup = node('div', null, 'progress-group');
      shortcutGroup.dataset.label = label;
      const progressRows = node('ul', null, 'progress-status-list');
      shortcutGroup.append(shortcut, progressRows);
      sidebar.append(shortcutGroup);
      return { buttons: [[tab, 'active'], [shortcut, 'selected']], progressRows, shortcutGroup };
    });
    updateProgress();
    const previous = sections.findIndex(group => (group.need_id || 'additional') === state.activePlan);
    const initial = previous < 0;
    choose(initial ? Math.max(firstSection, 0) : previous, false, initial ? first?.card_id : null);
  }

  const caseFactLabels = {
    zip_code: 'ZIP code', employment_status: 'Work situation', household_size: 'Household size',
    household_gross_monthly_income: 'Monthly income before taxes', rent_amount_monthly: 'Monthly rent',
    rent_shortfall_amount: 'Amount short for rent', rent_arrears_amount: 'Rent owed',
    cash_on_hand_approx: 'Money available now', rent_due_date: 'Rent due date',
    food_needed_by_tomorrow: 'Food needed today or tomorrow'
  };
  const caseMoneyFields = new Set([
    'household_gross_monthly_income', 'rent_amount_monthly', 'rent_shortfall_amount',
    'rent_arrears_amount', 'cash_on_hand_approx'
  ]);

  function readableCaseValue({ field, value }) {
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (Array.isArray(value)) return value.join(', ');
    if (caseMoneyFields.has(field) && typeof value === 'number') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 2
      }).format(value);
    }
    if (field.endsWith('_date') && typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
      const date = new Date(value + 'T00:00:00Z');
      if (Number.isFinite(date.valueOf())) {
        return new Intl.DateTimeFormat('en-US', {
          month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC'
        }).format(date);
      }
    }
    const text = String(value ?? '').replaceAll('_', ' ');
    return field === 'employment_status' ? text.charAt(0).toUpperCase() + text.slice(1) : text;
  }

  function renderCase() {
    const panel = $('live-case-panel');
    panel.replaceChildren();
    const response = state.response;
    if (response?.status !== 'completed') {
      panel.append(node('p', 'Confirm your Situation Summary to see your case here.', 'empty-plan'));
      return;
    }

    const { case_facts: facts, needs } = response.case;
    const cards = response.plan.action_cards;
    const byId = new Map(cards.map(card => [card.card_id, card]));
    const confirmedNeeds = needs.filter(need => need.confirmation_status === 'confirmed');
    const confirmedFacts = facts.filter(fact => fact.confirmation_status === 'confirmed');
    const overview = node('div', null, 'case-overview');

    const progress = node('section', null, 'case-progress-card');
    const progressHeader = node('div', null, 'case-progress-header');
    const pen = node('span', '✎', 'case-pen');
    pen.setAttribute('aria-hidden', 'true');
    progressHeader.append(node('h2', 'Your progress'), pen);
    const count = node('p', null, 'case-progress-count');
    count.setAttribute('role', 'status');
    const meter = node('progress', null, 'case-progress-meter');
    meter.max = cards.length || 1;
    meter.setAttribute('aria-label', 'Completed options');
    progress.append(progressHeader, count, meter);

    function updateCaseProgress() {
      const done = cards.filter(card =>
        (state.progress[card.card_id] || card.progress_status) === 'completed_received').length;
      meter.value = done;
      count.textContent = `${done} of ${cards.length} options completed`;
    }

    const summary = node('section', null, 'case-summary-card');
    summary.append(node('h2', 'Confirmed situation'));
    const chips = node('ul', null, 'case-needs');
    for (const need of confirmedNeeds) {
      const chip = node('li', null, 'case-need');
      chip.append(planEmblem(need.category), node('span', categories[need.category] || need.category));
      chips.append(chip);
    }
    if (chips.children.length) summary.append(chips);
    if (confirmedFacts.length) {
      const details = node('details', null, 'case-facts');
      details.append(node('summary', 'View confirmed details'));
      const fields = node('dl');
      for (const fact of confirmedFacts) {
        const name = fact.field.replaceAll('_', ' ');
        const label = caseFactLabels[fact.field] || name.charAt(0).toUpperCase() + name.slice(1);
        const pair = node('div');
        pair.append(node('dt', label), node('dd', readableCaseValue(fact)));
        fields.append(pair);
      }
      details.append(fields);
      summary.append(details);
    }
    overview.append(progress, summary);
    panel.append(overview);

    const groups = [...response.plan_by_need];
    const listed = new Set(groups.flatMap(group => group.card_ids));
    const remaining = cards.filter(card => !listed.has(card.card_id));
    if (remaining.length) groups.push({ label: 'Additional actions', card_ids: remaining.map(c => c.card_id) });

    const plan = node('section', null, 'case-action-list');
    plan.append(node('h2', 'Plan checklist'));
    for (const group of groups) {
      const section = node('section', null, 'case-action-group');
      const heading = node('div', null, 'case-group-heading');
      heading.append(planEmblem(group.category), node('h3', group.label || group.category));
      section.append(heading);
      for (const id of group.card_ids) {
        const card = byId.get(id);
        if (!card) continue;
        const details = response.card_details?.[id] || {};
        const row = node('div', null, 'case-action-row');
        const text = node('div', null, 'case-action-copy');
        const action = details.program_name && card.action_title.includes(': ')
          ? card.action_title.split(': ', 1)[0] : card.action_title;
        text.append(node('h4', details.program_name || card.action_title));
        if (details.program_name) {
          if (details.organization && !details.program_name.includes(details.organization)) {
            text.append(node('p', details.organization));
          }
          if (action && action !== details.program_name && action !== card.action_title) {
            text.append(node('p', action, 'case-action-verb'));
          }
        }
        const select = statusSelect(card, state.progress[id], value => {
          state.progress[id] = value;
          select.dataset.status = value;
          save();
          updateCaseProgress();
          renderPlan();
        });
        select.className = 'case-status-select';
        select.dataset.status = select.value;
        row.append(text, select);
        section.append(row);
      }
      for (const note of group.gap_notes || []) section.append(node('p', note, 'case-gap'));
      plan.append(section);
    }
    panel.append(plan);
    updateCaseProgress();
  }

  document.querySelectorAll('nav button').forEach(button => {
    button.onclick = () => showView(button.dataset.view);
  });
  $('go-plan').onclick = () => showView('plan');
  $('send').onclick = () => submit($('message').value);
  $('send-reviewed').onclick = () => submit($('transcript').value);
  $('skip').onclick = () => submit('', true);
  $('message').onkeydown = event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      submit($('message').value);
    }
  };
  $('reset-case').onclick = () => {
    if (busy) return;
    state = fresh();
    save();
    clearComposer();
    $('request-status').textContent = '';
    renderConversation();
    renderPlan();
    renderCase();
    showView('chat');
  };
  renderConversation();
  renderPlan();
  renderCase();
  setView(state.view);
})();
