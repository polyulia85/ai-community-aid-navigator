/* External UI boundary only. Does not change any agent JSON contract. */
window.NavigatorAdapter = (() => {
 const list = v => Array.isArray(v) ? v : [];
 const text = v => v == null ? '' : String(v);
 const normalizeCard = (c,i) => ({
   id: text(c.card_id || c.action_id || c.id || `card_${i+1}`),
   title: text(c.action_title || c.title || 'Follow-up action'),
   priority: text(c.order_group || c.priority || 'unspecified').toUpperCase(),
   next: text(c.next_step || c.next || ''), reason: text(c.reason || ''),
   progress: text(c.progress_status || c.progress || 'not_started'),
   related_need_ids: list(c.related_need_ids),
   official_deadline: c.official_deadline ?? null,
   user_target_date: c.user_target_date ?? null,
   uncertainty: list(c.uncertainty_notes || c.uncertainty),
   details: {conditions:list(c.details?.conditions), documents:list(c.details?.documents), steps:list(c.details?.steps),contacts:list(c.details?.contacts)}
 });
 function fromEnvelope(payload){
  if (!payload || typeof payload !== 'object') throw Error('Invalid Supervisor payload');
  const phase=text(payload.phase || 'error');
  const plan=payload.action_plan || {};
  const raw=plan.cards ?? plan.action_cards ?? [];
  if(!Array.isArray(raw))throw Error('Action plan cards must be an array');
  return {case_id:text(payload.case_id || 'mock-case'),case_version:payload.case_version ?? 1,phase,
   messages:list(payload.messages),summary:payload.situation_summary || null,
   processing:payload.processing || null,errors:list(payload.errors),
   cards:raw.map(normalizeCard),coverage_gaps:list(plan.coverage_gaps),potential_options:list(plan.potential_options)};
 }
 function fromSupervisorReport(report){
  if(!report || typeof report !== 'object')throw Error('Invalid Supervisor report');
  const p=report.plan || {};
  return fromEnvelope({case_id:report.case_id,case_version:report.case_version,
   phase:report.outcome==='completed'?'action_plan':'error',
   action_plan:{cards:p.action_cards || [],coverage_gaps:p.coverage_gaps || [],potential_options:p.potential_options || []},
   errors:report.supervisor_issues || []});
 }
 return {fromEnvelope,fromSupervisorReport,normalizeCard};
})();
