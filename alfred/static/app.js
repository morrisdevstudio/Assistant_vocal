const $ = id => document.getElementById(id);
const labels = {pending:"En attente",ringing:"Échéance atteinte",awaiting_delivery:"À délivrer · sortie audio non connectée",completed:"Terminé",missed:"Rappel manqué",cancelled:"Annulé"};
let serverOffset = 0;
let refreshRunning = false;

async function api(path, body) {
  const options = body === undefined ? {} : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)};
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) {
    throw new Error(typeof result.detail === "string" ? result.detail : "Vérifiez les champs et l’échéance demandée.");
  }
  return result;
}
function message(text, error=false) {
  $("feedback").textContent=text;
  $("feedback").classList.toggle("error",error);
}
function timeLeft(value) {
  const seconds = Math.max(0,Math.ceil((Date.parse(value)-Date.now()-serverOffset)/1000));
  return seconds >= 3600 ? `${Math.floor(seconds/3600)} h ${Math.floor(seconds%3600/60)} min` : `${Math.floor(seconds/60)} min ${String(seconds%60).padStart(2,"0")} s`;
}
function render(items,bells) {
  const container=$("items");
  const focused=document.activeElement?.dataset.cancel;
  container.replaceChildren();
  $("count").textContent=items.length;
  if (!items.length) {
    const p=document.createElement("p"); p.className="empty";
    p.textContent="Aucune échéance pour le moment. Commencez par un minuteur de 30 secondes.";
    container.append(p); return;
  }
  for (const item of items) {
    const article=document.createElement("article");article.className="entry";
    const top=document.createElement("div");top.className="entry-top";
    const title=document.createElement("h3");title.textContent=item.title;
    const state=document.createElement("span");state.className="state";state.textContent=labels[item.status]||item.status;
    if(item.kind==="reminder" && ["pending","awaiting_delivery"].includes(item.status)){
      state.textContent="Ancien rappel local · suspendu";
    }
    if(item.kind==="timer" && item.status==="ringing"){
      const targets=(bells?.targets||[]).filter(target=>target.floor_id===item.floor_id);
      state.textContent=bells?.configuration_error?"Sonnerie : configuration invalide":!targets.length?"Échéance atteinte · aucune sonnerie configurée":targets.some(target=>target.error)?"Sonnerie non confirmée · voir Home Assistant":targets.some(target=>target.phase==="sent")?"Sonnerie demandée au terminal":targets.every(target=>target.phase==="expired")?"Sonnerie terminée automatiquement":"Déclenchement de la sonnerie…";
    }
    top.append(title,state);
    const meta=document.createElement("p");
    const audience=item.kind==="reminder"?(item.audience==="family"?" · Famille":item.audience==="personal"?` · Personnel : ${item.owner_name||"profil indisponible"}`:" · Test sans profil"):"";
    meta.textContent=`${item.kind==="timer"?"Minuteur":"Rappel"}${audience}${item.series_id?" · Chaque semaine":""} · ${item.floor_id==="rdc"?"RDC":"1er étage"} · ${item.target_room||item.terminal_id}`;
    const date=document.createElement("p");
    date.textContent=new Date(item.due_at).toLocaleString("fr-FR") + (item.status==="pending" ? ` · dans ${timeLeft(item.due_at)}`:"");
    article.append(top,meta,date);
    if (["pending","ringing","awaiting_delivery","missed"].includes(item.status)) {
      const cancel=document.createElement("button");cancel.type="button";cancel.className="cancel";
      cancel.dataset.cancel=item.id;cancel.textContent=item.series_id && item.status==="pending"?"Annuler cette série":"Annuler";
      cancel.addEventListener("click", async()=>{
        cancel.disabled=true;
        try {await api(`/api/schedules/${item.id}/cancel`,{});message("Échéance annulée.");await refresh();}
        catch(error){message(error.message,true);cancel.disabled=false;}
      });
      article.append(cancel);
    }
    container.append(article);
  }
  if(focused) container.querySelector(`[data-cancel="${focused}"]`)?.focus();
}
async function refresh() {
  if(refreshRunning)return;
  refreshRunning=true;
  try {
    const [status,schedules,calendar]=await Promise.all([api("/api/status"),api("/api/schedules"),api("/api/calendar-reminders/status")]);
    serverOffset=Date.parse(status.server_time)-Date.now();
    $("health").textContent=status.scheduler_ok?"Service local actif":"Ordonnanceur en erreur";
    $("version").textContent=status.version;
    render(schedules.items,status.bells);
    $("calendar-reminder-status").textContent=!calendar.available?"Rappels HA non configurés.":calendar.calendar_errors?"Suivi des calendriers indisponible : vérifiez Home Assistant.":`${calendar.missed} rappel(s) manqué(s), ${calendar.unconfirmed} diffusion(s) non confirmée(s). Consultez les calendriers Home Assistant.`;
  } catch(error) {$("health").textContent="Service indisponible";message("Connexion au service interrompue. Les données affichées peuvent être anciennes.",true);}
  finally{refreshRunning=false;}
}
$("kind").addEventListener("change",()=>{
  const reminder=$("kind").value==="reminder";
  $("duration-field").hidden=reminder;$("duration").required=!reminder;
  $("date-field").hidden=!reminder;$("due").required=reminder;
  $("room-field").hidden=!reminder;
  $("room").required=reminder;
  $("audience-field").hidden=!reminder;
  $("recurrence-field").hidden=!reminder;
  $("owner-field").hidden=!reminder || $("audience").value!=="personal";
  $("owner").required=reminder && $("audience").value==="personal";
  if(reminder) loadReminderProfiles();
  $("submit").textContent=reminder?"Créer le rappel":"Créer le minuteur";
});
$("audience").addEventListener("change",()=>{
  const personal=$("kind").value==="reminder" && $("audience").value==="personal";
  $("owner-field").hidden=!personal; $("owner").required=personal;
});
async function loadReminderProfiles() {
  try {
    const result=await api("/api/profiles"), previous=$("owner").value;
    $("owner").replaceChildren(new Option("Choisir un profil", ""), ...result.items.map(profile=>new Option(profile.name, profile.id)));
    $("owner").value=previous;
  } catch(error) {message("Impossible de charger les profils : " + error.message,true);}
}
$("schedule-form").addEventListener("submit",async event=>{
  event.preventDefault();$("submit").disabled=true;
  try {
    const body={kind:$("kind").value,title:$("title").value.trim(),floor_id:$("floor").value,terminal_id:"browser-test"};
    if(body.kind==="timer")body.duration_seconds=Number($("duration").value);
    else {delete body.kind; delete body.terminal_id; body.due_at=new Date($("due").value).toISOString();body.target_room=$("room").value.trim();body.audience=$("audience").value;body.recurrence=$("recurrence").value;if(body.audience==="personal")body.owner_id=$("owner").value;}
    await api($("kind").value==="timer"?"/api/schedules":"/api/calendar-reminders",body);message($("kind").value==="reminder"?"Rappel enregistré dans Home Assistant. Sa diffusion sera demandée à l'échéance.":"Échéance enregistrée sur ce poste.");await refresh();
  } catch(error){message(error.message,true);}
  finally{$("submit").disabled=false;}
});
$("stop").addEventListener("click",async()=>{
  if(!$("floor").value){message("Choisissez l’étage du terminal de test.",true);$("floor").focus();return;}
  $("stop").disabled=true;
  try{const result=await api("/api/stop",{floor_id:$("floor").value});message(`${result.stopped} minuteur(s) arrêté(s) sur cet étage.`);await refresh();}
  catch(error){message(error.message,true);}
  finally{$("stop").disabled=false;}
});
function viewIs(name){const view=document.querySelector(`[data-view="${name}"]`);return Boolean(view&&!view.hidden);}
refresh();
// Un panneau masqué ne télécharge rien ; le retour à l'onglet rafraîchit tout de suite.
setInterval(()=>{if(!document.hidden&&viewIs("timers"))refresh();},1500);
window.addEventListener("hashchange",()=>{if(viewIs("timers"))refresh();});
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&viewIs("timers"))refresh();});
