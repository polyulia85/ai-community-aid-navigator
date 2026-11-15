/* Explicit developer-only fixture loader; never represents real program matches. */
(function(){
 const el=id=>document.getElementById(id);
 el('mock-load').addEventListener('click',async()=>{
  const name=el('mock-select').value;if(!name)return;
  const feedback=el('mock-feedback');feedback.textContent='Loading '+name+'…';
  try{const r=await fetch('./mock_ui/'+name+'.json',{cache:'no-store'});if(!r.ok)throw Error('Fixture unavailable');
   const envelope=window.NavigatorAdapter.fromEnvelope(await r.json());
   window.dispatchEvent(new CustomEvent('navigator:mock-loaded',{detail:envelope}));
   feedback.textContent='Mock loaded: '+name+'. Not a live Supervisor result.';
  }catch(e){feedback.textContent='Could not load fixture: '+e.message}
 });
})();
