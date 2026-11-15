const $ = id => document.getElementById(id);
const statuses = [
  ['not_started', 'Not started'], ['in_progress', 'In progress'],
  ['contacted_applied', 'Contacted / applied'], ['waiting_for_response', 'Waiting for response'],
  ['completed_received', 'Completed / received'], ['unsuccessful', 'Unsuccessful']
];

function node(tag, text, cls) {
  const element = document.createElement(tag);
  if (text != null) element.textContent = String(text);
  if (cls) element.className = cls;
  return element;
}

function setView(view) {
  document.querySelectorAll('nav button').forEach(button =>
    button.classList.toggle('active', button.dataset.view === view));
  for (const name of ['chat', 'plan', 'case']) $(name + '-view').classList.toggle('hidden', name !== view);
}

function itemText(item) {
  if (typeof item !== 'object' || item === null) return String(item ?? '');
  if (!('value' in item)) return JSON.stringify(item);
  return [item.label, item.value, item.hours, item.checked_at && 'Checked ' + item.checked_at,
    item.note].filter(Boolean).join(' · ');
}

function list(items) {
  const result = node('ul');
  for (const item of items) result.append(node('li', itemText(item)));
  return result;
}

function statusSelect(card, value, onChange) {
  const select = node('select');
  select.setAttribute('aria-label', 'Progress for ' + card.action_title);
  for (const [key, label] of statuses) select.append(new Option(label, key));
  select.value = value || card.progress_status || 'not_started';
  select.onchange = () => onChange(select.value);
  return select;
}

function planTheme(category) {
  return ({
    food_assistance: 'food', housing_assistance: 'housing', income_assistance: 'work'
  })[category] || 'support';
}

function planEmblem(category) {
  const theme = planTheme(category);
  const emblem = node('span', { food: '🥬', housing: '🏡', work: '💼', support: '🤝' }[theme],
    'plan-icon illustration ' + theme);
  emblem.setAttribute('aria-hidden', 'true');
  return emblem;
}

function renderCard(card, details, cards, state, update, category) {
  const article = node('article', null, 'featured-plan');
  const heading = node('div', null, 'featured-head');
  const title = node('div');
  title.append(node('h2', card.action_title));
  if (details.program_name && !card.action_title.includes(details.program_name)) {
    title.append(node('p', details.program_name));
  }
  if (details.organization) title.append(node('p', details.organization, 'muted'));
  const priority = { first: 'Do first', parallel: 'At the same time', later: 'Do later' }[card.order_group];
  if (priority) title.append(node('span', priority, 'priority-pill'));
  heading.append(planEmblem(category), title);
  article.append(heading);
  if (card.reason) {
    const why = node('section', null, 'based-on');
    why.append(node('h3', 'Based on what you shared'), node('p', card.reason));
    article.append(why);
  }
  if (card.priority_reason) article.append(node('p', card.priority_reason));
  if (card.uncertainty_notes?.length) article.append(list(card.uncertainty_notes));
  const panels = node('div', null, 'program-panels');
  const contacts = [...(card.contacts || []), ...(details.contacts || []).filter(item =>
    !card.contacts?.some(contact => contact.value === item.value))];
  for (const [key, label, items] of [
    ['steps', 'Your next steps', [...new Set([card.next_step].filter(Boolean)),
      ...(details.steps || []).filter(item => item.value !== card.next_step)]],
    ['contacts', 'Where to get help', contacts],
    ['conditions', 'Eligibility & requirements', details.conditions],
    ['documents', 'Documents to prepare', details.documents]
  ]) {
    const panel = node('details', null, 'program-panel');
    panel.open = key === 'steps';
    panel.append(node('summary', label));
    const body = node('div', null, 'program-panel-body');
    if (!items?.length) body.append(node('p', 'No verified information in the local knowledge base.'));
    else if (key !== 'documents') body.append(list(items));
    else {
      const checklist = node('div', null, 'document-checklist');
      for (const [index, item] of items.entries()) {
        const row = node('label');
        const check = node('input');
        check.type = 'checkbox';
        const id = card.card_id + ':' + index;
        check.checked = Boolean(state.documents[id]);
        check.onchange = () => {
          state.documents[id] = check.checked;
          update();
        };
        row.append(check, node('span', itemText(item)));
        checklist.append(row);
      }
      body.append(checklist);
    }
    panel.append(body);
    panels.append(panel);
  }
  article.append(panels);

  const guide = node('details', null, 'full-guide');
  guide.append(node('summary', 'Full program guide and sources'));
  const body = node('div', null, 'full-guide-body');
  for (const [label, items] of [
    ['Service area in the knowledge base', details.geography],
    ['Availability records', details.availability],
    ['Published deadline records', details.deadlines],
    ['Official deadline on this card', [card.official_deadline]],
    ['Your target date', [card.user_target_date]],
    ['Processing estimate', [card.processing_estimate]],
    ['Prerequisites', card.dependency_card_ids?.map(id => cards.get(id)?.action_title || id)]
  ]) {
    const values = (items || []).filter(value => value != null && value !== '');
    if (values.length) body.append(node('h4', label), list(values));
  }
  if (details.sources?.length) {
    body.append(node('h4', 'Source records'));
    const sources = node('ul');
    for (const source of details.sources) {
      const li = node('li');
      const title = source.source_title || source.source_url || source.evidence_id;
      if (/^https?:\/\//i.test(source.source_url || '')) {
        const link = node('a', title);
        link.href = source.source_url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        li.append(link);
      } else li.append(node('span', title));
      li.append(node('span', [source.checked_at && 'Checked ' + source.checked_at,
        source.effective_date && 'Effective ' + source.effective_date, source.notes]
        .filter(Boolean).map(text => ' · ' + text).join('')));
      sources.append(li);
    }
    body.append(sources);
  }
  guide.append(body);
  article.append(guide);
  const status = node('div', null, 'status-row');
  status.append(node('span', 'My progress'), statusSelect(card, state.progress[card.card_id], value => {
    state.progress[card.card_id] = value;
    update();
  }));
  article.append(status);
  return article;
}

let recognition = null;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
function record() {
  if (!SpeechRecognition) {
    $('speech-state').textContent = 'Speech recognition unavailable. Please type instead.';
    return;
  }
  if (recognition) {
    recognition.stop();
    return;
  }
  recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.onresult = event => {
    $('transcript').value = Array.from(event.results, result => result[0].transcript).join(' ');
    $('record-label').textContent = 'Speech transcript';
    $('review').classList.remove('hidden');
  };
  recognition.onerror = event => {
    $('speech-state').textContent = 'Voice error: ' + event.error + '. You can type instead.';
  };
  recognition.onend = () => {
    recognition = null;
    $('mic').textContent = '🎙 Speak';
    if ($('speech-state').textContent.startsWith('Listening')) {
      $('speech-state').textContent = 'Review the transcript before sending.';
    }
  };
  try {
    recognition.start();
    $('speech-state').textContent = 'Listening… tap Speak to stop';
    $('mic').textContent = '■ Stop';
  } catch {
    recognition = null;
    $('speech-state').textContent = 'Microphone could not start.';
  }
}
$('mic').onclick = record;
$('retry').onclick = () => { $('review').classList.add('hidden'); record(); };
$('discard').onclick = () => { $('transcript').value = ''; $('review').classList.add('hidden'); };
