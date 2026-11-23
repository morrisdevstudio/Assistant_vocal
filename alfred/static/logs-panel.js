const $ = id => document.getElementById(id);
let config, session, busy = false, displayed = [];
async function api(path, method = 'GET', value) {
  const response = await fetch(path, {method, cache:'no-store', headers:{'Content-Type':'application/json'}, ...(value === undefined ? {} : {body:JSON.stringify(value)})});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Opération impossible');
  return data;
}
function showEngine() {
  const stt = $('log-engine').value === 'stt'; $('log-stt').hidden = !stt; $('log-oww').hidden = stt;
}
async function loadConfig() {
  config = await api('/api/wake/config'); const v = config.settings.esp32;
  $('log-engine').value = v.engine; $('log-phrase').value = v.phrase;
  $('log-variants').value = v.variants.join(', '); $('log-threshold').value = v.threshold;
  const select = $('log-model'); select.replaceChildren();
  for (const model of config.models) { const o = document.createElement('option'); o.value=model.id; o.textContent=`${model.label} · ${model.phrase}`; select.append(o); }
  select.value = v.model; showEngine();
}
async function refreshLogs() {
  try {
    const entries = await api('/api/diagnostics?limit=1000'); $('logs-list').replaceChildren();
    const filter=$('logs-filter').value;
    displayed=entries.filter(e=>filter==='all'||(filter==='exchange' ? !['wake','wake-test'].includes(e.source) : e.source===filter));
    for (const entry of displayed) {
      const details=document.createElement('details'), summary=document.createElement('summary'), body=document.createElement('pre');
      summary.textContent=`${new Date(entry.created*1000).toLocaleString('fr-FR')} · ${entry.source || 'Diagnostic'} · ${entry.event || 'échange'}`;
      body.style.whiteSpace='pre-wrap'; body.textContent=JSON.stringify(entry,null,2); details.append(summary,body); $('logs-list').append(details);
    }
    $('logs-status').textContent=`${displayed.length} entrée(s) affichée(s).`;
  } catch(e) { $('logs-status').textContent=e.message; }
}
function render() {
  const active = session && !session.closed; const phase = session?.phase;
  for (const id of ['log-engine','log-model','log-threshold','log-phrase','log-variants','log-save','log-start']) $(id).disabled=Boolean(active)||busy;
  $('log-stop').disabled=!active||busy; $('log-ready').disabled=phase!=='placement'||busy;
  $('log-skip').disabled=phase!=='placement'||busy;
  $('log-missed').disabled=phase!=='trial'||busy; $('log-retry').disabled=phase!=='trial'||busy;
  if (!session) { $('log-test-status').textContent='Aucun test en cours.'; return; }
  const messages={silence_initial:`Ne parlez pas : mesure du silence (${session.remaining} s).`,silence_final:`Ne parlez pas : silence final (${session.remaining} s).`,placement:`Placez-vous à ${session.distance} m, face à la carte, puis confirmez.`,trial:`Essai ${session.number}/25 à ${session.distance} m : dites « ${session.phrase} » une fois.`,pause:'Essai enregistré. Patientez trois secondes.',interrupted:'Flux interrompu : essai suspendu, vérifiez la connexion.',termine:'Test terminé.',interrompu:'Test interrompu.'};
  $('log-test-status').textContent=messages[phase]||phase;
  if(phase==='trial' && session.trial_elapsed>=10) $('log-test-status').textContent+=' Si vous avez parlé, marquez l’appel manqué ; sinon, recommencez.';
  const results=$('log-results'); results.replaceChildren();
  if (session.results.length) {
    const measured=session.results.filter(x=>x.outcome!=='skipped');
    const p=document.createElement('p'); p.textContent=`${measured.filter(x=>x.outcome==='detected').length} détection(s) sur ${measured.length} essais réalisés.`; results.append(p);
    for (const distance of [0.5,1,2,3]) { const group=measured.filter(x=>x.distance===distance); if(!group.length) continue; const row=document.createElement('p'); row.textContent=`${distance} m : ${group.filter(x=>x.outcome==='detected').length}/${group.length} détectés`; results.append(row); }
  }
}
async function poll() {
  try { const [test, terminal]=await Promise.all([api('/api/wake-test'),api('/api/terminal/status')]); session=test;
    const w=terminal.wake_word||{}; $('log-terminal-status').textContent=`ESP32 : ${terminal.connected?'connecté':'déconnecté'} · flux ${w.receiving?'reçu':'absent'} · moteur ${w.engine||'indisponible'} · analyses ${w.inferences||0}`;
    render(); } catch(e) { $('log-test-status').textContent=e.message; }
}
async function action(name) {
  if (!session || busy) return; busy=true; render();
  try { session=await api(`/api/wake-test/${name}`,'POST',{id:session.id,number:session.number}); }
  catch(e) { $('log-test-status').textContent=e.message; }
  finally { busy=false; render(); if(session?.closed) refreshLogs(); }
}
$('log-engine').addEventListener('change',showEngine);
async function saveSettings(){
  const v={...config.settings.esp32,engine:$('log-engine').value,model:$('log-model').value,threshold:Number($('log-threshold').value),phrase:$('log-phrase').value,variants:$('log-variants').value.split(',').map(x=>x.trim()).filter(Boolean)};
  if(JSON.stringify(v)!==JSON.stringify(config.settings.esp32)) await api('/api/wake/config/esp32','PUT',v);
  await loadConfig();
}
$('log-save').addEventListener('click', async()=>{try {await saveSettings(); $('log-test-status').textContent='Réglages enregistrés.';} catch(e) {$('log-test-status').textContent=e.message;}});
$('log-start').addEventListener('click',async()=>{try {await saveSettings(); session=await api('/api/wake-test/start','POST',{}); render();} catch(e) {$('log-test-status').textContent=e.message;} });
for (const [id,name] of [['log-ready','ready'],['log-skip','skip'],['log-missed','missed'],['log-retry','retry'],['log-stop','stop']]) $(id).addEventListener('click',()=>action(name));
$('logs-refresh').addEventListener('click',refreshLogs);
$('logs-filter').addEventListener('change',refreshLogs);
$('logs-export').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(displayed,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='alfred-logs.json';link.click();URL.revokeObjectURL(url);});
window.addEventListener('hashchange',()=>{ if(location.hash==='#logs'){loadConfig().catch(()=>{}); refreshLogs(); poll();} });
setInterval(()=>{ if(location.hash==='#logs' || (session && !session.closed)) poll(); },1000);
loadConfig().catch(()=>{}); if(location.hash==='#logs'){refreshLogs(); poll();}
