const button=document.getElementById("terminal-test");
const bellButton=document.getElementById("terminal-bell-test");
const status=document.getElementById("terminal-status");
const sttButton=document.getElementById("terminal-stt-test");
const distanceButton=document.getElementById("terminal-stt-distance");
const sttResult=document.getElementById("terminal-stt-result");
const wakeStart=document.getElementById("wake-start");
const wakeStop=document.getElementById("wake-stop");
const wakeFalse=document.getElementById("wake-false-alarm");
const wakeStatus=document.getElementById("wake-status");
let sttPending=false,sttStarted=0,sttClear=null;
let busy=false;
let displayedExchange=null,conversationBusy=false;
let pendingDisplay=null;
async function refreshConversation(){
  if(conversationBusy)return;
  conversationBusy=true;
  try{
    const response=await fetch("/api/terminal/conversation",{cache:"no-store"});
    if(!response.ok)return;
    const result=await response.json();
    const transcript=document.getElementById("voice-transcript");
    const answer=document.getElementById("voice-answer");
    if(!result.available){
      if(pendingDisplay&&pendingDisplay.transcript===transcript.textContent&&pendingDisplay.answer===answer.textContent){
        transcript.textContent="Aucune demande transcrite.";
        answer.textContent="Échange ESP32 interrompu.";
      }
      displayedExchange=pendingDisplay=null;
      return;
    }
    const exchange=result.exchange;
    const revision=`${exchange.id}:${exchange.revision}`;
    if(revision===displayedExchange)return;
    displayedExchange=revision;
    const waiting=exchange.state==="waiting_for_command";
    const finished=exchange.state==="finished"||Boolean(exchange.error);
    transcript.textContent=exchange.transcript||
      (waiting?"Mot d’appel reconnu.":finished?"Aucune demande transcrite.":"Transcription en cours…");
    answer.textContent=exchange.answer||exchange.error||
      (waiting?"Alfred attend ta demande…":finished?"Échange terminé.":"Alfred prépare sa réponse…");
    pendingDisplay=finished||exchange.answer?null:{transcript:transcript.textContent,answer:answer.textContent};
    window.renderInternetSources?.(exchange.sources||[]);
    document.getElementById("voice-identity").textContent="";
    document.getElementById("voice-timings").textContent=exchange.error&&exchange.answer?exchange.error:"Conversation ESP32";
  }catch{}finally{conversationBusy=false;}
}
async function refresh(){
  if(busy)return;
  // Une requête de diagnostic différée conserve son état jusqu'à sa réponse.
  if(sttPending) return refreshSttResult();
  try{
    const response=await fetch("/api/terminal/status");
    if(!response.ok)throw new Error();
    const terminal=await response.json();
    button.disabled=!terminal.connected || terminal.phase!=="idle" || sttPending;
    bellButton.disabled=!terminal.connected || terminal.phase!=="idle" || sttPending || Boolean(terminal.bell&&terminal.bell.test);
    sttButton.disabled=!terminal.connected || terminal.phase!=="idle" || sttPending;
    distanceButton.disabled=sttButton.disabled;
    status.textContent=!terminal.enabled?"Aucun terminal ESP32 configuré."
      :terminal.connected?`ESP32 connecté · ${terminal.room}. Appuyez sur K2 puis parlez. État : ${{idle:"prêt",listening:"écoute",recording:"parole reçue",processing:"préparation de la réponse",playing:"réponse",test_playing:"essai sonore"}[terminal.phase]||terminal.phase}.`
      :"ESP32 déconnecté. Alfred tente de le retrouver.";
    const wake=terminal.wake_word||{enabled:false};
    const wakeName=wake.phrase||({alexa:"Alexa",jarvis:"Jarvis",alfred:"Hé Alfred"}[wake.name]||"Hé Alfred");
    wakeStart.textContent=`Activer « ${wakeName} »`;
    wakeStart.disabled=!terminal.connected || !wake.enabled || wake.armed || sttPending;
    wakeStop.disabled=!wake.armed;
    wakeFalse.disabled=!wake.armed;
    const health=terminal.health||{};
    const recovery=terminal.wake_recoveries||0, renewals=terminal.wake_renewals||0;
    if(!wake.enabled){
      wakeStatus.textContent=wake.error?`Mot d’appel indisponible (${wake.error}).`
        :"Mot d’appel désactivé dans la configuration du terminal.";
    }else if(!wake.armed){
      wakeStatus.textContent="Veille inactive : le mot d’appel n’écoute pas.";
    }else if(!wake.receiving){
      wakeStatus.textContent=terminal.phase==="playing"||terminal.phase==="processing"||terminal.phase==="listening"||terminal.phase==="recording"
        ?"Veille en pause pendant la conversation."
        :`Veille demandée · micro non confirmé${wake.error?" · "+wake.error:" · reprise en cours"}.`;
    }else{
      wakeStatus.textContent=`Veille active · ${wake.detections} détection(s) · ${wake.engine==="stt"?`STT local · dernière analyse ${wake.last_ms||0} ms`:`seuil ${wake.threshold}`} · ${wake.false_alarms} faux réveil(s) déclaré(s).${terminal.phase==="waking"?" En attente du mot.":""}`;
    }
    if(wake.armed)wakeStatus.textContent+=" Pendant la sonnerie, dites « Alfredo » seule pour couper le son.";
    if(health.status && health.status!=="ok"){
      status.textContent+=` Diagnostics : ${health.status}${health.recovery_reason?` · ${health.recovery_reason}`:""}.`;
    }
    status.dataset.recoveries=String(recovery);status.dataset.renewals=String(renewals);
    if(sttPending)await refreshSttResult();
  }catch{button.disabled=true;sttButton.disabled=true;distanceButton.disabled=true;wakeStart.disabled=true;wakeStop.disabled=true;wakeFalse.disabled=true;status.textContent="État de l’ESP32 indisponible.";}
}
async function refreshSttResult(){
  const response=await fetch("/api/terminal/stt-test/result");
  if(!response.ok)throw new Error();
  const result=await response.json();
  if(result.available){
    sttPending=false;
    const ending={speech_pause:"fin de parole détectée",max_duration:"durée maximale atteinte",device_end_or_timeout:"prise arrêtée"}[result.capture_end];
    sttResult.textContent=result.error || `Transcription : ${result.text||"Aucune parole reconnue."} · ${result.stt_ms} ms${ending?" · "+ending:""} · aucune action exécutée.`;
    sttClear=setTimeout(()=>{sttResult.textContent="Résultat du test effacé.";},120000);
  }else if(!result.armed && Date.now()-sttStarted>60000){
    sttPending=false;sttResult.textContent="Test expiré. Relancez-le puis appuyez sur K2.";
  }
}
bellButton.addEventListener("click",async()=>{
  bellButton.disabled=true;
  status.textContent="Sonnerie de test sur l’ESP32…";
  let message;
  try{
    const response=await fetch("/api/terminal/bell-test",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});
    if(!response.ok)throw new Error();
    message="Sonnerie de test terminée. Le son provient du haut-parleur de l’ESP32.";
  }catch{message="Sonnerie de test impossible : terminal occupé, déconnecté ou minuteur déjà en cours.";}
  await refresh();
  status.textContent=message;
});
async function wakeCall(path,message){
  wakeStart.disabled=true;wakeStop.disabled=true;wakeFalse.disabled=true;
  try{
    const response=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});
    if(!response.ok)throw new Error();
    if(message)wakeStatus.textContent=message;
  }catch{wakeStatus.textContent="Commande du mot d’appel impossible : vérifiez le terminal.";}
  await refresh();
}
wakeStart.addEventListener("click",()=>wakeCall("/api/terminal/wake-word/start","Veille demandée : attente du mot d’appel."));
wakeStop.addEventListener("click",()=>wakeCall("/api/terminal/wake-word/stop","Veille arrêtée."));
wakeFalse.addEventListener("click",()=>wakeCall("/api/terminal/wake-word/false-alarm"));
async function armSttTest(startNow=false){
  sttButton.disabled=true;distanceButton.disabled=true;clearTimeout(sttClear);
  try{
    const response=await fetch(`/api/terminal/stt-test${startNow?"?start=true":""}`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});
    if(!response.ok)throw new Error();
    sttPending=true;sttStarted=Date.now();
    sttResult.textContent=(startNow?"Attendez le signal de l’ESP32 puis dites une phrase, sans appuyer sur K2. ":"Appuyez sur K2 puis dites une phrase. ")+"Le texte apparaîtra ici. Aucune commande ni appel IA. Ce test ne lit pas de réponse vocale ; le texte est effacé après deux minutes.";
  }catch{sttResult.textContent="Test indisponible : vérifiez que le terminal est connecté et au repos.";}
  await refresh();
}
sttButton.addEventListener("click",()=>armSttTest(false));
distanceButton.addEventListener("click",()=>armSttTest(true));
button.addEventListener("click",async()=>{
  busy=true;button.disabled=true;status.textContent="Préparation de la voix pour l’ESP32…";
  try{
    const response=await fetch("/api/terminal/test",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});
    const result=await response.json();
    if(!response.ok || !result.finished)throw new Error();
    status.textContent="La carte signale la fin de lecture. Appuyez sur K2 pour essayer une conversation.";
  }catch{status.textContent="Lecture sur l’ESP32 non confirmée. Vérifiez le terminal avant de réessayer.";}
  finally{busy=false;}
});
function terminalViewVisible(){
  if(window.__alfredForceTerminalVisible===true)return true;
  // L'absence de navigateur de vues (tests ou panneau isolé) ne désactive pas
  // le diagnostic : seuls un autre panneau explicitement affiché le fait.
  const views=[...document.querySelectorAll('[data-view]')];
  if(!views.length)return true;
  const view=views.find(item=>item.dataset.view==="voice");
  return Boolean(view&&!view.hidden);
}
refresh();
refreshConversation();
setInterval(()=>{if(!document.hidden&&terminalViewVisible())refreshConversation();},1000);
setInterval(()=>{if(!document.hidden&&terminalViewVisible())refresh();},3000);
window.addEventListener("hashchange",()=>{if(terminalViewVisible()){refreshConversation();refresh();}});
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&terminalViewVisible()){refreshConversation();refresh();}});
